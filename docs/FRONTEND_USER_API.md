# 前端对接文档：用户管理接口 (UserManagement)

## 基础信息
- Base URL: `http://127.0.0.1:8000/api/v1`
- Content-Type: `application/json`
- user_id 说明: 使用微信 openid，类型为字符串（不要做数字转换）
- 性别约定: `1=女性`、`2=男性`、`3=其他`

## 一、快速上手（浏览器/React 等通用环境）

```javascript
// 简易 API 客户端封装（JS + 中文注释）
// 注意：user_id 必须是字符串（openid）
const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

// 通用 POST 封装
async function post(path, body) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    // 中文注释：统一 JSON 序列化
    body: JSON.stringify(body || {})
  });
  // 中文注释：后端异常时抛错便于前端捕获
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status}: ${text || '请求失败'}`);
  }
  return res.json();
}

// 1) 创建用户（传入 openid）
export async function createUser({ user_id, user_name, gender }) {
  // 中文注释：user_id 为 openid 字符串，gender 为 1/2/3
  return post('/UserManagement/create_new_user', { user_id, user_name, gender });
}

// 2) 编辑用户年龄
export async function editUserAge({ user_id, age }) {
  return post('/UserManagement/edit_user_age', { user_id, age });
}

// 3) 编辑用户目标性别
export async function editTargetGender({ user_id, target_gender }) {
  return post('/UserManagement/edit_target_gender', { user_id, target_gender });
}

// 4) 编辑用户简介
export async function editUserSummary({ user_id, summary }) {
  return post('/UserManagement/edit_summary', { user_id, summary });
}

// 5) 保存用户信息到数据库（可选 user_id，不传则保存所有内存中的用户）
export async function saveUserToDB({ user_id } = {}) {
  return post('/UserManagement/save_to_database', { user_id });
}

// 6) 根据 user_id 获取用户信息
export async function getUserInfo({ user_id }) {
  return post('/UserManagement/get_user_info_with_user_id', { user_id });
}

// 7) 注销用户（删除用户及其关联数据）
export async function deactivateUser({ user_id }) {
  return post('/UserManagement/deactivate_user', { user_id });
}
```

## 二、接口清单与示例

### 1. 创建用户 create_new_user
- Method/Path: `POST /UserManagement/create_new_user`
- Request
  - `user_name`: string（用户名称）
  - `user_id`: string（openid）
  - `gender`: number（1/2/3）
- Response
  - `{ success: boolean, user_id: string }`
- 示例
```javascript
const res = await createUser({ user_id: 'wx_openid_u1', user_name: '小明', gender: 1 });
// 返回示例: { success: true, user_id: 'wx_openid_u1' }
```

### 2. 编辑用户年龄 edit_user_age
- Method/Path: `POST /UserManagement/edit_user_age`
- Request: `{ user_id: string, age: number }`
- Response: `{ success: boolean }`
- 示例
```javascript
await editUserAge({ user_id: 'wx_openid_u1', age: 22 });
```

### 3. 编辑目标性别 edit_target_gender
- Method/Path: `POST /UserManagement/edit_target_gender`
- Request: `{ user_id: string, target_gender: 1|2|3 }`
- Response: `{ success: boolean }`
- 示例
```javascript
await editTargetGender({ user_id: 'wx_openid_u1', target_gender: 2 });
```

### 4. 编辑用户简介 edit_summary
- Method/Path: `POST /UserManagement/edit_summary`
- Request: `{ user_id: string, summary: string }`
- Response: `{ success: boolean }`
- 示例
```javascript
await editUserSummary({ user_id: 'wx_openid_u1', summary: '我是一名测试用户，喜欢论坛互动。' });
```

### 5. 保存用户信息到数据库 save_to_database
- Method/Path: `POST /UserManagement/save_to_database`
- Request: `{ user_id?: string }`（不传表示保存所有内存中的用户）
- Response: `{ success: boolean }`
- 示例
```javascript
await saveUserToDB({ user_id: 'wx_openid_u1' });
```

### 6. 获取用户信息 get_user_info_with_user_id
- Method/Path: `POST /UserManagement/get_user_info_with_user_id`
- Request: `{ user_id: string }`
- Response:
```json
{
  "user_id": "wx_openid_u1",
  "user_name": "小明",
  "gender": 1,
  "age": 22,
  "target_gender": 2,
  "user_personality_trait": "我是一名测试用户，喜欢论坛互动。",
  "match_ids": [] // 匹配ID列表，类型为 int[]
}
```
- 示例
```javascript
const info = await getUserInfo({ user_id: 'wx_openid_u1' });
```

### 7. 注销用户 deactivate_user
- Method/Path: `POST /UserManagement/deactivate_user`
- Request: `{ user_id: string }`
- Response: `{ success: boolean }`
- 示例
```javascript
await deactivateUser({ user_id: 'wx_openid_u1' });
```

## 三、典型调用流程建议
- **新用户首次使用小程序（拿到 openid）**:
  1) 调用 `createUser` 创建用户（`user_id` 为 `openid`）
  2) 可选：调用 `editUserAge` / `editTargetGender` / `editUserSummary` 设置用户资料
  3) 调用 `saveUserToDB({ user_id })` 明确将用户数据落库（若后台有自动保存任务，也可不手动调用）
- **页面加载用户中心**:
  1) 调用 `getUserInfo({ user_id })` 拉取最新用户信息
- **注销用户**:
  1) 调用 `deactivateUser({ user_id })`

## 四、错误处理与健壮性建议
- `user_id` 一律用字符串（openid），不要转成数字；任何 `Number()` / `parseInt()` 的逻辑应移除。
- 建议在统一的 `post` 封装中处理 `res.ok`，将错误文本抛出，便于界面层捕获并向用户展示友好提示。
- 对于网络波动，可以考虑在前端增加最少重试（如 1~2 次）或降级提示。
- 在生产环境中，请务必使用 HTTPS，并通过环境变量管理 `BASE_URL`。

## 五、微信小程序（wx.request）示例

```javascript
// 创建用户（微信小程序）
function createUserMini({ user_id, user_name, gender }) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: 'http://127.0.0.1:8000/api/v1/UserManagement/create_new_user',
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: { user_id, user_name, gender }, // 中文注释：user_id 为 openid 字符串
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${res.data ? JSON.stringify(res.data) : '请求失败'}`));
        }
      },
      fail: (err) => reject(err)
    });
  });
}

// 获取用户信息（微信小程序）
function getUserInfoMini({ user_id }) {
  return new Promise((resolve, reject) => {
    wx.request({
      url: 'http://127.0.0.1:8000/api/v1/UserManagement/get_user_info_with_user_id',
      method: 'POST',
      header: { 'Content-Type': 'application/json' },
      data: { user_id },
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data);
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${res.data ? JSON.stringify(res.data) : '请求失败'}`));
        }
      },
      fail: (err) => reject(err)
    });
  });
}
```

## 六、调试与联调建议
- **配合后端日志**：后端在 `logs/app.log` 中输出较完整的请求/响应与单例状态，有助于问题定位。
- **冒烟测试脚本**：本仓库提供了用户与论坛的冒烟脚本（示例使用 openid 字符串），可用于快速验证接口功能。
  - 运行方式：`conda run -n miracle_backend_env python tests/smoke_user_forum_openid.py`
- 若需 Chatroom/Match/AI 等其他模块接口文档，可在本文件基础上扩展分节。
