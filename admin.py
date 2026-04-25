"""
admin.py - админ-панель с бэкапом БД
Теперь с экспортом/импортом, бро!
"""

import streamlit as st
import sqlite3
import os
import datetime
import json
from pathlib import Path
from database import (
    get_all_users, create_user, delete_user, update_user_role,
    get_user_by_username, DB_NAME
)
from auth import require_role

# Константы
BACKUP_DIR = "backups"

def init_backup_dir():
    """Создаёт папку для бэкапов"""
    Path(BACKUP_DIR).mkdir(exist_ok=True)

def backup_database():
    """Создаёт бэкап базы данных"""
    try:
        init_backup_dir()
        
        # Создаём имя файла с датой
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"chat_backup_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        
        # Копируем файл БД
        import shutil
        shutil.copy2(DB_NAME, backup_path)
        
        # Дополнительно создаём JSON экспорт для читаемости
        json_backup = export_to_json()
        
        return True, backup_name, json_backup
    except Exception as e:
        return False, str(e), None

def export_to_json():
    """Экспортирует данные в JSON"""
    try:
        conn = sqlite3.connect(DB_NAME)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Собираем все данные
        data = {
            "export_date": datetime.datetime.now().isoformat(),
            "version": "1.0",
            "users": [],
            "groups": [],
            "group_members": [],
            "messages": []
        }
        
        # Пользователи
        c.execute("SELECT id, username, role, created_at FROM users")
        for row in c.fetchall():
            data["users"].append(dict(row))
        
        # Группы
        c.execute("SELECT * FROM groups")
        for row in c.fetchall():
            data["groups"].append(dict(row))
        
        # Участники групп
        c.execute("SELECT * FROM group_members")
        for row in c.fetchall():
            data["group_members"].append(dict(row))
        
        # Сообщения
        c.execute("SELECT * FROM messages ORDER BY id DESC LIMIT 1000")
        for row in c.fetchall():
            data["messages"].append(dict(row))
        
        conn.close()
        
        # Сохраняем JSON
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = os.path.join(BACKUP_DIR, f"chat_export_{timestamp}.json")
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        return json_path
    except Exception as e:
        return None

def restore_from_backup(uploaded_file):
    """Восстанавливает базу данных из загруженного файла"""
    try:
        # Проверяем расширение
        if uploaded_file.name.endswith('.db'):
            # Восстановление из SQLite
            import shutil
            
            # Создаём бэкап текущей БД перед восстановлением
            backup_before, _, _ = backup_database()
            
            # Закрываем текущие соединения (важно!)
            sqlite3.connect(DB_NAME).close()
            
            # Восстанавливаем файл
            with open(DB_NAME, 'wb') as f:
                f.write(uploaded_file.getbuffer())
            
            return True, f"Database restored from {uploaded_file.name}. Backup saved."
        
        elif uploaded_file.name.endswith('.json'):
            # Восстановление из JSON
            import json
            
            # Загружаем JSON
            data = json.load(uploaded_file)
            
            # Создаём бэкап текущей БД
            backup_before, _, _ = backup_database()
            
            # Очищаем и пересоздаём БД
            conn = sqlite3.connect(DB_NAME)
            c = conn.cursor()
            
            # Очищаем таблицы
            c.execute("DELETE FROM messages")
            c.execute("DELETE FROM group_members")
            c.execute("DELETE FROM groups")
            c.execute("DELETE FROM users")
            
            # Восстанавливаем пользователей
            for user in data.get('users', []):
                c.execute("""
                    INSERT OR REPLACE INTO users (id, username, password_hash, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (user['id'], user['username'], user.get('password_hash', ''), 
                      user['role'], user['created_at']))
            
            # Восстанавливаем группы
            for group in data.get('groups', []):
                c.execute("""
                    INSERT OR REPLACE INTO groups (id, name, created_by, created_at)
                    VALUES (?, ?, ?, ?)
                """, (group['id'], group['name'], group['created_by'], group['created_at']))
            
            # Восстанавливаем участников групп
            for member in data.get('group_members', []):
                c.execute("""
                    INSERT OR REPLACE INTO group_members (group_id, user_id, joined_at)
                    VALUES (?, ?, ?)
                """, (member['group_id'], member['user_id'], member['joined_at']))
            
            # Восстанавливаем сообщения
            for msg in data.get('messages', []):
                c.execute("""
                    INSERT OR REPLACE INTO messages (id, from_user_id, to_group_id, to_user_id, 
                                                   content, file_path, is_read, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (msg['id'], msg['from_user_id'], msg.get('to_group_id'), msg.get('to_user_id'),
                      msg.get('content'), msg.get('file_path'), msg.get('is_read', 0), msg['timestamp']))
            
            conn.commit()
            conn.close()
            
            return True, f"Database restored from JSON. Backup saved."
        
        else:
            return False, "Unsupported file format. Use .db or .json"
            
    except Exception as e:
        return False, f"Restore failed: {str(e)}"

def list_backups():
    """Показывает список доступных бэкапов"""
    init_backup_dir()
    
    backups = []
    for file in os.listdir(BACKUP_DIR):
        if file.endswith('.db') or file.endswith('.json'):
            file_path = os.path.join(BACKUP_DIR, file)
            stat = os.stat(file_path)
            backups.append({
                'name': file,
                'size': stat.st_size,
                'modified': datetime.datetime.fromtimestamp(stat.st_mtime)
            })
    
    # Сортируем по дате (новые сверху)
    backups.sort(key=lambda x: x['modified'], reverse=True)
    return backups

def download_backup(backup_name):
    """Скачивает выбранный бэкап"""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if os.path.exists(backup_path):
        with open(backup_path, 'rb') as f:
            return f.read()
    return None

def delete_backup(backup_name):
    """Удаляет бэкап"""
    backup_path = os.path.join(BACKUP_DIR, backup_name)
    if os.path.exists(backup_path):
        os.remove(backup_path)
        return True
    return False

def show_admin_panel():
    """
    Главная админ-панель
    Доступна только для админов
    """
    # Проверяем, что пользователь админ
    if not require_role('admin'):
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Admin Panel")
    
    # Табы для разных функций
    tab1, tab2, tab3, tab4 = st.sidebar.tabs(["Users", "Add User", "Roles", "Backup"])
    
    with tab1:
        show_users_list()
    
    with tab2:
        show_add_user_form()
    
    with tab3:
        show_advanced_controls()
    
    with tab4:
        show_backup_panel()

def show_backup_panel():
    """Панель управления бэкапами"""
    st.markdown("#### Database Backup & Restore")
    
    # Создаём бэкап
    st.markdown("##### Create Backup")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(" Backup Database", use_container_width=True):
            with st.spinner("Creating backup..."):
                success, result, json_path = backup_database()
                if success:
                    st.success(f"Backup created: {result}")
                    
                    # Предлагаем скачать
                    backup_path = os.path.join(BACKUP_DIR, result)
                    with open(backup_path, 'rb') as f:
                        st.download_button(
                            label="Download Backup",
                            data=f,
                            file_name=result,
                            mime="application/octet-stream"
                        )
                    
                    if json_path and os.path.exists(json_path):
                        with open(json_path, 'rb') as f:
                            st.download_button(
                                label="Download JSON Export",
                                data=f,
                                file_name=os.path.basename(json_path),
                                mime="application/json"
                            )
                else:
                    st.error(f"Backup failed: {result}")
    
    with col2:
        if st.button(" Export to JSON", use_container_width=True):
            with st.spinner("Exporting to JSON..."):
                json_path = export_to_json()
                if json_path and os.path.exists(json_path):
                    with open(json_path, 'rb') as f:
                        st.download_button(
                            label="Download JSON",
                            data=f,
                            file_name=os.path.basename(json_path),
                            mime="application/json"
                        )
                    st.success("JSON export created!")
                else:
                    st.error("JSON export failed")
    
    st.divider()
    
    # Восстановление из файла
    st.markdown("##### Restore from Backup")
    uploaded_file = st.file_uploader(
        "Upload backup file (.db or .json)",
        type=['db', 'json'],
        key="restore_upload"
    )
    
    if uploaded_file:
        st.warning("⚠️ Restoring will overwrite current database! Current data will be backed up automatically.")
        
        if st.button("Restore Database", use_container_width=True):
            with st.spinner("Restoring database..."):
                success, message = restore_from_backup(uploaded_file)
                if success:
                    st.success(message)
                    st.info("Please restart the application to see changes")
                    if st.button("Restart Now"):
                        st.rerun()
                else:
                    st.error(message)
    
    st.divider()
    
    # Список бэкапов
    st.markdown("##### Available Backups")
    backups = list_backups()
    
    if not backups:
        st.info("No backups found")
    else:
        for backup in backups:
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                icon = "📦" if backup['name'].endswith('.db') else "📄"
                st.write(f"{icon} {backup['name']}")
            
            with col2:
                size_kb = backup['size'] / 1024
                if size_kb < 1024:
                    st.write(f"{size_kb:.1f} KB")
                else:
                    st.write(f"{size_kb/1024:.1f} MB")
            
            with col3:
                time_str = backup['modified'].strftime("%Y-%m-%d %H:%M")
                st.write(time_str)
            
            with col4:
                # Кнопка скачивания
                file_data = download_backup(backup['name'])
                if file_data:
                    st.download_button(
                        label="Download",
                        data=file_data,
                        file_name=backup['name'],
                        key=f"download_{backup['name']}"
                    )
                
                # Кнопка удаления
                if st.button("Delete", key=f"del_backup_{backup['name']}"):
                    if delete_backup(backup['name']):
                        st.success(f"Deleted {backup['name']}")
                        st.rerun()

def show_users_list():
    """Показывает список всех пользователей"""
    st.markdown("#### Users List")
    
    users = get_all_users()
    
    if not users:
        st.info("No users yet")
        return
    
    # Создаём таблицу
    for user in users:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
            
            with col1:
                if user['role'] == 'admin':
                    st.markdown(f"**👑 {user['username']}**")
                elif user['role'] == 'user':
                    st.markdown(f"**👤 {user['username']}**")
                else:
                    st.markdown(f"**👁️ {user['username']}**")
            
            with col2:
                if user['role'] == 'admin':
                    st.markdown("🟢 **admin**")
                elif user['role'] == 'user':
                    st.markdown("🔵 user")
                else:
                    st.markdown("⚪ guest")
            
            with col3:
                created = user['created_at'][:10] if user['created_at'] else "recently"
                st.text(created)
            
            with col4:
                if user['username'] != st.session_state['username']:
                    if st.button("Delete", key=f"del_{user['id']}", help="Delete user"):
                        delete_user_with_confirm(user['id'], user['username'])
                        st.rerun()
                else:
                    st.text("—")
        
        st.divider()

def show_add_user_form():
    """Форма для добавления нового пользователя"""
    st.markdown("#### Add User")
    
    with st.form("add_user_form"):
        username = st.text_input("Username", placeholder="Enter unique username")
        password = st.text_input("Password", type="password", placeholder="Enter password")
        role = st.selectbox("Role", options=["guest", "user", "admin"])
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Add User", use_container_width=True)
    
    if submitted:
        if not username or not password:
            st.error("Fill both fields!")
            return
        
        if len(password) < 4:
            st.error("Password must be at least 4 characters!")
            return
        
        existing = get_user_by_username(username)
        if existing:
            st.error(f"User {username} already exists!")
            return
        
        user_id = create_user(username, password, role)
        
        if user_id:
            st.success(f"User {username} added successfully!")
            st.info(f"Role: {role}")
            st.rerun()
        else:
            st.error("Error creating user!")

def show_advanced_controls():
    """Расширенные возможности управления"""
    st.markdown("#### Role Management")
    
    users = get_all_users()
    
    if not users:
        st.info("No users to manage")
        return
    
    st.markdown("**Change user role:**")
    
    for user in users:
        if user['username'] == st.session_state['username']:
            continue
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**{user['username']}**")
            current_role_text = "Admin" if user['role'] == 'admin' else "User" if user['role'] == 'user' else "Guest"
            st.caption(f"Current: {current_role_text}")
        
        with col2:
            new_role = st.selectbox(
                "New role",
                options=["guest", "user", "admin"],
                index=["guest", "user", "admin"].index(user['role']),
                key=f"role_{user['id']}",
                label_visibility="collapsed"
            )
        
        with col3:
            if st.button("Apply", key=f"apply_{user['id']}"):
                if new_role != user['role']:
                    update_user_role(user['id'], new_role)
                    st.success(f"{user['username']} is now {new_role}!")
                    st.rerun()
                else:
                    st.info("Role unchanged")
        
        st.divider()

def delete_user_with_confirm(user_id, username):
    """Удаляет пользователя после подтверждения"""
    st.warning(f"⚠️ Are you sure you want to delete **{username}**?")
    st.caption("This action cannot be undone! All user messages will be deleted.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Yes, Delete", key=f"confirm_del_{user_id}"):
            delete_user(user_id)
            st.success(f"User {username} deleted!")
            st.rerun()
    with col2:
        if st.button("Cancel", key=f"cancel_del_{user_id}"):
            st.info("Deletion cancelled")
            st.rerun()

def quick_add_test_users():
    """Быстрое добавление тестовых пользователей"""
    if st.sidebar.button(" Add Test Users", help="Add test users for testing"):
        test_users = [
            ("user1", "pass123", "user"),
            ("user2", "pass123", "user"),
            ("guest1", "guest123", "guest")
        ]
        
        for username, password, role in test_users:
            existing = get_user_by_username(username)
            if not existing:
                create_user(username, password, role)
                st.sidebar.success(f"Added {username}")
            else:
                st.sidebar.info(f"{username} already exists")
        
        st.rerun()

# Компактная версия для сайдбара
def render_admin_section():
    """Главная функция рендеринга админ-раздела"""
    if st.session_state.get('role') != 'admin':
        return
    
    # Выбор режима отображения
    view_mode = st.sidebar.radio(
        "Admin mode",
        ["Full Panel", "Compact"],
        key="admin_view_mode"
    )
    
    if view_mode == "Full Panel":
        show_admin_panel()
    else:
        show_admin_compact()
    
    # Тестовые юзеры
    if st.sidebar.checkbox("Test Mode", key="test_mode_admin"):
        quick_add_test_users()

def show_admin_compact():
    """Компактная версия админ-панели"""
    with st.sidebar.expander("Admin Panel (Compact)", expanded=False):
        # Быстрое добавление
        with st.form("quick_add"):
            username = st.text_input("Username", placeholder="new_user", key="quick_user")
            password = st.text_input("Password", type="password", placeholder="password", key="quick_pass")
            role = st.selectbox("Role", ["guest", "user", "admin"], key="quick_role")
            
            if st.form_submit_button("Quick Add"):
                if username and password:
                    if create_user(username, password, role):
                        st.success(f"Added {username}!")
                        st.rerun()
                    else:
                        st.error("Error!")
                else:
                    st.warning("Fill both fields")
        
        st.divider()
        
        # Статистика
        users = get_all_users()
        if users:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Total", len(users))
            col2.metric("👑", sum(1 for u in users if u['role'] == 'admin'))
            col3.metric("👤", sum(1 for u in users if u['role'] == 'user'))
            col4.metric("👁️", sum(1 for u in users if u['role'] == 'guest'))
        
        # Быстрый бэкап
        if st.button(" Quick Backup", use_container_width=True):
            success, result, _ = backup_database()
            if success:
                st.success(f"Backup: {result}")
            else:
                st.error(f"Failed: {result}")
