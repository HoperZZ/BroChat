"""
database.py - работа с Supabase для Streamlit Cloud
Исправленная версия с правильными таблицами, бро!
"""

import streamlit as st
from datetime import datetime
import bcrypt
import os

# Пытаемся импортировать Supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    print("Warning: Supabase not installed.")

# Данные подключения
def get_supabase():
    if not SUPABASE_AVAILABLE:
        return None
    
    try:
        SUPABASE_URL = st.secrets.get("supabase_url", "")
        SUPABASE_KEY = st.secrets.get("supabase_key", "")
        
        if SUPABASE_URL and SUPABASE_KEY:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        else:
            print("DEBUG: Missing URL or KEY")
            return None
    except Exception as e:
        print(f"DEBUG: Exception in get_supabase: {e}")
        return None

def init_db():
    """Инициализация БД - создаём админа если нет"""
    supabase = get_supabase()
    if not supabase:
        return
    
    try:
        # Проверяем есть ли пользователи
        response = supabase.table('users').select('*').limit(1).execute()
        
        if not response.data:
            # Нет пользователей - создаём админа
            supabase.table('users').insert({
                'username': 'admin',
                'password_hash': '',  # Пустой пароль для теста
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }).execute()
            print("Admin created: admin / no password")
        else:
            # Проверяем есть ли именно админ
            admin_check = supabase.table('users').select('*').eq('username', 'admin').limit(1).execute()
            if not admin_check.data:
                # Нет админа - создаём
                supabase.table('users').insert({
                    'username': 'admin',
                    'password_hash': '',
                    'role': 'admin',
                    'created_at': datetime.now().isoformat()
                }).execute()
                print("Admin created: admin / no password")
    except Exception as e:
        print(f"Init error: {e}")

def create_admin_if_not_exists():
    """Принудительное создание админа если его нет"""
    supabase = get_supabase()
    if not supabase:
        print("Supabase not available")
        return False
    
    try:
        # Проверяем через прямой запрос
        response = supabase.table('users').select('*').eq('username', 'admin').execute()
        
        if not response.data:
            # Создаём админа с пустым паролем
            supabase.table('users').insert({
                'username': 'admin',
                'password_hash': '',
                'role': 'admin',
                'created_at': datetime.now().isoformat()
            }).execute()
            print("Admin created! (no password)")
            return True
        else:
            print(f"Admin already exists: {response.data[0]['id']}")
            return True
    except Exception as e:
        print(f"Create admin error: {e}")
        return False

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(password, hashed):
    try:
        # Если хеш пустой - пускаем без пароля (для теста)
        if hashed == "" and password == "":
            return True
        if hashed == "" and password == "admin":
            return True
        if hashed == "" and password == "1234":
            return True
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except:
        return False

def create_user(username, password, role='guest'):
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
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
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
        print(f"DEBUG: Looking for username: {username}")
        response = supabase.table('users').select('*').eq('username', username).execute()
        print(f"DEBUG: Response data: {response.data}")
        
        if response.data and len(response.data) > 0:
            return response.data[0]
        else:
            print(f"DEBUG: No user found with username: {username}")
            return None
    except Exception as e:
        print(f"Get user error: {e}")
        return None

def get_user_by_id(user_id):
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
        response = supabase.table('users').select('*').eq('id', user_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Get user by id error: {e}")
        return None

def get_all_users():
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        response = supabase.table('users').select('id, username, role, created_at').order('username').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Get all users error: {e}")
        return []

def delete_user(user_id):
    supabase = get_supabase()
    if not supabase:
        return False
    
    try:
        supabase.table('messages').delete().eq('from_user_id', user_id).execute()
        supabase.table('group_members').delete().eq('user_id', user_id).execute()
        supabase.table('users').delete().eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Delete user error: {e}")
        return False

def update_user_role(user_id, new_role):
    supabase = get_supabase()
    if not supabase:
        return False
    
    try:
        supabase.table('users').update({'role': new_role}).eq('id', user_id).execute()
        return True
    except Exception as e:
        print(f"Update role error: {e}")
        return False

def create_group(name, created_by):
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
        response = supabase.table('groups').insert({
            'name': name,
            'created_by': created_by,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        if response.data:
            group_id = response.data[0]['id']
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
    supabase = get_supabase()
    if not supabase:
        return False
    
    try:
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
    supabase = get_supabase()
    if not supabase:
        return False
    
    try:
        supabase.table('group_members').delete().eq('group_id', group_id).eq('user_id', user_id).execute()
        return True
    except Exception as e:
        print(f"Remove from group error: {e}")
        return False

def get_user_groups(user_id):
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
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
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
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
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
        response = supabase.table('groups').select('*').eq('id', group_id).execute()
        return response.data[0] if response.data else None
    except Exception as e:
        print(f"Get group by id error: {e}")
        return None

def get_direct_chat_users(user_id):
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        response = supabase.table('users').select('id, username, role').neq('id', user_id).order('username').execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Get direct chat users error: {e}")
        return []

def save_message(from_user_id, to_group_id, to_user_id, content, file_path=None):
    supabase = get_supabase()
    if not supabase:
        return None
    
    try:
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
    supabase = get_supabase()
    if not supabase:
        return []
    
    try:
        if chat_type == 'general':
            response = supabase.table('messages').select('*, users!from_user_id(username)').\
                is_('to_group_id', 'null').is_('to_user_id', 'null').\
                order('timestamp', desc=True).limit(limit).offset(offset).execute()
        elif chat_type == 'group':
            response = supabase.table('messages').select('*, users!from_user_id(username)').\
                eq('to_group_id', chat_id).\
                order('timestamp', desc=True).limit(limit).offset(offset).execute()
        elif chat_type == 'direct':
            response = supabase.table('messages').select('*, users!from_user_id(username)').\
                or_(f"and(to_user_id.eq.{user_id},from_user_id.eq.{chat_id}),"
                    f"and(to_user_id.eq.{chat_id},from_user_id.eq.{user_id})").\
                order('timestamp', desc=True).limit(limit).offset(offset).execute()
        else:
            return []
        
        messages = response.data if response.data else []
        return messages[::-1]
    except Exception as e:
        print(f"Get messages error: {e}")
        return []

def get_unread_count(user_id, chat_type, chat_id=None):
    supabase = get_supabase()
    if not supabase:
        return 0
    
    try:
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
        else:
            return 0
        
        return response.count if hasattr(response, 'count') else 0
    except Exception as e:
        print(f"Get unread count error: {e}")
        return 0

def mark_messages_as_read(user_id, chat_type, chat_id=None):
    supabase = get_supabase()
    if not supabase:
        return False
    
    try:
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

# ========== ФУНКЦИИ ДЛЯ ПРОВЕРКИ ПОДКЛЮЧЕНИЯ ==========

def check_db_connection():
    """Проверяет подключение к Supabase"""
    try:
        supabase = get_supabase()
        if not supabase:
            return False, "Supabase client not initialized. Check secrets configuration."
        
        # Пробуем выполнить простой запрос
        supabase.table('users').select('id').limit(1).execute()
        
        return True, "Connected to Supabase. Tables exist."
        
    except Exception as e:
        error_msg = str(e)
        if "API key" in error_msg or "Invalid JWT" in error_msg:
            return False, "Invalid API key. Check your supabase_key in secrets."
        elif "relation" in error_msg and "does not exist" in error_msg:
            return False, "Table 'users' not found. Please create tables in Supabase first."
        else:
            return False, f"Connection failed: {error_msg[:100]}"

def get_supabase_url():
    """Возвращает URL Supabase для отладки"""
    try:
        return st.secrets.get("supabase_url", "Not configured")
    except:
        return "Secrets not available"

# Константа для совместимости
DB_NAME = "supabase_cloud"
