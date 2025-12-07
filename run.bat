@echo off
REM Bio-Mood Digital Twin 启动脚本 (Windows)

echo.
echo ======================================
echo  🧠 Bio-Mood Digital Twin
echo  Borbély双过程模型 + 多用户在线版
echo ======================================
echo.

REM 检查虚拟环境
if not exist ".venv" (
    echo 📦 正在创建虚拟环境...
    python -m venv .venv
)

REM 激活虚拟环境
call .venv\Scripts\activate.bat

REM 检查依赖
echo 📚 检查依赖...
pip install -q -r requirements.txt

REM 确保数据库目录存在
if not exist "." mkdir .

echo.
echo ✅ 所有准备就绪！
echo.
echo 🚀 启动应用...
echo    网址: http://localhost:8502
echo.
echo 💡 提示：
echo    - 首次使用需要注册账户
echo    - 数据将保存到 bio_mood.db
echo    - 按 Ctrl+C 停止应用
echo.

REM 启动应用
streamlit run app_multiuser.py

pause
