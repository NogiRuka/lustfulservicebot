# 🤖 Jessy

> A modern, production-ready template for creating Telegram bots using [Aiogram](https://docs.aiogram.dev/) 🚀

This template includes essential setup for Docker 🐳, PostgreSQL 🐘, and Alembic for database migrations, making it easy to bootstrap your next Telegram bot project with best practices and clean architecture.

---

## ✨ Features

- 🤖 **Aiogram Framework:** A modern and efficient async framework for Telegram bots
- 🗄️ **Database Integration:** Pre-configured with PostgreSQL and SQLAlchemy ORM
- 🔄 **Database Migrations:** Integrated with Alembic for schema migrations
- 🐳 **Dockerized Setup:** Docker Compose configuration for easy deployment
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
├── 📂 migrations/           # Alembic migration scripts
├── 📂 logs/                 # Log files (created at runtime)
├── 📂 docs/                 # Documentation
│   └── 📄 CODE.md           # Code principles and project structure
├── 🚀 main.py               # Simple hello-world entry (for testing)
├── 🐚 run.sh                # Shell script to run the bot
├── 📋 requirements.txt      # Python dependencies
├── ⚙️ pyproject.toml        # Project metadata and dependencies
├── 🐳 Dockerfile            # Docker build instructions
├── 🐙 docker-compose.yml    # Docker Compose setup for bot and DB
├── 🔄 alembic.ini           # Alembic configuration
├── 📖 README.md             # Main project documentation
└── 📄 LICENSE               # License file
```

> 📚 **Want to learn more about the code structure?** Check out our [📄 CODE.md](docs/CODE.md) for detailed code principles and architecture guidelines!

---

## 🚀 Getting Started

### 📋 Prerequisites
- 🐍 Python 3.10+
- 🐳 Docker & Docker Compose
- 🐘 PostgreSQL (if running locally without Docker)

### ⚙️ Setup

#### 1️⃣ Clone the Repository
```bash
git clone https://github.com/right-git/jessy.git
cd jessy
```

#### 2️⃣ Create a `.env` File
Create a `.env` file in the project root with your configuration:
```bash
# Bot Configuration
BOT_TOKEN=your_bot_token_here
ADMINS_ID=123456789,987654321

# Database Configuration
DATABASE_URL_ASYNC=postgresql+asyncpg://user:password@localhost:5432/dbname
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_db_name
DB_PORT=5432
```

#### 3️⃣ Build and Start the Project
Using Docker Compose (recommended):
```bash
docker-compose up --build
```

This will:
- 🏗️ Build the `bot` service
- 🐘 Spin up a PostgreSQL database
- 🤖 Run the Telegram bot automatically

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

## 💻 Development

### 📦 Install Dependencies
If you prefer running the bot locally:

1. 🐘 Set up PostgreSQL database and configure `.env` file
2. 📦 Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or using `uv` (faster):
   ```bash
   uv sync
   ```
   or
   ```bash
   uv add -r requirements.txt
   ```
3. 🔄 Apply database migrations:
   ```bash
   alembic upgrade head
   ```
4. 🚀 Start the bot:
   ```bash
   bash run.sh
   ```

---

## 🌐 Deployment

This template is designed for easy deployment via Docker. You can use platforms like:

- ☁️ [Heroku](https://www.heroku.com/)
- ☁️ [AWS](https://aws.amazon.com/)
- ☁️ [DigitalOcean](https://www.digitalocean.com/)
- ☁️ [Railway](https://railway.app/)
- ☁️ [Render](https://render.com/)

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
