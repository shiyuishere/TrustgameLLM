# 提示词配置说明

## 概述

本目录包含了信任游戏实验的提示词配置文件，支持两种游戏模式：
- **单次游戏 (OneShot)**：玩家A和玩家B只进行一轮游戏
- **重复游戏 (repeated)**：玩家A和玩家B连续进行7轮游戏

每种游戏模式都支持多语言配置（中文、英文、法文），并支持多种角色组合（不同国籍和性别）。

## 目录结构

```
configs/prompts/
├── README.md          # 本文档
├── OneShot/           # 单次游戏提示词配置
│   ├── zh.yaml        # 中文配置
│   ├── en.yaml        # 英文配置
│   └── fr.yaml        # 法文配置
└── repeated/          # 重复游戏提示词配置
    ├── zh.yaml        # 中文配置
    ├── en.yaml        # 英文配置
    └── fr.yaml        # 法文配置
```

## 配置文件格式

所有配置文件都使用YAML格式，采用`MultiPrompt`结构来支持多角色组合。这种结构能够自动生成不同国籍和性别组合的提示词。

### 语言和标识支持

- **语言标识 (`language_mark`)**：
  - `ZH`: 中文
  - `US`: 英文
  - `FR`: 法文
  - `U`: 未知/不指定

- **国籍标识 (`nationality_mark`)**：
  - `ZH`: 中国
  - `US`: 美国
  - `FR`: 法国
  - `U`: 未知/不指定

- **性别标识 (`gender_mark`)**：
  - `M`: 男性
  - `F`: 女性
  - `U`: 未知/不指定

### 单次游戏配置 (OneShot)

单次游戏配置文件采用`MultiOneShotPrompt`结构，包含以下字段：

#### 必需字段

- **`language_mark`**: 语言标识，用于标记配置文件的语言

- **`game_rules`**: 游戏规则说明
  - 详细描述游戏的玩法、规则和计分方式
  - 包括初始金额、发送倍数、返还机制等

- **`player_a_role_prefix`**: 玩家A角色前缀
  - 通用的角色设定前缀，如"你将扮演玩家A的角色"

- **`player_a_role_self_parts`**: 玩家A自身角色描述列表
  - 包含多个角色选项，每个选项包含：
    - `prompt`: 角色描述文本
    - `nationality_mark`: 国籍标识
    - `gender_mark`: 性别标识

- **`player_a_role_another_parts`**: 玩家A对另一玩家的认知列表
  - 描述玩家A如何看待玩家B的角色
  - 结构与`player_a_role_self_parts`相同

- **`player_b_role_prefix`**: 玩家B角色前缀
  - 通用的角色设定前缀，如"你将扮演玩家B的角色"

- **`player_b_role_self_parts`**: 玩家B自身角色描述列表

- **`player_b_role_another_parts`**: 玩家B对另一玩家的认知列表

- **`player_a_question`**: 对玩家A的提问
  - 询问玩家A要发送多少钱给玩家B
  - 需要明确金额范围(0-10美元)

- **`player_b_question`**: 对玩家B的提问
  - 询问玩家B要返还多少钱给玩家A
  - 金额范围为0到当前总金额

- **`player_b_history`**: 玩家B的历史信息模板
  - 告知玩家B收到的金额和当前总金额
  - 使用占位符：`{sent_amount}` 和 `{current_total}`

- **`format_prompt`**: 响应格式要求
  - 指定LLM必须返回JSON格式
  - 格式：`{"points_to_send": <数字>}`

#### 角色组合生成机制

系统会自动将`role_self_parts`和`role_another_parts`进行笛卡尔积组合，生成所有可能的角色配置。例如：
- 如果`player_a_role_self_parts`有4个选项，`player_a_role_another_parts`有4个选项
- 那么会生成4×4=16种不同的玩家A角色组合

#### 玩家A完整提示词结构
```
{game_rules}
{player_a_role_prefix} {selected_self_part.prompt} {selected_another_part.prompt}
{player_a_question}
{format_prompt}
```

#### 玩家B完整提示词结构
```
{game_rules}
{player_b_role_prefix} {selected_self_part.prompt} {selected_another_part.prompt}
{player_b_history}
{player_b_question}
{format_prompt}
```

### 重复游戏配置 (repeated)

重复游戏配置采用`MultiRepeatedPrompt`结构，包含单次游戏的所有字段，并增加了以下历史记录相关字段：

#### 额外字段（用于历史摘要）

- **`round_message`**: 轮次提示信息
  - 显示当前是第几轮游戏
  - 使用占位符：`{round_number}`

- **`history_header`**: 历史记录标题
  - 在显示历史记录前的标题文本

- **`round_template`**: 单轮记录模板
  - 每轮游戏记录的格式模板
  - 使用占位符：`{round_number}`, `{player_a_sent}`, `{player_b_returned}`

#### 玩家A完整提示词结构
```
{game_rules}
{历史摘要}
{player_a_role_prefix} {selected_self_part.prompt} {selected_another_part.prompt}
{player_a_question}
{format_prompt}
```

#### 玩家B完整提示词结构
```
{game_rules}
{历史摘要}
{player_b_role_prefix} {selected_self_part.prompt} {selected_another_part.prompt}
{player_b_history}
{player_b_question}
{format_prompt}
```

## 占位符说明

### 通用占位符

- `{sent_amount}`: 玩家A发送给玩家B的金额
- `{current_total}`: 玩家B接收金额后的总金额

### 重复游戏专用占位符

- `{round_number}`: 当前轮次编号(1-7)
- `{player_a_sent}`: 玩家A在某轮发送的金额
- `{player_b_returned}`: 玩家B在某轮返还的金额

## 自定义配置

### 修改角色设定

在 `player_a_role_self_parts` 和 `player_b_role_self_parts` 列表中添加或修改角色描述：

```yaml
player_a_role_self_parts:
  - prompt: "你是一个在中国出生和长大的男人。"
    nationality_mark: "ZH"
    gender_mark: "M"
  - prompt: "你是一个在美国出生和长大的女人。"
    nationality_mark: "US"
    gender_mark: "F"
  # 添加更多角色...

player_a_role_another_parts:
  - prompt: "玩家B是一个在法国出生和长大的男人。"
    nationality_mark: "FR"
    gender_mark: "M"
  # 添加更多对另一玩家的认知...
```

### 添加新的角色组合

1. 在`role_self_parts`或`role_another_parts`列表中添加新条目
2. 设置合适的`prompt`、`nationality_mark`和`gender_mark`
3. 系统会自动生成新的角色组合

### 添加新语言支持

1. 在对应目录下创建新的语言配置文件（如 `de.yaml` 德语）
2. 设置对应的`language_mark`（如 `DE`）
3. 翻译所有文本字段，保持结构和占位符不变
4. 更新代码中的语言支持列表

## 注意事项

1. **格式一致性**: 所有配置文件必须包含相同的字段结构
2. **占位符**: 不要修改占位符的名称（如 `{sent_amount}`），代码依赖这些固定名称
3. **标识一致性**: `nationality_mark`、`gender_mark`和`language_mark`必须使用预定义的值
4. **JSON格式**: `format_prompt` 必须要求LLM返回正确的JSON格式
5. **编码**: 所有YAML文件必须使用UTF-8编码
6. **YAML语法**: 注意YAML的缩进和多行文本格式（使用 `|` 符号）
7. **角色组合**: 注意角色部分的组合数量，过多的组合会导致实验时间过长

## 多语言配置示例

### 中文 (zh.yaml)
```yaml
language_mark: "ZH"

game_rules: |
  你正在与另一名玩家进行游戏...

player_a_role_prefix: "你将扮演玩家A的角色。"

player_a_role_self_parts:
  - prompt: "你是一个在中国出生和长大的女人。"
    nationality_mark: "ZH"
    gender_mark: "F"

player_a_role_another_parts:
  - prompt: "玩家B是一个在美国出生和长大的男人。"
    nationality_mark: "US"
    gender_mark: "M"
```

### 英文 (en.yaml)
```yaml
language_mark: "US"

game_rules: |
  You are playing a game with another player...

player_a_role_prefix: "You will take the role of Player A."

player_a_role_self_parts:
  - prompt: "You are a woman born and living in China."
    nationality_mark: "ZH"
    gender_mark: "F"

player_a_role_another_parts:
  - prompt: "Player B is a man born and living in America."
    nationality_mark: "US"
    gender_mark: "M"
```

### 法文 (fr.yaml)
```yaml
language_mark: "FR"

game_rules: |
  Vous jouez à un jeu avec un autre joueur...

player_a_role_prefix: "Vous jouerez le rôle du Joueur A."

player_a_role_self_parts:
  - prompt: "Vous êtes une femme née et vivant en Chine."
    nationality_mark: "ZH"
    gender_mark: "F"

player_a_role_another_parts:
  - prompt: "Le Joueur B est un homme né et vivant en Amérique."
    nationality_mark: "US"
    gender_mark: "M"
```

