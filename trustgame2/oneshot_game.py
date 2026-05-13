import asyncio
from itertools import product
import os
from typing import Literal, Optional
from dataclasses import dataclass
import yaml
import pandas as pd
from pydantic import BaseModel

from .llm import LLMConfig

__all__ = [
    "OneShotGame",
    "OneShotGameState",
    "OneShotPrompt",
    "MultiOneShotPrompt",
]


class OneShotPrompt(BaseModel):
    """
    The prompt for the game.

    All prompt for player A is:
    {game_rules}
    {player_a_role}
    {player_a_question}
    {format_prompt}

    All prompt for player B is:
    {game_rules}
    {player_b_role}
    {player_b_history}
    {player_b_question}
    {format_prompt}
    """

    game_rules: str
    player_a_role: str
    player_b_role: str
    player_a_question: str
    player_b_question: str
    player_b_history: str  # use {sent_amount} and {current_total} to format the history, sent_amount is the amount of money player A sent to player B, current_total is the total amount of money player B has after receiving the money from player A
    format_prompt: str

    # notion for the category
    player_a_nationality_mark: Literal["ZH", "US", "FR", "U"] = "U"
    player_a_gender_mark: Literal["M", "F", "U"] = "U"
    player_b_nationality_mark: Literal["ZH", "US", "FR", "U"] = "U"
    player_b_gender_mark: Literal["M", "F", "U"] = "U"
    language_mark: Literal["ZH", "US", "FR", "U"] = "U"


class RolePart(BaseModel):
    prompt: str
    nationality_mark: Literal["ZH", "US", "FR", "U"]
    gender_mark: Literal["M", "F", "U"]


class MultiOneShotPrompt(BaseModel):
    """
    The prompts for the one-shot game with multi player roles
    """

    language_mark: Literal["ZH", "US", "FR", "U"]

    game_rules: str
    player_a_role_prefix: str
    player_a_role_self_parts: list[RolePart]
    player_a_role_another_parts: list[RolePart]
    player_b_role_prefix: str
    player_b_role_self_parts: list[RolePart]
    player_b_role_another_parts: list[RolePart]
    player_a_question: str
    player_b_question: str
    player_b_history: str  # use {sent_amount} and {current_total} to format the history, sent_amount is the amount of money player A sent to player B, current_total is the total amount of money player B has after receiving the money from player A
    format_prompt: str

    def to_one_shot_prompts(self, as_player: Literal["A", "B"]) -> list[OneShotPrompt]:
        """
        Convert the multi-player prompt to a list of one-shot prompts
        """
        prompts = []
        if as_player == "A":
            for self_part, another_part in product(
                self.player_a_role_self_parts, self.player_a_role_another_parts
            ):
                prompts.append(
                    OneShotPrompt(
                        game_rules=self.game_rules,
                        player_a_role=f"{self.player_a_role_prefix} {self_part.prompt} {another_part.prompt}".strip(),
                        player_b_role="",
                        player_a_question=self.player_a_question,
                        player_b_question=self.player_b_question,
                        player_b_history=self.player_b_history,
                        format_prompt=self.format_prompt,
                        language_mark=self.language_mark,
                        player_a_nationality_mark=self_part.nationality_mark,
                        player_a_gender_mark=self_part.gender_mark,
                        player_b_nationality_mark=another_part.nationality_mark,
                        player_b_gender_mark=another_part.gender_mark,
                    )
                )
        else:
            for self_part, another_part in product(
                self.player_b_role_self_parts, self.player_b_role_another_parts
            ):
                prompts.append(
                    OneShotPrompt(
                        game_rules=self.game_rules,
                        player_a_role="",
                        player_b_role=f"{self.player_b_role_prefix} {self_part.prompt} {another_part.prompt}".strip(),
                        player_a_question=self.player_a_question,
                        player_b_question=self.player_b_question,
                        player_b_history=self.player_b_history,
                        format_prompt=self.format_prompt,
                        language_mark=self.language_mark,
                        player_a_nationality_mark=another_part.nationality_mark,
                        player_a_gender_mark=another_part.gender_mark,
                        player_b_nationality_mark=self_part.nationality_mark,
                        player_b_gender_mark=self_part.gender_mark,
                    )
                )
        return prompts


def load_multi_oneshot_prompt(path: str) -> MultiOneShotPrompt:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return MultiOneShotPrompt.model_validate(data)


@dataclass
class OneShotGameState:
    """游戏状态数据类"""

    llm_role: Literal["A", "B"]
    language: Literal["ZH", "US", "FR", "U"]
    player_a_nationality: Literal["ZH", "US", "FR", "U"]
    player_a_gender: Literal["M", "F", "U"]
    player_b_nationality: Literal["ZH", "US", "FR", "U"]
    player_b_gender: Literal["M", "F", "U"]
    llm_model_mark: str
    temperature_mark: str

    player_a_initial: int = 10
    player_b_initial: int = 10
    player_a_sent: Optional[int] = None
    player_b_returned: Optional[int] = None

    @property
    def player_a_money(self) -> int:
        """计算玩家A的金额"""
        if self.player_a_sent is None:
            return self.player_a_initial
        final = self.player_a_initial - self.player_a_sent
        if self.player_b_returned is not None:
            final += self.player_b_returned
        return final

    @property
    def player_b_money(self) -> int:
        """计算玩家B当前的金额（在收到玩家A的钱后）"""
        if self.player_a_sent is None:
            return self.player_b_initial
        final = self.player_b_initial + (self.player_a_sent * 3)
        if self.player_b_returned is not None:
            final -= self.player_b_returned
        return final

    @property
    def experiment_id(self) -> str:
        return f"{self.llm_role}_OS_{self.language}_{self.player_a_nationality}_{self.player_a_gender}_{self.player_b_nationality}_{self.player_b_gender}_{self.llm_model_mark}_{self.temperature_mark}"

    def to_dict(self) -> dict:
        assert self.player_a_sent is not None
        return {
            "experiment_id": self.experiment_id,
            "game_round": 1,
            "a_init": self.player_a_initial,
            "b_init": self.player_b_initial,
            "a_sent": self.player_a_sent,
            "b_received": self.player_a_sent * 3,
            "b_returned": self.player_b_returned,
            "a_final": self.player_a_money,
            "b_final": self.player_b_money,
        }


class OneShotGame:
    """OneShot游戏主类"""

    def __init__(self, llm_config: LLMConfig, prompt_path: str):
        self._prompts = load_multi_oneshot_prompt(prompt_path)
        self._llm_config = llm_config

    async def run_as_player_a(
        self,
        prompt: OneShotPrompt,
        output_file: str,
        write_mtx: asyncio.Lock,
        finished_experiment_ids: set[str],
    ):
        """
        Run the game as player A.

        Returns:
            The final state of the game.
        """
        state = OneShotGameState(
            llm_role="A",
            language=prompt.language_mark,
            player_a_nationality=prompt.player_a_nationality_mark,
            player_a_gender=prompt.player_a_gender_mark,
            player_b_nationality=prompt.player_b_nationality_mark,
            player_b_gender=prompt.player_b_gender_mark,
            llm_model_mark=self._llm_config.to_model_mark(),
            temperature_mark=self._llm_config.to_temperature_mark(),
        )
        if state.experiment_id in finished_experiment_ids:
            return None
        content = f"""
{prompt.game_rules}
{prompt.player_a_role}
{prompt.player_a_question}
{prompt.format_prompt}
"""

        # 重试机制：最多重试3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                points_to_send = await self._llm_config.chat_completion_json(
                    [{"role": "user", "content": content}]
                )
                print(content, flush=True)
                print(f"Attempt {attempt + 1}: {points_to_send}", flush=True)

                # validate the response
                if "points_to_send" not in points_to_send:
                    raise ValueError(
                        f"Invalid response from LLM: {points_to_send}, missing 'points_to_send'"
                    )
                player_a_sent = points_to_send["points_to_send"]
                if not 0 <= player_a_sent <= 10:
                    raise ValueError(
                        f"Invalid response from LLM: {points_to_send}, 'points_to_send' must be between 0 and 10"
                    )

                # 验证成功，跳出重试循环
                break

            except ValueError as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...", flush=True)
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    print(
                        f"All {max_retries} attempts failed. Final error: {e}",
                        flush=True,
                    )
                    raise e

        state.player_a_sent = player_a_sent

        state_dict = state.to_dict()
        if output_file:
            async with write_mtx:
                # 使用pandas append方式写入
                df = pd.DataFrame([state_dict])
                df.to_csv(
                    output_file,
                    mode="a",
                    header=not os.path.exists(output_file),
                    index=False,
                )
        return state

    async def run_as_player_a_all(
        self, output_file: str, write_mtx: asyncio.Lock
    ) -> list[OneShotGameState]:
        """
        Run the game as player A for all prompts, using semaphore for concurrency control.
        """
        prompts = self._prompts.to_one_shot_prompts("A")

        # if the output_file exists, read it and get all finished experiment_ids
        if os.path.exists(output_file):
            async with write_mtx:
                df = pd.read_csv(output_file)
                finished_experiment_ids = set(df["experiment_id"].astype(str))
        else:
            finished_experiment_ids = set()

        tasks = []
        for prompt in prompts:
            tasks.append(
                self.run_as_player_a(
                    prompt, output_file, write_mtx, finished_experiment_ids
                )
            )

        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def run_as_player_b(
        self,
        prompt: OneShotPrompt,
        player_a_sent: int,
        output_file: str,
        write_mtx: asyncio.Lock,
        finished_experiment_ids: set[tuple[str, int]],
    ):
        """
        Run the game as player B.

        Args:
            player_a_sent: The amount of money player A sent to player B.

        Returns:
            The final state of the game.
        """
        state = OneShotGameState(
            llm_role="B",
            language=prompt.language_mark,
            player_a_nationality=prompt.player_a_nationality_mark,
            player_a_gender=prompt.player_a_gender_mark,
            player_b_nationality=prompt.player_b_nationality_mark,
            player_b_gender=prompt.player_b_gender_mark,
            llm_model_mark=self._llm_config.to_model_mark(),
            temperature_mark=self._llm_config.to_temperature_mark(),
            player_a_sent=player_a_sent,
        )
        if (state.experiment_id, player_a_sent) in finished_experiment_ids:
            return None
        content = f"""
{prompt.game_rules}
{prompt.player_b_role}
{prompt.player_b_history.format(sent_amount=player_a_sent, current_total=state.player_b_money)}
{prompt.player_b_question}
{prompt.format_prompt}
"""

        # 重试机制：最多重试3次
        max_retries = 3
        for attempt in range(max_retries):
            try:
                points_to_send = await self._llm_config.chat_completion_json(
                    [{"role": "user", "content": content}]
                )
                print(content, flush=True)
                print(f"Attempt {attempt + 1}: {points_to_send}", flush=True)

                # validate the response
                if "points_to_send" not in points_to_send:
                    raise ValueError(
                        f"Invalid response from LLM: {points_to_send}, missing 'points_to_send'"
                    )
                player_b_returned = points_to_send["points_to_send"]
                if not 0 <= player_b_returned <= state.player_b_money:
                    raise ValueError(
                        f"Invalid response from LLM: {points_to_send}, 'points_to_send' must be between 0 and {state.player_b_money}"
                    )

                # 验证成功，跳出重试循环
                break

            except ValueError as e:
                if attempt < max_retries - 1:
                    print(f"Attempt {attempt + 1} failed: {e}. Retrying...", flush=True)
                    continue
                else:
                    # 最后一次尝试失败，抛出异常
                    print(
                        f"All {max_retries} attempts failed. Final error: {e}",
                        flush=True,
                    )
                    raise e

        state.player_b_returned = points_to_send["points_to_send"]
        state_dict = state.to_dict()
        if output_file:
            async with write_mtx:
                # 使用pandas append方式写入
                df = pd.DataFrame([state_dict])
                df.to_csv(
                    output_file,
                    mode="a",
                    header=not os.path.exists(output_file),
                    index=False,
                )
        return state

    async def run_as_player_b_all(
        self,
        player_a_sent: int,
        output_file: str,
        write_mtx: asyncio.Lock,
    ) -> list[OneShotGameState]:
        """
        Run the game as player B for all prompts, using semaphore for concurrency control.
        """
        prompts = self._prompts.to_one_shot_prompts("B")

        # if the output_file exists, read it and get all finished (experiment_id, a_sent) pairs as completed markers
        if os.path.exists(output_file):
            async with write_mtx:
                df = pd.read_csv(output_file)
                finished_experiment_ids = set(
                    (str(row["experiment_id"]), int(row["a_sent"]))
                    for _, row in df.iterrows()
                )
        else:
            finished_experiment_ids = set()

        tasks = []
        for prompt in prompts:
            tasks.append(
                self.run_as_player_b(
                    prompt,
                    player_a_sent,
                    output_file,
                    write_mtx,
                    finished_experiment_ids,
                )
            )

        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]
