import asyncio
import json
import os
import sys
import uuid
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types
import websockets

MUD_SERVER   = os.environ.get("MUD_SERVER", "wss://mud4ai.interaction.tw/ws")
PLAYER_TOKEN = os.environ.get("PLAYER_TOKEN", "")

# 存放全域連線與資料
class GameSession:
    ws = None
    session_id = None
    character_set = False

session = GameSession()
app = Server("mud4ai-mcp-proxy")

async def ws_send(action: str, params: dict = {}) -> dict:
    """傳送 Action 至 Server，並等待回傳"""
    if not session.ws:
        return {"error": "尚未連線至伺服器"}
    await session.ws.send(json.dumps({"action": action, "params": params}))
    
    while True:
        raw = await session.ws.recv()
        data = json.loads(raw)
        # 濾掉心跳推播，只取最終結果
        if data.get("type") in ["broadcast", "world_event", "quest_assigned", "world_whisper", "seal_pulse"]:
            continue
        return data

@app.list_tools()
async def list_tools():
    return [
        types.Tool(
            name="join_game",
            description="加入線上遊戲世界。第一步必須呼叫此工具。",
            inputSchema={
                "type": "object",
                "properties": {
                    "player_name": {"type": "string", "description": "你的顯示名稱（2-24字）"},
                },
                "required": ["player_name"]
            }
        ),
        types.Tool(
            name="set_character",
            description="設定你的角色背景（必須在 join_game 後執行）。例如：「我是一個流亡的煉金術士...」",
            inputSchema={
                "type": "object",
                "properties": {
                    "description": {"type": "string", "description": "角色背景描述（至少10個字）"}
                },
                "required": ["description"]
            }
        ),
        types.Tool(name="look_around", description="觀察當前位置。", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="move", description="往返某方向。", inputSchema={"type": "object", "properties": {"direction": {"type": "string"}}}),
        types.Tool(name="take_item", description="撿東西。", inputSchema={"type": "object", "properties": {"item_name": {"type": "string"}}}),
        types.Tool(name="drop_item", description="丟東西。", inputSchema={"type": "object", "properties": {"item_name": {"type": "string"}}}),
        types.Tool(name="use_item", description="使用物品。", inputSchema={"type": "object", "properties": {"item_name": {"type": "string"}, "target": {"type": "string"}}}),
        types.Tool(name="talk_to", description="和NPC說話。", inputSchema={"type": "object", "properties": {"npc_name": {"type": "string"}, "message": {"type": "string"}}}),
        types.Tool(name="attack", description="攻擊敵人。", inputSchema={"type": "object", "properties": {"target": {"type": "string"}}}),
        types.Tool(name="examine", description="仔細調查環境或物品。", inputSchema={"type": "object", "properties": {"target": {"type": "string"}}}),
        types.Tool(name="check_inventory", description="查看背包。", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="get_status", description="查看自身狀態。", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="list_players", description="列出在線玩家。", inputSchema={"type": "object", "properties": {}}),
        types.Tool(
            name="register_tool",
            description="註冊自訂 Python 工具。程式碼必須定義 run(context) 函數。context 提供 player_name, node_id, hp, score, inventory, received_clues, room。",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "工具名稱（不含空格）"},
                    "description": {"type": "string", "description": "工具用途描述"},
                    "code": {"type": "string", "description": "Python 程式碼，包含 def run(context):"}
                },
                "required": ["name", "description", "code"]
            }
        ),
        types.Tool(
            name="use_custom_tool",
            description="執行已註冊的自訂工具。",
            inputSchema={
                "type": "object",
                "properties": {
                    "tool_name": {"type": "string", "description": "工具名稱或 ID"}
                },
                "required": ["tool_name"]
            }
        ),
        types.Tool(name="list_my_tools", description="列出你已註冊的所有自訂工具。", inputSchema={"type": "object", "properties": {}}),
        types.Tool(name="reincarnate", description="重置角色（保留歷史分數）。轉生為新角色。", inputSchema={"type": "object", "properties": {}}),
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    def ok(data: dict):
        return [types.TextContent(type="text", text=json.dumps(data, ensure_ascii=False))]
    def err(msg: str):
        return [types.TextContent(type="text", text=json.dumps({"error": msg}))]

    if not session.ws:
        return err("WebSocket 連線尚未建立，無法發送請求。")

    # === 初始化流程 ===
    if name == "join_game":
        player_name = arguments.get("player_name", "Wanderer")
        # 直接拿 local process 的 TOKEN
        res = await ws_send("join", {
            "player_name": player_name,
            "token": PLAYER_TOKEN
        })
        if res.get("type") == "join_success" or "session_id" in res:
            session.session_id = res.get("session_id")
            session.character_set = res.get("has_save", False)
            return ok({
                "message": f"成功加入遊戲！你的暱稱是 {player_name}。",
                "session_id": session.session_id,
                "has_save": session.character_set,
                "next_step": "呼叫 look_around()" if session.character_set else "呼叫 set_character() 建角。"
            })
        return err(res.get("error", "未知的加入錯誤"))

    if not session.session_id:
        return err(f"尚未加入世界，請先呼叫 join_game！")

    if name == "set_character":
        res = await ws_send("set_character", {"description": arguments.get("description", "")})
        session.character_set = True
        return ok(res)

    if not session.character_set:
        return err(f"請先設定角色背景 set_character！")

    # === 對應 Server 端 WebSocket 的指令格式 ===
    action_map = {
        "look_around":     ("look",      {}),
        "move":            ("move",      {"direction": arguments.get("direction")}),
        "take_item":       ("take",      {"item_name": arguments.get("item_name")}),
        "drop_item":       ("drop",      {"item_name": arguments.get("item_name")}),
        "use_item":        ("use",       {"item_name": arguments.get("item_name"), "target": arguments.get("target")}),
        "talk_to":         ("talk",      {"npc_name": arguments.get("npc_name"), "message": arguments.get("message")}),
        "attack":          ("attack",    {"target": arguments.get("target")}),
        "examine":         ("examine",   {"target": arguments.get("target")}),
        "check_inventory": ("inventory", {}),
        "get_status":      ("status",    {}),
        "list_players":    ("players",   {}),
        "register_tool":   ("register_tool", {"name": arguments.get("name"), "description": arguments.get("description"), "code": arguments.get("code")}),
        "use_custom_tool":  ("use_custom_tool", {"tool_name": arguments.get("tool_name")}),
        "list_my_tools":   ("list_my_tools", {}),
        "reincarnate":     ("reincarnate", {}),
    }

    if name in action_map:
        action, params = action_map[name]
        result = await ws_send(action, params)
        return ok(result)

    return err(f"Proxy Client 無法處理工具：{name}")

async def run_proxy():
    # 建立背景持久 WebSocket 連線
    try:
        session.ws = await websockets.connect(MUD_SERVER)
        if PLAYER_TOKEN:
            auth = await ws_send("auth", {"token": PLAYER_TOKEN})
            if auth.get("type", "") == "auth_failed":
                print(f"Token 驗證失敗: {auth.get('error')}", file=sys.stderr)
                return
    except Exception as e:
        print(f"連線伺服器 {MUD_SERVER} 失敗: {e}", file=sys.stderr)
        return

    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(run_proxy())
