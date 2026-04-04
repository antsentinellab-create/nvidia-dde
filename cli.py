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
from datetime import datetime
from pathlib import Path
import json
import sys
import time
import shutil

# 引入現有引擎
from design_decision_engine import SPEC, AGGREGATOR_MODEL, build_prompt, get_content, parse_json, normalize, is_valid_output, get_client
from openai import OpenAI
from engine.loader import load_roles, save_role, load_risk_templates, save_risk_template
from db.repository import save_review, get_recent_reviews

console = Console()

# 色彩配置（暖感工業風格）
STYLE_PRIMARY = "#F39C12"      # 琥珀橙
STYLE_BG = "#1A1A1B"           # 深炭黑
STYLE_SECONDARY = "#D35400"    # 深橙



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
            save_review(project_name, result)
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
    total = len(load_roles())
    
    # Phase 1: 各專家分工審查
    for i, role in enumerate(load_roles(), 1):
        console.print(f"[{i}/{total}] {role['name']} ({role['id'].split('/')[-1]})")
        
        success = False
        last_error = None
        
        # 重試機制：最多重試 2 次，間隔 5 秒
        for attempt in range(3):  # 1 次原始嘗試 + 2 次重試
            try:
                if attempt > 0:
                    console.print(f"  [yellow]重試 {attempt}/2...[/yellow]")
                    time.sleep(5)  # 間隔 5 秒
                
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
                    success = True
                else:
                    console.print(f"  [yellow]⚠[/yellow] {role['name']} JSON 解析失敗")
                    last_error = err
                    
                break  # 成功執行（無論 JSON 是否解析成功）
                    
            except Exception as e:
                last_error = str(e)
                if attempt < 2:  # 還沒到最後一次重試
                    continue  # 繼續重試
                else:  # 最終於失敗
                    console.print(f"  [red]✗[/red] {role['name']} 錯誤：{e}")
                    results[role["name"]] = {"data": None, "error": str(e)}
                    success = False
        
        if not success and last_error:
            # 重試後仍失敗，記錄錯誤
            if role["name"] not in results:
                results[role["name"]] = {"data": None, "error": last_error}
    
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


def view_history():
    """查看歷史記錄"""
    console.print(Panel("📊 歷史記錄查詢", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    rows = get_recent_reviews(10)
    
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
    while True:
        console.print(Panel("📚 知識庫管理", style="bold white on #1A1A1B", border_style="#F39C12"))
        
        choice = questionary.select(
            "請選擇功能：",
            choices=[
                questionary.Choice("[3-1] 📄 檢視所有角色設定", value="1"),
                questionary.Choice("[3-2] ✏️  編輯角色 Prompt", value="2"),
                questionary.Choice("[3-3] 📥 匯入公司設計規範", value="3"),
                questionary.Choice("[3-4] ⚠️  檢視風險模板", value="4"),
                questionary.Choice("[3-5] ➕ 新增風險模板", value="5"),
                questionary.Choice("[B] 🔙 返回主選單", value="b"),
            ],
            style=[("selected", "#F39C12 bold")]
        ).ask()
        
        if choice == "1":
            # [3-1] 檢視所有角色設定
            view_all_roles()
        elif choice == "2":
            # [3-2] 編輯角色 Prompt
            edit_role_prompt()
        elif choice == "3":
            # [3-3] 匯入公司設計規範
            import_design_standard()
        elif choice == "4":
            # [3-4] 檢視風險模板
            view_risk_templates()
        elif choice == "5":
            # [3-5] 新增風險模板
            add_new_risk_template()
        elif choice and choice.lower() == "b":
            break


def view_all_roles():
    """檢視所有角色設定"""
    console.print(Panel("📄 檢視所有角色設定", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    roles = load_roles()
    for i, role in enumerate(roles, 1):
        console.print(f"\n[bold #F39C12]【{i}. {role['name']}】[/bold #F39C12]")
        console.print(f"  ID: {role['id']}")
        console.print(f"  System Prompt:")
        console.print(f"    [dim]{role['system'][:200]}{'...' if len(role['system']) > 200 else ''}[/dim]")
        console.print(f"  主責欄位：{role.get('focus_desc', 'N/A')}")
    
    console.print(f"\n[yellow]共 {len(roles)} 個角色[/yellow]")


def edit_role_prompt():
    """編輯角色 Prompt"""
    console.print(Panel("✏️  編輯角色 Prompt", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    roles = load_roles()
    role_names = [f"{i}. {role['name']} ({role['id'].split('/')[-1]})" for i, role in enumerate(roles, 1)]
    
    choice = questionary.select(
        "選擇要編輯的角色：",
        choices=role_names + ["🔙 返回上層"],
        style=[("selected", "#F39C12 bold")]
    ).ask()
    
    if not choice or choice == "🔙 返回上層":
        return
    
    # 解析選擇的角色索引
    idx = int(choice.split(".")[0].strip()) - 1
    role = roles[idx]
    
    # 顯示當前 prompt
    console.print(f"\n[bold #F39C12]當前 System Prompt:[/bold #F39C12]")
    console.print(f"{role['system']}")
    
    # 詢問是否備份
    if questionary.confirm("是否先備份原檔案？（推薦）").ask():
        kb_path = Path(__file__).parent / "knowledge" / "roles"
        role_filename_map = {
            "Risk-Analyst": "risk_analyst",
            "Completeness-Reviewer": "completeness_reviewer",
            "Improvement-Advisor": "improvement_advisor",
        }
        base_name = role_filename_map.get(role["name"], role["id"].split("/")[-1])
        backup_file = f"{base_name}.json.bak"
        src = kb_path / f"{base_name}.json"
        dst = kb_path / backup_file
        if src.exists():
            shutil.copy2(src, dst)
            console.print(f"[green]✅ 已備份至 {backup_file}[/green]")
    
    # 輸入新的 prompt
    new_system = questionary.text(
        "請輸入新的 System Prompt：",
        default=role['system']
    ).ask()
    
    if not new_system:
        console.print("[red]❌ Prompt 不能為空[/red]")
        return
    
    # 確認修改
    if not questionary.confirm(f"確定要修改 {role['name']} 的 Prompt 嗎？").ask():
        return
    
    # 更新角色資料
    role['system'] = new_system
    role_filename_map = {
        "Risk-Analyst": "risk_analyst",
        "Completeness-Reviewer": "completeness_reviewer",
        "Improvement-Advisor": "improvement_advisor",
    }
    base_name = role_filename_map.get(role["name"], role["id"].split("/")[-1])
    filename = f"{base_name}.json"

    try:
        save_role(filename, role)
        console.print(f"[green]✅ 成功更新 {role['name']} 的 Prompt[/green]")
    except Exception as e:
        console.print(f"[red]❌ 更新失敗：{e}[/red]")


def import_design_standard():
    """匯入公司設計規範"""
    console.print(Panel("📥 匯入公司設計規範", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    # 選擇檔案類型
    file_type = questionary.select(
        "選擇檔案類型：",
        choices=[
            questionary.Choice("*.md (Markdown)", value=".md"),
            questionary.Choice("*.txt (純文字)", value=".txt"),
        ],
        style=[("selected", "#F39C12 bold")]
    ).ask()
    
    # 輸入檔案路徑
    file_path_str = questionary.text(
        "請輸入檔案絕對路徑或相對路徑："
    ).ask()
    
    if not file_path_str:
        console.print("[red]❌ 未輸入檔案路徑[/red]")
        return
    
    # 驗證檔案
    src_path = Path(file_path_str)
    if not src_path.exists():
        console.print(f"[red]❌ 找不到檔案：{src_path}[/red]")
        return
    
    if not src_path.name.endswith(file_type):
        console.print(f"[red]❌ 檔案類型不符，需要 {file_type}[/red]")
        return
    
    # 檢查大小
    file_size = src_path.stat().st_size
    if file_size > 1 * 1024 * 1024:  # 1MB
        console.print(f"[red]❌ 檔案過大（{file_size / 1024 / 1024:.2f}MB），上限 1MB[/red]")
        return
    
    # 複製到 standards 目錄
    standards_dir = Path(__file__).parent / "knowledge" / "standards"
    standards_dir.mkdir(parents=True, exist_ok=True)
    
    dst_path = standards_dir / src_path.name
    
    # 檢查是否已存在
    if dst_path.exists():
        if not questionary.confirm(f"⚠️  目標檔案已存在，是否覆蓋？ {dst_path.name}").ask():
            return
    
    try:
        shutil.copy2(src_path, dst_path)
        console.print(f"[green]✅ 成功匯入 {src_path.name} 至 knowledge/standards/[/green]")
        console.print(f"   大小：{file_size / 1024:.2f} KB")
    except Exception as e:
        console.print(f"[red]❌ 匯入失敗：{e}[/red]")


def view_risk_templates():
    """檢視風險模板"""
    console.print(Panel("⚠️  檢視風險模板", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    templates = load_risk_templates()
    
    if not templates:
        console.print("[yellow]⚠️  尚無風險模板[/yellow]")
        return
    
    for i, tpl in enumerate(templates, 1):
        data = tpl['data']
        console.print(f"\n[bold #F39C12]【{i}. {tpl['filename']}】[/bold #F39C12]")
        console.print(f"  Level: {data.get('level', 'N/A')}")
        console.print(f"  Issue: {data.get('issue', 'N/A')[:100]}{'...' if len(str(data.get('issue', ''))) > 100 else ''}")
        console.print(f"  Suggestion: {data.get('suggestion', 'N/A')[:100]}{'...' if len(str(data.get('suggestion', ''))) > 100 else ''}")
    
    console.print(f"\n[yellow]共 {len(templates)} 個風險模板[/yellow]")


def add_new_risk_template():
    """新增風險模板"""
    console.print(Panel("➕ 新增風險模板", style="bold white on #1A1A1B", border_style="#F39C12"))
    
    # 互動式填寫
    level = questionary.select(
        "風險等級：",
        choices=[
            questionary.Choice("🔴 High (高風險)", value="high"),
            questionary.Choice("🟡 Medium (中風險)", value="medium"),
            questionary.Choice("🟢 Low (低風險)", value="low"),
        ],
        style=[("selected", "#F39C12 bold")]
    ).ask()
    
    issue = questionary.text(
        "問題描述：",
        multiline=True
    ).ask()
    
    if not issue:
        console.print("[red]❌ 問題描述不能為空[/red]")
        return
    
    suggestion = questionary.text(
        "具體建議：",
        multiline=True
    ).ask()
    
    if not suggestion:
        console.print("[red]❌ 建議不能為空[/red]")
        return
    
    # 模板名稱
    template_name = questionary.text(
        "請輸入模板名稱（英文，不含副檔名）：",
        pattern=r'^[a-zA-Z0-9_-]+$'
    ).ask()
    
    if not template_name:
        console.print("[red]❌ 模板名稱不能為空[/red]")
        return
    
    # 建立資料
    template_data = {
        "level": level,
        "issue": issue,
        "suggestion": suggestion
    }
    
    try:
        saved_path = save_risk_template(template_name, template_data)
        console.print(f"[green]✅ 成功儲存風險模板：{saved_path.name}[/green]")
    except Exception as e:
        console.print(f"[red]❌ 儲存失敗：{e}[/red]")


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
