"""
认证模块 - 用户登录、注册和会话管理
简化版本，不依赖streamlit_authenticator
"""

import streamlit as st
import hashlib
from datetime import datetime
from database import Database

class AuthManager:
    """认证和会话管理"""
    
    def __init__(self, db: Database):
        """初始化认证管理器"""
        self.db = db
    
    @staticmethod
    def hash_password(password: str) -> str:
        """简单的密码哈希（实现）"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_session_state(self):
        """初始化session状态"""
        if 'authenticated' not in st.session_state:
            st.session_state.authenticated = False
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'username' not in st.session_state:
            st.session_state.username = None
        if 'user_info' not in st.session_state:
            st.session_state.user_info = None
    
    def register_page(self):
        """注册页面"""
        st.header("📝 用户注册")
        
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("用户名", help="长度3-20个字符", key="reg_username")
            
            with col2:
                email = st.text_input("邮箱", key="reg_email")
            
            col1, col2 = st.columns(2)
            
            with col1:
                password = st.text_input("密码", type="password", help="长度至少8个字符", key="reg_password")
            
            with col2:
                password_confirm = st.text_input("确认密码", type="password", key="reg_password_confirm")
            
            submit = st.form_submit_button("🚀 注册账户")
        
        if submit:
            # 验证输入
            if not username or len(username) < 3 or len(username) > 20:
                st.error("❌ 用户名必须是3-20个字符")
                return
            
            if not email or '@' not in email:
                st.error("❌ 请输入有效的邮箱")
                return
            
            if not password or len(password) < 8:
                st.error("❌ 密码必须至少8个字符")
                return
            
            if password != password_confirm:
                st.error("❌ 两次输入的密码不一致")
                return
            
            # 注册用户（使用简单哈希）
            success, message = self.db.register_user_simple(username, email, password)
            
            if success:
                st.success("✅ 注册成功！请返回登录页面登录")
                st.balloons()
            else:
                st.error(f"❌ {message}")
    
    def login_page(self):
        """登录页面"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("## 🧠 情绪量化生物数字孪生")
            st.markdown("### 用户登录")
            
            # 登录表单
            with st.form("login_form"):
                username = st.text_input("用户名", key="login_username")
                password = st.text_input("密码", type="password", key="login_password")
                
                col_login, col_reg = st.columns(2)
                
                with col_login:
                    submit = st.form_submit_button("🔓 登录", use_container_width=True)
                
                with col_reg:
                    register = st.form_submit_button("📝 注册新账户", use_container_width=True)
            
            if submit:
                if not username or not password:
                    st.error("❌ 请输入用户名和密码")
                    return
                
                # 验证用户
                success, user_id, message = self.db.login_user_simple(username, password)
                
                if success:
                    # 设置会话状态
                    st.session_state.authenticated = True
                    st.session_state.user_id = user_id
                    st.session_state.username = username
                    st.session_state.user_info = self.db.get_user_info(user_id)
                    
                    st.success(f"✅ {message}")
                    st.balloons()
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
            
            if register:
                st.session_state.page = "register"
                st.rerun()
        
        # 页脚
        st.markdown("---")
        st.markdown("""
        <div style='text-align: center; color: #999; font-size: 12px;'>
        🔐 安全加密 | 📱 多设备同步 | 🌍 全球访问
        <br>
        Copyright © 2025 Bio-Mood Digital Twin
        </div>
        """, unsafe_allow_html=True)
    
    def logout(self):
        """登出"""
        st.session_state.authenticated = False
        st.session_state.user_id = None
        st.session_state.username = None
        st.session_state.user_info = None
        st.session_state.pop('engine', None)
        st.session_state.pop('history', None)
        st.rerun()
    
    def show_user_profile(self):
        """显示用户资料"""
        if not st.session_state.user_info:
            return
        
        user_info = st.session_state.user_info
        
        with st.sidebar:
            st.divider()
            st.subheader("👤 用户资料")
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"**用户名**: {user_info['username']}")
                st.markdown(f"**邮箱**: {user_info['email']}")
                st.markdown(f"**创建于**: {user_info['created_at'][:10]}")
            
            with col2:
                if st.button("🚪 登出"):
                    self.logout()
            
            st.divider()

