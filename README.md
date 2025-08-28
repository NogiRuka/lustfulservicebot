# 🤖 Jessy

> A modern, production-ready template for creating Telegram bots using [Aiogram](https://docs.aiogram.dev/) 🚀

This template includes essential setup for SQLite 💾 (default), Alembic for database migrations, and a clean Aiogram v3 architecture to help you learn and iterate quickly without extra infrastructure.

---

## ✨ Features

- 🤖 **Aiogram Framework:** A modern and efficient async framework for Telegram bots
- 🗄️ **Database Integration:** Pre-configured with SQLite (default) via SQLAlchemy ORM
- 🔄 **Database Migrations:** Integrated with Alembic for schema migrations
- 🔧 **Environment Variables:** Centralized configuration using a `.env` file
- 📊 **Structured Logging:** Loguru-based logging with file rotation
- 🛡️ **Anti-Flood Protection:** Built-in middleware to prevent spam
- 👥 **User Management:** Automatic user tracking and activity monitoring
- 🔐 **Admin Panel:** Built-in admin commands and user management
- 🎯 **Clean Architecture:** Modular design with separation of concerns

---

## 📁 Project Structure

```
jessy/
├── 📂 app/                  # Main application code
│   ├── 🤖 bot.py            # Bot entry point and dispatcher setup
│   ├── 🔘 buttons/          # Telegram keyboard/button definitions
│   ├── ⚙️ config/           # Configuration and environment loading
│   ├── 🗄️ database/         # Database models, access, and admin/user logic
│   ├── 📝 handlers/         # Message handlers for users and admins
│   ├── 🔗 middlewares/      # Custom aiogram middlewares
│   └── 🛠️ utils/            # Filters, states, and utility code
├── (removed) migrations/
├── 📂 logs/                 # Log files (created at runtime)
├── 📂 docs/                 # Documentation
│   └── 📄 CODE.md           # Code principles and project structure
├── 🚀 main.py               # Simple hello-world entry (for testing)
├── 🐚 run.sh                # Shell script to run the bot
├── 📋 requirements.txt      # Python dependencies
├── ⚙️ pyproject.toml        # Project metadata and dependencies
├── (removed) Dockerfile
├── (removed) docker-compose.yml
├── 🔄 alembic.ini           # Alembic configuration
├── 📖 README.md             # Main project documentation
└── 📄 LICENSE               # License file
```

> 📚 **Want to learn more about the code structure?** Check out our [📄 CODE.md](docs/CODE.md) for detailed code principles and architecture guidelines!

---

## 🚀 Getting Started (SQLite, no Docker)

### 📋 Prerequisites
- 🐍 Python 3.10+

### ⚙️ Setup

#### 1️⃣ Clone the Repository
```bash
git clone https://github.com/right-git/jessy.git
cd jessy
```

#### 2️⃣ Create a `.env` File (optional)
Create a `.env` file in the project root to set your bot token and admins:
```bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMINS_ID=123456789,987654321

# Database (optional). Defaults to local SQLite file `./jessy.db`
# DATABASE_URL_ASYNC=sqlite+aiosqlite:///./jessy.db
```

#### 3️⃣ Install dependencies and run
```bash
pip install -r requirements.txt
python app/bot.py
```

---

## 🎯 Usage

### 🤖 Starting the Bot
The bot starts automatically when the `bot` container is running.

### 📊 Accessing Logs
To view logs:
```bash
docker-compose logs -f bot
```

### 🛑 Stopping the Services
```bash
docker-compose down
```

---

## 💻 Development Tips
 - Database defaults to `sqlite+aiosqlite:///jessy.db` in project root. Override via `DATABASE_URL_ASYNC`.
 - Tables are created automatically on startup for learning.
 - Use `run.sh` on Unix-like systems or run `python app/bot.py` directly.

---

## 🌐 Deployment
For learning, run locally. When ready for production, switch `DATABASE_URL_ASYNC` to a server DB (e.g., Postgres) and deploy to your preferred platform.

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

1. 🍴 Fork the repository
2. 🌿 Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. 💾 Commit your changes:
   ```bash
   git commit -m "✨ Add your commit message"
   ```
4. 📤 Push to the branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. 🔄 Create a Pull Request

### 📋 Contribution Guidelines
- 📖 Read our [CODE.md](docs/CODE.md) for coding standards
- 🧪 Write tests for new features
- 📝 Update documentation when needed
- 🎨 Follow the existing code style

---

## 📄 License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for details.

---

## 🙏 Acknowledgments

- 📚 [Aiogram Documentation](https://docs.aiogram.dev/)
- 🐳 [Docker Documentation](https://docs.docker.com/)
- 🔄 [Alembic Documentation](https://alembic.sqlalchemy.org/)
- 🐍 [Python Documentation](https://docs.python.org/)

---

## 🆘 Support

Need help? Here's how to get support:

- 🐛 **Bug Reports:** Open an [issue](https://github.com/right-git/jessy/issues)
- 💡 **Feature Requests:** Create a feature request issue
- 📖 **Documentation:** Check our [CODE.md](docs/CODE.md) for detailed guides
- 💬 **Discussions:** Use GitHub Discussions for questions

---

## ⭐ Show Your Support

If this project helped you, please give it a star! ⭐

[![Stars](https://img.shields.io/github/stars/right-git/jessy?style=social)](https://github.com/right-git/jessy)

---

<div align="center">

**Made with ❤️ for the Telegram Bot Community**

</div> 
