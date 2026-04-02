import sqlite3
import json
import os
from typing import Optional, List, Dict
from contextlib import contextmanager

DB_NAME = "trainer.db"
MATERIALS_DIR = "materials"
QUESTIONS_IMAGES_DIR = "questions_images"
ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "admin"


class Database:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path
        self.init_db()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Таблица пользователей
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('admin', 'user')),
                    full_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Таблица вопросов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT NOT NULL,
                    image_path TEXT,
                    option1 TEXT NOT NULL,
                    option2 TEXT NOT NULL,
                    option3 TEXT NOT NULL,
                    option4 TEXT NOT NULL,
                    correct_mask INTEGER NOT NULL DEFAULT 0,
                    explanation TEXT,
                    category TEXT
                )
            ''')

            # Таблица результатов тестов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    score INTEGER NOT NULL,
                    total INTEGER NOT NULL,
                    passed BOOLEAN NOT NULL,
                    details TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Таблица учебных материалов
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_materials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT NOT NULL,
                    content TEXT,
                    file_path TEXT,
                    file_type TEXT DEFAULT 'text',
                    uploaded_by INTEGER NOT NULL,
                    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    description TEXT,
                    FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')

            # Добавление admin пользователя
            cursor.execute("SELECT * FROM users WHERE username = ?", (ADMIN_LOGIN,))
            if not cursor.fetchone():
                cursor.execute(
                    "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                    (ADMIN_LOGIN, ADMIN_PASSWORD, 'admin', 'Администратор')
                )
                cursor.execute(
                    "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                    ('user1', 'pass1', 'user', 'Иванов Иван Иванович')
                )
                cursor.execute(
                    "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                    ('user2', 'pass2', 'user', 'Петров Петр Петрович')
                )

            # Добавление тестовых вопросов
            cursor.execute("SELECT COUNT(*) FROM questions")
            if cursor.fetchone()[0] == 0:
                test_questions = [
                    ("Что такое воинский транспорт согласно Положению об охране и сопровождении воинских грузов?",
                     None,
                     "Груз, принадлежащий МО и принятый к перевозке",
                     "Принятый для перевозки ж/д, морским или речным транспортом от одного отправителя в адрес одного или нескольких получателей воинский груз, для перевозки которого требуется не менее одного вагона (100 т и более)",
                     "Любой груз военной тематики", "Транспортное средство для перевозки военных",
                     0b0010, "Согласно п. 3 Положения (Приказ МО РФ № 321)", "Нормативная база"),
                    ("Кто подчиняется начальник караула в пути следования?",
                     None,
                     "Только командиру своей части",
                     "Военным комендантам ж/д (водных) участков и станций, аэропортов по пути следования",
                     "Грузоотправителю", "Начальнику ж/д станции",
                     0b0010, "Согласно п. 5 Положения (Приказ МО РФ № 321)", "Организация службы"),
                ]
                for q in test_questions:
                    cursor.execute('''
                        INSERT INTO questions (text, image_path, option1, option2, option3, option4, correct_mask, explanation, category)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', q)

        # Создание директорий
        os.makedirs(MATERIALS_DIR, exist_ok=True)
        os.makedirs(QUESTIONS_IMAGES_DIR, exist_ok=True)

    def execute_query(self, query: str, params: tuple = ()) -> List[Dict]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            if query.strip().upper().startswith('SELECT'):
                return [dict(row) for row in cursor.fetchall()]
            return []

    def execute_insert(self, query: str, params: tuple = ()) -> int:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            return cursor.lastrowid

    def execute_update(self, query: str, params: tuple = ()) -> bool:
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, params)
                return True
        except Exception:
            return False

    # Пользователи
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        result = self.execute_query("SELECT * FROM users WHERE username = ?", (username,))
        return result[0] if result else None

    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        result = self.execute_query("SELECT * FROM users WHERE id = ?", (user_id,))
        return result[0] if result else None

    def get_all_users(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM users")

    def add_user(self, username: str, password: str, role: str, full_name: str) -> bool:
        try:
            self.execute_insert(
                "INSERT INTO users (username, password, role, full_name) VALUES (?, ?, ?, ?)",
                (username, password, role, full_name)
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def update_user(self, user_id: int, username: str, full_name: str, role: str, password: str = None) -> bool:
        if password:
            return self.execute_update(
                "UPDATE users SET username=?, full_name=?, role=?, password=? WHERE id=?",
                (username, full_name, role, password, user_id)
            )
        else:
            return self.execute_update(
                "UPDATE users SET username=?, full_name=?, role=? WHERE id=?",
                (username, full_name, role, user_id)
            )

    def delete_user(self, user_id: int) -> bool:
        return self.execute_update("DELETE FROM users WHERE id = ?", (user_id,))

    # Вопросы
    def add_question(self, text: str, image_path: Optional[str], opts: List[str], correct_mask: int,
                     explanation: str, category: str) -> int:
        return self.execute_insert('''
            INSERT INTO questions (text, image_path, option1, option2, option3, option4, correct_mask, explanation, category)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (text, image_path, opts[0], opts[1], opts[2], opts[3], correct_mask, explanation, category))

    def update_question(self, qid: int, text: str, image_path: Optional[str], opts: List[str],
                        correct_mask: int, explanation: str, category: str):
        self.execute_update('''
            UPDATE questions SET text=?, image_path=?, option1=?, option2=?, option3=?, option4=?, 
            correct_mask=?, explanation=?, category=? WHERE id=?
        ''', (text, image_path, opts[0], opts[1], opts[2], opts[3], correct_mask, explanation, category, qid))

    def delete_question(self, qid: int):
        self.execute_update("DELETE FROM questions WHERE id = ?", (qid,))

    def get_all_questions(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM questions")

    def get_question_by_id(self, qid: int) -> Optional[Dict]:
        result = self.execute_query("SELECT * FROM questions WHERE id = ?", (qid,))
        return result[0] if result else None

    def get_random_questions(self, count: int) -> List[Dict]:
        return self.execute_query("SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (count,))

    # Результаты тестов
    def save_test_result(self, user_id: int, score: int, total: int, details: List[Dict]) -> int:
        passed = (score / total * 100) >= 80 if total > 0 else False
        details_json = json.dumps(details, ensure_ascii=False)
        return self.execute_insert('''
            INSERT INTO test_results (user_id, score, total, passed, details)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, score, total, passed, details_json))

    def get_user_test_results(self, user_id: int) -> List[Dict]:
        return self.execute_query(
            "SELECT * FROM test_results WHERE user_id = ? ORDER BY date DESC",
            (user_id,)
        )

    def get_test_result_by_id(self, result_id: int) -> Optional[Dict]:
        result = self.execute_query("SELECT * FROM test_results WHERE id = ?", (result_id,))
        return result[0] if result else None

    # Учебные материалы
    def add_learning_material(self, filename: str, content: str, file_path: str,
                               file_type: str, uploaded_by: int, description: str) -> int:
        return self.execute_insert('''
            INSERT INTO learning_materials (filename, content, file_path, file_type, uploaded_by, description)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (filename, content, file_path, file_type, uploaded_by, description))

    def delete_learning_material(self, material_id: int):
        self.execute_update("DELETE FROM learning_materials WHERE id = ?", (material_id,))

    def get_all_learning_materials(self) -> List[Dict]:
        return self.execute_query("SELECT * FROM learning_materials ORDER BY uploaded_at DESC")

    # Статистика
    def get_user_mistakes(self, user_id: int, limit: int = 20) -> List[Dict]:
        results = self.get_user_test_results(user_id)
        mistake_questions = {}
        for res in results[:10]:
            try:
                details = json.loads(res['details'])
                for detail in details:
                    if not detail['correct']:
                        qid = detail['question_id']
                        if qid not in mistake_questions:
                            mistake_questions[qid] = {
                                'question_id': qid,
                                'question_text': detail['question_text'],
                                'explanation': detail.get('explanation', ''),
                                'correct_mask': detail['correct_mask'],
                                'options': detail['options'],
                                'error_count': 1
                            }
                        else:
                            mistake_questions[qid]['error_count'] += 1
            except:
                continue
        questions = []
        for qid, mistake_data in mistake_questions.items():
            q = self.get_question_by_id(qid)
            if q:
                q['error_count'] = mistake_data['error_count']
                q['explanation'] = mistake_data['explanation']
                questions.append(q)
        questions.sort(key=lambda x: x.get('error_count', 0), reverse=True)
        return questions[:limit]

    def get_overall_stats(self) -> Dict:
        total_users = self.execute_query("SELECT COUNT(*) as count FROM users WHERE role='user'")[0]['count']
        total_questions = self.execute_query("SELECT COUNT(*) as count FROM questions")[0]['count']
        avg = self.execute_query("SELECT AVG(score*100.0/total) as avg FROM test_results")
        avg_score = avg[0]['avg'] if avg[0]['avg'] else 0
        passed = self.execute_query("SELECT COUNT(*) as count FROM test_results WHERE passed=1")[0]['count']
        total_tests = self.execute_query("SELECT COUNT(*) as count FROM test_results")[0]['count']
        passed_percent = (passed / total_tests * 100) if total_tests > 0 else 0
        return {
            'total_users': total_users,
            'total_questions': total_questions,
            'avg_score': avg_score,
            'passed_percent': passed_percent
        }

    def get_user_stats_for_admin(self) -> List[Dict]:
        users = self.get_all_users()
        stats = []
        for user in users:
            if user['role'] == 'admin':
                continue
            results = self.get_user_test_results(user['id'])
            if not results:
                continue
            avg = sum(r['score'] * 100 / r['total'] for r in results) / len(results)
            passed_count = sum(1 for r in results if r['passed'])
            stats.append({
                'user_id': user['id'],
                'username': user['username'],
                'full_name': user['full_name'],
                'tests_count': len(results),
                'avg_score': avg,
                'passed_count': passed_count
            })
        return stats

    # Добавьте эти методы в класс Database

    def get_user_detailed_stats(self, user_id: int) -> Dict:
        """Получение детальной статистики пользователя"""
        results = self.get_user_test_results(user_id)

        if not results:
            return {
                'total_tests': 0,
                'total_correct': 0,
                'total_questions': 0,
                'avg_percent': 0,
                'passed_tests': 0,
                'failed_tests': 0,
                'best_result': 0,
                'worst_result': 0,
                'recent_results': []
            }

        total_correct = sum(r['score'] for r in results)
        total_questions = sum(r['total'] for r in results)
        avg_percent = (total_correct / total_questions * 100) if total_questions > 0 else 0
        passed_tests = sum(1 for r in results if r['passed'])
        failed_tests = len(results) - passed_tests
        best_result = max((r['score'] / r['total'] * 100) for r in results)
        worst_result = min((r['score'] / r['total'] * 100) for r in results)

        return {
            'total_tests': len(results),
            'total_correct': total_correct,
            'total_questions': total_questions,
            'avg_percent': avg_percent,
            'passed_tests': passed_tests,
            'failed_tests': failed_tests,
            'best_result': best_result,
            'worst_result': worst_result,
            'recent_results': results[:5]
        }

    def get_all_users_stats(self) -> List[Dict]:
        """Получение статистики по всем пользователям для админа"""
        users = self.get_all_users()
        stats = []

        for user in users:
            if user['role'] == 'admin':
                continue

            results = self.get_user_test_results(user['id'])

            if results:
                total_correct = sum(r['score'] for r in results)
                total_questions = sum(r['total'] for r in results)
                avg_percent = (total_correct / total_questions * 100) if total_questions > 0 else 0
                passed_tests = sum(1 for r in results if r['passed'])

                stats.append({
                    'user_id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'total_tests': len(results),
                    'total_correct': total_correct,
                    'total_questions': total_questions,
                    'avg_percent': avg_percent,
                    'passed_tests': passed_tests,
                    'failed_tests': len(results) - passed_tests,
                    'last_test_date': results[0]['date'] if results else None
                })
            else:
                stats.append({
                    'user_id': user['id'],
                    'username': user['username'],
                    'full_name': user['full_name'],
                    'total_tests': 0,
                    'total_correct': 0,
                    'total_questions': 0,
                    'avg_percent': 0,
                    'passed_tests': 0,
                    'failed_tests': 0,
                    'last_test_date': None
                })

        return stats