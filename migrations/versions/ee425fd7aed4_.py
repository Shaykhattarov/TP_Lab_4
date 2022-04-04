"""empty message

Revision ID: ee425fd7aed4
Revises: 
Create Date: 2022-03-15 22:29:21.798586

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'ee425fd7aed4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('news',
    sa.Column('news_id', sa.Integer(), nullable=False),
    sa.Column('news_title', sa.String(length=144), nullable=True),
    sa.Column('news_intro', sa.String(length=300), nullable=True),
    sa.Column('news_text', sa.Text(), nullable=True),
    sa.Column('news_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('news_id')
    )
    op.create_table('user',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('user_name', sa.String(length=300), nullable=False),
    sa.Column('user_surname', sa.String(length=300), nullable=False),
    sa.Column('user_email', sa.String(length=2025), nullable=False),
    sa.Column('user_password', sa.String(), nullable=False),
    sa.Column('user_old', sa.Integer(), nullable=False),
    sa.Column('user_work', sa.String(length=300), nullable=True),
    sa.Column('user_img', sa.String(length=2025), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user')
    op.drop_table('news')
    # ### end Alembic commands ###