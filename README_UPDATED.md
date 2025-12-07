# Bio-Mood Digital Twin 系统

基于Borbély双过程睡眠模型的情绪量化与自适应Web系统

## 📌 重要更新 (2025年12月7日)

**参数深度科学优化完成！**

所有生理参数现在基于同行评审的神经科学文献。详见下方新增文档。

---

## 📚 文档导航

### 🔬 学术文档 (针对研究人员和医疗专业人士)

- **[PARAMETER_SCIENCE.md](./PARAMETER_SCIENCE.md)** - 完整的科学验证 (7000+字)
  - 所有参数的原始论文引用 (20+篇)
  - 每个参数的生物学机制详解
  - 临床应用指南和诊断对照
  - 参数范围和个性化公式

### 👤 用户文档 (针对应用用户)

- **[PARAMETER_USER_GUIDE.md](./PARAMETER_USER_GUIDE.md)** - 用户友好指南 (4500+字)
  - 每个参数的简明解释
  - 时间特征和数值示例
  - 场景应用 (疲劳、焦虑、易激动等)
  - 干预建议和效果对标

### 📊 快速参考

- **[QUICK_REFERENCE.md](./QUICK_REFERENCE.md)** - 10个速查表格
  - 参数对照表
  - HRV标准值表
  - 个性化调整矩阵
  - 诊断速查和时间常数含义
  - 临界值和参考范围

### 📋 项目总结

- **[COMPLETION_REPORT.md](./COMPLETION_REPORT.md)** - 完整的项目总结
  - 参数改进对比表
  - 科学验证清单
  - 参数与诊病的关系
  - 后续优化方向

- **[OPTIMIZATION_SUMMARY.md](./OPTIMIZATION_SUMMARY.md)** - 详细的优化说明
  - 新增功能详解
  - 改进的HRV映射
  - 动态应激事件处理
  - 已知限制和扩展方向

---

## 🚀 快速开始

### 安装

```bash
cd e:\InvestMe\pyweb
pip install -r requirements.txt
```

### 运行应用

```bash
python -m streamlit run app.py
```

应用将在 `http://localhost:8501` 打开

### 首次使用

1. **输入基准HRV**: 使用HRV app或智能手表测量
2. **设定作息类型**: 影响昼夜节律相位
3. **记录睡眠**: 系统自动计算睡眠压力
4. **输入事件**: 记录关键事件和反应

---

## 🧠 核心参数概览

| 参数 | 值 | 含义 |
|------|-----|------|
| tau_r | 17.0h | 清醒时睡眠压力积累速度 |
| tau_d | 5.5h | 睡眠时压力清除速度 |
| k | 12.0 | 心理韧性/恢复力 |
| c | 3.5 | 情绪调节速率 |
| amplitude | 0.3 | 昼夜节律振幅 |
| base_hrv | 50ms | 基准自主神经平衡 |

**更多详细信息**: 见 [PARAMETER_USER_GUIDE.md](./PARAMETER_USER_GUIDE.md)

---

## 📈 系统工作原理

### 1. 生物学基线 (Process S + C)

系统根据Borbély双过程模型自动计算:
- **Process S**: 睡眠稳态 (腺苷积累)
- **Process C**: 昼夜节律 (核心体温、激素)
- **Baseline**: S和C的综合效果

### 2. 事件响应 (阻尼谐振子)

用户输入的事件(压力、运动、社交)作为脉冲力:
- 幅度取决于事件严重程度
- 恢复速度取决于k和c值
- 容易反刍取决于阻尼比

### 3. 自适应优化

系统根据用户反馈动态调整参数:
- 每周重新计算个人参数
- 学习个人的"心理个性"
- 提供个性化干预建议

---

## 🔍 参数科学依据

所有参数都基于这些关键论文:

### 核心论文
1. **Borbély, A. A. (1982)**. A two process model of sleep regulation
2. **Xie, L., et al. (2013)**. Sleep drives metabolite clearance from the adult brain
3. **Thayer, J. F., & Lane, R. D. (2000)**. A model of neurovisceral integration

### 睡眠与节律
4. **Czeisler, C. A., & Gooley, J. J. (2007)**. Sleep and circadian rhythms in humans
5. **Borbély, A. A., et al. (2016)**. The two-process model of sleep regulation: a reappraisal

### 情绪与神经生物学
6. **Ochsner, K. N., & Gross, J. J. (2008)**. Cognitive emotion regulation
7. **Banks, S. J., et al. (2007)**. Amygdala-frontal connectivity during emotion regulation

### HRV与自主神经
8. **Task Force of ESC (1996)**. Heart rate variability: standards of measurement
9. **Shaffer, F., & Ginsberg, J. P. (2017)**. An overview of heart rate variability metrics

**完整参考文献**: 见 [PARAMETER_SCIENCE.md](./PARAMETER_SCIENCE.md)

---

## 💡 使用场景

### 个人健康管理
- 追踪睡眠和情绪趋势
- 识别不良模式 (如经常熬夜导致情绪恶化)
- 评估干预效果 (运动、冥想、心理治疗)

### 医学诊断辅助
- 初步筛查睡眠障碍
- 情绪障碍的定量评估
- 治疗反应监测

### 科学研究
- 参数验证实验
- 人群差异研究
- 干预机制探索

---

## ⚙️ 技术栈

- **语言**: Python 3.14
- **核心库**: NumPy, SciPy, Pandas
- **Web框架**: Streamlit
- **可视化**: Plotly
- **AI分析**: Google Gemini, SiliconFlow Qwen (可选)

---

## 📞 常见问题

### Q: 这个系统能替代医学诊断吗?
**A**: 否。本系统是教育和自我监测工具。任何医学诊断必须由合格医疗专业人士进行。

### Q: 参数值能否个性化?
**A**: 可以。系统会根据你的反馈自动调整。详见 [PARAMETER_USER_GUIDE.md](./PARAMETER_USER_GUIDE.md) 的个性化调整部分。

### Q: 为什么要输入HRV?
**A**: HRV (心率变异性) 是自主神经平衡的指标,直接影响情绪调节能力。详见 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md) 表2。

### Q: 模型是否考虑了性别/年龄差异?
**A**: 基础参数是健康成人平均值。可通过个性化调整适应不同人群。见 [PARAMETER_USER_GUIDE.md](./PARAMETER_USER_GUIDE.md) 的场景调整表。

---

## 🛠️ 开发路线图

### 短期 (已完成)
- ✅ 参数科学优化
- ✅ 详细文档编写
- ✅ 代码质量改进

### 中期 (计划中)
- [ ] 可穿戴设备集成 (Apple Watch, Oura Ring)
- [ ] 激素模型添加 (cortisol, melatonin)
- [ ] 参数推荐引擎

### 长期 (展望)
- [ ] 多中心临床验证
- [ ] 机器学习参数拟合
- [ ] 与医疗系统集成

详见 [COMPLETION_REPORT.md](./COMPLETION_REPORT.md)

---

## 📄 文件结构

```
.
├── app.py                      # 主应用程序
├── requirements.txt            # 依赖包列表
│
├── PARAMETER_SCIENCE.md        # 学术文档 (20+论文引用)
├── PARAMETER_USER_GUIDE.md     # 用户指南 (易读版)
├── QUICK_REFERENCE.md          # 快速参考 (表格集)
├── COMPLETION_REPORT.md        # 项目总结
├── OPTIMIZATION_SUMMARY.md     # 优化说明
│
└── readme.md                   # 原始文件
```

---

## 📧 反馈与联系

如有科学问题或使用建议,欢迎提出!

---

## 📜 许可证

本项目基于教育和研究目的。

---

**最后更新**: 2025年12月7日  
**当前版本**: 2.0 (参数优化版)

---

## 致谢

感谢以下研究人员的突破性工作:
- Alexander Borbély (睡眠两过程模型)
- Julian Thayer (神经内脏整合模型)
- Maiken Nedergaard (Glymphatic系统)
- James Ochsner (认知情绪调节)

本应用旨在将这些科学发现应用于实际的个人健康管理。

---

**现在就开始探索您的生物节律吧!** 🚀
