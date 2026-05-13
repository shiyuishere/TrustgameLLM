# 大模型配置说明

本目录包含大模型API的配置文件，支持多个大模型提供商，每个提供商可以配置多个模型和温度参数。

## 配置文件

- `llms.yaml`: 主要配置文件，定义所有大模型提供商和模型参数
- `README.md`: 本说明文档

## 配置格式

配置文件采用YAML格式，支持环境变量引用。基本结构如下：

```yaml
llms:
  - base_url: "https://api.deepseek.com/v1"
    api_key: "${DEEPSEEK_API_KEY}"
    models:
      - model: "deepseek-chat"
        mark: "DSV3"
        concurrency: 10
      - model: "deepseek-reasoner"
        mark: "DSR1"
        concurrency: 20
    temperatures:
      - 0.3
      - 0.5
      - 0.7
```

## 配置参数说明

### 顶层配置
- `llms`: 大模型提供商列表

### 每个提供商配置
- `base_url`: 大模型API的基础URL
- `api_key`: API密钥，支持环境变量引用（如 `${API_KEY_NAME}`）
- `models`: 支持的模型列表
- `temperatures`: 温度参数列表

### 模型配置
- `model`: 模型名称
- `mark`: 模型标识符（用于日志和结果标识）
- `concurrency`: 并发数，用于限制每个模型的并发请求数，设置太小将降低实验效率，设置太大可能导致API调用失败

## 环境变量设置

在项目根目录创建 `.env` 文件，设置相应的API密钥：

```env
# DeepSeek API
DEEPSEEK_API_KEY=your_deepseek_api_key_here

# Mistral AI API
MISTRAL_API_KEY=your_mistral_api_key_here

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

```

## 温度参数说明

温度参数控制模型输出的随机性：
- `0.0`: 最确定性，输出最一致
- `0.3`: 较低随机性，适合需要稳定性的任务
- `0.5`: 中等随机性，平衡创造性和一致性
- `0.7`: 较高随机性，适合需要创造性的任务
- `1.0`: 最高随机性，输出最多样化

## 配置组合

系统会自动为每个模型和温度组合生成独立的配置。例如：
- 1个模型 × 3个温度 = 3个配置组合
- 2个模型 × 3个温度 = 6个配置组合

## 注意事项

1. **API密钥安全**: 不要将API密钥直接写入配置文件，始终使用环境变量
2. **成本控制**: 不同模型的调用成本差异很大，请根据需求选择合适的模型
3. **可用性**: 确保配置的模型在对应提供商中可用
4. **速率限制**: 注意各提供商的API调用频率限制

## 故障排除

### 常见问题

1. **配置文件不存在**: 确保 `llms.yaml` 文件存在于正确路径
2. **环境变量未设置**: 检查 `.env` 文件中的API密钥是否正确设置
3. **模型不可用**: 验证模型名称是否在对应提供商中可用
4. **API调用失败**: 检查网络连接和API密钥有效性

### 调试建议

- 启用详细日志输出
- 检查API响应状态码
- 验证环境变量是否正确加载
