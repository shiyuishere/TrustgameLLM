#!/usr/bin/env python3
"""
实验状态检查工具
用于检查OneShotGame实验的完成状态，识别未完成和重复的实验
"""

import os
import argparse
import pandas as pd
from collections import Counter
from datetime import datetime
from typing import List, Set, Dict, Tuple
from dotenv import load_dotenv

from trustgame2 import OneShotGame, RepeatedGame, LLMsConfig

# Load environment variables
load_dotenv()

# TODO: 修改这里！！！
SENT_AMOUNTS = [0, 2, 5, 8, 10]


class ExperimentChecker:
    """实验状态检查器"""

    def __init__(self, llm_config_path: str, prompt_config_path: str):
        self.llm_config_path = llm_config_path
        self.prompt_config_path = prompt_config_path
        self.llms_config = LLMsConfig.from_yaml(llm_config_path)
        self.game_type = None  # 将在分析文件时自动检测

    def detect_game_type(self, output_file: str) -> str:
        """根据CSV文件的列数自动检测游戏类型"""
        if not os.path.exists(output_file):
            # 默认返回oneshot，用户可以通过参数指定
            return "oneshot"

        try:
            df = pd.read_csv(output_file, nrows=1)  # 只读取第一行来检查列数
            columns = df.columns.tolist()

            # OneShotGame的典型列: experiment_id, game_round, a_init, b_init, a_sent, b_received, b_returned, a_final, b_final
            # RepeatedGame的典型列: experiment_id, game_round, a_init_1, b_init_1, a_sent_1, ..., a_final_7, b_final_7

            if any("_1" in col for col in columns) and any(
                "_7" in col for col in columns
            ):
                return "repeated"
            elif "a_init" in columns and "b_init" in columns:
                return "oneshot"
            else:
                print(f"警告: 无法识别游戏类型，列名: {columns[:10]}...")
                return "oneshot"  # 默认

        except Exception as e:
            print(f"警告: 检测游戏类型失败: {e}")
            return "oneshot"  # 默认

    def get_all_expected_oneshot_experiments(self) -> Set[str]:
        """获取所有预期的OneShotGame实验ID（dry-run模式）"""
        all_experiment_ids = set()

        for llm_config in self.llms_config.to_llm_configs():
            game = OneShotGame(llm_config, self.prompt_config_path)

            # 获取Player A的实验ID
            prompts_a = game._prompts.to_one_shot_prompts("A")
            for prompt in prompts_a:
                from trustgame2.oneshot_game import OneShotGameState

                state = OneShotGameState(
                    llm_role="A",
                    language=prompt.language_mark,
                    player_a_nationality=prompt.player_a_nationality_mark,
                    player_a_gender=prompt.player_a_gender_mark,
                    player_b_nationality=prompt.player_b_nationality_mark,
                    player_b_gender=prompt.player_b_gender_mark,
                    llm_model_mark=llm_config.to_model_mark(),
                    temperature_mark=llm_config.to_temperature_mark(),
                )
                all_experiment_ids.add(state.experiment_id)

            # 获取Player B的实验ID
            prompts_b = game._prompts.to_one_shot_prompts("B")
            for prompt in prompts_b:
                for sent_amount in SENT_AMOUNTS:
                    from trustgame2.oneshot_game import OneShotGameState

                    state = OneShotGameState(
                        llm_role="B",
                        language=prompt.language_mark,
                        player_a_nationality=prompt.player_a_nationality_mark,
                        player_a_gender=prompt.player_a_gender_mark,
                        player_b_nationality=prompt.player_b_nationality_mark,
                        player_b_gender=prompt.player_b_gender_mark,
                        llm_model_mark=llm_config.to_model_mark(),
                        temperature_mark=llm_config.to_temperature_mark(),
                        player_a_sent=sent_amount,
                    )
                    # 对于Player B的实验，需要包含sent_amount信息
                    unique_id = f"{state.experiment_id}_SENT_{sent_amount}"
                    all_experiment_ids.add(unique_id)

        return all_experiment_ids

    def get_all_expected_repeated_experiments(self) -> Set[str]:
        """获取所有预期的RepeatedGame实验ID（dry-run模式）"""
        all_experiment_ids = set()

        for llm_config in self.llms_config.to_llm_configs():
            game = RepeatedGame(llm_config, self.prompt_config_path)

            # 获取Player A的实验ID
            prompts_a = game._prompts.to_repeated_prompts("A")
            for prompt in prompts_a:
                from trustgame2.repeated_game import RepeatedGameState

                state = RepeatedGameState(
                    llm_role="A",
                    language=prompt.language_mark,
                    player_a_nationality=prompt.player_a_nationality_mark,
                    player_a_gender=prompt.player_a_gender_mark,
                    player_b_nationality=prompt.player_b_nationality_mark,
                    player_b_gender=prompt.player_b_gender_mark,
                    llm_model_mark=llm_config.to_model_mark(),
                    temperature_mark=llm_config.to_temperature_mark(),
                )
                all_experiment_ids.add(state.experiment_id)

            # 获取Player B的实验ID（对于每个sent_amount从0到10）
            prompts_b = game._prompts.to_repeated_prompts("B")
            for prompt in prompts_b:
                for sent_amount in SENT_AMOUNTS:
                    from trustgame2.repeated_game import RepeatedGameState

                    state = RepeatedGameState(
                        llm_role="B",
                        language=prompt.language_mark,
                        player_a_nationality=prompt.player_a_nationality_mark,
                        player_a_gender=prompt.player_a_gender_mark,
                        player_b_nationality=prompt.player_b_nationality_mark,
                        player_b_gender=prompt.player_b_gender_mark,
                        llm_model_mark=llm_config.to_model_mark(),
                        temperature_mark=llm_config.to_temperature_mark(),
                    )
                    # 对于Player B的实验，需要包含sent_amount信息
                    unique_id = f"{state.experiment_id}_SENT_{sent_amount}"
                    all_experiment_ids.add(unique_id)

        return all_experiment_ids

    def get_all_expected_experiments(self, game_type: str) -> Set[str]:
        """根据游戏类型获取所有预期的实验ID（dry-run模式）"""
        if game_type == "oneshot":
            return self.get_all_expected_oneshot_experiments()
        elif game_type == "repeated":
            return self.get_all_expected_repeated_experiments()
        else:
            raise ValueError(f"不支持的游戏类型: {game_type}")

    def analyze_output_file(self, output_file: str) -> Tuple[List[str], Counter]:
        """分析输出文件，返回已完成的实验ID和实验计数"""
        if not os.path.exists(output_file):
            print(f"警告: 输出文件 {output_file} 不存在")
            return set(), Counter()

        try:
            df = pd.read_csv(output_file)
            if "experiment_id" not in df.columns:
                print(f"错误: 输出文件 {output_file} 缺少 'experiment_id' 列")
                return set(), Counter()

            # 对于Player B的实验，需要结合experiment_id和sent_amount来生成唯一标识符
            completed_ids = []
            id_counts = Counter()

            for _, row in df.iterrows():
                exp_id = str(row["experiment_id"])

                if exp_id.startswith("B_"):
                    # Player B的实验需要考虑sent_amount
                    if self.game_type == "oneshot":
                        # OneShotGame: 使用a_sent字段
                        if "a_sent" in df.columns:
                            sent_amount = row["a_sent"]
                            unique_id = f"{exp_id}_SENT_{sent_amount}"
                        else:
                            unique_id = exp_id
                    else:
                        # RepeatedGame: 使用第一轮的a_sent_1字段
                        if "a_sent_1" in df.columns:
                            sent_amount = row["a_sent_1"]
                            unique_id = f"{exp_id}_SENT_{sent_amount}"
                        else:
                            unique_id = exp_id
                else:
                    # Player A的实验直接使用experiment_id
                    unique_id = exp_id

                completed_ids.append(unique_id)
                id_counts[unique_id] += 1

            return completed_ids, id_counts

        except Exception as e:
            print(f"错误: 读取输出文件失败: {e}")
            return set(), Counter()

    def generate_report(self, output_file: str) -> Dict:
        """生成实验状态报告"""
        print("=== 开始分析实验状态 ===")
        print(f"LLM配置文件: {self.llm_config_path}")
        print(f"Prompt配置文件: {self.prompt_config_path}")
        print(f"输出文件: {output_file}")

        # 检测游戏类型
        self.game_type = self.detect_game_type(output_file)
        print(f"检测到的游戏类型: {self.game_type.upper()}")
        print()

        # 获取所有预期实验
        print("获取所有预期实验...")
        expected_experiments = self.get_all_expected_experiments(self.game_type)
        print(f"预期实验总数: {len(expected_experiments)}")

        # 分析输出文件
        print("分析输出文件...")
        completed_experiments, experiment_counts = self.analyze_output_file(output_file)
        print(f"已完成实验总数: {len(completed_experiments)}")

        # 找出未完成的实验
        missing_experiments = expected_experiments - set(completed_experiments)

        # 找出重复的实验
        duplicated_experiments = {
            exp_id: count for exp_id, count in experiment_counts.items() if count > 1
        }

        # 统计信息
        report = {
            "game_type": self.game_type,
            "expected_total": len(expected_experiments),
            "completed_total": len(completed_experiments),
            "missing_total": len(missing_experiments),
            "duplicated_total": len(duplicated_experiments),
            "missing_experiments": sorted(list(missing_experiments)),
            "duplicated_experiments": dict(sorted(duplicated_experiments.items())),
            "completion_rate": (
                (1 - len(missing_experiments) / len(expected_experiments)) * 100
                if expected_experiments
                else 0
            ),
        }

        return report

    def print_report(self, report: Dict):
        """打印报告到屏幕"""
        print("\n" + "=" * 80)
        print("实验状态报告")
        print("=" * 80)

        print(f"游戏类型: {report['game_type'].upper()}")
        print(f"预期实验总数: {report['expected_total']}")
        print(
            f"已完成实验数（含不在预期实验内的以及重复实验）: {report['completed_total']}"
        )
        print(f"预期实验列表中未完成实验数: {report['missing_total']}")
        print(f"重复实验数（含不在预期实验内）: {report['duplicated_total']}")
        print(f"完成率: {report['completion_rate']:.2f}%")
        print()

        if report["missing_experiments"]:
            print("未完成的实验:")
            print("-" * 40)
            for i, exp_id in enumerate(report["missing_experiments"], 1):
                print(f"{i:4d}. {exp_id}")
            print()
        else:
            print("✅ 所有预期实验都已完成!")
            print()

        if report["duplicated_experiments"]:
            print("重复的实验:")
            print("-" * 40)
            for i, (exp_id, count) in enumerate(
                report["duplicated_experiments"].items(), 1
            ):
                print(f"{i:4d}. {exp_id} (重复 {count} 次)")
            print()
        else:
            print("✅ 没有发现重复实验!")
            print()

        print("=" * 80)

    def save_report_to_file(self, report: Dict, report_file: str):
        """保存报告到文件"""
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("实验状态报告\n")
                f.write("=" * 80 + "\n")
                f.write(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"游戏类型: {report['game_type'].upper()}\n")
                f.write(f"预期实验总数: {report['expected_total']}\n")
                f.write(
                    f"已完成实验数（含不在预期实验内的以及重复实验）: {report['completed_total']}\n"
                )
                f.write(f"预期实验列表中未完成实验数: {report['missing_total']}\n")
                f.write(
                    f"重复实验数（含不在预期实验内）: {report['duplicated_total']}\n"
                )
                f.write(f"完成率: {report['completion_rate']:.2f}%\n")
                f.write("\n")

                if report["missing_experiments"]:
                    f.write("未完成的实验:\n")
                    f.write("-" * 40 + "\n")
                    for i, exp_id in enumerate(report["missing_experiments"], 1):
                        f.write(f"{i:4d}. {exp_id}\n")
                    f.write("\n")
                else:
                    f.write("✅ 所有预期实验都已完成!\n\n")

                if report["duplicated_experiments"]:
                    f.write("重复的实验:\n")
                    f.write("-" * 40 + "\n")
                    for i, (exp_id, count) in enumerate(
                        report["duplicated_experiments"].items(), 1
                    ):
                        f.write(f"{i:4d}. {exp_id} (重复 {count} 次)\n")
                    f.write("\n")
                else:
                    f.write("✅ 没有发现重复实验!\n\n")

                f.write("=" * 80 + "\n")

            print(f"报告已保存到: {report_file}")

        except Exception as e:
            print(f"错误: 保存报告失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="检查OneShot Trust Game实验状态")
    parser.add_argument("--result", required=True, help="要检查的输出CSV文件路径")
    parser.add_argument(
        "--llm-config",
        default="configs/llms/llms.yaml",
        help="LLM配置文件路径 (默认: configs/llms/llms.yaml)",
    )
    parser.add_argument(
        "--prompt-config",
        required=True,
        help="Prompt配置文件路径",
    )
    parser.add_argument(
        "--report-file",
        default=None,
        help="报告输出文件路径",
    )

    args = parser.parse_args()

    # 生成默认报告文件名，使用与输入的CSV文件相同的目录
    if args.report_file is None:
        args.report_file = args.result + ".report.txt"

    # 创建检查器
    checker = ExperimentChecker(args.llm_config, args.prompt_config)

    # 生成报告
    report = checker.generate_report(args.result)

    # 打印报告
    checker.print_report(report)

    # 保存报告
    checker.save_report_to_file(report, args.report_file)


if __name__ == "__main__":
    main()
