"""
数据库模块 - 处理用户、心情记录、事件等数据
支持SQLite和MySQL两种数据库
简化版本：使用SHA256哈希（无需bcrypt依赖）
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import hashlib
import json

class Database:
    """数据库操作类"""
    
    def __init__(self, db_type="sqlite", db_path="bio_mood.db", mysql_config=None):
        """初始化数据库"""
        self.db_type = db_type
        self.db_path = db_path
        
        if db_type == "sqlite":
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        else:
            try:
                import pymysql
                self.conn = pymysql.connect(
                    host=mysql_config['host'],
                    user=mysql_config['user'],
                    password=mysql_config['password'],
                    database=mysql_config['database'],
                    charset='utf8mb4'
                )
            except ImportError:
                raise ImportError("MySQL支持需要: pip install pymysql")
        
        self.init_tables()
    
    @staticmethod
    def hash_password(password: str) -> str:
        """SHA256密码哈希"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def init_tables(self):
        """初始化数据表"""
        cursor = self.conn.cursor()
        
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
                preferences TEXT DEFAULT '{}'
            )
        """)
        
        # 心情记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS mood_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                mood_value REAL NOT NULL,
                baseline REAL,
                sleep_pressure REAL,
                hrv_value REAL,
                parameters TEXT,
                notes TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 事件记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                event_description TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                amplitude REAL,
                duration REAL,
                ai_analysis TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 用户参数个性化表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_parameters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                tau_r REAL DEFAULT 17.0,
                tau_d REAL DEFAULT 5.5,
                circadian_k REAL DEFAULT 0.1,
                circadian_amplitude REAL DEFAULT 0.3,
                k REAL DEFAULT 12.0,
                c REAL DEFAULT 3.5,
                m REAL DEFAULT 1.0,
                base_hrv REAL DEFAULT 50.0,
                phi REAL DEFAULT 0.0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # 创建索引
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_mood_user_time 
            ON mood_records(user_id, timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_events_user_time 
            ON events(user_id, timestamp DESC)
        """)
        
        self.conn.commit()
    
    # ===== 用户管理 =====
    
    def register_user_simple(self, username: str, email: str, password: str) -> Tuple[bool, str]:
        """注册新用户"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("SELECT id FROM users WHERE username=? OR email=?", (username, email))
            if cursor.fetchone():
                return False, "用户名或邮箱已存在"
            
            password_hash = self.hash_password(password)
            
            cursor.execute("""
                INSERT INTO users (username, email, password_hash)
                VALUES (?, ?, ?)
            """, (username, email, password_hash))
            
            user_id = cursor.lastrowid
            
            cursor.execute("""
                INSERT INTO user_parameters (user_id)
                VALUES (?)
            """, (user_id,))
            
            self.conn.commit()
            return True, "注册成功"
            
        except Exception as e:
            return False, f"注册失败: {str(e)}"
    
    def login_user_simple(self, username: str, password: str) -> Tuple[bool, Optional[int], str]:
        """用户登录"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT id, password_hash, is_active FROM users 
                WHERE username=?
            """, (username,))
            
            row = cursor.fetchone()
            if not row:
                return False, None, "用户不存在"
            
            user_id, password_hash, is_active = row if self.db_type == "sqlite" else (row[0], row[1], row[2])
            
            if not is_active:
                return False, None, "账户已禁用"
            
            if self.hash_password(password) != password_hash:
                return False, None, "密码错误"
            
            cursor.execute("""
                UPDATE users SET last_login=? WHERE id=?
            """, (datetime.now(), user_id))
            self.conn.commit()
            
            return True, user_id, "登录成功"
            
        except Exception as e:
            return False, None, f"登录失败: {str(e)}"
    
    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """获取用户信息"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT id, username, email, created_at, last_login, preferences 
                FROM users WHERE id=?
            """, (user_id,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            if self.db_type == "sqlite":
                return {
                    'id': row['id'],
                    'username': row['username'],
                    'email': row['email'],
                    'created_at': row['created_at'],
                    'last_login': row['last_login'],
                    'preferences': json.loads(row['preferences'] or '{}')
                }
            else:
                return {
                    'id': row[0],
                    'username': row[1],
                    'email': row[2],
                    'created_at': row[3],
                    'last_login': row[4],
                    'preferences': json.loads(row[5] or '{}')
                }
        except Exception as e:
            print(f"获取用户信息失败: {e}")
            return None
    
    # ===== 心情记录 =====
    
    def add_mood_record(self, user_id: int, mood_value: float, 
                       baseline: float = None, sleep_pressure: float = None,
                       hrv_value: float = None, parameters: dict = None,
                       notes: str = None) -> Tuple[bool, str]:
        """添加心情记录"""
        try:
            cursor = self.conn.cursor()
            params_json = json.dumps(parameters) if parameters else None
            
            cursor.execute("""
                INSERT INTO mood_records 
                (user_id, mood_value, baseline, sleep_pressure, hrv_value, parameters, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, mood_value, baseline, sleep_pressure, hrv_value, params_json, notes))
            
            self.conn.commit()
            return True, "心情记录已保存"
            
        except Exception as e:
            return False, f"保存失败: {str(e)}"
    
    def get_mood_history(self, user_id: int, limit: int = 100, days: int = None) -> List[Dict]:
        """获取用户心情历史"""
        try:
            cursor = self.conn.cursor()
            
            if days:
                query = """
                    SELECT * FROM mood_records 
                    WHERE user_id=? AND timestamp > datetime('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                cursor.execute(query, (user_id, days, limit))
            else:
                cursor.execute("""
                    SELECT * FROM mood_records 
                    WHERE user_id=?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            
            rows = cursor.fetchall()
            records = []
            
            for row in rows:
                if self.db_type == "sqlite":
                    records.append({
                        'id': row['id'],
                        'timestamp': row['timestamp'],
                        'mood_value': row['mood_value'],
                        'baseline': row['baseline'],
                        'sleep_pressure': row['sleep_pressure'],
                        'hrv_value': row['hrv_value'],
                        'parameters': json.loads(row['parameters'] or '{}'),
                        'notes': row['notes']
                    })
            
            return records
            
        except Exception as e:
            print(f"获取心情历史失败: {e}")
            return []
    
    def get_mood_statistics(self, user_id: int, days: int = 7) -> Dict:
        """获取心情统计数据"""
        try:
            cursor = self.conn.cursor()
            
            cursor.execute("""
                SELECT 
                    AVG(mood_value) as avg_mood,
                    MAX(mood_value) as max_mood,
                    MIN(mood_value) as min_mood,
                    COUNT(*) as count
                FROM mood_records 
                WHERE user_id=? AND timestamp > datetime('now', '-' || ? || ' days')
            """, (user_id, days))
            
            row = cursor.fetchone()
            
            if self.db_type == "sqlite":
                return {
                    'average': round(row['avg_mood'] or 0, 2),
                    'max': row['max_mood'],
                    'min': row['min_mood'],
                    'count': row['count']
                }
            else:
                return {
                    'average': round(row[0] or 0, 2),
                    'max': row[1],
                    'min': row[2],
                    'count': row[3]
                }
        except Exception as e:
            print(f"获取统计数据失败: {e}")
            return {'average': 0, 'max': 0, 'min': 0, 'count': 0}
    
    # ===== 事件记录 =====
    
    def add_event(self, user_id: int, event_type: str, 
                 event_description: str = None, amplitude: float = None,
                 duration: float = None, ai_analysis: dict = None) -> Tuple[bool, str]:
        """添加事件记录"""
        try:
            cursor = self.conn.cursor()
            ai_json = json.dumps(ai_analysis) if ai_analysis else None
            
            cursor.execute("""
                INSERT INTO events 
                (user_id, event_type, event_description, amplitude, duration, ai_analysis)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, event_type, event_description, amplitude, duration, ai_json))
            
            self.conn.commit()
            return True, "事件已记录"
            
        except Exception as e:
            return False, f"记录失败: {str(e)}"
    
    def get_events(self, user_id: int, limit: int = 100, days: int = None) -> List[Dict]:
        """获取用户事件历史"""
        try:
            cursor = self.conn.cursor()
            
            if days:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE user_id=? AND timestamp > datetime('now', '-' || ? || ' days')
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, days, limit))
            else:
                cursor.execute("""
                    SELECT * FROM events 
                    WHERE user_id=?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (user_id, limit))
            
            rows = cursor.fetchall()
            events = []
            
            for row in rows:
                if self.db_type == "sqlite":
                    events.append({
                        'id': row['id'],
                        'event_type': row['event_type'],
                        'event_description': row['event_description'],
                        'timestamp': row['timestamp'],
                        'amplitude': row['amplitude'],
                        'duration': row['duration'],
                        'ai_analysis': json.loads(row['ai_analysis'] or '{}')
                    })
            
            return events
            
        except Exception as e:
            print(f"获取事件历史失败: {e}")
            return []
    
    # ===== 用户参数 =====
    
    def get_user_parameters(self, user_id: int) -> Dict:
        """获取用户个性化参数"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT tau_r, tau_d, circadian_k, circadian_amplitude, k, c, m, base_hrv, phi
                FROM user_parameters 
                WHERE user_id=?
            """, (user_id,))
            
            row = cursor.fetchone()
            
            if not row:
                return None
            
            if self.db_type == "sqlite":
                return {
                    'tau_r': row['tau_r'],
                    'tau_d': row['tau_d'],
                    'circadian_k': row['circadian_k'],
                    'circadian_amplitude': row['circadian_amplitude'],
                    'k': row['k'],
                    'c': row['c'],
                    'm': row['m'],
                    'base_hrv': row['base_hrv'],
                    'phi': row['phi']
                }
        except Exception as e:
            print(f"获取用户参数失败: {e}")
            return None
    
    def update_user_parameters(self, user_id: int, params: Dict) -> Tuple[bool, str]:
        """更新用户个性化参数"""
        try:
            cursor = self.conn.cursor()
            
            if 'tau_r' in params:
                cursor.execute("UPDATE user_parameters SET tau_r=?, updated_at=? WHERE user_id=?", 
                             (params['tau_r'], datetime.now(), user_id))
            if 'tau_d' in params:
                cursor.execute("UPDATE user_parameters SET tau_d=?, updated_at=? WHERE user_id=?", 
                             (params['tau_d'], datetime.now(), user_id))
            if 'k' in params:
                cursor.execute("UPDATE user_parameters SET k=?, updated_at=? WHERE user_id=?", 
                             (params['k'], datetime.now(), user_id))
            if 'c' in params:
                cursor.execute("UPDATE user_parameters SET c=?, updated_at=? WHERE user_id=?", 
                             (params['c'], datetime.now(), user_id))
            if 'circadian_amplitude' in params:
                cursor.execute("UPDATE user_parameters SET circadian_amplitude=?, updated_at=? WHERE user_id=?", 
                             (params['circadian_amplitude'], datetime.now(), user_id))
            if 'base_hrv' in params:
                cursor.execute("UPDATE user_parameters SET base_hrv=?, updated_at=? WHERE user_id=?", 
                             (params['base_hrv'], datetime.now(), user_id))
            
            self.conn.commit()
            return True, "参数已更新"
            
        except Exception as e:
            return False, f"更新失败: {str(e)}"
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
