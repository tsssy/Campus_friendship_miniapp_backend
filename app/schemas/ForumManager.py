from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ========== 通用结构 ==========
class MediaFile(BaseModel):
    """媒体文件（简化）"""
    file_type: str = Field(..., description="文件类型：image 等")
    file_url: str = Field(..., description="文件地址（占位即可）")
    thumbnail_url: Optional[str] = Field(None, description="缩略图地址（可缺省）")


class CreatorInfo(BaseModel):
    user_id: int = Field(..., description="创建者用户ID")
    user_name: str = Field(..., description="创建者用户名")


class PostStats(BaseModel):
    like_count: int = Field(0, description="点赞数")
    comment_count: int = Field(0, description="评论数")
    view_count: int = Field(0, description="浏览数")


class PostItem(BaseModel):
    post_id: int
    post_content: str
    post_type: str
    creator: CreatorInfo
    media_files: List[MediaFile] = Field(default_factory=list)
    stats: PostStats
    is_liked: bool = False
    post_category: str = ""
    tags: List[str] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    time_display: str = ""


# ========== 请求/响应模型 ==========

# 2.1.1 获取帖子列表
class GetPostsListRequest(BaseModel):
    user_id: int = Field(..., description="用户ID")
    sort_type: str = Field("latest", description="排序类型：latest/hot")
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class GetPostsListResponse(BaseModel):
    success: bool
    posts: List[PostItem]
    has_more: bool


# 2.1.2 发布新帖子
class CreatePostRequest(BaseModel):
    creator_user_id: int = Field(..., description="创建者用户ID")
    post_content: str = Field(..., description="帖子内容")
    post_type: str = Field("text", description="帖子类型：text/image/text_image")
    post_category: Optional[str] = Field("", description="帖子分类")
    tags: List[str] = Field(default_factory=list, description="标签（最多3个）")
    media_files: List[MediaFile] = Field(default_factory=list, description="媒体文件列表")


class CreatePostResponse(BaseModel):
    success: bool
    post_id: Optional[int] = None
    message: Optional[str] = None


# 2.1.3 搜索帖子
class SearchPostsRequest(BaseModel):
    user_id: int
    search_query: str
    page: int = 1
    page_size: int = 20


class SearchPostsResponse(BaseModel):
    success: bool
    posts: List[PostItem]
    has_more: bool


# 2.1.4 帖子点赞/取消点赞
class TogglePostLikeRequest(BaseModel):
    user_id: int
    post_id: int
    action: str = Field(..., description="like 或 unlike")


class TogglePostLikeResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    new_like_count: Optional[int] = None
    is_liked: Optional[bool] = None
    message: Optional[str] = None


# 2.1.5 发布评论
class CreateCommentRequest(BaseModel):
    user_id: int
    post_id: int
    comment_content: str


class CreateCommentResponse(BaseModel):
    success: bool
    comment_id: Optional[int] = None
    message: Optional[str] = None


# 2.1.6 获取帖子评论列表
class GetPostCommentsRequest(BaseModel):
    post_id: int
    user_id: int
    page: int = 1
    page_size: int = 20


class CommentItem(BaseModel):
    comment_id: int
    comment_content: str
    commenter: CreatorInfo
    like_count: int
    is_liked: bool
    created_at: Optional[datetime] = None


class GetPostCommentsResponse(BaseModel):
    success: bool
    comments: List[CommentItem]
    has_more: bool


# 2.1.7 评论点赞/取消点赞
class ToggleCommentLikeRequest(BaseModel):
    user_id: int
    comment_id: int
    action: str = Field(..., description="like 或 unlike")


class ToggleCommentLikeResponse(BaseModel):
    success: bool
    action: Optional[str] = None
    new_like_count: Optional[int] = None
    is_liked: Optional[bool] = None
    message: Optional[str] = None


# 2.1.8 获取帖子详情（新增）
class GetPostDetailRequest(BaseModel):
    """获取单个帖子详情的请求体"""
    user_id: int = Field(..., description="请求者用户ID（用于计算是否已点赞）")
    post_id: int = Field(..., description="帖子ID")


class GetPostDetailResponse(BaseModel):
    """获取单个帖子详情的响应体"""
    success: bool
    post: Optional[PostItem] = None
    message: Optional[str] = None

