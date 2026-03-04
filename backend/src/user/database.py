# user/database.py
# SQLite3 数据库操作类
#

import sqlite3
import json
from typing import Optional, List
from pathlib import Path

from src.user.typedef import UserData


class UserDatabase:
    """
    用户数据库管理类
    """
    
    def __init__(self, db_path: str = "user_data.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self._init_database()
    
    def _init_database(self):
        """
        初始化数据库表结构
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 创建用户表
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            medicine TEXT DEFAULT '[]',
            face_data BLOB DEFAULT NULL
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_user(self, user_id: str, name: str) -> bool:
        """
        创建新用户
        
        Args:
            user_id: 用户ID
            name: 用户姓名
            
        Returns:
            bool: 是否创建成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "INSERT INTO users (id, name) VALUES (?, ?)",
                (user_id, name)
            )
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            # ID已存在
            return False
        except Exception as e:
            print(f"创建用户失败: {e}")
            return False
    
    def get_user(self, user_id: str) -> Optional[UserData]:
        """
        获取用户数据
        
        Args:
            user_id: 用户ID
            
        Returns:
            Optional[UserData]: 用户数据，如果不存在则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, name, medicine, face_data FROM users WHERE id = ?",
                (user_id,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                # 解析药物列表
                medicine_list = json.loads(row[2]) if row[2] else []
                return UserData(
                    id=row[0],
                    name=row[1],
                    medicine=medicine_list,
                    face_data=row[3] if row[3] else b""
                )
            return None
        except Exception as e:
            print(f"获取用户失败: {e}")
            return None
    
    def update_user_face_data(self, user_id: str, face_data: bytes) -> bool:
        """
        更新用户人脸数据
        
        Args:
            user_id: 用户ID
            face_data: 人脸识别二进制数据
            
        Returns:
            bool: 是否更新成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "UPDATE users SET face_data = ? WHERE id = ?",
                (face_data, user_id)
            )
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"更新人脸数据失败: {e}")
            return False
    
    def update_user_medicine(self, user_id: str, medicine: List[str]) -> bool:
        """
        更新用户药物列表
        
        Args:
            user_id: 用户ID
            medicine: 药物列表
            
        Returns:
            bool: 是否更新成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            medicine_json = json.dumps(medicine)
            cursor.execute(
                "UPDATE users SET medicine = ? WHERE id = ?",
                (medicine_json, user_id)
            )
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"更新药物列表失败: {e}")
            return False
    
    def get_user_by_face_data(self, face_data: bytes) -> Optional[str]:
        """
        通过人脸数据查找用户ID
        
        Args:
            face_data: 人脸识别二进制数据
            
        Returns:
            Optional[str]: 用户ID，如果未找到则返回None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id FROM users WHERE face_data = ?",
                (face_data,)
            )
            
            row = cursor.fetchone()
            conn.close()
            
            return row[0] if row else None
        except Exception as e:
            print(f"通过人脸数据查找用户失败: {e}")
            return None
    
    def get_all_users(self) -> List[UserData]:
        """
        获取所有用户数据
        
        Returns:
            List[UserData]: 用户数据列表
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "SELECT id, name, medicine, face_data FROM users"
            )
            
            users = []
            for row in cursor.fetchall():
                medicine_list = json.loads(row[2]) if row[2] else []
                users.append(UserData(
                    id=row[0],
                    name=row[1],
                    medicine=medicine_list,
                    face_data=row[3] if row[3] else b""
                ))
            
            conn.close()
            return users
        except Exception as e:
            print(f"获取所有用户失败: {e}")
            return []
    
    def delete_user(self, user_id: str) -> bool:
        """
        删除用户
        
        Args:
            user_id: 用户ID
            
        Returns:
            bool: 是否删除成功
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute(
                "DELETE FROM users WHERE id = ?",
                (user_id,)
            )
            
            conn.commit()
            conn.close()
            return cursor.rowcount > 0
        except Exception as e:
            print(f"删除用户失败: {e}")
            return False