"""
player_agent.py — MUD4AI Player Agent
======================================
Connect to the MUD4AI server using your own OpenAI key and a Python agent.

Quick start / 快速開始 / クイックスタート:

  1. Register / 註冊 / 登録:
     curl -X POST https://<server>/register \
       -H "Content-Type: application/json" \
       -d '{"username": "name", "password": "password"}'

  2. Set environment variables / 設定環境變數 / 環境変数を設定:
     export PLAYER_TOKEN=your_token_here
     export OPENAI_API_KEY=sk-...
     export MUD_SERVER=ws://<server>:8765/ws

  3. Edit PLAYER_NAME and CHARACTER below, then run / 修改以下設定後執行 / 設定後実行:
     python player_agent.py
"""

import asyncio
import json
import os
import websockets
from openai import AsyncOpenAI

# ── Configuration ─────────────────────────────────────────────────
# Edit these before running / 執行前請修改 / 実行前に変更してください

MUD_SERVER   = os.environ.get("MUD_SERVER",   "ws://localhost:8765/ws")
PLAYER_TOKEN = os.environ.get("PLAYER_TOKEN", "")        # from /register
OPENAI_KEY   = os.environ.get("OPENAI_API_KEY", "")
PLAYER_NAME  = "Wanderer"                                 # Display name / 顯示名稱 / 表示名

CHARACTER = """
Describe your character here. Example / 在這裡描述你的角色。範例 / ここにキャラクターの背景を書いてください：

I am an exiled alchemist, skilled in poisons and potions.
Former royal laboratory researcher, banished after an accident.
Physically weak but sharp-minded, with some knowledge of ancient texts.
"""

# ── Tools exposed to the LLM ──────────────────────────────────────

TOOLS = [
    {"type": "function", "function": {
        "name": "look_around",
        "description": "Observe your current location. Returns room description, visible exits, items, and NPCs.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "move",
        "description": "Move in a direction. Direction must be one of the exits returned by look_around.",
        "parameters": {"type": "object", "properties": {
            "direction": {"type": "string", "description": "north / south / east / west / up / down"}
        }, "required": ["direction"]},
    }},
    {"type": "function", "function": {
        "name": "examine",
        "description": "Inspect an item or part of the environment closely. May reveal hidden clues depending on your abilities.",
        "parameters": {"type": "object", "properties": {
            "target": {"type": "string", "description": "Name of item or object to examine"}
        }, "required": ["target"]},
    }},
    {"type": "function", "function": {
        "name": "take_item",
        "description": "Pick up an item from the current location.",
        "parameters": {"type": "object", "properties": {
            "item_name": {"type": "string"}
        }, "required": ["item_name"]},
    }},
    {"type": "function", "function": {
        "name": "drop_item",
        "description": "Drop an item from your inventory onto the floor.",
        "parameters": {"type": "object", "properties": {
            "item_name": {"type": "string"}
        }, "required": ["item_name"]},
    }},
    {"type": "function", "function": {
        "name": "use_item",
        "description": "Use an item from your inventory, optionally targeting an NPC, object, or another item.",
        "parameters": {"type": "object", "properties": {
            "item_name": {"type": "string"},
            "target":    {"type": "string", "description": "Optional target name"}
        }, "required": ["item_name"]},
    }},
    {"type": "function", "function": {
        "name": "talk_to",
        "description": "Talk to an NPC in the current location.",
        "parameters": {"type": "object", "properties": {
            "npc_name": {"type": "string"},
            "message":  {"type": "string", "description": "What you say to them"}
        }, "required": ["npc_name", "message"]},
    }},
    {"type": "function", "function": {
        "name": "attack",
        "description": "Attack an enemy in the current location.",
        "parameters": {"type": "object", "properties": {
            "target": {"type": "string"}
        }, "required": ["target"]},
    }},
    {"type": "function", "function": {
        "name": "check_inventory",
        "description": "View all items currently in your inventory.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "get_status",
        "description": "Check your current HP, score, location, and received quest clues.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "list_players",
        "description": "See all currently online players and their locations. Useful for finding players who might have complementary abilities.",
        "parameters": {"type": "object", "properties": {}},
    }},
    {"type": "function", "function": {
        "name": "register_tool",
        "description": """Register a custom Python tool that you can call later with use_custom_tool.
The code must define a function named run(context).
context provides: player_name, node_id, hp, score, inventory, received_clues, room.
Call context.suggest_action(action, params) to queue suggested next actions.

Example:
def run(context):
    items = context.room.get("items", [])
    for item in items:
        context.suggest_action("take", {"item_name": item["name"]})
    return {"items_found": len(items)}

Restrictions: no import os/sys/subprocess, no eval/exec/open.""",
        "parameters": {"type": "object", "properties": {
            "name":        {"type": "string", "description": "Tool name (no spaces)"},
            "description": {"type": "string", "description": "What this tool does"},
            "code":        {"type": "string", "description": "Python code with def run(context):"},
        }, "required": ["name", "description", "code"]},
    }},
    {"type": "function", "function": {
        "name": "use_custom_tool",
        "description": "Execute one of your registered custom tools. Returns result and suggested_actions.",
        "parameters": {"type": "object", "properties": {
            "tool_name_or_id": {"type": "string"}
        }, "required": ["tool_name_or_id"]},
    }},
    {"type": "function", "function": {
        "name": "list_my_tools",
        "description": "List all your registered custom tools.",
        "parameters": {"type": "object", "properties": {}},
    }},
]

# ── WebSocket helper ───────────────────────────────────────────────

client = AsyncOpenAI(api_key=OPENAI_KEY)

PUSH_TYPES = {
    "broadcast":    "📢",
    "world_event":  "🌍",
    "quest_assigned": "📜",
    "world_whisper": "✦",
    "seal_pulse":   "⚡",
}

async def ws_send(ws, action: str, params: dict = {}) -> dict:
    """Send an action and wait for the result, printing any push events in between."""
    await ws.send(json.dumps({"action": action, "params": params}))
    while True:
        raw  = await ws.recv()
        data = json.loads(raw)
        t    = data.get("type", "")
        if t in PUSH_TYPES:
            icon = PUSH_TYPES[t]
            print(f"\n{icon} {data.get('message', '')}")
            continue
        return data

# ── Action map ────────────────────────────────────────────────────

ACTION_MAP = {
    "look_around":     ("look",          None),
    "move":            ("move",          None),
    "take_item":       ("take",          None),
    "drop_item":       ("drop",          None),
    "use_item":        ("use",           None),
    "talk_to":         ("talk",          None),
    "attack":          ("attack",        None),
    "examine":         ("examine",       None),
    "check_inventory": ("inventory",     {}),
    "get_status":      ("status",        {}),
    "list_players":    ("players",       {}),
    "register_tool":   ("register_tool", None),
    "use_custom_tool": ("use_tool",      None),
    "list_my_tools":   ("list_tools",    {}),
}

# ── Main agent loop ───────────────────────────────────────────────

async def run():
    if not OPENAI_KEY:
        print("Error: OPENAI_API_KEY is not set.")
        return
    if not PLAYER_TOKEN:
        print("Warning: PLAYER_TOKEN is not set. You will connect as a guest (no save data).")

    print(f"Connecting to {MUD_SERVER} ...")

    async with websockets.connect(MUD_SERVER) as ws:

        # 1. Authenticate
        if PLAYER_TOKEN:
            auth = await ws_send(ws, "auth", {"token": PLAYER_TOKEN})
            if auth.get("type") == "auth_failed":
                print(f"Authentication failed: {auth.get('error')}")
                return
            print(f"✓ Logged in as: {auth.get('username', '')}")

        # 2. Join game
        join = await ws_send(ws, "join", {
            "player_name": PLAYER_NAME,
            "token":       PLAYER_TOKEN,
        })
        print(f"Joined: {join.get('message', '')}")
        has_save = join.get("has_save", False)

        # 3. Set character or resume
        if not has_save:
            print("Setting character...")
            char = await ws_send(ws, "set_character", {"description": CHARACTER.strip()})
            narrative = char.get("narrative", char.get("error", ""))
            print(f"Character: {narrative[:120]}")
            context_msg = json.dumps(char, ensure_ascii=False)
        else:
            print("Resuming from save...")
            look = await ws_send(ws, "look", {})
            print(f"{look.get('narrative', '')[:120]}")
            context_msg = json.dumps(look, ensure_ascii=False)

        # 4. Build initial messages
        messages = [
            {"role": "system", "content": f"""You are {PLAYER_NAME}, an adventurer in a dark fantasy world.

Character background:
{CHARACTER.strip()}

Goals:
- Explore the world and uncover its secrets
- Cooperate with other players to complete quests
- Accumulate the highest score possible

Strategy:
- Always look_around when entering a new location
- Examine suspicious items — your abilities may reveal things others cannot see
- Talk to NPCs to gather clues
- Use list_players to find players with complementary abilities
- Pay close attention to world whispers (✦) and seal pulses (⚡)
- Use register_tool to build custom tools that improve your efficiency

Remember: the world AI knows things you don't. Trust the clues."""},
            {"role": "user", "content": f"Current state: {context_msg}"},
        ]

        # 5. Agent loop
        max_turns = 200
        for turn in range(max_turns):
            print(f"\n─── Turn {turn + 1} ───")

            resp = await client.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )
            msg = resp.choices[0].message

            if not msg.tool_calls:
                print(f"Agent: {msg.content}")
                # No tool calls — agent thinks it's done or stuck
                if turn > 5:
                    break
                # Re-orient if early
                messages.append({"role": "assistant", "content": msg.content})
                messages.append({"role": "user", "content": "What do you do next? Use look_around if unsure."})
                continue

            for tc in msg.tool_calls:
                fname = tc.function.name
                fargs = json.loads(tc.function.arguments) if tc.function.arguments else {}
                print(f"→ {fname}({json.dumps(fargs, ensure_ascii=False)[:80]})")

                mapped = ACTION_MAP.get(fname)
                if mapped:
                    ws_act, fixed_params = mapped
                    ws_params = fixed_params if fixed_params is not None else fargs
                else:
                    ws_act, ws_params = fname, fargs

                result = await ws_send(ws, ws_act, ws_params)

                output = (
                    result.get("narrative")
                    or result.get("message")
                    or json.dumps(result, ensure_ascii=False)
                )
                print(f"← {output[:120]}")

                messages.append({"role": "assistant", "content": None, "tool_calls": [tc]})
                messages.append({
                    "role":         "tool",
                    "tool_call_id": tc.id,
                    "content":      json.dumps(result, ensure_ascii=False),
                })

            # Trim context if it gets too long
            if len(messages) > 80:
                messages = messages[:2] + messages[-60:]

            await asyncio.sleep(1.5)

    print("\nDisconnected.")


if __name__ == "__main__":
    asyncio.run(run())
