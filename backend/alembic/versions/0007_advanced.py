"""advanced features - poster + tasks

Revision ID: 0007
Create Date: 2026-03-22
"""
from alembic import op
import sqlalchemy as sa

revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'poster_templates',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('layout', sa.String(32), server_default='vertical'),
        sa.Column('background_color', sa.String(16), server_default='#1a1a2e'),
        sa.Column('text_color', sa.String(16), server_default='#ffffff'),
        sa.Column('accent_color', sa.String(16), server_default='#e94560'),
        sa.Column('columns', sa.Integer(), server_default='3'),
        sa.Column('show_rating', sa.Boolean(), server_default='true'),
        sa.Column('show_year', sa.Boolean(), server_default='true'),
        sa.Column('show_genres', sa.Boolean(), server_default='false'),
        sa.Column('cover_text', sa.String(256), nullable=True),
    )

    op.create_table(
        'generated_posters',
        sa.Column('id', sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column('template_id', sa.BigInteger(), nullable=True),
        sa.Column('title', sa.String(256), nullable=False),
        sa.Column('item_ids', sa.JSON(), nullable=True),
        sa.Column('image_path', sa.String(512), nullable=True),
        sa.Column('html_content', sa.Text(), nullable=True),
        sa.Column('status', sa.String(16), server_default='generated'),
    )


def downgrade():
    op.drop_table('generated_posters')
    op.drop_table('poster_templates')
