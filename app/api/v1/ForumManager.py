from fastapi import APIRouter, Depends, HTTPException
from app.schemas.ForumManager import (
    GetPostsListRequest, GetPostsListResponse,
    CreatePostRequest, CreatePostResponse,
    SearchPostsRequest, SearchPostsResponse,
    TogglePostLikeRequest, TogglePostLikeResponse,
    CreateCommentRequest, CreateCommentResponse,
    GetPostCommentsRequest, GetPostCommentsResponse,
    ToggleCommentLikeRequest, ToggleCommentLikeResponse,
    GetPostDetailRequest, GetPostDetailResponse,
)
from app.services.https.ForumManager import ForumManager as ForumService
from app.utils.my_logger import MyLogger

router = APIRouter(prefix="/ForumManager", tags=["forum"])
logger = MyLogger(__name__)


def get_forum_service():
    return ForumService()


@router.post("/get_posts_list", response_model=GetPostsListResponse, summary="获取帖子列表")
async def get_posts_list(request: GetPostsListRequest, forum: ForumService = Depends(get_forum_service)):
    """获取帖子列表（latest/hot）"""
    try:
        result = await forum.get_posts_list(
            user_id=request.user_id,
            sort_type=request.sort_type,
            page=request.page,
            page_size=request.page_size,
        )
        return GetPostsListResponse(**result)
    except Exception as e:
        logger.error(f"get_posts_list error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


@router.post("/create_post", response_model=CreatePostResponse, summary="发布新帖子")
async def create_post(request: CreatePostRequest, forum: ForumService = Depends(get_forum_service)):
    """发布新帖子"""
    try:
        post_id = await forum.create_post(
            creator_user_id=request.creator_user_id,
            post_content=request.post_content,
            post_type=request.post_type,
            post_category=request.post_category or "",
            tags=request.tags or [],
            media_files=[mf.dict() for mf in request.media_files] if request.media_files else [],
        )
        if not post_id:
            return CreatePostResponse(success=False, message="帖子发布失败")
        return CreatePostResponse(success=True, post_id=post_id, message="帖子发布成功")
    except Exception as e:
        logger.error(f"create_post error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


@router.post("/search_posts", response_model=SearchPostsResponse, summary="搜索帖子")
async def search_posts(request: SearchPostsRequest, forum: ForumService = Depends(get_forum_service)):
    try:
        result = await forum.search_posts(
            user_id=request.user_id,
            search_query=request.search_query,
            page=request.page,
            page_size=request.page_size,
        )
        return SearchPostsResponse(**result)
    except Exception as e:
        logger.error(f"search_posts error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


@router.post("/toggle_post_like", response_model=TogglePostLikeResponse, summary="帖子点赞/取消点赞")
async def toggle_post_like(request: TogglePostLikeRequest, forum: ForumService = Depends(get_forum_service)):
    try:
        result = await forum.toggle_post_like(
            user_id=request.user_id,
            post_id=request.post_id,
            action=request.action,
        )
        return TogglePostLikeResponse(**result)
    except Exception as e:
        logger.error(f"toggle_post_like error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


@router.post("/create_comment", response_model=CreateCommentResponse, summary="发布评论")
async def create_comment(request: CreateCommentRequest, forum: ForumService = Depends(get_forum_service)):
    try:
        result = await forum.create_comment(
            user_id=request.user_id,
            post_id=request.post_id,
            comment_content=request.comment_content,
        )
        return CreateCommentResponse(**result)
    except Exception as e:
        logger.error(f"create_comment error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


@router.post("/get_post_detail", response_model=GetPostDetailResponse, summary="获取帖子详情（新增）")
async def get_post_detail(request: GetPostDetailRequest, forum: ForumService = Depends(get_forum_service)):
    try:
        result = await forum.get_post_detail(user_id=request.user_id, post_id=request.post_id)
        return GetPostDetailResponse(**result)
    except Exception as e:
        logger.error(f"get_post_detail error: {e}")
        raise HTTPException(status_code=500, detail="internal error")

@router.post("/get_post_comments", response_model=GetPostCommentsResponse, summary="获取帖子评论列表")
async def get_post_comments(request: GetPostCommentsRequest, forum: ForumService = Depends(get_forum_service)):
    try:
        result = await forum.get_post_comments(
            post_id=request.post_id,
            user_id=request.user_id,
            page=request.page,
            page_size=request.page_size,
        )
        return GetPostCommentsResponse(**result)
    except Exception as e:
        logger.error(f"get_post_comments error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


@router.post("/toggle_comment_like", response_model=ToggleCommentLikeResponse, summary="评论点赞/取消点赞")
async def toggle_comment_like(request: ToggleCommentLikeRequest, forum: ForumService = Depends(get_forum_service)):
    try:
        result = await forum.toggle_comment_like(
            user_id=request.user_id,
            comment_id=request.comment_id,
            action=request.action,
        )
        return ToggleCommentLikeResponse(**result)
    except Exception as e:
        logger.error(f"toggle_comment_like error: {e}")
        raise HTTPException(status_code=500, detail="internal error")


