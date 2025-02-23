# DeepClaude 项目说明

## 项目简介

DeepClaude 是一个基于多模型协作的 AI 助手系统，它结合了 DeepSeek 的强大推理能力和其他模型的生成能力，提供了一个强大的 AI 对话系统。

## 特点

- 支持多种大语言模型
- 流式输出响应
- OpenAI 兼容的 API 接口
- 支持模型动态切换
- 完整的中文支持

## 支持的模型

### 推理模型（第一阶段）
- DeepSeek R1
- 支持自定义推理模型

### 生成模型（第二阶段）
- 通义千问 2.5
- Google Gemini 2.0 Pro
- Anthropic Claude 3 Sonnet
- Meta Llama 2
- Mistral Large

## 模型切换指南

### 1. 通过环境变量切换

在 `.env` 文件中配置：

```bash
# 推理模型配置
DEEPSEEK_MODEL=deepseek-r1

# 生成模型配置
QWEN_MODEL=qwen2.5-14b-instruct-1m
```

### 2. 通过 API 请求切换

在发送请求时通过 `model` 参数指定：

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Authorization: Bearer $ALLOW_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "google/gemini-2.0-pro-exp-02-05:free",
    "messages": [{"role": "user", "content": "你好"}],
    "stream": true
  }'
```

### 3. 在 Obsidian 插件中切换

在插件设置中：
1. 选择"生成模型"下拉菜单
2. 可选择以下模型：
   - 通义千问 2.5 (qwen2.5-14b-instruct-1m)
   - Gemini 2.0 Pro (google/gemini-2.0-pro-exp-02-05:free)
   - Claude 3 Sonnet (anthropic/claude-3-sonnet)

## API 格式说明

### 请求格式

```json
{
  "model": "模型名称",
  "messages": [
    {"role": "user", "content": "用户输入"}
  ],
  "stream": true,
  "temperature": 0.7,
  "top_p": 0.95
}
```

### 响应格式

```json
{
  "id": "chatcmpl-xxx",
  "object": "chat.completion.chunk",
  "created": 1709123456,
  "model": "使用的模型名称",
  "choices": [{
    "index": 0,
    "delta": {
      "role": "assistant",
      "reasoning_content": "推理内容",
      "content": "生成内容"
    }
  }]
}
```

## 模型特点对比

### DeepSeek R1
- 优势：强大的推理能力
- 适用：复杂问题分析、逻辑推理

### 通义千问 2.5
- 优势：优秀的中文理解和生成能力
- 适用：日常对话、文本创作

### Gemini 2.0 Pro
- 优势：强大的多模态能力
- 适用：图文理解、代码生成

### Claude 3 Sonnet
- 优势：优秀的文本生成和任务执行能力
- 适用：长文本生成、专业写作

## 最佳实践

1. 选择合适的模型组合：
   - 代码生成：DeepSeek R1 + Claude 3 Sonnet
   - 中文创作：DeepSeek R1 + 通义千问 2.5
   - 多模态任务：DeepSeek R1 + Gemini 2.0 Pro

2. 参数调优：
   - temperature：控制输出随机性（0.1-1.0）
   - top_p：控制输出多样性（0.1-1.0）

3. 错误处理：
   - 实现请求重试机制
   - 添加超时处理
   - 记录详细日志

## 常见问题

1. 模型切换失败
   - 检查 API 密钥是否正确
   - 确认模型名称拼写正确
   - 验证环境变量配置

2. 响应延迟
   - 检查网络连接
   - 考虑使用更快的模型
   - 优化请求参数

3. 内容质量问题
   - 调整模型参数
   - 选择更适合的模型
   - 优化提示词 