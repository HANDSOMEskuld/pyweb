#!/bin/bash

# Bio-Mood Digital Twin 启动脚本 (Linux/macOS)

echo ""
echo "======================================"
echo "  🧠 Bio-Mood Digital Twin"
echo "  Borbély双过程模型 + 多用户在线版"
echo "======================================"
echo ""

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 正在创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
source .venv/bin/activate

# 检查依赖
echo "📚 检查依赖..."
pip install -q -r requirements.txt

# 确保数据库目录存在
mkdir -p .

echo ""
echo "✅ 所有准备就绪！"
echo ""
echo "🚀 启动应用..."
echo "   网址: http://localhost:8502"
echo ""
echo "💡 提示："
echo "   - 首次使用需要注册账户"
echo "   - 数据将保存到 bio_mood.db"
echo "   - 按 Ctrl+C 停止应用"
echo ""

# 启动应用
streamlit run app_multiuser.py
