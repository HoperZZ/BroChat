"""
auth.py - авторизация, сессии, блокировки
Bro version, clean and stable
"""

import streamlit as st
import time
from database import verify_password, get_user_by_username

def login_user(username, password):
    """
    Проверяет логин и пароль
    Returns: (success, user_data or error_message)
    """
    # Проверяем блокировку
    block_status, remaining = check_block_status()
    if block_status:
        minutes = remaining // 60
        seconds = remaining % 60
        return False, f"Too many attempts. Wait {minutes} min {seconds} sec"
    
    user = get_user_by_username(username)
    
    if not user:
        # Неправильный логин
        increment_failed_attempts()
        return False, "Invalid username or password!"
    
    # Проверяем пароль
    if verify_password(password, user['password_hash']):
        # Успешный вход! Сбрасываем попытки
        reset_failed_attempts()
        
        # Сохраняем в сессию
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user['id']
        st.session_state['username'] = user['username']
        st.session_state['role'] = user['role']
        
        return True, user
    else:
        # Неправильный пароль
        increment_failed_attempts()
        return False, "Invalid username or password!"

def logout():
    """Выход из системы - чистим сессию"""
    keys_to_remove = ['authenticated', 'user_id', 'username', 'role', 
                      'failed_attempts', 'block_until', 'active_chat', 'manage_group']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def increment_failed_attempts():
    """Увеличиваем счетчик неудачных попыток"""
    if 'failed_attempts' not in st.session_state:
        st.session_state['failed_attempts'] = 0
    
    st.session_state['failed_attempts'] += 1
    
    # Если 3 попытки - блокируем на 15 минут
    if st.session_state['failed_attempts'] >= 3:
        st.session_state['block_until'] = time.time() + 900  # 900 секунд = 15 минут

def reset_failed_attempts():
    """Сбрасываем счетчик попыток"""
    st.session_state['failed_attempts'] = 0
    if 'block_until' in st.session_state:
        del st.session_state['block_until']

def check_block_status():
    """
    Проверяет, заблокирован ли пользователь
    Returns: (is_blocked, remaining_seconds)
    """
    # Если нет данных о блокировке - не заблокирован
    if 'block_until' not in st.session_state:
        return False, 0
    
    block_until = st.session_state['block_until']
    
    # Если значение None или не число - сбрасываем
    if block_until is None or not isinstance(block_until, (int, float)):
        reset_failed_attempts()
        return False, 0
    
    current_time = time.time()
    
    # Если время блокировки еще не прошло
    if current_time < block_until:
        remaining = int(block_until - current_time)
        return True, remaining
    else:
        # Блокировка истекла
        reset_failed_attempts()
        return False, 0

def get_block_remaining_time():
    """Возвращает оставшееся время блокировки в секундах"""
    is_blocked, remaining = check_block_status()
    return remaining if is_blocked else 0

def require_auth():
    """Проверка авторизации для защищенных страниц"""
    if not st.session_state.get('authenticated', False):
        st.warning("Please login first, bro!")
        st.stop()
    return True

def require_role(required_role):
    """Проверяет, есть ли у пользователя нужная роль"""
    if not st.session_state.get('authenticated', False):
        st.warning("Please login first!")
        st.stop()
    
    current_role = st.session_state.get('role', 'guest')
    if current_role != required_role and required_role != 'any':
        st.error(f"Access denied! Requires role: {required_role}. Your role: {current_role}")
        st.stop()
    
    return True

def is_admin():
    """Проверяет, является ли текущий пользователь админом"""
    return st.session_state.get('role', '') == 'admin'

def is_user():
    """Проверяет, является ли текущий пользователь обычным пользователем"""
    role = st.session_state.get('role', '')
    return role == 'user' or role == 'admin'

def is_guest():
    """Проверяет, является ли текущий пользователь гостем"""
    return st.session_state.get('role', '') == 'guest'

def show_login_form():
    """Показывает форму входа"""
    st.markdown("### Welcome to BroChat")
    st.markdown("Login to start messaging")
    
    # Проверка блокировки
    is_blocked, remaining = check_block_status()
    if is_blocked:
        minutes = remaining // 60
        seconds = remaining % 60
        st.error(f"Account temporarily blocked! Wait {minutes} min {seconds} sec")
        return
    
    # Форма входа
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="Enter your username")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Login", use_container_width=True)
    
    if submitted:
        if not username or not password:
            st.warning("Fill both fields, bro!")
            return
        
        success, result = login_user(username, password)
        if success:
            st.success(f"Welcome back, {username}!")
            st.rerun()
        else:
            # Показываем количество оставшихся попыток
            if 'failed_attempts' in st.session_state:
                attempts_left = 3 - st.session_state['failed_attempts']
                if attempts_left > 0:
                    st.error(f"{result} Attempts left: {attempts_left}")
                else:
                    st.error(f"{result}")
            else:
                st.error(f"{result}")
    
    # Информация о ролях
    with st.expander("ℹ️ About roles"):
        st.markdown("""
        **Roles in BroChat:**
        
        - **Admin** : Full control, can add/remove users, manage roles
        - **User** : Can create groups, send messages, share files
        - **Guest** : Read-only access to general chat
        
        **Default admin account:**
        - Login: `admin`
        - Password: `admin123`
        
        *For security, change password after first login*
        """)
    
    # Советы
    st.caption("Tip: First launch creates admin account automatically")

def show_registration_disabled():
    """Сообщение о том, что регистрация только через админа"""
    st.info("""
    **Registration is admin-only**
    
    New users can only be added by administrator.
    
    If you need an account, contact the admin.
    """)

# Функция для отображения текущего статуса пользователя
def show_user_status():
    """Показывает статус текущего пользователя в sidebar"""
    if st.session_state.get('authenticated', False):
        role = st.session_state['role']
        role_icon = "👑" if role == 'admin' else "👤" if role == 'user' else "👁️"
        role_name = "Admin" if role == 'admin' else "User" if role == 'user' else "Guest"
        
        st.sidebar.markdown(f"""
        ---
        **Your status:**
        {role_icon} **{st.session_state['username']}**  
        Role: {role_name}
        ---
        """)

# Тестовая функция для проверки (только для дебага)
if __name__ == "__main__":
    # Заглушка для тестирования
    if 'session_state' not in st.__dict__:
        st.session_state = {}
    
    st.title("Auth Module Test")
    
    col1, col2 = st.columns(2)
    with col1:
        show_login_form()
    with col2:
        st.markdown("### Current Session State")
        st.json({
            'authenticated': st.session_state.get('authenticated', False),
            'username': st.session_state.get('username', None),
            'role': st.session_state.get('role', None),
            'failed_attempts': st.session_state.get('failed_attempts', 0),
            'block_until': st.session_state.get('block_until', None)
        })
        
        if st.session_state.get('authenticated', False):
            if st.button("Logout"):
                logout()
                st.rerun()
