# DeepClaude 部署指南

## 目录
- [本地开发环境部署](#本地开发环境部署)
- [Docker部署](#docker部署)
- [Railway云平台部署](#railway云平台部署)
- [环境变量配置](#环境变量配置)

## 本地开发环境部署

### 1. 克隆项目
```bash
git clone <your-repository-url>
cd your-project-name
```

### 2. 安装依赖
```bash
# 使用 uv 包管理器安装依赖
uv sync

# 激活虚拟环境
# macOS/Linux
source .venv/bin/activate
# Windows
.venv\Scripts\activate
```

### 3. 配置环境变量
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，填入必要的配置
ALLOW_API_KEY=your_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENROUTER_API_KEY=your_openrouter_api_key
```

### 4. 启动服务
```bash
uvicorn app.main:app --reload
```

## Docker部署

### 使用 Docker Compose（推荐）

1. 创建 docker-compose.yml：
```yaml
services:
  deepclaude:
    build: .
    ports:
      - "8000:8000"
    environment:
      ALLOW_API_KEY: your_api_key
      DASHSCOPE_API_KEY: your_dashscope_api_key
      OPENROUTER_API_KEY: your_openrouter_api_key
      DEEPSEEK_MODEL: deepseek-r1
      QWEN_MODEL: qwen2.5-14b-instruct-1m
      IS_ORIGIN_REASONING: "true"
      LOG_LEVEL: "INFO"
    restart: always
```

2. 启动服务：
```bash
docker-compose up -d
```

### 手动构建Docker

1. 构建镜像：
```bash
docker build -t deepclaude:latest .
```

2. 运行容器：
```bash
docker run -d \
    -p 8000:8000 \
    -e ALLOW_API_KEY=your_api_key \
    -e DASHSCOPE_API_KEY=your_dashscope_api_key \
    -e OPENROUTER_API_KEY=your_openrouter_api_key \
    -e DEEPSEEK_MODEL=deepseek-r1 \
    -e QWEN_MODEL=qwen2.5-14b-instruct-1m \
    -e IS_ORIGIN_REASONING=true \
    -e LOG_LEVEL=INFO \
    --restart always \
    deepclaude:latest
```

## Railway云平台部署

1. Fork项目到你的GitHub账号

2. 访问 [Railway](https://railway.app)

3. 点击 "Deploy a new project"

4. 选择 "Deploy from GitHub repo"

5. 配置环境变量：
   - ALLOW_API_KEY
   - DASHSCOPE_API_KEY
   - OPENROUTER_API_KEY
   - 其他必要的环境变量

6. 设置域名和端口(8000)

## 环境变量配置

### 必需的环境变量
- `ALLOW_API_KEY`: API访问密钥
- `DASHSCOPE_API_KEY`: 阿里云DashScope API密钥
- `OPENROUTER_API_KEY`: OpenRouter API密钥（用于访问其他模型）

### 可选的环境变量
- `DEEPSEEK_MODEL`: DeepSeek模型名称（默认：deepseek-r1）
- `QWEN_MODEL`: 通义千问模型名称（默认：qwen2.5-14b-instruct-1m）
- `IS_ORIGIN_REASONING`: 是否启用原生推理（默认：true）
- `LOG_LEVEL`: 日志级别（默认：INFO）
- `ALLOW_ORIGINS`: 允许的跨域来源（默认：*）

### API地址配置
- `DASHSCOPE_API_URL`: DashScope API地址
- `OPENROUTER_API_URL`: OpenRouter API地址

## 验证部署

服务启动后，可以通过以下方式验证：

1. 访问API文档：
```
http://localhost:8000/docs
```

2. 测试API连接：
```bash
curl http://localhost:8000/v1/models \
  -H "Authorization: Bearer your_api_key"
```

## 常见问题

1. 环境变量未正确配置
   - 检查 .env 文件是否存在
   - 确认所有必需的环境变量都已设置

2. API密钥无效
   - 验证 DASHSCOPE_API_KEY 是否正确
   - 确认 OPENROUTER_API_KEY 是否有效

3. 端口占用
   - 修改docker-compose.yml中的端口映射
   - 或使用其他可用端口启动服务 