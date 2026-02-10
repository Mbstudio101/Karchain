"""Add turnovers and three_pointers to player_stats

Revision ID: add_turnovers_three_pointers
Revises: 
Create Date: 2026-02-10

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_turnovers_three_pointers'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add turnovers column to player_stats
    op.add_column('player_stats', sa.Column('turnovers', sa.Float(), nullable=True, server_default='0'))
    # Add three_pointers column to player_stats  
    op.add_column('player_stats', sa.Column('three_pointers', sa.Float(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('player_stats', 'turnovers')
    op.drop_column('player_stats', 'three_pointers')