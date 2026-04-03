#!/bin/bash
# DSS Phase C 快速啟動腳本

echo "============================================================"
echo "🚀 DSS Phase C 快速啟動"
echo "============================================================"
echo ""

# 1. 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "❌ 錯誤：找不到 .venv 虛擬環境"
    echo "請先執行：python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
    exit 1
fi

echo "✓ 虛擬環境存在"

# 2. 激活虛擬環境
source .venv/bin/activate
echo "✓ 已激活虛擬環境"

# 3. 檢查環境變數
if [ ! -f ".env" ]; then
    echo "⚠️  警告：找不到 .env 文件，將使用預設設定"
    echo "建議複製 .env.example 並修改："
    echo "  cp .env.example .env"
    echo ""
fi

# 4. 初始化資料庫（如果需要）
echo "正在初始化資料庫..."
python -c "from db.models import init_db; init_db()" 2>/dev/null
echo "✓ 資料庫就緒"

# 5. 啟動 Web UI
echo ""
echo "============================================================"
echo "🌐 啟動 Web UI"
echo "============================================================"
echo "訪問地址：http://localhost:8000"
echo "按 Ctrl+C 停止服務"
echo "============================================================"
echo ""

python web/main.py
