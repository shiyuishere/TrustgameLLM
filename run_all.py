import subprocess

commands = [
    # oneshot
    'uv run oneshot.py --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/fr.yaml --output "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/FR/OS/oneshot_20250903_114621.csv"',
    'uv run oneshot.py --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/fr.yaml --output "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/FR/OS/oneshot_20250903_122926.csv"',
    'uv run oneshot.py --llm-config configs/llms/openai.yaml --prompt-config configs/prompts/oneshot/zh.yaml --output "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_152146.csv"',
    'uv run oneshot.py --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/zh.yaml --output "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_162023.csv"',
    'uv run oneshot.py --llm-config configs/llms/openai.yaml --prompt-config configs/prompts/oneshot/zh.yaml --output "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_155001.csv"',
    'uv run oneshot.py --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/zh.yaml --output "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_180255.csv"',

    # check_experiments 
    'uv run ./check_experiments.py --result "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/FR/OS/oneshot_20250903_114621.csv" --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/fr.yaml',
    'uv run ./check_experiments.py --result "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/FR/OS/oneshot_20250903_122926.csv" --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/fr.yaml',
    'uv run ./check_experiments.py --result "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_152146.csv" --llm-config configs/llms/openai.yaml --prompt-config configs/prompts/oneshot/zh.yaml',
    'uv run ./check_experiments.py --result "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_162023.csv" --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/zh.yaml',
    'uv run ./check_experiments.py --result "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_155001.csv" --llm-config configs/llms/openai.yaml --prompt-config configs/prompts/oneshot/zh.yaml',
    'uv run ./check_experiments.py --result "/Users/fancy/Documents/Utrecht SaSR/My thesis/AI Experiments/trustgame/trustgame_0912/results/ZH/OS/oneshot_20250903_180255.csv" --llm-config configs/llms/deepseek.yaml --prompt-config configs/prompts/oneshot/zh.yaml',

   
]

for i, cmd in enumerate(commands, 1):
    print(f"▶️ Running {i}/{len(commands)}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode == 0:
        print(f"✅ Finished {i}")
    else:
        print(f"❌ Command {i} failed with code {result.returncode}")

print("\n==============================")
if failed_cmds:
    print("The following command failed to execute：")
    for c in failed_cmds:
        print(c)
else:
    print("All commands were executed successfully!")
print("==============================")
