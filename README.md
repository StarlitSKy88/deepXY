# DeepXY 🚀

DeepXY 是一个创新的 AI 对话系统，结合了 DeepSeek 的强大推理能力和其他模型的生成能力。

## 特点 ✨

- 💡 **双模型协作**: 结合 DeepSeek 的推理能力和 Qwen 的生成能力
- 🌊 **流式输出**: 支持实时流式响应
- 🔌 **OpenAI 兼容**: 完全兼容 OpenAI API 格式
- 🎯 **高性能**: 优化的并发处理和错误重试机制
- 📝 **详细日志**: 结构化的日志记录系统

## 快速开始 🚀

### Docker 部署

```bash
# 克隆项目
git clone https://github.com/StarlitSKy88/deepXY.git
cd deepXY

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填写必要的配置

# 启动服务
docker-compose up -d
```

### 本地开发

```bash
# 安装依赖
uv sync

# 启动服务
uvicorn app.main:app --reload
```

## 支持的模型 📚

- DeepSeek R1
- 通义千问 2.5
- Google Gemini 2.0 Pro
- Anthropic Claude 3 Sonnet
- Meta Llama 2
- Mistral Large

## API 使用示例 💻

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    headers={
        "Authorization": "Bearer your-api-key",
        "Content-Type": "application/json"
    },
    json={
        "model": "deepxy",
        "messages": [{"role": "user", "content": "你好"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 配置说明 ⚙️

主要配置项（在 .env 文件中设置）：

```bash
# API 认证配置
ALLOW_API_KEY=your-api-key
ALLOW_ORIGINS=*

# 模型配置
DEEPSEEK_MODEL=deepseek-r1
QWEN_MODEL=qwen2.5-14b-instruct-1m

# 推理配置
IS_ORIGIN_REASONING=True

# 日志配置
LOG_LEVEL=INFO
```

## 开发计划 📅

- [ ] 添加更多模型支持
- [ ] 优化并发性能
- [ ] 添加 WebSocket 支持
- [ ] 完善监控系统
- [ ] 添加单元测试

## 贡献指南 🤝

欢迎提交 Issue 和 Pull Request！

## 许可证 📄

[MIT License](LICENSE)