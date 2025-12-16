# 数据畸变助手系统设计文档

## 1. 项目概述

### 1.1 项目目标
开发一个数据畸变助手系统，用于生成测试数据，通过智能化的畸变策略生成各种边界场景、异常场景的测试数据，帮助提高软件测试的覆盖率和质量。

### 1.2 核心功能
- 自动识别数据类型和特征
- 智能制定畸变策略
- 批量生成畸变测试数据
- 支持多种数据类型（整数、字符串、日期等）
- 支持笛卡尔积组合生成

### 1.3 技术栈
- **编程语言**: Python 3.10+
- **智能体框架**: LangChain / AutoGen
- **数据处理**: Pandas, NumPy
- **日期处理**: datetime, dateutil
- **配置格式**: JSON
- **日志**: logging
- **测试**: pytest

## 2. 系统架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    数据畸变助手系统                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌──────────────────┐                                  │
│  │  输入配置JSON     │                                  │
│  └────────┬─────────┘                                  │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────────────────────────────┐         │
│  │   数据类型识别智能体 (Agent 1)             │         │
│  │   - 解析输入配置                           │         │
│  │   - 识别数据类型和约束                      │         │
│  │   - 验证配置合法性                          │         │
│  └────────┬─────────────────────────────────┘         │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────────────────────────────┐         │
│  │   畸变策略制定智能体 (Agent 2)             │         │
│  │   - 根据数据类型推荐畸变策略                │         │
│  │   - 合并用户指定策略                        │         │
│  │   - 生成畸变规则集                          │         │
│  └────────┬─────────────────────────────────┘         │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────────────────────────────┐         │
│  │   数据畸变智能体 (Agent 3)                 │         │
│  │   - 执行畸变策略生成变异值                  │         │
│  │   - 笛卡尔积组合                            │         │
│  │   - 文件输出                                │         │
│  └────────┬─────────────────────────────────┘         │
│           │                                            │
│           ▼                                            │
│  ┌──────────────────┐                                  │
│  │  输出文件         │                                  │
│  │  - mutation.json  │                                  │
│  │  - result.json    │                                  │
│  └──────────────────┘                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### 2.2 核心模块

```
datagen/
├── agents/                    # 智能体模块
│   ├── __init__.py
│   ├── base_agent.py         # 智能体基类
│   ├── type_identifier.py    # 数据类型识别智能体
│   ├── strategy_maker.py     # 畸变策略制定智能体
│   └── data_mutator.py       # 数据畸变智能体
├── core/                      # 核心功能模块
│   ├── __init__.py
│   ├── data_types.py         # 数据类型定义
│   ├── validators.py         # 数据验证器
│   ├── mutators.py           # 畸变器实现
│   └── combiners.py          # 组合器（笛卡尔积）
├── strategies/                # 畸变策略库
│   ├── __init__.py
│   ├── integer_strategies.py # 整数畸变策略
│   ├── string_strategies.py  # 字符串畸变策略
│   ├── date_strategies.py    # 日期畸变策略
│   └── custom_strategies.py  # 自定义策略
├── utils/                     # 工具模块
│   ├── __init__.py
│   ├── file_handler.py       # 文件处理
│   ├── logger.py             # 日志工具
│   └── config_parser.py      # 配置解析
├── tests/                     # 测试模块
│   ├── __init__.py
│   ├── test_agents.py
│   ├── test_mutators.py
│   └── test_integration.py
├── examples/                  # 示例文件
│   └── sample_config.json
├── main.py                    # 主入口
├── requirements.txt           # 依赖
└── README.md                  # 说明文档
```

## 3. 智能体详细设计

### 3.1 数据类型识别智能体 (TypeIdentifierAgent)

**职责**:
- 解析输入的JSON配置
- 识别并验证每个字段的数据类型
- 提取数据约束（范围、长度等）
- 验证配置的合法性和完整性

**输入**:
```json
{
  "dir": "/data/user_profiles/",
  "data": [
    {
      "name": "user_id",
      "type": "integer",
      "value": 1001,
      "range": "1-1000000",
      "policy": "边界值"
    }
  ],
  "sum": 10
}
```

**输出**:
```json
{
  "fields": [
    {
      "name": "user_id",
      "data_type": "INTEGER",
      "constraints": {
        "min": 1,
        "max": 1000000,
        "default_value": 1001
      },
      "user_policies": ["边界值"],
      "validation": "PASSED"
    }
  ],
  "output_dir": "/data/user_profiles/",
  "total_count": 10,
  "validation_status": "SUCCESS"
}
```

**核心方法**:
- `parse_config(config: dict) -> ParsedConfig`: 解析配置
- `identify_type(field: dict) -> DataType`: 识别数据类型
- `extract_constraints(field: dict) -> Constraints`: 提取约束
- `validate_config(parsed_config: ParsedConfig) -> bool`: 验证配置

### 3.2 畸变策略制定智能体 (StrategyMakerAgent)

**职责**:
- 根据数据类型推荐默认畸变策略
- 合并用户指定的畸变策略
- 生成完整的畸变规则集
- 优先级排序和去重

**策略库**:

#### 整数类型 (Integer)
- **边界值**: 最小值、最大值、最小值-1、最大值+1、0
- **特殊值**: 负数、超大数、NULL
- **随机值**: 范围内随机值

#### 字符串类型 (String)
- **长度畸变**: 空字符串、超长字符串、最大长度±1
- **字符集畸变**: 特殊字符、SQL注入字符、XSS字符、emoji
- **格式畸变**: 全角/半角、大小写、空格
- **语言畸变**: 中文姓名、随机中文、英文、混合

#### 日期类型 (Date)
- **格式畸变**: 不同日期格式 (YYYY-MM-DD, YYYYMMDD, MM/DD/YYYY)
- **边界值**: 最早日期、最晚日期、当前日期
- **无效值**: 不存在的日期 (2月30日)、未来日期、过去日期
- **特殊值**: NULL, 空字符串

**输入**:
```json
{
  "fields": [
    {
      "name": "user_id",
      "data_type": "INTEGER",
      "constraints": {"min": 1, "max": 1000000},
      "user_policies": ["边界值"]
    }
  ]
}
```

**输出**:
```json
{
  "mutation_plan": [
    {
      "field_name": "user_id",
      "strategies": [
        {
          "name": "边界值",
          "priority": 1,
          "rules": [
            {"type": "min_boundary", "description": "最小值"},
            {"type": "max_boundary", "description": "最大值"},
            {"type": "below_min", "description": "最小值-1"},
            {"type": "above_max", "description": "最大值+1"}
          ]
        }
      ]
    }
  ]
}
```

**核心方法**:
- `recommend_strategies(data_type: DataType) -> List[Strategy]`: 推荐策略
- `merge_policies(default: List, user: List) -> List`: 合并策略
- `generate_mutation_plan(fields: List) -> MutationPlan`: 生成畸变计划

### 3.3 数据畸变智能体 (DataMutatorAgent)

**职责**:
- 执行畸变策略，生成变异值
- 对所有字段的变异值进行笛卡尔积组合
- 根据指定数量采样输出
- 生成文件并保存到指定目录

**工作流程**:

1. **畸变阶段**: 为每个字段生成所有可能的变异值
2. **组合阶段**: 笛卡尔积生成所有可能的组合
3. **采样阶段**: 根据sum值选择指定数量的数据
4. **输出阶段**: 生成JSON文件

**输入**:
```json
{
  "mutation_plan": [...],
  "total_count": 10,
  "output_dir": "/data/user_profiles/"
}
```

**中间输出** (total_mutation.json):
```json
[
  {"user_id": [0, 1, 1000000, 1000001]},
  {"username": ["", "张", "张伟李芳王明...", "欧阳明日"]},
  {"出生日期": ["20251201", "2030-05-20", "2025-02-30", "1950-01-01"]}
]
```

**最终输出** (result.json):
```json
[
  {
    "user_id": 0,
    "username": "",
    "出生日期": "20251201"
  },
  {
    "user_id": 1,
    "username": "张",
    "出生日期": "2030-05-20"
  },
  ...
]
```

**核心方法**:
- `execute_strategy(field, strategy) -> List[Any]`: 执行单个策略
- `mutate_field(field, strategies) -> List[Any]`: 畸变单个字段
- `cartesian_product(mutations: Dict) -> List[Dict]`: 笛卡尔积组合
- `sample_data(combinations: List, count: int) -> List[Dict]`: 采样
- `save_to_file(data: List, output_path: str)`: 保存文件

## 4. 核心算法

### 4.1 笛卡尔积算法

```python
from itertools import product

def cartesian_product(mutations: Dict[str, List]) -> List[Dict]:
    """
    对所有字段的变异值进行笛卡尔积组合

    Args:
        mutations: {field_name: [mutated_values]}

    Returns:
        List of all possible combinations
    """
    field_names = list(mutations.keys())
    field_values = list(mutations.values())

    combinations = []
    for combo in product(*field_values):
        record = {}
        for i, field_name in enumerate(field_names):
            record[field_name] = combo[i]
        combinations.append(record)

    return combinations
```

### 4.2 采样算法

支持多种采样策略:

1. **随机采样**: 从所有组合中随机选择
2. **分层采样**: 确保每个字段的所有变异值都被包含
3. **优先级采样**: 优先选择高优先级策略的组合

```python
import random

def sample_data(combinations: List[Dict], count: int, strategy: str = "random") -> List[Dict]:
    """
    从组合中采样指定数量的数据

    Args:
        combinations: 所有可能的组合
        count: 需要的数据量
        strategy: 采样策略

    Returns:
        采样后的数据
    """
    if strategy == "random":
        if len(combinations) <= count:
            return combinations
        return random.sample(combinations, count)

    elif strategy == "stratified":
        # 实现分层采样逻辑
        pass

    elif strategy == "priority":
        # 实现优先级采样逻辑
        pass
```

## 5. 数据类型与畸变策略详细设计

### 5.1 整数类型 (Integer)

**识别规则**:
- type字段为 "integer" 或 "int"
- value可以转换为整数

**约束提取**:
- range: "min-max" → min, max
- 默认范围: -2^31 到 2^31-1

**畸变策略**:

| 策略名称 | 变异规则 | 示例 (range: 1-1000000) |
|---------|---------|------------------------|
| 边界值 | min, max, min-1, max+1, 0 | [0, 1, 1000000, 1000001] |
| 特殊值 | 负数, 超大数, NULL | [-1, 999999999, null] |
| 随机值 | 范围内随机N个值 | [42, 12345, 888888] |

### 5.2 字符串类型 (String)

**识别规则**:
- type字段为 "string" 或 "str"
- value为字符串类型

**约束提取**:
- length: "max_length" → max_length
- 默认最大长度: 255

**畸变策略**:

| 策略名称 | 变异规则 | 示例 |
|---------|---------|------|
| 空字符串 | "" | "" |
| 最小长度 | 单字符 | "张" |
| 最大长度 | 达到长度限制 | "张伟李芳..." (20字符) |
| 超长字符串 | 超出长度限制 | "张伟李芳..." (21字符) |
| 特殊字符 | SQL注入, XSS | "'; DROP TABLE--", "<script>" |
| 中文姓名 | 常见中文姓名 | "张伟", "王芳", "李明" |
| 随机中文 | 随机长度中文 | "随机中文字符串" |
| Emoji | 包含emoji | "😀测试🎉" |

### 5.3 日期类型 (Date)

**识别规则**:
- type字段为 "date" 或 "datetime"
- value可以解析为日期

**约束提取**:
- range: "start_date/end_date" → start_date, end_date
- format: 日期格式字符串

**畸变策略**:

| 策略名称 | 变异规则 | 示例 |
|---------|---------|------|
| 格式错误 | 不同日期格式 | "20251201", "12/01/2025" |
| 最早日期 | 范围最小值 | "1950-01-01" |
| 最晚日期 | 范围最大值 | "2025-12-31" |
| 未来日期 | 超出当前日期 | "2030-05-20" |
| 无效日期 | 不存在的日期 | "2025-02-30", "2025-13-01" |
| NULL值 | null, "", "null" | null |

## 6. 接口设计

### 6.1 输入配置接口

```json
{
  "dir": "string, 输出目录路径",
  "data": [
    {
      "name": "string, 字段名称",
      "type": "string, 数据类型 (integer|string|date|float|boolean)",
      "value": "any, 示例值",
      "range": "string, 可选, 数据范围",
      "length": "string, 可选, 字符串最大长度",
      "format": "string, 可选, 日期格式",
      "policy": "string|array, 畸变策略"
    }
  ],
  "sum": "integer, 输出数据总数",
  "sample_strategy": "string, 可选, 采样策略 (random|stratified|priority)"
}
```

### 6.2 API接口 (可选)

如果需要提供API服务，可以设计以下接口:

```python
# RESTful API 设计

POST /api/v1/mutate
# 提交畸变任务

GET /api/v1/task/{task_id}
# 查询任务状态

GET /api/v1/task/{task_id}/download
# 下载生成的文件

POST /api/v1/strategies/recommend
# 获取推荐的畸变策略
```

### 6.3 CLI接口

```bash
# 基本用法
python main.py --config config.json

# 指定输出目录
python main.py --config config.json --output /path/to/output

# 指定采样策略
python main.py --config config.json --sample-strategy stratified

# 查看帮助
python main.py --help
```

## 7. 配置示例

### 7.1 基础配置示例

```json
{
  "dir": "/data/user_profiles/",
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
    },
    {
      "name": "birth_date",
      "type": "date",
      "value": "2025-12-01",
      "range": "1950-01-01/2025-12-31",
      "policy": ["格式错误(YYYYMMDD)", "未来日期", "无效日期(如2月30日)"]
    }
  ],
  "sum": 10,
  "sample_strategy": "random"
}
```

### 7.2 高级配置示例

```json
{
  "dir": "/data/payment_records/",
  "data": [
    {
      "name": "amount",
      "type": "float",
      "value": 99.99,
      "range": "0.01-999999.99",
      "precision": 2,
      "policy": ["边界值", "特殊值", "负数"]
    },
    {
      "name": "email",
      "type": "string",
      "value": "user@example.com",
      "length": "100",
      "policy": ["无效邮箱格式", "超长邮箱", "特殊字符"]
    },
    {
      "name": "status",
      "type": "enum",
      "value": "pending",
      "enum_values": ["pending", "completed", "failed", "cancelled"],
      "policy": ["所有枚举值", "无效值", "NULL"]
    }
  ],
  "sum": 50,
  "sample_strategy": "stratified"
}
```

## 8. 错误处理

### 8.1 配置验证错误

- 缺少必需字段
- 数据类型不匹配
- 范围格式错误
- 无效的畸变策略

### 8.2 运行时错误

- 文件系统权限错误
- 磁盘空间不足
- 内存溢出 (组合数过多)
- 策略执行失败

### 8.3 错误响应格式

```json
{
  "status": "error",
  "error_code": "INVALID_CONFIG",
  "message": "配置文件验证失败",
  "details": [
    {
      "field": "data[0].range",
      "error": "范围格式错误，应为 'min-max'"
    }
  ]
}
```

## 9. 性能优化

### 9.1 组合爆炸问题

当字段数量较多且每个字段的变异值较多时，笛卡尔积会产生巨大的组合数。

**解决方案**:
1. **预警机制**: 计算组合总数，超过阈值时警告用户
2. **分批生成**: 使用生成器模式，避免一次性加载所有组合到内存
3. **智能采样**: 优先选择覆盖率高的组合

```python
def estimate_combinations(mutations: Dict) -> int:
    """估算组合总数"""
    total = 1
    for values in mutations.values():
        total *= len(values)
    return total

def smart_sample(mutations: Dict, target_count: int) -> List[Dict]:
    """智能采样，确保每个变异值至少出现一次"""
    # 实现优化的采样算法
    pass
```

### 9.2 大文件处理

对于生成大量数据的场景:
- 使用流式写入
- 支持分块输出
- 支持压缩格式

## 10. 扩展性设计

### 10.1 自定义数据类型

支持用户定义新的数据类型:

```python
# custom_types.py
class EmailType(DataType):
    def validate(self, value: str) -> bool:
        # 邮箱验证逻辑
        pass

    def get_default_strategies(self) -> List[Strategy]:
        return [
            InvalidFormatStrategy(),
            SpecialCharacterStrategy(),
            MaxLengthStrategy()
        ]
```

### 10.2 自定义畸变策略

支持用户定义新的畸变策略:

```python
# custom_strategies.py
class SQLInjectionStrategy(Strategy):
    name = "SQL注入"

    def mutate(self, value: str, constraints: Dict) -> List[str]:
        return [
            "' OR '1'='1",
            "'; DROP TABLE users--",
            "admin'--"
        ]
```

### 10.3 插件系统

支持通过插件扩展功能:

```python
# plugins/
# ├── __init__.py
# ├── export_csv.py      # CSV导出插件
# ├── export_xml.py      # XML导出插件
# └── validator_plugin.py # 自定义验证器插件
```

## 11. 日志与监控

### 11.1 日志设计

```python
# 日志级别
# DEBUG: 详细的调试信息
# INFO: 关键步骤信息
# WARNING: 警告信息
# ERROR: 错误信息

# 日志示例
2025-12-16 10:30:00 [INFO] TypeIdentifierAgent: 开始解析配置文件
2025-12-16 10:30:01 [INFO] TypeIdentifierAgent: 识别到3个字段
2025-12-16 10:30:02 [INFO] StrategyMakerAgent: 为字段 'user_id' 生成4个畸变规则
2025-12-16 10:30:05 [WARNING] DataMutatorAgent: 组合总数(10000)超过建议值(5000)
2025-12-16 10:30:10 [INFO] DataMutatorAgent: 成功生成10条数据
2025-12-16 10:30:11 [INFO] 文件已保存: /data/user_profiles/result.json
```

### 11.2 进度跟踪

对于耗时操作，提供进度反馈:

```
[====================] 100% 畸变字段 'username'
[====================] 100% 生成组合
[=====               ]  25% 采样数据 (25/100)
```

## 12. 测试策略

### 12.1 单元测试

- 测试每个智能体的核心功能
- 测试每种数据类型的畸变策略
- 测试工具函数

### 12.2 集成测试

- 测试端到端流程
- 测试不同配置组合
- 测试边界场景

### 12.3 性能测试

- 测试大数据量生成
- 测试组合爆炸场景
- 测试内存和CPU使用

## 13. 实施计划

### Phase 1: 基础框架 (Week 1-2)
- [ ] 搭建项目结构
- [ ] 实现配置解析模块
- [ ] 实现数据类型识别智能体
- [ ] 实现文件处理工具

### Phase 2: 核心功能 (Week 3-4)
- [ ] 实现畸变策略制定智能体
- [ ] 实现整数、字符串、日期的畸变策略
- [ ] 实现数据畸变智能体
- [ ] 实现笛卡尔积和采样算法

### Phase 3: 优化和扩展 (Week 5-6)
- [ ] 性能优化
- [ ] 添加更多数据类型支持
- [ ] 实现CLI接口
- [ ] 完善错误处理和日志

### Phase 4: 测试和文档 (Week 7-8)
- [ ] 编写单元测试和集成测试
- [ ] 性能测试和优化
- [ ] 编写用户文档
- [ ] 代码审查和重构

## 14. 附录

### 14.1 常见中文姓名库

```python
COMMON_SURNAMES = ["张", "王", "李", "赵", "刘", "陈", "杨", "黄", "周", "吴"]
COMMON_NAMES = ["伟", "芳", "娜", "秀英", "敏", "静", "丽", "强", "磊", "军"]
```

### 14.2 特殊字符库

```python
SQL_INJECTION_CHARS = ["'", "\"", ";", "--", "/*", "*/", "xp_", "sp_"]
XSS_CHARS = ["<", ">", "<script>", "javascript:", "onerror="]
SPECIAL_CHARS = ["@", "#", "$", "%", "^", "&", "*", "(", ")", "!", "~"]
```

### 14.3 日期格式库

```python
DATE_FORMATS = [
    "%Y-%m-%d",      # 2025-12-16
    "%Y/%m/%d",      # 2025/12/16
    "%Y%m%d",        # 20251216
    "%m/%d/%Y",      # 12/16/2025
    "%d-%m-%Y",      # 16-12-2025
    "%Y年%m月%d日"   # 2025年12月16日
]
```

### 14.4 参考资料

- Python itertools文档: https://docs.python.org/3/library/itertools.html
- LangChain文档: https://python.langchain.com/
- 软件测试边界值分析: 测试理论基础
- OWASP安全测试指南: 特殊字符注入测试

---

**文档版本**: v1.0
**创建日期**: 2025-12-16
**最后更新**: 2025-12-16
**维护者**: 数据畸变助手开发团队
