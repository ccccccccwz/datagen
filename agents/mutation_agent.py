"""
数据畸变智能体 (Data Mutation Agent)

职责：
1. 接受输入配置（数据名称、类型、范围、畸变策略）
2. 执行畸变策略生成变异值
3. 笛卡尔积组合所有字段的变异值
4. 根据指定数量采样数据
5. 输出文件到指定目录
"""

import json
import random
import os
from datetime import datetime, timedelta
from itertools import product
from typing import List, Dict, Any, Optional
from pathlib import Path


class DataMutationAgent:
    """
    数据畸变智能体

    基于工具化设计，提供以下工具：
    1. IntegerMutator - 整数畸变工具
    2. StringMutator - 字符串畸变工具
    3. DateMutator - 日期畸变工具
    4. CartesianProduct - 笛卡尔积组合工具
    5. SampleData - 数据采样工具
    6. SaveFile - 文件保存工具
    """

    def __init__(self):
        """初始化数据畸变智能体"""
        self.mutations_cache = {}  # 缓存每个字段的畸变结果
        self.combinations = []     # 笛卡尔积组合结果
        self.sampled_data = []     # 采样后的数据

    def _mutate_integer(self, input_str: str) -> str:
        """
        整数畸变

        Args:
            input_str: "name,value,min,max,policies"

        Returns:
            JSON格式的变异值列表
        """
        try:
            parts = input_str.split(',')
            name = parts[0].strip()
            value = int(parts[1].strip())
            min_val = int(parts[2].strip())
            max_val = int(parts[3].strip())
            policies = parts[4].strip() if len(parts) > 4 else "边界值"

            mutations = []
            policy_list = [p.strip() for p in policies.split('|')]

            for policy in policy_list:
                if policy == "边界值":
                    mutations.extend([
                        min_val - 1,  # 低于最小值
                        min_val,      # 最小值
                        max_val,      # 最大值
                        max_val + 1,  # 超过最大值
                        0             # 零值
                    ])
                elif policy == "特殊值":
                    mutations.extend([
                        -1,           # 负数
                        999999999,    # 超大数
                        None          # NULL
                    ])
                elif policy == "随机值":
                    # 生成3个随机值
                    for _ in range(3):
                        mutations.append(random.randint(min_val, max_val))

            # 去重并保持顺序
            seen = set()
            unique_mutations = []
            for m in mutations:
                if m not in seen:
                    seen.add(m)
                    unique_mutations.append(m)

            # 缓存结果
            self.mutations_cache[name] = unique_mutations

            result = {
                "field": name,
                "type": "integer",
                "mutations": unique_mutations,
                "count": len(unique_mutations)
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _mutate_string(self, input_str: str) -> str:
        """
        字符串畸变

        Args:
            input_str: "name,value,max_length,policies"

        Returns:
            JSON格式的变异值列表
        """
        try:
            parts = input_str.split(',', 3)  # 最多分割3次，因为value可能包含逗号
            name = parts[0].strip()
            value = parts[1].strip() if len(parts) > 1 else ""
            max_length = int(parts[2].strip()) if len(parts) > 2 else 255
            policies = parts[3].strip() if len(parts) > 3 else "生成随机长度中文字符"

            mutations = []
            policy_list = [p.strip() for p in policies.split('|')]

            # 常见中文姓名库
            common_names = [
                "张伟", "王芳", "李明", "刘洋", "陈晓",
                "杨光", "赵雷", "周涛", "吴刚", "郑洁"
            ]

            for policy in policy_list:
                if policy == "空字符串":
                    mutations.append("")

                elif policy == "生成随机长度中文字符":
                    # 生成不同长度的中文字符串
                    mutations.append("张")  # 1字符
                    mutations.append("张伟李")  # 3字符
                    mutations.append("张伟李芳王明刘洋陈晓杨光赵雷")  # 15字符

                elif policy == "生成超长字符":
                    # 超过最大长度
                    long_str = "张伟李芳王明刘洋陈晓杨光赵雷周涛吴刚郑洁孙丽朱军" * ((max_length // 10) + 2)
                    mutations.append(long_str[:max_length + 5])

                elif policy == "生成合法中文姓名":
                    mutations.extend(common_names[:5])
                    # 添加复姓
                    mutations.append("欧阳明日")
                    mutations.append("司马相如")

                elif policy == "特殊字符":
                    mutations.extend([
                        "'; DROP TABLE--",
                        "<script>alert('XSS')</script>",
                        "admin'--",
                        "' OR '1'='1",
                        "../../../etc/passwd"
                    ])

                elif policy == "Emoji":
                    mutations.extend([
                        "😀测试",
                        "🎉庆祝🎊",
                        "👨‍👩‍👧‍👦家庭"
                    ])

            # 如果没有生成任何变异，至少包含原值
            if not mutations:
                mutations.append(value)

            # 去重
            unique_mutations = list(dict.fromkeys(mutations))

            # 缓存结果
            self.mutations_cache[name] = unique_mutations

            result = {
                "field": name,
                "type": "string",
                "mutations": unique_mutations,
                "count": len(unique_mutations)
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _mutate_date(self, input_str: str) -> str:
        """
        日期畸变

        Args:
            input_str: "name,value,start_date,end_date,policies"

        Returns:
            JSON格式的变异值列表
        """
        try:
            parts = input_str.split(',')
            name = parts[0].strip()
            value = parts[1].strip()
            start_date = parts[2].strip() if len(parts) > 2 else "1950-01-01"
            end_date = parts[3].strip() if len(parts) > 3 else "2099-12-31"
            policies = parts[4].strip() if len(parts) > 4 else "格式错误(YYYYMMDD)"

            mutations = []
            policy_list = [p.strip() for p in policies.split('|')]

            for policy in policy_list:
                if "格式错误" in policy or policy == "格式错误(YYYYMMDD)":
                    # 不同的日期格式
                    mutations.extend([
                        "20251201",           # YYYYMMDD
                        "12/01/2025",         # MM/DD/YYYY
                        "01-12-2025",         # DD-MM-YYYY
                        "2025年12月01日",      # 中文格式
                    ])

                elif policy == "未来日期":
                    # 生成未来日期
                    future = datetime.now() + timedelta(days=365*5)  # 5年后
                    mutations.append(future.strftime("%Y-%m-%d"))
                    mutations.append("2030-05-20")
                    mutations.append("2099-12-31")

                elif "无效日期" in policy or policy == "无效日期(如2月30日)":
                    # 不存在的日期
                    mutations.extend([
                        "2025-02-30",  # 2月没有30日
                        "2025-13-01",  # 没有13月
                        "2025-04-31",  # 4月没有31日
                        "2025-00-01",  # 无效月份
                        "2025-01-00",  # 无效日期
                    ])

                elif policy == "边界值":
                    # 范围边界
                    mutations.append(start_date)
                    mutations.append(end_date)

                    # 边界外
                    try:
                        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                        before_start = start_dt - timedelta(days=1)
                        mutations.append(before_start.strftime("%Y-%m-%d"))

                        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                        after_end = end_dt + timedelta(days=1)
                        mutations.append(after_end.strftime("%Y-%m-%d"))
                    except:
                        pass

                elif policy == "NULL值":
                    mutations.extend([
                        None,
                        "",
                        "null",
                        "NULL"
                    ])

            # 去重
            seen = set()
            unique_mutations = []
            for m in mutations:
                key = str(m) if m is not None else "None"
                if key not in seen:
                    seen.add(key)
                    unique_mutations.append(m)

            # 缓存结果
            self.mutations_cache[name] = unique_mutations

            result = {
                "field": name,
                "type": "date",
                "mutations": unique_mutations,
                "count": len(unique_mutations)
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _cartesian_product(self, input_str: str = "") -> str:
        """
        笛卡尔积组合

        Returns:
            组合总数
        """
        try:
            if not self.mutations_cache:
                return json.dumps({"error": "没有可用的畸变数据"}, ensure_ascii=False)

            # 计算组合总数
            total = 1
            for values in self.mutations_cache.values():
                total *= len(values)

            # 生成所有组合
            field_names = list(self.mutations_cache.keys())
            field_values = [self.mutations_cache[name] for name in field_names]

            combinations = []
            for combo in product(*field_values):
                record = {}
                for i, field_name in enumerate(field_names):
                    record[field_name] = combo[i]
                combinations.append(record)

            # 缓存组合结果
            self.combinations = combinations

            result = {
                "total_combinations": total,
                "generated": len(combinations),
                "fields": field_names
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _sample_data(self, input_str: str) -> str:
        """
        数据采样

        Args:
            input_str: "count,strategy"

        Returns:
            采样后的数据
        """
        try:
            parts = input_str.split(',')
            count = int(parts[0].strip())
            strategy = parts[1].strip() if len(parts) > 1 else "random"

            if not hasattr(self, 'combinations') or not self.combinations:
                return json.dumps({"error": "没有可用的组合数据，请先执行笛卡尔积"}, ensure_ascii=False)

            if strategy == "all" or len(self.combinations) <= count:
                sampled = self.combinations
            elif strategy == "random":
                sampled = random.sample(self.combinations, min(count, len(self.combinations)))
            elif strategy == "stratified":
                # 分层采样：确保每个字段的每个变异值至少出现一次
                sampled = self._stratified_sample(count)
            else:
                sampled = random.sample(self.combinations, min(count, len(self.combinations)))

            # 缓存采样结果
            self.sampled_data = sampled

            result = {
                "requested": count,
                "sampled": len(sampled),
                "strategy": strategy,
                "preview": sampled[:3] if len(sampled) > 3 else sampled
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def _stratified_sample(self, count: int) -> List[Dict]:
        """
        分层采样：确保覆盖率

        Args:
            count: 需要的样本数量

        Returns:
            采样的数据
        """
        # 先包含所有唯一的变异值组合
        required = []
        field_names = list(self.mutations_cache.keys())

        # 为每个字段的每个变异值至少选择一个组合
        covered_values = {name: set() for name in field_names}

        for combo in self.combinations:
            should_include = False
            for field_name in field_names:
                if combo[field_name] not in covered_values[field_name]:
                    covered_values[field_name].add(combo[field_name])
                    should_include = True

            if should_include:
                required.append(combo)
                if len(required) >= count:
                    break

        # 如果还需要更多数据，随机补充
        if len(required) < count:
            remaining = [c for c in self.combinations if c not in required]
            additional = random.sample(remaining, min(count - len(required), len(remaining)))
            required.extend(additional)

        return required[:count]

    def _save_file(self, input_str: str) -> str:
        """
        保存文件

        Args:
            input_str: "output_dir,filename,data_type"

        Returns:
            保存的文件路径
        """
        try:
            parts = input_str.split(',')
            output_dir = parts[0].strip()
            filename = parts[1].strip() if len(parts) > 1 else "result.json"
            data_type = parts[2].strip() if len(parts) > 2 else "final"

            # 创建输出目录
            Path(output_dir).mkdir(parents=True, exist_ok=True)

            # 确定要保存的数据
            if data_type == "mutation":
                # 保存畸变中间结果
                data = [
                    {field: self.mutations_cache[field]}
                    for field in self.mutations_cache
                ]
            elif data_type == "final":
                # 保存最终采样结果
                if not hasattr(self, 'sampled_data'):
                    return json.dumps({"error": "没有采样数据可保存"}, ensure_ascii=False)
                data = self.sampled_data
            else:
                return json.dumps({"error": f"未知的数据类型: {data_type}"}, ensure_ascii=False)

            # 保存文件
            file_path = os.path.join(output_dir, filename)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            result = {
                "file_path": file_path,
                "data_type": data_type,
                "records": len(data) if isinstance(data, list) else len(data)
            }

            return json.dumps(result, ensure_ascii=False)

        except Exception as e:
            return json.dumps({"error": str(e)}, ensure_ascii=False)

    def run(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行数据畸变流程

        Args:
            config: 输入配置
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
                    "sum": 10,
                    "sample_strategy": "random"
                }

        Returns:
            执行结果
        """
        try:
            results = {
                "status": "success",
                "mutations": {},
                "combinations": 0,
                "sampled": 0,
                "files": []
            }

            # 清空缓存
            self.mutations_cache = {}

            # 1. 执行畸变
            print("🔄 步骤1: 执行数据畸变...")
            for field_config in config.get("data", []):
                field_name = field_config["name"]
                field_type = field_config["type"]

                if field_type in ["integer", "int"]:
                    # 解析range
                    range_str = field_config.get("range", "1-1000000")
                    min_val, max_val = range_str.split("-")

                    # 处理policy
                    policy = field_config.get("policy", "边界值")
                    if isinstance(policy, list):
                        policy = "|".join(policy)

                    input_str = f"{field_name},{field_config['value']},{min_val},{max_val},{policy}"
                    result = self._mutate_integer(input_str)
                    results["mutations"][field_name] = json.loads(result)
                    print(f"  ✓ {field_name}: 生成 {results['mutations'][field_name]['count']} 个变异值")

                elif field_type in ["string", "str"]:
                    max_length = field_config.get("length", "255")
                    policy = field_config.get("policy", "生成随机长度中文字符")
                    if isinstance(policy, list):
                        policy = "|".join(policy)

                    input_str = f"{field_name},{field_config.get('value', '')},{max_length},{policy}"
                    result = self._mutate_string(input_str)
                    results["mutations"][field_name] = json.loads(result)
                    print(f"  ✓ {field_name}: 生成 {results['mutations'][field_name]['count']} 个变异值")

                elif field_type in ["date", "datetime"]:
                    range_str = field_config.get("range", "1950-01-01/2099-12-31")
                    if "/" in range_str:
                        start_date, end_date = range_str.split("/")
                    else:
                        start_date, end_date = "1950-01-01", "2099-12-31"

                    policy = field_config.get("policy", "格式错误(YYYYMMDD)")
                    if isinstance(policy, list):
                        policy = "|".join(policy)

                    input_str = f"{field_name},{field_config.get('value', '')},{start_date},{end_date},{policy}"
                    result = self._mutate_date(input_str)
                    results["mutations"][field_name] = json.loads(result)
                    print(f"  ✓ {field_name}: 生成 {results['mutations'][field_name]['count']} 个变异值")

            # 2. 笛卡尔积组合
            print("\n🔄 步骤2: 笛卡尔积组合...")
            combo_result = json.loads(self._cartesian_product())
            results["combinations"] = combo_result.get("total_combinations", 0)
            print(f"  ✓ 生成 {results['combinations']} 个组合")

            # 如果组合数过多，给出警告
            if results["combinations"] > 10000:
                print(f"  ⚠️  警告: 组合数({results['combinations']})较大，可能影响性能")

            # 3. 采样
            print("\n🔄 步骤3: 数据采样...")
            sample_count = config.get("sum", 10)
            sample_strategy = config.get("sample_strategy", "random")
            sample_input = f"{sample_count},{sample_strategy}"
            sample_result = json.loads(self._sample_data(sample_input))
            results["sampled"] = sample_result.get("sampled", 0)
            print(f"  ✓ 采样 {results['sampled']} 条数据 (策略: {sample_strategy})")

            # 4. 保存文件
            print("\n🔄 步骤4: 保存文件...")
            output_dir = config.get("dir", "./output")

            # 保存畸变中间结果
            mutation_file = self._save_file(f"{output_dir},total_mutation.json,mutation")
            mutation_info = json.loads(mutation_file)
            results["files"].append(mutation_info["file_path"])
            print(f"  ✓ 畸变结果: {mutation_info['file_path']}")

            # 保存最终结果
            final_file = self._save_file(f"{output_dir},result.json,final")
            final_info = json.loads(final_file)
            results["files"].append(final_info["file_path"])
            print(f"  ✓ 最终结果: {final_info['file_path']}")

            print("\n✅ 数据畸变完成！")

            return results

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# 使用示例
if __name__ == "__main__":
    # 创建智能体
    agent = DataMutationAgent()

    # 示例配置
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

    # 运行
    result = agent.run(config)
    print(f"\n结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
