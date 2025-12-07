# 🚀 Bio-Mood Digital Twin 部署指南

## 📋 目录

1. [快速开始](#快速开始)
2. [本地部署](#本地部署)
3. [云端部署](#云端部署)
4. [功能说明](#功能说明)
5. [故障排除](#故障排除)

---

## 快速开始

### 环境要求
- Python 3.8+
- pip 包管理工具
- （可选）MySQL 数据库

### 1️⃣ 安装依赖

```bash
# 在项目目录下运行
pip install -r requirements.txt
```

### 2️⃣ 启动应用（本地）

```bash
# 运行多用户版本（推荐）
streamlit run app_multiuser.py

# 或运行原始单用户版本
streamlit run app.py
```

应用将在 `http://localhost:8502` 启动

---

## 本地部署

### 数据库设置

#### 方案A：SQLite（无需额外配置，推荐用于小规模使用）

```python
# app_multiuser.py 中自动使用 SQLite
db = Database(db_type="sqlite", db_path="bio_mood.db")
```

数据库文件将自动创建在项目目录下：`bio_mood.db`

#### 方案B：MySQL（推荐用于生产环境）

1. **安装 MySQL**

```bash
# Windows - 使用 MySQL 安装程序
# macOS - 使用 Homebrew
brew install mysql

# Linux - 使用包管理器
sudo apt-get install mysql-server
```

2. **创建数据库**

```sql
CREATE DATABASE bio_mood CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

3. **配置连接**

在 `app_multiuser.py` 中修改数据库初始化：

```python
mysql_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',
    'database': 'bio_mood'
}

db = Database(db_type="mysql", mysql_config=mysql_config)
```

### 用户认证

系统使用 bcrypt 加密密码，注册新账户时自动哈希处理。

**首次使用**：
1. 点击"📝 注册新账户"
2. 输入用户名（3-20字符）、邮箱、密码（8字符以上）
3. 注册完成后可使用账户登录

---

## 云端部署

### 方案 1️⃣：Streamlit Community Cloud（免费，推荐新手）

#### 步骤：

1. **上传到 GitHub**

```bash
git init
git add .
git commit -m "Initial commit"
git push origin main
```

2. **访问 Streamlit Cloud**
   - 登录 https://share.streamlit.io
   - 点击"Create app"
   - 选择 GitHub 仓库
   - 输入路径：`app_multiuser.py`
   - 点击"Deploy"

#### 配置环境变量

在 Streamlit Cloud 的 Settings → Secrets 中添加：

```toml
# 如果使用 MySQL
[database]
host = "your-database-host"
user = "your-database-user"
password = "your-database-password"
database = "bio_mood"
```

### 方案 2️⃣：Heroku（适合小型应用）

#### 步骤：

1. **创建 Procfile**

```
web: streamlit run app_multiuser.py --server.port=$PORT --server.address=0.0.0.0
```

2. **创建 setup.sh**

```bash
mkdir -p ~/.streamlit/

echo "\
[theme]
primaryColor = \"#667eea\"
backgroundColor = \"#ffffff\"
secondaryBackgroundColor = \"#f5f5f5\"
textColor = \"#262730\"
font = \"sans serif\"

[server]
headless = true
port = \$PORT
enableXsrfProtection = false
" > ~/.streamlit/config.toml

echo "\
[logger]
level = \"warning\"
" >> ~/.streamlit/config.toml
```

3. **部署**

```bash
heroku login
heroku create your-app-name
heroku config:set DATABASE_URL="your-mysql-url"
git push heroku main
```

### 方案 3️⃣：Docker + 云服务器（推荐专业用户）

#### 创建 Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["streamlit", "run", "app_multiuser.py", "--server.port=8502", "--server.address=0.0.0.0"]
```

#### 创建 docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8502:8502"
    environment:
      - DATABASE_URL=mysql://user:password@db:3306/bio_mood
    depends_on:
      - db
    volumes:
      - ./bio_mood.db:/app/bio_mood.db

  db:
    image: mysql:8.0
    environment:
      - MYSQL_ROOT_PASSWORD=password
      - MYSQL_DATABASE=bio_mood
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

#### 启动容器

```bash
docker-compose up -d
```

### 方案 4️⃣：阿里云/腾讯云/华为云

#### 使用云函数 + RDS

1. **上传代码到云函数**
2. **配置 RDS 数据库连接**
3. **配置自定义域名和 HTTPS**

参考各云服务商的 Streamlit 部署文档

---

## 功能说明

### 👤 用户管理

- **注册**：创建新账户，密码使用 bcrypt 加密
- **登录**：安全认证和会话管理
- **个人资料**：查看账户信息和最后登录时间
- **登出**：安全退出并清理会话

### 📊 数据记录

#### 心情记录
- 自动每10步保存一次心情数据
- 保存项目：心情值、基线、睡眠压力、HRV、参数
- 可追溯用户的完整情绪变化过程

#### 事件记录
- 快速事件：喝咖啡、运动、压力、冥想、睡眠等
- AI 分析事件：使用 GPT 或 Gemini 进行深度分析
- 保存事件影响幅度和时间

### 📈 数据分析

#### 统计分析（Tab 1）
- 平均心情值、最高值、最低值
- 心情值分布直方图
- 自定义时间范围（7/14/30天）

#### 心情历史（Tab 2）
- 表格形式查看所有心情记录
- 支持 CSV 下载导出

#### 事件记录（Tab 3）
- 查看所有记录的事件
- 显示事件类型和影响幅度

#### 参数设置（Tab 4）
- 调整个性化模型参数
- 实时保存到数据库
- 支持参数恢复

### 🤖 AI 分析

支持两种大模型：

- **SiliconFlow (Qwen)**：国内 API，速度快
- **Google Gemini**：国际服务，性能强

AI 会分析事件对心情的影响，返回：
- 影响幅度（正负值）
- 持续时间
- 参数建议
- 详细说明

### 🧬 Borbély 模型

系统实现了科学的睡眠-情绪模型：

**Process S**（睡眠稳态）
- 清醒时积累，睡眠时衰减
- 参数：tau_r（积累时间）、tau_d（衰减时间）

**Process C**（昼夜节律）
- 24小时周期性变化
- 模拟核心体温和激素周期

**DHO**（阻尼谐振子）
- 模拟情绪动力学
- 参数：k（刚度）、c（阻尼）

---

## 故障排除

### 问题 1：数据库连接错误

```
ERROR: database is locked (sqlite3)
```

**解决方案**：
```bash
# 删除旧的数据库文件重新开始
rm bio_mood.db
# 重启应用
streamlit run app_multiuser.py
```

### 问题 2：API 超时

```
ERROR: Request timeout (60秒)
```

**解决方案**：
- 检查网络连接
- 增加超时时间（见 `app.py` 中的 `timeout=60`）
- 更换 AI 模型

### 问题 3：Streamlit 缓存问题

```
FileNotFoundError: .streamlit config not found
```

**解决方案**：
```bash
mkdir -p .streamlit
# 复制 config.toml 文件
cp .streamlit/config.toml ~/.streamlit/
```

### 问题 4：Python 版本不兼容

```
ERROR: No matching distribution found for streamlit-authenticator>=0.2.3
```

**解决方案**：
```bash
# 升级 Python 到 3.9+
python --version

# 或使用兼容版本
pip install streamlit-authenticator==0.2.2
```

### 问题 5：MySQL 连接失败

```
ERROR: (2003, "Can't connect to MySQL server")
```

**解决方案**：
```bash
# 检查 MySQL 服务是否运行
# Windows
net start MySQL80

# macOS
brew services start mysql

# Linux
sudo systemctl start mysql

# 检查连接信息
mysql -h localhost -u root -p
```

---

## 性能优化

### 1️⃣ 数据库优化

```sql
-- 为常用查询添加索引
CREATE INDEX idx_mood_user_time ON mood_records(user_id, timestamp DESC);
CREATE INDEX idx_events_user_time ON events(user_id, timestamp DESC);
```

### 2️⃣ 缓存优化

```python
# 使用 Streamlit 缓存减少计算
@st.cache_data
def get_mood_statistics(user_id, days):
    return db.get_mood_statistics(user_id, days)
```

### 3️⃣ 前端优化

- 限制图表显示的数据量（最近 288 条）
- 使用懒加载加载历史数据
- 优化 Plotly 图表性能

---

## 安全建议

### 🔐 密码安全

- ✅ 已实现 bcrypt 加密
- ✅ 已实现密码长度验证（8+ 字符）
- 建议：定期更改密码

### 🛡️ HTTPS

对于云端部署，务必启用 HTTPS：

```python
# Streamlit Cloud 自动启用 HTTPS
# 自助服务器需手动配置

[server]
sslKeyFile = "/path/to/key.pem"
sslCertFile = "/path/to/cert.pem"
```

### 📧 API 密钥管理

```bash
# 使用环境变量存储敏感信息
export SILICONFLOW_API_KEY="sk-xxx"
export GEMINI_API_KEY="AIza..."

# 在代码中读取
import os
api_key = os.getenv("SILICONFLOW_API_KEY")
```

### 🗄️ 数据库备份

```bash
# SQLite 备份
cp bio_mood.db bio_mood.backup.db

# MySQL 备份
mysqldump -u root -p bio_mood > backup.sql
```

---

## 维护和更新

### 升级依赖

```bash
pip install --upgrade -r requirements.txt
```

### 监控日志

```bash
# 检查 Streamlit 日志
tail -f ~/.streamlit/logs/streamlit.log
```

### 数据导出

系统支持导出用户数据：
- CSV 格式
- JSON 格式（通过 API）

---

## 常见问题 (FAQ)

**Q: 数据存储在哪里？**
A: SQLite 时存在本地 `bio_mood.db` 文件，MySQL 时存在 MySQL 服务器上。

**Q: 支持多少用户？**
A: SQLite 版本适合 <100 用户，MySQL 版本可扩展到 >10000 用户。

**Q: 如何导入旧数据？**
A: 见 `database.py` 中的 `add_mood_record()` 和 `add_event()` 方法。

**Q: 可以离线使用吗？**
A: 除了 AI 分析功能，其他功能完全可以离线使用。

**Q: 支持移动端吗？**
A: Streamlit 和现代浏览器支持响应式设计，完全兼容移动设备。

---

## 支持和反馈

- 📧 反馈问题：提交 GitHub Issue
- 💬 讨论功能：参与 GitHub Discussions
- 🔗 获取帮助：查看 Streamlit 官方文档

---

## 许可证

MIT License © 2025 Bio-Mood Digital Twin
