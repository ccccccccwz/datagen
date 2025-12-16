"""
数据畸变智能体测试脚本
"""

import json
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from agents.mutation_agent import DataMutationAgent


def test_basic_example():
    """测试基础示例"""
    print("=" * 60)
    print("测试: 基础示例 - 用户信息畸变")
    print("=" * 60)

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

    # 输出结果
    print(f"\n{'=' * 60}")
    print("执行结果:")
    print(f"{'=' * 60}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_stratified_sampling():
    """测试分层采样"""
    print("\n\n" + "=" * 60)
    print("测试: 分层采样 - 确保覆盖率")
    print("=" * 60)

    agent = DataMutationAgent()

    config = {
        "dir": "./output",
        "data": [
            {
                "name": "status",
                "type": "string",
                "value": "active",
                "length": "20",
                "policy": "生成合法中文姓名"
            },
            {
                "name": "score",
                "type": "integer",
                "value": 50,
                "range": "0-100",
                "policy": "边界值|特殊值"
            }
        ],
        "sum": 20,
        "sample_strategy": "stratified"
    }

    result = agent.run(config)

    print(f"\n{'=' * 60}")
    print("执行结果:")
    print(f"{'=' * 60}")
    print(json.dumps(result, ensure_ascii=False, indent=2))


def test_all_types():
    """测试所有数据类型"""
    print("\n\n" + "=" * 60)
    print("测试: 所有数据类型")
    print("=" * 60)

    agent = DataMutationAgent()

    config = {
        "dir": "./output",
        "data": [
            {
                "name": "id",
                "type": "integer",
                "value": 100,
                "range": "1-1000",
                "policy": "边界值|特殊值|随机值"
            },
            {
                "name": "email",
                "type": "string",
                "value": "test@example.com",
                "length": "50",
                "policy": ["空字符串", "特殊字符", "生成超长字符"]
            },
            {
                "name": "created_at",
                "type": "date",
                "value": "2025-01-01",
                "range": "2020-01-01/2025-12-31",
                "policy": ["边界值", "格式错误(YYYYMMDD)", "NULL值"]
            }
        ],
        "sum": 15,
        "sample_strategy": "random"
    }

    result = agent.run(config)

    print(f"\n{'=' * 60}")
    print("执行结果:")
    print(f"{'=' * 60}")
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 读取并显示生成的文件内容
    print(f"\n{'=' * 60}")
    print("生成的文件内容预览:")
    print(f"{'=' * 60}")

    if result.get("status") == "success":
        for file_path in result.get("files", []):
            if os.path.exists(file_path):
                print(f"\n📄 {file_path}:")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 只显示前3条
                    if isinstance(data, list):
                        preview = data[:3] if len(data) > 3 else data
                        print(json.dumps(preview, ensure_ascii=False, indent=2))
                        if len(data) > 3:
                            print(f"... (共 {len(data)} 条记录)")
                    else:
                        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    try:
        # 运行所有测试
        test_basic_example()
        test_stratified_sampling()
        test_all_types()

        print("\n\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
