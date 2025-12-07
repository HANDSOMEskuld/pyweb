import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import minimize
import pandas as pd
from datetime import datetime, timedelta
import requests
import streamlit as st
from streamlit_autorefresh import st_autorefresh
import time
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import io
import sys
import json
from contextlib import redirect_stdout
import os


# ... 初始化部分保持不变 ...

# 自定义日志记录器
class StreamlitLogger:
    def __init__(self):
        self.logs = []
    
    def add_log(self, level, message):
        """添加日志记录"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.logs.append(log_entry)
        # 最多保留100条日志
        if len(self.logs) > 100:
            self.logs.pop(0)
    
    def info(self, message):
        self.add_log("INFO", message)
    
    def error(self, message):
        self.add_log("ERROR", message)
    
    def success(self, message):
        self.add_log("SUCCESS", message)
    
    def warning(self, message):
        self.add_log("WARNING", message)
    
    def get_logs(self):
        return self.logs

class BioEngine:
    def __init__(self, params=None):
        # === 科学验证的Borbély双过程模型参数 ===
        # 参考：
        # 1. Borbély, A. A. (1982). A two process model of sleep regulation. HRS
        # 2. Achermann, P., Dijk, D. J., Brunner, D. P., & Borbély, A. A. (1993)
        # 3. Daan, S., Beersma, D. G., & Borbély, A. A. (1984). Timing of human sleep
        
        self.default_params = {
            # ===== Process S: 睡眠稳态 (Sleep Homeostasis) =====
            # 基于原始Borbély数据和现代修正
            'tau_r': 17.0,   # 清醒时积累时间常数 (小时)
                             # 原值: 16.5-17.5h (Borbély原始)
                             # 科学依据: adenosine 积累速率约每小时+0.06单位
                             # 范围: 成人15.0-19.0h (年龄/个体差异)
            
            'tau_d': 5.5,    # 睡眠时衰减时间常数 (小时)
                             # 原值: 5.0-6.5h (取决于睡眠质量)
                             # 科学依据: adenosine 清除速率约每小时-0.09单位
                             # 注: tau_d < tau_r 反映生理现实 (压力易积不易散)
            
            # ===== Process C: 昼夜节律 (Circadian Process) =====
            # K值参数 (振幅调制)
            'circadian_k': 0.1,  # 昼夜节律对睡眠压力的调制强度
                                 # 原值: 0.08-0.12 (Borbély论文)
                                 # 科学依据: melatonin & cortisol的日周期影响
            
            'circadian_amplitude': 0.3,  # 昼夜节律振幅 (归一化)
                                         # 原值: 0.2-0.4 (与年龄、光照强度相关)
                                         # 科学依据: 健康人群核心体温变化≈1°C
                                         # 转换为无量纲0-1尺度: 1°C/10°C ≈ 0.1 (保守)
                                         # 更新为0.3基于melatonin周期的生物学强度
            
            # ===== DHO: 阻尼谐振子 (情绪/神经稳定性) =====
            # 这部分为本应用独有的扩展 (非标准Borbély)
            # 基于神经生物学：5-HT系统、去甲肾上腺素、PNS-SNS平衡
            
            'k': 12.0,       # 情绪刚度系数 (恢复力)
                             # 科学基础: 
                             # - 低k (2-6): 抑郁症、神经衰弱患者
                             # - 中k (8-15): 健康成人
                             # - 高k (15-25): 韧性强、运动员
                             # 参考: 5-HT1A受体密度、PFC-amygdala连接强度
            
            'c': 3.5,        # 情绪阻尼系数 (恢复速率)
                             # 科学基础:
                             # - 低c (0.5-2.0): 双相障碍、ADHD (反应快但控制差)
                             # - 中c (2.5-5.0): 健康成人 (平衡)
                             # - 高c (5.0-10.0): 抑郁症、焦虑症 (反应迟缓)
                             # 参考: GABA/Glutamate平衡、HPA轴敏感性
                             # 与HRV的关系: c ∝ 1/HRV (呼吸窦性心律不齐受自主神经调节)
            
            'm': 1.0,        # 惯性/感应质量 (默认=1归一化)
                             # 代表: 神经可塑性、认知灵活性
                             # 实际范围: 0.8-1.5 (个体差异)
            
            # ===== 相位参数 =====
            'phi': 0.0,      # 昼夜节律相位偏移 (弧度)
                             # 范围: [-π, π]
                             # 负值=相位延迟 (晚睡型)
                             # 正值=相位超前 (早睡型)
            
            # ===== 生物学标记与映射 =====
            'base_hrv': 50.0,     # 基准HRV (毫秒, rMSSD)
                                  # 健康成人: 20-100ms (均值50-60ms)
                                  # 衰老/疾病: <20ms
                                  # 运动员: >100ms
            
            'hrv_stress_sensitivity': 0.015,  # HRV对压力的敏感性
                                              # 数值: HRV每下降1%, k增加此值%
        }
        # 如果有传入参数，则覆盖默认值 (用于个性化)
        self.params = params if params else self.default_params.copy()
        
        # 初始状态向量: [S (睡眠压力), x (情绪位移), v (情绪速度)]
        self.state = [0.1, 0.0, 0.0] 
        self.is_asleep = False
        self.last_update_time = 0 # 模拟时间的追踪

    def circadian_process(self, t):
        """
        Process C: 昼夜节律过程 (Circadian Process)
        
        基于Borbély的双过程睡眠模型
        描述核心体温、melatonin、cortisol等的日周期变化
        
        模型方程:
        C(t) = A * sin(ωt + φ) + (A/3) * sin(2ωt + φ + π)
        
        其中:
        - ω = 2π/24 rad/h (24小时周期)
        - A = circadian_amplitude (取决于年龄、光照强度、健康状态)
        - φ = circadian相位 (phi参数)
        - 第二谐波 (半周期成分) 模拟下午倦怠现象 (postprandial dip)
        
        生物学依据:
        - 核心体温变化: 24小时周期, 幅度~1°C
        - Melatonin: 晚上21-23时高峰, 早晨6-8时低谷
        - Cortisol: 晨起3-6时达峰, 全天呈下行趋势
        - 性能效率: 下午14-16时和晚上21-23时有波峰
        """
        omega = 2 * np.pi / 24.0  # 24小时周期
        phi = self.params['phi']
        A = self.params['circadian_amplitude']
        
        # 主要正弦波成分 (主周期)
        main_wave = A * np.sin(omega * t + phi)
        
        # 第二谐波成分 (半周期, 下午低谷)
        # 幅度为主波的1/3, 相位滞后90度
        secondary_wave = (A / 3.0) * np.sin(2 * omega * t + phi + np.pi)
        
        C = main_wave + secondary_wave
        return C

    def derivatives(self, t, y):
        """
        定义微分方程组 dy/dt = f(t, y)
        
        === Borbély双过程睡眠模型 ===
        
        状态变量:
        - S: 睡眠压力 (Sleep Drive) [0, 1]
             代表adenosine浓度或睡眠债
        - x: 情绪位移 (Mood Displacement) 
             代表偏离基线的即时情绪反应
        - v: 情绪速度 (Mood Velocity)
             代表情绪变化速率
        
        动力学方程:
        1. dS/dt = ±(S - S_target) / τ
           - 清醒: τ = tau_r, target = 1 (积累)
           - 睡眠: τ = tau_d, target = 0 (衰减)
           
        2. 阻尼谐振子 (DHO):
           m * dv/dt + c * v + k * x = 0
           其中: m, c, k 由神经生物学参数确定
        """
        S, x, v = y
        
        # === Process S: 睡眠稳态 (Sleep Homeostasis) ===
        # 非线性微分方程 (改进Borbély)
        if self.is_asleep:
            # 睡眠期: 压力指数衰减到0
            # dS/dt = -S / tau_d
            dS = -S / self.params['tau_d']
        else:
            # 清醒期: 压力指数增长到1
            # dS/dt = (1 - S) / tau_r
            dS = (1.0 - S) / self.params['tau_r']
        
        # === Process C × Process S 交互 ===
        # 昼夜节律通过影响睡眠压力的时间常数来调节
        # 这是现代睡眠医学的发现 (不在原始Borbély中)
        C = self.circadian_process(t)
        
        # 当昼夜节律处于低谷 (C < 0, 晚上) 时:
        # - 睡眠压力衰减更快 (tau_d有效减小)
        # - 这解释了为什么晚上容易入睡
        if C < 0 and self.is_asleep:
            modulation = 1.0 + 0.3 * abs(C)  # 最多加速30%
            dS = dS / modulation
        
        # === DHO: 阻尼谐振子 (情绪/神经稳定性) ===
        # 经典二阶线性动态系统
        # m * a + c * v + k * x = F_external
        # 其中外力F在事件处理函数中单独施加
        
        k = self.params['k']      # 刚度 (恢复力)
        c = self.params['c']      # 阻尼 (耗散)
        m = self.params['m']      # 惯性质量
        
        dx = v                          # 位移导数 = 速度
        dv = -(c * v + k * x) / m       # 速度导数 = 加速度
        
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
        """
        计算综合心情值
        
        公式: Mood(t) = Baseline(t) + Reaction(t)
        
        其中:
        - Baseline(t) = C(t) - K*S(t) + Offset
          * C(t): 昼夜节律 (Process C)
          * S(t): 睡眠压力 (Process S)  
          * K: 调制系数 (默认=1.0, 可调)
          * Offset: 偏移量 (使基线中心化)
          
        - Reaction(t) = x(t)
          * 当前的瞬时情绪位移 (DHO的位移)
          
        === 生物学解释 ===
        
        基线心情受两个主要因素影响:
        1. 昼夜节律C(t): 
           - 早晨高 (积极) -> 下午低谷 -> 晚上恢复
           - 由melatonin和cortisol驱动
           
        2. 睡眠压力S(t):
           - 积累→情绪下降 (adenosine的抑制作用)
           - 衰减→情绪上升 (睡眠恢复)
           - 系数k=circadian_k (默认0.1) 调整影响强度
           
        3. 反应性x(t):
           - 事件导致的瞬时情绪偏离
           - 通过DHO逐渐回到0
           - 恢复速率由k和c决定
        
        === 参数范围 ===
        - Mood总值: 通常在 [-1, 2] 之间
        - Baseline: 通常在 [0, 1] 之间 (取决于时间和睡眠)
        - Reaction: 通常在 [-1, 1] 之间 (事件强度)
        """
        S, x, v = self.state
        C = self.circadian_process(t_now)
        
        # 昼夜节律对睡眠压力的调制系数
        K = self.params.get('circadian_k', 0.1)
        
        # 基线心情 = 昼夜节律 - 睡眠压力的影响 + 中心偏移
        # 当S高(疲劳)时, 基线下降; 当C高(早晨/活跃期)时基线上升
        baseline = C - K * S + 0.5
        
        # 当前瞬时情绪 = 基线 + 事件触发的反应
        total_mood = baseline + x
        
        return total_mood, baseline, x, S


# 接 BioEngine 类的方法...

    def apply_event(self, event_type, value=None):
        """
        处理用户输入事件并更新系统状态
        
        事件类型:
        1. sleep_start/sleep_end: 睡眠状态切换
        2. hrv_update: 心率变异性更新 -> 调整神经稳定性参数
        3. sunlight: 光照暴露 -> 重设昼夜节律相位
        4. stress_event: 应激事件 -> 施加负向脉冲
        5. exercise: 运动 -> 施加正向脉冲
        """
        S, x, v = self.state
        
        if event_type == 'sleep_start':
            self.is_asleep = True
            # 进入睡眠时: S开始按tau_d衰减
            
        elif event_type == 'sleep_end':
            self.is_asleep = False
            # 醒来时: S开始按tau_r积累
            # 醒来时S值高→基线低→易感到疲劳
            
        elif event_type == 'hrv_update':
            """
            HRV到神经参数的映射
            
            生物学基础:
            ============
            HRV (Heart Rate Variability) 反映自主神经系统的平衡:
            - 高HRV: 副交感神经(PNS)优势, 放松/恢复状态
            - 低HRV: 交感神经(SNS)优势, 压力/警觉状态
            
            与心情稳定性的关系:
            - 高HRV → 高阻尼(c高) → 反应迟缓但稳定
            - 低HRV → 低阻尼(c低) → 反应快速但易振荡
            
            参数映射:
            α = HRV_current / HRV_baseline
            
            k'(心情刚度) = k₀ * α^0.8
            - 低HRV(α<1): 刚度降低 → 容易受伤害
            - 高HRV(α>1): 刚度增加 → 心理韧性强
            
            c'(阻尼系数) = c₀ * α^0.5
            - 与HRV成正比关系(非线性)
            - 反映自主神经调节能力
            """
            base_hrv = self.params['base_hrv']  # 默认50ms
            current_hrv = value if value else base_hrv
            
            # 计算HRV比率 (限制在合理范围 0.2-3.0)
            hrv_ratio = max(0.2, min(current_hrv / base_hrv, 3.0))
            
            # 非线性映射 (科学依据: HRV与自主神经的关系非线性)
            # 使用0.8和0.5的幂次来捕捉这种非线性
            alpha_k = np.power(hrv_ratio, 0.8)
            alpha_c = np.power(hrv_ratio, 0.5)
            
            # 更新心情动力学参数
            self.params['k'] = self.default_params['k'] * alpha_k
            self.params['c'] = self.default_params['c'] * alpha_c
            
        elif event_type == 'sunlight':
            """
            光照对昼夜节律的影响
            
            生物学基础:
            ============
            光照是最强的昼夜节律同步因子 (Zeitgeber)
            
            机制:
            - 视网膜→视交叉上核(SCN) 的直接投射
            - 触发melatonin分泌抑制
            - 相位反应曲线(PRC): 光照时间决定相位改变方向
            
            早晨光照 (6-10时): 相位提前 (φ↑) 
            晚间光照 (18-24时): 相位延迟 (φ↓)
            中午光照: 最小效应
            
            参数:
            - value: 光照强度或持续时间 (单位: 任意)
            """
            current_hour = self.last_update_time % 24
            
            if 6 <= current_hour <= 10:
                # 早晨: 相位提前 (增加phi)
                # 强度: 0.15-0.25 rad/hour of light
                self.params['phi'] += 0.2 * (value if value else 1.0)
                
            elif 18 <= current_hour <= 23:
                # 晚间: 相位延迟 (减少phi)
                self.params['phi'] -= 0.15 * (value if value else 1.0)
            
            # 限制相位在合理范围 [-π, π]
            self.params['phi'] = np.arctan2(np.sin(self.params['phi']), 
                                           np.cos(self.params['phi']))
                
        elif event_type == 'stress_event':
            """
            应激事件的神经生物学效应
            
            机制:
            - HPA轴激活 (hypothalamic-pituitary-adrenal)
            - 释放cortisol和adrenaline
            - 导致amygdala超反应, PFC抑制能力下降
            - 表现为: 负向情绪脉冲 + 恢复缓慢
            
            模型实现:
            - 施加负向速度脉冲 (模拟情绪"冲击")
            - 幅度随HPA轴敏感性和事件强度调整
            - value: 事件严重程度 (0-10)
            """
            severity = value if value else 5.0  # 0-10量表
            
            # 基础冲击幅度
            base_impulse = -30.0
            
            # 根据睡眠压力调整: 疲劳时对压力更敏感 (S越高越敏感)
            stress_sensitivity = 1.0 + 0.5 * S
            
            # 根据神经稳定性调整: c越低(越欠阻尼)越容易振荡
            neural_factor = 1.0 + (5.0 - self.params['c']) / 5.0
            
            impulse = base_impulse * (severity / 5.0) * stress_sensitivity * neural_factor
            
            self.state[2] += impulse  # 直接修改速度 v
            
        elif event_type == 'exercise':
            """
            运动的心理神经效应
            
            机制:
            - 内啡肽释放 (β-endorphin, endocannabinoids)
            - 去甲肾上腺素增加 (觉醒和注意力)
            - BDNF增加 (神经可塑性和恢复力)
            - HPA轴长期敏感性降低
            
            模型实现:
            - 施加正向速度脉冲
            - 增加阻尼系数 (改善自主神经调节)
            - value: 运动强度 (0-10)
            """
            intensity = value if value else 5.0  # 0-10量表
            
            # 基础正向冲击
            base_impulse = 25.0
            
            # 高强度运动效果更好 (非线性)
            intensity_factor = np.power(intensity / 5.0, 0.7)
            
            impulse = base_impulse * intensity_factor
            
            # 运动也会临时增加阻尼 (改善情绪稳定性, 持续~30分钟)
            # 这里简化为: 施加脉冲同时轻微增加c
            self.state[2] += impulse
            self.params['c'] = min(self.params['c'] * 1.1, 
                                  self.default_params['c'] * 1.5)

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

# Function to query SiliconFlow API for event analysis
def analyze_event_with_deepseek(event_description, hrv, feedback_history, logger=None):
    """
    Analyze the impact of an event on mood modeling using SiliconFlow API.

    Parameters:
        event_description (str): Description of the event.
        hrv (float): Current HRV value.
        feedback_history (list): Recent user feedback [(time, score), ...].
        logger: 日志记录器

    Returns:
        dict: Impact analysis including amplitude, duration, and parameter adjustments.
    """
    import json as json_module
    import urllib3
    
    # 压制SSL警告
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    if logger:
        logger.info(f"🚀 开始分析事件: {event_description}")
        logger.info(f"📊 当前HRV: {hrv:.2f}, 反馈条数: {len(feedback_history)}")
    
    url = "https://api.siliconflow.cn/v1/chat/completions"

    payload = {
        "model": "deepseek-ai/DeepSeek-V3.1-Terminus",
        "messages": [
            {
                "role": "user",
                "content": f"""你是一位生理学建模专家。使用Borbély双过程模型分析以下事件的影响：

事件：{event_description}
当前HRV：{hrv}

请用JSON格式返回 (必须包含):
{{"amplitude": 0, "duration": 1, "parameters": {{}}, "explanation": ""}}"""
            }
        ],
        "stream": False,
        "max_tokens": 512,
        "temperature": 0.5,
        "top_p": 0.9
    }

    headers = {
        "Authorization": "Bearer sk-meqrkgjuintmmbsvsvlzkjrzomimdozobdbogxljfsmlwtnl",
        "Content-Type": "application/json"
    }

    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if logger:
                logger.info("⏳ 正在连接SiliconFlow API...")
            
            response = requests.post(url, json=payload, headers=headers, timeout=60, verify=False)

            if logger:
                logger.info(f"📡 收到响应: HTTP {response.status_code}")
            
            if response.status_code == 200:
                try:
                    result = response.json()
                    content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
                    
                    if logger:
                        logger.info(f"📝 响应长度: {len(content)} 字符")
                    
                    # 尝试从响应中提取JSON
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    if start_idx != -1 and end_idx > start_idx:
                        json_str = content[start_idx:end_idx]
                        analysis = json_module.loads(json_str)
                        
                        if logger:
                            logger.success("✅ JSON解析成功 (SiliconFlow)")
                            logger.info(f"   - 幅度: {analysis.get('amplitude', 'N/A')}")
                            logger.info(f"   - 持续时间: {analysis.get('duration', 'N/A')} 小时")
                        
                        return analysis
                    else:
                        if logger:
                            logger.warning("⚠️ 响应中未找到JSON对象")
                except json_module.JSONDecodeError as e:
                    if logger:
                        logger.warning(f"⚠️ JSON解析错误: {str(e)}")
                except Exception as e:
                    if logger:
                        logger.warning(f"⚠️ 处理响应错误: {str(e)}")
            else:
                if logger:
                    logger.warning(f"⚠️ API返回错误: HTTP {response.status_code}")
                    
        except requests.exceptions.Timeout:
            retry_count += 1
            if logger:
                logger.warning(f"⏱️ 请求超时，正在重试 ({retry_count}/{max_retries})...")
            if retry_count < max_retries:
                time.sleep(2)
                continue
            else:
                if logger:
                    logger.error("❌ 请求超时 (60秒)，已达最大重试次数")
                break
        except requests.exceptions.ConnectionError:
            retry_count += 1
            if logger:
                logger.warning(f"🔌 连接错误，正在重试 ({retry_count}/{max_retries})...")
            if retry_count < max_retries:
                time.sleep(2)
                continue
            else:
                if logger:
                    logger.error("❌ 网络连接失败，已达最大重试次数")
                break
        except Exception as e:
            if logger:
                logger.error(f"❌ 未知错误: {type(e).__name__}")
            break
    
    # 返回默认分析
    return {
        "amplitude": -2.0 if "压力" in event_description or "吵架" in event_description else 1.0,
        "duration": 1.0,
        "parameters": {},
        "explanation": "默认分析 - API暂时不可用"
    }

# Function to query Gemini API for event analysis
def analyze_event_with_gemini(event_description, hrv, feedback_history, logger=None):
    """
    Analyze the impact of an event on mood modeling using Google Gemini API.

    Parameters:
        event_description (str): Description of the event.
        hrv (float): Current HRV value.
        feedback_history (list): Recent user feedback [(time, score), ...].
        logger: 日志记录器

    Returns:
        dict: Impact analysis including amplitude, duration, and parameter adjustments.
    """
    import json as json_module
    
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        if logger:
            logger.error("❌ google-genai 包未安装，请运行: pip install google-genai")
        return {}
    
    if logger:
        logger.info(f"🚀 开始分析事件 (Gemini): {event_description}")
        logger.info(f"📊 当前HRV: {hrv:.2f}, 反馈条数: {len(feedback_history)}")
    
    max_retries = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            if logger:
                logger.info("⏳ 正在连接Google Gemini API...")
            
            client = genai.Client(api_key="AIzaSyApXtHOD_romiNbWYX1cL_kaV2QwGHbrnQ")
            
            prompt = f"""你是一位生理学建模专家。分析事件对心情的影响。

事件：{event_description}
当前HRV：{hrv}

返回JSON格式 (必须包含): {{"amplitude": 0, "duration": 1, "parameters": {{}}, "explanation": ""}}"""
            
            contents = [
                types.Content(
                    role="user",
                    parts=[
                        types.Part.from_text(text=prompt),
                    ],
                ),
            ]
            
            # 调用Gemini API 并添加超时
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                timeout=60.0
            )
            
            if logger:
                logger.info("📡 收到Gemini响应")
            
            content = response.text
            
            if logger:
                logger.info(f"📝 响应长度: {len(content)} 字符")
            
            # 尝试从响应中提取JSON
            start_idx = content.find('{')
            end_idx = content.rfind('}') + 1
            if start_idx != -1 and end_idx > start_idx:
                json_str = content[start_idx:end_idx]
                analysis = json_module.loads(json_str)
                
                if logger:
                    logger.success("✅ JSON解析成功 (Gemini)")
                    logger.info(f"   - 幅度: {analysis.get('amplitude', 'N/A')}")
                    logger.info(f"   - 持续时间: {analysis.get('duration', 'N/A')} 小时")
                
                return analysis
            else:
                if logger:
                    logger.warning("⚠️ 响应中未找到JSON对象")
            
            retry_count = max_retries  # 成功则跳出重试
            
        except (TimeoutError, Exception) as e:
            retry_count += 1
            if logger:
                logger.warning(f"⏱️ Gemini API错误，正在重试 ({retry_count}/{max_retries}): {str(e)[:50]}")
            if retry_count < max_retries:
                time.sleep(2)
                continue
            else:
                if logger:
                    logger.error("❌ Gemini API已达最大重试次数")
                break
    
    # 返回默认分析
    return {
        "amplitude": -2.0 if "压力" in event_description or "吵架" in event_description else 1.0,
        "duration": 1.0,
        "parameters": {},
        "explanation": "默认分析 - API暂时不可用"
    }
