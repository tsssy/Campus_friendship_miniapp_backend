#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
开放式接口冒烟测试（openid 作为 user_id 字符串）
仅覆盖两类：
1) 用户相关接口（UserManagement）
2) 论坛相关接口（ForumManager）

使用方法：
1) 先启动后端服务（例如）：
   uvicorn app.server_run:app --host 127.0.0.1 --port 8000
2) 运行本脚本：
   python tests/smoke_user_forum_openid.py

注意：
- 数据库已清空时更易复现完整流程
- 所有 user_id 均为字符串（模拟 openid），例如 "wx_openid_u1"
"""

import asyncio
import os
import time
from typing import Dict, Any

import httpx


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1")


async def wait_for_server_ready(timeout_sec: int = 20) -> None:
    """等待后端可用（轮询 / 根接口）"""
    health_url = BASE_URL.replace("/api/v1", "/")
    start = time.time()
    async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
        while time.time() - start < timeout_sec:
            try:
                resp = await client.get(health_url)
                if resp.status_code in (200, 404):
                    return
            except Exception:
                pass
            await asyncio.sleep(0.5)
    raise TimeoutError("后端在预期时间内未就绪，请确认服务已启动并监听 8000 端口")


async def post_json(client: httpx.AsyncClient, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    r = await client.post(url, json=payload)
    try:
        data = r.json()
    except Exception:
        data = {"_raw": r.text}
    if r.status_code >= 400:
        raise RuntimeError(f"POST {path} 失败, status={r.status_code}, resp={data}")
    return data


async def run_user_flow(client: httpx.AsyncClient) -> str:
    """用户相关接口冒烟：创建/编辑/保存/获取"""
    print("\n==== 用户相关接口冒烟测试 ====")
    user_id = "wx_openid_u1"

    # 1) 创建用户（使用字符串 user_id）
    payload = {
        "user_name": "smoke_user_1",
        "user_id": user_id,  # 字符串 openid
        "gender": 1
    }
    data = await post_json(client, "/UserManagement/create_new_user", payload)
    assert data.get("success") is True, data
    assert isinstance(data.get("user_id"), str), data
    print("创建用户成功:", data)

    # 2) 编辑用户年龄
    data = await post_json(client, "/UserManagement/edit_user_age", {
        "user_id": user_id,
        "age": 22
    })
    assert data.get("success") is True, data
    print("编辑年龄成功")

    # 3) 编辑目标性别
    data = await post_json(client, "/UserManagement/edit_target_gender", {
        "user_id": user_id,
        "target_gender": 2
    })
    assert data.get("success") is True, data
    print("编辑目标性别成功")

    # 4) 编辑用户简介
    data = await post_json(client, "/UserManagement/edit_summary", {
        "user_id": user_id,
        "summary": "我是一名测试用户，喜欢论坛互动。"
    })
    assert data.get("success") is True, data
    print("编辑简介成功")

    # 5) 保存到数据库
    data = await post_json(client, "/UserManagement/save_to_database", {
        "user_id": user_id
    })
    assert data.get("success") in (True, False)  # True 表示已保存，False 表示可能无变更
    print("保存到数据库返回:", data)

    # 6) 读取用户信息
    data = await post_json(client, "/UserManagement/get_user_info_with_user_id", {
        "user_id": user_id
    })
    assert data.get("user_id") == user_id, data
    assert data.get("user_name") == "smoke_user_1", data
    print("读取用户信息成功:", data)

    return user_id


async def run_forum_flow(client: httpx.AsyncClient, creator_user_id: str) -> None:
    """论坛相关接口冒烟：发帖/列表/点赞/评论/详情"""
    print("\n==== 论坛相关接口冒烟测试 ====")

    # 准备第二个用户用于互动
    other_user_id = "wx_openid_u2"
    await post_json(client, "/UserManagement/create_new_user", {
        "user_name": "smoke_user_2",
        "user_id": other_user_id,
        "gender": 2
    })
    # 将第二个用户写入数据库（否则点赞时用户文档不存在，liked_post_ids 无法更新）
    await post_json(client, "/UserManagement/save_to_database", {"user_id": other_user_id})

    # 1) 发帖
    data = await post_json(client, "/ForumManager/create_post", {
        "creator_user_id": creator_user_id,
        "post_content": "这是第一条论坛帖子 (smoke test)",
        "post_type": "text",
        "post_category": "",
        "tags": []
    })
    assert data.get("success") is True and isinstance(data.get("post_id"), int), data
    post_id = data["post_id"]
    print("发帖成功, post_id=", post_id)

    # 2) 获取帖子列表（用另一用户视角）
    data = await post_json(client, "/ForumManager/get_posts_list", {
        "user_id": other_user_id,
        "sort_type": "latest",
        "page": 1,
        "page_size": 10
    })
    assert data.get("success") is True, data
    posts = data.get("posts", [])
    assert any(p.get("post_id") == post_id for p in posts), data
    print("获取帖子列表成功, 条数:", len(posts))

    # 3) 点赞（other_user 点赞 post）
    data = await post_json(client, "/ForumManager/toggle_post_like", {
        "user_id": other_user_id,
        "post_id": post_id,
        "action": "like"
    })
    assert data.get("success") is True and data.get("is_liked") is True, data
    print("点赞成功")

    # 4) 查看帖子详情，确认 is_liked 为 True
    data = await post_json(client, "/ForumManager/get_post_detail", {
        "user_id": other_user_id,
        "post_id": post_id
    })
    assert data.get("success") is True and data.get("post", {}).get("is_liked") is True, data
    print("帖子详情校验点赞成功")

    # 5) 取消点赞
    data = await post_json(client, "/ForumManager/toggle_post_like", {
        "user_id": other_user_id,
        "post_id": post_id,
        "action": "unlike"
    })
    assert data.get("success") is True and data.get("is_liked") is False, data
    print("取消点赞成功")

    # 6) 评论（other_user 评论）
    data = await post_json(client, "/ForumManager/create_comment", {
        "user_id": other_user_id,
        "post_id": post_id,
        "comment_content": "首条评论 (smoke test)"
    })
    assert data.get("success") is True and isinstance(data.get("comment_id"), int), data
    comment_id = data["comment_id"]
    print("评论发布成功, comment_id=", comment_id)

    # 7) 获取评论列表（creator_user 视角）
    data = await post_json(client, "/ForumManager/get_post_comments", {
        "post_id": post_id,
        "user_id": creator_user_id,
        "page": 1,
        "page_size": 10
    })
    assert data.get("success") is True and len(data.get("comments", [])) >= 1, data
    print("获取评论列表成功, 条数:", len(data.get("comments", [])))

    # 8) 评论点赞/取消点赞（creator_user 点赞）
    data = await post_json(client, "/ForumManager/toggle_comment_like", {
        "user_id": creator_user_id,
        "comment_id": comment_id,
        "action": "like"
    })
    assert data.get("success") is True and data.get("is_liked") is True, data
    data = await post_json(client, "/ForumManager/toggle_comment_like", {
        "user_id": creator_user_id,
        "comment_id": comment_id,
        "action": "unlike"
    })
    assert data.get("success") is True and data.get("is_liked") is False, data
    print("评论点赞/取消点赞成功")


async def main():
    await wait_for_server_ready()
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        uid = await run_user_flow(client)
        await run_forum_flow(client, uid)
    print("\n✅ 冒烟测试完成（用户 + 论坛）")


if __name__ == "__main__":
    asyncio.run(main())


