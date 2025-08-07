# Jessy Project Code Principles & Structure

## Overview
Jessy is a template for building Telegram bots using the Aiogram framework, with a focus on clean architecture, modularity, and maintainability. It leverages async programming, SQLAlchemy ORM, Alembic migrations, and Docker for deployment. The project is structured to separate concerns such as handlers, middlewares, database, and configuration.

---

## Project Structure

```
jessy/
├── app/                  # Main application code
│   ├── bot.py            # Bot entry point and dispatcher setup
│   ├── buttons/          # Telegram keyboard/button definitions
│   ├── config/           # Configuration and environment loading
│   ├── database/         # Database models, access, and admin/user logic
│   ├── handlers/         # Message handlers for users and admins
│   ├── middlewares/      # Custom aiogram middlewares
│   └── utils/            # Filters, states, and utility code
├── migrations/           # Alembic migration scripts
├── logs/                 # Log files (created at runtime)
├── docs/                 # Documentation (this file, etc.)
├── main.py               # Simple hello-world entry (for testing)
├── run.sh                # Shell script to run the bot
├── requirements.txt      # Python dependencies
├── pyproject.toml        # Project metadata and dependencies
├── Dockerfile            # Docker build instructions
├── docker-compose.yml    # Docker Compose setup for bot and DB
├── alembic.ini           # Alembic configuration
├── README.md             # Main project documentation
└── LICENSE               # License file
```

---

## Code Principles

### 1. **Modularity & Separation of Concerns**
- **Handlers** are split into `users` and `admins` for clarity and access control.
- **Middlewares** encapsulate cross-cutting concerns (e.g., anti-flood, user tracking).
- **Database** logic is separated into schema, user, and admin modules.
- **Buttons** and **utils** are isolated for reusability.

### 2. **Async & Modern Python**
- All I/O (DB, bot polling) is async for scalability.
- Type hints are used throughout for clarity and tooling support.

### 3. **Configuration Management**
- All secrets and environment variables are loaded via `.env` and `python-dotenv`.
- No secrets are hardcoded; use `os.getenv` in `config.py`.

### 4. **Database & Migrations**
- SQLAlchemy ORM is used for models and async DB access.
- Alembic is used for migrations, with scripts in `migrations/`.
- All DB access is via async sessions and context managers.

### 5. **Logging & Error Handling**
- Loguru is used for structured logging to files in `logs/`.
- Errors are logged and handled gracefully; the bot exits on fatal errors.

### 6. **Testing & Extensibility**
- Handlers and middlewares are designed to be easily testable and extendable.
- New features should be added as new routers, middlewares, or utility modules.

### 7. **Docker & Deployment**
- Dockerfile and docker-compose.yml provide reproducible environments.
- Alembic migrations are run automatically on container startup.

### 8. **Coding Style**
- Follows PEP8 and modern Python best practices.
- Use of docstrings for all public functions and classes.
- Consistent naming: `snake_case` for functions/variables, `CamelCase` for classes.

---

## Key Directories Explained

- **app/bot.py**: Main entry, sets up dispatcher, routers, middlewares, and starts polling.
- **app/handlers/**: Contains message handlers for users and admins, organized by role.
- **app/middlewares/**: Custom aiogram middlewares (e.g., anti-flood, user tracking).
- **app/database/**: Async DB setup, models, and user/admin logic.
- **app/buttons/**: Keyboard and button definitions for Telegram UI.
- **app/utils/**: Filters, FSM states, and other helpers.
- **app/config/**: Loads environment variables and bot settings.
- **migrations/**: Alembic migration scripts for DB schema changes.
- **logs/**: Log files (created at runtime).
- **docs/**: Project documentation.

---

## Adding New Features
- Add new handlers in `app/handlers/` and register them in `bot.py`.
- Add new middlewares in `app/middlewares/` and include them in the dispatcher.
- For new DB models, update `app/database/schema.py` and create a new Alembic migration.
- Use environment variables for all secrets and configuration.

---

## Example: Adding a New Command
1. Create a new handler in `app/handlers/users/` or `app/handlers/admins/`.
2. Register the handler in the corresponding router list in `__init__.py`.
3. Import and include the router in `bot.py`.

---

## Contribution Guidelines
- Follow the code principles above.
- Write clear, modular, and well-documented code.
- Update documentation and tests when adding features.
