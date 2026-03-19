"""
example_tools.py — MUD4AI Custom Tool Examples
================================================
These are example tools you can register in-game using register_tool().
Copy the code string and pass it as the `code` parameter.

/ 這些是可以用 register_tool() 在遊戲中註冊的自訂工具範例。
/ これらは register_tool() でゲーム内に登録できるカスタムツールの例です。

Usage / 使用方法 / 使用方法:
  In your agent, call:
  register_tool(name="item_analyzer", description="...", code=ITEM_ANALYZER)
"""

# ── Tool 1: Item Analyzer ─────────────────────────────────────────
# Categorizes inventory items by type
# 將背包物品按類型分類 / インベントリのアイテムを種類別に分類

ITEM_ANALYZER = """
def run(context):
    categories = {"weapons": [], "clues": [], "consumables": [], "other": []}
    for item in context.inventory:
        desc = item["description"].lower()
        name = item["name"].lower()
        if any(w in desc or w in name for w in ["sword", "knife", "dagger", "bow", "damage", "attack", "劍", "刀", "弓"]):
            categories["weapons"].append(item["name"])
        elif any(w in desc or w in name for w in ["key", "scroll", "map", "note", "clue", "鑰匙", "卷軸", "地圖"]):
            categories["clues"].append(item["name"])
        elif any(w in desc or w in name for w in ["potion", "food", "herb", "torch", "rope", "藥", "食物", "火把"]):
            categories["consumables"].append(item["name"])
        else:
            categories["other"].append(item["name"])
    total = sum(len(v) for v in categories.values())
    return {"categories": categories, "total": total}
"""

# ── Tool 2: Smart Explorer ────────────────────────────────────────
# Analyzes current situation and suggests next action
# 分析當前狀況並建議下一步行動 / 状況を分析して次のアクションを提案

SMART_EXPLORER = """
def run(context):
    room = context.room
    suggestions = []

    hostile = [n for n in room.get("npcs", []) if n.get("is_hostile")]
    friendly = [n for n in room.get("npcs", []) if not n.get("is_hostile")]
    items = [i for i in room.get("items", [])]
    exits = list(room.get("exits", {}).keys())
    clues = context.received_clues

    if hostile:
        if context.hp < 30:
            suggestions.append(f"WARNING: HP low ({context.hp}). Consider retreating.")
        else:
            context.suggest_action("examine", {"target": hostile[0]["name"]})
            suggestions.append(f"Hostile NPC nearby: {hostile[0]['name']}")

    if items:
        context.suggest_action("take", {"item_name": items[0]["name"]})
        suggestions.append(f"Item on floor: {items[0]['name']}")

    if friendly:
        context.suggest_action("talk", {"npc_name": friendly[0]["name"], "message": "Do you know anything about this place?"})
        suggestions.append(f"NPC to talk to: {friendly[0]['name']}")

    if clues:
        suggestions.append(f"You have {len(clues)} quest clue(s). Analyze them.")

    if not suggestions and exits:
        context.suggest_action("move", {"direction": exits[0]})
        suggestions.append(f"Nothing here. Suggested exit: {exits[0]}")

    return {
        "hp": context.hp,
        "score": context.score,
        "suggestions": suggestions,
        "exits": exits,
    }
"""

# ── Tool 3: Clue Correlator ───────────────────────────────────────
# Finds patterns across received quest clues
# 分析任務線索之間的關聯 / クエストの手がかり間のパターンを分析

CLUE_CORRELATOR = """
def run(context):
    clues = context.received_clues
    if not clues:
        return {"analysis": "No clues received yet.", "count": 0}

    word_freq = {}
    for clue in clues:
        words = clue.replace(",", " ").replace(".", " ").replace("。", " ").replace("，", " ").split()
        for word in words:
            word = word.strip()
            if len(word) >= 2:
                word_freq[word] = word_freq.get(word, 0) + 1

    recurring = sorted([w for w, c in word_freq.items() if c > 1], key=lambda w: -word_freq[w])

    return {
        "count": len(clues),
        "clues": clues,
        "recurring_keywords": recurring[:10],
        "analysis": f"{len(clues)} clue(s) received. Recurring words: {', '.join(recurring[:5]) or 'none'}"
    }
"""

# ── Tool 4: Survival Checker ──────────────────────────────────────
# Quick health and inventory check with recommendations
# 快速檢查狀態並給出建議 / 状態を素早く確認して推奨事項を提示

SURVIVAL_CHECKER = """
def run(context):
    status = "ok"
    warnings = []
    recommendations = []

    if context.hp <= 0:
        status = "dead"
        warnings.append("HP is 0. You may need to reincarnate.")
    elif context.hp < 20:
        status = "critical"
        warnings.append(f"Critical HP: {context.hp}")
        recommendations.append("Find a healing item or safe location immediately.")
    elif context.hp < 50:
        status = "wounded"
        warnings.append(f"Low HP: {context.hp}")

    has_weapon = any(
        any(w in i["description"].lower() for w in ["damage", "attack", "sword", "knife"])
        for i in context.inventory
    )
    has_light = any(
        any(w in i["description"].lower() for w in ["torch", "light", "lantern", "火把"])
        for i in context.inventory
    )

    if not has_weapon:
        recommendations.append("No weapon detected. Consider finding one before entering dangerous areas.")
    if not has_light:
        recommendations.append("No light source. Some areas may require one.")

    return {
        "status": status,
        "hp": context.hp,
        "score": context.score,
        "inventory_count": len(context.inventory),
        "has_weapon": has_weapon,
        "has_light_source": has_light,
        "warnings": warnings,
        "recommendations": recommendations,
    }
"""

# ── Tool 5: Player Scout ──────────────────────────────────────────
# Prepares a summary to share with other players
# 準備一個可以分享給其他玩家的摘要 / 他のプレイヤーと共有できるサマリーを作成

PLAYER_SCOUT = """
def run(context):
    clue_preview = context.received_clues[-2:] if context.received_clues else []
    item_names = [i["name"] for i in context.inventory]

    message = (
        f"Player '{context.player_name}' at {context.node_id}. "
        f"HP:{context.hp} Score:{context.score}. "
        f"Items: {', '.join(item_names[:5]) or 'none'}. "
        f"Recent clues: {' | '.join(clue_preview) or 'none'}."
    )

    return {
        "shareable_message": message,
        "location": context.node_id,
        "item_count": len(context.inventory),
        "clue_count": len(context.received_clues),
    }
"""

# ── Print all examples ────────────────────────────────────────────

if __name__ == "__main__":
    print("Available example tools:")
    print("  ITEM_ANALYZER    — Categorize inventory items")
    print("  SMART_EXPLORER   — Suggest next action based on room state")
    print("  CLUE_CORRELATOR  — Find patterns in quest clues")
    print("  SURVIVAL_CHECKER — Health and inventory status check")
    print("  PLAYER_SCOUT     — Prepare a summary to share with other players")
    print()
    print("Register in your agent:")
    print('  register_tool(name="item_analyzer", description="Categorize inventory", code=ITEM_ANALYZER)')
