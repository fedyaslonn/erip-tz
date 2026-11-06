import os

os.environ.setdefault(
    "DB_URL", "postgresql+asyncpg://exchange:exchange@localhost/exchange"
)
