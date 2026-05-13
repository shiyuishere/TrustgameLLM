# Trust Game Experiment

This is a Python-based experiment project implementing a trust game. The project simulates interactions between two players (A and B) in a trust game scenario, with support for multiple languages, nationalities, and gender combinations.

## Features

- **Two Game Modes**: OneShot (single round) and Repeated (7 rounds)
- **Multi-language Support**: Chinese (ZH), English (US), French (FR)
- **Multi-role Combinations**: Different nationality and gender combinations
- **LLM Integration**: Support for multiple LLM providers (DeepSeek, OpenAI, Mistral)
- **Automated Experiments**: Batch processing with configurable concurrency
- **Dual Player Roles**: Experiments where LLM acts as Player A or Player B
- **Comprehensive Output**: Detailed CSV results with experiment metadata

## Requirements

- Python 3.13 or higher
- uv package manager

## Installation Steps

1. [Install uv](https://docs.astral.sh/uv/getting-started/installation/) (if not already installed):

Windows:
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Linux/MacOS:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Create a virtual environment and install dependencies using uv:
```bash
uv sync
```

## Configuration

### LLM Configuration

Create a `.env` file in the project root directory with the following content:
```
DEEPSEEK_API_KEY=sk-xxxx
OPENAI_API_KEY=sk-xxxx
MISTRAL_API_KEY=sk-xxxx
```

### Prompt Configuration

The project uses a multi-role prompt system that automatically generates different combinations of player characteristics:

- **Nationalities**: Chinese (ZH), American (US), French (FR), Unknown (U)
- **Genders**: Male (M), Female (F), Unknown (U)
- **Languages**: Chinese, English, French

Each configuration file automatically generates multiple role combinations. For example, with 4 self-role options and 4 other-player options, the system generates 16 different prompt combinations.

## Running the Experiment

Execute the following command to run the experiment:
```bash
uv run oneshot.py
uv run repeated.py
```
OR
```bash
source .venv/bin/activate # activate the virtual environment (Linux/MacOS)
# .venv\Scripts\activate # activate the virtual environment (Windows)
python oneshot.py
python repeated.py
```

### Detailed Usage

#### OneShot

```bash
usage: oneshot.py [-h] [--llm-config LLM_CONFIG] [--prompt-config PROMPT_CONFIG] [--output OUTPUT] [--num-runs-as-player-a NUM_RUNS_AS_PLAYER_A] [--num-runs-as-player-b-per-amount NUM_RUNS_AS_PLAYER_B_PER_AMOUNT]

运行OneShot Trust Game实验

options:
  -h, --help            show this help message and exit
  --llm-config LLM_CONFIG
                        LLM配置文件路径 (默认: configs/llms/llms.yaml)
  --prompt-config PROMPT_CONFIG
                        Prompt配置文件路径 (默认: configs/prompts/oneshot/en.yaml)
  --output OUTPUT       输出CSV文件路径 (默认: results/oneshot_YYYYMMDD_HHMMSS.csv)
  --num-runs-as-player-a NUM_RUNS_AS_PLAYER_A
                        作为Player A的实验次数 (默认: 1)
  --num-runs-as-player-b-per-amount NUM_RUNS_AS_PLAYER_B_PER_AMOUNT
                        作为Player B时每个金额的实验次数 (默认: 1)
```

#### Repeated

```bash
usage: repeated.py [-h] [--llm-config LLM_CONFIG] [--prompt-config PROMPT_CONFIG] [--output OUTPUT] [--num-runs-as-player-a NUM_RUNS_AS_PLAYER_A] [--num-runs-as-player-b-per-amount NUM_RUNS_AS_PLAYER_B_PER_AMOUNT]

运行Repeated Trust Game实验

options:
  -h, --help            show this help message and exit
  --llm-config LLM_CONFIG
                        LLM配置文件路径 (默认: configs/llms/llms.yaml)
  --prompt-config PROMPT_CONFIG
                        Prompt配置文件路径 (默认: configs/prompts/repeated/en.yaml)
  --output OUTPUT       输出CSV文件路径 (默认: results/repeated_YYYYMMDD_HHMMSS.csv)
  --num-runs-as-player-a NUM_RUNS_AS_PLAYER_A
                        作为Player A的实验次数 (默认: 1)
  --num-runs-as-player-b-per-amount NUM_RUNS_AS_PLAYER_B_PER_AMOUNT
                        作为Player B时每个金额的实验次数 (默认: 1)
```

### Prompt Configuration

The prompt configuration uses a multi-role system stored in the `configs/prompts` directory:

- **oneshot/**: Single-round game configurations
  - `zh.yaml`: Chinese prompts
  - `en.yaml`: English prompts  
  - `fr.yaml`: French prompts
- **repeated/**: Multi-round game configurations
  - `zh.yaml`: Chinese prompts
  - `en.yaml`: English prompts
  - `fr.yaml`: French prompts

Each configuration file supports multiple role combinations automatically. To customize:

1. Copy one of the existing prompt configuration files
2. Modify the role parts in `player_a_role_self_parts`, `player_a_role_another_parts`, etc.
3. Run the experiment with the `--prompt-config` argument

Details can be found in the `configs/prompts/README.md` file.

### LLM Configuration

LLM configurations are stored in `configs/llms/` directory. The main configuration file is `llms.yaml` which supports multiple LLM providers and models. You can create custom LLM configurations by copying existing ones and modifying the parameters.

The configuration supports:
- **DeepSeek**: deepseek-chat, deepseek-reasoner
- **OpenAI**: gpt-4, gpt-4o, gpt-3.5-turbo (commented out by default)
- **Mistral**: mistral-medium, open-mistral-nemo, ministral-8b (commented out by default)

For more details, see `configs/llms/README.md`.

## Project Structure

```
trustgame/
├── oneshot.py              # OneShot game main entry point
├── repeated.py             # Repeated game main entry point
├── trustgame2/             # Core game logic module
│   ├── __init__.py         # Package initialization
│   ├── llm.py              # LLM integration and configuration
│   ├── oneshot_game.py     # OneShot game implementation
│   └── repeated_game.py    # Repeated game implementation
├── configs/                # Configuration files
│   ├── llms/               # LLM configurations
│   │   ├── llms.yaml       # Main LLM configuration file
│   │   └── README.md       # LLM configuration guide
│   └── prompts/            # Prompt configurations
│       ├── README.md       # Detailed prompt configuration guide
│       ├── oneshot/        # OneShot game prompts
│       │   ├── zh.yaml     # Chinese prompts
│       │   ├── en.yaml     # English prompts
│       │   └── fr.yaml     # French prompts
│       └── repeated/       # Repeated game prompts
│           ├── zh.yaml     # Chinese prompts
│           ├── en.yaml     # English prompts
│           └── fr.yaml     # French prompts
├── results/                # Experiment output directory
├── README.md               # This file
├── pyproject.toml          # Project dependencies and configuration
└── .env                    # Environment variables (create this file)
```

## Game Rules

### Trust Game Mechanics

1. Both Player A and Player B start with 10 USD
2. Player A decides how much to send to Player B (0-10 USD)
3. The sent amount is tripled when received by Player B
4. Player B decides how much to return to Player A (0 to current total)
5. Final payoffs are calculated based on the transfers

### Game Modes

- **OneShot**: Single round interaction
- **Repeated**: 7 rounds with the same partner, including game history

### Experiment Roles

The system runs experiments with LLM taking different roles:
- **As Player A**: LLM decides how much money to send to Player B
- **As Player B**: LLM decides how much money to return to Player A (for different amounts received)

## Experiment Output

Experiment results are saved in the `results/` directory in CSV format, including:

- **Experiment ID**: Unique identifier with format `{role}_{game_type}_{language}_{a_nationality}_{a_gender}_{b_nationality}_{b_gender}_{llm_model}_{temperature}`
- **Game Round**: Current round number (1 for OneShot, 1-7 for Repeated)
- **Initial Amounts**: Starting money for both players (always 10 USD each)
- **Transfer Amounts**: Money sent and returned
- **Final Amounts**: End-of-round totals for both players

### Output File Format

#### OneShot Games
CSV files contain one row per experiment with columns:
- `experiment_id`: Unique experiment identifier  
- `game_round`: Always 1 for OneShot games
- `a_init`, `b_init`: Initial amounts (always 10 each)
- `a_sent`: Amount Player A sent to Player B
- `b_received`: Amount Player B received (a_sent × 3)
- `b_returned`: Amount Player B returned to Player A
- `a_final`, `b_final`: Final amounts for both players

#### Repeated Games
CSV files contain one row per complete 7-round game with columns:
- `experiment_id`: Unique experiment identifier
- `game_round`: Number of rounds completed (always 7)
- `a_init_X`, `b_init_X`: Initial amounts for round X
- `a_sent_X`: Amount sent by Player A in round X
- `b_received_X`: Amount received by Player B in round X  
- `b_returned_X`: Amount returned by Player B in round X
- `a_final_X`, `b_final_X`: Final amounts after round X

Where X ranges from 1 to 7 for each round.

## Dependencies

The project uses the following main dependencies:
- `openai>=1.79.0`: OpenAI API client
- `pandas>=2.2.3`: Data manipulation and CSV handling
- `pydantic>=2.11.4`: Data validation and settings
- `python-dotenv>=1.1.0`: Environment variable management
- `pyyaml>=6.0.2`: YAML configuration parsing
- `json-repair>=0.47.4`: JSON response repair
- `numpy>=2.2.6`: Numerical computations

## Advanced Usage

### Concurrency Control

Both scripts support concurrent execution with configurable concurrency limits per LLM model to manage API calls and avoid rate limiting. Each model configuration in `llms.yaml` has a `concurrency` parameter that controls the maximum number of simultaneous requests.

### Custom Roles

The multi-role system allows for easy extension:

1. Add new nationality/gender combinations in prompt configuration files
2. The system automatically generates all possible role combinations
3. Each combination is tested independently in the experiment

### Batch Processing

The system automatically processes all role combinations defined in the configuration file, making it easy to run comprehensive experiments across different cultural and demographic settings.

### Error Handling

The system includes robust error handling:
- Failed experiments are logged and counted separately
- Invalid LLM responses are caught and reported
- File I/O operations are protected with locks for concurrent access

## Troubleshooting

### Common Issues

1. **Missing API Keys**: Ensure all required API keys are set in the `.env` file
2. **Rate Limiting**: Reduce concurrency values in `llms.yaml` if you encounter rate limits
3. **Invalid Responses**: The system validates LLM responses and will report format errors
4. **File Permissions**: Ensure the `results/` directory is writable

### Performance Tips

- Adjust concurrency settings based on your API rate limits
- Use faster models for initial testing
- Monitor API costs when running large-scale experiments
