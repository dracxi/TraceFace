"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create missing_persons table
    op.create_table(
        'missing_persons',
        sa.Column('person_id', sa.String(36), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('last_seen_location', sa.String(500)),
        sa.Column('date_reported', sa.DateTime(), nullable=False),
        sa.Column('contact_info', sa.String(500)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('idx_missing_persons_date', 'missing_persons', ['date_reported'])
    
    # Create admin_users table
    op.create_table(
        'admin_users',
        sa.Column('user_id', sa.String(36), primary_key=True),
        sa.Column('username', sa.String(100), unique=True, nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255)),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    
    # Create person_photos table
    op.create_table(
        'person_photos',
        sa.Column('photo_id', sa.String(36), primary_key=True),
        sa.Column('person_id', sa.String(36), nullable=False),
        sa.Column('photo_url', sa.String(1000), nullable=False),
        sa.Column('embedding_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['person_id'], ['missing_persons.person_id'], ondelete='CASCADE')
    )
    
    # Create audit_logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', sa.String(36), primary_key=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('user_id', sa.String(36)),
        sa.Column('person_id', sa.String(36)),
        sa.Column('result_count', sa.Integer()),
        sa.Column('timestamp', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(45)),
        sa.ForeignKeyConstraint(['user_id'], ['admin_users.user_id']),
        sa.ForeignKeyConstraint(['person_id'], ['missing_persons.person_id'])
    )
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_audit_logs_event_type', 'audit_logs', ['event_type'])


def downgrade() -> None:
    op.drop_table('audit_logs')
    op.drop_table('person_photos')
    op.drop_table('admin_users')
    op.drop_table('missing_persons')
