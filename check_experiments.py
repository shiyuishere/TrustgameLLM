#!/usr/bin/env python3
"""
Experiment Status Check Tool
Used to check the completion status of OneShotGame experiments, identifying incomplete and duplicate experiments.
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

# TODO: change initial trust level
SENT_AMOUNTS = [0, 2, 5, 8, 10]


class ExperimentChecker:
    """Experimental Status Inspector"""

    def __init__(self, llm_config_path: str, prompt_config_path: str):
        self.llm_config_path = llm_config_path
        self.prompt_config_path = prompt_config_path
        self.llms_config = LLMsConfig.from_yaml(llm_config_path)
        self.game_type = None  # Automatic detection will be performed during file analysis

    def detect_game_type(self, output_file: str) -> str:
        """Automatically detect game type based on the number of columns in the CSV file"""
        if not os.path.exists(output_file):
            # The default value is one-shot, but users can specify a different value via parameters
            return "oneshot"

        try:
            df = pd.read_csv(output_file, nrows=1)  # Read only the first row to check the number of columns
            columns = df.columns.tolist()

            # OneShotGame: experiment_id, game_round, a_init, b_init, a_sent, b_received, b_returned, a_final, b_final
            # RepeatedGame: experiment_id, game_round, a_init_1, b_init_1, a_sent_1, ..., a_final_7, b_final_7

            if any("_1" in col for col in columns) and any(
                "_7" in col for col in columns
            ):
                return "repeated"
            elif "a_init" in columns and "b_init" in columns:
                return "oneshot"
            else:
                print(f"Warning: Game type not recognized, column name: {columns[:10]}...")
                return "oneshot"  # default

        except Exception as e:
            print(f"Warning: Game type detection failed: {e}")
            return "oneshot"  # default

    def get_all_expected_oneshot_experiments(self) -> Set[str]:
        """Retrieve all expected OneShotGame experiment IDs (dry-run mode)"""
        all_experiment_ids = set()

        for llm_config in self.llms_config.to_llm_configs():
            game = OneShotGame(llm_config, self.prompt_config_path)

            # Get Player A's Experiment ID
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

            #Get Player B's Experiment ID
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
                    # For Player B's experiment, the sent_amount information needs to be included
                    unique_id = f"{state.experiment_id}_SENT_{sent_amount}"
                    all_experiment_ids.add(unique_id)

        return all_experiment_ids

    def get_all_expected_repeated_experiments(self) -> Set[str]:
        """Retrieve all expected RepeatedGame experiment IDs (dry-run mode)"""
        all_experiment_ids = set()

        for llm_config in self.llms_config.to_llm_configs():
            game = RepeatedGame(llm_config, self.prompt_config_path)

            # Get Player A's Experiment ID
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

            # Get Player B's experiment ID (from 0 to 10 for each send_amount)
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
                    # For Player B's experiment, the sent_amount information needs to be included
                    unique_id = f"{state.experiment_id}_SENT_{sent_amount}"
                    all_experiment_ids.add(unique_id)

        return all_experiment_ids

    def get_all_expected_experiments(self, game_type: str) -> Set[str]:
        """Retrieve all expected experiment IDs based on game type (dry-run mode)"""
        if game_type == "oneshot":
            return self.get_all_expected_oneshot_experiments()
        elif game_type == "repeated":
            return self.get_all_expected_repeated_experiments()
        else:
            raise ValueError(f"Unsupported game types: {game_type}")

    def analyze_output_file(self, output_file: str) -> Tuple[List[str], Counter]:
        """Analyze the output file to return the completed experiment IDs and experiment counts"""
        if not os.path.exists(output_file):
            print(f"Warning: Output file {output_file} does not exist")
            return set(), Counter()

        try:
            df = pd.read_csv(output_file)
            if "experiment_id" not in df.columns:
                print(f"Error: Output file {output_file} lacks 'experiment_id' ")
                return set(), Counter()

            # For Player B's experiment, it is necessary to combine experiment_id and send_amount to generate a unique identifier
            completed_ids = []
            id_counts = Counter()

            for _, row in df.iterrows():
                exp_id = str(row["experiment_id"])

                if exp_id.startswith("B_"):
                    # Player B's experiment needs to consider send_amount
                    if self.game_type == "oneshot":
                        # OneShotGame: Use the a_sent field
                        if "a_sent" in df.columns:
                            sent_amount = row["a_sent"]
                            unique_id = f"{exp_id}_SENT_{sent_amount}"
                        else:
                            unique_id = exp_id
                    else:
                        # RepeatedGame:Use the a_sent_1 field from the first round
                        if "a_sent_1" in df.columns:
                            sent_amount = row["a_sent_1"]
                            unique_id = f"{exp_id}_SENT_{sent_amount}"
                        else:
                            unique_id = exp_id
                else:
                    # Player A's experiment directly uses experiment_id
                    unique_id = exp_id

                completed_ids.append(unique_id)
                id_counts[unique_id] += 1

            return completed_ids, id_counts

        except Exception as e:
            print(f"Error: Failed to read output file: {e}")
            return set(), Counter()

    def generate_report(self, output_file: str) -> Dict:
        """Generate experimental status report"""
        print("=== Start analyzing the experimental status ===")
        print(f"LLM configuration file: {self.llm_config_path}")
        print(f"Promptconfiguration file: {self.prompt_config_path}")
        print(f"Output file: {output_file}")

        # check game type
        self.game_type = self.detect_game_type(output_file)
        print(f"Detected game type: {self.game_type.upper()}")
        print()

        # Obtain all expected experiments
        print("Obtaining all expected experiments...")
        expected_experiments = self.get_all_expected_experiments(self.game_type)
        print(f"Total number of experiments expected: {len(expected_experiments)}")

        # Analyse output file
        print("Analysing output file...")
        completed_experiments, experiment_counts = self.analyze_output_file(output_file)
        print(f"Total number of experiments completed: {len(completed_experiments)}")

        # Identify unfinished experiments
        missing_experiments = expected_experiments - set(completed_experiments)

        # Find duplicate experiments
        duplicated_experiments = {
            exp_id: count for exp_id, count in experiment_counts.items() if count > 1
        }

        # Statistical information
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
        """Print"""
        print("\n" + "=" * 80)
        print("Experimental Status Report告")
        print("=" * 80)

        print(f"Game type: {report['game_type'].upper()}")
        print(f"Expected total number: {report['expected_total']}")
        print(
            f"Number of completed experiments (including those not included in the initial experiment and duplicate experiments): {report['completed_total']}"
        )
        print(f"Number of uncompleted experiments in the expected experiment list: {report['missing_total']}")
        print(f"Number of repeated experiments (including those not included in the expected experiments): {report['duplicated_total']}")
        print(f"Finished rate: {report['completion_rate']:.2f}%")
        print()

        if report["missing_experiments"]:
            print("Unfinished experiments:")
            print("-" * 40)
            for i, exp_id in enumerate(report["missing_experiments"], 1):
                print(f"{i:4d}. {exp_id}")
            print()
        else:
            print("All anticipated experiments have been completed!")
            print()

        if report["duplicated_experiments"]:
            print("eplication experiments:")
            print("-" * 40)
            for i, (exp_id, count) in enumerate(
                report["duplicated_experiments"].items(), 1
            ):
                print(f"{i:4d}. {exp_id} (Repeated {count} times)")
            print()
        else:
            print("No replication experiments were found!")
            print()

        print("=" * 80)

    def save_report_to_file(self, report: Dict, report_file: str):
        """Save report into file"""
        try:
            with open(report_file, "w", encoding="utf-8") as f:
                f.write("Experimental Status Report\n")
                f.write("=" * 80 + "\n")
                f.write(f"Generation time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Game type: {report['game_type'].upper()}\n")
                f.write(f"Total number of experiments expected: {report['expected_total']}\n")
                f.write(
                    f"Number of completed experiments (including those not included in the initial experiment and duplicate experiments): {report['completed_total']}\n"
                )
                f.write(f"Number of uncompleted experiments in the expected experiment list: {report['missing_total']}\n")
                f.write(
                    f"Number of repeated experiments (including those not included in the expected experiments): {report['duplicated_total']}\n"
                )
                f.write(f"Finished rate: {report['completion_rate']:.2f}%\n")
                f.write("\n")

                if report["missing_experiments"]:
                    f.write("Unfinished experiments:\n")
                    f.write("-" * 40 + "\n")
                    for i, exp_id in enumerate(report["missing_experiments"], 1):
                        f.write(f"{i:4d}. {exp_id}\n")
                    f.write("\n")
                else:
                    f.write("All anticipated experiments have been completed!\n\n")

                if report["duplicated_experiments"]:
                    f.write("Replication experiments:\n")
                    f.write("-" * 40 + "\n")
                    for i, (exp_id, count) in enumerate(
                        report["duplicated_experiments"].items(), 1
                    ):
                        f.write(f"{i:4d}. {exp_id} (Repeat {count} times)\n")
                    f.write("\n")
                else:
                    f.write("No replication experiments were found!\n\n")

                f.write("=" * 80 + "\n")

            print(f"The report has been saved to: {report_file}")

        except Exception as e:
            print(f"Error: Failed to save report: {e}")


def main():
    parser = argparse.ArgumentParser(description=" Check OneShot Trust Game experiment status")
    parser.add_argument("--result", required=True, help="The path to the output CSV file to check")
    parser.add_argument(
        "--llm-config",
        default="configs/llms/llms.yaml",
        help="LLM configuration file path (Default: configs/llms/llms.yaml)",
    )
    parser.add_argument(
        "--prompt-config",
        required=True,
        help="Prompt configuration file path",
    )
    parser.add_argument(
        "--report-file",
        default=None,
        help="Report output file path",
    )

    args = parser.parse_args()

    # Generate a default report file name, using the same directory as the input CSV file.
    if args.report_file is None:
        args.report_file = args.result + ".report.txt"

    # create checker
    checker = ExperimentChecker(args.llm_config, args.prompt_config)

    # generate report
    report = checker.generate_report(args.result)

    # print report
    checker.print_report(report)

    # save report
    checker.save_report_to_file(report, args.report_file)


if __name__ == "__main__":
    main()
