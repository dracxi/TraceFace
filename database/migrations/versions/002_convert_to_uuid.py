"""Convert string IDs to UUID type

Revision ID: 002
Revises: 001
Create Date: 2024-01-15 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, INET

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable UUID extension if not already enabled
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Drop foreign key constraints first
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    op.drop_constraint('audit_logs_person_id_fkey', 'audit_logs', type_='foreignkey')
    op.drop_constraint('person_photos_person_id_fkey', 'person_photos', type_='foreignkey')
    
    # Convert primary key columns first (referenced tables)
    op.alter_column('admin_users', 'user_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='user_id::uuid')
    
    op.alter_column('missing_persons', 'person_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='person_id::uuid')
    
    # Convert foreign key columns (referencing tables)
    op.alter_column('person_photos', 'photo_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='photo_id::uuid')
    op.alter_column('person_photos', 'person_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='person_id::uuid')
    
    op.alter_column('audit_logs', 'log_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='log_id::uuid')
    op.alter_column('audit_logs', 'user_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='user_id::uuid')
    op.alter_column('audit_logs', 'person_id',
                    type_=UUID(as_uuid=True),
                    postgresql_using='person_id::uuid')
    
    # Convert ip_address to INET type
    op.alter_column('audit_logs', 'ip_address',
                    type_=INET,
                    postgresql_using='ip_address::inet')
    
    # Recreate foreign key constraints
    op.create_foreign_key('audit_logs_user_id_fkey', 'audit_logs', 'admin_users', 
                         ['user_id'], ['user_id'])
    op.create_foreign_key('audit_logs_person_id_fkey', 'audit_logs', 'missing_persons',
                         ['person_id'], ['person_id'])
    op.create_foreign_key('person_photos_person_id_fkey', 'person_photos', 'missing_persons',
                         ['person_id'], ['person_id'], ondelete='CASCADE')


def downgrade() -> None:
    # Drop foreign key constraints
    op.drop_constraint('person_photos_person_id_fkey', 'person_photos', type_='foreignkey')
    op.drop_constraint('audit_logs_person_id_fkey', 'audit_logs', type_='foreignkey')
    op.drop_constraint('audit_logs_user_id_fkey', 'audit_logs', type_='foreignkey')
    
    # Convert back to string types
    op.alter_column('audit_logs', 'ip_address',
                    type_=sa.String(45),
                    postgresql_using='ip_address::varchar')
    op.alter_column('audit_logs', 'person_id',
                    type_=sa.String(36),
                    postgresql_using='person_id::varchar')
    op.alter_column('audit_logs', 'user_id',
                    type_=sa.String(36),
                    postgresql_using='user_id::varchar')
    op.alter_column('audit_logs', 'log_id',
                    type_=sa.String(36),
                    postgresql_using='log_id::varchar')
    
    op.alter_column('person_photos', 'person_id',
                    type_=sa.String(36),
                    postgresql_using='person_id::varchar')
    op.alter_column('person_photos', 'photo_id',
                    type_=sa.String(36),
                    postgresql_using='photo_id::varchar')
    
    op.alter_column('missing_persons', 'person_id',
                    type_=sa.String(36),
                    postgresql_using='person_id::varchar')
    
    op.alter_column('admin_users', 'user_id',
                    type_=sa.String(36),
                    postgresql_using='user_id::varchar')
    
    # Recreate foreign key constraints
    op.create_foreign_key('person_photos_person_id_fkey', 'person_photos', 'missing_persons',
                         ['person_id'], ['person_id'], ondelete='CASCADE')
    op.create_foreign_key('audit_logs_person_id_fkey', 'audit_logs', 'missing_persons',
                         ['person_id'], ['person_id'])
    op.create_foreign_key('audit_logs_user_id_fkey', 'audit_logs', 'admin_users',
                         ['user_id'], ['user_id'])
