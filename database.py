"""
database.py - работа с SQLite и bcrypt
Бро-версия, всё чётко
"""

import sqlite3
import bcrypt
from datetime import datetime
from pathlib import Path
import os

DB_NAME = "chat.db"
UPLOAD_DIR = "uploads"

# Создаём папку для файлов при импорте
Path(UPLOAD_DIR).mkdir(exist_ok=True)

def get_db_connection():
    """Возвращает соединение с БД"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Чтобы обращаться по именам колонок
    return conn

def init_db():
    """Создаём таблицы и первого админа"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'guest',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Таблица групп
    c.execute('''CREATE TABLE IF NOT EXISTS groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_by INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )''')
    
    # Участники групп
    c.execute('''CREATE TABLE IF NOT EXISTS group_members (
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (group_id, user_id),
        FOREIGN KEY (group_id) REFERENCES groups(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )''')
    
    # Сообщения (универсальная таблица)
    c.execute('''CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        from_user_id INTEGER NOT NULL,
        to_group_id INTEGER,
        to_user_id INTEGER,
        content TEXT,
        file_path TEXT,
        is_read INTEGER DEFAULT 0,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (from_user_id) REFERENCES users(id),
        FOREIGN KEY (to_group_id) REFERENCES groups(id),
        FOREIGN KEY (to_user_id) REFERENCES users(id),
        CHECK (to_group_id IS NOT NULL OR to_user_id IS NOT NULL OR (to_group_id IS NULL AND to_user_id IS NULL))
    )''')
    
    # Создаём индексы для скорости
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_timestamp ON messages(timestamp)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_from_user ON messages(from_user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_to_user ON messages(to_user_id)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_messages_to_group ON messages(to_group_id)')
    
    # Проверяем, есть ли админ
    c.execute("SELECT * FROM users WHERE role = 'admin' LIMIT 1")
    if not c.fetchone():
        # Первый пользователь - админ (пароль: admin123)
        hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  ("admin", hashed, "admin"))
        print("✅ Создан админ: admin / admin123")
    
    conn.commit()
    conn.close()

def hash_password(password):
    """Хэшируем пароль bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    """Проверяем пароль"""
    return bcrypt.checkpw(password.encode(), hashed)

def create_user(username, password, role='guest'):
    """Создаёт нового пользователя"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        hashed = hash_password(password)
        c.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                  (username, hashed, role))
        user_id = c.lastrowid
        conn.commit()
        conn.close()
        return user_id
    except sqlite3.IntegrityError:
        return None

def get_user_by_username(username):
    """Получает пользователя по логину"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def get_user_by_id(user_id):
    """Получает пользователя по ID"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_users():
    """Список всех пользователей"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role, created_at FROM users ORDER BY username")
    users = c.fetchall()
    conn.close()
    return [dict(user) for user in users]

def delete_user(user_id):
    """Удаляет пользователя и все его сообщения"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Удаляем сообщения пользователя
    c.execute("DELETE FROM messages WHERE from_user_id = ?", (user_id,))
    # Удаляем из групп
    c.execute("DELETE FROM group_members WHERE user_id = ?", (user_id,))
    # Удаляем созданные группы (передаём владение админу или удаляем?)
    c.execute("UPDATE groups SET created_by = 1 WHERE created_by = ?", (user_id,))
    # Удаляем пользователя
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    
    conn.commit()
    conn.close()

def update_user_role(user_id, new_role):
    """Меняет роль пользователя"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE users SET role = ? WHERE id = ?", (new_role, user_id))
    conn.commit()
    conn.close()

def create_group(name, created_by):
    """Создаёт новую группу"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO groups (name, created_by) VALUES (?, ?)", (name, created_by))
    group_id = c.lastrowid
    # Автоматически добавляем создателя в группу
    c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, created_by))
    conn.commit()
    conn.close()
    return group_id

def add_user_to_group(group_id, user_id):
    """Добавляет пользователя в группу"""
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("INSERT INTO group_members (group_id, user_id) VALUES (?, ?)", (group_id, user_id))
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False

def remove_user_from_group(group_id, user_id):
    """Удаляет пользователя из группы"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, user_id))
    conn.commit()
    conn.close()

def get_user_groups(user_id):
    """Возвращает все группы, где состоит пользователь"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT g.id, g.name, g.created_by, g.created_at 
                 FROM groups g
                 JOIN group_members gm ON g.id = gm.group_id
                 WHERE gm.user_id = ?
                 ORDER BY g.name''', (user_id,))
    groups = c.fetchall()
    conn.close()
    return [dict(group) for group in groups]

def get_group_members(group_id):
    """Список участников группы"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''SELECT u.id, u.username, u.role
                 FROM users u
                 JOIN group_members gm ON u.id = gm.user_id
                 WHERE gm.group_id = ?
                 ORDER BY u.username''', (group_id,))
    members = c.fetchall()
    conn.close()
    return [dict(member) for member in members]

def get_direct_chat_users(user_id):
    """Возвращает всех пользователей для личных чатов (кроме себя)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id, username, role FROM users WHERE id != ? ORDER BY username", (user_id,))
    users = c.fetchall()
    conn.close()
    return [dict(user) for user in users]

def save_message(from_user_id, to_group_id, to_user_id, content, file_path=None):
    """Сохраняет сообщение в БД"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO messages (from_user_id, to_group_id, to_user_id, content, file_path)
                 VALUES (?, ?, ?, ?, ?)''',
              (from_user_id, to_group_id, to_user_id, content, file_path))
    msg_id = c.lastrowid
    conn.commit()
    conn.close()
    return msg_id

def get_messages(chat_type, chat_id=None, user_id=None, limit=50, offset=0):
    """
    Получает сообщения для конкретного чата
    chat_type: 'general' (общий чат), 'group', 'direct'
    """
    conn = get_db_connection()
    c = conn.cursor()
    
    if chat_type == 'general':
        # Общий чат: to_group_id IS NULL AND to_user_id IS NULL
        c.execute('''SELECT m.*, u.username 
                     FROM messages m
                     JOIN users u ON m.from_user_id = u.id
                     WHERE m.to_group_id IS NULL AND m.to_user_id IS NULL
                     ORDER BY m.timestamp DESC
                     LIMIT ? OFFSET ?''', (limit, offset))
    
    elif chat_type == 'group':
        # Групповой чат
        c.execute('''SELECT m.*, u.username 
                     FROM messages m
                     JOIN users u ON m.from_user_id = u.id
                     WHERE m.to_group_id = ?
                     ORDER BY m.timestamp DESC
                     LIMIT ? OFFSET ?''', (chat_id, limit, offset))
    
    elif chat_type == 'direct':
        # Личный чат между двумя пользователями
        c.execute('''SELECT m.*, u.username 
                     FROM messages m
                     JOIN users u ON m.from_user_id = u.id
                     WHERE (m.to_user_id = ? AND m.from_user_id = ?)
                        OR (m.to_user_id = ? AND m.from_user_id = ?)
                     ORDER BY m.timestamp DESC
                     LIMIT ? OFFSET ?''', 
                  (user_id, chat_id, chat_id, user_id, limit, offset))
    
    messages = c.fetchall()
    conn.close()
    return [dict(msg) for msg in messages][::-1]  # Переворачиваем для хронологического порядка

def get_unread_count(user_id, chat_type, chat_id=None):
    """Считает непрочитанные сообщения в чате"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if chat_type == 'general':
        c.execute('''SELECT COUNT(*) FROM messages 
                     WHERE to_group_id IS NULL AND to_user_id IS NULL 
                     AND from_user_id != ? AND is_read = 0''', (user_id,))
    elif chat_type == 'group':
        c.execute('''SELECT COUNT(*) FROM messages 
                     WHERE to_group_id = ? AND from_user_id != ? AND is_read = 0''', 
                  (chat_id, user_id))
    elif chat_type == 'direct':
        c.execute('''SELECT COUNT(*) FROM messages 
                     WHERE to_user_id = ? AND from_user_id = ? AND is_read = 0''', 
                  (user_id, chat_id))
    
    count = c.fetchone()[0]
    conn.close()
    return count

def mark_messages_as_read(user_id, chat_type, chat_id=None):
    """Отмечает сообщения как прочитанные"""
    conn = get_db_connection()
    c = conn.cursor()
    
    if chat_type == 'general':
        c.execute('''UPDATE messages SET is_read = 1 
                     WHERE to_group_id IS NULL AND to_user_id IS NULL 
                     AND from_user_id != ? AND is_read = 0''', (user_id,))
    elif chat_type == 'group':
        c.execute('''UPDATE messages SET is_read = 1 
                     WHERE to_group_id = ? AND from_user_id != ? AND is_read = 0''', 
                  (chat_id, user_id))
    elif chat_type == 'direct':
        c.execute('''UPDATE messages SET is_read = 1 
                     WHERE to_user_id = ? AND from_user_id = ? AND is_read = 0''', 
                  (user_id, chat_id))
    
    conn.commit()
    conn.close()
# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ CHAT.PY ==========

def get_group_by_id(group_id):
    """Получает группу по ID"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM groups WHERE id = ?", (group_id,))
    group = c.fetchone()
    conn.close()
    return dict(group) if group else None

def get_db_connection():
    """Возвращает соединение с БД (уже есть в начале, но на всякий случай)"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def message_exists(message_id):
    """Проверяет существует ли сообщение"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM messages WHERE id = ?", (message_id,))
    exists = c.fetchone() is not None
    conn.close()
    return exists

def delete_message(message_id, user_id):
    """Удаляет сообщение (только если пользователь его автор)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM messages WHERE id = ? AND from_user_id = ?", (message_id, user_id))
    deleted = c.rowcount > 0
    conn.commit()
    conn.close()
    return deleted

def get_user_by_username(username):
    """Получает пользователя по логину (дубль, но пусть будет)"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    conn.close()
    return dict(user) if user else None

def search_users(search_term, exclude_user_id=None):
    """Поиск пользователей по имени"""
    conn = get_db_connection()
    c = conn.cursor()
    if exclude_user_id:
        c.execute("SELECT id, username, role FROM users WHERE username LIKE ? AND id != ? LIMIT 20",
                  (f'%{search_term}%', exclude_user_id))
    else:
        c.execute("SELECT id, username, role FROM users WHERE username LIKE ? LIMIT 20",
                  (f'%{search_term}%',))
    users = c.fetchall()
    conn.close()
    return [dict(user) for user in users]

def get_recent_chats(user_id, limit=10):
    """Возвращает последние чаты пользователя (для быстрого доступа)"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Получаем последние уникальные чаты из сообщений
    c.execute('''
        SELECT DISTINCT 
            CASE 
                WHEN m.to_user_id = ? THEN m.from_user_id
                WHEN m.from_user_id = ? THEN m.to_user_id
                ELSE NULL
            END as chat_user_id,
            g.id as group_id,
            g.name as group_name,
            MAX(m.timestamp) as last_message_time
        FROM messages m
        LEFT JOIN groups g ON m.to_group_id = g.id
        WHERE m.from_user_id = ? OR m.to_user_id = ? OR m.to_group_id IS NOT NULL
        GROUP BY chat_user_id, group_id
        ORDER BY last_message_time DESC
        LIMIT ?
    ''', (user_id, user_id, user_id, user_id, limit))
    
    chats = c.fetchall()
    conn.close()
    return [dict(chat) for chat in chats]

def get_unread_count_all(user_id):
    """Получает общее количество непрочитанных сообщений"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Общий чат
    c.execute("SELECT COUNT(*) FROM messages WHERE to_group_id IS NULL AND to_user_id IS NULL AND from_user_id != ? AND is_read = 0", (user_id,))
    general_unread = c.fetchone()[0]
    
    # Личные сообщения
    c.execute("SELECT COUNT(*) FROM messages WHERE to_user_id = ? AND is_read = 0", (user_id,))
    direct_unread = c.fetchone()[0]
    
    # Групповые сообщения (юзер состоит в группе)
    c.execute('''
        SELECT COUNT(*) FROM messages m
        JOIN group_members gm ON m.to_group_id = gm.group_id
        WHERE gm.user_id = ? AND m.from_user_id != ? AND m.is_read = 0
    ''', (user_id, user_id))
    group_unread = c.fetchone()[0]
    
    conn.close()
    return general_unread + direct_unread + group_unread

def mark_all_as_read(user_id):
    """Отмечает все сообщения как прочитанные"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # Общий чат
    c.execute("UPDATE messages SET is_read = 1 WHERE to_group_id IS NULL AND to_user_id IS NULL AND from_user_id != ?", (user_id,))
    
    # Личные
    c.execute("UPDATE messages SET is_read = 1 WHERE to_user_id = ?", (user_id,))
    
    # Групповые
    c.execute('''
        UPDATE messages SET is_read = 1 
        WHERE to_group_id IN (
            SELECT group_id FROM group_members WHERE user_id = ?
        ) AND from_user_id != ?
    ''', (user_id, user_id))
    
    conn.commit()
    conn.close()

def get_message_by_id(message_id):
    """Получает сообщение по ID"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    message = c.fetchone()
    conn.close()
    return dict(message) if message else None

def update_message(message_id, new_content):
    """Обновляет текст сообщения"""
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE messages SET content = ? WHERE id = ?", (new_content, message_id))
    updated = c.rowcount > 0
    conn.commit()
    conn.close()
    return updated
