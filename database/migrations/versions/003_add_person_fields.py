"""Add age, gender, status, and audit fields to missing_persons

Revision ID: 003
Revises: 002
Create Date: 2024-02-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to missing_persons table
    op.add_column('missing_persons', sa.Column('age', sa.Integer(), nullable=True))
    op.add_column('missing_persons', sa.Column('gender', sa.String(20), nullable=True))
    op.add_column('missing_persons', sa.Column('status', sa.String(20), nullable=False, server_default='missing'))
    op.add_column('missing_persons', sa.Column('traced_date', sa.TIMESTAMP(), nullable=True))
    op.add_column('missing_persons', sa.Column('traced_notes', sa.Text(), nullable=True))
    op.add_column('missing_persons', sa.Column('created_by', UUID(as_uuid=True), nullable=True))
    op.add_column('missing_persons', sa.Column('updated_by', UUID(as_uuid=True), nullable=True))
    
    # Add check constraint for status
    op.create_check_constraint(
        'missing_persons_status_check',
        'missing_persons',
        "status IN ('missing', 'traced')"
    )
    
    # Add foreign key constraints for created_by and updated_by
    op.create_foreign_key(
        'missing_persons_created_by_fkey',
        'missing_persons',
        'admin_users',
        ['created_by'],
        ['user_id']
    )
    op.create_foreign_key(
        'missing_persons_updated_by_fkey',
        'missing_persons',
        'admin_users',
        ['updated_by'],
        ['user_id']
    )
    
    # Add index on status for faster filtering
    op.create_index('idx_missing_persons_status', 'missing_persons', ['status'])
    
    # Update audit_logs to support more event types and add action details
    op.add_column('audit_logs', sa.Column('action', sa.String(50), nullable=True))
    op.add_column('audit_logs', sa.Column('changes', sa.JSON(), nullable=True))
    op.add_column('audit_logs', sa.Column('admin_name', sa.String(100), nullable=True))
    op.add_column('audit_logs', sa.Column('person_name', sa.String(255), nullable=True))


def downgrade() -> None:
    # Remove audit_logs columns
    op.drop_column('audit_logs', 'person_name')
    op.drop_column('audit_logs', 'admin_name')
    op.drop_column('audit_logs', 'changes')
    op.drop_column('audit_logs', 'action')
    
    # Remove index
    op.drop_index('idx_missing_persons_status', 'missing_persons')
    
    # Remove foreign key constraints
    op.drop_constraint('missing_persons_updated_by_fkey', 'missing_persons', type_='foreignkey')
    op.drop_constraint('missing_persons_created_by_fkey', 'missing_persons', type_='foreignkey')
    
    # Remove check constraint
    op.drop_constraint('missing_persons_status_check', 'missing_persons', type_='check')
    
    # Remove columns from missing_persons
    op.drop_column('missing_persons', 'updated_by')
    op.drop_column('missing_persons', 'created_by')
    op.drop_column('missing_persons', 'traced_notes')
    op.drop_column('missing_persons', 'traced_date')
    op.drop_column('missing_persons', 'status')
    op.drop_column('missing_persons', 'gender')
    op.drop_column('missing_persons', 'age')
