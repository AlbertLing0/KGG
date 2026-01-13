# API错误处理改进说明

## 问题分析

### 原始问题

1. **API权限错误（403）**：
   - 错误信息：`your account is disabled`
   - 原因：API账户被禁用或权限不足

2. **JSON解析错误**：
   - 当API返回错误时，`call_llm()` 返回错误字符串（如 `"API call error: Error code: 403..."`）
   - `generate_graph_data()` 尝试将这个错误字符串当作JSON解析
   - 导致二次错误：`JSON parsing error: Expecting value: line 1 column 1 (char 0)`

### 根本原因

代码逻辑问题：
- `call_llm()` 在API调用失败时返回错误字符串
- `generate_graph_data()` 没有检查返回内容是否是错误信息
- 直接尝试将错误字符串解析为JSON，导致解析失败

## 修复方案

### 1. 改进错误检测

在 `utils.py` 的 `generate_graph_data()` 函数中，添加错误信息检测：

```python
# 检查是否是错误信息（API调用失败时返回的错误字符串）
if output_stripped.startswith("API call error:"):
    # 这是API调用错误，直接抛出异常，不要尝试解析JSON
    error_details = output_stripped.replace("API call error: ", "")
    raise ValueError(f"API调用失败: {error_details}")
```

### 2. 改进异常处理

将异常处理分为三类：

1. **JSON解析错误**：显示原始内容和解析错误
2. **API调用错误（ValueError）**：显示清晰的错误信息和解决建议
3. **其他未知错误**：显示详细堆栈信息

### 3. 用户友好的错误提示

当检测到API调用失败时，提供解决建议：
- 检查API密钥是否正确
- 检查API账户是否可用
- 检查网络连接是否正常
- 检查模型名称是否正确

## 修复后的效果

### 之前
```
API call error: Error code: 403 - {'code': 'permission_error', 'message': 'your account is disabled'}
JSON parsing error: Expecting value: line 1 column 1 (char 0) Actual output: API call error: ...
❌ Full graph data after merging is empty.
```

### 之后
```
❌ API调用失败: Error code: 403 - {'code': 'permission_error', 'message': 'your account is disabled'}
💡 请检查：
1. API密钥是否正确
2. API账户是否可用
3. 网络连接是否正常
4. 模型名称是否正确
```

## 如何解决403错误

### 可能的原因

1. **账户被禁用**：API服务提供商禁用了你的账户
2. **API密钥无效**：密钥已过期或被撤销
3. **权限不足**：账户没有使用该模型的权限
4. **配额用尽**：账户的API调用配额已用完

### 解决步骤

1. **检查API账户状态**：
   - 登录API服务提供商的控制台
   - 检查账户状态和余额
   - 确认账户是否被禁用

2. **验证API密钥**：
   - 确认API密钥是否正确
   - 检查密钥是否过期
   - 尝试重新生成API密钥

3. **检查模型权限**：
   - 确认账户是否有权限使用 `claude-sonnet-4-20250514` 模型
   - 检查模型名称是否正确

4. **联系服务提供商**：
   - 如果账户被禁用，联系API服务提供商
   - 申请恢复账户或创建新账户

## 代码改进点

### 改进前
```python
output = call_llm(...)
output = output.strip()
result = json.loads(output)  # 如果output是错误信息，这里会失败
```

### 改进后
```python
output = call_llm(...)
if output.startswith("API call error:"):
    raise ValueError(f"API调用失败: {error_details}")  # 直接抛出，不尝试解析
output = output.strip()
result = json.loads(output)  # 只有正常响应才会到这里
```

## 测试建议

1. **测试正常情况**：使用有效的API密钥和账户，验证功能正常
2. **测试错误情况**：使用无效的API密钥，验证错误提示是否清晰
3. **测试网络错误**：断开网络，验证错误处理是否正常

## 更新日志

- **2024-XX-XX**: 改进API错误处理，避免将错误信息当作JSON解析
- **2024-XX-XX**: 添加用户友好的错误提示和解决建议
