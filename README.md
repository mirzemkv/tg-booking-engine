# Commercial Booking Engine

[![CI](https://github.com/mirzemkv/tg-booking-engine/actions/workflows/ci.yml/badge.svg)](https://github.com/mirzemkv/tg-booking-engine/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Aiogram](https://img.shields.io/badge/Aiogram-3.x-green.svg)](https://docs.aiogram.dev/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue.svg)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Compose-orange.svg)](https://www.docker.com/)

A production-oriented, asynchronous Telegram bot for client booking and lead management. It uses a layered architecture, transactional row locking to prevent double-booking, Redis-backed FSM state, Alembic migrations, and containerized deployment.

---

## Features

- **Layered architecture:** handlers, keyboards, FSM states, repositories, and database models are separated.
- **Race-condition safe booking:** PostgreSQL `SELECT ... FOR UPDATE` inside a transaction prevents two clients from booking the same slot.
- **Persistent FSM:** conversation state is stored in Redis and survives bot restarts.
- **Async database stack:** SQLAlchemy 2.0 + asyncpg with a connection pool.
- **Schema migrations:** Alembic is wired into the container entrypoint. Existing databases are detected and stamped automatically.
- **Seed data:** one command creates demo services and bookable slots for a fresh database.
- **Tests and CI:** repository and concurrency tests run against PostgreSQL in GitHub Actions.
- **Container hardening:** the bot runs as a non-root user, and secrets are excluded from the Docker build context.

---

## Tech stack

| Component | Technology |
| --- | --- |
| Language | Python 3.12 |
| Telegram framework | aiogram 3.x |
| Database | PostgreSQL 16 |
| ORM / driver | SQLAlchemy 2.0 / asyncpg |
| FSM storage | Redis 7 |
| Migrations | Alembic |
| Tests | pytest, pytest-asyncio |
| Deployment | Docker, Docker Compose |

---

## Booking flow

1. A client sends `/start`. The bot creates or loads the user and shows available services.
2. The client chooses a service. The bot stores the service ID in FSM data and shows free slots.
3. The client chooses a slot. The bot locks the slot row with `SELECT ... FOR UPDATE`, verifies it is still free, and books it.
4. If another client booked the same slot first, the second request receives an "already booked" message and the user can start again.

The row lock is released on commit or rollback, so concurrent requests are serialized by PostgreSQL rather than by the Python process.

---

## Project structure

```text
tg-booking-engine/
├── .env.example
├── .dockerignore
├── .gitattributes
├── .gitignore
├── .github/
│   └── workflows/
│       └── ci.yml
├── Dockerfile
├── LICENSE
├── README.md
├── alembic.ini
├── docker-compose.yml
├── docker-entrypoint.sh
├── requirements.txt
├── requirements-dev.txt
├── pyproject.toml
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_initial.py
├── tests/
│   ├── conftest.py
│   └── test_repository.py
└── src/
    ├── __init__.py
    ├── main.py
    ├── bot/
    │   ├── errors.py
    │   ├── handlers/
    │   │   ├── __init__.py
    │   │   └── booking.py
    │   ├── keyboards/
    │   │   ├── __init__.py
    │   │   └── inline.py
    │   └── states/
    │       ├── __init__.py
    │       └── booking.py
    ├── core/
    │   ├── __init__.py
    │   └── config.py
    ├── database/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── models.py
    │   └── session.py
    ├── repositories/
    │   ├── __init__.py
    │   └── booking.py
    └── scripts/
        ├── __init__.py
        ├── migration_mode.py
        └── seed.py
```

---

## Quick start

### Prerequisites

- Docker Desktop with Docker Compose
- A Telegram bot token from [@BotFather](https://t.me/BotFather)

### 1. Clone the repository

```bash
git clone https://github.com/mirzemkv/tg-booking-engine.git
cd tg-booking-engine
```

### 2. Create the environment file

Linux/macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Open `.env` and set your real token:

```dotenv
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
```

All other defaults work with Docker Compose.

### 3. Start the stack

```bash
docker compose up -d --build
```

This builds the bot image, starts PostgreSQL and Redis, waits for both health checks, applies database migrations, and starts long polling.

### 4. Create demo data

A fresh database contains no services or slots. Run the idempotent seeder once:

```bash
docker compose exec bot python -m src.scripts.seed
```

The seeder adds three demo services and 35 slots (seven days, five time slots per day) only when the corresponding tables are empty.

### 5. Open the bot

Open your bot in Telegram and send `/start`. If you used the demo data, you can immediately select a service and a time.

### Useful commands

```bash
# Follow bot logs
docker compose logs -f bot

# Check container status
docker compose ps

# Run the seeder again (safe, it will not duplicate data)
docker compose exec bot python -m src.scripts.seed

# Stop containers (data is preserved)
docker compose down

# Stop and delete the PostgreSQL volume (destructive)
docker compose down -v
```

---

## Configuration

Settings are loaded from `.env` or from process environment variables. The bot container receives variables through `env_file` in `docker-compose.yml`.

| Variable | Default | Description |
| --- | --- | --- |
| `BOT_TOKEN` | none (required) | Telegram bot token from BotFather |
| `DB_HOST` | `postgres` | PostgreSQL host |
| `DB_PORT` | `5432` | PostgreSQL port inside the Docker network |
| `DB_USER` | `postgres` | PostgreSQL user |
| `DB_PASS` | `postgres` | PostgreSQL password |
| `DB_NAME` | `booking_db` | PostgreSQL database |
| `REDIS_HOST` | `redis` | Redis host |
| `REDIS_PORT` | `6379` | Redis port inside the Docker network |

`.env` is ignored by Git and excluded from the Docker build context. Never commit real secrets.

For host access, Docker publishes PostgreSQL on `127.0.0.1:5433` and Redis on `127.0.0.1:6380` to avoid collisions with local installations. The values above are the container-internal ports used by the bot.

---

## Database and migrations

The container entrypoint detects the database state before starting the bot:

- **Fresh database:** runs `alembic upgrade head`.
- **Existing database created before Alembic was added:** stamps the current schema as the initial revision.
- **Existing Alembic database:** applies pending revisions.

Manual commands:

```bash
# Apply all migrations
docker compose exec bot alembic upgrade head

# Show the current revision
docker compose exec bot alembic current

# Compare models with the migrated schema
docker compose exec bot alembic check

# Create a new migration after changing models
docker compose exec bot alembic revision --autogenerate -m "describe change"
```

Migration files are stored in `migrations/versions/`.

### Local development without Docker

1. Start PostgreSQL and Redis, or use `docker compose up -d postgres redis`.
2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows PowerShell
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

3. Create `.env` with `DB_HOST=localhost`, `DB_PORT=5433`, `REDIS_HOST=localhost`, and `REDIS_PORT=6380`.
   Use these host values only when the bot runs on the host. Inside Docker, keep
   `DB_HOST=postgres`, `DB_PORT=5432`, `REDIS_HOST=redis`, and `REDIS_PORT=6379`.
4. Apply migrations:

   ```bash
   alembic upgrade head
   ```

5. Run the bot:

   ```bash
   python -m src.main
   ```

---

## Tests

The test suite uses a dedicated PostgreSQL database named `booking_test` and is also run in GitHub Actions.

### GitHub Actions

`.github/workflows/ci.yml` runs:

- `ruff check .`
- `alembic upgrade head`
- `alembic check`
- `alembic downgrade base`
- `pytest -q`
- a Docker image build

### Local tests

Create the test database once:

```bash
docker compose exec postgres psql -U postgres -c "CREATE DATABASE booking_test;"
```

Create a virtual environment, install development dependencies, and run pytest:

```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements-dev.txt

$env:TEST_DATABASE_URL="postgresql+asyncpg://postgres:postgres_password@localhost:5433/booking_test"
pytest -q
```

The tests cover:

- user creation and persistence;
- successful booking;
- rejection of a second booking for the same slot;
- concurrent booking attempts where exactly one wins;
- filtering of unavailable slots.

---

## Deployment notes

- Change the default PostgreSQL password in `.env` before exposing the service anywhere.
- `docker-compose.yml` binds PostgreSQL and Redis to `127.0.0.1` only. Do not expose them publicly.
- Keep `.env` on the server and out of version control.
- Use a process supervisor or the provided `restart: unless-stopped` policy for the bot container.
- Back up the `pgdata` volume regularly.
- If a bot token is ever exposed, revoke it in BotFather and issue a new one.
- Timestamps are stored as timezone-naive values. Keep the database and bot server timezone consistent; UTC is recommended.

---

## Roadmap ideas

- Admin commands for creating services and slots from Telegram.
- Timezone-aware slot storage and localized display.
- Notification job for upcoming bookings.
- Payment and lead-management integrations.

---

## License

Distributed under the MIT License. See [LICENSE](LICENSE) for details.
