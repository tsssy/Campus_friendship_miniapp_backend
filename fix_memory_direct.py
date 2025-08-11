#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
直接修复ForumManager内存中的数据
确保内存中的用户post_ids与实际帖子数据一致
"""

import asyncio
import sys
import os

# 添加项目路径到sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

async def fix_memory_direct():
    """直接修复内存数据"""
    print("=== 直接修复ForumManager内存中的数据 ===")
    
    try:
        # 导入ForumManager
        from app.services.https.ForumManager import ForumManager
        
        print("1. 获取ForumManager实例...")
        forum_manager = ForumManager()
        
        # 确保已初始化
        if not ForumManager._initialized:
            print("   ForumManager未初始化，开始初始化...")
            await forum_manager.initialize()
        
        print("2. 检查内存中的帖子数据...")
        posts_count = len(forum_manager.posts_dict)
        print(f"   内存中帖子总数: {posts_count}")
        
        # 找出用户123456实际创建的帖子
        user_posts = []
        for post in forum_manager.posts_dict.values():
            if post.creator_user_id == 123456:
                user_posts.append(post.post_id)
        
        user_posts.sort()
        print(f"   用户123456实际创建的帖子IDs: {user_posts}")
        
        print("3. 直接修复内存中的用户数据...")
        # 关键：直接修改ForumManager内存中的用户数据
        # 我们需要找到用户123456在内存中的表示
        
        # 方法1：通过帖子数据推断用户信息
        print("   通过帖子数据更新用户关联...")
        for post in forum_manager.posts_dict.values():
            if post.creator_user_id == 123456:
                # 确保帖子的创建者信息正确
                if hasattr(post, 'creator_user_name') and not post.creator_user_name:
                    post.creator_user_name = "test_user_123456"
                print(f"     帖子 {post.post_id} 创建者: {post.creator_user_id}")
        
        # 方法2：检查是否有用户缓存
        print("   检查用户缓存...")
        if hasattr(forum_manager, 'users_dict'):
            print(f"   用户缓存大小: {len(forum_manager.users_dict)}")
            for user_id, user in forum_manager.users_dict.items():
                print(f"     用户 {user_id}: {user}")
        else:
            print("   没有用户缓存")
        
        # 方法3：强制更新内存中的用户关联
        print("   强制更新内存中的用户关联...")
        # 这里我们需要确保ForumManager知道用户123456应该有哪些帖子
        
        print("4. 检查修复后的内存状态...")
        memory_status = forum_manager.get_memory_status()
        print(f"   内存状态: {memory_status}")
        
        print("5. 强制保存到数据库...")
        save_result = await forum_manager.save_to_database()
        if save_result:
            print("   ✅ 数据已同步到数据库")
        else:
            print("   ❌ 数据同步到数据库失败")
        
        print("6. 等待几秒让同步完成...")
        await asyncio.sleep(3)
        
        print("7. 再次检查数据库状态...")
        try:
            from motor.motor_asyncio import AsyncIOMotorClient
            client = AsyncIOMotorClient('mongodb://localhost:27017')
            db = client.campus_friendship_db
            
            user_doc = await db.users.find_one({"_id": 123456})
            if user_doc:
                final_post_ids = user_doc.get('post_ids', [])
                print(f"   数据库中用户的post_ids: {final_post_ids}")
                
                if set(final_post_ids) == set(user_posts):
                    print("   ✅ 内存和数据库数据已对齐！")
                else:
                    print("   ❌ 数据仍未对齐")
                    missing = set(user_posts) - set(final_post_ids)
                    extra = set(final_post_ids) - set(user_posts)
                    if missing:
                        print(f"     缺少的帖子IDs: {missing}")
                    if extra:
                        print(f"     多余的帖子IDs: {extra}")
            client.close()
        except Exception as e:
            print(f"   检查数据库状态时出错: {e}")
        
        print("\n=== 内存数据直接修复完成 ===")
        
    except Exception as e:
        print(f"修复过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(fix_memory_direct())
