import os
import asyncio
from datetime import datetime
from dotenv import load_dotenv
import argparse

from trustgame2 import RepeatedGame
from trustgame2.llm import LLMsConfig

# Load environment variables from .env file
load_dotenv()


async def run_player_a_experiments(
    game: RepeatedGame,
    output_file: str,
    write_mtx: asyncio.Lock,
    num_runs: int,
) -> None:
    """运行LLM作为Player A的实验"""
    for _ in range(num_runs):
        try:
            await game.run_full_game_as_player_a_all(output_file, write_mtx)
        except Exception as e:
            print(f"Player A实验失败: {e}")


async def run_player_b_experiments(
    game: RepeatedGame,
    output_file: str,
    write_mtx: asyncio.Lock,
    num_runs_per_amount: int,
) -> None:
    """运行LLM作为Player B的实验（串行执行，不返回结果）"""
    for sent_amount in [0,2,5,8,10]:
        for _ in range(num_runs_per_amount):
            try:
                await game.run_full_game_as_player_b_all(sent_amount, output_file, write_mtx)
            except Exception as e:
                print(f"Player B实验失败: {e}")


async def main():
    parser = argparse.ArgumentParser(description="运行Repeated Trust Game实验")
    parser.add_argument(
        "--llm-config",
        default="configs/llms/llms.yaml",
        help="LLM配置文件路径 (默认: configs/llms/llms.yaml)",
    )
    parser.add_argument(
        "--prompt-config",
        default="configs/prompts/repeated/en.yaml",
        help="Prompt配置文件路径 (默认: configs/prompts/repeated/en.yaml)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="输出CSV文件路径 (默认: results/repeated_YYYYMMDD_HHMMSS.csv)",
    )
    parser.add_argument(
        "--num-runs-as-player-a",
        type=int,
        default=1,
        help="实验次数 (默认: 1)",
    )
    parser.add_argument(
        "--num-runs-as-player-b-per-amount",
        type=int,
        default=1,
        help="实验次数 (默认: 1)",
    )

    args = parser.parse_args()

    # 生成默认输出文件名
    if args.output is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        args.output = f"results/repeated_{timestamp}.csv"

    # 保证文件夹存在性
    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    print("=== Repeated Trust Game 实验开始 ===")
    print(f"LLM配置文件: {args.llm_config}")
    print(f"Prompt配置文件: {args.prompt_config}")
    print(f"输出文件: {args.output}")
    print()

    try:
        # 加载配置
        print("加载配置...")
        llms_config = LLMsConfig.from_yaml(args.llm_config)
        print(llms_config)
        lock = asyncio.Lock()
        for llm_config in llms_config.to_llm_configs():
            game = RepeatedGame(llm_config, args.prompt_config)
            print("配置加载完成")
            print()

            # 并发运行两种实验
            print("开始并发运行实验...")
            await run_player_a_experiments(
                game, args.output, lock, args.num_runs_as_player_a
            )
            await run_player_b_experiments(
                game,
                args.output,
                lock,
                args.num_runs_as_player_b_per_amount,
            )

            print("=== 实验完成 ===")

    except Exception as e:
        import traceback

        traceback.print_exc()
        print(f"实验运行失败: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
