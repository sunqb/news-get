from datetime import datetime, timedelta
from typing import Dict, Optional
import threading


class SessionStore:
    """内存会话存储"""

    def __init__(self):
        self._sessions: Dict[str, dict] = {}
        self._lock = threading.Lock()

    def add_session(self, token: str, user_email: str, expires_at: datetime):
        """添加会话"""
        with self._lock:
            self._sessions[token] = {
                "email": user_email,
                "expires_at": expires_at,
                "created_at": datetime.utcnow(),
            }

    def get_session(self, token: str) -> Optional[dict]:
        """获取会话信息"""
        with self._lock:
            session = self._sessions.get(token)
            if session:
                # 检查是否过期
                if session["expires_at"] > datetime.utcnow():
                    return session
                else:
                    # 过期则删除
                    del self._sessions[token]
            return None

    def remove_session(self, token: str):
        """移除会话"""
        with self._lock:
            if token in self._sessions:
                del self._sessions[token]

    def is_valid(self, token: str) -> bool:
        """检查会话是否有效"""
        return self.get_session(token) is not None

    def cleanup_expired(self):
        """清理过期会话"""
        now = datetime.utcnow()
        with self._lock:
            expired_tokens = [
                token
                for token, session in self._sessions.items()
                if session["expires_at"] <= now
            ]
            for token in expired_tokens:
                del self._sessions[token]
        return len(expired_tokens)

    def get_active_count(self) -> int:
        """获取活跃会话数量"""
        self.cleanup_expired()
        return len(self._sessions)


# 全局会话存储实例
session_store = SessionStore()
