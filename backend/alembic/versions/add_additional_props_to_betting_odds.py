"""Add additional_props column to betting_odds

Revision ID: add_additional_props_betting_odds
Revises: add_turnovers_three_pointers
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'add_additional_props_betting_odds'
down_revision = 'add_turnovers_three_pointers'
branch_labels = None
depends_on = None


def upgrade():
    # Add additional_props column to betting_odds as JSONB for PostgreSQL
    op.add_column('betting_odds', 
                  sa.Column('additional_props', 
                           postgresql.JSONB(), 
                           nullable=True))


def downgrade():
    op.drop_column('betting_odds', 'additional_props')