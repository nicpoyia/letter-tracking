"""Initial migration

Revision ID: 6297642bcbc4
Revises: 
Create Date: 2022-05-01 23:41:27.119735

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6297642bcbc4'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('letter',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('tracking_number', sa.String(length=256), nullable=True),
    sa.Column('status', sa.String(length=191), nullable=True),
    sa.Column('final', sa.Boolean(), nullable=True),
    sa.Column('updated', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_letter_final'), 'letter', ['final'], unique=False)
    op.create_index(op.f('ix_letter_tracking_number'), 'letter', ['tracking_number'], unique=True)
    op.create_index(op.f('ix_letter_updated'), 'letter', ['updated'], unique=False)
    op.create_table('status_history',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('letter_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=191), nullable=True),
    sa.Column('timestamp_tracked', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
    sa.ForeignKeyConstraint(['letter_id'], ['letter.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_status_history_letter_id'), 'status_history', ['letter_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    op.drop_index(op.f('ix_status_history_letter_id'), table_name='status_history')
    op.drop_table('status_history')
    op.drop_index(op.f('ix_letter_updated'), table_name='letter')
    op.drop_index(op.f('ix_letter_tracking_number'), table_name='letter')
    op.drop_index(op.f('ix_letter_final'), table_name='letter')
    op.drop_table('letter')
    # ### end Alembic commands ###
