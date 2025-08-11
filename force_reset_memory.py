#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
内存强制重置脚本
- 清空 ForumManager 内存缓存（posts_dict/comments_dict）并复位初始化标志
- 清空 UserManagement 内存缓存（user_list 等）并复位初始化标志
- 复位 Post/Comment 的自增计数器与初始化标志
使用场景：数据库已清空，需要让服务端内存也回到干净状态
"""

# 按用户要求：加中文注释

from typing import Any

def safe_reset_forum_manager() -> None:
    """重置 ForumManager 的内存状态"""
    try:
        from app.services.https.ForumManager import ForumManager
        fm = ForumManager()
        # 清空缓存
        if hasattr(fm, "posts_dict"):
            fm.posts_dict.clear()
        if hasattr(fm, "comments_dict"):
            fm.comments_dict.clear()
        # 复位初始化标志
        ForumManager._initialized = False
        # 如果类里有单例引用，保持为现有对象但内容为空即可
        print("[OK] ForumManager 内存已清空，已复位初始化标志")
    except Exception as e:
        print(f"[WARN] 重置 ForumManager 失败: {e}")


def safe_reset_user_management() -> None:
    """重置 UserManagement 的内存状态"""
    try:
        from app.services.https.UserManagement import UserManagement
        um = UserManagement()
        # 清空用户缓存
        if hasattr(um, "user_list"):
            um.user_list.clear()
        if hasattr(um, "male_user_list"):
            um.male_user_list.clear()
        if hasattr(um, "female_user_list"):
            um.female_user_list.clear()
        # 复位计数与初始化标志
        um.user_counter = 0
        UserManagement._initialized = False
        print("[OK] UserManagement 内存已清空，已复位初始化标志")
    except Exception as e:
        print(f"[WARN] 重置 UserManagement 失败: {e}")


def safe_reset_post_comment_counters() -> None:
    """重置 Post / Comment 的计数器与初始化标志"""
    try:
        from app.objects.Post import Post
        Post._post_counter = 0
        Post._initialized = False
        print("[OK] Post 计数器与初始化标志已复位")
    except Exception as e:
        print(f"[WARN] 重置 Post 失败: {e}")

    try:
        from app.objects.Comment import Comment
        Comment._comment_counter = 0
        Comment._initialized = False
        print("[OK] Comment 计数器与初始化标志已复位")
    except Exception as e:
        print(f"[WARN] 重置 Comment 失败: {e}")


def main() -> None:
    print("=== 开始强制清理内存（Forum/User/Post/Comment）===")
    safe_reset_forum_manager()
    safe_reset_user_management()
    safe_reset_post_comment_counters()
    print("=== 内存清理完成 ===")

if __name__ == "__main__":
    main()
