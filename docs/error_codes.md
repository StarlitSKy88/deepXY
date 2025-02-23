# DeepClaude 错误码说明文档

## 错误码格式

所有错误响应都遵循以下格式：

```json
{
    "error": {
        "message": "错误描述信息",
        "code": "错误代码",
        "status": 400,
        "details": {
            "additional": "附加信息"
        }
    }
}
```

## 错误码列表

### 认证相关 (4xx)

#### AUTH_ERROR (401)
- 描述：认证失败
- 常见原因：
  - API密钥无效或已过期
  - API密钥格式错误
  - 未提供API密钥
- 解决方案：
  - 检查API密钥是否正确
  - 确保请求头中包含正确的Authorization字段
  - 如需要，重新生成API密钥

### 请求相关 (4xx)

#### INVALID_REQUEST (400)
- 描述：无效的请求
- 常见原因：
  - 请求参数格式错误
  - 缺少必需参数
  - 参数值超出有效范围
- 解决方案：
  - 检查请求参数格式
  - 确保提供所有必需参数
  - 确保参数值在有效范围内

#### MODEL_NOT_FOUND (404)
- 描述：模型不存在
- 常见原因：
  - 指定的模型名称错误
  - 模型已下线或暂时不可用
- 解决方案：
  - 检查模型名称拼写
  - 查看可用模型列表
  - 选择其他可用模型

#### RATE_LIMIT (429)
- 描述：请求频率超限
- 常见原因：
  - 短时间内发送了过多请求
  - 超过了API调用配额
- 解决方案：
  - 降低请求频率
  - 实现请求队列
  - 考虑升级API配额

### 服务相关 (5xx)

#### API_ERROR (502)
- 描述：API调用失败
- 常见原因：
  - 上游服务暂时不可用
  - 网络连接问题
  - 服务内部错误
- 解决方案：
  - 检查网络连接
  - 稍后重试
  - 联系技术支持

#### TIMEOUT (504)
- 描述：请求超时
- 常见原因：
  - 服务响应时间过长
  - 网络延迟
  - 系统负载过高
- 解决方案：
  - 检查网络状态
  - 优化请求参数
  - 实现请求重试机制

## 错误处理最佳实践

1. 实现重试机制
   ```python
   @retry(max_retries=3, base_delay=1.0)
   async def make_api_call():
       # 发送请求
   ```

2. 错误日志记录
   ```python
   try:
       response = await api.request()
   except APIError as e:
       logger.error(f"API调用失败: {e.message}", extra={"error_code": e.error_code})
   ```

3. 用户友好的错误提示
   ```python
   def handle_error(error: DeepClaudeError) -> dict:
       return {
           "error": {
               "message": error.message,
               "code": error.error_code,
               "status": error.http_status
           }
       }
   ```

## 错误监控建议

1. 监控指标
   - 错误率
   - 错误类型分布
   - 响应时间
   - 重试次数

2. 告警设置
   - 错误率超过阈值
   - 连续失败次数
   - 响应时间异常
   - 特定错误码频繁出现

3. 日志分析
   - 错误模式识别
   - 性能瓶颈分析
   - 用户行为分析
   - 系统健康状况评估 