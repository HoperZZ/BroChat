"""
main.py - Точка входа мессенджера BroChat
Бро-версия, полный функционал
"""

import streamlit as st
from database import init_db
from auth import show_login_form, logout
from admin import render_admin_section
from chat import show_chat_interface, show_group_management

# Конфиг страницы (первым делом!)
st.set_page_config(
    page_title="BroChat - Messenger",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="auto"
)

def apply_mobile_styles():
    """Мобильная адаптация"""
    st.markdown("""
    <style>
    /* Основные стили для мобил */
    @media (max-width: 768px) {
        .stColumn {
            flex: 1 !important;
            min-width: 100% !important;
        }
        
        .stTextArea textarea, .stTextInput input {
            font-size: 16px !important;
        }
        
        .chat-message {
            font-size: 14px !important;
            padding: 10px !important;
        }
        
        .stButton button {
            width: 100% !important;
            margin: 5px 0 !important;
        }
        
        [data-testid="stSidebar"] {
            width: 85% !important;
            transform: translateX(-100%);
            transition: transform 0.3s ease;
        }
        
        [data-testid="stSidebar"][aria-expanded="true"] {
            transform: translateX(0);
        }
        
        .st-emotion-cache-1v0mbdj {
            position: fixed;
            top: 10px;
            left: 10px;
            z-index: 999;
            background: #fff;
            border-radius: 50%;
            padding: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }
        
        .main .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
    }
    
    /* Анимация сообщений */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .chat-message {
        animation: fadeIn 0.3s ease;
    }
    
    /* Скроллбар */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f1f1;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #888;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #555;
    }
    
    .stAlert {
        border-radius: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

def init_session_state():
    """Инициализация session_state"""
    if 'authenticated' not in st.session_state:
        st.session_state['authenticated'] = False
    if 'user_id' not in st.session_state:
        st.session_state['user_id'] = None
    if 'username' not in st.session_state:
        st.session_state['username'] = None
    if 'role' not in st.session_state:
        st.session_state['role'] = 'guest'
    if 'active_chat' not in st.session_state:
        st.session_state['active_chat'] = None
    if 'manage_group' not in st.session_state:
        st.session_state['manage_group'] = None
    if 'failed_attempts' not in st.session_state:
        st.session_state['failed_attempts'] = 0
    if 'block_until' not in st.session_state:
        st.session_state['block_until'] = None

def show_header():
    """Показывает шапку приложения"""
    if st.session_state.get('authenticated'):
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("<h1 style='text-align: center;'>💬 BroChat</h1>", unsafe_allow_html=True)
            role_text = "Admin" if st.session_state['role'] == 'admin' else "User" if st.session_state['role'] == 'user' else "Guest"
            st.caption(f"Hello, {st.session_state['username']} | Role: {role_text}")
    else:
        st.markdown("<h1 style='text-align: center;'>💬 BroChat</h1>", unsafe_allow_html=True)
        st.caption("Your reliable messenger, bro!")

def show_mobile_note():
    """Подсказка для мобильных"""
    if st.sidebar.button("ℹ️ How to open chats on phone?"):
        st.sidebar.info("""
        **On phone:**
        1. Click ☰ in top left corner
        2. Select chat from list
        3. Enjoy chatting!
        
        To close menu - click X or swipe left
        """)

def show_guest_mode():
    """Гостевой режим"""
    st.divider()
    with st.expander("👁️ Enter as guest (read only)"):
        st.warning("""
        **Guest mode:**
        - View general chat only
        - Cannot send messages
        - No groups and private chats
        
        For full access ask admin to add you!
        """)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("Enter as Guest", use_container_width=True):
                st.session_state['authenticated'] = True
                st.session_state['user_id'] = 0
                st.session_state['username'] = 'guest'
                st.session_state['role'] = 'guest'
                st.rerun()

def main():
    """Главная функция"""
    
    # Инициализация БД с обработкой ошибок
    try:
        init_db()
    except Exception as e:
        st.error(f"Database init error: {str(e)}")
        st.info("Make sure you have write permissions in current directory")
        return
    
    apply_mobile_styles()
    init_session_state()
    
    # Шапка
    show_header()
    
    # Мобильная подсказка для авторизованных
    if st.session_state.get('authenticated'):
        show_mobile_note()
    
    st.divider()
    
    # Проверяем авторизацию
    if not st.session_state['authenticated']:
        # Показываем форму входа
        show_login_form()
        
        # Гостевой режим
        show_guest_mode()
        
    else:
        # Основной интерфейс для авторизованных
        
        # Боковая панель с системной инфой (для дебага)
        with st.sidebar:
            if st.checkbox("🛠️ System Info", key="system_info"):
                st.json({
                    "Authenticated": st.session_state.get('authenticated'),
                    "User ID": st.session_state.get('user_id'),
                    "Username": st.session_state.get('username'),
                    "Role": st.session_state.get('role'),
                    "Active Chat": st.session_state.get('active_chat')
                })
        
        # Админ-панель (только для админов)
        if st.session_state['role'] == 'admin':
            try:
                render_admin_section()
            except Exception as e:
                st.error(f"Admin panel error: {str(e)}")
        
        # Интерфейс чата
        try:
            show_chat_interface()
        except Exception as e:
            st.error(f"Chat error: {str(e)}")
            st.info("Try refreshing the page (F5)")
        
        # Управление группой (если открыто)
        try:
            show_group_management()
        except Exception as e:
            # Не критичная ошибка
            pass
        
        # Кнопка выхода в сайдбаре
        with st.sidebar:
            st.divider()
            if st.button("🚪 Logout", use_container_width=True):
                logout()
                st.rerun()

# Точка входа
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"Critical error: {str(e)}")
        st.info("Check that all modules exist: database.py, auth.py, admin.py, chat.py")
        st.code("""
        Required files:
        - main.py
        - database.py
        - auth.py
        - admin.py
        - chat.py
        
        Install dependencies:
        pip install streamlit bcrypt pillow
        
        Run:
        streamlit run main.py
        """)
