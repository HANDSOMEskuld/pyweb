# 🧠 Bio-Mood Digital Twin - 多用户在线版

> 基于科学的Borbély双过程睡眠模型与阻尼谐振子动力学的实时心情量化系统
> 
> **完整的用户认证 + 云端部署 + 心情追踪 + AI分析**

---

## ✨ 核心功能

### 👤 用户管理
- ✅ 安全注册登录（bcrypt密码加密）
- ✅ 个人资料管理
- ✅ 会话持久化
- ✅ 多用户隔离

### 📊 心情记录
- ✅ 实时心情值记录
- ✅ 自动保存到数据库
- ✅ 完整历史追踪
- ✅ 心情趋势分析

### 📅 事件追踪
- ✅ 快速事件记录（喝咖啡、运动、冥想等）
- ✅ AI智能分析（使用GPT/Gemini）
- ✅ 事件影响评估
- ✅ 事件标记在图表上

### 📈 数据中心
- ✅ 统计分析（平均值、最高值、最低值）
- ✅ 心情分布图
- ✅ 历史数据查询
- ✅ CSV导出功能

### 🧬 科学模型
- ✅ Borbély双过程睡眠模型
- ✅ 昼夜节律（Process C）
- ✅ 睡眠稳态（Process S）
- ✅ 阻尼谐振子（DHO情绪动力学）
- ✅ HRV生物标志物映射

### 🤖 AI增强
- ✅ SiliconFlow (Qwen) API 支持
- ✅ Google Gemini API 支持
- ✅ 自动事件影响分析
- ✅ 智能参数建议

---

## 🚀 快速开始

### 最简单的方式（3步）

#### 1️⃣ 克隆项目
```bash
git clone <repository-url>
cd pyweb
```

#### 2️⃣ 运行启动脚本

**Windows:**
```bash
run.bat
```

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

#### 3️⃣ 打开浏览器
```
http://localhost:8502
```

### 完整安装步骤

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行应用
streamlit run app_multiuser.py
```

---

## 📖 使用指南

### 首次使用

1. **注册账户**
   - 点击"📝 注册新账户"
   - 输入用户名（3-20字符）、邮箱、密码（8字符以上）
   - 完成注册

2. **登录**
   - 使用注册的用户名和密码登录
   - 系统会加载你的个人数据

3. **记录心情**
   - 使用侧边栏的HRV滑块和快速事件按钮
   - 系统实时记录和展示心情曲线
   - 自动保存到数据库

### 核心页面说明

#### 仪表板（主页）
- **当前心情值**：实时心情评分
- **能量基线**：生物节律基线
- **睡眠压力**：当前睡眠债
- **心情曲线图**：可视化情绪变化

#### 数据中心（4个标签页）

**📈 统计分析**
- 选择时间范围（7/14/30天）
- 查看平均值、最高值、最低值
- 心情值分布直方图

**📝 心情历史**
- 表格显示所有心情记录
- 包含时间戳、基线、睡眠压力等
- 支持CSV导出

**📅 事件记录**
- 显示所有记录的事件
- 事件类型和影响幅度
- 时间追踪

**⚙️ 参数设置**
- 个性化调整模型参数
- 实时保存
- 对应用行为有即时影响

### 侧边栏功能

#### 快速事件按钮
- ☕ **喝咖啡**：暂时降低睡眠压力
- 🏃 **运动**：释放内啡肽，增加能量
- 🤯 **压力事件**：模拟压力冲击
- 🧘 **冥想**：增加情绪稳定性
- 💤 **睡眠开关**：切换睡眠状态

#### AI分析
- 输入事件描述（如"和朋友吵架"）
- AI使用GPT/Gemini进行分析
- 返回影响幅度、持续时间、参数建议

#### HRV生物标志物
- 输入当前心率变异性（10-100 ms）
- 自动映射到情绪参数k和c
- 反映自主神经系统平衡

---

## 🏗️ 项目结构

```
pyweb/
├── app.py                    # 原始单用户版本
├── app_multiuser.py          # 多用户在线版本（推荐）
├── database.py               # 数据库操作模块
├── auth.py                   # 认证和用户管理
├── requirements.txt          # Python依赖
├── DEPLOYMENT.md             # 详细部署指南
├── PARAMETER_SCIENCE.md      # 参数科学验证
├── PARAMETER_USER_GUIDE.md   # 用户指南
├── QUICK_REFERENCE.md        # 快速参考表
├── run.bat                   # Windows启动脚本
├── run.sh                    # Linux/macOS启动脚本
├── .env.example              # 环境变量模板
├── .streamlit/
│   └── config.toml          # Streamlit配置
├── bio_mood.db              # SQLite数据库（自动创建）
└── README.md                # 本文件
```

---

## 📊 数据模型

### 用户表 (users)
```
id, username, email, password_hash, created_at, last_login, is_active, preferences
```

### 心情记录表 (mood_records)
```
id, user_id, timestamp, mood_value, baseline, sleep_pressure, hrv_value, parameters, notes
```

### 事件记录表 (events)
```
id, user_id, event_type, event_description, timestamp, amplitude, duration, ai_analysis, created_at
```

### 用户参数表 (user_parameters)
```
id, user_id, tau_r, tau_d, circadian_k, circadian_amplitude, k, c, m, base_hrv, phi, updated_at
```

---

## 🧬 科学基础

### Borbély双过程模型

系统基于1982年Alexander Borbély提出的睡眠调控双过程模型：

#### Process S（睡眠稳态）
- 清醒时积累（tau_r ≈ 17小时）
- 睡眠时衰减（tau_d ≈ 5.5小时）
- 由脑脊液中的腺苷浓度驱动

#### Process C（昼夜节律）
- 24小时周期性变化
- 由视交叉上核（SCN）驱动
- 控制核心体温、激素分泌

#### DHO（情绪动力学）
- 阻尼谐振子模型
- 参数：k（刚度）、c（阻尼）
- 模拟心理韧性和情绪调节能力

### 模型方程

```
dS/dt = ±(S - S_target) / τ
C(t) = A*sin(ωt+φ) + (A/3)*sin(2ωt+φ+π)
m*dv/dt + c*v + k*x = F_external
```

### 参数范围

| 参数 | 单位 | 范围 | 默认值 | 说明 |
|------|------|------|--------|------|
| tau_r | 小时 | 15.0-19.0 | 17.0 | 清醒时睡眠压力积累时间 |
| tau_d | 小时 | 3.0-10.0 | 5.5 | 睡眠时睡眠压力衰减时间 |
| circadian_amplitude | - | 0.1-0.5 | 0.3 | 昼夜节律振幅 |
| k | - | 2.0-30.0 | 12.0 | 情绪刚度（心理韧性） |
| c | - | 0.5-10.0 | 3.5 | 情绪阻尼（调节速度） |
| base_hrv | ms | 20-100 | 50.0 | 基准心率变异性 |

---

## 🌐 云端部署

支持多种部署方案：

### 1️⃣ Streamlit Community Cloud（推荐）
最简单，零成本

```bash
# 仅需：
1. 上传到GitHub
2. 在 https://share.streamlit.io 连接仓库
3. 选择 app_multiuser.py 和 MySQL 数据库配置
```

### 2️⃣ Heroku
$5-50/月，含数据库

```bash
heroku create your-app
git push heroku main
```

### 3️⃣ Docker
自托管，完全控制

```bash
docker-compose up -d
```

### 4️⃣ 云服务商
阿里云、腾讯云、华为云等

详见 [DEPLOYMENT.md](./DEPLOYMENT.md)

---

## 🔐 安全特性

- ✅ bcrypt密码加密
- ✅ SQL注入防护
- ✅ HTTPS支持
- ✅ CSRF保护
- ✅ 用户隔离（每用户只能访问自己的数据）
- ✅ API密钥环境变量存储
- ✅ 会话超时管理

---

## 📱 浏览器兼容性

- ✅ Chrome/Edge (推荐)
- ✅ Firefox
- ✅ Safari
- ✅ 移动浏览器（iOS Safari, Android Chrome）

---

## 🤖 AI集成

### SiliconFlow API
```python
# 使用国内高速API
analyze_event_with_deepseek(event, hrv, feedback)
```

### Google Gemini API
```python
# 使用国际高性能API
analyze_event_with_gemini(event, hrv, feedback)
```

**获取API密钥：**
- [SiliconFlow](https://siliconflow.cn)
- [Google AI Studio](https://aistudio.google.com)

---

## 🐛 常见问题

**Q: 可以离线使用吗？**
A: 可以，除了AI分析功能外都支持离线。

**Q: 数据隐私如何保证？**
A: 用户数据只保存在本地（SQLite）或自己的MySQL服务器，不上传到云端。

**Q: 支持多少用户？**
A: SQLite版本<100，MySQL版本>10000。

**Q: 可以修改模型参数吗？**
A: 可以，在"参数设置"页面自定义。

**Q: 如何导出数据？**
A: 在"心情历史"和"事件记录"页面有导出按钮。

---

## 📚 文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) - 详细部署指南
- [PARAMETER_SCIENCE.md](./PARAMETER_SCIENCE.md) - 科学验证文档
- [PARAMETER_USER_GUIDE.md](./PARAMETER_USER_GUIDE.md) - 用户指南
- [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) - 快速参考表

---

## 🔄 更新日志

### v2.0 (2025-12-07)
- ✨ 完整的多用户系统
- ✨ SQLite/MySQL双数据库支持
- ✨ 用户认证和会话管理
- ✨ 心情和事件完整追踪
- ✨ 云端部署支持
- ✨ 数据统计和导出
- 🐛 修复API超时问题

### v1.0 (原始版本)
- 基础Borbély模型实现
- 单用户本地版本
- AI事件分析

---

## 📄 许可证

MIT License © 2025 Bio-Mood Digital Twin

---

## 🙏 致谢

- Borbély A. A. - 双过程睡眠模型
- Czeisler C. A. - 昼夜节律研究
- Thayer J. F. - 神经内脏整合模型
- Streamlit - 优秀的数据应用框架

---

## 📞 支持

- 📧 邮件：support@bio-mood.com
- 🐛 问题报告：GitHub Issues
- 💬 讨论：GitHub Discussions
- 📖 文档：见本目录下各markdown文件

---

**开始你的情绪量化之旅吧！** 🚀

```bash
# 一键启动
./run.sh  # Linux/macOS
# 或
run.bat   # Windows
```

访问 `http://localhost:8502` 开始使用！
