"""Add performance indexes for todos queries

Revision ID: 003_add_performance_indexes
Revises: a0790c76a129
Create Date: 2026-09-21 16:00:00.000000

This migration adds composite and single-column indexes to optimize
common query patterns for the todos table:

1. Composite index (user_id, completed, created_at) - for filtered queries
2. Single index (user_id) - for simple user queries
3. Index on created_at - for sorting

These indexes significantly improve query performance for:
- Listing user's todos with filters
- Counting todos per user
- Sorting by creation date
"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "003_add_performance_indexes"
down_revision: Union[str, None] = "a0790c76a129"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add performance indexes to todos table.
    
    Indexes created:
    - idx_todos_user_id: For queries filtering by user_id alone
    - idx_todos_user_completed_created: Composite index for complex queries
      with filtering and sorting (user_id, completed, created_at DESC)
    - idx_todos_created_at: For queries sorting by created_at
    """
    # Index 1: Single column index on user_id
    # Used for: SELECT * FROM todos WHERE user_id = ?
    op.create_index(
        'idx_todos_user_id',
        'todos',
        ['user_id'],
        unique=False
    )
    
    # Index 2: Composite index for user_id, completed, created_at
    # Used for: SELECT * FROM todos WHERE user_id = ? AND completed = ? ORDER BY created_at DESC
    # This is the most important index - covers filtering and sorting in one
    op.create_index(
        'idx_todos_user_completed_created',
        'todos',
        ['user_id', 'completed', 'created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'}  # Optimize for DESC sorting
    )
    
    # Index 3: Index on created_at for sorting
    # Used when sorting by created_at without user_id filter
    op.create_index(
        'idx_todos_created_at',
        'todos',
        ['created_at'],
        unique=False,
        postgresql_ops={'created_at': 'DESC'}
    )


def downgrade() -> None:
    """Remove performance indexes."""
    op.drop_index('idx_todos_created_at', table_name='todos')
    op.drop_index('idx_todos_user_completed_created', table_name='todos')
    op.drop_index('idx_todos_user_id', table_name='todos')
