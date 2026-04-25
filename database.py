"""
database.py - работа с Supabase вместо SQLite
Бро-версия для облака!
"""

import streamlit as st
from supabase import create_client, Client
from datetime import datetime
import bcrypt
import os

# Данные подключения из secrets
SUPABASE_URL = st.secrets["supabase_url"]
SUPABASE_KEY = st.secrets["supabase_key"]

@st.cache_resource
def get_supabase() -> Client:
    """Возвращает клиент Supabase (кэшируется)"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def init_db():
    """Инициализирует таблицы в Supabase через raw SQL"""
    supabase = get_supabase()
    
    # Создаём таблицы (если не существуют)
    # В Supabase лучше создать таблицы через веб-интерфейс или миграции
    # Эта функция для проверки существования первого админа
    
    try:
        # Проверяем, есть ли админ
        response = supabase.table('users').select('*').eq('role', 'admin').limit(1).execute()
        
        if not response.data:
            # Первый пользователь - админ
            hashed = bcrypt.hashpw("admin123".encode(), bcrypt.gensalt())
            supabase.table('users').insert({
                'username': 'admin',
                'password_hash': hashed.decode(),
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }).execute()
            print("[OK] Admin created: admin / admin123")
    except Exception as e:
        print(f"Init error: {e}")

def hash_password(password):
    """Хэширует пароль"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    """Проверяет пароль"""
    return bcrypt.checkpw(password.encode(), hashed.encode())

def create_user(username, password, role='guest'):
    """Создаёт нового пользователя"""
    try:
        supabase = get_supabase()
        hashed = hash_password(password)
        
        response = supabase.table('users').insert({
            'username': username,
            'password_hash': hashed,
            'role': role,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Create user error: {e}")
        return None

def get_user_by_username(username):
    """Получает пользователя по логину"""
    try:
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('username', username).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Get user error: {e}")
        return None

def get_user_by_id(user_id):
    """Получает пользователя по ID"""
    try:
        supabase = get_supabase()
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Get user by id error: {e}")
        return None

def get_all_users():
    """Список всех пользователей"""
    try:
        supabase = get_supabase()
        response = supabase.table('users').select('id, username, role, created_at').order('username').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Get all users error: {e}")
        return []

def delete_user(user_id):
    """Удаляет пользователя и все его данные"""
    try:
        supabase = get_supabase()
        
        # Удаляем сообщения
        supabase.table('messages').delete().eq('from_user_id', user_id).execute()
        
        # Удаляем из групп
        supabase.table('group_members').delete().eq('user_id', user_id).execute()
        
        # Удаляем созданные группы (передаём владение админу)
        admin = get_user_by_username('admin')
        if admin:
            supabase.table('groups').update({'created_by': admin['id']}).eq('created_by', user_id).execute()
        
        # Удаляем пользователя
        supabase.table('users').delete().eq('id', user_id).execute()
        
        return True
    except Exception as e:
        print(f"Delete user error: {e}")
        return False

def update_user_role(user_id, new_role):
    """Меняет роль пользователя"""
    try:
        supabase = get_supabase()
        supabase.table('users').update({'role': new_role}).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Update role error: {e}")
        return False

def create_group(name, created_by):
    """Создаёт новую группу"""
    try:
        supabase = get_supabase()
        
        response = supabase.table('groups').insert({
            'name': name,
            'created_by': created_by,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        if response.data:
            group_id = response.data[0]['id']
            # Добавляем создателя в группу
            supabase.table('group_members').insert({
                'group_id': group_id,
                'user_id': created_by,
                'joined_at': datetime.now().isoformat()
            }).execute()
            return group_id
        return None
    except Exception as e:
        print(f"Create group error: {e}")
        return None

def add_user_to_group(group_id, user_id):
    """Добавляет пользователя в группу"""
    try:
        supabase = get_supabase()
        supabase.table('group_members').insert({
            'group_id': group_id,
            'user_id': user_id,
            'joined_at': datetime.now().isoformat()
        }).execute()
        return True
    except Exception as e:
        print(f"Add to group error: {e}")
        return False

def remove_user_from_group(group_id, user_id):
    """Удаляет пользователя из группы"""
    try:
        supabase = get_supabase()
        supabase.table('group_members').delete().eq('group_id', group_id).eq('user_id', user_id).execute()
        return True
    except Exception as e:
        print(f"Remove from group error: {e}")
        return False

def get_user_groups(user_id):
    """Возвращает все группы пользователя"""
    try:
        supabase = get_supabase()
        response = supabase.table('group_members').select('groups(*)').eq('user_id', user_id).execute()
        
        groups = []
        if response.data:
            for item in response.data:
                if item.get('groups'):
                    groups.append(item['groups'])
        return groups
    except Exception as e:
        print(f"Get user groups error: {e}")
        return []

def get_group_members(group_id):
    """Список участников группы"""
    try:
        supabase = get_supabase()
        response = supabase.table('group_members').select('users(id, username, role)').eq('group_id', group_id).execute()
        
        members = []
        if response.data:
            for item in response.data:
                if item.get('users'):
                    members.append(item['users'])
        return members
    except Exception as e:
        print(f"Get group members error: {e}")
        return []

def get_group_by_id(group_id):
    """Получает группу по ID"""
    try:
        supabase = get_supabase()
        response = supabase.table('groups').select('*').eq('id', group_id).execute()
        
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        print(f"Get group by id error: {e}")
        return None

def get_direct_chat_users(user_id):
    """Возвращает всех пользователей для личных чатов"""
    try:
        supabase = get_supabase()
        response = supabase.table('users').select('id, username, role').neq('id', user_id).order('username').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Get direct chat users error: {e}")
        return []

def save_message(from_user_id, to_group_id, to_user_id, content, file_path=None):
    """Сохраняет сообщение"""
    try:
        supabase = get_supabase()
        
        response = supabase.table('messages').insert({
            'from_user_id': from_user_id,
            'to_group_id': to_group_id,
            'to_user_id': to_user_id,
            'content': content or '',
            'file_path': file_path,
            'is_read': 0,
            'timestamp': datetime.now().isoformat()
        }).execute()
        
        return response.data[0]['id'] if response.data else None
    except Exception as e:
        print(f"Save message error: {e}")
        return None

def get_messages(chat_type, chat_id=None, user_id=None, limit=50, offset=0):
    """Получает сообщения для чата"""
    try:
        supabase = get_supabase()
        
        if chat_type == 'general':
            # Общий чат
            response = supabase.table('messages').select('*, users!from_user_id(username)').\
                is_('to_group_id', 'null').is_('to_user_id', 'null').\
                order('timestamp', desc=True).limit(limit).offset(offset).execute()
        
        elif chat_type == 'group':
            # Групповой чат
            response = supabase.table('messages').select('*, users!from_user_id(username)').\
                eq('to_group_id', chat_id).\
                order('timestamp', desc=True).limit(limit).offset(offset).execute()
        
        elif chat_type == 'direct':
            # Личный чат
            response = supabase.table('messages').select('*, users!from_user_id(username)').\
                or_(f"and(to_user_id.eq.{user_id},from_user_id.eq.{chat_id}),"
                    f"and(to_user_id.eq.{chat_id},from_user_id.eq.{user_id})").\
                order('timestamp', desc=True).limit(limit).offset(offset).execute()
        
        messages = response.data if response.data else []
        return messages[::-1]  # Переворачиваем для хронологии
    except Exception as e:
        print(f"Get messages error: {e}")
        return []

def get_unread_count(user_id, chat_type, chat_id=None):
    """Считает непрочитанные сообщения"""
    try:
        supabase = get_supabase()
        
        if chat_type == 'general':
            response = supabase.table('messages').select('id', count='exact').\
                is_('to_group_id', 'null').is_('to_user_id', 'null').\
                neq('from_user_id', user_id).eq('is_read', 0).execute()
        
        elif chat_type == 'group':
            response = supabase.table('messages').select('id', count='exact').\
                eq('to_group_id', chat_id).neq('from_user_id', user_id).eq('is_read', 0).execute()
        
        elif chat_type == 'direct':
            response = supabase.table('messages').select('id', count='exact').\
                eq('to_user_id', user_id).eq('from_user_id', chat_id).eq('is_read', 0).execute()
        
        return response.count if hasattr(response, 'count') else 0
    except Exception as e:
        print(f"Get unread count error: {e}")
        return 0

def mark_messages_as_read(user_id, chat_type, chat_id=None):
    """Отмечает сообщения как прочитанные"""
    try:
        supabase = get_supabase()
        
        if chat_type == 'general':
            supabase.table('messages').update({'is_read': 1}).\
                is_('to_group_id', 'null').is_('to_user_id', 'null').\
                neq('from_user_id', user_id).eq('is_read', 0).execute()
        
        elif chat_type == 'group':
            supabase.table('messages').update({'is_read': 1}).\
                eq('to_group_id', chat_id).neq('from_user_id', user_id).eq('is_read', 0).execute()
        
        elif chat_type == 'direct':
            supabase.table('messages').update({'is_read': 1}).\
                eq('to_user_id', user_id).eq('from_user_id', chat_id).eq('is_read', 0).execute()
        
        return True
    except Exception as e:
        print(f"Mark as read error: {e}")
        return False

# Экспортируем имя БД для совместимости (не используется в Supabase)
DB_NAME = "supabase_cloud"
