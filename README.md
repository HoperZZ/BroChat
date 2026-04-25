# 💬 BroChat - Modern Messenger on Streamlit

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![SQLite](https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://sqlite.org)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**Full-featured messenger with admin panel, groups, private chats, file sharing and mobile support**

![BroChat Demo](https://via.placeholder.com/800x400?text=BroChat+Demo)

## ✨ Features

### 🔐 Authentication & Roles
- **3 Role System**: Admin, User, Guest
- **Login protection**: 3 attempts then 15 min block
- **Session management** via Streamlit session_state
- **First user** automatically becomes admin

### 👑 Admin Panel
- View all users with their roles
- Add/delete users on the fly
- Change user roles (guest/user/admin)
- **Database backup & restore** (.db and JSON formats)
- Quick add test users for development
- User statistics dashboard

### 💬 Chat System
- **General chat** - public channel for everyone
- **Private messages** - direct conversations between users
- **Group chats** - create and manage group conversations
- Real-time message updates
- Unread messages counter with badges
- Message history (last 100 messages)

### 👥 Group Management
- Create groups with custom names
- Add/remove participants
- Group creator has special privileges
- Admins can manage any group
- Leave group option for regular users

### 📎 File Sharing
- Upload any file type (images, documents, etc.)
- Image preview in chat
- Download files from messages
- 200MB max file size
- Files stored in `uploads/` folder

### 📱 Mobile Friendly
- Responsive design for all screen sizes
- Hamburger menu for mobile devices
- Touch-friendly buttons and inputs
- Auto-scaling chat bubbles
- Optimized for both portrait and landscape

### 💾 Backup System
- One-click database backup
- JSON export for human-readable data
- Restore from .db or JSON files
- Automatic backup before restore
- Backup history with timestamps
- Download/delete old backups

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/brochat.git
cd brochat
Install dependencies

bash
pip install -r requirements.txt
Run the application

bash
streamlit run main.py
Open in browser

Local: http://localhost:8501

Network: http://your-ip:8501

Default Admin Account
text
Username: admin
Password: admin123
⚠️ Change password after first login!

📁 Project Structure
text
brochat/
├── main.py              # Application entry point
├── database.py          # SQLite database operations
├── auth.py              # Authentication & session management
├── admin.py             # Admin panel & backup system
├── chat.py              # Chat interface & messaging
├── requirements.txt     # Python dependencies
├── uploads/             # User uploaded files (auto-created)
├── backups/             # Database backups (auto-created)
└── chat.db              # SQLite database (auto-created)
🎮 Usage Guide
First Launch
Run streamlit run main.py

Admin account is created automatically

Login with admin/admin123

Start adding users from admin panel

Creating Groups
Click "Create Group" in sidebar

Enter group name

Select participants

Start chatting!

Sending Files
Click "Browse files" in chat input

Select file (image, document, etc.)

Add optional text message

Click "Send"

Managing Users (Admin only)
Open admin panel in sidebar

Use tabs to:

View all users

Add new users

Change roles

Create backups

Database Backup (Admin only)
Go to Admin Panel → Backup tab

Click "Backup Database" to create backup

Or "Export to JSON" for readable format

Restore from previous backups anytime

🛠️ Technology Stack
Technology	Purpose
Streamlit	Web interface framework
SQLite3	Embedded database
bcrypt	Password hashing
Pillow	Image processing
Python	Core logic
📱 Mobile Usage
BroChat is fully responsive and works great on phones:

Open on phone: Use your local IP address (e.g., http://192.168.1.100:8501)

Access menu: Click ☰ icon in top-left corner

Select chat: Choose from general, groups, or private chats

Send messages: Type and send like on desktop

🔒 Security Features
Password hashing with bcrypt (no plain text storage)

Session-based authentication

Role-based access control (RBAC)

Input validation and sanitization

SQL injection protection (parameterized queries)

File type validation

Rate limiting (3 login attempts)

🤝 Contributing
Want to contribute? Great, bro!

Fork the repository

Create feature branch (git checkout -b feature/amazing-feature)

Commit changes (git commit -m 'Add amazing feature')

Push to branch (git push origin feature/amazing-feature)

Open Pull Request

Development Setup
bash
# Install dev dependencies
pip install -r requirements.txt

# Run in development mode
streamlit run main.py --logger.level=debug
🐛 Troubleshooting
Common Issues
"Database locked" error

bash
# Delete lock file
rm chat.db-journal  # Linux/Mac
del chat.db-journal  # Windows
Files not uploading

Check uploads/ folder permissions

Verify disk space

Check file size (max 200MB)

Can't see messages

Refresh page (F5)

Check if you're in correct chat

Verify user role permissions

Port already in use

bash
streamlit run main.py --server.port 8502
📊 Database Schema
sql
users (id, username, password_hash, role, created_at)
groups (id, name, created_by, created_at)
group_members (group_id, user_id, joined_at)
messages (id, from_user_id, to_group_id, to_user_id, 
          content, file_path, is_read, timestamp)
🎯 Roadmap
Message editing and deletion

Typing indicators

Online/offline status

Read receipts

Push notifications

End-to-end encryption

Voice messages

Video calls (WebRTC)

Dark mode

Multiple language support

📄 License
Distributed under MIT License. See LICENSE file for details.

🙏 Acknowledgments
Streamlit team for amazing framework

bcrypt developers for security

All contributors and testers



⭐ Show Your Support
If this project helped you, please give it a star on GitHub!

https://img.shields.io/github/stars/yourusername/brochat?style=social

Made with ❤️ by Bro-Coder Team

"Chat like a bro, code like a pro!" 🚀

text

## А ТАКЖЕ СОЗДАЙ ФАЙЛ `requirements.txt` (если ещё нет):

```txt
streamlit>=1.28.0
bcrypt>=4.0.0
pillow>=10.0.0
И ФАЙЛ .gitignore:
gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual Environment
venv/
env/
ENV/
env.bak/
venv.bak/

# Database
*.db
*.db-journal
*.sqlite
*.sqlite3

# Uploads and Backups
uploads/
backups/
*.bak

# Streamlit
.streamlit/
.secrets/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
desktop.ini

# Logs
*.log
И ФАЙЛ LICENSE (MIT):
text
MIT License

Copyright (c) 2024 BroChat Team

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
