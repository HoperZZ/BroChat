"""
admin.py - админ-панель для управления пользователями
Только для role = 'admin', бро!
"""

import streamlit as st
from database import (
    get_all_users, create_user, delete_user, update_user_role,
    get_user_by_id, get_user_by_username
)
from auth import require_role

def show_admin_panel():
    """
    Главная админ-панель
    Доступна только для админов
    """
    # Проверяем, что пользователь админ
    if not require_role('admin'):
        return
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 👑 Админ-панель")
    
    # Табы для разных функций
    tab1, tab2, tab3 = st.sidebar.tabs(["📋 Все юзеры", "➕ Добавить", "⚙️ Управление"])
    
    with tab1:
        show_users_list()
    
    with tab2:
        show_add_user_form()
    
    with tab3:
        show_advanced_controls()

def show_users_list():
    """Показывает список всех пользователей"""
    st.markdown("#### 👥 Список пользователей")
    
    users = get_all_users()
    
    if not users:
        st.info("Пока нет пользователей, кроме тебя, бро!")
        return
    
    # Создаём таблицу вручную через st.columns
    for user in users:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 1.5, 1.5, 1])
            
            with col1:
                # Иконка для админа
                if user['role'] == 'admin':
                    st.markdown(f"**👑 {user['username']}**")
                elif user['role'] == 'user':
                    st.markdown(f"**👤 {user['username']}**")
                else:
                    st.markdown(f"**👁️ {user['username']}**")
            
            with col2:
                # Роль с цветом
                if user['role'] == 'admin':
                    st.markdown("🟢 **admin**")
                elif user['role'] == 'user':
                    st.markdown("🔵 user")
                else:
                    st.markdown("⚪ guest")
            
            with col3:
                # Дата создания (коротко)
                created = user['created_at'][:10] if user['created_at'] else "недавно"
                st.text(created)
            
            with col4:
                # Кнопки действий
                if user['username'] != st.session_state['username']:
                    if st.button("🗑️", key=f"del_{user['id']}", help="Удалить пользователя"):
                        delete_user_with_confirm(user['id'], user['username'])
                        st.rerun()
                else:
                    st.text("—")  # Нельзя удалить себя
        
        st.divider()

def show_add_user_form():
    """Форма для добавления нового пользователя"""
    st.markdown("#### ➕ Добавить участника")
    
    with st.form("add_user_form"):
        username = st.text_input("👤 Логин", placeholder="Введи уникальный логин")
        password = st.text_input("🔑 Пароль", type="password", placeholder="Придумай пароль")
        role = st.selectbox("🎭 Роль", options=["guest", "user", "admin"], 
                           help="guest - только чтение, user - полный доступ, admin - всё может")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("✅ Добавить", use_container_width=True)
        with col2:
            if st.form_submit_button("🗑️ Очистить", use_container_width=True):
                # Просто очищаем форму (через rerun)
                pass
    
    if submitted:
        if not username or not password:
            st.error("❌ Заполни оба поля, бро!")
            return
        
        if len(password) < 4:
            st.error("❌ Пароль должен быть хотя бы 4 символа!")
            return
        
        # Проверяем, не занят ли логин
        existing = get_user_by_username(username)
        if existing:
            st.error(f"❌ Пользователь {username} уже существует!")
            return
        
        # Создаём пользователя
        user_id = create_user(username, password, role)
        
        if user_id:
            st.success(f"✅ Пользователь **{username}** успешно добавлен!")
            st.info(f"📝 Роль: {role}\n🔐 Пароль: {password}")
            # Даём время прочитать сообщение
            import time
            time.sleep(1.5)
            st.rerun()
        else:
            st.error("❌ Ошибка при создании пользователя!")

def show_advanced_controls():
    """Расширенные возможности управления"""
    st.markdown("#### ⚙️ Управление ролями")
    
    users = get_all_users()
    
    if not users:
        st.info("Нет пользователей для управления")
        return
    
    st.markdown("**Изменить роль пользователя:**")
    
    for user in users:
        # Пропускаем самого себя (нельзя менять свою роль через эту панель)
        if user['username'] == st.session_state['username']:
            continue
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown(f"**{user['username']}**")
            current_role_text = "👑 Админ" if user['role'] == 'admin' else "👤 Пользователь" if user['role'] == 'user' else "👁️ Гость"
            st.caption(f"Текущая роль: {current_role_text}")
        
        with col2:
            # Выбор новой роли
            new_role = st.selectbox(
                "Новая роль",
                options=["guest", "user", "admin"],
                index=["guest", "user", "admin"].index(user['role']),
                key=f"role_{user['id']}",
                label_visibility="collapsed"
            )
        
        with col3:
            if st.button("Применить", key=f"apply_{user['id']}"):
                if new_role != user['role']:
                    update_user_role(user['id'], new_role)
                    st.success(f"✅ {user['username']} теперь {new_role}!")
                    st.rerun()
                else:
                    st.info("Роль не изменилась")
        
        st.divider()

def delete_user_with_confirm(user_id, username):
    """
    Удаляет пользователя после подтверждения
    """
    # Создаём диалог подтверждения через st.modal (в стиле Streamlit)
    st.warning(f"⚠️ Ты уверен, что хочешь удалить **{username}**?")
    st.caption("Это действие нельзя отменить! Все сообщения пользователя будут удалены.")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("❌ Да, удалить", key=f"confirm_del_{user_id}"):
            delete_user(user_id)
            st.success(f"✅ Пользователь {username} удалён!")
            st.rerun()
    with col2:
        if st.button("Отмена", key=f"cancel_del_{user_id}"):
            st.info("Удаление отменено")
            st.rerun()

def show_user_statistics():
    """
    Показывает статистику по пользователям (дополнительная функция)
    """
    st.markdown("#### 📊 Статистика")
    
    users = get_all_users()
    
    if not users:
        return
    
    total_users = len(users)
    admins = sum(1 for u in users if u['role'] == 'admin')
    regular_users = sum(1 for u in users if u['role'] == 'user')
    guests = sum(1 for u in users if u['role'] == 'guest')
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Всего", total_users)
    with col2:
        st.metric("Админы", admins)
    with col3:
        st.metric("Пользователи", regular_users)
    with col4:
        st.metric("Гости", guests)

def quick_add_test_users():
    """
    Быстрое добавление тестовых пользователей (для разработки)
    """
    if st.sidebar.button("🧪 Добавить тестовых юзеров", help="Добавит user1/user2/guest1 для тестов"):
        test_users = [
            ("user1", "pass123", "user"),
            ("user2", "pass123", "user"),
            ("guest1", "guest123", "guest")
        ]
        
        for username, password, role in test_users:
            existing = get_user_by_username(username)
            if not existing:
                create_user(username, password, role)
                st.sidebar.success(f"✅ Добавлен {username}")
            else:
                st.sidebar.info(f"⚠️ {username} уже существует")
        
        st.rerun()

# ========== ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ УДОБСТВА ==========

def is_admin():
    """Проверяет, является ли текущий пользователь админом"""
    return st.session_state.get('role', '') == 'admin'

def get_admin_actions():
    """Возвращает список доступных админ-действий"""
    if not is_admin():
        return []
    
    return [
        "📋 Просмотр пользователей",
        "➕ Добавление пользователей",
        "🗑️ Удаление пользователей",
        "🎭 Смена ролей",
        "📊 Просмотр статистики"
    ]

# ========== КОМПАКТНАЯ ВЕРСИЯ ДЛЯ САЙДБАРА ==========

def show_admin_compact():
    """
    Компактная версия админ-панели для боковой панели
    Занимает меньше места
    """
    if not is_admin():
        return
    
    with st.sidebar.expander("👑 Админ-панель (компактная)", expanded=False):
        # Быстрое добавление пользователя
        with st.form("quick_add"):
            col1, col2 = st.columns([1, 1])
            with col1:
                username = st.text_input("Логин", placeholder="new_user", key="quick_user")
            with col2:
                password = st.text_input("Пароль", type="password", placeholder="пароль", key="quick_pass")
            
            role = st.selectbox("Роль", ["guest", "user", "admin"], key="quick_role")
            
            if st.form_submit_button("➕ Быстро добавить"):
                if username and password:
                    if create_user(username, password, role):
                        st.success(f"✅ {username} добавлен!")
                        st.rerun()
                    else:
                        st.error("Ошибка!")
                else:
                    st.warning("Заполни оба поля")
        
        st.divider()
        
        # Статистика в мини-формате
        users = get_all_users()
        if users:
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Всего", len(users))
            col2.metric("👑", sum(1 for u in users if u['role'] == 'admin'))
            col3.metric("👤", sum(1 for u in users if u['role'] == 'user'))
            col4.metric("👁️", sum(1 for u in users if u['role'] == 'guest'))
        
        # Последние добавленные
        st.caption("📋 Последние 5 юзеров:")
        for user in users[-5:][::-1]:
            role_icon = "👑" if user['role'] == 'admin' else "👤" if user['role'] == 'user' else "👁️"
            st.text(f"{role_icon} {user['username']}")

# ========== ОСНОВНАЯ ФУНКЦИЯ ДЛЯ ВЫЗОВА ==========

def render_admin_section():
    """
    Главная функция рендеринга админ-раздела
    Вызывается из main.py
    """
    if not is_admin():
        return
    
    # Выбор режима отображения
    view_mode = st.sidebar.radio(
        "Режим админки",
        ["🖥️ Полная панель", "📱 Компактный"],
        key="admin_view_mode"
    )
    
    if view_mode == "🖥️ Полная панель":
        show_admin_panel()
    else:
        show_admin_compact()
    
    # Кнопка для тестовых юзеров (только в разработке)
    if st.sidebar.checkbox("🧪 Тестовый режим", key="test_mode_admin"):
        quick_add_test_users()

# ========== ПРИМЕР ИСПОЛЬЗОВАНИЯ ==========
if __name__ == "__main__":
    """
    Тестовый запуск (только для отладки)
    """
    import sys
    from pathlib import Path
    
    # Добавляем текущую директорию в PATH
    sys.path.append(str(Path(__file__).parent))
    
    # Инициализируем БД
    from database import init_db
    init_db()
    
    # Заглушка для Streamlit (имитация session_state)
    if 'session_state' not in st.__dict__:
        st.session_state = {}
    
    # Тестовый вход как админ
    st.session_state['authenticated'] = True
    st.session_state['user_id'] = 1
    st.session_state['username'] = 'admin'
    st.session_state['role'] = 'admin'
    
    st.title("Тест админ-панели")
    render_admin_section()
