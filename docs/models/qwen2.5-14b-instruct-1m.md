# 通义千问2.5-14B-1M

## 模型信息

- **模型名称**: qwen2.5-14b-instruct-1m
- **发布方**: 阿里云通义实验室
- **更新时间**: 2025-01-27
- **API 端点**: https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions

## 模型特点

通义千问2.5-14B-1M是阿里云发布的大规模语言模型，具有以下特点：

1. 基于1M数据训练的指令微调版本
2. 支持流式输出
3. 具备中英双语能力
4. 适合对话和文本生成任务

## API 参数

### 请求参数

```json
{
    "model": "qwen2.5-14b-instruct-1m",
    "messages": [
        {"role": "user", "content": "用户输入"}
    ],
    "stream": true,
    "parameters": {
        "temperature": 0.7,
        "top_p": 0.95,
        "top_k": 40,
        "repetition_penalty": 1.0,
        "enable_search": false
    }
}
```

### 参数说明

- temperature: 控制输出的随机性，范围 0-1
- top_p: 控制输出的多样性，范围 0-1
- top_k: 控制每次生成时从概率最高的 k 个词中采样
- repetition_penalty: 重复惩罚系数
- enable_search: 是否启用搜索增强

## 使用示例

```python
import requests
import json

url = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {api_key}"
}

data = {
    "model": "qwen2.5-14b-instruct-1m",
    "messages": [
        {"role": "user", "content": "你好，请介绍一下你自己"}
    ],
    "stream": True,
    "parameters": {
        "temperature": 0.7,
        "top_p": 0.95
    }
}

response = requests.post(url, headers=headers, json=data, stream=True)
for line in response.iter_lines():
    if line:
        print(json.loads(line.decode('utf-8').split('data: ')[1]))
```

## 注意事项

1. 使用前需要先获取阿里云的 API Key
2. 建议在生产环境中使用 stream=True 来获得更好的用户体验
3. 根据具体场景调整 temperature 和 top_p 参数
4. 注意请求频率限制和并发限制
5. 建议实现错误重试机制

## 最佳实践

1. 合理设置 temperature 和 top_p：
   - 对于需要创意的场景，可以适当提高 temperature
   - 对于需要准确性的场景，建议降低 temperature

2. 正确处理流式响应：
   - 实现适当的缓冲机制
   - 处理好断线重连
   - 注意错误处理

3. 优化提示词：
   - 使用清晰、具体的指令
   - 提供足够的上下文
   - 避免模糊不清的表述

4. 性能优化：
   - 实现连接池
   - 使用异步请求
   - 做好并发控制

## 更新日志

### 2025-01-27
- 发布通义千问2.5-14B-1M模型
- 优化了模型的中文理解能力
- 提升了指令遵循能力
- 改进了多轮对话的连贯性 