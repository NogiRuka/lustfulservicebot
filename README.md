# Jessy

A template repository for creating a Telegram bot using [Aiogram](https://docs.aiogram.dev/). This template includes essential setup for Docker, PostgreSQL, and Alembic for database migrations, making it easy to bootstrap your next project.

---

## Features
- **Aiogram Framework:** A modern and efficient framework for Telegram bots.
- **Database Integration:** Pre-configured with PostgreSQL.
- **Database Migrations:** Integrated with Alembic for schema migrations.
- **Dockerized Setup:** Docker Compose configuration for easy deployment.
- **Environment Variables:** Centralized configuration using a `.env` file.

---

## Project Structure

```
├── app/                  # Main application folder
│   ├── runme.py          # Entry point to start the bot
│   ├── bot.py            # Core bot logic
├── migrations/           # Alembic migrations folder
├── .env                  # Environment configuration file
├── alembic.ini           # Alembic configuration file
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration for the bot
├── docker-compose.yml    # Docker Compose setup
└── README.md             # Project documentation
```

---

## Getting Started

### Prerequisites
- Python 3.10+
- Docker & Docker Compose
- PostgreSQL (if running locally without Docker)

### Setup

#### 1. Clone the Repository
```bash
git clone https://github.com/iismoilov7/jessy.git
cd jessy
```

#### 2. Create a `.env` File
Create a `.env` file in the project root, you can use `.env-example` for instacne

#### 3. Build and Start the Project
Using Docker Compose:
```bash
docker-compose up --build
```
This will:
- Build the `bot` service.
- Spin up a PostgreSQL database.
- Run the Telegram bot.

---

## Usage
- **Starting the Bot:**
  The bot starts automatically when the `bot` container is running.

- **Accessing Logs:**
  To view logs:
  ```bash
  docker-compose logs -f bot
  ```

- **Stopping the Services:**
  ```bash
  docker-compose down
  ```

---

## Development

### Install Dependencies
If you prefer running the bot locally:
1. Set up postgresql database and set .env files
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   or
   ```bash
   uv sync
   ```
   or
   ```bash
   uv add -r requirements.txt
   ```
3. Apply migrations:
   ```bash
   alembic upgrade head
   ```
4. Start the bot:
   ```bash
   bash run.sh
   ```

---

## Deployment
This template is designed for easy deployment via Docker. You can use platforms like [Heroku](https://www.heroku.com/), [AWS](https://aws.amazon.com/), or [DigitalOcean](https://www.digitalocean.com/) to host your bot.

---

## Contributing
1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add your commit message"
   ```
4. Push to the branch:
   ```bash
   git push origin feature/your-feature-name
   ```
5. Create a Pull Request.

---

## License
This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgments
- [Aiogram Documentation](https://docs.aiogram.dev/)
- [Docker Documentation](https://docs.docker.com/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)

---

## Support
For issues or questions, please open an [issue](https://github.com/iismoilov7/jessy/issues).


![Stars](https://img.shields.io/github/stars/iismoilov7/jessy?style=social) 
