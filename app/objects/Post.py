from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from app.core.database import Database
from app.utils.my_logger import MyLogger

logger = MyLogger("Post")


class Post:
    """帖子对象（最简版）
    - 负责持久化自身到 `posts` 集合
    - 使用 `_id` 为递增整型主键（由数据库中最大 `_id` 初始化）
    """

    _post_counter: int = 0
    _initialized: bool = False

    @classmethod
    async def initialize_counter(cls) -> None:
        """从数据库初始化帖子计数器
        - 读取 `posts` 集合中最大的 `_id` 作为起始值
        - 若集合为空，从 0 开始
        - 若异常，回退为毫秒时间戳，避免冲突
        """
        if cls._initialized:
            return

        try:
            posts = await Database.find("posts", sort=[("_id", -1)], limit=1)
            if posts:
                max_id = posts[0]["_id"]
                cls._post_counter = int(max_id)
                logger.info(f"Post counter initialized from database: starting from {max_id}")
            else:
                cls._post_counter = 0
                logger.info("No existing posts found, starting counter from 0")
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize post counter: {e}")
            import time
            cls._post_counter = int(time.time() * 1000)
            cls._initialized = True

    def __init__(
        self,
        creator_user_id: str,
        creator_user_name: str,
        post_content: str,
        post_type: str = "text",
        post_category: str = "",
        tags: Optional[List[str]] = None,
        media_files: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        # 确保已初始化计数器
        if not Post._initialized:
            raise RuntimeError("Post counter not initialized. Call Post.initialize_counter() first.")

        Post._post_counter += 1
        self.post_id: int = Post._post_counter

        # 基础内容
        self.post_content: str = post_content
        self.post_type: str = post_type  # text | image | text_image
        # 中文注释：发布者用户ID改为字符串（openid），但贴子本身ID仍为数字
        self.creator_user_id: str = creator_user_id
        self.creator_user_name: str = creator_user_name

        # 媒体与分类
        self.media_files: List[Dict[str, Any]] = media_files or []
        self.post_category: str = post_category
        self.tags: List[str] = (tags or [])[:3]

        # 互动数据
        self.like_count: int = 0
        self.comment_count: int = 0
        self.view_count: int = 0
        # 中文注释：点赞用户ID列表改为字符串列表
        self.liked_user_ids: List[str] = []
        self.comment_ids: List[int] = []

        # 状态与时间
        self.post_status: str = "published"  # published | deleted
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = self.created_at

        logger.info(f"Created post {self.post_id} by user {self.creator_user_id}")

    async def to_dict(self) -> Dict[str, Any]:
        """转换为可写入数据库的字典"""
        return {
            "_id": self.post_id,
            "post_content": self.post_content,
            "post_type": self.post_type,
            "creator_user_id": self.creator_user_id,
            "creator_user_name": self.creator_user_name,
            "media_files": self.media_files,
            "like_count": self.like_count,
            "comment_count": self.comment_count,
            "view_count": self.view_count,
            "liked_user_ids": self.liked_user_ids,
            "comment_ids": self.comment_ids,
            "post_category": self.post_category,
            "tags": self.tags,
            "post_status": self.post_status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    async def save_to_database(self) -> bool:
        """保存帖子到数据库（存在则更新，不存在则插入）"""
        try:
            post_dict = await self.to_dict()
            existing = await Database.find_one("posts", {"_id": self.post_id})
            if existing:
                await Database.update_one(
                    "posts",
                    {"_id": self.post_id},
                    {"$set": {k: v for k, v in post_dict.items() if k != "_id"}},
                )
            else:
                await Database.insert_one("posts", post_dict)
            logger.info(f"Saved post {self.post_id} to database")
            return True
        except Exception as e:
            logger.error(f"Error saving post {self.post_id}: {e}")
            return False

    async def add_like(self, user_id: str) -> bool:
        """添加点赞（同时更新计数）"""
        if user_id not in self.liked_user_ids:
            self.liked_user_ids.append(user_id)
            self.like_count += 1
            self.updated_at = datetime.now(timezone.utc)
            return await self.save_to_database()
        return True

    async def remove_like(self, user_id: str) -> bool:
        """取消点赞（同时更新计数）"""
        if user_id in self.liked_user_ids:
            self.liked_user_ids.remove(user_id)
            self.like_count = max(0, self.like_count - 1)
            self.updated_at = datetime.now(timezone.utc)
            return await self.save_to_database()
        return True

    async def add_comment(self, comment_id: int) -> bool:
        """新增评论（同时更新计数）"""
        if comment_id not in self.comment_ids:
            self.comment_ids.append(comment_id)
            self.comment_count += 1
            self.updated_at = datetime.now(timezone.utc)
            return await self.save_to_database()
        return True


