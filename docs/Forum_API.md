## 论坛接口说明文档（内存优先 + 周期落库）

本系统的论坛服务采用“内存优先”的设计：所有写操作优先更新内存，后台任务每 10 秒将内存中的帖子与评论落库到 MongoDB。部分接口会尝试立即同步到数据库，但即使数据库短暂不同步，内存也会保证数据即时一致。

- 基础地址: `http://127.0.0.1:8000`
- 总前缀: `/api/v1/ForumManager`
- 数据一致性策略:
  - 帖子与评论: 写入内存，定时任务每 10 秒持久化（`posts`、`comments`）
  - 用户的帖子 ID（`users.post_ids`）: 在发帖时先更新内存，再尝试写 DB；初始化与落库前会基于内存帖子对齐用户的 `post_ids`
  - 帖子点赞: 写内存 + 立即更新 `users.liked_post_ids`，若失败由定时任务兜底
  - 评论点赞: 仅写内存，随定时任务落库

### 通用数据结构

- 帖子项 PostItem
  - `post_id` number
  - `post_content` string
  - `post_type` string ("text" | "image" | "text_image")
  - `creator` { `user_id`: number, `user_name`: string }
  - `media_files` Array<{ file_type, file_url, thumbnail_url? }>
  - `stats` { `like_count`: number, `comment_count`: number, `view_count`: number }
  - `is_liked` boolean
  - `post_category` string
  - `tags` string[]
  - `created_at` string | null (ISO, UTC)
  - `time_display` string (MM-DD HH:mm)

- 评论项 CommentItem
  - `comment_id` number
  - `comment_content` string
  - `commenter` { `user_id`: number, `user_name`: string }
  - `like_count` number
  - `is_liked` boolean
  - `created_at` string | null (ISO, UTC)

---

## 接口一览

- 创建帖子: POST `/create_post`
- 获取帖子列表: POST `/get_posts_list`
- 搜索帖子: POST `/search_posts`
- 帖子点赞/取消点赞: POST `/toggle_post_like`
- 获取帖子详情: POST `/get_post_detail`
- 发布评论: POST `/create_comment`
- 获取帖子评论列表: POST `/get_post_comments`
- 评论点赞/取消点赞: POST `/toggle_comment_like`

> 注：所有 URL 均应加上前缀 `/api/v1/ForumManager`。

---

## 创建帖子

- URL: `/api/v1/ForumManager/create_post`
- 方法: POST
- 说明: 在内存中创建新帖子，立即可见；尝试将 `post_id` 写入 `users.post_ids`，失败由后台落库对齐

请求

```json
{
  "creator_user_id": 123456,
  "post_content": "这是一个新帖子",
  "post_type": "text",
  "post_category": "测试",
  "tags": ["论坛", "接口"],
  "media_files": []
}
```

响应

```json
{
  "success": true,
  "post_id": 15,
  "message": "帖子发布成功"
}
```

前端调用示例（JavaScript，含中文注释）

```javascript
// 创建帖子（内存优先）
const res = await fetch('/api/v1/ForumManager/create_post', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    creator_user_id: 123456,
    post_content: '这是一个新帖子',
    post_type: 'text',
    post_category: '测试',
    tags: ['论坛', '接口'],
    media_files: []
  })
});
const data = await res.json();
```

---

## 获取帖子列表

- URL: `/api/v1/ForumManager/get_posts_list`
- 方法: POST
- 说明:
  - 从内存中返回已发布的帖子
  - 排序:
    - `latest`: 按创建时间倒序（已统一为 UTC aware datetime，避免时区比较异常）
    - `hot`: 按点赞数、评论数、时间综合倒序
  - 支持分页（page/page_size）
  - 返回 `is_liked` 以及格式化时间 `time_display`

请求

```json
{
  "user_id": 123456,
  "sort_type": "latest",
  "page": 1,
  "page_size": 20
}
```

响应

```json
{
  "success": true,
  "posts": [
    {
      "post_id": 15,
      "post_content": "这是一个新帖子",
      "post_type": "text",
      "creator": { "user_id": 123456, "user_name": "test_user_123456" },
      "media_files": [],
      "stats": { "like_count": 0, "comment_count": 0, "view_count": 0 },
      "is_liked": false,
      "post_category": "测试",
      "tags": ["论坛", "接口"],
      "created_at": "2025-08-11T08:18:51.283000Z",
      "time_display": "08-11 08:18"
    }
  ],
  "has_more": false
}
```

前端调用示例（无限滚动）

```javascript
async function fetchPosts(page) {
  const res = await fetch('/api/v1/ForumManager/get_posts_list', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ user_id: 123456, sort_type: 'latest', page, page_size: 10 })
  });
  const { posts, has_more } = await res.json();
  return { posts, has_more };
}
```

---

## 搜索帖子

- URL: `/api/v1/ForumManager/search_posts`
- 方法: POST
- 说明: 内存中按 `post_content` 或 `tags` 包含关键字（大小写不敏感），按时间倒序，分页

请求

```json
{
  "user_id": 123456,
  "search_query": "论坛",
  "page": 1,
  "page_size": 20
}
```

响应

```json
{
  "success": true,
  "posts": [],
  "has_more": false
}
```

---

## 帖子点赞/取消点赞

- URL: `/api/v1/ForumManager/toggle_post_like`
- 方法: POST
- 说明:
  - 内存中更新帖子点赞计数与 `liked_user_ids`
  - 同步更新 `users.liked_post_ids`（DB），失败由定时任务兜底
  - 返回最新点赞数与是否已点赞

请求

```json
{
  "user_id": 123456,
  "post_id": 15,
  "action": "like"
}
```

响应

```json
{
  "success": true,
  "action": "like",
  "new_like_count": 1,
  "is_liked": true
}
```

取消点赞时 `action` 为 `"unlike"`，`is_liked` 变为 `false`。

---

## 获取帖子详情（新增）

- URL: `/api/v1/ForumManager/get_post_detail`
- 方法: POST
- 说明: 基于内存返回单个帖子的完整详情；`is_liked` 由 `users.liked_post_ids` 计算

请求

```json
{
  "user_id": 123456,
  "post_id": 15
}
```

响应

```json
{
  "success": true,
  "post": { /* PostItem */ },
  "message": null
}
```

---

## 发布评论

- URL: `/api/v1/ForumManager/create_comment`
- 方法: POST
- 说明:
  - 内存中新建评论并加入目标帖子的评论列表
  - 评论的点赞计数与点赞人列表仅在内存维护，定时任务落库

请求

```json
{
  "user_id": 123456,
  "post_id": 15,
  "comment_content": "首条评论"
}
```

响应

```json
{
  "success": true,
  "comment_id": 1,
  "message": "评论发布成功"
}
```

---

## 获取帖子评论列表

- URL: `/api/v1/ForumManager/get_post_comments`
- 方法: POST
- 说明:
  - 从内存中按时间正序返回评论，分页
  - 当前版本为 page/page_size 分页；如需增量加载（游标分页），可扩展 `after_cursor`/`next_cursor`

请求

```json
{
  "post_id": 15,
  "user_id": 123456,
  "page": 1,
  "page_size": 20
}
```

响应

```json
{
  "success": true,
  "comments": [
    {
      "comment_id": 1,
      "comment_content": "首条评论",
      "commenter": { "user_id": 123456, "user_name": "test_user_123456" },
      "like_count": 0,
      "is_liked": false,
      "created_at": "2025-08-11T08:20:51.283000Z"
    }
  ],
  "has_more": false
}
```

---

## 评论点赞/取消点赞

- URL: `/api/v1/ForumManager/toggle_comment_like`
- 方法: POST
- 说明:
  - 仅更新内存中的评论点赞数据（`like_count`、`liked_user_ids`），随定时任务落库
  - 返回最新点赞数

请求

```json
{
  "user_id": 123456,
  "comment_id": 1,
  "action": "like"
}
```

响应

```json
{
  "success": true,
  "action": "like",
  "new_like_count": 1,
  "is_liked": true
}
```

---

## 前端集成建议

- 列表/滚动
  - 调用 `get_posts_list` 实现首页/话题页无限滚动
  - `sort_type` 可选 `latest`/`hot`，推荐默认 `latest`
- 帖子详情
  - 列表项点击后调用 `get_post_detail`，并并行首屏拉取 `get_post_comments`
- 点赞
  - 调用 `toggle_post_like` 后，本地 UI 立即乐观更新（计数 +1/-1；高亮状态），失败再回滚
- 评论
  - `create_comment` 成功后直接将新评论插入当前列表顶部或合适位置
- 同步延迟感知
  - 数据最终一致性保证：即使数据库短时不同步，内存接口始终一致；后台 10 秒落库
  - 如前端需要“确认已落库”，可在关键动作后轮询对应集合（一般不必）

---

## 错误与返回规范

- 正常失败（业务层捕获）:
  - 响应 HTTP 200，`{ "success": false, ... }`
- 未捕获异常/内部错误:
  - 响应 HTTP 500，`{ "detail": "internal error" }`
- 可能错误场景:
  - `post not found`、`comment not found`、`user not found`
  - 非法 `action` 值（仅 `like`/`unlike`）

---

## 后续可选增强

- 评论游标分页（增量加载）：`after_cursor`/`next_cursor`，避免重复/漏数据
- 帖子详情接口支持返回“最新评论前 N 条”与“更多评论游标”
- 软删除与状态过滤：`post_status = deleted` 的隐藏策略
- 视图计数 `view_count` 自动增长策略（进入详情页时增长，去重策略等）


