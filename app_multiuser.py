"""
主应用 - Bio-Mood Digital Twin (多用户在线版本)
集成用户认证、数据持久化、云端同步功能
"""

import streamlit as st
import time
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.graph_objects as go

# 导入自定义模块
from bio_model import BioEngine, StreamlitLogger, analyze_event_with_deepseek, analyze_event_with_gemini
from db_module import Database
from auth import AuthManager

# ===== 页面配置 =====
st.set_page_config(
    page_title="Bio-Mood Digital Twin",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式（简化版，避免主题配置错误）
st.markdown("""
<style>
    /* 主容器样式 */
    .main {
        padding-top: 1rem;
    }
    
    /* 按钮样式 */
    .stButton > button {
        border-radius: 8px;
        border: none;
        font-weight: bold;
    }
    
    /* 标题样式 */
    h1 {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ===== 初始化 =====

# 初始化数据库
if 'db' not in st.session_state:
    st.session_state.db = Database(db_type="sqlite", db_path="bio_mood.db")

# 初始化认证管理器
if 'auth_manager' not in st.session_state:
    st.session_state.auth_manager = AuthManager(st.session_state.db)

db = st.session_state.db
auth_manager = st.session_state.auth_manager

# 初始化会话状态
auth_manager.init_session_state()

# ===== 主程序逻辑 =====

def main():
    """主应用程序"""
    
    # 如果未认证，显示登录界面
    if not st.session_state.authenticated:
        # 检查是否在注册页面
        if 'page' not in st.session_state:
            st.session_state.page = "login"
        
        if st.session_state.page == "register":
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                auth_manager.register_page()
                
                col_back1, col_back2, col_back3 = st.columns([1, 2, 1])
                with col_back2:
                    if st.button("← 返回登录", width='stretch'):
                        st.session_state.page = "login"
                        st.rerun()
        else:
            auth_manager.login_page()
        return
    
    # ===== 已认证用户的主界面 =====
    
    # 显示用户资料和登出按钮
    auth_manager.show_user_profile()
    
    # 初始化用户特定的引擎和数据
    if 'engine' not in st.session_state:
        # 从数据库加载用户的个性化参数
        user_params = db.get_user_parameters(st.session_state.user_id)
        
        engine = BioEngine()
        if user_params:
            engine.params.update(user_params)
        
        st.session_state['engine'] = engine
        st.session_state['start_real_time'] = time.time()
        st.session_state['history'] = {'time': [], 'mood': [], 'baseline': []}
        st.session_state['feedback_data'] = []
        st.session_state['event_markers'] = []
        st.session_state['logger'] = StreamlitLogger()
    
    # 页面标题
    st.title("🧠 情绪量化生物数字孪生")
    st.markdown(f"欢迎回来，**{st.session_state.username}** 👋")
    st.markdown("基于 **Borbély双过程模型** 与 **阻尼动力学** 的实时情绪模拟器")
    
    # 侧边栏：事件输入
    with st.sidebar:
        st.header("🎮 施加环境刺激")
        
        # AI模型选择
        if 'ai_model' not in st.session_state:
            st.session_state['ai_model'] = 'SiliconFlow'
        
        st.subheader("🤖 AI大模型选择")
        ai_model = st.radio(
            "选择AI大模型",
            options=['SiliconFlow (Qwen)', 'Google Gemini'],
            index=0 if st.session_state['ai_model'] == 'SiliconFlow' else 1
        )
        st.session_state['ai_model'] = ai_model
        
        st.divider()
        
        # 生理数据
        st.subheader("生理数据")
        hrv_input = st.slider("当前 HRV (rMSSD)", 10, 100, 50)
        if st.button("更新 HRV"):
            st.session_state['engine'].apply_event('hrv_update', hrv_input)
            st.success(f"HRV参数已映射: k={st.session_state['engine'].params['k']:.1f}, c={st.session_state['engine'].params['c']:.1f}")
        
        # 快速事件按钮
        st.subheader("快速事件")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("☕ 喝咖啡"):
                st.session_state['engine'].state[0] *= 0.6
                db.add_event(st.session_state.user_id, 'caffeine', '喝咖啡')
                st.toast("咖啡因生效：睡眠压力暂时降低")
            
            if st.button("🏃 运动"):
                st.session_state['engine'].apply_event('exercise')
                db.add_event(st.session_state.user_id, 'exercise', '运动')
                st.toast("运动释放内啡肽！")
        
        with col2:
            if st.button("🤯 压力事件"):
                st.session_state['engine'].apply_event('stress_event')
                db.add_event(st.session_state.user_id, 'stress', '压力事件')
                st.toast("受到压力冲击！")
            
            if st.button("🧘 冥想"):
                st.session_state['engine'].state[2] = 0
                st.session_state['engine'].params['c'] += 2.0
                db.add_event(st.session_state.user_id, 'meditation', '冥想')
                st.toast("系统强制平静 (阻尼增加)")
        
        st.divider()
        
        # 睡眠切换
        is_sleeping = st.toggle("正在睡眠模式", value=st.session_state['engine'].is_asleep)
        if is_sleeping != st.session_state['engine'].is_asleep:
            if is_sleeping:
                st.session_state['engine'].apply_event('sleep_start')
                db.add_event(st.session_state.user_id, 'sleep_start', '开始睡眠')
            else:
                st.session_state['engine'].apply_event('sleep_end')
                db.add_event(st.session_state.user_id, 'sleep_end', '睡眠结束')
            st.rerun()
        
        # 自定义事件分析
        st.divider()
        st.subheader("自定义事件 (AI分析)")
        
        # 初始化AI分析状态
        if 'ai_analysis_status' not in st.session_state:
            st.session_state['ai_analysis_status'] = None
            st.session_state['ai_analysis_result'] = None
        
        custom_event = st.text_input("描述事件", placeholder="例如: 和朋友聚会, 工作失败等", key="custom_event_input")
        
        col_analyze, col_clear = st.columns([2, 1])
        
        with col_analyze:
            if st.button("分析事件", width='stretch'):
                if custom_event:
                    st.session_state['ai_analysis_status'] = 'analyzing'
                else:
                    st.session_state['ai_analysis_status'] = 'empty'
        
        with col_clear:
            if st.button("清除", width='stretch'):
                st.session_state['ai_analysis_status'] = None
                st.session_state['ai_analysis_result'] = None
        
        # 显示分析过程
        st.divider()
        st.markdown("**📊 AI分析状态**")
        
        if st.session_state['ai_analysis_status'] == 'analyzing':
            with st.spinner("AI正在分析事件影响..."):
                try:
                    hrv = st.session_state['engine'].params['c']
                    feedback = st.session_state['feedback_data'][-5:]
                    logger = st.session_state['logger']
                    
                    # 调用AI分析
                    if st.session_state['ai_model'] == 'Google Gemini':
                        analysis = analyze_event_with_gemini(custom_event, hrv, feedback, logger)
                    else:
                        analysis = analyze_event_with_deepseek(custom_event, hrv, feedback, logger)
                    
                    if analysis and 'amplitude' in analysis:
                        amplitude = float(analysis.get('amplitude', 0))
                        duration = float(analysis.get('duration', 1))
                        explanation = analysis.get('explanation', '')
                        
                        # 应用事件影响
                        st.session_state['engine'].state[2] += amplitude
                        
                        # 保存到数据库
                        db.add_event(
                            st.session_state.user_id,
                            'ai_analysis',
                            custom_event,
                            amplitude,
                            duration,
                            analysis
                        )
                        
                        # 记录事件标记
                        if 'event_markers' not in st.session_state:
                            st.session_state['event_markers'] = []
                        
                        current_time = st.session_state['engine'].last_update_time
                        st.session_state['event_markers'].append({
                            'time': current_time,
                            'event': custom_event,
                            'amplitude': amplitude,
                            'duration': duration,
                            'color': 'green' if amplitude > 0 else 'red'
                        })
                        
                        # 保存结果
                        st.session_state['ai_analysis_status'] = 'success'
                        st.session_state['ai_analysis_result'] = {
                            'amplitude': amplitude,
                            'duration': duration,
                            'explanation': explanation,
                            'event': custom_event
                        }
                    else:
                        st.session_state['ai_analysis_status'] = 'error'
                except Exception as e:
                    st.session_state['ai_analysis_status'] = 'error'
        
        # 显示分析结果
        if st.session_state['ai_analysis_status'] == 'success' and st.session_state['ai_analysis_result']:
            result = st.session_state['ai_analysis_result']
            st.success("✅ 分析完成!")
            
            col_res1, col_res2, col_res3 = st.columns(3)
            with col_res1:
                st.metric("事件", result['event'][:15])
            with col_res2:
                affect = "↑ 积极" if result['amplitude'] > 0 else "↓ 消极"
                st.metric("影响", f"{result['amplitude']:+.2f}", affect)
            with col_res3:
                st.metric("持续", f"{result['duration']:.1f}h")
            
            if result['explanation']:
                st.info(f"💡 {result['explanation']}")
            
            st.success("✨ 事件已标记在图表上")
        
        elif st.session_state['ai_analysis_status'] == 'error':
            st.error("❌ 分析失败，请检查网络或API配置")
        
        elif st.session_state['ai_analysis_status'] == 'empty':
            st.warning("⚠️ 请输入事件描述")
        
        else:
            st.info("💭 输入事件描述，点击分析获得AI评估")
    
    # ===== 核心循环 =====
    # 使用Streamlit的自动刷新而非st_autorefresh库（避免频繁刷新问题）
    # 时间推进
    current_real_time = time.time()
    time_scale = 10 * 60  # 1秒 = 10分钟模拟时间
    elapsed_real = current_real_time - st.session_state['start_real_time']
    sim_time_now = 8.0 + (elapsed_real * time_scale / 3600.0)
    
    # 引擎步进
    dt = sim_time_now - st.session_state['engine'].last_update_time
    if dt > 0:
        st.session_state['engine'].step(dt)
        
        mood, base, x, S = st.session_state['engine'].get_mood_value(sim_time_now)
        st.session_state['history']['time'].append(sim_time_now)
        st.session_state['history']['mood'].append(mood)
        st.session_state['history']['baseline'].append(base)
        
        # 每10步保存一次到数据库
        if len(st.session_state['history']['time']) % 10 == 0:
            db.add_mood_record(
                st.session_state.user_id,
                mood,
                baseline=base,
                sleep_pressure=S,
                hrv_value=st.session_state['engine'].params['c'],
                parameters=st.session_state['engine'].params.copy()
            )
        
        # 限制历史数据
        if len(st.session_state['history']['time']) > 288:
            for k in st.session_state['history']:
                st.session_state['history'][k].pop(0)
    
    # ===== 仪表盘 =====
    mood_now, base_now, x_now, S_now = st.session_state['engine'].get_mood_value(sim_time_now)
    
    col_a, col_b, col_c, col_d = st.columns(4)
    col_a.metric("当前心情值", f"{mood_now:.2f}", delta=f"{x_now:.2f} (偏差)")
    col_b.metric("能量基线", f"{base_now:.2f}")
    col_c.metric("睡眠压力", f"{S_now:.2f}")
    col_d.metric("模拟时间", f"{int(sim_time_now)%24:02d}:{int((sim_time_now%1)*60):02d}")
    
    # ===== 曲线图 =====
    st.subheader("📈 心情动力学曲线")
    
    if len(st.session_state['history']['time']) > 0:
        fig = go.Figure()
        
        times = st.session_state['history']['time']
        moods = st.session_state['history']['mood']
        baselines = st.session_state['history']['baseline']
        
        # 主曲线
        fig.add_trace(go.Scatter(
            x=times, y=moods,
            name='Mood (Total)',
            mode='lines',
            line=dict(color='rgba(38, 166, 154, 1)', width=3),
            fill='tozeroy',
            fillcolor='rgba(38, 166, 154, 0.2)'
        ))
        
        fig.add_trace(go.Scatter(
            x=times, y=baselines,
            name='Baseline (Bio-Rhythm)',
            mode='lines',
            line=dict(color='rgba(239, 83, 80, 1)', width=2, dash='dash')
        ))
        
        fig.add_hline(y=0, line_dash="dash", line_color="rgba(150, 150, 150, 0.3)", annotation_text="基准线")
        
        # 添加事件标记（增强版）
        if 'event_markers' in st.session_state and st.session_state['event_markers']:
            for i, marker in enumerate(st.session_state['event_markers']):
                marker_time = marker['time']
                marker_event = marker['event']
                amplitude = marker['amplitude']
                
                # 根据影响确定颜色和符号
                if amplitude > 0:
                    marker_color = 'rgba(76, 175, 80, 0.8)'  # 绿色：积极
                    marker_symbol = '▲'
                elif amplitude < 0:
                    marker_color = 'rgba(244, 67, 54, 0.8)'   # 红色：消极
                    marker_symbol = '▼'
                else:
                    marker_color = 'rgba(255, 193, 7, 0.8)'   # 黄色：中性
                    marker_symbol = '●'
                
                # 竖线标记
                fig.add_vline(
                    x=marker_time,
                    line_dash="dash",
                    line_color=marker_color,
                    line_width=2,
                    annotation_text=f"{marker_symbol} {marker_event[:8]}",
                    annotation_position="top",
                    annotation_font=dict(size=10, color=marker_color)
                )
        
        fig.update_layout(
            title="实时心情变化曲线 (事件自动标记)",
            xaxis_title='模拟时间 (小时)',
            yaxis_title='心情值',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            paper_bgcolor='white',
            hovermode='x unified',
            height=500,
            showlegend=True,
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )
        
        st.plotly_chart(fig, width='stretch')
        
        # 显示事件列表
        if 'event_markers' in st.session_state and st.session_state['event_markers']:
            st.markdown("#### 📍 标记事件列表")
            event_list = []
            for marker in st.session_state['event_markers']:
                affect = "📈 积极" if marker['amplitude'] > 0 else "📉 消极"
                event_list.append({
                    '时间': f"{marker['time']:.2f}h",
                    '事件': marker['event'],
                    '影响': f"{marker['amplitude']:+.2f}",
                    '类型': affect
                })
            
            event_df = pd.DataFrame(event_list)
            st.dataframe(event_df, width='stretch', hide_index=True)
    
    # ===== 诊断建议 =====
    st.subheader("🩺 实时生物反馈与建议")
    
    advice_list, state_tags = st.session_state['engine'].get_diagnosis()
    
    if state_tags:
        cols = st.columns(len(state_tags))
        for idx, tag in enumerate(state_tags):
            with cols[idx % len(cols)]:
                if "积极" in tag:
                    st.success(f"✨ {tag}")
                elif "疲劳" in tag:
                    st.error(f"🔴 {tag}")
                elif "反刍" in tag:
                    st.warning(f"🟠 {tag}")
                else:
                    st.info(f"ℹ️ {tag}")
    
    st.divider()
    
    for advice in advice_list:
        if "紧急" in advice or "强效" in advice:
            st.error(advice)
        elif "严重" in advice:
            st.warning(advice)
        elif "建议" in advice:
            st.info(advice)
        elif "积极" in advice:
            st.success(advice)
        else:
            st.markdown(advice)
    
    # ===== 数据中心 =====
    st.divider()
    st.subheader("📊 我的数据中心")
    
    tab1, tab2, tab3, tab4 = st.tabs(["📈 统计分析", "📝 心情历史", "📅 事件记录", "⚙️ 参数设置"])
    
    with tab1:
        st.markdown("### 心情统计")
        
        # 时间范围选择
        col1, col2, col3 = st.columns(3)
        with col1:
            days = st.selectbox("选择时间范围", [7, 14, 30], index=0)
        
        # 获取统计数据
        stats = db.get_mood_statistics(st.session_state.user_id, days=days)
        
        col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
        col_stat1.metric("平均心情值", f"{stats['average']:.2f}")
        col_stat2.metric("最高值", f"{stats['max']:.2f}")
        col_stat3.metric("最低值", f"{stats['min']:.2f}")
        col_stat4.metric("记录数", f"{stats['count']}")
        
        st.markdown("---")
        
        # 心情分布图
        mood_history = db.get_mood_history(st.session_state.user_id, days=days, limit=100)
        
        if mood_history:
            mood_values = [m['mood_value'] for m in mood_history]
            
            fig_dist = go.Figure()
            fig_dist.add_trace(go.Histogram(x=mood_values, nbinsx=20, name='Mood Distribution'))
            fig_dist.update_layout(
                title="心情值分布",
                xaxis_title="心情值",
                yaxis_title="频次",
                height=400
            )
            st.plotly_chart(fig_dist, width='stretch')
    
    with tab2:
        st.markdown("### 心情记录")
        
        mood_history = db.get_mood_history(st.session_state.user_id, limit=50)
        
        if mood_history:
            df_mood = pd.DataFrame([
                {
                    '时间': m['timestamp'][:16],
                    '心情值': f"{m['mood_value']:.2f}",
                    '基线': f"{m['baseline']:.2f}" if m['baseline'] else "-",
                    '睡眠压力': f"{m['sleep_pressure']:.2f}" if m['sleep_pressure'] else "-",
                    '备注': m['notes'] or "-"
                }
                for m in mood_history
            ])
            
            st.dataframe(df_mood, width='stretch')
            
            # 导出功能
            csv = df_mood.to_csv(index=False)
            st.download_button(
                "📥 下载CSV",
                csv,
                f"mood_records_{datetime.now().strftime('%Y%m%d')}.csv",
                "text/csv"
            )
        else:
            st.info("暂无心情记录")
    
    with tab3:
        st.markdown("### 事件记录")
        
        events = db.get_events(st.session_state.user_id, limit=50)
        
        if events:
            df_events = pd.DataFrame([
                {
                    '时间': e['timestamp'][:16],
                    '事件类型': e['event_type'],
                    '描述': e['event_description'] or "-",
                    '影响': f"{e['amplitude']:+.2f}" if e['amplitude'] else "-"
                }
                for e in events
            ])
            
            st.dataframe(df_events, width='stretch')
        else:
            st.info("暂无事件记录")
    
    with tab4:
        st.markdown("### 参数个性化设置")
        
        user_params = db.get_user_parameters(st.session_state.user_id)
        
        if user_params:
            st.info("💡 这些参数基于您的使用数据自动调整，也可以手动修改")
            
            col1, col2 = st.columns(2)
            
            with col1:
                tau_r = st.slider("tau_r (睡眠积累时间)", 15.0, 22.0, user_params['tau_r'], step=0.1)
                tau_d = st.slider("tau_d (睡眠衰减时间)", 3.0, 10.0, user_params['tau_d'], step=0.1)
                k = st.slider("k (情绪刚度)", 2.0, 30.0, user_params['k'], step=0.1)
            
            with col2:
                c = st.slider("c (情绪阻尼)", 0.5, 10.0, user_params['c'], step=0.1)
                circadian_amplitude = st.slider("circadian_amplitude", 0.1, 0.5, user_params['circadian_amplitude'], step=0.01)
                base_hrv = st.slider("base_hrv (基准HRV)", 20.0, 100.0, user_params['base_hrv'], step=1.0)
            
            if st.button("💾 保存参数设置"):
                new_params = {
                    'tau_r': tau_r,
                    'tau_d': tau_d,
                    'k': k,
                    'c': c,
                    'circadian_amplitude': circadian_amplitude,
                    'base_hrv': base_hrv
                }
                
                success, msg = db.update_user_parameters(st.session_state.user_id, new_params)
                
                if success:
                    # 更新本地引擎参数
                    st.session_state['engine'].params.update(new_params)
                    st.success("✅ 参数已保存！")
                else:
                    st.error(f"❌ {msg}")

if __name__ == "__main__":
    main()
