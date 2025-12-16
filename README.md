# 数据畸变助手 (Data Mutation Agent)

一个基于 LangChain 框架的智能数据畸变系统，用于生成测试数据，通过智能化的畸变策略生成各种边界场景、异常场景的测试数据。

## 功能特性

- 🎯 **多类型支持**: 支持整数、字符串、日期等多种数据类型
- 🔧 **智能畸变**: 自动生成边界值、特殊值、异常值等测试数据
- 🔀 **笛卡尔积组合**: 自动生成所有可能的数据组合
- 📊 **智能采样**: 支持随机采样、分层采样等多种策略
- 📁 **文件输出**: 自动生成 JSON 格式的测试数据文件
- 🛠️ **工具化设计**: 基于 LangChain Tool 实现，易于扩展

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 运行测试

```bash
python test_mutation_agent.py
```

### 使用示例

```python
from agents.mutation_agent import DataMutationAgent

# 创建智能体
agent = DataMutationAgent()

# 配置
config = {
    "dir": "./output",
    "data": [
        {
            "name": "user_id",
            "type": "integer",
            "value": 1001,
            "range": "1-1000000",
            "policy": "边界值"
        },
        {
            "name": "username",
            "type": "string",
            "value": "张三",
            "length": "20",
            "policy": ["生成随机长度中文字符", "生成超长字符", "生成合法中文姓名"]
        }
    ],
    "sum": 10,
    "sample_strategy": "random"
}

# 运行
result = agent.run(config)
```

## 畸变策略

### 整数类型

- **边界值**: 最小值、最大值、最小值-1、最大值+1、0
- **特殊值**: 负数、超大数、NULL
- **随机值**: 范围内随机值

### 字符串类型

- **空字符串**: ""
- **生成随机长度中文字符**: 不同长度的中文字符串
- **生成超长字符**: 超过最大长度限制
- **生成合法中文姓名**: 常见中文姓名
- **特殊字符**: SQL注入、XSS等安全测试字符
- **Emoji**: 包含emoji表情的字符串

### 日期类型

- **格式错误(YYYYMMDD)**: 不同的日期格式
- **未来日期**: 超出当前日期
- **无效日期(如2月30日)**: 不存在的日期
- **边界值**: 范围的最小值和最大值
- **NULL值**: null、空字符串等

## 配置格式

```json
{
  "dir": "输出目录路径",
  "data": [
    {
      "name": "字段名称",
      "type": "数据类型 (integer|string|date)",
      "value": "示例值",
      "range": "数据范围 (整数: min-max, 日期: start/end)",
      "length": "字符串最大长度 (可选)",
      "policy": "畸变策略 (字符串或数组)"
    }
  ],
  "sum": "输出数据总数",
  "sample_strategy": "采样策略 (random|stratified|all)"
}
```

## 输出文件

执行后会在指定目录生成两个文件：

1. **total_mutation.json**: 畸变中间结果，包含每个字段的所有变异值
2. **result.json**: 最终采样结果，包含指定数量的测试数据

## 工具集

基于 LangChain 的 Tool 实现：

- **IntegerMutator**: 整数畸变工具
- **StringMutator**: 字符串畸变工具
- **DateMutator**: 日期畸变工具
- **CartesianProduct**: 笛卡尔积组合工具
- **SampleData**: 数据采样工具
- **SaveFile**: 文件保存工具

## 项目结构

```
datagen/
├── agents/
│   ├── __init__.py
│   └── mutation_agent.py      # 数据畸变智能体
├── examples/
│   └── sample_config.json     # 示例配置
├── output/                     # 输出目录
├── test_mutation_agent.py     # 测试脚本
├── requirements.txt            # 依赖
├── Plan.md                     # 设计文档
└── README.md                   # 说明文档
```

## 高级特性

### 分层采样

使用分层采样确保每个字段的每个变异值至少出现一次：

```python
config = {
    # ...
    "sample_strategy": "stratified"
}
```

### 组合爆炸警告

当字段数量较多且每个字段的变异值较多时，系统会自动计算组合总数并给出警告。

### 自定义策略

支持多种策略组合：

```python
"policy": ["边界值", "特殊值", "随机值"]
# 或
"policy": "边界值|特殊值|随机值"
```

## 开发计划

详见 [Plan.md](Plan.md) 设计文档。

## License

MIT

## 作者

数据畸变助手开发团队
