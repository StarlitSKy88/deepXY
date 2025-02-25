# DeepXY - 高级大语言模型组合服务（优化版）

[![Python Tests](https://github.com/StarlitSKy88/deepXY/actions/workflows/python-tests.yml/badge.svg)](https://github.com/StarlitSKy88/deepXY/actions/workflows/python-tests.yml)
[![Docker Image CI/CD](https://github.com/StarlitSKy88/deepXY/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/StarlitSKy88/deepXY/actions/workflows/docker-publish.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)

DeepXY是一个创新的服务，允许不同语言模型之间的组合和协作，以发挥各自的优势，创造更强大的AI体验。本项目在[DeepClaude](https://github.com/ErlichLiu/DeepClaude)的基础上进行了扩展和优化。

## 特点 ✨

* 💡 **双模型协作**: 结合 DeepSeek 的推理能力和其他模型的生成能力
* 🌊 **流式输出**: 支持实时流式响应
* 🔌 **OpenAI 兼容**: 完全兼容 OpenAI API 格式
* 🎯 **高性能**: 优化的并发处理和错误重试机制
* 📝 **详细日志**: 结构化的日志记录系统

## 项目进展

本项目已完成以下工作：

1. 清理了所有测试文件和缓存内容
2. 对比分析了与原DeepClaude项目的差异
3. 提出了具体的优化建议和实施计划

## 主要特性

### 1. 模型组合

- **DeepW组合**：DeepSeek + Qwen，结合DeepSeek的推理能力和Qwen的生成能力
- **DeepG组合**：DeepSeek + Gemini，利用DeepSeek的思考过程和Gemini的表达能力
- **DeepC组合**：DeepSeek + Claude，组合DeepSeek的推理和Claude的文本生成

### 2. 智能监控系统

- **性能监控**：实时跟踪每个模型的调用次数、成功率、响应时间和token使用情况
- **故障转移**：当一个模型出现故障时，自动切换到备用模型
- **响应缓存**：缓存常见查询的结果，减少重复API调用，提高响应速度
- **自动模型选择**：基于性能、可靠性或速度自动选择最佳模型

### 3. 灵活配置

- 支持通过环境变量配置所有API密钥和端点
- 可自定义缓存大小、过期时间和故障转移冷却时间
- 支持自定义模型参数，如温度、top_p等

## 与原项目的对比分析

### 优势

1. **监控系统更完善**：DeepXY实现了更完整的监控系统，包括性能监控、故障转移和响应缓存。
2. **抽象设计更好**：使用了抽象基类`ModelCombination`定义标准接口，使代码更加模块化。
3. **更多组合选项**：支持多种模型组合，提供更多选择。
4. **配置更灵活**：支持更多配置选项，可通过环境变量自定义。
5. **错误处理更完善**：实现了完整的错误处理系统，包括错误码和详细错误信息。

### 待优化的地方

1. **代码复杂度**：相比原项目，代码结构更复杂，可能增加理解和维护成本。
2. **API文档不完善**：需要添加更全面的API文档。
3. **测试覆盖率低**：需要提高测试覆盖率，尤其是对核心功能的测试。
4. **配置验证机制**：可以加强配置验证机制，确保所有必要配置都被正确设置。
5. **Docker配置**：可以进一步优化Docker配置，减小镜像大小，提高启动速度。

## 优化计划概述

我们已制定了详细的优化实施计划，分为三个阶段：

### 第一阶段（1-2周）
- 简化代码结构
- 完善配置验证机制
- 修复已知问题
- 改进API文档
- 优化Docker配置

### 第二阶段（3-4周）
- 增强错误处理
- 优化性能监控
- 添加单元测试
- 改进用户界面

### 第三阶段（5-8周）
- 添加更多模型组合
- 增强安全性
- 性能优化
- 添加用户反馈机制

## 快速开始

### 1. 克隆仓库
```bash
git clone https://github.com/StarlitSKy88/deepXY.git
cd deepXY
```

### 2. 配置环境变量
创建`.env`文件并添加以下内容：
```
# API密钥配置
ALLOW_API_KEY=your_own_api_key_for_authentication
DEEPSEEK_API_KEY=your_deepseek_api_key
DASHSCOPE_API_KEY=your_dashscope_api_key
OPENROUTER_API_KEY=your_openrouter_api_key

# API URL配置
DEEPSEEK_API_URL=https://api.deepseek.com/v1/chat/completions
DASHSCOPE_API_URL=https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation
OPENROUTER_API_URL=https://openrouter.ai/api/v1/chat/completions
```

### 3. 使用Docker运行
```bash
docker-compose up -d
```

## 如何获取和保护API密钥

为了使用DeepXY服务，您需要获取并配置以下API密钥：

### 获取API密钥
1. **DeepSeek API密钥**：访问[DeepSeek官网](https://www.deepseek.com)注册并申请API密钥
2. **通义千问API密钥**：访问[阿里云DashScope](https://dashscope.aliyun.com)注册获取API密钥
3. **OpenRouter API密钥**：访问[OpenRouter](https://openrouter.ai)注册获取，用于访问Gemini等模型

### 保护API密钥
为保护您的API密钥安全：
1. 永远不要将包含真实API密钥的`.env`文件提交到Git仓库
2. 确保项目的`.gitignore`包含`.env`文件
3. 在服务器上部署时，使用环境变量或安全的密钥管理工具
4. 定期轮换您的API密钥
5. 使用权限最小化原则设置API密钥的权限范围

## 文档目录

项目文档包含以下内容：

### 英文文档
- [API参考](./docs/api_reference.md) - API接口详细说明
- [部署指南](./docs/deployment.md) - 项目部署和配置说明
- [错误代码](./docs/error_codes.md) - 错误代码和解决方案

### 中文文档
- [优化建议](./docs/zh/优化建议.md) - 对比原项目的优化建议
- [优化计划](./docs/zh/优化计划.md) - 详细的优化实施计划

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
        "model": "deepW",  # 可选: deepW, deepG, deepC
        "messages": [{"role": "user", "content": "你好"}],
        "stream": True
    },
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 贡献

欢迎贡献代码、报告问题或提出新功能建议！请参阅[贡献指南](./CONTRIBUTING.md)。

## 许可证

MIT