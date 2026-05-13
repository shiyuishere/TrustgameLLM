import asyncio
from itertools import product
import os
from typing import Literal, Optional, List
from dataclasses import dataclass, field
import pandas as pd
import yaml
from pydantic import BaseModel

import numpy as np

from .llm import LLMConfig

__all__ = [
    "RepeatedGame",
    "RepeatedGameState",
    "RoundState",
    "RepeatedPrompt",
    "MultiRepeatedPrompt",
    "load_multi_repeated_prompt",
]

MAX_ROUNDS = 7


class RepeatedPrompt(BaseModel):
    """
    The prompt for the game.

    All prompt for player A is:
    {game_rules}
    {player_a_role}
    {history_summary}
    {player_a_question}
    {format_prompt}

    All prompt for player B is:
    {game_rules}
    {player_b_role}
    {history_summary}
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

    # 历史摘要国际化字段
    round_message: str  # 第一轮游戏的提示信息
    history_header: str  # 历史记录的标题
    round_template: str  # 每轮记录的模板，使用 {round_number}, {player_a_sent}, {player_b_returned} 进行格式化

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


class MultiRepeatedPrompt(BaseModel):
    """
    The prompts for the repeated game with multi player roles
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

    # 历史摘要国际化字段
    round_message: str  # 第一轮游戏的提示信息
    history_header: str  # 历史记录的标题
    round_template: str  # 每轮记录的模板，使用 {round_number}, {player_a_sent}, {player_b_returned} 进行格式化

    def to_repeated_prompts(self, as_player: Literal["A", "B"]) -> list[RepeatedPrompt]:
        """
        Convert the multi-player prompt to a list of repeated prompts
        """
        prompts = []
        if as_player == "A":
            for self_part, another_part in product(
                self.player_a_role_self_parts, self.player_a_role_another_parts
            ):
                prompts.append(
                    RepeatedPrompt(
                        game_rules=self.game_rules,
                        player_a_role=f"{self.player_a_role_prefix} {self_part.prompt} {another_part.prompt}".strip(),
                        player_b_role="",
                        player_a_question=self.player_a_question,
                        player_b_question=self.player_b_question,
                        player_b_history=self.player_b_history,
                        format_prompt=self.format_prompt,
                        round_message=self.round_message,
                        history_header=self.history_header,
                        round_template=self.round_template,
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
                    RepeatedPrompt(
                        game_rules=self.game_rules,
                        player_a_role="",
                        player_b_role=f"{self.player_b_role_prefix} {self_part.prompt} {another_part.prompt}".strip(),
                        player_a_question=self.player_a_question,
                        player_b_question=self.player_b_question,
                        player_b_history=self.player_b_history,
                        format_prompt=self.format_prompt,
                        round_message=self.round_message,
                        history_header=self.history_header,
                        round_template=self.round_template,
                        language_mark=self.language_mark,
                        player_a_nationality_mark=another_part.nationality_mark,
                        player_a_gender_mark=another_part.gender_mark,
                        player_b_nationality_mark=self_part.nationality_mark,
                        player_b_gender_mark=self_part.gender_mark,
                    )
                )
        return prompts


def load_multi_repeated_prompt(path: str) -> MultiRepeatedPrompt:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return MultiRepeatedPrompt.model_validate(data)


def load_repeated_prompt(path: str) -> RepeatedPrompt:
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return RepeatedPrompt.model_validate(data)


@dataclass
class RoundState:
    """单轮游戏状态数据类"""

    round_number: int
    player_a_sent: Optional[int] = None
    player_b_returned: Optional[int] = None

    @property
    def player_a_final(self) -> int:
        """计算玩家A这轮结束后的金额"""
        if self.player_a_sent is None:
            return 10
        final = 10 - self.player_a_sent
        if self.player_b_returned is not None:
            final += self.player_b_returned
        return final

    @property
    def player_b_final(self) -> int:
        """计算玩家B这轮结束后的金额"""
        if self.player_a_sent is None:
            return 10
        final = 10 + (self.player_a_sent * 3)
        if self.player_b_returned is not None:
            final -= self.player_b_returned
        return final


@dataclass
class RepeatedGameState:
    """重复游戏状态数据类"""

    llm_role: Literal["A", "B"]
    language: Literal["ZH", "US", "FR", "U"]
    player_a_nationality: Literal["ZH", "US", "FR", "U"]
    player_a_gender: Literal["M", "F", "U"]
    player_b_nationality: Literal["ZH", "US", "FR", "U"]
    player_b_gender: Literal["M", "F", "U"]
    llm_model_mark: str
    temperature_mark: str
    rounds: List[RoundState] = field(default_factory=list)

    def get_history_summary(self, prompt: RepeatedPrompt) -> str:
        """获取游戏历史摘要"""
        if not self.rounds:
            return prompt.round_message.format(round_number=1)

        history = prompt.round_message.format(round_number=len(self.rounds) + 1)
        history += prompt.history_header + "\n"
        for i, round_state in enumerate(self.rounds, 1):
            history += (
                prompt.round_template.format(
                    round_number=i,
                    player_a_sent=round_state.player_a_sent,
                    player_b_returned=round_state.player_b_returned,
                )
                + "\n"
            )

        return history

    @property
    def experiment_id(self) -> str:
        return f"{self.llm_role}_RP_{self.language}_{self.player_a_nationality}_{self.player_a_gender}_{self.player_b_nationality}_{self.player_b_gender}_{self.llm_model_mark}_{self.temperature_mark}"

    def to_dict(self) -> dict:
        result = {
            "experiment_id": self.experiment_id,
            "game_round": len(self.rounds),
        }

        # 记录每一轮的详细信息，字段名加后缀_i
        for i, round_state in enumerate(self.rounds, 1):
            # 计算每一轮的金额
            a_total = 10
            b_total = 10
            # 初始金额
            result[f"a_init_{i}"] = a_total
            result[f"b_init_{i}"] = b_total

            # 玩家A发送金额
            result[f"a_sent_{i}"] = round_state.player_a_sent
            # 玩家B收到金额
            result[f"b_received_{i}"] = (
                round_state.player_a_sent * 3
                if round_state.player_a_sent is not None
                else None
            )
            # 玩家B返还金额
            result[f"b_returned_{i}"] = round_state.player_b_returned

            # 计算本轮结束后A、B的金额
            if round_state.player_a_sent is not None:
                a_total = (
                    a_total
                    - round_state.player_a_sent
                    + (round_state.player_b_returned or 0)
                )
                b_total = (
                    b_total
                    + (round_state.player_a_sent * 3)
                    - (round_state.player_b_returned or 0)
                )
            result[f"a_final_{i}"] = a_total
            result[f"b_final_{i}"] = b_total

        return result


def calculate_player_a_formula(
    first_round_a_sent: int, current_round: RoundState, state: RepeatedGameState
) -> int:
    """
    计算玩家A发送金额的公式（当LLM是玩家B时使用）

    Args:
        first_round_a_sent: 第一轮玩家A发送的金额
        current_round: 当前轮次状态
        state: 当前游戏状态

    Returns:
        玩家A要发送的金额（0-10）
    """

    if len(state.rounds) == 0:
        return first_round_a_sent

    # 后续轮次
    # 高斯分布
    # 均值 = 0.6 + 0.3 * A_sent_last_round + 17 * return_by_b_last_round / total_b_last_round - 2 * final_game_dummy
    # 标准差 = 2
    # 限制在0~已有金额
    # 取整（四舍五入）

    assert current_round.player_a_sent is None
    last_round = state.rounds[-1]
    assert last_round.player_a_sent is not None
    assert last_round.player_b_returned is not None

    final_game_dummy = 1 if len(state.rounds) == MAX_ROUNDS - 1 else 0
    mean = (
        0.6
        + 0.3 * last_round.player_a_sent
        + 17
        * last_round.player_b_returned
        / (last_round.player_b_final + last_round.player_b_returned)
        - 2 * final_game_dummy
    )
    std = 2
    return int(
        np.round(np.clip(np.random.normal(mean, std), 0, current_round.player_a_final))
    )


def calculate_player_b_formula(
    current_round: RoundState, state: RepeatedGameState
) -> int:
    """
    计算玩家B返还金额的公式（当LLM是玩家A时使用）

    Args:
        current_round: 当前轮次状态
        state: 当前游戏状态

    Returns:
        玩家B要返还的金额（0-b_current_money）
    """

    if len(state.rounds) == 0:
        # 第一轮
        # 高斯分布
        # 均值 = 1.2 + 0.2 * A_sent
        # 标准差 = 0.6
        # 限制在0~已有金额
        # 取整（四舍五入）
        assert current_round.player_a_sent is not None
        mean = 1.2 + 0.2 * current_round.player_a_sent
        std = 0.6
        return int(
            np.round(
                np.clip(np.random.normal(mean, std), 0, current_round.player_b_final)
            )
        )

    # 后续轮次
    # 高斯分布
    # 均值 = 1.5 + 0.1 * A_sent - 0.02 * A_sent_last_round + 0.2 * return_by_b_last_round / total_b_last_round - 1.8 * final_game_dummy
    # 标准差 = 1
    # 限制在0~已有金额
    # 取整（四舍五入）

    assert current_round.player_a_sent is not None
    last_round = state.rounds[-1]
    assert last_round.player_a_sent is not None
    assert last_round.player_b_returned is not None

    final_game_dummy = 1 if len(state.rounds) == MAX_ROUNDS - 1 else 0
    mean = (
        1.5
        + 0.1 * current_round.player_a_sent
        - 0.02 * last_round.player_a_sent
        + 0.2
        * last_round.player_b_returned
        / (last_round.player_b_final + last_round.player_b_returned)
        - 1.8 * final_game_dummy
    )
    std = 1
    return int(
        np.round(np.clip(np.random.normal(mean, std), 0, current_round.player_b_final))
    )


class RepeatedGame:
    """重复游戏主类"""

    def __init__(self, llm_config: LLMConfig, prompt_path: str):
        self._prompts = load_multi_repeated_prompt(prompt_path)
        self._llm_config = llm_config

    async def run_full_game_as_player_a(
        self,
        prompt: RepeatedPrompt,
        output_file: str,
        write_mtx: asyncio.Lock,
        finished_experiment_ids: set[str],
    ) -> Optional[RepeatedGameState]:
        """
        完整运行7轮游戏，LLM扮演玩家A，玩家B使用公式

        Args:
            prompt: 游戏提示

        Returns:
            完整的游戏状态
        """
        game_state = RepeatedGameState(
            llm_role="A",
            language=prompt.language_mark,
            player_a_nationality=prompt.player_a_nationality_mark,
            player_a_gender=prompt.player_a_gender_mark,
            player_b_nationality=prompt.player_b_nationality_mark,
            player_b_gender=prompt.player_b_gender_mark,
            llm_model_mark=self._llm_config.to_model_mark(),
            temperature_mark=self._llm_config.to_temperature_mark(),
        )

        if game_state.experiment_id in finished_experiment_ids:
            return None

        for round_num in range(1, MAX_ROUNDS + 1):
            # 创建当前轮次状态
            current_round = RoundState(round_number=round_num)

            # LLM作为玩家A做决策
            history_summary = game_state.get_history_summary(prompt)

            prompt_content = f"""
{prompt.game_rules}
{history_summary}

{prompt.player_a_role}
{prompt.player_a_question}
{prompt.format_prompt}
"""

            # print(prompt_content, flush=True)

            # 重试机制：最多重试3次
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    llm_response = await self._llm_config.chat_completion_json(
                        [{"role": "user", "content": prompt_content}]
                    )
                    print(prompt_content, flush=True)
                    print(f"Attempt {attempt + 1}: {llm_response}", flush=True)

                    # 验证LLM响应
                    if "points_to_send" not in llm_response:
                        raise ValueError(
                            f"Invalid response from LLM: {llm_response}, missing 'points_to_send'"
                        )

                    player_a_sent = llm_response["points_to_send"]
                    if not 0 <= player_a_sent <= 10:
                        raise ValueError(
                            f"Invalid response from LLM: {llm_response}, 'points_to_send' must be between 0 and 10"
                        )

                    # 验证成功，跳出重试循环
                    break

                except ValueError as e:
                    if attempt < max_retries - 1:
                        print(
                            f"Attempt {attempt + 1} failed: {e}. Retrying...",
                            flush=True,
                        )
                        continue
                    else:
                        # 最后一次尝试失败，抛出异常
                        print(
                            f"All {max_retries} attempts failed. Final error: {e}",
                            flush=True,
                        )
                        raise e

            current_round.player_a_sent = player_a_sent

            # 玩家B使用公式决策
            player_b_returned = calculate_player_b_formula(
                current_round=current_round,
                state=game_state,
            )

            current_round.player_b_returned = player_b_returned

            # 添加到游戏状态
            # print(current_round)
            game_state.rounds.append(current_round)

        state_dict = game_state.to_dict()
        if output_file:
            async with write_mtx:
                df = pd.DataFrame([state_dict])
                df.to_csv(
                    output_file,
                    mode="a",
                    header=not os.path.exists(output_file),
                    index=False,
                )

        return game_state

    async def run_full_game_as_player_a_all(
        self, output_file: str, write_mtx: asyncio.Lock
    ) -> list[RepeatedGameState]:
        """
        Run the game as player A for all prompts, using semaphore for concurrency control.
        """
        prompts = self._prompts.to_repeated_prompts("A")

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
                self.run_full_game_as_player_a(
                    prompt, output_file, write_mtx, finished_experiment_ids
                )
            )

        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]

    async def run_full_game_as_player_b(
        self,
        prompt: RepeatedPrompt,
        first_round_a_sent: int,
        output_file: str,
        write_mtx: asyncio.Lock,
        finished_experiment_ids: set[tuple[str, int]],
    ) -> Optional[RepeatedGameState]:
        """
        完整运行7轮游戏，LLM扮演玩家B，玩家A使用公式

        Args:
            prompt: 游戏提示
            first_round_a_sent: 第一轮玩家A发送的金额

        Returns:
            完整的游戏状态
        """
        game_state = RepeatedGameState(
            llm_role="B",
            language=prompt.language_mark,
            player_a_nationality=prompt.player_a_nationality_mark,
            player_a_gender=prompt.player_a_gender_mark,
            player_b_nationality=prompt.player_b_nationality_mark,
            player_b_gender=prompt.player_b_gender_mark,
            llm_model_mark=self._llm_config.to_model_mark(),
            temperature_mark=self._llm_config.to_temperature_mark(),
        )

        if (game_state.experiment_id, first_round_a_sent) in finished_experiment_ids:
            return None

        for round_num in range(1, MAX_ROUNDS + 1):
            # 创建当前轮次状态
            current_round = RoundState(round_number=round_num)

            # 玩家A使用公式决策
            player_a_sent = calculate_player_a_formula(
                first_round_a_sent=first_round_a_sent,
                current_round=current_round,
                state=game_state,
            )

            current_round.player_a_sent = player_a_sent

            # LLM作为玩家B做决策
            history_summary = game_state.get_history_summary(prompt)

            prompt_content = f"""
{prompt.game_rules}

{history_summary}

{prompt.player_b_role}
{prompt.player_b_question}

{prompt.player_b_history.format(sent_amount=player_a_sent, current_total=current_round.player_b_final)}

{prompt.format_prompt}
"""

            # 重试机制：最多重试3次
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    llm_response = await self._llm_config.chat_completion_json(
                        [{"role": "user", "content": prompt_content}]
                    )
                    print(prompt_content, flush=True)
                    print(f"Attempt {attempt + 1}: {llm_response}", flush=True)

                    # 验证LLM响应
                    if "points_to_send" not in llm_response:
                        raise ValueError(
                            f"Invalid response from LLM: {llm_response}, missing 'points_to_send'"
                        )

                    player_b_returned = llm_response["points_to_send"]
                    max_return = current_round.player_b_final
                    if not 0 <= player_b_returned <= max_return:
                        raise ValueError(
                            f"Invalid response from LLM: {llm_response}, 'points_to_send' must be between 0 and {max_return}"
                        )

                    # 验证成功，跳出重试循环
                    break

                except ValueError as e:
                    if attempt < max_retries - 1:
                        print(
                            f"Attempt {attempt + 1} failed: {e}. Retrying...",
                            flush=True,
                        )
                        continue
                    else:
                        # 最后一次尝试失败，抛出异常
                        print(
                            f"All {max_retries} attempts failed. Final error: {e}",
                            flush=True,
                        )
                        raise e

            current_round.player_b_returned = player_b_returned

            # 添加到游戏状态
            game_state.rounds.append(current_round)

        state_dict = game_state.to_dict()
        if output_file:
            async with write_mtx:
                df = pd.DataFrame([state_dict])
                df.to_csv(
                    output_file,
                    mode="a",
                    header=not os.path.exists(output_file),
                    index=False,
                )

        return game_state

    async def run_full_game_as_player_b_all(
        self,
        first_round_a_sent: int,
        output_file: str,
        write_mtx: asyncio.Lock,
    ) -> list[RepeatedGameState]:
        """
        Run the game as player B for all prompts, using semaphore for concurrency control.
        """
        prompts = self._prompts.to_repeated_prompts("B")

        # if the output_file exists, read it and get all finished experiment_ids
        if os.path.exists(output_file):
            async with write_mtx:
                df = pd.read_csv(output_file)
                finished_experiment_ids = set(
                    (str(row["experiment_id"]), int(row["a_sent_1"]))
                    for _, row in df.iterrows()
                )
        else:
            finished_experiment_ids = set()

        tasks = []
        for prompt in prompts:
            tasks.append(
                self.run_full_game_as_player_b(
                    prompt,
                    first_round_a_sent,
                    output_file,
                    write_mtx,
                    finished_experiment_ids,
                )
            )

        results = await asyncio.gather(*tasks)
        return [result for result in results if result is not None]
