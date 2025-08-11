# 微信小程序频道群聊系统设计文档

## 项目概述

基于现有的双人聊天室WebSocket架构，为微信小程序设计简化版频道群聊系统。该系统最大化复用现有代码，通过扩展而非重写的方式实现频道功能。

## 一、前端功能分析

### 1.1 页面结构
- **频道列表页面**: 显示所有可用频道，包含频道名称、描述、成员数等信息
- **频道聊天页面**: 实时群聊界面，支持消息发送和接收
- **创建频道页面**: 创建新频道的表单页面

### 1.2 核心功能
- 浏览和加入频道
- 创建新频道
- 实时群聊消息收发
- 在线人数显示

## 二、数据结构设计

### 2.1 Channel对象（频道）

#### 数据库集合：`channels`
```javascript
{
  "_id": channel_id,  // 频道ID作为主键（int类型）
  "channel_name": "舞蹈社",
  "channel_description": "古典舞、现代舞、民族舞、双人舞\n最新舞蹈小伙伴",
  "channel_avatar_url": "https://example.com/avatar.jpg",
  "category": "兴趣",  // 频道分类
  "creator_user_id": 123456,
  "member_user_ids": [123456, 789012, 345678],  // 成员列表
  "member_count": 1000,  // 总成员数
  "online_count": 100,   // 当前在线数
  "message_ids": [2001, 2002, 2003],  // 消息ID列表
  "is_public": true,     // 是否公开频道
  "created_at": "2024-01-01T10:00:00Z",
  "updated_at": "2024-01-01T10:00:00Z"
}
```

#### 数据库索引设计
```javascript
// 主键索引
db.channels.createIndex({"_id": 1}, {unique: true})
// 分类索引
db.channels.createIndex({"category": 1})
// 创建者索引
db.channels.createIndex({"creator_user_id": 1})
// 成员索引
db.channels.createIndex({"member_user_ids": 1})
```

### 2.2 ChannelMessage对象（频道消息）

#### 数据库集合：`channel_messages`
```javascript
{
  "_id": message_id,  // 消息ID作为主键（int类型）
  "message_content": "Hi Fajar, Nice to meet you too 👋",
  "message_send_time_in_utc": "2024-01-01T07:00:00Z",
  "message_sender_id": 123456,
  "channel_id": 2001,  // 所属频道ID
  "message_type": "text"  // 消息类型：text, image, system
}
```

#### 数据库索引设计
```javascript
// 主键索引
db.channel_messages.createIndex({"_id": 1}, {unique: true})
// 频道消息时间索引（用于分页查询）
db.channel_messages.createIndex({"channel_id": 1, "message_send_time_in_utc": -1})
// 发送者索引
db.channel_messages.createIndex({"message_sender_id": 1})
```

## 三、API接口设计

### 3.1 频道管理API (`/api/v1/ChannelManager/`)

#### 3.1.1 获取频道列表
```http
POST /api/v1/ChannelManager/get_channels_list
```

**请求参数:**
```json
{
  "user_id": 123456,
  "category": "all",  // 可选：筛选分类，"all"表示所有分类
  "page": 1,
  "page_size": 20
}
```

**响应格式:**
```json
{
  "success": true,
  "total_channels": 50,
  "channels": [
    {
      "channel_id": 2001,
      "channel_name": "舞蹈社",
      "channel_description": "古典舞、现代舞、民族舞、双人舞\n最新舞蹈小伙伴",
      "channel_avatar_url": "https://example.com/avatar.jpg",
      "category": "兴趣",
      "member_count": 1000,
      "online_count": 100,
      "is_member": true  // 当前用户是否已加入
    }
  ]
}
```

#### 3.1.2 创建新频道
```http
POST /api/v1/ChannelManager/create_channel
```

**请求参数:**
```json
{
  "creator_user_id": 123456,
  "channel_name": "Football",
  "channel_description": "We talk about football. American football.",
  "category": "General Topics",
  "channel_avatar_url": "https://example.com/avatar.jpg"  // 可选
}
```

**响应格式:**
```json
{
  "success": true,
  "channel_id": 2002,
  "message": "频道创建成功"
}
```

#### 3.1.3 加入频道
```http
POST /api/v1/ChannelManager/join_channel
```

**请求参数:**
```json
{
  "user_id": 123456,
  "channel_id": 2001
}
```

**响应格式:**
```json
{
  "success": true,
  "message": "成功加入频道"
}
```

#### 3.1.4 获取频道详情
```http
POST /api/v1/ChannelManager/get_channel_info
```

**请求参数:**
```json
{
  "channel_id": 2001,
  "user_id": 123456
}
```

**响应格式:**
```json
{
  "success": true,
  "channel_info": {
    "channel_id": 2001,
    "channel_name": "舞蹈社",
    "channel_description": "古典舞、现代舞、民族舞、双人舞\n最新舞蹈小伙伴",
    "member_count": 1000,
    "online_count": 100,
    "is_member": true,
    "created_at": "2024-01-01T10:00:00Z"
  }
}
```

#### 3.1.5 获取频道聊天历史
```http
POST /api/v1/ChannelManager/get_channel_history
```

**请求参数:**
```json
{
  "channel_id": 2001,
  "user_id": 123456,
  "page": 1,
  "page_size": 50
}
```

**响应格式:**
```json
{
  "success": true,
  "total_messages": 200,
  "messages": [
    {
      "message_id": 3001,
      "sender_name": "Fajar",
      "message_content": "Hi Fajar, Nice to meet you too 👋",
      "send_time": "07:00 am",
      "is_own_message": false
    },
    {
      "message_id": 3002,
      "sender_name": "I",
      "message_content": "Hello Jennifer, Nice to meet you 👋",
      "send_time": "07:10 am",
      "is_own_message": true
    }
  ],
  "has_more": true
}
```

## 四、WebSocket实时通信设计

### 4.1 复用现有WebSocket端点

**端点**: `/ws/message`

复用现有的`MessageConnectionHandler`，通过扩展消息类型来支持频道功能。

### 4.2 WebSocket消息类型

#### 4.2.1 加入频道房间
```javascript
// 客户端 -> 服务器
{
  "type": "channel_join",
  "channel_id": 2001
}

// 服务器 -> 客户端
{
  "type": "channel_join_response",
  "success": true,
  "channel_id": 2001,
  "online_count": 101,
  "message": "成功加入频道"
}
```

#### 4.2.2 发送频道消息
```javascript
// 客户端 -> 服务器
{
  "type": "channel_message",
  "channel_id": 2001,
  "content": "Type your message...",
  "timestamp": "2024-01-01T08:00:00Z"
}

// 服务器广播给频道所有成员
{
  "type": "channel_message_received",
  "channel_id": 2001,
  "message_id": 3003,
  "from": 123456,
  "sender_name": "张三",
  "content": "Type your message...",
  "timestamp": "2024-01-01T08:00:00Z"
}

// 服务器 -> 发送者确认
{
  "type": "channel_message_status",
  "channel_id": 2001,
  "message_id": 3003,
  "success": true,
  "timestamp": "2024-01-01T08:00:00Z"
}
```

#### 4.2.3 离开频道房间
```javascript
// 客户端 -> 服务器
{
  "type": "channel_leave",
  "channel_id": 2001
}

// 服务器 -> 客户端
{
  "type": "channel_leave_response",
  "success": true,
  "channel_id": 2001,
  "online_count": 99
}
```

#### 4.2.4 频道成员状态通知
```javascript
// 新成员加入通知
{
  "type": "channel_user_joined",
  "channel_id": 2001,
  "user_name": "王五",
  "online_count": 102
}

// 成员离开通知
{
  "type": "channel_user_left",
  "channel_id": 2001,
  "user_name": "李四",
  "online_count": 100
}
```

## 五、技术实现方案

### 5.1 文件结构（遵循三层架构）

#### Objects层 (`app/objects/`)
- `Channel.py` - 频道对象类
- `ChannelMessage.py` - 频道消息对象类

#### Service层 (`app/services/https/`)
- `ChannelManager.py` - 频道管理业务逻辑类

#### Schema层 (`app/schemas/`)
- `ChannelManager.py` - 频道API请求响应模型

#### API层 (`app/api/v1/`)
- `ChannelManager.py` - 频道管理API接口

#### WebSocket扩展
- 修改 `app/WebSocketsService/MessageConnectionHandler.py` - 添加频道支持

### 5.2 核心类设计

#### 5.2.1 Channel对象
```python
# app/objects/Channel.py
from datetime import datetime, timezone
from app.core.database import Database
from app.utils.my_logger import MyLogger

logger = MyLogger("Channel")

class Channel:
    """频道类，管理频道信息"""
    _channel_counter = 0
    _initialized = False
    
    @classmethod
    async def initialize_counter(cls):
        """从数据库初始化频道计数器"""
        if cls._initialized:
            return
            
        try:
            channels = await Database.find("channels", sort=[("_id", -1)], limit=1)
            if channels:
                max_id = channels[0]["_id"]
                cls._channel_counter = max_id
                logger.info(f"Channel counter initialized from database: starting from {max_id}")
            else:
                cls._channel_counter = 0
                logger.info("No existing channels found, starting counter from 0")
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize channel counter: {e}")
            import time
            cls._channel_counter = int(time.time() * 1000)
            cls._initialized = True
    
    def __init__(self, creator_user, channel_name, channel_description, category):
        if not Channel._initialized:
            raise RuntimeError("Channel counter not initialized. Call Channel.initialize_counter() first.")
            
        Channel._channel_counter += 1
        self.channel_id = Channel._channel_counter
        self.channel_name = channel_name
        self.channel_description = channel_description
        self.category = category
        self.creator_user_id = creator_user.user_id
        self.member_user_ids = [creator_user.user_id]
        self.message_ids = []
        self.is_public = True
        self.created_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
        
        logger.info(f"Created channel {self.channel_id}: {self.channel_name}")
    
    async def save_to_database(self) -> bool:
        """保存频道到数据库"""
        try:
            channel_dict = {
                "_id": self.channel_id,
                "channel_name": self.channel_name,
                "channel_description": self.channel_description,
                "category": self.category,
                "creator_user_id": self.creator_user_id,
                "member_user_ids": self.member_user_ids,
                "message_ids": self.message_ids,
                "is_public": self.is_public,
                "created_at": self.created_at,
                "updated_at": self.updated_at
            }
            
            existing_channel = await Database.find_one("channels", {"_id": self.channel_id})
            if existing_channel:
                await Database.update_one(
                    "channels",
                    {"_id": self.channel_id},
                    {"$set": {k: v for k, v in channel_dict.items() if k != "_id"}}
                )
            else:
                await Database.insert_one("channels", channel_dict)
            
            logger.info(f"Saved channel {self.channel_id} to database")
            return True
        except Exception as e:
            logger.error(f"Error saving channel {self.channel_id}: {e}")
            return False
```

#### 5.2.2 ChannelMessage对象
```python
# app/objects/ChannelMessage.py
from datetime import datetime, timezone
from app.core.database import Database
from app.utils.my_logger import MyLogger

logger = MyLogger("ChannelMessage")

class ChannelMessage:
    """频道消息类"""
    _message_counter = 0
    _initialized = False
    
    @classmethod
    async def initialize_counter(cls):
        """从数据库初始化消息计数器"""
        if cls._initialized:
            return
            
        try:
            messages = await Database.find("channel_messages", sort=[("_id", -1)], limit=1)
            if messages:
                max_id = messages[0]["_id"]
                cls._message_counter = max_id
                logger.info(f"ChannelMessage counter initialized from database: starting from {max_id}")
            else:
                cls._message_counter = 0
                logger.info("No existing channel messages found, starting counter from 0")
            cls._initialized = True
        except Exception as e:
            logger.error(f"Failed to initialize channel message counter: {e}")
            import time
            cls._message_counter = int(time.time() * 1000)
            cls._initialized = True
    
    def __init__(self, sender_user, channel_id, message_content):
        if not ChannelMessage._initialized:
            raise RuntimeError("ChannelMessage counter not initialized. Call ChannelMessage.initialize_counter() first.")
            
        ChannelMessage._message_counter += 1
        self.message_id = ChannelMessage._message_counter
        self.message_content = message_content
        self.message_sender_id = sender_user.user_id
        self.channel_id = channel_id
        self.message_send_time_in_utc = datetime.now(timezone.utc)
        self.message_type = "text"
        
        logger.info(f"Created channel message {self.message_id} from {self.message_sender_id} in channel {self.channel_id}")
    
    async def save_to_database(self) -> bool:
        """保存消息到数据库"""
        try:
            message_dict = {
                "_id": self.message_id,
                "message_content": self.message_content,
                "message_send_time_in_utc": self.message_send_time_in_utc,
                "message_sender_id": self.message_sender_id,
                "channel_id": self.channel_id,
                "message_type": self.message_type
            }
            
            existing_message = await Database.find_one("channel_messages", {"_id": self.message_id})
            if existing_message:
                logger.warning(f"Channel message {self.message_id} already exists - skipping save")
                return True
            else:
                await Database.insert_one("channel_messages", message_dict)
                logger.info(f"Saved channel message {self.message_id} to database")
                return True
        except Exception as e:
            logger.error(f"Error saving channel message {self.message_id}: {e}")
            return False
```

#### 5.2.3 ChannelManager服务
```python
# app/services/https/ChannelManager.py
from app.config import settings
from app.objects.Channel import Channel
from app.objects.ChannelMessage import ChannelMessage
from app.services.https.UserManagement import UserManagement
from app.core.database import Database
from app.utils.my_logger import MyLogger
from typing import Optional, List, Dict

logger = MyLogger("ChannelManager")

class ChannelManager:
    """频道管理器，管理所有频道"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.channels = {}  # {channel_id: Channel}
            logger.info("ChannelManager singleton instance created")
        return cls._instance
    
    async def construct(self) -> bool:
        """初始化ChannelManager，从数据库加载数据"""
        try:
            await Channel.initialize_counter()
            await ChannelMessage.initialize_counter()
            
            channels_data = await Database.find("channels")
            logger.info(f"Found {len(channels_data)} channels in database")
            
            loaded_count = 0
            user_manager = UserManagement()
            
            for channel_data in channels_data:
                try:
                    channel_id = channel_data["_id"]
                    creator_user_id = channel_data["creator_user_id"]
                    
                    creator_user = user_manager.get_user_instance(creator_user_id)
                    if creator_user:
                        channel = Channel(
                            creator_user,
                            channel_data["channel_name"],
                            channel_data["channel_description"],
                            channel_data["category"]
                        )
                        channel.channel_id = channel_id
                        channel.member_user_ids = channel_data.get("member_user_ids", [creator_user_id])
                        channel.message_ids = channel_data.get("message_ids", [])
                        channel.is_public = channel_data.get("is_public", True)
                        channel.created_at = channel_data.get("created_at")
                        channel.updated_at = channel_data.get("updated_at")
                        
                        self.channels[channel_id] = channel
                        loaded_count += 1
                        logger.info(f"Loaded channel {channel_id}: {channel.channel_name}")
                    else:
                        logger.warning(f"Creator user {creator_user_id} not found for channel {channel_id}")
                except Exception as e:
                    logger.error(f"Error loading channel: {e}")
                    continue
            
            logger.info(f"Loaded {loaded_count} channels from database")
            return True
        except Exception as e:
            logger.error(f"Error constructing ChannelManager: {e}")
            return False
    
    async def create_channel(self, creator_user_id: int, channel_name: str, 
                           channel_description: str, category: str, 
                           channel_avatar_url: str = None) -> Optional[int]:
        """创建新频道"""
        try:
            user_manager = UserManagement()
            creator_user = user_manager.get_user_instance(creator_user_id)
            if not creator_user:
                logger.error(f"Creator user {creator_user_id} not found")
                return None
            
            channel = Channel(creator_user, channel_name, channel_description, category)
            
            # 保存到数据库
            if await channel.save_to_database():
                self.channels[channel.channel_id] = channel
                logger.info(f"Created channel {channel.channel_id}: {channel_name}")
                return channel.channel_id
            else:
                logger.error(f"Failed to save channel {channel.channel_id} to database")
                return None
        except Exception as e:
            logger.error(f"Error creating channel: {e}")
            return None
    
    async def get_channels_list(self, user_id: Optional[int] = None, 
                              category: str = "all", page: int = 1, 
                              page_size: int = 20) -> Dict:
        """获取频道列表"""
        try:
            # 筛选频道
            filtered_channels = []
            for channel in self.channels.values():
                if category != "all" and channel.category != category:
                    continue
                if not channel.is_public:
                    continue
                
                # 计算成员数和在线数（简化实现）
                member_count = len(channel.member_user_ids)
                online_count = min(member_count, member_count // 10 + 1)  # 简化的在线数计算
                
                # 检查用户是否已加入
                is_member = user_id in channel.member_user_ids if user_id else False
                
                filtered_channels.append({
                    "channel_id": channel.channel_id,
                    "channel_name": channel.channel_name,
                    "channel_description": channel.channel_description,
                    "category": channel.category,
                    "member_count": member_count,
                    "online_count": online_count,
                    "is_member": is_member
                })
            
            # 分页
            total_channels = len(filtered_channels)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            paginated_channels = filtered_channels[start_idx:end_idx]
            
            return {
                "success": True,
                "total_channels": total_channels,
                "channels": paginated_channels
            }
        except Exception as e:
            logger.error(f"Error getting channels list: {e}")
            return {"success": False, "channels": []}
    
    async def join_channel(self, user_id: int, channel_id: int) -> bool:
        """加入频道"""
        try:
            channel = self.channels.get(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return False
            
            if user_id not in channel.member_user_ids:
                channel.member_user_ids.append(user_id)
                channel.updated_at = datetime.now(timezone.utc)
                
                # 保存到数据库
                if await channel.save_to_database():
                    logger.info(f"User {user_id} joined channel {channel_id}")
                    return True
                else:
                    # 回滚
                    channel.member_user_ids.remove(user_id)
                    return False
            else:
                logger.info(f"User {user_id} already in channel {channel_id}")
                return True
        except Exception as e:
            logger.error(f"Error joining channel: {e}")
            return False
    
    async def send_channel_message(self, channel_id: int, sender_user_id: int, 
                                 message_content: str) -> Dict:
        """发送频道消息"""
        try:
            channel = self.channels.get(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return {"success": False, "message_id": None}
            
            if sender_user_id not in channel.member_user_ids:
                logger.error(f"User {sender_user_id} not authorized for channel {channel_id}")
                return {"success": False, "message_id": None}
            
            user_manager = UserManagement()
            sender_user = user_manager.get_user_instance(sender_user_id)
            if not sender_user:
                logger.error(f"Sender user {sender_user_id} not found")
                return {"success": False, "message_id": None}
            
            # 创建消息
            message = ChannelMessage(sender_user, channel_id, message_content)
            
            # 保存消息到数据库
            if await message.save_to_database():
                # 添加消息ID到频道
                channel.message_ids.append(message.message_id)
                await channel.save_to_database()
                
                logger.info(f"Message {message.message_id} sent in channel {channel_id}")
                return {"success": True, "message_id": message.message_id}
            else:
                logger.error(f"Failed to save message to database")
                return {"success": False, "message_id": None}
        except Exception as e:
            logger.error(f"Error sending channel message: {e}")
            return {"success": False, "message_id": None}
    
    async def get_channel_history(self, channel_id: int, user_id: int, 
                                page: int = 1, page_size: int = 50) -> List:
        """获取频道聊天历史"""
        try:
            channel = self.channels.get(channel_id)
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return []
            
            if user_id not in channel.member_user_ids:
                logger.error(f"User {user_id} not authorized for channel {channel_id}")
                return []
            
            # 分页获取消息ID
            message_ids = channel.message_ids
            total_messages = len(message_ids)
            start_idx = max(0, total_messages - page * page_size)
            end_idx = total_messages - (page - 1) * page_size
            paginated_message_ids = message_ids[start_idx:end_idx]
            
            # 从数据库加载消息
            messages = []
            user_manager = UserManagement()
            
            for message_id in paginated_message_ids:
                try:
                    message_data = await Database.find_one("channel_messages", {"_id": message_id})
                    if message_data:
                        sender_user = user_manager.get_user_instance(message_data["message_sender_id"])
                        sender_name = "I" if message_data["message_sender_id"] == user_id else (
                            sender_user.telegram_user_name if sender_user else f"User{message_data['message_sender_id']}"
                        )
                        
                        # 格式化时间
                        send_time = message_data["message_send_time_in_utc"]
                        if hasattr(send_time, 'strftime'):
                            time_str = send_time.strftime("%H:%M")
                        else:
                            time_str = str(send_time)[:5]  # 简化处理
                        
                        messages.append({
                            "message_id": message_id,
                            "sender_name": sender_name,
                            "message_content": message_data["message_content"],
                            "send_time": time_str,
                            "is_own_message": message_data["message_sender_id"] == user_id
                        })
                except Exception as e:
                    logger.error(f"Error loading message {message_id}: {e}")
                    continue
            
            logger.info(f"Retrieved {len(messages)} messages for channel {channel_id}")
            return messages
        except Exception as e:
            logger.error(f"Error getting channel history: {e}")
            return []
```

### 5.3 WebSocket扩展

在现有的`MessageConnectionHandler`中添加频道支持：

```python
# 在app/WebSocketsService/MessageConnectionHandler.py中添加
class MessageConnectionHandler(ConnectionHandler):
    # 新增频道房间管理
    channel_rooms = {}  # {channel_id: {user_id: websocket}}
    
    async def on_message(self, message: dict):
        """处理消息，扩展支持频道消息"""
        message_type = message.get("type", "broadcast")
        
        if message_type == "channel_join":
            await self.handle_channel_join(message)
        elif message_type == "channel_message":
            await self.handle_channel_message(message)
        elif message_type == "channel_leave":
            await self.handle_channel_leave(message)
        elif message_type == "private_chat_init":
            # 保持现有的私聊功能
            await self.handle_private_chat_init(message)
        elif message_type == "private":
            # 保持现有的私聊功能
            await self.handle_private_message(message)
        elif message_type == "broadcast":
            # 保持现有的广播功能
            await self.handle_broadcast_message(message)
        else:
            await self.websocket.send_text(json.dumps({
                "error": f"Unknown message type: {message_type}"
            }))
    
    async def handle_channel_join(self, message: dict):
        """处理加入频道"""
        try:
            channel_id = int(message.get("channel_id"))
            user_id = int(self.user_id)
            
            # 检查用户是否有权限加入频道
            from app.services.https.ChannelManager import ChannelManager
            channel_manager = ChannelManager()
            
            channel = channel_manager.channels.get(channel_id)
            if not channel:
                await self.websocket.send_text(json.dumps({
                    "type": "channel_join_response",
                    "success": False,
                    "error": "Channel not found"
                }))
                return
            
            if user_id not in channel.member_user_ids:
                await self.websocket.send_text(json.dumps({
                    "type": "channel_join_response",
                    "success": False,
                    "error": "Not a member of this channel"
                }))
                return
            
            # 加入频道房间
            if channel_id not in self.channel_rooms:
                self.channel_rooms[channel_id] = {}
            self.channel_rooms[channel_id][self.user_id] = self.websocket
            
            # 计算在线人数
            online_count = len(self.channel_rooms[channel_id])
            
            # 响应加入成功
            await self.websocket.send_text(json.dumps({
                "type": "channel_join_response",
                "success": True,
                "channel_id": channel_id,
                "online_count": online_count,
                "message": "成功加入频道"
            }))
            
            # 通知其他成员
            await self.broadcast_to_channel(channel_id, json.dumps({
                "type": "channel_user_joined",
                "channel_id": channel_id,
                "user_name": self.user_id,  # 可以改为用户昵称
                "online_count": online_count
            }), exclude_user_id=self.user_id)
            
            logger.info(f"User {user_id} joined channel {channel_id}")
            
        except Exception as e:
            logger.error(f"Error handling channel join: {e}")
            await self.websocket.send_text(json.dumps({
                "type": "channel_join_response",
                "success": False,
                "error": "Internal server error"
            }))
    
    async def handle_channel_message(self, message: dict):
        """处理频道消息"""
        try:
            channel_id = int(message.get("channel_id"))
            content = message.get("content", "")
            user_id = int(self.user_id)
            
            if not content.strip():
                await self.websocket.send_text(json.dumps({
                    "type": "channel_message_status",
                    "success": False,
                    "error": "Message content cannot be empty"
                }))
                return
            
            # 发送消息到频道
            from app.services.https.ChannelManager import ChannelManager
            channel_manager = ChannelManager()
            
            result = await channel_manager.send_channel_message(channel_id, user_id, content)
            
            if result["success"]:
                # 获取发送者信息
                from app.services.https.UserManagement import UserManagement
                user_manager = UserManagement()
                sender_user = user_manager.get_user_instance(user_id)
                sender_name = sender_user.telegram_user_name if sender_user else f"User{user_id}"
                
                # 广播给频道所有成员
                await self.broadcast_to_channel(channel_id, json.dumps({
                    "type": "channel_message_received",
                    "channel_id": channel_id,
                    "message_id": result["message_id"],
                    "from": user_id,
                    "sender_name": sender_name,
                    "content": content,
                    "timestamp": message.get("timestamp")
                }), exclude_user_id=self.user_id)
                
                # 给发送者确认
                await self.websocket.send_text(json.dumps({
                    "type": "channel_message_status",
                    "channel_id": channel_id,
                    "message_id": result["message_id"],
                    "success": True,
                    "timestamp": message.get("timestamp")
                }))
            else:
                await self.websocket.send_text(json.dumps({
                    "type": "channel_message_status",
                    "success": False,
                    "error": "Failed to send message"
                }))
                
        except Exception as e:
            logger.error(f"Error handling channel message: {e}")
            await self.websocket.send_text(json.dumps({
                "type": "channel_message_status",
                "success": False,
                "error": "Internal server error"
            }))
    
    async def handle_channel_leave(self, message: dict):
        """处理离开频道"""
        try:
            channel_id = int(message.get("channel_id"))
            
            # 从频道房间移除
            if channel_id in self.channel_rooms and self.user_id in self.channel_rooms[channel_id]:
                del self.channel_rooms[channel_id][self.user_id]
                
                # 计算在线人数
                online_count = len(self.channel_rooms[channel_id])
                
                # 响应离开成功
                await self.websocket.send_text(json.dumps({
                    "type": "channel_leave_response",
                    "success": True,
                    "channel_id": channel_id,
                    "online_count": online_count
                }))
                
                # 通知其他成员
                await self.broadcast_to_channel(channel_id, json.dumps({
                    "type": "channel_user_left",
                    "channel_id": channel_id,
                    "user_name": self.user_id,  # 可以改为用户昵称
                    "online_count": online_count
                }), exclude_user_id=self.user_id)
                
                logger.info(f"User {self.user_id} left channel {channel_id}")
                
        except Exception as e:
            logger.error(f"Error handling channel leave: {e}")
    
    async def broadcast_to_channel(self, channel_id: int, message: str, exclude_user_id: str = None):
        """向频道广播消息"""
        if channel_id not in self.channel_rooms:
            return
        
        room = self.channel_rooms[channel_id]
        disconnected = []
        
        for user_id, websocket in room.items():
            if exclude_user_id and user_id == exclude_user_id:
                continue
            try:
                await websocket.send_text(message)
            except Exception:
                disconnected.append(user_id)
        
        # 清理断开的连接
        for user_id in disconnected:
            room.pop(user_id, None)
    
    async def on_disconnect(self):
        """用户断开连接时清理频道房间"""
        # 从所有频道房间中移除用户
        for channel_id, room in self.channel_rooms.items():
            if self.user_id in room:
                del room[self.user_id]
        
        await super().on_disconnect()
```

## 六、前端集成指南

### 6.1 微信小程序API调用示例

#### 6.1.1 获取频道列表
```javascript
// 页面加载时获取频道列表
Page({
  data: {
    channels: []
  },
  
  onLoad: function() {
    this.loadChannels();
  },
  
  loadChannels: function() {
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ChannelManager/get_channels_list',
      method: 'POST',
      data: {
        user_id: 123456,
        category: 'all',
        page: 1,
        page_size: 20
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            channels: res.data.channels
          });
        }
      },
      fail: (err) => {
        console.error('获取频道列表失败:', err);
        wx.showToast({
          title: '加载失败',
          icon: 'error'
        });
      }
    });
  },
  
  // 点击频道进入聊天页面
  onChannelTap: function(e) {
    const channelId = e.currentTarget.dataset.channelId;
    const channelName = e.currentTarget.dataset.channelName;
    
    wx.navigateTo({
      url: `/pages/channel-chat/index?channelId=${channelId}&channelName=${channelName}`
    });
  }
});
```

#### 6.1.2 创建频道
```javascript
// 创建频道页面
Page({
  data: {
    channelName: '',
    channelDescription: '',
    category: 'General Topics'
  },
  
  onChannelNameInput: function(e) {
    this.setData({
      channelName: e.detail.value
    });
  },
  
  onDescriptionInput: function(e) {
    this.setData({
      channelDescription: e.detail.value
    });
  },
  
  onCategoryChange: function(e) {
    this.setData({
      category: e.detail.value
    });
  },
  
  createChannel: function() {
    if (!this.data.channelName.trim()) {
      wx.showToast({
        title: '请输入频道名称',
        icon: 'error'
      });
      return;
    }
    
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ChannelManager/create_channel',
      method: 'POST',
      data: {
        creator_user_id: 123456,
        channel_name: this.data.channelName,
        channel_description: this.data.channelDescription,
        category: this.data.category
      },
      success: (res) => {
        if (res.data.success) {
          wx.showToast({
            title: '创建成功',
            icon: 'success'
          });
          
          // 跳转到新创建的频道
          setTimeout(() => {
            wx.navigateTo({
              url: `/pages/channel-chat/index?channelId=${res.data.channel_id}&channelName=${this.data.channelName}`
            });
          }, 1500);
        }
      },
      fail: (err) => {
        console.error('创建频道失败:', err);
        wx.showToast({
          title: '创建失败',
          icon: 'error'
        });
      }
    });
  }
});
```

### 6.2 频道聊天页面WebSocket集成

```javascript
// 频道聊天页面
Page({
  data: {
    channelId: 0,
    channelName: '',
    messages: [],
    inputValue: '',
    onlineCount: 0
  },
  
  onLoad: function(options) {
    this.setData({
      channelId: parseInt(options.channelId),
      channelName: options.channelName
    });
    
    this.connectWebSocket();
    this.loadChatHistory();
  },
  
  connectWebSocket: function() {
    this.socketTask = wx.connectSocket({
      url: 'wss://lovetapoversea.xyz:4433/ws/message',
      success: (res) => {
        console.log('WebSocket连接成功');
      }
    });
    
    this.socketTask.onOpen((res) => {
      console.log('WebSocket连接已打开');
      
      // 发送认证消息
      this.socketTask.send({
        data: JSON.stringify({
          user_id: "123456"
        })
      });
    });
    
    this.socketTask.onMessage((res) => {
      const data = JSON.parse(res.data);
      this.handleWebSocketMessage(data);
    });
    
    this.socketTask.onError((res) => {
      console.error('WebSocket连接错误:', res);
      wx.showToast({
        title: '连接失败',
        icon: 'error'
      });
    });
  },
  
  handleWebSocketMessage: function(data) {
    switch(data.type) {
      case 'authenticated':
        // 认证成功，加入频道房间
        this.joinChannelRoom();
        break;
        
      case 'channel_join_response':
        if (data.success) {
          this.setData({
            onlineCount: data.online_count
          });
          console.log('成功加入频道');
        } else {
          wx.showToast({
            title: data.error || '加入频道失败',
            icon: 'error'
          });
        }
        break;
        
      case 'channel_message_received':
        // 收到新的频道消息
        this.addMessage({
          message_id: data.message_id,
          sender_name: data.sender_name,
          message_content: data.content,
          send_time: this.formatTime(data.timestamp),
          is_own_message: false
        });
        break;
        
      case 'channel_message_status':
        if (data.success) {
          // 自己发送的消息确认
          console.log('消息发送成功');
        } else {
          wx.showToast({
            title: '发送失败',
            icon: 'error'
          });
        }
        break;
        
      case 'channel_user_joined':
      case 'channel_user_left':
        // 更新在线人数
        this.setData({
          onlineCount: data.online_count
        });
        break;
    }
  },
  
  joinChannelRoom: function() {
    this.socketTask.send({
      data: JSON.stringify({
        type: "channel_join",
        channel_id: this.data.channelId
      })
    });
  },
  
  loadChatHistory: function() {
    wx.request({
      url: 'https://lovetapoversea.xyz:4433/api/v1/ChannelManager/get_channel_history',
      method: 'POST',
      data: {
        channel_id: this.data.channelId,
        user_id: 123456,
        page: 1,
        page_size: 50
      },
      success: (res) => {
        if (res.data.success) {
          this.setData({
            messages: res.data.messages
          });
          // 滚动到底部
          this.scrollToBottom();
        }
      }
    });
  },
  
  onInputChange: function(e) {
    this.setData({
      inputValue: e.detail.value
    });
  },
  
  sendMessage: function() {
    const content = this.data.inputValue.trim();
    if (!content) {
      return;
    }
    
    // 通过WebSocket发送消息
    this.socketTask.send({
      data: JSON.stringify({
        type: "channel_message",
        channel_id: this.data.channelId,
        content: content,
        timestamp: new Date().toISOString()
      })
    });
    
    // 立即显示自己的消息（乐观更新）
    this.addMessage({
      message_id: Date.now(), // 临时ID
      sender_name: "I",
      message_content: content,
      send_time: this.formatTime(new Date()),
      is_own_message: true
    });
    
    // 清空输入框
    this.setData({
      inputValue: ''
    });
  },
  
  addMessage: function(message) {
    const messages = this.data.messages;
    messages.push(message);
    this.setData({
      messages: messages
    });
    this.scrollToBottom();
  },
  
  formatTime: function(timestamp) {
    const date = new Date(timestamp);
    return date.toTimeString().substring(0, 5); // HH:MM格式
  },
  
  scrollToBottom: function() {
    // 滚动到消息列表底部
    this.createSelectorQuery().select('#message-list').boundingClientRect((rect) => {
      wx.pageScrollTo({
        scrollTop: rect.height,
        duration: 300
      });
    }).exec();
  },
  
  onUnload: function() {
    // 页面卸载时离开频道房间
    if (this.socketTask) {
      this.socketTask.send({
        data: JSON.stringify({
          type: "channel_leave",
          channel_id: this.data.channelId
        })
      });
      this.socketTask.close();
    }
  }
});
```

## 七、部署和配置

### 7.1 数据库初始化

在服务器启动时，需要确保频道管理器正确初始化：

```python
# 在app/server_run.py中添加
@app.on_event("startup")
async def startup_event():
    from app.services.https.ChannelManager import ChannelManager
    
    # 初始化现有的管理器
    user_manager = UserManagement()
    await user_manager.construct()
    
    match_manager = MatchManager()
    await match_manager.construct()
    
    chatroom_manager = ChatroomManager()
    await chatroom_manager.construct()
    
    # 新增：初始化频道管理器
    channel_manager = ChannelManager()
    await channel_manager.construct()
    
    logger.info("All managers initialized successfully")
```

### 7.2 路由注册

```python
# 在app/server_run.py中注册新的API路由
from app.api.v1 import ChannelManager

# 注册API路由
app.include_router(ChannelManager.router, prefix="/api/v1/ChannelManager", tags=["频道管理"])
```

### 7.3 数据库索引创建

```javascript
// 在MongoDB中执行以下命令创建索引
use local_test_db

// channels集合索引
db.channels.createIndex({"_id": 1}, {unique: true})
db.channels.createIndex({"category": 1})
db.channels.createIndex({"creator_user_id": 1})
db.channels.createIndex({"member_user_ids": 1})

// channel_messages集合索引
db.channel_messages.createIndex({"_id": 1}, {unique: true})
db.channel_messages.createIndex({"channel_id": 1, "message_send_time_in_utc": -1})
db.channel_messages.createIndex({"message_sender_id": 1})
```

## 八、测试和验证

### 8.1 API测试用例

可以使用以下curl命令测试API：

```bash
# 创建频道
curl -X POST "http://localhost:8000/api/v1/ChannelManager/create_channel" \
  -H "Content-Type: application/json" \
  -d '{
    "creator_user_id": 123456,
    "channel_name": "测试频道",
    "channel_description": "这是一个测试频道",
    "category": "测试"
  }'

# 获取频道列表
curl -X POST "http://localhost:8000/api/v1/ChannelManager/get_channels_list" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456,
    "category": "all",
    "page": 1,
    "page_size": 10
  }'

# 加入频道
curl -X POST "http://localhost:8000/api/v1/ChannelManager/join_channel" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456,
    "channel_id": 1
  }'
```

### 8.2 WebSocket测试

可以使用WebSocket测试工具或浏览器控制台测试：

```javascript
// 连接WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/message');

// 认证
ws.onopen = function() {
  ws.send(JSON.stringify({
    user_id: "123456"
  }));
};

// 加入频道
ws.send(JSON.stringify({
  type: "channel_join",
  channel_id: 1
}));

// 发送频道消息
ws.send(JSON.stringify({
  type: "channel_message",
  channel_id: 1,
  content: "Hello from WebSocket!",
  timestamp: new Date().toISOString()
}));
```

## 九、扩展功能规划

### 9.1 第一阶段扩展（优先级高）
- 频道搜索功能
- 频道分类管理
- 消息@提及功能
- 消息删除功能

### 9.2 第二阶段扩展（优先级中）
- 频道管理员功能
- 私有频道支持
- 频道邀请链接
- 消息表情回应

### 9.3 第三阶段扩展（优先级低）
- 文件和图片消息
- 语音消息支持
- 频道公告功能
- 消息置顶功能

## 十、维护和监控

### 10.1 日志监控
- 频道创建/加入/离开日志
- 消息发送成功率监控
- WebSocket连接状态监控
- 数据库操作性能监控

### 10.2 性能优化
- 频道列表缓存策略
- 消息历史分页优化
- WebSocket连接池管理
- 数据库查询优化

### 10.3 错误处理
- WebSocket连接断开重连机制
- 消息发送失败重试机制
- 数据库操作异常处理
- 用户权限验证异常处理

---

## 总结

本设计文档详细描述了基于现有双人聊天室架构的频道群聊系统。该方案具有以下特点：

1. **高度复用**：复用90%以上的现有代码和架构
2. **简单实用**：专注核心功能，避免过度设计
3. **易于实现**：分阶段开发，快速上线
4. **扩展性强**：预留了丰富的扩展功能接口
5. **维护性好**：遵循现有的代码规范和架构模式

该系统完全满足微信小程序的使用需求，提供了流畅的群聊体验，同时保持了与现有系统的完美兼容。
