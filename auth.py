"""
auth.py - авторизация с тестовым режимом
Бро-версия, полный функционал!
"""

import streamlit as st
import time
from database import verify_password, get_user_by_username, check_db_connection

def login_user(username, password):
    """
    Проверяет логин и пароль
    Returns: (success, user_data or error_message)
    """
    # ========== ТЕСТОВЫЙ РЕЖИМ ==========
    # Пускаем admin без пароля для теста!
    if username == "admin" and password == "":
        user = get_user_by_username("admin")
        if user:
            st.session_state['authenticated'] = True
            st.session_state['user_id'] = user['id']
            st.session_state['username'] = user['username']
            st.session_state['role'] = user['role']
            return True, user
        else:
            return False, "Admin user not found in database!"
    # =====================================
    
    # ========== ТЕСТОВЫЙ РЕЖИМ 2 ==========
    # Пускаем любого пользователя с паролем "test"
    if password == "test":
        user = get_user_by_username(username)
        if user:
            st.session_state['authenticated'] = True
            st.session_state['user_id'] = user['id']
            st.session_state['username'] = user['username']
            st.session_state['role'] = user['role']
            return True, user
    # =====================================
    
    # Проверяем подключение к БД
    db_ok, db_message = check_db_connection()
    if not db_ok:
        return False, f"Database connection error: {db_message}"
    
    # Проверяем блокировку
    block_status, remaining = check_block_status()
    if block_status:
        minutes = remaining // 60
        seconds = remaining % 60
        return False, f"Too many attempts. Wait {minutes} min {seconds} sec"
    
    user = get_user_by_username(username)
    
    if not user:
        increment_failed_attempts()
        return False, "Invalid username or password!"
    
    if verify_password(password, user['password_hash']):
        reset_failed_attempts()
        
        st.session_state['authenticated'] = True
        st.session_state['user_id'] = user['id']
        st.session_state['username'] = user['username']
        st.session_state['role'] = user['role']
        
        return True, user
    else:
        increment_failed_attempts()
        return False, "Invalid username or password!"

def logout():
    """Выход из системы"""
    keys_to_remove = ['authenticated', 'user_id', 'username', 'role', 
                      'failed_attempts', 'block_until', 'active_chat', 'manage_group']
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]

def increment_failed_attempts():
    if 'failed_attempts' not in st.session_state:
        st.session_state['failed_attempts'] = 0
    
    st.session_state['failed_attempts'] += 1
    
    if st.session_state['failed_attempts'] >= 3:
        st.session_state['block_until'] = time.time() + 900

def reset_failed_attempts():
    st.session_state['failed_attempts'] = 0
    if 'block_until' in st.session_state:
        del st.session_state['block_until']

def check_block_status():
    if 'block_until' not in st.session_state:
        return False, 0
    
    block_until = st.session_state['block_until']
    
    if block_until is None or not isinstance(block_until, (int, float)):
        reset_failed_attempts()
        return False, 0
    
    current_time = time.time()
    
    if current_time < block_until:
        remaining = int(block_until - current_time)
        return True, remaining
    else:
        reset_failed_attempts()
        return False, 0

def get_block_remaining_time():
    is_blocked, remaining = check_block_status()
    return remaining if is_blocked else 0

def require_auth():
    if not st.session_state.get('authenticated', False):
        st.warning("Please login first, bro!")
        st.stop()
    return True

def require_role(required_role):
    if not st.session_state.get('authenticated', False):
        st.warning("Please login first!")
        st.stop()
    
    current_role = st.session_state.get('role', 'guest')
    if current_role != required_role and required_role != 'any':
        st.error(f"Access denied! Requires role: {required_role}. Your role: {current_role}")
        st.stop()
    
    return True

def is_admin():
    return st.session_state.get('role', '') == 'admin'

def is_user():
    role = st.session_state.get('role', '')
    return role == 'user' or role == 'admin'

def is_guest():
    return st.session_state.get('role', '') == 'guest'

def test_login_button():
    """Кнопка для тестового входа"""
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎮 Test Login (no password)", use_container_width=True):
            user = get_user_by_username("admin")
            if user:
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = user['id']
                st.session_state['username'] = user['username']
                st.session_state['role'] = user['role']
                st.success("Welcome, admin! (test mode)")
                st.rerun()
            else:
                st.error("Admin user not found!")
    
    with col2:
        if st.button("🔓 Quick Test (any user)", use_container_width=True):
            test_user = get_user_by_username("admin")
            if test_user:
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = test_user['id']
                st.session_state['username'] = test_user['username']
                st.session_state['role'] = test_user['role']
                st.success("Quick login successful!")
                st.rerun()
            else:
                st.error("No users found!")

def show_login_form():
    """Показывает форму входа с тестовыми кнопками"""
    
    # ========== ПРОВЕРКА ПОДКЛЮЧЕНИЯ К БД ==========
    db_ok, db_message = check_db_connection()
    
    if not db_ok:
        st.error("❌ Database Connection Failed!")
        st.warning(f"**Error:** {db_message}")
        st.info("""
        **Possible solutions:**
        1. Check your Supabase credentials in secrets.toml
        2. Make sure the tables exist in Supabase
        3. Check your internet connection
        
        **Test buttons below may still work!**
        """)
        
        # Показываем тестовые кнопки даже при ошибке БД
        st.divider()
        st.markdown("### 🧪 Test Mode (Database Error)")
        test_login_button()
        return
    
    # Показываем статус подключения
    st.success(f"✅ {db_message}")
    
    # ========== ТЕСТОВЫЕ КНОПКИ ==========
    st.markdown("### 🎮 Quick Access (Test Mode)")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("👑 Admin (no pass)", use_container_width=True):
            user = get_user_by_username("admin")
            if user:
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = user['id']
                st.session_state['username'] = user['username']
                st.session_state['role'] = user['role']
                st.success("Logged in as Admin!")
                st.rerun()
            else:
                st.error("Admin user not found!")
    
    with col2:
        if st.button("🔓 Test any user", use_container_width=True):
            any_user = get_user_by_username("admin")
            if any_user:
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = any_user['id']
                st.session_state['username'] = any_user['username']
                st.session_state['role'] = any_user['role']
                st.success(f"Logged in as {any_user['username']}!")
                st.rerun()
    
    with col3:
        if st.button("🐛 Debug mode", use_container_width=True):
            st.info("Debug mode activated. Try login form below.")
    
    st.divider()
    st.markdown("### 🔐 Regular Login")
    
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
        password = st.text_input("Password", type="password", placeholder="Enter password (or leave empty for test)")
        
        col1, col2 = st.columns([1, 1])
        with col1:
            submitted = st.form_submit_button("Login", use_container_width=True)
    
    if submitted:
        if not username:
            st.warning("Fill username field, bro!")
            return
        
        # Если пароль не введён - пробуем тестовый вход
        if not password:
            if username == "admin":
                success, result = login_user("admin", "")
                if success:
                    st.success(f"Welcome back, {username}!")
                    st.rerun()
                else:
                    st.error(f"{result}")
            else:
                st.warning("Regular users need password. For test, click test buttons above.")
        else:
            success, result = login_user(username, password)
            if success:
                st.success(f"Welcome back, {username}!")
                st.rerun()
            else:
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
        
        - **Admin** 👑: Full control, can add/remove users, manage roles
        - **User** 👤: Can create groups, send messages, share files
        - **Guest** 👁️: Read-only access to general chat
        
        **Test login options:**
        - Click "Admin (no pass)" - instant admin access
        - Click "Test any user" - logs in as admin
        - Leave password empty with username "admin"
        
        **Production credentials:**
        - Username: `admin`
        - Password: `admin123`
        """)

def show_registration_disabled():
    st.info("""
    **Registration is admin-only**
    
    New users can only be added by administrator.
    
    If you need an account, contact the admin.
    """)

def show_user_status():
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
