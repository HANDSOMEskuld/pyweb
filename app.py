import numpy as np
from scipy.integrate import solve_ivp
import pandas as pd
import datetime

class BioEngine:
    def __init__(self, params=None):
        # 默认生理参数 (基于文档参考值)
        self.default_params = {
            'tau_r': 18.2,   # 清醒时睡眠压力积累时间常数 [cite: 19]
            'tau_d': 4.2,    # 睡眠时压力衰减时间常数 [cite: 20]
            'k': 10.0,       # 情绪刚度 (恢复力) [cite: 46]
            'c': 2.0,        # 情绪阻尼 (粘性) [cite: 47]
            'm': 1.0,        # 质量 (归一化)
            'phi': 0.0,      # 昼夜节律相位偏移
            'amplitude': 0.12 # 昼夜节律振幅
        }
        # 如果有传入参数，则覆盖默认值 (用于个性化)
        self.params = params if params else self.default_params.copy()
        
        # 初始状态向量: [S (睡眠压力), x (情绪位移), v (情绪速度)]
        self.state = [0.1, 0.0, 0.0] 
        self.is_asleep = False
        self.last_update_time = 0 # 模拟时间的追踪

    def circadian_process(self, t):
        """Process C: 昼夜节律 (谐波回归模型) [cite: 25]"""
        omega = 2 * np.pi / 24.0
        # t 是小时数
        phi = self.params['phi']
        A = self.params['amplitude']
        # 模拟主波 + 下午低谷 (第二谐波)
        C = A * np.sin(omega * t + phi) + (A/2.5) * np.sin(2 * omega * t + phi + np.pi)
        return C

    def derivatives(self, t, y):
        """定义微分方程组 dy/dt = f(t, y) [cite: 113]"""
        S, x, v = y
        
        # --- 1. Process S: 睡眠稳态 [cite: 17] ---
        # 如果当前是睡眠状态，压力下降；否则上升
        if self.is_asleep:
            dS = (0 - S) / self.params['tau_d'] # 向0衰减
        else:
            dS = (1 - S) / self.params['tau_r'] # 向1攀升
            
        # --- 2. DHO: 阻尼谐振子 (情绪反应) [cite: 54] ---
        # m*a + c*v + k*x = 0 (外力 F 在事件处理中单独施加)
        k = self.params['k']
        c = self.params['c']
        m = self.params['m']
        
        dx = v
        dv = -(c * v + k * x) / m
        
        return [dS, dx, dv]

    def step(self, duration_hours):
        """向前模拟指定时长的步进"""
        t_span = (self.last_update_time, self.last_update_time + duration_hours)
        
        # 求解微分方程 [cite: 118]
        sol = solve_ivp(
            fun=self.derivatives,
            t_span=t_span,
            y0=self.state,
            method='RK45',
            dense_output=True
        )
        
        # 更新状态
        self.state = sol.y[:, -1]
        self.last_update_time += duration_hours
        return sol

    def get_mood_value(self, t_now):
        """计算综合心情值: Mood = Baseline + Reaction"""
        S, x, v = self.state
        C = self.circadian_process(t_now)
        
        # Mood Baseline = C(t) - S(t) + Offset [cite: 36]
        # Offset 设为 0.5 保证基线大概率在正数区间
        baseline = C - S + 0.5 
        
        # Reaction = x (当前的瞬时情绪位移)
        total_mood = baseline + x
        return total_mood, baseline, x, S


# 接 BioEngine 类的方法...

    def apply_event(self, event_type, value=None):
        """处理用户输入事件 [cite: 78]"""
        S, x, v = self.state
        
        if event_type == 'sleep_start':
            self.is_asleep = True
            
        elif event_type == 'sleep_end':
            self.is_asleep = False
            # 醒来时S值较高意味着睡眠不足，自然影响后续基线
            
        elif event_type == 'hrv_update':
            # HRV (rMSSD) 映射到 阻尼系数 c 和 刚度 k [cite: 64]
            # 假设基准 HRV 为 50ms. 如果 HRV=25 (压力大), alpha=0.5
            base_hrv = 50.0
            current_hrv = value if value else 50.0
            alpha = max(0.5, min(current_hrv / base_hrv, 2.0))  # 限制 alpha 在 0.5 到 2.0 之间

            self.params['k'] = self.default_params['k'] * alpha
            self.params['c'] = self.default_params['c'] * np.sqrt(alpha)
            
        elif event_type == 'sunlight':
            # 光照重置相位 [cite: 68]
            # 简单实现：早晨光照(t<12)使相位提前(增加phi)
            current_hour = self.last_update_time % 24
            if 6 <= current_hour <= 10:
                self.params['phi'] += 0.2 * value # value是时长
                
        elif event_type == 'stress_event':
            # 施加负向脉冲力 -> 瞬间改变速度 v
            # 模拟力 F 作用一段时间 dt，导致 dv = F/m * dt
            impulse = -30.0 # 强烈的负向冲击 [cite: 79]
            self.state[2] += impulse # 直接修改 v
            
        elif event_type == 'exercise':
            # 运动产生正向推动
            impulse = 20.0
            self.state[2] += impulse

    def get_diagnosis(self):
        """根据参数提供建议 [cite: 128]"""
        k = self.params['k']
        c = self.params['c']
        m = self.params['m']
        S, x, v = self.state
        
        advice = []
        state_tags = []
        
        # 1. 阻尼状态分析
        discriminant = c**2 - 4*m*k
        if discriminant < 0:
            advice.append("⚠️ **欠阻尼状态**：你现在情绪比较敏感，容易受外界影响产生波动。")
            state_tags.append("欠阻尼")
            if c < 1.0:
                advice.append("💡 **缓解建议**：")
                advice.append("  • 进行冥想或深呼吸（4-7-8呼吸法），增加情绪的'粘性'，防止剧烈振荡")
                advice.append("  • 在安静环境中待15-20分钟，减少外界刺激")
                advice.append("  • 尝试渐进式肌肉放松 (PMR)")
        else:
            advice.append("🛡️ **过阻尼状态**：你现在情绪比较钝感/平稳，反应迟缓。")
            state_tags.append("过阻尼")
            advice.append("💡 **缓解建议**：")
            advice.append("  • 进行高强度间歇运动 (HIIT)，激活神经系统")
            advice.append("  • 听节奏感强的音乐或进行社交活动增加刺激")
            advice.append("  • 冷水淋浴或冰水浸泡双手，刺激交感神经")
            
        # 2. 睡眠压力分析
        if S > 0.8:
            advice.append("\n😴 **严重睡眠不足**：adenosine 大量积累，认知能力下降。")
            state_tags.append("严重疲劳")
            advice.append("🚨 **紧急建议**：")
            advice.append("  • **立即**: 进行20分钟 Power Nap（有科学证明可快速恢复）")
            advice.append("  • 找一个暗而安静的地方，关闭手机")
            advice.append("  • 如果无法睡眠，做冥想或眼动脱敏疗法 (EMDR) 式的眼球转动")
        elif S > 0.5:
            advice.append("\n😴 **中等睡眠压力**：开始影响注意力和情绪调节。")
            state_tags.append("疲劳")
            advice.append("💡 **缓解建议**：")
            advice.append("  • 安排15分钟的小憩或午睡")
            advice.append("  • 晒太阳（10-20分钟）以推迟睡眠压力衰减")
            advice.append("  • 避免高强度工作，改做低认知负荷的任务")
        
        # 3. 反刍检测 (负向位移且恢复慢)
        if x < -0.8:
            advice.append("\n🔴 **严重反刍状态**：你陷入了强烈的负面情绪循环。")
            state_tags.append("深度反刍")
            advice.append("🚨 **强效干预**：")
            advice.append("  • **最有效**: 高强度运动（30分钟跑步/骑行），释放内啡肽")
            advice.append("  • 进行冷暴露疗法：冷水淋浴或冰水浸泡")
            advice.append("  • 使用认知行为疗法 (CBT) 的记录法：写下负面想法，逐一反驳")
            advice.append("  • 联系信任的人倾诉（社交支持是最强的重置器）")
        elif x < -0.5:
            advice.append("\n🟠 **中度负面情绪**：开始出现反刍迹象。")
            state_tags.append("反刍")
            advice.append("💡 **缓解建议**：")
            advice.append("  • 进行20-30分钟的中等强度运动（快走、瑜伽）")
            advice.append("  • 切换环境：外出散步、改变工作地点")
            advice.append("  • 进行正念冥想 (5-10分钟)")
            advice.append("  • 完成一个小的成就任务，重建自信")
        elif x < -0.2:
            advice.append("\n🟡 **轻微负面情绪**：情绪略低。")
            state_tags.append("轻微消极")
            advice.append("💡 **缓解建议**：")
            advice.append("  • 做一项你喜欢的活动（听音乐、阅读、手工）")
            advice.append("  • 十分钟伸展或瑜伽")
            advice.append("  • 回忆最近的积极经历")
        
        # 4. 积极情绪分析
        if x > 0.5:
            advice.append("\n🟢 **积极情绪状态**：情绪高涨，适合进行创意工作。")
            state_tags.append("积极")
            advice.append("💡 **建议充分利用**：")
            advice.append("  • 进行需要高创意的任务（写作、设计、问题解决）")
            advice.append("  • 安排社交活动，分享正能量")
            advice.append("  • 学习新技能，这时学习效率最高")
            advice.append("  • 运动表现也会更好，适合挑战极限")
        
        # 5. 综合建议
        if v > 1.0:  # 速度很快（快速变化）
            advice.append("\n⚡ **情绪变化剧烈**：你的情绪在快速波动。")
            state_tags.append("波动中")
            advice.append("💡 **稳定建议**：")
            advice.append("  • 降低决策重要性：避免在这时做重大决定")
            advice.append("  • 进行稳定性运动：太极、普拉提")
            advice.append("  • 增加规律性：建立固定的作息和活动计划")
        elif abs(v) < 0.1:  # 速度很慢（平稳）
            advice.append("\n✨ **情绪平稳**：你处于相对稳定的状态。")
            state_tags.append("平稳")
            advice.append("💡 **维持建议**：")
            advice.append("  • 保持当前的生活节奏")
            advice.append("  • 进行中等强度运动维持体能")
            advice.append("  • 适合进行重要决策")
            
        return advice, state_tags

from scipy.optimize import minimize

def optimize_parameters(engine, feedback_history):
    """
    engine: 当前的 BioEngine 实例
    feedback_history: 列表 [(time, user_score), ...]
    """
    if len(feedback_history) < 3:
        return engine.params # 数据太少，不优化
        
    print("正在根据用户反馈优化参数...")
    
    # 目标函数：最小化 (模型预测 - 用户真实) 的平方差 [cite: 85]
    def objective_function(param_values):
        # 解包参数
        tau_r, k, c = param_values
        
        # 创建临时引擎进行模拟
        temp_engine = BioEngine()
        temp_engine.params['tau_r'] = tau_r
        temp_engine.params['k'] = k
        temp_engine.params['c'] = c
        temp_engine.state = engine.state # 继承当前状态 (简化处理，严谨应用应该从历史起点重跑)
        
        error_sum = 0
        
        # 简单回测：这里为了演示，只计算当前点的误差
        # *在生产环境中，应该重演过去几天的事件流*
        for t_log, score_true in feedback_history:
             # 假设 score_true 归一化在 -1 到 1 之间
             # 模型输出
             pred, _, _, _ = temp_engine.get_mood_value(t_log)
             # 归一化模型输出以便比较 (假设模型输出范围大概在 -2 到 2)
             pred_norm = np.clip(pred / 2.0, -1, 1)
             
             error_sum += (pred_norm - score_true)**2
             
        return error_sum

    # 初始猜测
    initial_guess = [engine.params['tau_r'], engine.params['k'], engine.params['c']]
    
    # 边界约束 [cite: 94]
    bounds = [
        (15.0, 22.0), # tau_r
        (2.0, 30.0),  # k (刚度)
        (0.5, 10.0)   # c (阻尼)
    ]
    
    # 执行优化 L-BFGS-B
    result = minimize(objective_function, initial_guess, bounds=bounds, method='L-BFGS-B')
    
    if result.success:
        new_params = engine.params.copy()
        new_params['tau_r'] = result.x[0]
        new_params['k'] = result.x[1]
        new_params['c'] = result.x[2]
        return new_params
    else:
        return engine.params

import streamlit as st
import time
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from streamlit_autorefresh import st_autorefresh # 需要 pip install streamlit-autorefresh

# 引入上面的类和函数 (假设在同一文件中或已导入)
# from bio_model import BioEngine, optimize_parameters

# --- 页面配置 ---
st.set_page_config(page_title="Bio-Mood Digital Twin", layout="wide")

st.title("🧠 情绪量化生物数字孪生系统")
st.markdown("基于 **Borbély双过程模型** 与 **阻尼动力学** 的实时情绪模拟器")

# --- 1. Session State 初始化 ---
if 'engine' not in st.session_state:
    st.session_state['engine'] = BioEngine()
    # 模拟从早上8点开始
    st.session_state['engine'].last_update_time = 8.0 
    st.session_state['start_real_time'] = time.time()
    
if 'history' not in st.session_state:
    st.session_state['history'] = {'time': [], 'mood': [], 'baseline': []}

if 'feedback_data' not in st.session_state:
    st.session_state['feedback_data'] = []

# --- 2. 侧边栏：事件输入 (React) ---
with st.sidebar:
    st.header("🎮 施加环境刺激")
    
    st.subheader("生理数据")
    hrv_input = st.slider("当前 HRV (rMSSD)", 10, 100, 50)
    if st.button("更新 HRV"):
        st.session_state['engine'].apply_event('hrv_update', hrv_input)
        st.success(f"HRV参数已映射: k={st.session_state['engine'].params['k']:.1f}, c={st.session_state['engine'].params['c']:.1f}")
        st.info("HRV 越低，可能导致情绪波动更大；HRV 越高，情绪更稳定。")

    st.subheader("事件")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☕ 喝咖啡"):
            # 咖啡因生效：暂时降低睡眠压力
            st.session_state['engine'].state[0] *= 0.6 
            st.toast("咖啡因生效：睡眠压力暂时降低")
            
    with col2:
        if st.button("🤯 压力事件"):
            st.session_state['engine'].apply_event('stress_event')
            st.toast("受到压力冲击！")
            
    with col1:
         if st.button("🏃 运动"):
            st.session_state['engine'].apply_event('exercise')
            st.toast("运动释放内啡肽！")
            
    with col2:
        if st.button("🧘 冥想"):
            # 冥想增加阻尼，减缓速度
            st.session_state['engine'].state[2] = 0 # 速度归零
            st.session_state['engine'].params['c'] += 2.0
            st.toast("系统强制平静 (阻尼增加)")

    st.divider()
    
    # 睡眠开关
    is_sleeping = st.toggle("正在睡眠模式", value=st.session_state['engine'].is_asleep)
    if is_sleeping != st.session_state['engine'].is_asleep:
        if is_sleeping:
            st.session_state['engine'].apply_event('sleep_start')
        else:
            st.session_state['engine'].apply_event('sleep_end')
        st.rerun()

# --- 3. 核心循环 (自动刷新) ---
# 每 1 秒刷新一次页面，模拟时间的流逝
count = st_autorefresh(interval=1000, key="fizzbuzz")

# 计算时间步进
current_real_time = time.time()
# 缩放时间：现实 1 秒 = 模拟 10 分钟 (为了演示效果能看到曲线变化)
time_scale = 10 * 60 
elapsed_real = current_real_time - st.session_state['start_real_time']
sim_time_now = 8.0 + (elapsed_real * time_scale / 3600.0) # 小时

# 运行物理引擎步进 [cite: 122]
dt = sim_time_now - st.session_state['engine'].last_update_time
if dt > 0:
    st.session_state['engine'].step(dt)
    
    # 记录数据用于绘图
    mood, base, x, S = st.session_state['engine'].get_mood_value(sim_time_now)
    st.session_state['history']['time'].append(sim_time_now)
    st.session_state['history']['mood'].append(mood)
    st.session_state['history']['baseline'].append(base)
    
    # 保持历史数据不无限增长 (最近48小时)
    if len(st.session_state['history']['time']) > 288:
        for k in st.session_state['history']:
            st.session_state['history'][k].pop(0)

# --- 4. 主界面展示 ---

# 4.1 仪表盘
mood_now, base_now, x_now, S_now = st.session_state['engine'].get_mood_value(sim_time_now)

col_a, col_b, col_c, col_d = st.columns(4)
col_a.metric("当前心情值", f"{mood_now:.2f}", delta=f"{x_now:.2f} (偏差)")
col_b.metric("能量基线 (Energy)", f"{base_now:.2f}")
col_c.metric("睡眠压力 (Process S)", f"{S_now:.2f}")
col_d.metric("模拟时间", f"{int(sim_time_now)%24:02d}:{int((sim_time_now%1)*60):02d}")

# 4.2 实时曲线图 - 使用 Baseline 样式
st.subheader("📈 心情动力学曲线")

if len(st.session_state['history']['time']) > 0:
    # 创建 Plotly Baseline 样式图表
    fig = go.Figure()
    
    # 获取基线和心情数据
    times = st.session_state['history']['time']
    moods = st.session_state['history']['mood']
    baselines = st.session_state['history']['baseline']
    
    # 设置基线值（使用当前基线的平均值）
    baseline_value = sum(baselines) / len(baselines) if baselines else 0
    
    # 添加心情数据 - 绿色（积极情绪）
    fig.add_trace(go.Scatter(
        x=times,
        y=moods,
        name='Mood (Total)',
        mode='lines',
        line=dict(color='rgba(38, 166, 154, 1)', width=2),
        fill='tozeroy',
        fillcolor='rgba(38, 166, 154, 0.28)',
        hovertemplate='<b>时间</b>: %{x:.1f}h<br><b>心情值</b>: %{y:.2f}<extra></extra>'
    ))
    
    # 添加基线数据 - 红色（基础生物节律）
    fig.add_trace(go.Scatter(
        x=times,
        y=baselines,
        name='Baseline (Bio-Rhythm)',
        mode='lines',
        line=dict(color='rgba(239, 83, 80, 1)', width=2),
        fill='tozeroy',
        fillcolor='rgba(239, 83, 80, 0.28)',
        hovertemplate='<b>时间</b>: %{x:.1f}h<br><b>基线</b>: %{y:.2f}<extra></extra>'
    ))
    
    # 添加中线（0值线）用于参考
    fig.add_hline(
        y=0, 
        line_dash="dash", 
        line_color="rgba(150, 150, 150, 0.5)",
        annotation_text="情绪中线",
        annotation_position="right"
    )
    
    # 添加状态区域标记
    # 积极区域 (y > 0.5)
    fig.add_hrect(
        y0=0.5, y1=max(moods) if moods else 1,
        fillcolor="rgba(76, 175, 80, 0.1)", line_width=0,
        annotation_text="✨ 积极区域", annotation_position="right",
        layer="below"
    )
    
    # 消极区域 (y < -0.5)
    fig.add_hrect(
        y0=min(moods) if moods else -1, y1=-0.5,
        fillcolor="rgba(244, 67, 54, 0.1)", line_width=0,
        annotation_text="🔴 消极区域", annotation_position="right",
        layer="below"
    )
    
    # 更新图表布局 - 仿 lightweight-charts 样式
    fig.update_layout(
        title=dict(text='', x=0.5, xanchor='center'),
        xaxis=dict(
            title='模拟时间 (小时)',
            gridcolor='rgba(200, 200, 200, 0.3)',
            showgrid=True,
            zeroline=False,
            color='black'
        ),
        yaxis=dict(
            title='心情值',
            gridcolor='rgba(200, 200, 200, 0.3)',
            showgrid=True,
            zeroline=False,
            color='black'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial', size=12, color='black'),
        hovermode='x unified',
        margin=dict(l=50, r=120, t=40, b=50),
        height=450,
        showlegend=True,
        legend=dict(
            x=0.02,
            y=0.98,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='rgba(200, 200, 200, 0.5)',
            borderwidth=1
        )
    )
    
    st.plotly_chart(fig, width='stretch')
else:
    st.info("等待数据更新中...")

# 4.3 诊断与建议 [cite: 129]
st.subheader("🩺 实时生物反馈与建议")

# 获取诊断信息
advice_list, state_tags = st.session_state['engine'].get_diagnosis()

# 显示当前状态标签
if state_tags:
    st.markdown("**当前状态：**")
    cols = st.columns(len(state_tags))
    for idx, tag in enumerate(state_tags):
        with cols[idx % len(cols)]:
            if "积极" in tag:
                st.success(f"✨ {tag}")
            elif "疲劳" in tag or "消极" in tag:
                st.error(f"🔴 {tag}")
            elif "反刍" in tag:
                st.warning(f"🟠 {tag}")
            elif "波动" in tag:
                st.warning(f"⚡ {tag}")
            else:
                st.info(f"ℹ️ {tag}")

st.divider()

# 显示详细建议
if advice_list:
    for advice in advice_list:
        # 根据内容类型选择显示方式
        if "紧急" in advice or "强效干" in advice:
            st.error(advice)
        elif "严重" in advice:
            st.warning(advice)
        elif "缓解建议" in advice or "建议" in advice or "维持建议" in advice:
            st.info(advice)
        elif "积极" in advice or "✨" in advice:
            st.success(advice)
        else:
            st.markdown(advice)
else:
    st.success("✅ 系统运行平稳，情绪处于健康平衡状态。")

# --- 5. 参数自适应与反馈 (Optimize) ---
st.divider()
st.subheader("🎯 模型校准 (Ground Truth)")

with st.expander("告诉我你现在的真实感觉，帮助我学习"):
    user_feel = st.slider("你现在感觉如何？(-1 悲伤/疲惫, 1 兴奋/精力充沛)", -1.0, 1.0, 0.0)
    if st.button("提交反馈"):
        # 记录反馈
        st.session_state['feedback_data'].append((sim_time_now, user_feel))
        st.success("反馈已记录！")
        
        # 触发优化 [cite: 89]
        if len(st.session_state['feedback_data']) >= 3:
            new_params = optimize_parameters(st.session_state['engine'], st.session_state['feedback_data'])
            st.session_state['engine'].params = new_params
            st.toast(f"参数已更新！个性化刚度 k: {new_params['k']:.2f}, 阻尼 c: {new_params['c']:.2f}")
            st.success("模型校准完成！参数已优化。")

# 显示当前内部参数
st.json(st.session_state['engine'].params)