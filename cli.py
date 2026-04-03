import os
#!/usr/bin/env python3
"""
Design Review Support System - 互動式 CLI

選單：
  [1] 新增審查
  [2] 查歷史記錄
  [3] 管理知識庫
  [Q] 退出
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
import questionary
import sqlite3
from datetime import datetime
from pathlib import Path
import json
import sys

# 引入現有引擎
from design_decision_engine import SPEC, ROLES, AGGREGATOR_MODEL, build_prompt, get_content, parse_json, normalize, is_valid_output, get_client
from openai import OpenAI
from engine.loader import load_roles

console = Console()

# 色彩配置（暖感工業風格）
STYLE_PRIMARY = "#F39C12"      # 琥珀橙
STYLE_BG = "#1A1A1B"           # 深炭黑
STYLE_SECONDARY = "#D35400"    # 深橙

DB_PATH = Path(__file__).parent / "db" / "history.db"


def show_main_menu():
    """顯示主選單"""
    console.print(Panel.fit(
        "[bold white]Design Review Support System[/bold white]\n"
        "[#F39C12]暖感工業風格 | 琥珀橙主題[/#F39C12]",
        style="bold white on #1A1A1B",
        border_style="#F39C12"
    ))
    
    choice = questionary.select(
        "請選擇功能：",
        choices=[
            questionary.Choice("[1] 🔍 新增審查", value="1"),
            questionary.Choice("[2] 📊 查歷史記錄", value="2"),
            questionary.Choice("[3] 📚 管理知識庫", value="3"),
            questionary.Choice("[Q] 🚪 退出系統", value="q"),
        ],
        style=[("selected", "#F39C12 bold")]
    ).ask()
    
    return choice


def add_new_review():
    """新增審查"""
    console.print(Panel("🔍 新增設計審查", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    # 詢問專案名稱
    project_name = questionary.text("請輸入專案名稱：").ask()
    
    if not project_name:
        console.print("[red]❌ 專案名稱不能為空[/red]")
        return
    
    # 確認執行
    if not questionary.confirm(f"確定要執行审查嗎？專案：{project_name}").ask():
        return
    
    # 執行審查
    console.print("\n[yellow]正在執行多專家審查...[/yellow]")
    console.print("這可能需要 2-8 分鐘，請耐心等待。\n")
    
    try:
        # 執行審查流程
        result = run_design_review(SPEC)
        
        if result:
            # 儲存至資料庫
            save_review_to_db(project_name, result)
            console.print(f"[green]✅ 審查完成！結果已儲存至資料庫。[/green]")
            
            # 顯示摘要
            risks = result.get("risks", [])
            risk_high = sum(1 for r in risks if r.get("level") == "high")
            console.print(f"\n[bold #F39C12]風險統計:[/bold #F39C12]")
            console.print(f"  高風險：{risk_high}")
            console.print(f"  總數：{len(risks)}")
        else:
            console.print("[red]❌ 審查失敗，未獲得有效結果[/red]")
            
    except Exception as e:
        console.print(f"[red]❌ 執行審查時發生錯誤：{e}[/red]")


def run_design_review(spec: str) -> dict:
    """
    執行設計審查並回傳結果
    
    Args:
        spec: 設計規格字串
        
    Returns:
        dict: Aggregator 輸出的完整 JSON
    """
    from openai import OpenAI
    

    
    results = {}
    total = len(ROLES)
    
    # Phase 1: 各專家分工審查
    for i, role in enumerate(load_roles(), 1):
        console.print(f"[{i}/{total}] {role['name']} ({role['id'].split('/')[-1]})")
        
        try:
            response = get_client().chat.completions.create(
                model=role["id"],
                messages=[
                    {"role": "system", "content": role["system"]},
                    {"role": "user", "content": build_prompt(role)}
                ],
                temperature=0.3,
                max_tokens=2048
            )
            raw = get_content(response)
            data, err = parse_json(raw)
            
            results[role["name"]] = {
                "data": data, "raw": raw,
                "error": err
            }
            
            if data:
                console.print(f"  [green]✓[/green] {role['name']} 完成")
            else:
                console.print(f"  [yellow]⚠[/yellow] {role['name']} JSON 解析失敗")
                
        except Exception as e:
            console.print(f"  [red]✗[/red] {role['name']} 錯誤：{e}")
            results[role["name"]] = {"data": None, "error": str(e)}
    
    # Phase 2: 合併各專家結果
    merged = {
        "risks": [],
        "missing": [],
        "improvements": [],
        "good_points": [],
        "expert_verdicts": {}
    }
    for name, r in results.items():
        d = normalize(r["data"])
        merged["risks"].extend(d["risks"])
        merged["missing"].extend(d["missing"])
        merged["improvements"].extend(d["improvements"])
        merged["good_points"].extend(d["good_points"])
        if d["verdict"]:
            merged["expert_verdicts"][name] = d["verdict"]
    
    # Phase 3: Aggregator 最終裁決
    console.print(f"\n🏛️  Aggregator ({AGGREGATOR_MODEL.split('/')[-1]}) 最終裁決")
    
    agg_prompt = f"""你是最終裁決者。以下是三位專家的分工審查結果：

{json.dumps(merged, ensure_ascii=False, indent=2)}

任務：
1. 合併語意相同的項目（即使措辭不同）
2. 刪除低價值或重複建議
3. 對 risks / missing / improvements 排「優先順序」（最重要在前）
4. 若專家意見衝突，請選擇你認為正確的，並在 verdict 說明原因

限制：
- 最多保留每類 5 條
- 必須做取捨，不可全部保留

輸出格式（只輸出 JSON）：
{{
  "risks": [{{
    "level": "high/medium/low",
    "issue": "問題描述",
    "suggestion": "具體建議"
  }}],
  "missing": [{{
    "item": "缺少的設計",
    "reason": "為什麼需要",
    "how": "如何補充"
  }}],
  "improvements": [{{
    "area": "改善領域",
    "current": "現況",
    "better": "更好的做法"
  }}],
  "good_points": ["值得保留的設計決策"],
  "verdict": "整體評估（含衝突裁決說明）"
}}"""
    
    try:
        agg_response = get_client().chat.completions.create(
            model=AGGREGATOR_MODEL,
            messages=[
                {"role": "system", "content": "你是資深首席架構師，負責整合各專家意見並做最終裁決。只輸出 JSON，不要任何說明文字。"},
                {"role": "user", "content": agg_prompt}
            ],
            temperature=0.2,
            max_tokens=4096
        )
        agg_raw = get_content(agg_response)
        agg_data, agg_err = parse_json(agg_raw)
        
        if agg_data and is_valid_output(agg_data):
            console.print(f"  [green]✓[/green] Aggregator 裁決完成")
            return agg_data
        else:
            console.print(f"  [yellow]⚠[/yellow] Aggregator 未通過 sanity check，使用合併結果")
            return merged
            
    except Exception as e:
        console.print(f"  [red]✗[/red] Aggregator 錯誤：{e}")
        return merged


def save_review_to_db(project_name: str, result_json: dict):
    """
    將審查結果儲存至資料庫
    
    Args:
        project_name: 專案名稱
        result_json: Aggregator 輸出的完整 JSON
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 統計各等級風險數量
    risks = result_json.get("risks", [])
    risk_high = sum(1 for r in risks if r.get("level") == "high")
    risk_medium = sum(1 for r in risks if r.get("level") == "medium")
    risk_low = sum(1 for r in risks if r.get("level") == "low")
    
    # 裁決摘要
    verdict = result_json.get("verdict", "")[:500]
    
    # 插入資料庫
    cursor.execute("""
        INSERT INTO reviews (project, reviewed_at, risk_high, risk_medium, risk_low, verdict, result_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        project_name,
        datetime.utcnow().isoformat(),
        risk_high,
        risk_medium,
        risk_low,
        verdict,
        json.dumps(result_json, ensure_ascii=False)
    ))
    
    conn.commit()
    conn.close()


def view_history():
    """查看歷史記錄"""
    console.print(Panel("📊 歷史記錄查詢", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    if not DB_PATH.exists():
        console.print("[red]❌ 資料庫尚未初始化。請先執行 'python db/init_db.py'[/red]")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 查詢最近 10 筆記錄
    cursor.execute("""
        SELECT id, project, reviewed_at, risk_high, risk_medium, risk_low, verdict
        FROM reviews
        ORDER BY reviewed_at DESC
        LIMIT 10
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        console.print("[yellow]⚠️  尚無歷史記錄[/yellow]")
        return
    
    # 建立表格
    table = Table(title="最近 10 筆審查記錄", style="#F39C12")
    table.add_column("ID", style="dim", justify="right")
    table.add_column("專案名稱", style="bold")
    table.add_column("審查時間", justify="center")
    table.add_column("高風險", justify="center", style="red")
    table.add_column("中風險", justify="center", style="yellow")
    table.add_column("低風險", justify="center", style="green")
    table.add_column("裁決摘要", overflow="ellipsis")
    
    for row in rows:
        table.add_row(
            str(row[0]),
            row[1],
            row[2][:19],
            str(row[3]),
            str(row[4]),
            str(row[5]),
            row[6][:50] + "..." if len(row[6]) > 50 else row[6]
        )
    
    console.print(table)


def manage_knowledge_base():
    """管理知識庫"""
    console.print(Panel("📚 知識庫管理", style="bold white on #1A1A1B", border_style="#F39C12"))
    # TODO: Phase B 實現知識庫管理功能
    console.print("[yellow]⚠️  此功能將於 Phase B 實現[/yellow]")
    console.print("\n未來將支援：")
    console.print("  - 📄 檢視角色設定")
    console.print("  - 📝 編輯公司規範模板")
    console.print("  - 📥 匯入/匯出風險模板")
    console.print("\n目前知識庫位置：")
    console.print(f"  [cyan]{Path(__file__).parent / 'knowledge'}[/cyan]")


def main():
    """CLI 主迴圈"""
    while True:
        choice = show_main_menu()
        
        if choice == "1":
            add_new_review()
        elif choice == "2":
            view_history()
        elif choice == "3":
            manage_knowledge_base()
        elif choice and choice.lower() == "q":
            console.print(Panel("[green]👋 感謝使用，再見！[/green]", 
                              style="bold white on #1A1A1B", 
                              border_style="#F39C12"))
            break


if __name__ == '__main__':
    main()
