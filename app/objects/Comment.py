from datetime import datetime, timezone
from typing import List, Dict, Any

from app.core.database import Database
from app.utils.my_logger import MyLogger

logger = MyLogger("Comment")


class Comment:
    """评论对象（极简版，无回复层级）
    - 负责持久化自身到 `comments` 集合
    - 使用 `_id` 为递增整型主键（由数据库中最大 `_id` 初始化）
    """

    _comment_counter: int = 0
    _initialized: bool = False

    @classmethod
    async def initialize_counter(cls) -> None:
        """从数据库初始化评论计数器"""
        if cls._initialized:
            return
        try:
            comments = await Database.find("comments", sort=[("_id", -1)], limit=1)
            if comments:
                max_id = comments[0]["_id"]
                cls._comment_counter = int(max_id)
                logger.info(f"Comment counter initialized from database: starting from {max_id}")
            else:
                cls._comment_counter = 0
                logger.info("No existing comments found, starting counter from 0")
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize comment counter: {e}")
            import time
            cls._comment_counter = int(time.time() * 1000)
            cls._initialized = True

    def __init__(self, commenter_user_id: int, commenter_user_name: str, post_id: int, comment_content: str) -> None:
        # 确保计数器已初始化
        if not Comment._initialized:
            raise RuntimeError("Comment counter not initialized. Call Comment.initialize_counter() first.")

        Comment._comment_counter += 1
        self.comment_id: int = Comment._comment_counter

        # 基础内容
        self.post_id: int = post_id
        self.comment_content: str = comment_content
        self.commenter_user_id: int = commenter_user_id
        self.commenter_user_name: str = commenter_user_name

        # 互动数据
        self.like_count: int = 0
        self.liked_user_ids: List[int] = []

        # 状态与时间
        self.comment_status: str = "published"
        self.created_at = datetime.now(timezone.utc)

        logger.info(f"Created comment {self.comment_id} for post {self.post_id}")

    async def to_dict(self) -> Dict[str, Any]:
        return {
            "_id": self.comment_id,
            "post_id": self.post_id,
            "comment_content": self.comment_content,
            "commenter_user_id": self.commenter_user_id,
            "commenter_user_name": self.commenter_user_name,
            "like_count": self.like_count,
            "liked_user_ids": self.liked_user_ids,
            "comment_status": self.comment_status,
            "created_at": self.created_at,
        }

    async def save_to_database(self) -> bool:
        """保存评论到数据库（存在则更新，不存在则插入）"""
        try:
            comment_dict = await self.to_dict()
            existing = await Database.find_one("comments", {"_id": self.comment_id})
            if existing:
                await Database.update_one(
                    "comments",
                    {"_id": self.comment_id},
                    {"$set": {k: v for k, v in comment_dict.items() if k != "_id"}},
                )
            else:
                await Database.insert_one("comments", comment_dict)
            logger.info(f"Saved comment {self.comment_id} to database")
            return True
        except Exception as e:
            logger.error(f"Error saving comment {self.comment_id}: {e}")
            return False

    async def add_like(self, user_id: int) -> bool:
        """添加点赞"""
        if user_id not in self.liked_user_ids:
            self.liked_user_ids.append(user_id)
            self.like_count += 1
            return await self.save_to_database()
        return True

    async def remove_like(self, user_id: int) -> bool:
        """取消点赞"""
        if user_id in self.liked_user_ids:
            self.liked_user_ids.remove(user_id)
            self.like_count = max(0, self.like_count - 1)
            return await self.save_to_database()
        return True


