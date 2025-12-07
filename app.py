from bio_model import BioEngine, StreamlitLogger, analyze_event_with_deepseek, analyze_event_with_gemini
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

if 'event_markers' not in st.session_state:
    st.session_state['event_markers'] = []

if 'logger' not in st.session_state:
    st.session_state['logger'] = StreamlitLogger()

if 'ai_model' not in st.session_state:
    st.session_state['ai_model'] = 'SiliconFlow'

# 为了简化，定义一个全局logger
logger = st.session_state['logger']

# 默认加载硅基流动模型
st.sidebar.title("模型设置")
st.sidebar.write("当前模型: 硅基流动 (SiliconFlow)")

# 示例：初始化硅基流动模型
silicon_flow_model = BioEngine()
st.sidebar.success("硅基流动模型已加载！")

# --- 2. 侧边栏：事件输入 (React) ---
with st.sidebar:
    st.header("🎮 施加环境刺激")
    
    # AI模型选择
    st.subheader("🤖 AI大模型选择")
    ai_model = st.radio(
        "选择AI大模型",
        options=['SiliconFlow (Qwen)', 'Google Gemini'],
        index=0 if st.session_state['ai_model'] == 'SiliconFlow' else 1,
        key='ai_model_radio'
    )
    st.session_state['ai_model'] = ai_model
    
    if ai_model == 'SiliconFlow (Qwen)':
        st.info("✅ 使用硅基流动的Qwen模型")
    else:
        st.info("✅ 使用Google Gemini-2.5-Pro模型")
    
    st.divider()

# 为了简化，定义一个全局logger
logger = st.session_state['logger']

if 'feedback_data' not in st.session_state:
    st.session_state['feedback_data'] = []

if 'event_markers' not in st.session_state:
    st.session_state['event_markers'] = []

# --- 2. 侧边栏：事件输入 (React) ---
with st.sidebar:
    st.header("🎮 施加环境刺激")
    
    st.subheader("生理数据")
    hrv_input = st.slider("当前 HRV (rMSSD)", 10, 100, 50, key="hrv_slider")
    if st.button("更新 HRV"):
        st.session_state['engine'].apply_event('hrv_update', hrv_input)
        st.success(f"HRV参数已映射: k={st.session_state['engine'].params['k']:.1f}, c={st.session_state['engine'].params['c']:.1f}")
        st.info("HRV 越低，可能导致情绪波动更大；HRV 越高，情绪更稳定。")
        # 记录事件
        if 'event_markers' not in st.session_state:
            st.session_state['event_markers'] = []
        st.session_state['event_markers'].append({
            'time': datetime.now(),
            'event': f'HRV 更新: {hrv_input}',
            'amplitude': 0
        })

    st.subheader("事件")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("☕ 喝咖啡"):
            # 咖啡因生效：暂时降低睡眠压力
            st.session_state['engine'].state[0] *= 0.6 
            st.toast("咖啡因生效：睡眠压力暂时降低")
            # 记录事件
            st.session_state.setdefault('event_markers', []).append({
                'time': datetime.now(), 'event': '喝咖啡', 'amplitude': -0.5
            })
            
    with col2:
        if st.button("🤯 压力事件"):
            st.session_state['engine'].apply_event('stress_event')
            st.toast("受到压力冲击！")
            st.session_state.setdefault('event_markers', []).append({
                'time': datetime.now(), 'event': '压力事件', 'amplitude': -1.0
            })
            
    with col1:
         if st.button("🏃 运动"):
            st.session_state['engine'].apply_event('exercise')
            st.toast("运动释放内啡肽！")
            st.session_state.setdefault('event_markers', []).append({
                'time': datetime.now(), 'event': '运动', 'amplitude': 1.0
            })
            
    with col2:
        if st.button("🧘 冥想"):
            # 冥想增加阻尼，减缓速度
            st.session_state['engine'].state[2] = 0 # 速度归零
            st.session_state['engine'].params['c'] += 2.0
            st.toast("系统强制平静 (阻尼增加)")
            st.session_state.setdefault('event_markers', []).append({
                'time': datetime.now(), 'event': '冥想', 'amplitude': 0.2
            })

    st.divider()
    
    # 睡眠开关
    is_sleeping = st.toggle("正在睡眠模式", value=st.session_state['engine'].is_asleep)
    if is_sleeping != st.session_state['engine'].is_asleep:
        if is_sleeping:
            st.session_state['engine'].apply_event('sleep_start')
        else:
            st.session_state['engine'].apply_event('sleep_end')
        st.rerun()
        # 记录睡眠切换事件
        st.session_state.setdefault('event_markers', []).append({
            'time': datetime.now(), 'event': 'sleep_start' if is_sleeping else 'sleep_end', 'amplitude': 0
        })

    st.subheader("自定义事件 (AI分析)")
    custom_event = st.text_input("描述事件 (例如: 喝咖啡, 运动, 压力事件)")
    if st.button("分析事件"):
        with st.spinner("AI正在分析事件影响..."):
            hrv = st.session_state['engine'].params['c']  # Use current HRV as input
            feedback = st.session_state['feedback_data'][-5:]  # 最多5条反馈

            # 根据用户选择的模型调用相应的API
            if st.session_state['ai_model'] == 'Google Gemini':
                logger.info(f"🔄 切换到Google Gemini模型")
                analysis = analyze_event_with_gemini(custom_event, hrv, feedback, logger)
            else:
                analysis = analyze_event_with_deepseek(custom_event, hrv, feedback, logger)

            if analysis and isinstance(analysis, dict) and 'amplitude' in analysis:
                try:
                    amplitude = float(analysis.get('amplitude', 0))
                    duration = float(analysis.get('duration', 1))
                    param_adjustments = analysis.get('parameters', {})
                    explanation = analysis.get('explanation', '')

                    # Apply the impact to the model
                    st.session_state['engine'].state[2] += amplitude  # Adjust velocity
                    logger.info(f"📊 应用参数调整...")
                    
                    # Apply parameter adjustments with bounds checking
                    if isinstance(param_adjustments, dict):
                        for param, value in param_adjustments.items():
                            if param in st.session_state['engine'].params:
                                try:
                                    st.session_state['engine'].params[param] = float(value)
                                except (ValueError, TypeError):
                                    pass

                    # Display the analysis result
                    st.success("✅ 事件分析完成")
                    st.info("**AI分析结果:**")
                    st.write(f"**事件**: {custom_event}")
                    st.write(f"**影响幅度**: {amplitude:+.2f}")
                    st.write(f"**持续时间**: {duration:.1f} 小时")
                    if explanation:
                        st.write(f"**分析说明**: {explanation}")
                    
                    with st.expander("参数调整详情"):
                        st.json(param_adjustments)

                    # Add markers to the chart (use actual datetime for x-axis)
                    if 'event_markers' not in st.session_state:
                        st.session_state['event_markers'] = []
                    marker_time = datetime.now()
                    st.session_state['event_markers'].append({
                        'time': marker_time,
                        'event': custom_event,
                        'amplitude': amplitude
                    })

                    st.toast("✨ 图表已更新，事件标记已添加！")
                except Exception as e:
                    st.error(f"处理分析结果出错: {e}")
            else:
                st.error("❌ 无法分析事件，请检查网络连接或稍后再试。")
                if analysis:
                    with st.expander("调试信息"):
                        st.write("返回数据:", analysis)

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
    
    # 记录数据用于绘图（使用实际时间作为横轴）
    mood, base, x, S = st.session_state['engine'].get_mood_value(sim_time_now)
    now_dt = datetime.now()
    st.session_state['history']['time'].append(now_dt)
    st.session_state['history']['mood'].append(mood)
    st.session_state['history']['baseline'].append(base)
    
    # 保持历史数据不无限增长 (最近48小时，假设每10分钟记录一次 => 288点)
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
        hovertemplate='<b>时间</b>: %{x|%Y-%m-%d %H:%M:%S}<br><b>心情值</b>: %{y:.2f}<extra></extra>'
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
        hovertemplate='<b>时间</b>: %{x|%Y-%m-%d %H:%M:%S}<br><b>基线</b>: %{y:.2f}<extra></extra>'
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
    
    # 添加事件标记
    if 'event_markers' in st.session_state and st.session_state['event_markers']:
        for marker in st.session_state['event_markers']:
            marker_time = marker['time']
            marker_event = marker['event']
            marker_amplitude = marker['amplitude']

            # 在图表上添加竖线标记（marker_time 为 datetime）
            fig.add_vline(
                x=marker_time,
                line_dash="dash",
                line_color="rgba(255, 152, 0, 0.7)",
                annotation_text=f"📍 {marker_event[:10]}",
                annotation_position="top",
                annotation_font_size=10,
                annotation_font_color="orange"
            )

            # 找到与事件时间最接近的历史点用于标记 y 值
            y_val = 0
            try:
                if times:
                    closest_idx = min(range(len(times)), key=lambda i: abs((times[i] - marker_time).total_seconds()))
                    y_val = moods[closest_idx]
            except Exception:
                y_val = 0

            # 添加事件标记点
            fig.add_trace(go.Scatter(
                x=[marker_time],
                y=[y_val],
                mode='markers',
                marker=dict(size=12, color='orange', symbol='star'),
                name=f"事件: {marker_event[:15]}",
                hovertemplate=f"<b>事件</b>: {marker_event}<br><b>幅度</b>: {marker_amplitude:+.2f}<extra></extra>",
                showlegend=False
            ))
    
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

# --- 6. AI日志面板 ---
st.divider()
st.subheader("🔍 AI分析过程日志")

# 创建日志显示面板
col_log1, col_log2 = st.columns([3, 1])

with col_log1:
    log_placeholder = st.empty()

with col_log2:
    if st.button("🗑️ 清空日志"):
        st.session_state['logger'].logs = []
        st.rerun()

# 获取日志并显示
logs = logger.get_logs()

if logs:
    # 创建日志表格数据
    log_data = []
    for log in reversed(logs[-20:]):  # 显示最近20条日志
        level = log['level']
        
        # 为不同级别的日志设置颜色标记
        if level == "ERROR":
            icon = "❌"
            color = "#FF6B6B"
        elif level == "SUCCESS":
            icon = "✅"
            color = "#51CF66"
        elif level == "WARNING":
            icon = "⚠️"
            color = "#FFD93D"
        else:
            icon = "ℹ️"
            color = "#6C63FF"
        
        log_data.append({
            '时间': log['timestamp'],
            '等级': f"{icon} {level}",
            '信息': log['message']
        })
    
    # 显示为表格
    with log_placeholder.container():
        st.dataframe(
            pd.DataFrame(log_data),
            width='stretch',
            height=300
        )
else:
    with log_placeholder.container():
        st.info("📭 暂无日志，请先执行AI分析")

# 详细日志导出功能
st.subheader("📥 日志导出")
col_export1, col_export2 = st.columns(2)

with col_export1:
    if st.button("📄 导出为CSV"):
        if logs:
            df_logs = pd.DataFrame([
                {
                    '时间': log['timestamp'],
                    '等级': log['level'],
                    '信息': log['message']
                }
                for log in logs
            ])
            csv = df_logs.to_csv(index=False)
            st.download_button(
                label="⬇️ 下载CSV文件",
                data=csv,
                file_name=f"ai_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        else:
            st.warning("没有日志数据可导出")

with col_export2:
    if st.button("📋 导出为JSON"):
        if logs:
            json_str = json.dumps(logs, ensure_ascii=False, indent=2)
            st.download_button(
                label="⬇️ 下载JSON文件",
                data=json_str,
                file_name=f"ai_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
        else:
            st.warning("没有日志数据可导出")

# 实时更新图表（使用 session history，非阻塞）
st.title("实时更新图表")
chart_placeholder = st.empty()

# 从 session history 绘制最新的心情轨迹（随 autorefresh 更新）
def render_live_chart():
    times = st.session_state['history']['time']
    moods = st.session_state['history']['mood']
    baselines = st.session_state['history']['baseline']

    if not times:
        chart_placeholder.info("等待数据更新中（历史为空）...")
        return

    fig_live = go.Figure()
    fig_live.add_trace(go.Scatter(
        x=times, y=moods, name='Mood (Total)', mode='lines+markers',
        line=dict(color='rgba(38, 166, 154, 1)', width=2)
    ))
    fig_live.add_trace(go.Scatter(
        x=times, y=baselines, name='Baseline', mode='lines',
        line=dict(color='rgba(239, 83, 80, 1)', width=1)
    ))

    # 绘制事件标记（如果有）
    for marker in st.session_state.get('event_markers', []):
        t = marker.get('time')
        ev = marker.get('event')
        amp = marker.get('amplitude', 0)
        try:
            y_val = 0
            if times:
                closest_idx = min(range(len(times)), key=lambda i: abs((times[i] - t).total_seconds()))
                y_val = moods[closest_idx]
            fig_live.add_vline(x=t, line_dash='dash', line_color='rgba(255,152,0,0.7)')
            fig_live.add_trace(go.Scatter(x=[t], y=[y_val], mode='markers', marker=dict(size=10, color='orange', symbol='star'),
                                         name=f'事件: {ev}', hovertemplate=f"{ev}<br>幅度: {amp}"))
        except Exception:
            pass

    fig_live.update_layout(title='实时心情曲线', xaxis_title='实际时间', yaxis_title='心情值', height=420)
    chart_placeholder.plotly_chart(fig_live, width='stretch')

render_live_chart()

# 添加保存事件数据和建模公式参数的功能
# 定义保存路径
SAVE_DIR = "saved_data"
os.makedirs(SAVE_DIR, exist_ok=True)

def save_event_data(event_data, filename="event_data.json"):
    """保存事件数据到JSON文件"""
    filepath = os.path.join(SAVE_DIR, filename)
    # 将 datetime 转为 ISO 字符串以便JSON序列化
    def _serialize(obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        raise TypeError("Type not serializable")

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(event_data, f, ensure_ascii=False, indent=4, default=_serialize)
    st.sidebar.success(f"事件数据已保存到 {filepath}")

def save_model_params(params, filename="model_params.json"):
    """保存建模公式参数到JSON文件"""
    filepath = os.path.join(SAVE_DIR, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(params, f, ensure_ascii=False, indent=4)
    st.sidebar.success(f"建模参数已保存到 {filepath}")

def save_session_data(filename="session_data.json"):
    """保存整个会话数据（history + event_markers + params）到JSON"""
    filepath = os.path.join(SAVE_DIR, filename)
    data = {
        'history': {
            'time': [t.isoformat() for t in st.session_state['history']['time']],
            'mood': st.session_state['history']['mood'],
            'baseline': st.session_state['history']['baseline']
        },
        'event_markers': [
            {**{k: (v.isoformat() if isinstance(v, datetime) else v) for k, v in m.items()}}
            for m in st.session_state.get('event_markers', [])
        ],
        'params': st.session_state['engine'].params
    }
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    st.sidebar.success(f"会话数据已保存到 {filepath}")

def load_session_data(filename="session_data.json"):
    filepath = os.path.join(SAVE_DIR, filename)
    if not os.path.exists(filepath):
        st.sidebar.warning(f"未找到文件: {filepath}")
        return
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 恢复 history
    hist = data.get('history', {})
    times = hist.get('time', [])
    moods = hist.get('mood', [])
    baselines = hist.get('baseline', [])
    try:
        st.session_state['history'] = {
            'time': [datetime.fromisoformat(t) for t in times],
            'mood': moods,
            'baseline': baselines
        }
    except Exception:
        st.session_state['history'] = {'time': [], 'mood': [], 'baseline': []}

    # 恢复 events
    events = data.get('event_markers', [])
    recovered = []
    for e in events:
        e_copy = e.copy()
        if isinstance(e_copy.get('time'), str):
            try:
                e_copy['time'] = datetime.fromisoformat(e_copy['time'])
            except Exception:
                pass
        recovered.append(e_copy)
    st.session_state['event_markers'] = recovered

    # 恢复 params
    params = data.get('params')
    if params:
        st.session_state['engine'].params = params
    st.sidebar.success(f"会话数据已从 {filepath} 加载")

# 示例：保存当前事件数据和参数
if st.sidebar.button("保存数据"):
    # 保存会话数据（history + events + params）
    save_session_data()
    # 另外也保存模型参数单独文件
    save_model_params(silicon_flow_model.params)

if st.sidebar.button("加载会话数据"):
    load_session_data()

if st.sidebar.button("导出会话为CSV"):
    # 导出 history 和 events 为 CSV 并提供下载
    hist = st.session_state.get('history', {'time': [], 'mood': [], 'baseline': []})
    if hist['time']:
        df_hist = pd.DataFrame({
            'time': [t.isoformat() for t in hist['time']],
            'mood': hist['mood'],
            'baseline': hist['baseline']
        })
        csv_hist = df_hist.to_csv(index=False)
        st.sidebar.download_button(label='⬇️ 下载 history CSV', data=csv_hist, file_name='history.csv')
    else:
        st.sidebar.warning('历史数据为空，无法导出')

    events = st.session_state.get('event_markers', [])
    if events:
        df_evt = pd.DataFrame([{
            'time': (e['time'].isoformat() if isinstance(e.get('time'), datetime) else e.get('time')),
            'event': e.get('event'),
            'amplitude': e.get('amplitude')
        } for e in events])
        csv_evt = df_evt.to_csv(index=False)
        st.sidebar.download_button(label='⬇️ 下载 events CSV', data=csv_evt, file_name='events.csv')
    else:
        st.sidebar.info('暂无事件可导出')

if st.sidebar.button('备份会话数据（带时间戳）'):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    save_session_data(filename=f'session_data_{ts}.json')
    st.sidebar.success('已备份会话数据')