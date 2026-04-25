"""
chat.py - основной движок чата
С удалением участников из групп, бро!
"""

import streamlit as st
import os
import datetime
from pathlib import Path
from database import (
    get_user_by_id, get_user_groups, get_direct_chat_users,
    save_message, get_messages, get_unread_count, mark_messages_as_read,
    get_group_members, add_user_to_group, remove_user_from_group, 
    get_all_users, get_group_by_id, create_group
)
from auth import require_auth

# Константы
UPLOAD_DIR = "uploads"
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200 MB

def init_chat():
    """Инициализация чата - создаём папки для файлов"""
    Path(UPLOAD_DIR).mkdir(exist_ok=True)

def show_chat_interface():
    """Главный интерфейс чата"""
    require_auth()
    
    # Инициализируем
    init_chat()
    
    # Боковая панель со списком чатов
    with st.sidebar:
        st.markdown(f"### Chats")
        st.caption(f"Hi, **{st.session_state['username']}**!")
        
        # Показываем список чатов
        render_chat_list()
        
        st.divider()
        
        # Кнопка создания группы
        if st.session_state['role'] in ['admin', 'user']:
            create_group_dialog()
    
    # Основная область - показываем активный чат
    if 'active_chat' in st.session_state and st.session_state['active_chat']:
        render_active_chat()
    else:
        # Приветственный экран
        show_welcome_screen()

def render_chat_list():
    """Отображает список всех чатов пользователя"""
    user_id = st.session_state['user_id']
    
    # 1. Общий чат
    unread_general = get_unread_count(user_id, 'general')
    unread_badge = f" ({unread_general})" if unread_general > 0 else ""
    
    if st.button(f"🌍 General Chat{unread_badge}", use_container_width=True, key="chat_general"):
        st.session_state['active_chat'] = {
            'type': 'general',
            'id': None,
            'name': 'General Chat'
        }
        mark_messages_as_read(user_id, 'general')
        st.rerun()
    
    # 2. Группы
    groups = get_user_groups(user_id)
    if groups:
        st.markdown("#### 👥 Groups")
        for group in groups:
            unread = get_unread_count(user_id, 'group', group['id'])
            unread_badge = f" ({unread})" if unread > 0 else ""
            
            col1, col2 = st.columns([0.8, 0.2])
            with col1:
                if st.button(f"👥 {group['name']}{unread_badge}", 
                           use_container_width=True, 
                           key=f"group_{group['id']}"):
                    st.session_state['active_chat'] = {
                        'type': 'group',
                        'id': group['id'],
                        'name': group['name']
                    }
                    mark_messages_as_read(user_id, 'group', group['id'])
                    st.rerun()
            
            with col2:
                if st.button("⚙️", key=f"settings_{group['id']}", help="Manage group"):
                    st.session_state['manage_group'] = group['id']
                    st.rerun()
    
    # 3. Личные сообщения
    users = get_direct_chat_users(user_id)
    if users:
        st.markdown("#### 💌 Private Chats")
        
        search = st.text_input("🔍 Search", placeholder="Find user...", key="search_users")
        
        for user in users:
            if search and search.lower() not in user['username'].lower():
                continue
            
            unread = get_unread_count(user_id, 'direct', user['id'])
            unread_badge = f" ({unread})" if unread > 0 else ""
            
            icon = "👑" if user['role'] == 'admin' else "👤" if user['role'] == 'user' else "👁️"
            
            if st.button(f"{icon} {user['username']}{unread_badge}", 
                       use_container_width=True, 
                       key=f"direct_{user['id']}"):
                st.session_state['active_chat'] = {
                    'type': 'direct',
                    'id': user['id'],
                    'name': user['username']
                }
                mark_messages_as_read(user_id, 'direct', user['id'])
                st.rerun()

def create_group_dialog():
    """Диалог создания новой группы"""
    with st.popover("➕ Create Group", use_container_width=True):
        group_name = st.text_input("Group name", placeholder="Example: Football Team")
        
        all_users = get_all_users()
        current_user_id = st.session_state['user_id']
        
        potential_members = [u for u in all_users if u['id'] != current_user_id]
        
        if potential_members:
            members = st.multiselect(
                "Add participants",
                options=[(u['id'], u['username']) for u in potential_members],
                format_func=lambda x: x[1]
            )
        else:
            members = []
            st.info("No other users to add")
        
        if st.button("✅ Create", use_container_width=True):
            if group_name:
                group_id = create_group(group_name, current_user_id)
                
                for member_id, _ in members:
                    add_user_to_group(group_id, member_id)
                
                st.success(f"Group '{group_name}' created!")
                st.rerun()
            else:
                st.warning("Enter group name!")

def render_active_chat():
    """Отображает активный чат с сообщениями"""
    chat = st.session_state['active_chat']
    user_id = st.session_state['user_id']
    
    st.markdown(f"## {get_chat_icon(chat['type'])} {chat['name']}")
    
    if chat['type'] == 'group':
        if st.button("⚙️ Manage Group", key="manage_group_btn"):
            st.session_state['manage_group'] = chat['id']
            st.rerun()
    
    st.divider()
    
    messages_container = st.container()
    
    with messages_container:
        show_messages(chat['type'], chat['id'] if chat['id'] else None, user_id)
    
    st.divider()
    send_message_form(chat['type'], chat['id'] if chat['id'] else None)

def show_messages(chat_type, chat_id, user_id):
    """Показывает историю сообщений"""
    messages = get_messages(chat_type, chat_id, user_id, limit=100)
    
    if not messages:
        st.info("💬 No messages yet. Write something, bro!")
        return
    
    for msg in messages:
        is_my_message = msg['from_user_id'] == user_id
        render_message(msg, is_my_message)

def render_message(msg, is_my_message):
    """Рендерит одно сообщение"""
    timestamp = msg['timestamp'][:16] if msg['timestamp'] else "just now"
    
    if is_my_message:
        bg_color = "#dcf8c6"
        margin_style = "margin-left: auto;"
        sender_name = "You"
    else:
        bg_color = "#f1f1f1"
        margin_style = "margin-right: auto;"
        sender_name = msg.get('users', {}).get('username', msg.get('username', 'Unknown'))
    
    msg_html = f"""
    <div style="
        max-width: 85%;
        margin: 10px 0;
        padding: 10px;
        border-radius: 12px;
        background-color: {bg_color};
        {margin_style}
        word-wrap: break-word;
    ">
        <div style="font-weight: bold; margin-bottom: 5px;">
            {sender_name}
            <span style="font-size: 11px; color: #666; margin-left: 8px;">{timestamp}</span>
        </div>
        <div style="margin-bottom: 8px;">{msg['content'] if msg['content'] else ''}</div>
    """
    
    st.markdown(msg_html, unsafe_allow_html=True)
    
    if msg.get('file_path') and msg['file_path'] and os.path.exists(msg['file_path']):
        if msg['file_path'].lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
            st.image(msg['file_path'], width=200)
        else:
            with open(msg['file_path'], "rb") as f:
                st.download_button(
                    label=f"📎 Download {os.path.basename(msg['file_path'])}",
                    data=f,
                    file_name=os.path.basename(msg['file_path']),
                    key=f"download_{msg['id']}"
                )

def send_message_form(chat_type, chat_id):
    """Форма для отправки сообщений"""
    user_id = st.session_state['user_id']
    
    if st.session_state['role'] == 'guest' and chat_type != 'general':
        st.warning("👁️ Guests can only write in general chat!")
        return
    
    to_group_id = None
    to_user_id = None
    
    if chat_type == 'group':
        to_group_id = chat_id
    elif chat_type == 'direct':
        to_user_id = chat_id
    
    with st.form(key="send_message_form", clear_on_submit=True):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            message = st.text_area(
                "Message",
                placeholder="Write something, bro... 📝",
                label_visibility="collapsed",
                height=68,
                key="message_input"
            )
        
        with col2:
            uploaded_file = st.file_uploader(
                "📎 File",
                type=None,
                label_visibility="collapsed",
                key="file_uploader"
            )
        
        submitted = st.form_submit_button("📤 Send", use_container_width=True)
        
        if submitted:
            if not message.strip() and not uploaded_file:
                st.warning("Write a message or attach a file, bro!")
                return
            
            file_path = None
            if uploaded_file:
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_filename = f"{timestamp}_{uploaded_file.name}"
                file_path = os.path.join(UPLOAD_DIR, safe_filename)
                
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                st.success(f"✅ File {uploaded_file.name} uploaded!")
            
            save_message(
                from_user_id=user_id,
                to_group_id=to_group_id,
                to_user_id=to_user_id,
                content=message.strip(),
                file_path=file_path
            )
            
            st.rerun()

def get_chat_icon(chat_type):
    icons = {
        'general': '🌍',
        'group': '👥',
        'direct': '💌'
    }
    return icons.get(chat_type, '💬')

def show_welcome_screen():
    st.markdown("""
    <div style="
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 70vh;
        text-align: center;
    ">
        <h1 style="font-size: 48px;">💬</h1>
        <h2>Welcome to BroChat!</h2>
        <p style="color: #666;">Select a chat from the list on the left to start messaging</p>
        <br>
        <p style="font-size: 14px; color: #999;">
            🌍 General Chat - for everyone<br>
            👥 Groups - chat with team<br>
            💌 Private - personal conversations
        </p>
    </div>
    """, unsafe_allow_html=True)

def show_group_management():
    """Управление группой"""
    if 'manage_group' not in st.session_state:
        return
    
    group_id = st.session_state['manage_group']
    group = get_group_by_id(group_id)
    
    if not group:
        del st.session_state['manage_group']
        return
    
    group_name = group['name']
    created_by = group['created_by']
    current_user_id = st.session_state['user_id']
    is_creator = current_user_id == created_by
    is_admin_user = st.session_state['role'] == 'admin'
    can_manage = is_creator or is_admin_user
    
    with st.sidebar:
        st.markdown(f"### Group Management: {group_name}")
        
        creator_info = get_user_by_id(created_by)
        creator_name = creator_info['username'] if creator_info else 'Unknown'
        st.caption(f"Created by: {creator_name}")
        
        st.divider()
        
        st.markdown("#### Participants")
        members = get_group_members(group_id)
        
        if not members:
            st.info("No members in this group")
        else:
            for member in members:
                col1, col2, col3 = st.columns([2, 1.5, 0.8])
                
                with col1:
                    if member['id'] == created_by:
                        icon = "👑"
                    elif member.get('role') == 'admin':
                        icon = "👑"
                    else:
                        icon = "👤"
                    st.write(f"{icon} {member['username']}")
                
                with col2:
                    if member['id'] == created_by:
                        st.caption("(creator)")
                    elif member['id'] == current_user_id:
                        st.caption("(you)")
                    else:
                        st.caption(f"({member.get('role', 'user')})")
                
                with col3:
                    can_remove = False
                    
                    if is_admin_user:
                        can_remove = True
                    elif is_creator and member['id'] != created_by:
                        can_remove = True
                    elif member['id'] == current_user_id:
                        can_remove = True
                    
                    if can_remove:
                        button_text = "❌" if member['id'] != current_user_id else "🚪"
                        button_help = "Remove from group" if member['id'] != current_user_id else "Leave group"
                        
                        if st.button(button_text, key=f"remove_{member['id']}", help=button_help):
                            if member['id'] == created_by and not is_admin_user:
                                st.warning("Cannot remove group creator!")
                            else:
                                remove_user_from_group(group_id, member['id'])
                                if member['id'] == current_user_id:
                                    del st.session_state['manage_group']
                                    if 'active_chat' in st.session_state:
                                        del st.session_state['active_chat']
                                    st.success(f"You left group '{group_name}'")
                                else:
                                    st.success(f"{member['username']} removed from group")
                                st.rerun()
        
        if can_manage:
            st.divider()
            st.markdown("#### Add Participants")
            all_users = get_all_users()
            current_member_ids = [m['id'] for m in members]
            
            available_users = [u for u in all_users if u['id'] not in current_member_ids and u['id'] != current_user_id]
            
            if available_users:
                user_to_add = st.selectbox(
                    "Select user",
                    options=[(u['id'], u['username']) for u in available_users],
                    format_func=lambda x: x[1]
                )
                
                if st.button("Add to Group", use_container_width=True):
                    add_user_to_group(group_id, user_to_add[0])
                    st.success("User added to group!")
                    st.rerun()
            else:
                st.info("All users are already in the group")
        
        st.divider()
        if st.button("Close", use_container_width=True):
            del st.session_state['manage_group']
            st.rerun()
