# 校园交友小程序后端

## 项目简介

这是一个基于Python的校园交友小程序后端系统，提供用户管理、匹配算法、聊天室、AI交互等核心功能。

## 主要功能

### 🔐 用户管理
- 用户注册、登录、认证
- 个人信息管理
- 用户状态管理

### 💕 智能匹配
- 基于性格测试的匹配算法
- 多维度用户匹配
- 匹配会话管理

### 💬 聊天系统
- 实时聊天功能
- WebSocket支持
- 聊天室管理

### 🤖 AI交互
- 智能对话系统
- 性格测试生成
- 多AI模型支持（Claude、Gemini、Kimi等）



## 技术架构

- **后端框架**: Python + FastAPI
- **数据库**: 支持多种数据库后端
- **实时通信**: WebSocket
- **AI集成**: 多AI模型API集成
- **部署**: 支持HTTPS和SSL

## 项目结构

```
Campus_friendship_miniapp_backend/
├── app/                    # 主应用目录
│   ├── api/v1/            # API接口
│   ├── core/              # 核心功能
│   ├── objects/           # 数据模型
│   ├── services/          # 业务服务
│   ├── utils/             # 工具函数
│   ├── prompts/           # AI提示词
│   ├── schemas/           # 数据模式
│   └── WebSocketsService/ # WebSocket服务
├── docs/                  # 项目文档
├── tests/                 # 测试文件
├── logs/                  # 日志文件
├── requirements.txt       # 依赖包
└── 抽卡游戏前端调用指南.md # 前端集成指南
```

## 快速开始

### 环境要求
- Python 3.8+
- 相关依赖包（见requirements.txt）

### 安装步骤
1. 克隆仓库
```bash
git clone https://github.com/tsssy/Campus_friendship_miniapp_backend.git
cd Campus_friendship_miniapp_backend
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑.env文件，配置必要的环境变量
```

4. 运行应用
```bash
python app/server_run.py
```

## 配置说明

项目支持多种配置选项，包括：
- 数据库连接配置
- AI模型API密钥

- SSL证书配置

## API文档

详细的API文档请参考 `docs/` 目录下的相关文档。

## 贡献指南

欢迎提交Issue和Pull Request来改进这个项目！

## 许可证

本项目采用开源许可证，具体请查看LICENSE文件。

## 联系方式

如有问题或建议，请通过GitHub Issues联系我们。
