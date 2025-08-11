# 最简论坛系统设计方案

## 项目概述

设计最简版论坛功能，专注于核心的帖子浏览、发布、点赞和简单评论功能。移除所有复杂特性，确保短时间内可快速开发上线。

## 一、数据库结构设计（最简版）

### 1.1 扩展现有Users集合（最小化）

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
  "creator_user_name": "清清小助手",  // 创建者用户名
  
  // 媒体文件信息（简化）
  "media_files": [
    {
      "file_type": "image",
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
  "tags": ["新年", "指南"],  // 标签（简化，最多3个）
  "post_status": "published",  // published, deleted
  
  // 时间信息
  "created_at": "2024-01-05T16:34:00Z",
  "updated_at": "2024-01-05T16:34:00Z"
}
```

### 1.3 Comments集合（评论数据库 - 极简版）

```javascript
// comments 集合（极简版 - 移除回复功能）
{
  "_id": comment_id,  // 评论ID作为主键
  "post_id": 2001,  // 所属帖子ID
  "comment_content": "很有用的指南，谢谢分享！",  // 评论内容
  "commenter_user_id": 789012,  // 评论者用户ID
  "commenter_user_name": "张三",  // 评论者用户名
  
  // 互动数据（简化）
  "like_count": 5,  // 评论点赞数
  "liked_user_ids": [123456, 345678],  // 点赞用户ID列表
  
  // 评论状态
  "comment_status": "published",  // published, deleted
  
  // 时间信息
  "created_at": "2024-01-05T17:00:00Z"
}
```

### 1.4 数据库索引设计（简化）

```javascript
// posts 集合索引
db.posts.createIndex({"_id": 1}, {unique: true})
db.posts.createIndex({"creator_user_id": 1})
db.posts.createIndex({"post_status": 1, "created_at": -1})  // 按状态和时间排序
db.posts.createIndex({"post_category": 1})  // 分类浏览
db.posts.createIndex({"post_content": "text"})  // 简单全文搜索

// comments 集合索引
db.comments.createIndex({"_id": 1}, {unique: true})
db.comments.createIndex({"post_id": 1, "created_at": 1})  // 按帖子和时间查询评论
db.comments.createIndex({"commenter_user_id": 1})
```

## 二、API接口设计（最简版）

### 2.1 ForumManager API (`/api/v1/ForumManager/`)

#### 2.1.1 获取帖子列表
```http
POST /api/v1/ForumManager/get_posts_list
```
**请求参数:**
```json
{
  "user_id": 123456,
  "sort_type": "latest",  // latest(最新), hot(热门)
  "page": 1,
  "page_size": 20
}
```
**响应格式:**
```json
{
  "success": true,
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
      "is_liked": false,
      "post_category": "生活",
      "tags": ["新年", "指南"],
      "created_at": "2024-01-05T16:34:00Z",
      "time_display": "08-05 16:34"
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
  "post_content": "今天天气真好 🌞",
  "post_type": "text_image",
  "post_category": "生活",
  "tags": ["天气", "心情"],
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
  "message": "帖子发布成功"
}
```

#### 2.1.3 搜索帖子
```http
POST /api/v1/ForumManager/search_posts
```
**请求参数:**
```json
{
  "user_id": 123456,
  "search_query": "新年",
  "page": 1,
  "page_size": 20
}
```
**响应格式:**
```json
{
  "success": true,
  "posts": [
    // 与get_posts_list相同的帖子格式
  ],
  "has_more": true
}
```

#### 2.1.4 帖子点赞/取消点赞
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
  "is_liked": true
}
```

#### 2.1.5 发布评论（极简版）
```http
POST /api/v1/ForumManager/create_comment
```
**请求参数:**
```json
{
  "user_id": 123456,
  "post_id": 2001,
  "comment_content": "很有用的指南，谢谢分享！"
}
```
**响应格式:**
```json
{
  "success": true,
  "comment_id": 4001,
  "message": "评论发布成功"
}
```

#### 2.1.6 获取帖子评论列表（极简版）
```http
POST /api/v1/ForumManager/get_post_comments
```
**请求参数:**
```json
{
  "post_id": 2001,
  "user_id": 123456,
  "page": 1,
  "page_size": 20
}
```
**响应格式:**
```json
{
  "success": true,
  "comments": [
    {
      "comment_id": 4001,
      "comment_content": "很有用的指南，谢谢分享！",
      "commenter": {
        "user_id": 789012,
        "user_name": "张三"
      },
      "like_count": 5,
      "is_liked": false,
      "created_at": "2024-01-05T17:00:00Z"
    }
  ],
  "has_more": false
}
```

#### 2.1.7 评论点赞/取消点赞
```http
POST /api/v1/ForumManager/toggle_comment_like
```
**请求参数:**
```json
{
  "user_id": 123456,
  "comment_id": 4001,
  "action": "like"
}
```
**响应格式:**
```json
{
  "success": true,
  "action": "like",
  "new_like_count": 6,
  "is_liked": true
}
```

## 三、技术实现架构（最简版）

### 3.1 新增文件结构

#### Objects层 (`app/objects/`)
- `Post.py` - 帖子对象
- `Comment.py` - 评论对象（极简版）

#### Service层 (`app/services/https/`)
- `ForumManager.py` - 论坛管理服务（统一管理）

#### Schema层 (`app/schemas/`)
- `ForumManager.py` - 论坛管理API请求响应模型

#### API层 (`app/api/v1/`)
- `ForumManager.py` - 论坛管理API接口

### 3.2 核心类设计（极简版）

#### 3.2.1 Comment对象（极简版）
```python
# app/objects/Comment.py（极简版）
from datetime import datetime, timezone
from app.core.database import Database
from app.utils.my_logger import MyLogger

logger = MyLogger("Comment")

class Comment:
    """评论类（极简版 - 无回复功能）"""
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
    
    def __init__(self, commenter_user, post_id: int, comment_content: str):
        if not Comment._initialized:
            raise RuntimeError("Comment counter not initialized. Call Comment.initialize_counter() first.")
            
        Comment._comment_counter += 1
        self.comment_id = Comment._comment_counter
        self.post_id = post_id
        self.comment_content = comment_content
        self.commenter_user_id = commenter_user.user_id
        self.commenter_user_name = commenter_user.telegram_user_name
        
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

## 四、前端集成指南（极简版）

### 4.1 生活圈动态页面（极简版）
```javascript
// 生活圈动态页面（极简版）
Page({
  data: {
    posts: [],
    loading: false,
    page: 1
  },
  
  onLoad: function() {
    this.loadPosts();
  },
  
  // 加载帖子列表
  loadPosts: function() {
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/get_posts_list',
      method: 'POST',
      data: {
        user_id: 123456,
        sort_type: 'latest',
        page: this.data.page,
        page_size: 20
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            posts: this.data.page === 1 ? res.data.posts : [...this.data.posts, ...res.data.posts],
            page: this.data.page + 1
          });
        }
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
  
  // 进入评论页面
  onCommentTap: function(e) {
    const postId = e.currentTarget.dataset.postId;
    wx.navigateTo({
      url: `/pages/comments/index?postId=${postId}`
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
  }
});
```

### 4.2 评论页面（极简版）
```javascript
// 评论页面（极简版）
Page({
  data: {
    postId: 0,
    comments: [],
    newComment: ''
  },
  
  onLoad: function(options) {
    this.setData({ postId: parseInt(options.postId) });
    this.loadComments();
  },
  
  // 加载评论
  loadComments: function() {
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/get_post_comments',
      method: 'POST',
      data: {
        post_id: this.data.postId,
        user_id: 123456,
        page: 1,
        page_size: 50
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({ comments: res.data.comments });
        }
      }
    });
  },
  
  // 输入评论
  onCommentInput: function(e) {
    this.setData({ newComment: e.detail.value });
  },
  
  // 发布评论
  submitComment: function() {
    if (!this.data.newComment.trim()) return;
    
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/create_comment',
      method: 'POST',
      data: {
        user_id: 123456,
        post_id: this.data.postId,
        comment_content: this.data.newComment
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({ newComment: '' });
          this.loadComments(); // 重新加载评论列表
          wx.showToast({
            title: '评论成功',
            icon: 'success'
          });
        }
      }
    });
  },
  
  // 点赞评论
  onLikeComment: function(e) {
    const { commentId, index, isLiked } = e.currentTarget.dataset;
    
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ForumManager/toggle_comment_like',
      method: 'POST',
      data: {
        user_id: 123456,
        comment_id: commentId,
        action: isLiked ? 'unlike' : 'like'
      },
      success: (res) => {
        if (res.data.success) {
          const comments = this.data.comments;
          comments[index].like_count = res.data.new_like_count;
          comments[index].is_liked = res.data.is_liked;
          this.setData({ comments });
        }
      }
    });
  }
});
```

## 五、开发优势

### ✅ 极简化优势
1. **开发时间最短**：减少90%的复杂功能
2. **代码量最少**：只需要2个对象类 + 1个管理服务
3. **测试简单**：功能单一，测试用例少
4. **维护容易**：逻辑简单，bug少
5. **快速上线**：可在1-2周内完成开发

### 🎯 保留的核心功能
- ✅ 浏览帖子（按时间排序）
- ✅ 发布帖子（文字+图片）
- ✅ 点赞帖子
- ✅ 评论帖子（直接评论，无回复）
- ✅ 点赞评论
- ✅ 搜索帖子

### ❌ 移除的复杂功能
- ❌ 评论回复功能
- ❌ 用户资料管理
- ❌ 关注系统
- ❌ 复杂的排序算法
- ❌ 高级搜索功能
- ❌ 媒体文件详细信息

## 六、总结

这个极简版论坛系统专为快速开发设计：

### 📊 开发量对比
- **原版设计**：9个文件，复杂的关联关系
- **简化版设计**：6个文件，移除用户资料
- **极简版设计**：4个文件，移除回复功能

### 🚀 实现周期
- **数据库设计**：1天
- **后端开发**：3-5天
- **前端集成**：2-3天
- **测试调试**：1-2天
- **总计**：7-11天即可完成

这个极简版本确保你能在最短时间内上线一个功能完整的论坛系统！
