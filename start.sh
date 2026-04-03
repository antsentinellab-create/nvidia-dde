#!/bin/bash
# Design Review Support System 快速啟動腳本

echo "🚀 啟動 Design Review Support System..."
echo ""

# 檢查虛擬環境
if [ ! -d ".venv" ]; then
    echo "❌ 錯誤：找不到 .venv 虛擬環境"
    echo "請先執行：python3 -m venv .venv"
    exit 1
fi

# 啟動虛擬環境
source .venv/bin/activate

# 設定 API 金鑰（若未設定）
if [ -z "$NVIDIA_API_KEY" ]; then
    echo "⚠️  警告：NVIDIA_API_KEY 未設定"
    echo "建議在 .bashrc 或 .zshrc 中設定："
    echo "  export NVIDIA_API_KEY=\"nvapi-YOUR_API_KEY_HERE\""
    echo ""
    read -p "是否繼續？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 啟動 CLI
echo "✅ 啟動 CLI 介面..."
echo ""
python cli.py
