from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from app.core.database import Database
from app.objects.Post import Post
from app.objects.Comment import Comment
from app.services.https.UserManagement import UserManagement
from app.utils.my_logger import MyLogger
from app.schemas.ForumManager import GetPostDetailResponse

logger = MyLogger("ForumManager")


class ForumManager:
    """论坛管理服务（最简版）
    - 采用内存优先模式：所有操作先在内存中进行，定期同步到数据库
    - 内存缓存：posts_dict, comments_dict
    - 数据库集合：`posts`, `comments`
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # 内存数据结构
            cls._instance.posts_dict = {}      # post_id -> Post 实例
            cls._instance.comments_dict = {}   # comment_id -> Comment 实例
            cls._instance._initialized = False
        return cls._instance

    async def initialize(self) -> bool:
        """从数据库初始化内存缓存（应用启动时调用一次）"""
        try:
            if ForumManager._initialized:
                return True
                
            logger.info("开始初始化ForumManager...")
            
            # 初始化计数器
            await Post.initialize_counter()
            await Comment.initialize_counter()
            
            # 清空现有内存缓存
            self.posts_dict.clear()
            self.comments_dict.clear()
            
            # 从数据库加载现有数据到内存
            posts_loaded = await self._load_posts_from_database()
            comments_loaded = await self._load_comments_from_database()
            
            # 在完成加载后，基于帖子内存对 UserManagement 中用户的 post_ids 进行对齐
            try:
                self._reconcile_user_post_relationships()
                logger.info("已基于帖子内存对齐用户的 post_ids")
            except Exception as reconcile_error:
                logger.warning(f"对齐用户 post_ids 时出现问题: {reconcile_error}")

            logger.info(f"ForumManager初始化完成: 加载了 {posts_loaded} 个帖子, {comments_loaded} 个评论")
            ForumManager._initialized = True
            return True
        except Exception as e:
            logger.error(f"ForumManager initialize failed: {e}")
            # 初始化失败时，重置状态
            ForumManager._initialized = False
            return False

    async def _load_posts_from_database(self):
        """从数据库加载帖子到内存缓存"""
        try:
            logger.info("开始从数据库加载帖子到内存...")
            posts_data = await Database.find("posts", {})
            loaded_count = 0
            
            logger.info(f"数据库中找到 {len(posts_data)} 个帖子")
            
            for post_data in posts_data:
                try:
                    post_id = post_data.get("_id")
                    if post_id:
                        # 重建Post实例
                        post = Post(
                            creator_user_id=str(post_data.get("creator_user_id")),
                            creator_user_name=post_data.get("creator_user_name", ""),
                            post_content=post_data.get("post_content", ""),
                            post_type=post_data.get("post_type", "text"),
                            post_category=post_data.get("post_category", ""),
                            tags=post_data.get("tags", []),
                            media_files=post_data.get("media_files", []),
                        )
                        # 恢复原有ID和状态
                        Post._post_counter = max(Post._post_counter, int(post_id))
                        post.post_id = int(post_id)
                        post.like_count = int(post_data.get("like_count", 0))
                        # 中文注释：liked_user_ids 改为字符串列表
                        post.liked_user_ids = [str(uid) for uid in list(post_data.get("liked_user_ids", []))]
                        post.comment_count = int(post_data.get("comment_count", 0))
                        post.view_count = int(post_data.get("view_count", 0))
                        post.comment_ids = list(post_data.get("comment_ids", []))
                        post.post_status = post_data.get("post_status", "published")
                        post.created_at = self._ensure_aware_datetime(post_data.get("created_at"))
                        post.updated_at = self._ensure_aware_datetime(post_data.get("updated_at"))
                        
                        self.posts_dict[post.post_id] = post
                        loaded_count += 1
                        
                        logger.debug(f"成功加载帖子 {post_id}: {post.post_content[:30]}...")
                except Exception as post_error:
                    logger.error(f"加载帖子 {post_data.get('_id', 'unknown')} 时出错: {post_error}")
                    continue
            
            logger.info(f"成功从数据库加载 {loaded_count} 个帖子到内存")
            return loaded_count
        except Exception as e:
            logger.error(f"从数据库加载帖子失败: {e}")
            raise  # 重新抛出异常，确保初始化失败时能被捕获

    async def _load_comments_from_database(self):
        """从数据库加载评论到内存缓存"""
        try:
            logger.info("开始从数据库加载评论到内存...")
            comments_data = await Database.find("comments", {})
            loaded_count = 0
            
            logger.info(f"数据库中找到 {len(comments_data)} 个评论")
            
            for comment_data in comments_data:
                try:
                    comment_id = comment_data.get("_id")
                    if comment_id:
                        # 重建Comment实例
                        comment = Comment(
                            commenter_user_id=str(comment_data.get("commenter_user_id")),
                            commenter_user_name=comment_data.get("commenter_user_name", ""),
                            post_id=comment_data.get("post_id"),
                            comment_content=comment_data.get("comment_content", ""),
                        )
                        # 恢复原有ID和状态
                        Comment._comment_counter = max(Comment._comment_counter, int(comment_id))
                        comment.comment_id = int(comment_id)
                        comment.like_count = int(comment_data.get("like_count", 0))
                        # 中文注释：liked_user_ids 改为字符串列表
                        comment.liked_user_ids = [str(uid) for uid in list(comment_data.get("liked_user_ids", []))]
                        comment.comment_status = comment_data.get("comment_status", "published")
                        comment.created_at = self._ensure_aware_datetime(comment_data.get("created_at"))
                        
                        self.comments_dict[comment.comment_id] = comment
                        loaded_count += 1
                        
                        logger.debug(f"成功加载评论 {comment_id}: {comment.comment_content[:30]}...")
                except Exception as comment_error:
                    logger.error(f"加载评论 {comment_data.get('_id', 'unknown')} 时出错: {comment_error}")
                    continue
            
            logger.info(f"成功从数据库加载 {loaded_count} 个评论到内存")
            return loaded_count
        except Exception as e:
            logger.error(f"从数据库加载评论失败: {e}")
            raise  # 重新抛出异常，确保初始化失败时能被捕获

    # ==================== 帖子相关 ====================
    async def create_post(
        self,
        creator_user_id: str,
        post_content: str,
        post_type: str,
        post_category: str,
        tags: Optional[List[str]],
        media_files: Optional[List[Dict[str, Any]]],
    ) -> Optional[int]:
        """发布新帖子，返回 `post_id`"""
        try:
            # 确保已初始化
            if not ForumManager._initialized:
                await self.initialize()
                
            user_manager = UserManagement()
            user = user_manager.get_user_instance(str(creator_user_id))
            if not user:
                logger.error(f"User {creator_user_id} not found when creating post")
                return None

            post = Post(
                creator_user_id=user.user_id,
                creator_user_name=user.telegram_user_name or str(user.user_id),
                post_content=post_content,
                post_type=post_type or "text",
                post_category=post_category or "",
                tags=tags or [],
                media_files=media_files or [],
            )

            # 只写入内存缓存，不直接写数据库
            self.posts_dict[post.post_id] = post

            # 维护用户的 post_ids（先更新内存，再尝试同步数据库；数据库不同步不影响流程）
            try:
                # 先更新内存，确保内存优先策略
                user.add_post(post.post_id)
                # 再尝试更新数据库（注意：Database.update_one 返回修改条数整数）
                modified_count = await Database.update_one(
                    "users",
                    {"_id": user.user_id},
                    {"$addToSet": {"post_ids": post.post_id}},
                )
                if modified_count > 0:
                    logger.info(f"用户 {user.user_id} 的 post_ids 已写入数据库，添加帖子 {post.post_id}")
                else:
                    logger.warning(
                        f"数据库未更新用户 {user.user_id} 的 post_ids（可能用户文档尚未创建，将由定时任务写入）"
                    )
                    
            except Exception as e:
                logger.error(f"更新用户 {user.user_id} 的 post_ids 失败: {e}")
                logger.info(f"已确保内存中用户 {user.user_id} 的 post_ids 包含 {post.post_id}")

            return post.post_id
        except Exception as e:
            logger.error(f"create_post error: {e}")
            return None

    async def get_posts_list(
        self,
        user_id: str,
        sort_type: str,
        page: int,
        page_size: int,
    ) -> Dict[str, Any]:
        """获取帖子列表，按最新或热门排序"""
        try:
            # 确保已初始化
            if not ForumManager._initialized:
                logger.info("ForumManager未初始化，开始初始化...")
                await self.initialize()
                
            # 检查内存缓存状态
            logger.debug(f"内存缓存状态: posts_dict大小={len(self.posts_dict)}, comments_dict大小={len(self.comments_dict)}")
            
            # 从内存缓存获取数据
            published_posts = [post for post in self.posts_dict.values() if post.post_status == "published"]
            logger.debug(f"找到 {len(published_posts)} 个已发布的帖子")

            if not published_posts:
                logger.warning("内存缓存中没有已发布的帖子，尝试重新初始化...")
                await self.force_reinitialize()
                published_posts = [post for post in self.posts_dict.values() if post.post_status == "published"]
                logger.debug(f"重新初始化后找到 {len(published_posts)} 个已发布的帖子")

            if sort_type == "hot":
                # 内存排序（确保比较的时间为 aware datetime）
                published_posts.sort(
                    key=lambda x: (
                        x.like_count,
                        x.comment_count,
                        self._ensure_aware_datetime(x.created_at) or datetime.min.replace(tzinfo=timezone.utc),
                    ),
                    reverse=True,
                )
            else:
                # 按时间倒序（确保比较的时间为 aware datetime）
                published_posts.sort(
                    key=lambda x: self._ensure_aware_datetime(x.created_at) or datetime.min.replace(tzinfo=timezone.utc),
                    reverse=True,
                )

            skip = max(0, (page - 1) * page_size)
            end_index = skip + page_size
            page_posts = published_posts[skip:end_index]

            # 预取用户点赞集合（用于 is_liked）
            user_doc = await Database.find_one("users", {"_id": str(user_id)})
            liked_post_ids = set(user_doc.get("liked_post_ids", [])) if user_doc else set()

            posts: List[Dict[str, Any]] = []
            for post in page_posts:
                posts.append(
                    {
                        "post_id": post.post_id,
                        "post_content": post.post_content,
                        "post_type": post.post_type,
                        "creator": {
                            "user_id": post.creator_user_id,
                            "user_name": post.creator_user_name
                        },
                        "media_files": post.media_files,
                        "stats": {
                            "like_count": post.like_count,
                            "comment_count": post.comment_count,
                            "view_count": post.view_count,
                        },
                        "is_liked": post.post_id in liked_post_ids,
                        "post_category": post.post_category,
                        "tags": post.tags,
                        "created_at": post.created_at,
                        "time_display": self._format_time_display(post.created_at),
                    }
                )

            # 判断是否还有更多
            has_more = end_index < len(published_posts)
            
            logger.info(f"成功获取帖子列表: {len(posts)} 个帖子，还有更多: {has_more}")
            return {"success": True, "posts": posts, "has_more": has_more}
        except Exception as e:
            logger.error(f"get_posts_list error: {e}")
            return {"success": False, "posts": [], "has_more": False}

    async def toggle_post_like(self, user_id: str, post_id: int, action: str) -> Dict[str, Any]:
        """帖子点赞/取消点赞"""
        try:
            # 确保已初始化
            if not ForumManager._initialized:
                await self.initialize()
                
            # 从内存缓存获取帖子
            post = self.posts_dict.get(post_id)
            if not post:
                return {"success": False, "message": "post not found"}

            if action == "like":
                # 只更新内存，不写数据库
                if str(user_id) not in post.liked_user_ids:
                    post.liked_user_ids.append(str(user_id))
                    post.like_count += 1
                    post.updated_at = datetime.now(timezone.utc)
                # 更新数据库
                modified_count = await Database.update_one("users", {"_id": str(user_id)}, {"$addToSet": {"liked_post_ids": post_id}})
                
                if modified_count > 0:
                    # 同步更新内存中的用户对象
                    user_manager = UserManagement()
                    user = user_manager.get_user_instance(str(user_id))
                    if user:
                        user.add_liked_post(post_id)
                        logger.info(f"用户 {user_id} 的 liked_post_ids 已更新，添加帖子 {post_id}")
                    else:
                        logger.warning(f"用户 {user_id} 在内存中不存在")
                else:
                    logger.warning(f"用户 {user_id} 的 liked_post_ids 更新失败")
                    
                is_liked = True
            else:
                # 只更新内存，不写数据库
                if str(user_id) in post.liked_user_ids:
                    post.liked_user_ids.remove(str(user_id))
                    post.like_count = max(0, post.like_count - 1)
                    post.updated_at = datetime.now(timezone.utc)
                # 更新数据库
                modified_count = await Database.update_one("users", {"_id": str(user_id)}, {"$pull": {"liked_post_ids": post_id}})
                
                if modified_count > 0:
                    # 同步更新内存中的用户对象
                    user_manager = UserManagement()
                    user = user_manager.get_user_instance(str(user_id))
                    if user:
                        user.remove_liked_post(post_id)
                        logger.info(f"用户 {user_id} 的 liked_post_ids 已更新，移除帖子 {post_id}")
                    else:
                        logger.warning(f"用户 {user_id} 在内存中不存在")
                else:
                    logger.warning(f"用户 {user_id} 的 liked_post_ids 更新失败")
                    
                is_liked = False

            return {"success": True, "action": action, "new_like_count": post.like_count, "is_liked": is_liked}
        except Exception as e:
            logger.error(f"toggle_post_like error: {e}")
            return {"success": False, "message": str(e)}

    async def search_posts(self, user_id: str, search_query: str, page: int, page_size: int) -> Dict[str, Any]:
        """搜索帖子（最简：content 文本匹配 + 标签匹配）"""
        try:
            # 确保已初始化
            if not ForumManager._initialized:
                await self.initialize()
                
            # 从内存缓存搜索
            published_posts = [post for post in self.posts_dict.values() if post.post_status == "published"]
            
            # 内存搜索：内容匹配或标签匹配
            search_query_lower = search_query.lower()
            matched_posts = []
            for post in published_posts:
                if (search_query_lower in post.post_content.lower() or
                    any(search_query_lower in tag.lower() for tag in post.tags)):
                    matched_posts.append(post)

            skip = max(0, (page - 1) * page_size)
            end_index = skip + page_size
            # 按时间倒序（确保比较的时间为 aware datetime）
            matched_posts.sort(
                key=lambda x: self._ensure_aware_datetime(x.created_at) or datetime.min.replace(tzinfo=timezone.utc),
                reverse=True,
            )
            page_posts = matched_posts[skip:end_index]

            user_doc = await Database.find_one("users", {"_id": str(user_id)})
            liked_post_ids = set(user_doc.get("liked_post_ids", [])) if user_doc else set()

            posts: List[Dict[str, Any]] = []
            for post in page_posts:
                posts.append(
                    {
                        "post_id": post.post_id,
                        "post_content": post.post_content,
                        "post_type": post.post_type,
                        "creator": {
                            "user_id": post.creator_user_id,
                            "user_name": post.creator_user_name
                        },
                        "media_files": post.media_files,
                        "stats": {
                            "like_count": post.like_count,
                            "comment_count": post.comment_count,
                            "view_count": post.view_count,
                        },
                        "is_liked": post.post_id in liked_post_ids,
                        "post_category": post.post_category,
                        "tags": post.tags,
                        "created_at": post.created_at,
                        "time_display": self._format_time_display(post.created_at),
                    }
                )

            has_more = end_index < len(matched_posts)

            return {"success": True, "posts": posts, "has_more": has_more}
        except Exception as e:
            logger.error(f"search_posts error: {e}")
            return {"success": False, "posts": [], "has_more": False}

    # ==================== 评论相关 ====================
    async def get_post_detail(self, user_id: str, post_id: int) -> Dict[str, Any]:
        """获取单个帖子详情（内存优先）"""
        try:
            if not ForumManager._initialized:
                await self.initialize()

            post = self.posts_dict.get(post_id)
            if not post:
                return {"success": False, "post": None, "message": "post not found"}

            user_doc = await Database.find_one("users", {"_id": str(user_id)})
            liked_post_ids = set(user_doc.get("liked_post_ids", [])) if user_doc else set()

            post_item = {
                "post_id": post.post_id,
                "post_content": post.post_content,
                "post_type": post.post_type,
                "creator": {"user_id": post.creator_user_id, "user_name": post.creator_user_name},
                "media_files": post.media_files,
                "stats": {
                    "like_count": post.like_count,
                    "comment_count": post.comment_count,
                    "view_count": post.view_count,
                },
                "is_liked": post.post_id in liked_post_ids,
                "post_category": post.post_category,
                "tags": post.tags,
                "created_at": post.created_at,
                "time_display": self._format_time_display(post.created_at),
            }

            return {"success": True, "post": post_item}
        except Exception as e:
            logger.error(f"get_post_detail error: {e}")
            return {"success": False, "post": None, "message": "internal error"}
    async def create_comment(self, user_id: str, post_id: int, comment_content: str) -> Dict[str, Any]:
        """发布评论（极简）"""
        try:
            # 确保已初始化
            if not ForumManager._initialized:
                await self.initialize()
                
            user_manager = UserManagement()
            user = user_manager.get_user_instance(str(user_id))
            if not user:
                return {"success": False, "message": "user not found"}

            # 从内存缓存获取帖子
            post = self.posts_dict.get(post_id)
            if not post:
                return {"success": False, "message": "post not found"}

            comment = Comment(
                commenter_user_id=user.user_id,
                commenter_user_name=user.telegram_user_name or str(user.user_id),
                post_id=post_id,
                comment_content=comment_content,
            )
            # 只写入内存缓存，不直接写数据库
            self.comments_dict[comment.comment_id] = comment

            # 更新帖子的评论计数和评论ID列表（内存）
            post.comment_ids.append(comment.comment_id)
            post.comment_count += 1
            post.updated_at = datetime.now(timezone.utc)

            return {"success": True, "comment_id": comment.comment_id, "message": "评论发布成功"}
        except Exception as e:
            logger.error(f"create_comment error: {e}")
            return {"success": False, "message": str(e)}

    async def get_post_comments(self, post_id: int, user_id: str, page: int, page_size: int) -> Dict[str, Any]:
        """获取评论列表（极简）"""
        try:
            skip = max(0, (page - 1) * page_size)
            end_index = skip + page_size
            
            # 从内存缓存获取评论
            post_comments = [comment for comment in self.comments_dict.values() 
                           if comment.post_id == post_id and comment.comment_status == "published"]
            
            # 按时间正序
            post_comments.sort(key=lambda x: x.created_at)
            page_comments = post_comments[skip:end_index]

            comments: List[Dict[str, Any]] = []
            for comment in page_comments:
                comments.append(
                    {
                        "comment_id": comment.comment_id,
                        "comment_content": comment.comment_content,
                        "commenter": {
                            "user_id": comment.commenter_user_id,
                            "user_name": comment.commenter_user_name,
                        },
                        "like_count": comment.like_count,
                        "is_liked": str(user_id) in set(comment.liked_user_ids),
                        "created_at": comment.created_at,
                    }
                )

            has_more = end_index < len(post_comments)

            return {"success": True, "comments": comments, "has_more": has_more}
        except Exception as e:
            logger.error(f"get_post_comments error: {e}")
            return {"success": False, "comments": [], "has_more": False}

    async def toggle_comment_like(self, user_id: str, comment_id: int, action: str) -> Dict[str, Any]:
        """评论点赞/取消点赞"""
        try:
            # 确保已初始化
            if not ForumManager._initialized:
                await self.initialize()
                
            # 从内存缓存获取评论
            comment = self.comments_dict.get(comment_id)
            if not comment:
                return {"success": False, "message": "comment not found"}

            if action == "like":
                # 只更新内存，不写数据库
                if str(user_id) not in comment.liked_user_ids:
                    comment.liked_user_ids.append(str(user_id))
                    comment.like_count += 1
                is_liked = True
            else:
                # 只更新内存，不写数据库
                if str(user_id) in comment.liked_user_ids:
                    comment.liked_user_ids.remove(str(user_id))
                    comment.like_count = max(0, comment.like_count - 1)
                is_liked = False

            return {"success": True, "action": action, "new_like_count": comment.like_count, "is_liked": is_liked}
        except Exception as e:
            logger.error(f"toggle_comment_like error: {e}")
            return {"success": False, "message": str(e)}

    # ==================== 管理方法 ====================
    async def force_reinitialize(self) -> bool:
        """强制重新初始化（用于恢复）"""
        try:
            logger.info("强制重新初始化ForumManager...")
            ForumManager._initialized = False
            return await self.initialize()
        except Exception as e:
            logger.error(f"强制重新初始化失败: {e}")
            return False
    
    def get_memory_status(self) -> Dict[str, Any]:
        """获取内存状态信息"""
        return {
            "initialized": ForumManager._initialized,
            "posts_count": len(self.posts_dict),
            "comments_count": len(self.comments_dict),
            "post_ids": list(self.posts_dict.keys()),
            "comment_ids": list(self.comments_dict.keys())
        }
    
    # ==================== 数据库同步方法 ====================
    async def save_to_database(self) -> bool:
        """将内存数据同步到数据库（供自动保存任务调用）"""
        try:
            # 保存前再次对齐一次用户与帖子关系，确保落库一致
            try:
                self._reconcile_user_post_relationships()
            except Exception as reconcile_error:
                logger.warning(f"保存前对齐用户 post_ids 失败: {reconcile_error}")

            success_count = 0
            total_count = len(self.posts_dict) + len(self.comments_dict)
            
            # 保存所有帖子
            for post in self.posts_dict.values():
                try:
                    post_dict = await post.to_dict()
                    existing = await Database.find_one("posts", {"_id": post.post_id})
                    if existing:
                        await Database.update_one(
                            "posts",
                            {"_id": post.post_id},
                            {"$set": {k: v for k, v in post_dict.items() if k != "_id"}}
                        )
                    else:
                        await Database.insert_one("posts", post_dict)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to save post {post.post_id}: {e}")
                    continue
            
            # 保存所有评论
            for comment in self.comments_dict.values():
                try:
                    comment_dict = await comment.to_dict()
                    existing = await Database.find_one("comments", {"_id": comment.comment_id})
                    if existing:
                        await Database.update_one(
                            "comments",
                            {"_id": comment.comment_id},
                            {"$set": {k: v for k, v in comment_dict.items() if k != "_id"}}
                        )
                    else:
                        await Database.insert_one("comments", comment_dict)
                    success_count += 1
                except Exception as e:
                    logger.error(f"Failed to save comment {comment.comment_id}: {e}")
                    continue
            
            logger.info(f"Saved {success_count}/{total_count} forum items to database")
            return success_count == total_count
        except Exception as e:
            logger.error(f"Failed to save forum data to database: {e}")
            return False

    # ==================== 工具方法 ====================
    def _format_time_display(self, dt: Any) -> str:
        """将 UTC 时间格式化为 MM-DD HH:mm（前端示例要求）"""
        try:
            if not dt:
                return ""
            if isinstance(dt, datetime):
                d = dt
            else:
                # 尝试解析字符串
                d = datetime.fromisoformat(str(dt).replace("Z", "+00:00"))
            return d.strftime("%m-%d %H:%M")
        except Exception:
            return ""

    def _ensure_aware_datetime(self, dt: Any) -> Optional[datetime]:
        """将任意输入规范为带UTC时区的 aware datetime；无法解析则返回 None"""
        if dt is None:
            return None
        try:
            if isinstance(dt, datetime):
                if dt.tzinfo is None:
                    return dt.replace(tzinfo=timezone.utc)
                return dt
            parsed = datetime.fromisoformat(str(dt).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed
        except Exception:
            return None

    # ==================== 内部对齐方法 ====================
    def _reconcile_user_post_relationships(self) -> None:
        """
        基于内存中的帖子，确保 UserManagement 内存里的用户 post_ids 一致。
        - 内存优先：只改内存，不直接写库；持久化交给定时保存任务
        """
        user_manager = UserManagement()
        for post in self.posts_dict.values():
            user = user_manager.get_user_instance(post.creator_user_id)
            if user is None:
                # 如果用户不在内存，这里跳过（上层启动流程应先初始化 UserManagement）
                continue
            if post.post_id not in getattr(user, "post_ids", []):
                user.add_post(post.post_id)
                logger.debug(
                    f"对齐用户 {user.user_id} 的 post_ids，补充帖子 {post.post_id}")


