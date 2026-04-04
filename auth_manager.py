# -*- coding: utf-8 -*-
from typing import Optional, Dict
from database import Database


class AuthManager:
    def __init__(self, db: Database):
        self.db = db
        self.current_user: Optional[Dict] = None

    def login(self, username: str, password: str) -> bool:
        user = self.db.get_user_by_username(username)
        # Добавим отладочный вывод (можно убрать потом)
        print(f"Login attempt - username: {username}")
        print(f"User found: {user is not None}")
        if user:
            print(f"User role: {user.get('role')}")
            print(f"Password match: {user['password'] == password}")

        if user and user['password'] == password:
            self.current_user = user
            print(f"Login successful! User: {user['username']}, Role: {user['role']}")
            return True
        return False

    def logout(self):
        self.current_user = None

    def is_admin(self) -> bool:
        result = self.current_user and self.current_user.get('role') == 'admin'
        print(f"is_admin check: {result}, user: {self.current_user.get('username') if self.current_user else 'None'}")
        return result

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user