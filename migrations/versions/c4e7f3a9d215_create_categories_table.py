"""create categories table and link products to it

Revision ID: c4e7f3a9d215
Revises: a8c2d91f4b63
Create Date: 2026-10-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e7f3a9d215"
down_revision: Union[str, Sequence[str], None] = "a8c2d91f4b63"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["owner_id"],
            ["users.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_id", "name", name="uq_categories_owner_id_name"),
    )
    op.create_index(op.f("ix_categories_owner_id"), "categories", ["owner_id"])

    op.add_column(
        "products",
        sa.Column("category_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_products_category_id_categories",
        "products",
        "categories",
        ["category_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(op.f("ix_products_category_id"), "products", ["category_id"])

    # Preserve existing free-text categories by turning each distinct
    # (owner, name) pair into a real category row and linking the products.
    op.execute(
        """
        INSERT INTO categories (owner_id, name)
        SELECT DISTINCT owner_id, category
        FROM products
        WHERE category IS NOT NULL AND category <> ''
        """
    )
    op.execute(
        """
        UPDATE products AS p
        SET category_id = c.id
        FROM categories AS c
        WHERE c.owner_id = p.owner_id AND c.name = p.category
        """
    )

    op.drop_column("products", "category")


def downgrade() -> None:
    op.add_column(
        "products",
        sa.Column("category", sa.String(length=100), nullable=True),
    )
    op.execute(
        """
        UPDATE products AS p
        SET category = c.name
        FROM categories AS c
        WHERE c.id = p.category_id
        """
    )

    op.drop_index(op.f("ix_products_category_id"), table_name="products")
    op.drop_constraint(
        "fk_products_category_id_categories",
        "products",
        type_="foreignkey",
    )
    op.drop_column("products", "category_id")

    op.drop_index(op.f("ix_categories_owner_id"), table_name="categories")
    op.drop_table("categories")
