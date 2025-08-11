#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Chatroom 冒烟测试（openid 作为字符串 user_id）
- 创建两个用户（字符串 user_id）
- 创建匹配并获取/创建聊天室
- 发送消息与获取历史

使用：
  conda run -n miracle_backend_env python tests/smoke_chatroom_openid.py
"""

import asyncio
import os
import time
from typing import Dict, Any, List

import httpx


BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000/api/v1")


async def wait_for_server_ready(timeout_sec: int = 20) -> None:
    """等待后端可用（轮询根路径）"""
    root_url = BASE_URL.replace("/api/v1", "/")
    start = time.time()
    async with httpx.AsyncClient(timeout=2.0, trust_env=False) as client:
        while time.time() - start < timeout_sec:
            try:
                r = await client.get(root_url)
                if r.status_code in (200, 404):
                    return
            except Exception:
                pass
            await asyncio.sleep(0.5)
    raise TimeoutError("服务未就绪，请确认 127.0.0.1:8000 已启动")


async def post(client: httpx.AsyncClient, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}{path}"
    resp = await client.post(url, json=payload)
    data: Dict[str, Any]
    try:
        data = resp.json()
    except Exception:
        data = {"_raw": resp.text}
    if resp.status_code >= 400:
        raise RuntimeError(f"POST {path} 失败 status={resp.status_code}, resp={data}")
    return data


async def main():
    await wait_for_server_ready()
    async with httpx.AsyncClient(timeout=10.0, trust_env=False) as client:
        print("\n==== Chatroom 冒烟测试 ====")

        user1 = "wx_openid_c1"
        user2 = "wx_openid_c2"

        # 1) 创建两个用户并存库
        for uid, name, gender in (
            (user1, "chat_user_1", 1),
            (user2, "chat_user_2", 2),
        ):
            await post(client, "/UserManagement/create_new_user", {
                "user_name": name,
                "user_id": uid,
                "gender": gender
            })
            await post(client, "/UserManagement/save_to_database", {"user_id": uid})

        # 2) 创建匹配
        create_match = await post(client, "/MatchManager/create_match", {
            "user_id_1": user1,
            "user_id_2": user2,
            "reason_1": "reason for u1",
            "reason_2": "reason for u2",
            "match_score": 90
        })
        assert create_match.get("success") is True, create_match
        match_id = create_match.get("match_id")
        assert isinstance(match_id, int), create_match
        print("创建匹配成功, match_id=", match_id)

        # 3) 获取或创建聊天室
        room_resp = await post(client, "/ChatroomManager/get_or_create_chatroom", {
            "user_id_1": user1,
            "user_id_2": user2,
            "match_id": match_id
        })
        assert room_resp.get("success") is True and isinstance(room_resp.get("chatroom_id"), int), room_resp
        chatroom_id = room_resp["chatroom_id"]
        print("获取/创建聊天室成功, chatroom_id=", chatroom_id)

        # 4) 获取历史（应为空）
        history_1 = await post(client, "/ChatroomManager/get_chat_history", {
            "chatroom_id": chatroom_id,
            "user_id": user1
        })
        assert history_1.get("success") is True, history_1
        print("初始历史条数:", len(history_1.get("messages", [])))

        # 5) user1 发送消息
        send_1 = await post(client, "/ChatroomManager/send_message", {
            "chatroom_id": chatroom_id,
            "sender_user_id": user1,
            "message_content": "Hello from user1"
        })
        assert send_1.get("success") is True, send_1
        print("user1 发送消息成功")

        # 6) user2 发送消息
        send_2 = await post(client, "/ChatroomManager/send_message", {
            "chatroom_id": chatroom_id,
            "sender_user_id": user2,
            "message_content": "Hi, this is user2"
        })
        assert send_2.get("success") is True, send_2
        print("user2 发送消息成功")

        # 7) 分别查询历史，验证有消息
        h1 = await post(client, "/ChatroomManager/get_chat_history", {"chatroom_id": chatroom_id, "user_id": user1})
        h2 = await post(client, "/ChatroomManager/get_chat_history", {"chatroom_id": chatroom_id, "user_id": user2})
        assert h1.get("success") and len(h1.get("messages", [])) >= 2, h1
        assert h2.get("success") and len(h2.get("messages", [])) >= 2, h2
        print("user1 历史条数:", len(h1["messages"]))
        print("user2 历史条数:", len(h2["messages"]))

        # 8) 再次请求 get_or_create_chatroom，确认复用同一聊天室
        room_again = await post(client, "/ChatroomManager/get_or_create_chatroom", {
            "user_id_1": user1,
            "user_id_2": user2,
            "match_id": match_id
        })
        assert room_again.get("chatroom_id") == chatroom_id, room_again
        print("二次获取聊天室复用成功")

        print("\n✅ Chatroom 冒烟测试完成")


if __name__ == "__main__":
    asyncio.run(main())


