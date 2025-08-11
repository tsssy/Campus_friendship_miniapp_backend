# 简化版论坛系统设计方案

## 项目概述

基于现有用户系统，设计简化版论坛功能，专注于核心的帖子浏览、发布、互动和搜索功能。暂不包含用户论坛资料管理，后续可通过profile页面扩展。

## 一、数据库结构设计

### 1.1 扩展现有Users集合（最小化扩展）

在现有的`users`集合中仅新增必要的论坛字段：

```javascript
// users 集合（最小化扩展）
{
  "_id": 123456789,  // 现有的telegram_user_id
  "telegram_user_name": "john_doe",  // 现有字段
  "gender": 1,  // 现有字段
  "age": 25,  // 现有字段
  "target_gender": 2,  // 现有字段
  "user_personality_summary": "I love traveling!",  // 现有字段
  "match_ids": [1001, 1002],  // 现有字段
  
  // 新增最少必要的论坛字段
  "post_ids": [2001, 2002, 2003],  // 用户发布的帖子ID列表
  "liked_post_ids": [3001, 3002]   // 用户点赞的帖子ID列表
}
```

### 1.2 Posts集合（帖子数据库）

```javascript
// posts 集合
{
  "_id": post_id,  // 帖子ID作为主键
  "post_content": "清清小助手\n新年指南\n[图片]",  // 帖子内容
  "post_type": "text_image",  // 帖子类型：text, image, text_image
  "creator_user_id": 123456,  // 创建者用户ID
  "creator_user_name": "清清小助手",  // 创建者用户名（冗余存储，提高查询效率）
  
  // 媒体文件信息（简化）
  "media_files": [
    {
      "file_type": "image",  // image
      "file_url": "https://example.com/image1.jpg",
      "thumbnail_url": "https://example.com/thumb1.jpg"
    }
  ],
  
  // 互动数据
  "like_count": 15,  // 点赞数
  "comment_count": 3,  // 评论数
  "view_count": 128,  // 浏览数
  "liked_user_ids": [789012, 345678, 901234],  // 点赞用户ID列表
  "comment_ids": [4001, 4002, 4003],  // 评论ID列表
  
  // 帖子分类和状态
  "post_category": "生活",  // 帖子分类：生活、学习、娱乐、科技等
  "tags": ["新年", "指南", "生活"],  // 标签
  "post_status": "published",  // published, deleted
  
  // 时间信息
  "created_at": "2024-01-05T16:34:00Z",
  "updated_at": "2024-01-05T16:34:00Z"
}
```

### 1.3 Comments集合（评论数据库）

```javascript
// comments 集合
{
  "_id": comment_id,  // 评论ID作为主键
  "post_id": 2001,  // 所属帖子ID
  "comment_content": "很有用的指南，谢谢分享！",  // 评论内容
  "commenter_user_id": 789012,  // 评论者用户ID
  "commenter_user_name": "张三",  // 评论者用户名
  
  // 回复相关（简化）
  "parent_comment_id": null,  // 父评论ID（用于回复评论）
  "reply_to_user_id": null,  // 回复的用户ID
  "reply_to_user_name": null,  // 回复的用户名
  
  // 互动数据
  "like_count": 5,  // 评论点赞数
  "liked_user_ids": [123456, 345678],  // 点赞用户ID列表
  
  // 评论状态
  "comment_status": "published",  // published, deleted
  
  // 时间信息
  "created_at": "2024-01-05T17:00:00Z"
}
```

### 1.4 数据库索引设计

```javascript
// posts 集合索引
db.posts.createIndex({"_id": 1}, {unique: true})
db.posts.createIndex({"creator_user_id": 1})
db.posts.createIndex({"post_status": 1, "created_at": -1})  // 按状态和时间排序
db.posts.createIndex({"post_category": 1, "created_at": -1})  // 分类浏览
db.posts.createIndex({"like_count": -1, "created_at": -1})  // 热门排序
db.posts.createIndex({"post_content": "text", "tags": "text"})  // 全文搜索

// comments 集合索引
db.comments.createIndex({"_id": 1}, {unique: true})
db.comments.createIndex({"post_id": 1, "created_at": 1})  // 按帖子和时间查询评论
db.comments.createIndex({"commenter_user_id": 1})
db.comments.createIndex({"parent_comment_id": 1})  // 查询回复
```

## 二、API接口设计

### 2.1 帖子管理API (`/api/v1/ForumManager/`)

#### 2.1.1 获取帖子列表（生活圈动态）
```http
POST /api/v1/ForumManager/get_posts_list
```
**请求参数:**
```json
{
  "user_id": 123456,  // 请求用户ID
  "sort_type": "latest",  // latest(最新), hot(热门)
  "category": "all",  // all(全部), 生活, 学习, 娱乐等
  "page": 1,
  "page_size": 20
}
```
**响应格式:**
```json
{
  "success": true,
  "total_posts": 150,
  "posts": [
    {
      "post_id": 2001,
      "post_content": "清清小助手\n新年指南\n[图片]",
      "post_type": "text_image",
      "creator": {
        "user_id": 123456,
        "user_name": "清清小助手"
      },
      "media_files": [
        {
          "file_type": "image",
          "file_url": "https://example.com/image1.jpg",
          "thumbnail_url": "https://example.com/thumb1.jpg"
        }
      ],
      "stats": {
        "like_count": 15,
        "comment_count": 3,
        "view_count": 128
      },
      "is_liked": false,  // 当前用户是否已点赞
      "post_category": "生活",
      "tags": ["新年", "指南"],
      "created_at": "2024-01-05T16:34:00Z",
      "time_display": "08-05 16:34"  // 格式化的时间显示
    }
  ],
  "has_more": true
}
```

#### 2.1.2 发布新帖子
```http
POST /api/v1/ForumManager/create_post
```
**请求参数:**
```json
{
  "creator_user_id": 123456,
  "post_content": "今天天气真好，适合出门散步 🌞",
  "post_type": "text_image",
  "post_category": "生活",
  "tags": ["天气", "散步", "心情"],
  "media_files": [
    {
      "file_type": "image",
      "file_url": "https://example.com/upload/image1.jpg",
      "thumbnail_url": "https://example.com/upload/thumb1.jpg"
    }
  ]
}
```
**响应格式:**
```json
{
  "success": true,
  "post_id": 2002,
  "message": "帖子发布成功",
  "created_at": "2024-01-05T18:00:00Z"
}
```

#### 2.1.3 获取帖子详情
```http
POST /api/v1/ForumManager/get_post_detail
```
**请求参数:**
```json
{
  "post_id": 2001,
  "user_id": 123456  // 请求用户ID
}
```
**响应格式:**
```json
{
  "success": true,
  "post": {
    "post_id": 2001,
    "post_content": "清清小助手\n新年指南\n[图片]",
    "post_type": "text_image",
    "creator": {
      "user_id": 123456,
      "user_name": "清清小助手"
    },
    "media_files": [
      {
        "file_type": "image",
        "file_url": "https://example.com/image1.jpg",
        "thumbnail_url": "https://example.com/thumb1.jpg"
      }
    ],
    "stats": {
      "like_count": 15,
      "comment_count": 3,
      "view_count": 129  // 浏览数+1
    },
    "is_liked": false,
    "created_at": "2024-01-05T16:34:00Z"
  }
}
```

#### 2.1.4 搜索帖子
```http
POST /api/v1/ForumManager/search_posts
```
**请求参数:**
```json
{
  "user_id": 123456,
  "search_query": "新年指南",  // 搜索关键词
  "sort_type": "relevance",  // relevance(相关性), latest(最新), hot(热门)
  "category": "all",
  "page": 1,
  "page_size": 20
}
```
**响应格式:**
```json
{
  "success": true,
  "total_results": 25,
  "search_query": "新年指南",
  "posts": [
    // 与get_posts_list相同的帖子格式
  ],
  "has_more": true
}
```

#### 2.1.5 帖子点赞/取消点赞
```http
POST /api/v1/ForumManager/toggle_post_like
```
**请求参数:**
```json
{
  "user_id": 123456,
  "post_id": 2001,
  "action": "like"  // like(点赞), unlike(取消点赞)
}
```
**响应格式:**
```json
{
  "success": true,
  "action": "like",
  "new_like_count": 16,
  "is_liked": true,
  "message": "点赞成功"
}
```

### 2.2 评论管理API (`/api/v1/ForumManager/`)

#### 2.2.1 发布评论
```http
POST /api/v1/ForumManager/create_comment
```
**请求参数:**
```json
{
  "user_id": 123456,
  "post_id": 2001,
  "comment_content": "很有用的指南，谢谢分享！",
  "parent_comment_id": null,  // 可选，回复评论时填写
  "reply_to_user_id": null  // 可选，回复特定用户时填写
}
```
**响应格式:**
```json
{
  "success": true,
  "comment_id": 4001,
  "message": "评论发布成功",
  "created_at": "2024-01-05T17:00:00Z"
}
```

#### 2.2.2 获取帖子评论列表
```http
POST /api/v1/ForumManager/get_post_comments
```
**请求参数:**
```json
{
  "post_id": 2001,
  "user_id": 123456,  // 请求用户ID
  "sort_type": "latest",  // latest(最新), hot(热门)
  "page": 1,
  "page_size": 20
}
```
**响应格式:**
```json
{
  "success": true,
  "total_comments": 8,
  "comments": [
    {
      "comment_id": 4001,
      "comment_content": "很有用的指南，谢谢分享！",
      "commenter": {
        "user_id": 789012,
        "user_name": "张三"
      },
      "like_count": 5,
      "is_liked": false,  // 当前用户是否已点赞此评论
      "parent_comment_id": null,
      "reply_to_user": null,
      "replies": [  // 最多显示3条回复
        {
          "comment_id": 4002,
          "comment_content": "同感！",
          "commenter": {
            "user_id": 345678,
            "user_name": "李四"
          },
          "like_count": 1,
          "is_liked": false,
          "reply_to_user": {
            "user_id": 789012,
            "user_name": "张三"
          },
          "created_at": "2024-01-05T17:15:00Z"
        }
      ],
      "created_at": "2024-01-05T17:00:00Z"
    }
  ],
  "has_more": false
}
```

#### 2.2.3 评论点赞/取消点赞
```http
POST /api/v1/ForumManager/toggle_comment_like
```
**请求参数:**
```json
{
  "user_id": 123456,
  "comment_id": 4001,
  "action": "like"  // like, unlike
}
```
**响应格式:**
```json
{
  "success": true,
  "action": "like",
  "new_like_count": 6,
  "is_liked": true,
  "message": "点赞成功"
}
```

## 三、技术实现架构

### 3.1 新增文件结构（遵循三层架构）

#### Objects层 (`app/objects/`)
- `Post.py` - 帖子对象
- `Comment.py` - 评论对象

#### Service层 (`app/services/https/`)
- `ForumManager.py` - 论坛管理服务（包含帖子和评论管理）

#### Schema层 (`app/schemas/`)
- `ForumManager.py` - 论坛管理API请求响应模型

#### API层 (`app/api/v1/`)
- `ForumManager.py` - 论坛管理API接口

### 3.2 核心类设计示例

#### 3.2.1 Post对象
```python
# app/objects/Post.py
from datetime import datetime, timezone
from app.core.database import Database
from app.utils.my_logger import MyLogger
from typing import List, Dict, Optional

logger = MyLogger("Post")

class Post:
    """帖子类，管理帖子信息"""
    _post_counter = 0
    _initialized = False
    
    @classmethod
    async def initialize_counter(cls):
        """从数据库初始化帖子计数器"""
        if cls._initialized:
            return
            
        try:
            posts = await Database.find("posts", sort=[("_id", -1)], limit=1)
            if posts:
                max_id = posts[0]["_id"]
                cls._post_counter = max_id
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
    
    def __init__(self, creator_user, post_content: str, post_type: str, 
                 post_category: str, tags: List[str] = None, 
                 media_files: List[Dict] = None):
        if not Post._initialized:
            raise RuntimeError("Post counter not initialized. Call Post.initialize_counter() first.")
            
        Post._post_counter += 1
        self.post_id = Post._post_counter
        self.post_content = post_content
        self.post_type = post_type
        self.creator_user_id = creator_user.user_id
        self.creator_user_name = creator_user.telegram_user_name
        self.post_category = post_category
        self.tags = tags or []
        self.media_files = media_files or []
        
        # 互动数据
        self.like_count = 0
        self.comment_count = 0
        self.view_count = 0
        self.liked_user_ids = []
        self.comment_ids = []
        
        # 状态
        self.post_status = "published"
        
        # 时间
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Created post {self.post_id}: {self.post_content[:50]}...")
    
    async def save_to_database(self) -> bool:
        """保存帖子到数据库"""
        try:
            post_dict = {
                "_id": self.post_id,
                "post_content": self.post_content,
                "post_type": self.post_type,
                "creator_user_id": self.creator_user_id,
                "creator_user_name": self.creator_user_name,
                "post_category": self.post_category,
                "tags": self.tags,
                "media_files": self.media_files,
                "like_count": self.like_count,
                "comment_count": self.comment_count,
                "view_count": self.view_count,
                "liked_user_ids": self.liked_user_ids,
                "comment_ids": self.comment_ids,
                "post_status": self.post_status,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
            
            existing_post = await Database.find_one("posts", {"_id": self.post_id})
            if existing_post:
                await Database.update_one(
                    "posts",
                    {"_id": self.post_id},
                    {"$set": {k: v for k, v in post_dict.items() if k != "_id"}}
                )
            else:
                await Database.insert_one("posts", post_dict)
            
            logger.info(f"Saved post {self.post_id} to database")
            return True
        except Exception as e:
            logger.error(f"Error saving post {self.post_id}: {e}")
            return False
    
    async def add_like(self, user_id: int) -> bool:
        """添加点赞"""
        if user_id not in self.liked_user_ids:
            self.liked_user_ids.append(user_id)
            self.like_count += 1
            self.updated_at = datetime.now(timezone.utc)
            return await self.save_to_database()
        return True
    
    async def remove_like(self, user_id: int) -> bool:
        """取消点赞"""
        if user_id in self.liked_user_ids:
            self.liked_user_ids.remove(user_id)
            self.like_count -= 1
            self.updated_at = datetime.now(timezone.utc)
            return await self.save_to_database()
        return True
    
    async def add_comment(self, comment_id: int) -> bool:
        """添加评论"""
        if comment_id not in self.comment_ids:
            self.comment_ids.append(comment_id)
            self.comment_count += 1
            self.updated_at = datetime.now(timezone.utc)
            return await self.save_to_database()
        return True
    
    async def increment_view_count(self) -> bool:
        """增加浏览数"""
        self.view_count += 1
        return await self.save_to_database()
```

#### 3.2.2 Comment对象
```python
# app/objects/Comment.py
from datetime import datetime, timezone
from app.core.database import Database
from app.utils.my_logger import MyLogger
from typing import Optional

logger = MyLogger("Comment")

class Comment:
    """评论类"""
    _comment_counter = 0
    _initialized = False
    
    @classmethod
    async def initialize_counter(cls):
        """从数据库初始化评论计数器"""
        if cls._initialized:
            return
            
        try:
            comments = await Database.find("comments", sort=[("_id", -1)], limit=1)
            if comments:
                max_id = comments[0]["_id"]
                cls._comment_counter = max_id
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
    
    def __init__(self, commenter_user, post_id: int, comment_content: str,
                 parent_comment_id: Optional[int] = None, 
                 reply_to_user_id: Optional[int] = None,
                 reply_to_user_name: Optional[str] = None):
        if not Comment._initialized:
            raise RuntimeError("Comment counter not initialized. Call Comment.initialize_counter() first.")
            
        Comment._comment_counter += 1
        self.comment_id = Comment._comment_counter
        self.post_id = post_id
        self.comment_content = comment_content
        self.commenter_user_id = commenter_user.user_id
        self.commenter_user_name = commenter_user.telegram_user_name
        
        # 回复相关
        self.parent_comment_id = parent_comment_id
        self.reply_to_user_id = reply_to_user_id
        self.reply_to_user_name = reply_to_user_name
        
        # 互动数据
        self.like_count = 0
        self.liked_user_ids = []
        
        # 状态
        self.comment_status = "published"
        
        # 时间
        self.created_at = datetime.now(timezone.utc)
        
        logger.info(f"Created comment {self.comment_id} for post {self.post_id}")
    
    async def save_to_database(self) -> bool:
        """保存评论到数据库"""
        try:
            comment_dict = {
                "_id": self.comment_id,
                "post_id": self.post_id,
                "comment_content": self.comment_content,
                "commenter_user_id": self.commenter_user_id,
                "commenter_user_name": self.commenter_user_name,
                "parent_comment_id": self.parent_comment_id,
                "reply_to_user_id": self.reply_to_user_id,
                "reply_to_user_name": self.reply_to_user_name,
                "like_count": self.like_count,
                "liked_user_ids": self.liked_user_ids,
                "comment_status": self.comment_status,
                "created_at": self.created_at
            }
            
            existing_comment = await Database.find_one("comments", {"_id": self.comment_id})
            if existing_comment:
                await Database.update_one(
                    "comments",
                    {"_id": self.comment_id},
                    {"$set": {k: v for k, v in comment_dict.items() if k != "_id"}}
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
            self.like_count -= 1
            return await self.save_to_database()
        return True
```

## 四、前端集成指南（简化版）

### 4.1 生活圈动态页面
```javascript
// 生活圈动态页面（简化版）
Page({
  data: {
    posts: [],
    loading: false,
    hasMore: true,
    page: 1
  },
  
  onLoad: function() {
    this.loadPosts(true);
  },
  
  // 加载帖子列表
  loadPosts: function(refresh = false) {
    if (this.data.loading) return;
    
    this.setData({ loading: true });
    
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/get_posts_list',
      method: 'POST',
      data: {
        user_id: 123456,
        sort_type: 'latest',
        category: 'all',
        page: refresh ? 1 : this.data.page,
        page_size: 20
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            posts: refresh ? res.data.posts : [...this.data.posts, ...res.data.posts],
            hasMore: res.data.has_more,
            page: refresh ? 2 : this.data.page + 1,
            loading: false
          });
        }
      },
      complete: () => {
        this.setData({ loading: false });
      }
    });
  },
  
  // 点赞帖子
  onLikePost: function(e) {
    const { postId, index, isLiked } = e.currentTarget.dataset;
    
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/toggle_post_like',
      method: 'POST',
      data: {
        user_id: 123456,
        post_id: postId,
        action: isLiked ? 'unlike' : 'like'
      },
      success: (res) => {
        if (res.data.success) {
          const posts = this.data.posts;
          posts[index].stats.like_count = res.data.new_like_count;
          posts[index].is_liked = res.data.is_liked;
          this.setData({ posts });
        }
      }
    });
  },
  
  // 进入帖子详情
  onPostTap: function(e) {
    const postId = e.currentTarget.dataset.postId;
    wx.navigateTo({
      url: `/pages/post-detail/index?postId=${postId}`
    });
  },
  
  // 搜索
  onSearch: function(e) {
    const query = e.detail.value;
    if (query.trim()) {
      wx.navigateTo({
        url: `/pages/search/index?q=${encodeURIComponent(query)}`
      });
    }
  },
  
  // 发布帖子
  onCreatePost: function() {
    wx.navigateTo({
      url: '/pages/create-post/index'
    });
  },
  
  // 下拉刷新
  onPullDownRefresh: function() {
    this.loadPosts(true);
    wx.stopPullDownRefresh();
  },
  
  // 上拉加载更多
  onReachBottom: function() {
    if (this.data.hasMore) {
      this.loadPosts(false);
    }
  }
});
```

### 4.2 搜索页面（简化版）
```javascript
// 搜索页面（简化版）
Page({
  data: {
    searchQuery: '',
    searchResults: [],
    searching: false
  },
  
  onLoad: function(options) {
    if (options.q) {
      this.setData({ searchQuery: decodeURIComponent(options.q) });
      this.performSearch();
    }
  },
  
  // 执行搜索
  performSearch: function() {
    if (!this.data.searchQuery.trim()) return;
    
    this.setData({ searching: true });
    
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/search_posts',
      method: 'POST',
      data: {
        user_id: 123456,
        search_query: this.data.searchQuery,
        sort_type: 'relevance',
        category: 'all',
        page: 1,
        page_size: 20
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            searchResults: res.data.posts,
            searching: false
          });
        }
      },
      complete: () => {
        this.setData({ searching: false });
      }
    });
  }
});
```

## 五、部署配置

### 5.1 数据库初始化
```python
# 在app/server_run.py中添加
@app.on_event("startup")
async def startup_event():
    # 现有的初始化...
    
    # 新增：初始化论坛管理器
    from app.services.https.ForumManager import ForumManager
    forum_manager = ForumManager()
    await forum_manager.construct()
    
    logger.info("Forum system initialized successfully")
```

### 5.2 路由注册
```python
# 在app/server_run.py中注册API路由
from app.api.v1 import ForumManager

app.include_router(ForumManager.router, prefix="/api/v1/ForumManager", tags=["论坛管理"])
```

## 六、总结

### ✅ 简化后的优势
1. **减少复杂性**：移除用户资料管理，专注核心功能
2. **快速开发**：只需要3个主要文件（Post.py, Comment.py, ForumManager.py）
3. **易于维护**：统一的API接口，简化的数据结构
4. **扩展友好**：后续可以轻松添加用户资料功能

### 🎯 核心功能保留
- ✅ 浏览帖子动态
- ✅ 发布新帖子
- ✅ 点赞系统
- ✅ 评论系统（支持回复）
- ✅ 搜索功能

### 📊 简化的数据库设计
- **最小化用户扩展**：只添加必要的帖子和点赞ID列表
- **独立的帖子和评论系统**：保持功能完整性
- **简化的媒体文件支持**：专注图片分享
- **高效的索引设计**：支持快速查询和搜索

这个简化版本大大降低了开发复杂度，同时保持了论坛的核心功能，非常适合快速迭代和后续扩展。
