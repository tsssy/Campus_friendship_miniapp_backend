#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
论坛接口端到端测试脚本（内存优先 + 周期性落库校验）
- 覆盖以下接口：
  1) /UserManagement/create_new_user
  2) /ForumManager/create_post
  3) /ForumManager/get_posts_list
  4) /ForumManager/search_posts
  5) /ForumManager/toggle_post_like（like -> unlike）
  6) /ForumManager/create_comment
  7) /ForumManager/get_post_comments
  8) /ForumManager/toggle_comment_like（like -> unlike）
- 在关键节点对 MongoDB 的 users/posts/comments 进行轮询校验，确保内存与数据库同步

运行前提：
- 本地服务已启动: http://127.0.0.1:8000
- 数据库为本地 MongoDB: mongodb://localhost:27017
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional

import aiohttp
from motor.motor_asyncio import AsyncIOMotorClient

BASE_URL = "http://127.0.0.1:8000"
API_USER_PREFIX = "/api/v1/UserManagement"
API_FORUM_PREFIX = "/api/v1/ForumManager"

# 测试用固定用户
TEST_USER_ID = 123456
TEST_USER_NAME = "test_user_123456"

# DB 配置
MONGO_URL = "mongodb://localhost:27017"
DB_NAME = "campus_friendship_db"

# 同步等待参数（ForumManager 每10s自动落库一次，这里给足余量）
SYNC_TIMEOUT_SEC = 20
SYNC_POLL_INTERVAL_SEC = 1.0


async def http_post(session: aiohttp.ClientSession, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    async with session.post(url, json=data) as resp:
        text = await resp.text()
        try:
            payload = json.loads(text)
        except Exception:
            payload = {"raw": text}
        return {"ok": (resp.status == 200), "status": resp.status, "data": payload}


async def wait_until(predicate, timeout_sec: int = SYNC_TIMEOUT_SEC, interval_sec: float = SYNC_POLL_INTERVAL_SEC) -> bool:
    """轮询等待直到条件为真或超时"""
    started = time.time()
    while time.time() - started < timeout_sec:
        ok = await predicate()
        if ok:
            return True
        await asyncio.sleep(interval_sec)
    return False


async def ensure_user_exists(session: aiohttp.ClientSession) -> bool:
    """确保测试用户存在（内存 + DB）"""
    url = f"{BASE_URL}{API_USER_PREFIX}/create_new_user"
    resp = await http_post(session, url, {
        "telegram_user_name": TEST_USER_NAME,
        "telegram_user_id": TEST_USER_ID,
        "gender": 2
    })
    # 如果已存在也返回 success True（后端当前实现会直接创建覆盖内存）
    return resp["ok"] and resp["data"].get("success", False)


async def run_e2e() -> int:
    # 连接数据库
    mongo_client = AsyncIOMotorClient(MONGO_URL)
    db = mongo_client[DB_NAME]

    async with aiohttp.ClientSession() as session:
        print("\n=== 论坛接口端到端测试开始 ===")

        # 1) 创建用户（内存优先）
        print("1) 创建用户...")
        if not await ensure_user_exists(session):
            print("   ❌ create_new_user 失败")
            return 1
        print("   ✅ 用户创建/存在")

        # 2) 发帖
        print("2) 发布帖子...")
        create_post_url = f"{BASE_URL}{API_FORUM_PREFIX}/create_post"
        post_content = "端到端测试首帖"
        create_post_resp = await http_post(session, create_post_url, {
            "creator_user_id": TEST_USER_ID,
            "post_content": post_content,
            "post_type": "text",
            "post_category": "测试",
            "tags": ["e2e", "forum"],
            "media_files": []
        })
        if not (create_post_resp["ok"] and create_post_resp["data"].get("success")):
            print("   ❌ create_post 失败:", create_post_resp)
            return 1
        post_id = create_post_resp["data"].get("post_id")
        print(f"   ✅ 发帖成功，post_id={post_id}")

        # 2.1) 校验：内存接口可见
        get_list_url = f"{BASE_URL}{API_FORUM_PREFIX}/get_posts_list"
        posts_list_resp = await http_post(session, get_list_url, {
            "user_id": TEST_USER_ID,
            "sort_type": "latest",
            "page": 1,
            "page_size": 10
        })
        if not (posts_list_resp["ok"] and posts_list_resp["data"].get("success")):
            print("   ❌ get_posts_list 失败:", posts_list_resp)
            return 1
        ids = [p.get("post_id") for p in posts_list_resp["data"].get("posts", [])]
        if post_id not in ids:
            print("   ❌ get_posts_list 未返回新帖子")
            return 1
        print("   ✅ get_posts_list 包含新帖子")

        # 2.2) 校验：搜索可见
        search_url = f"{BASE_URL}{API_FORUM_PREFIX}/search_posts"
        search_resp = await http_post(session, search_url, {
            "user_id": TEST_USER_ID,
            "search_query": "e2e",
            "page": 1,
            "page_size": 10
        })
        if not (search_resp["ok"] and search_resp["data"].get("success")):
            print("   ❌ search_posts 失败:", search_resp)
            return 1
        s_ids = [p.get("post_id") for p in search_resp["data"].get("posts", [])]
        if post_id not in s_ids:
            print("   ❌ search_posts 未命中新帖子")
            return 1
        print("   ✅ search_posts 命中新帖子")

        # 2.3) 等待 DB 对齐：users.post_ids 包含 post_id，posts 存在该文档
        print("   ⏳ 等待数据库对齐 users/posts...")
        async def user_has_post():
            d = await db.users.find_one({"_id": TEST_USER_ID, "post_ids": post_id})
            return d is not None

        async def post_exists():
            d = await db.posts.find_one({"_id": post_id})
            return d is not None

        ok_users = await wait_until(user_has_post)
        ok_posts = await wait_until(post_exists)
        if not (ok_users and ok_posts):
            print("   ❌ 数据库未在超时内对齐 users/posts")
            return 1
        print("   ✅ 数据库 users/posts 已对齐")

        # 3) 点赞帖子（like -> unlike），并校验 DB liked_post_ids 同步
        print("3) 点赞/取消点赞 帖子...")
        toggle_like_url = f"{BASE_URL}{API_FORUM_PREFIX}/toggle_post_like"

        like_resp = await http_post(session, toggle_like_url, {
            "user_id": TEST_USER_ID,
            "post_id": post_id,
            "action": "like"
        })
        if not (like_resp["ok"] and like_resp["data"].get("success")):
            print("   ❌ toggle_post_like like 失败:", like_resp)
            return 1
        print("   ✅ 点赞成功，new_like_count=", like_resp["data"].get("new_like_count"))

        # 等待 DB liked_post_ids 包含
        print("   ⏳ 等待数据库 users.liked_post_ids 包含 post_id...")
        async def liked_added():
            d = await db.users.find_one({"_id": TEST_USER_ID, "liked_post_ids": post_id})
            return d is not None

        ok_liked_add = await wait_until(liked_added)
        if not ok_liked_add:
            print("   ❌ 数据库未在超时内写入 liked_post_ids")
            return 1
        print("   ✅ 数据库 liked_post_ids 已写入")

        # 取消点赞
        unlike_resp = await http_post(session, toggle_like_url, {
            "user_id": TEST_USER_ID,
            "post_id": post_id,
            "action": "unlike"
        })
        if not (unlike_resp["ok"] and unlike_resp["data"].get("success")):
            print("   ❌ toggle_post_like unlike 失败:")
            return 1
        print("   ✅ 取消点赞成功，new_like_count=", unlike_resp["data"].get("new_like_count"))

        # 等待 DB liked_post_ids 移除
        print("   ⏳ 等待数据库 users.liked_post_ids 移除 post_id...")
        async def liked_removed():
            d = await db.users.find_one({"_id": TEST_USER_ID, "liked_post_ids": post_id})
            return d is None

        ok_liked_rm = await wait_until(liked_removed)
        if not ok_liked_rm:
            print("   ❌ 数据库未在超时内移除 liked_post_ids")
            return 1
        print("   ✅ 数据库 liked_post_ids 已移除")

        # 4) 发布评论
        print("4) 发布评论...")
        create_comment_url = f"{BASE_URL}{API_FORUM_PREFIX}/create_comment"
        comment_content = "首条评论：内存优先测试"
        create_comment_resp = await http_post(session, create_comment_url, {
            "user_id": TEST_USER_ID,
            "post_id": post_id,
            "comment_content": comment_content
        })
        if not (create_comment_resp["ok"] and create_comment_resp["data"].get("success")):
            print("   ❌ create_comment 失败:", create_comment_resp)
            return 1
        comment_id = create_comment_resp["data"].get("comment_id")
        print(f"   ✅ 评论发布成功，comment_id={comment_id}")

        # 4.1) 获取评论列表（内存）
        get_comments_url = f"{BASE_URL}{API_FORUM_PREFIX}/get_post_comments"
        comments_resp = await http_post(session, get_comments_url, {
            "post_id": post_id,
            "user_id": TEST_USER_ID,
            "page": 1,
            "page_size": 10
        })
        if not (comments_resp["ok"] and comments_resp["data"].get("success")):
            print("   ❌ get_post_comments 失败:", comments_resp)
            return 1
        c_ids = [c.get("comment_id") for c in comments_resp["data"].get("comments", [])]
        if comment_id not in c_ids:
            print("   ❌ get_post_comments 未返回新评论")
            return 1
        print("   ✅ get_post_comments 包含新评论")

        # 4.2) 等待 DB 对齐：comments 表出现该评论
        print("   ⏳ 等待数据库 comments 对齐...")
        async def comment_exists():
            d = await db.comments.find_one({"_id": comment_id})
            return d is not None

        ok_comment = await wait_until(comment_exists)
        if not ok_comment:
            print("   ❌ 数据库未在超时内写入评论")
            return 1
        print("   ✅ 数据库 comments 已对齐")

        # 5) 评论点赞（内存，不落库，但验证接口行为）
        print("5) 评论点赞/取消点赞（仅内存）...")
        toggle_comment_like_url = f"{BASE_URL}{API_FORUM_PREFIX}/toggle_comment_like"
        c_like_resp = await http_post(session, toggle_comment_like_url, {
            "user_id": TEST_USER_ID,
            "comment_id": comment_id,
            "action": "like"
        })
        if not (c_like_resp["ok"] and c_like_resp["data"].get("success")):
            print("   ❌ toggle_comment_like like 失败:", c_like_resp)
            return 1
        c_unlike_resp = await http_post(session, toggle_comment_like_url, {
            "user_id": TEST_USER_ID,
            "comment_id": comment_id,
            "action": "unlike"
        })
        if not (c_unlike_resp["ok"] and c_unlike_resp["data"].get("success")):
            print("   ❌ toggle_comment_like unlike 失败:", c_unlike_resp)
            return 1
        print("   ✅ 评论点赞/取消点赞 接口通过")

        print("\n=== 论坛接口端到端测试完成（全部通过）===")
        return 0


if __name__ == "__main__":
    exit(asyncio.run(run_e2e()))
