import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "exchange_rates",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("currency_code", sa.String(3), nullable=False),
        sa.Column("scale", sa.Integer(), nullable=False),
        sa.Column("rate", sa.Numeric(12, 6), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("currency_code", "rate_date", name="uq_currency_rate_date"),
    )
    op.create_index(
        "ix_exchange_rates_currency_code", "exchange_rates", ["currency_code"]
    )
    op.create_index("ix_exchange_rates_rate_date", "exchange_rates", ["rate_date"])
    op.create_table(
        "exchange_transactions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("source_currency", sa.String(3), nullable=False),
        sa.Column("target_currency", sa.String(3), nullable=False),
        sa.Column("source_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("target_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("exchange_rate", sa.Numeric(24, 12), nullable=False),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "REJECTED", name="transaction_status"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    for name in ("source_currency", "target_currency", "status", "created_at"):
        op.create_index(
            f"ix_exchange_transactions_{name}", "exchange_transactions", [name]
        )


def downgrade() -> None:
    op.drop_table("exchange_transactions")
    op.drop_table("exchange_rates")
    sa.Enum(name="transaction_status").drop(op.get_bind())
