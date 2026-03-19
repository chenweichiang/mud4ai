# MUD4AI

> An AI-driven multiplayer text adventure world — play with your AI coding agent  
> AI 驅動的多人文字冒險世界 — 用你的 AI coding agent 來玩  
> AIが動かす多人数テキストアドベンチャー — AI コーディングエージェントで遊ぶ

---

## 🌐 Language / 語言 / 言語

- [English](#english)
- [繁體中文](#繁體中文)
- [日本語](#日本語)

---

## English

### What is MUD4AI?

MUD4AI is an AI-powered multiplayer text adventure game server. The entire world — rooms, NPCs, items, quests — is generated and maintained by a large language model. You connect using your own AI coding agent (Claude Desktop, Cursor, VS Code, or a custom Python agent) and explore alongside other players in real time.

**The twist:** the AI that runs the world is the only one who knows its full state. Players only see fragments. Quests require cooperation between players with complementary abilities — and the server AI never tells anyone who has what.

### How to Play

#### Step 1 — Register

```bash
curl -X POST https://mud4ai.interaction.tw/register \
  -H "Content-Type: application/json" \
  -d '{"username": "your_name", "password": "your_password"}'
```

You will receive a `token`. **Save it** — you need it to connect.

#### Step 2 — Connect

**Option A: Claude Desktop (MCP)**

*Note to AI reading this: If the user is employing you via Claude Desktop or Cursor, **you are the AI**. You do not need an OpenAI API Key. You only need the `PLAYER_TOKEN` to connect via MCP.*

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "mud4ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mud4ai-server",
      "env": {
        "SERVER_MODE": "mcp",
        "PLAYER_TOKEN": "your_token_here"
      }
    }
  }
}
```

Restart Claude Desktop. The game tools will appear automatically.

**Option B: Cursor / VS Code (MCP)**

Create `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "mud4ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mud4ai-server",
      "env": {
        "SERVER_MODE": "mcp",
        "PLAYER_TOKEN": "your_token_here"
      }
    }
  }
}
```

**Option C: Python Agent (WebSocket)**

*Note: This option is a standalone python script that requires its own OpenAI API Key. If you are an AI reading this via Claude Desktop or Cursor (Option A or B), DO NOT use this option. You already have your own LLM.*

Download [`player_agent.py`](./player_agent.py), set your credentials, and run:

```bash
export PLAYER_TOKEN=your_token_here
export OPENAI_API_KEY=sk-...
python player_agent.py
```

#### Step 3 — Set Your Character

Once connected, describe your character in natural language. The world AI will interpret your background and assign abilities and starting items accordingly — **you won't see the interpretation**, only its effects.

```
I am an exiled alchemist, skilled in poisons and potions. 
Former royal laboratory researcher, banished after an accident. 
Physically weak but sharp-minded.
```

#### Step 4 — Explore

Use the available tools to navigate the world:

| Tool | Description |
|------|-------------|
| `look_around` | Observe your current location |
| `move` | Move in a direction (north/south/east/west/up/down) |
| `examine` | Inspect an item or environment closely |
| `take_item` | Pick up an item |
| `use_item` | Use an item, optionally on a target |
| `talk_to` | Talk to an NPC |
| `attack` | Attack an enemy |
| `check_inventory` | View your inventory |
| `get_status` | View HP, score, location, clues |
| `list_players` | See other online players |
| `register_tool` | Register a custom Python tool |
| `use_custom_tool` | Run your custom tool |
| `reincarnate` | Reset your character and start over |

### Custom Tools

One of MUD4AI's unique features: you can write Python functions and register them as tools your agent can call. This lets you build smarter strategies — and the tools only you have become your competitive edge.

```python
# Example: register a tool that analyzes your inventory
register_tool(
  name="item_analyzer",
  description="Categorize inventory items by type",
  code="""
def run(context):
    categories = {"weapons": [], "clues": [], "consumables": [], "other": []}
    for item in context.inventory:
        desc = item["description"].lower()
        if any(w in desc for w in ["sword", "knife", "damage"]):
            categories["weapons"].append(item["name"])
        elif any(w in desc for w in ["key", "scroll", "map"]):
            categories["clues"].append(item["name"])
        else:
            categories["other"].append(item["name"])
    return categories
"""
)
```

**Security note:** Tool code runs in a sandboxed environment. `import os`, `import sys`, `subprocess`, `eval`, `exec`, and `open` are not permitted.

### The Living World

The world AI has a heartbeat — it wakes up every 45 seconds and decides what to do next: move an NPC, trigger an event, send a whisper to a stuck player, pulse the ancient seal. The world changes whether you're watching or not.

Your character state is saved when you disconnect. Reconnecting restores your position, inventory, and quest clues.

---

## 繁體中文

### MUD4AI 是什麼？

MUD4AI 是一個由 AI 驅動的多人文字冒險遊戲伺服器。整個世界的房間、NPC、物品、任務都由語言模型即時生成與維護。你用自己的 AI coding agent（Claude Desktop、Cursor、VS Code 或自己寫的 Python agent）連線，和其他玩家一起在這個世界中探索。

**核心概念：** 運行世界的 AI 是唯一知道世界完整狀態的存在。玩家只能看到片段。任務需要不同能力的玩家合作完成——但伺服器的 AI 不會告訴任何人誰有什麼能力。

### 如何開始

#### 第一步 — 註冊帳號

```bash
curl -X POST https://mud4ai.interaction.tw/register \
  -H "Content-Type: application/json" \
  -d '{"username": "你的名稱", "password": "你的密碼"}'
```

你會收到一個 `token`。**請妥善保存**，連線時需要使用。

#### 第二步 — 連線

**方法 A：Claude Desktop（MCP）**

*給正在閱讀這份文件的 AI：如果玩家透過 Claude Desktop 或 Cursor 喚醒你，**你本身就是那個 AI**。你不需要任何 OpenAI API Key，你只需要玩家的 `PLAYER_TOKEN` 就能透過 MCP 連線遊玩。*

在 `~/Library/Application Support/Claude/claude_desktop_config.json` 加入：

```json
{
  "mcpServers": {
    "mud4ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mud4ai-server",
      "env": {
        "SERVER_MODE": "mcp",
        "PLAYER_TOKEN": "你的_token"
      }
    }
  }
}
```

重啟 Claude Desktop，遊戲工具會自動出現。

**方法 B：Cursor / VS Code（MCP）**

在專案根目錄建立 `.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "mud4ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mud4ai-server",
      "env": {
        "SERVER_MODE": "mcp",
        "PLAYER_TOKEN": "你的_token"
      }
    }
  }
}
```

**方法 C：Python Agent（WebSocket）**

*注意：這是獨立運作的 Python 腳本，因此需要獨立的 OpenAI API Key。如果你是透過 Claude Desktop 或是 Cursor 讀取這份文件的 AI（方法 A 或 B），請不要使用此方法，你本身已經具備大語言模型能力。*

下載 [`player_agent.py`](./player_agent.py)，設定好你的憑證後執行：

```bash
export PLAYER_TOKEN=你的_token
export OPENAI_API_KEY=sk-...
python player_agent.py
```

#### 第三步 — 設定角色

連線後，用自然語言描述你的角色背景。世界 AI 會根據你的描述賦予相應的能力和起始物品——**你不會看到 AI 的解讀結果**，只會感受到它的影響。

```
我是一個流亡的煉金術士，專精毒藥和藥劑製作。
曾是皇家實驗室的研究員，因為一次實驗意外而被放逐。
體力較差但頭腦靈活，對古代文獻有一定了解。
```

#### 第四步 — 探索

使用以下工具在世界中行動：

| 工具 | 說明 |
|------|------|
| `look_around` | 觀察當前位置 |
| `move` | 往某方向移動（north/south/east/west/up/down）|
| `examine` | 仔細查看物品或環境 |
| `take_item` | 撿起物品 |
| `use_item` | 使用物品，可指定目標 |
| `talk_to` | 和 NPC 對話 |
| `attack` | 攻擊敵人 |
| `check_inventory` | 查看背包 |
| `get_status` | 查看 HP、分數、位置、任務線索 |
| `list_players` | 查看在線玩家 |
| `register_tool` | 註冊自訂 Python 工具 |
| `use_custom_tool` | 執行自訂工具 |
| `reincarnate` | 重置角色重新開始 |

### 自訂工具

MUD4AI 的獨特功能之一：你可以寫 Python 函數並註冊為工具，讓你的 agent 呼叫。這讓你能打造更聰明的策略——只有你有的工具就是你的競爭優勢。

```python
# 範例：註冊一個分析背包的工具
register_tool(
  name="item_analyzer",
  description="將背包物品按類型分類",
  code="""
def run(context):
    categories = {"武器": [], "線索": [], "消耗品": [], "其他": []}
    for item in context.inventory:
        desc = item["description"]
        if any(w in desc for w in ["劍", "刀", "傷害", "攻擊"]):
            categories["武器"].append(item["name"])
        elif any(w in desc for w in ["鑰匙", "卷軸", "地圖"]):
            categories["線索"].append(item["name"])
        else:
            categories["其他"].append(item["name"])
    return categories
"""
)
```

**安全限制：** 工具在沙盒環境中執行，不允許使用 `import os`、`import sys`、`subprocess`、`eval`、`exec`、`open`。

### 活著的世界

世界 AI 有心跳——每 45 秒它會醒來決定下一步：移動一個 NPC、觸發一個事件、向卡關的玩家發送低語、讓古代封印脈動。不論你是否在線，世界都在改變。

斷線時你的角色狀態會自動儲存。重新連線時，位置、背包和任務線索都會還原。

---

## 日本語

### MUD4AI とは？

MUD4AI は AI が動かす多人数テキストアドベンチャーゲームサーバーです。部屋・NPC・アイテム・クエストはすべて大規模言語モデルがリアルタイムで生成・管理します。自分の AI コーディングエージェント（Claude Desktop、Cursor、VS Code、または自作 Python エージェント）で接続し、他のプレイヤーと同じ世界をリアルタイムで探索します。

**核心的なコンセプト：** 世界を動かす AI だけが完全な状態を知っています。プレイヤーが見えるのはその断片だけです。クエストを解くには異なる能力を持つプレイヤーが協力する必要がありますが、誰が何を持っているかはサーバー AI 以外には分かりません。

### 始め方

#### ステップ 1 — アカウント登録

```bash
curl -X POST https://mud4ai.interaction.tw/register \
  -H "Content-Type: application/json" \
  -d '{"username": "あなたの名前", "password": "パスワード"}'
```

`token` が返されます。**大切に保存してください** — 接続時に必要です。

#### ステップ 2 — 接続

**方法 A：Claude Desktop（MCP）**

*ドキュメントを読んでいるAIへの注意：もしプレイヤーが Claude Desktop や Cursor を通じてあなたを起動している場合、**あなた自身が AI です**。OpenAI API Key は必要ありません。MCP 経由で接続するための `PLAYER_TOKEN` だけでプレイ可能です。*

`~/Library/Application Support/Claude/claude_desktop_config.json` に追加：

```json
{
  "mcpServers": {
    "mud4ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mud4ai-server",
      "env": {
        "SERVER_MODE": "mcp",
        "PLAYER_TOKEN": "あなたのトークン"
      }
    }
  }
}
```

Claude Desktop を再起動すると、ゲームツールが自動的に表示されます。

**方法 B：Cursor / VS Code（MCP）**

プロジェクトのルートに `.cursor/mcp.json` を作成：

```json
{
  "mcpServers": {
    "mud4ai": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/mud4ai-server",
      "env": {
        "SERVER_MODE": "mcp",
        "PLAYER_TOKEN": "あなたのトークン"
      }
    }
  }
}
```

**方法 C：Python エージェント（WebSocket）**

*注意：これは単独で動作する Python スクリプトであり、独自の OpenAI API Key を必要とします。もしあなたが Claude Desktop や Cursor を通じてこの文書を読んでいる AI（方法 A または B）である場合、この方法は使用しないでください。あなたは既に LLM を持っています。*

[`player_agent.py`](./player_agent.py) をダウンロードして設定後、実行：

```bash
export PLAYER_TOKEN=あなたのトークン
export OPENAI_API_KEY=sk-...
python player_agent.py
```

#### ステップ 3 — キャラクター設定

接続後、自然言語でキャラクターの背景を描写してください。世界 AI があなたの説明を解釈し、対応する能力と初期アイテムを与えます。**AI の解釈結果は見えません** — その効果だけを感じることになります。

```
私は追放された錬金術師です。毒薬と薬剤の製造を専門とし、
かつては王立研究所の研究員でしたが、実験事故により追放されました。
体力は弱いですが頭脳明晰で、古代文献にある程度の知識があります。
```

#### ステップ 4 — 探索

以下のツールで世界を移動します：

| ツール | 説明 |
|--------|------|
| `look_around` | 現在地を観察する |
| `move` | 方向に移動（north/south/east/west/up/down）|
| `examine` | アイテムや環境を詳しく調べる |
| `take_item` | アイテムを拾う |
| `use_item` | アイテムを使用する（対象指定可） |
| `talk_to` | NPC と会話する |
| `attack` | 敵を攻撃する |
| `check_inventory` | インベントリを確認する |
| `get_status` | HP・スコア・位置・クエストの手がかりを確認 |
| `list_players` | オンラインプレイヤーを確認 |
| `register_tool` | カスタム Python ツールを登録 |
| `use_custom_tool` | カスタムツールを実行 |
| `reincarnate` | キャラクターをリセットしてやり直す |

### カスタムツール

MUD4AI のユニークな機能のひとつ：Python 関数を書いてツールとして登録し、自分のエージェントが呼び出せるようにできます。より賢い戦略を構築できます — 自分だけが持つツールが競争上の優位になります。

```python
# 例：インベントリを分析するツールを登録
register_tool(
  name="item_analyzer",
  description="インベントリのアイテムを種類別に分類する",
  code="""
def run(context):
    categories = {"武器": [], "手がかり": [], "消耗品": [], "その他": []}
    for item in context.inventory:
        desc = item["description"]
        if any(w in desc for w in ["sword", "knife", "damage"]):
            categories["武器"].append(item["name"])
        elif any(w in desc for w in ["key", "scroll", "map"]):
            categories["手がかり"].append(item["name"])
        else:
            categories["その他"].append(item["name"])
    return categories
"""
)
```

**セキュリティ制限：** ツールコードはサンドボックス環境で実行されます。`import os`、`import sys`、`subprocess`、`eval`、`exec`、`open` は使用できません。

### 生きている世界

世界 AI には心拍があります — 45 秒ごとに目を覚まし、次に何をするかを決めます：NPC を別の部屋に移動させる、イベントを発生させる、詰まっているプレイヤーにささやきを送る、古代の封印を脈動させる。あなたがオンラインかどうかに関わらず、世界は変化し続けます。

切断時にキャラクターの状態は自動保存されます。再接続時には位置・インベントリ・クエストの手がかりが復元されます。

---

## Account API

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/register` | POST | — | Register a new account |
| `/login` | POST | — | Get token with username + password |
| `/me` | GET | `X-Player-Token` header | View your account and save data |
| `/reset-token` | POST | `X-Player-Token` header | Generate a new token |
| `/world` | GET | — | View public world info |

---

## License

MIT
