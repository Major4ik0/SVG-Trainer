# -*- coding: utf-8 -*-
from typing import Optional, Dict
from database import Database


class AuthManager:
    def __init__(self, db: Database):
        self.db = db
        self.current_user: Optional[Dict] = None

    def login(self, username: str, password: str) -> bool:
        user = self.db.get_user_by_username(username)
        if user and user['password'] == password:
            self.current_user = user
            return True
        return False

    def logout(self):
        self.current_user = None

    def is_admin(self) -> bool:
        return self.current_user and self.current_user['role'] == 'admin'

    def get_current_user(self) -> Optional[Dict]:
        return self.current_user