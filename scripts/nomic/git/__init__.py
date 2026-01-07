"""
Git operations for nomic loop.

Provides safe git operations including stash management,
diff retrieval, commits, and rollback helpers.
"""

from .operations import (
    git_stash_create,
    git_stash_pop,
    get_git_diff,
    get_git_diff_full,
    get_git_changed_files,
    get_modified_files,
    git_add_all,
    git_commit,
    git_reset_hard,
    selective_rollback,
    preserve_failed_work,
)

__all__ = [
    "git_stash_create",
    "git_stash_pop",
    "get_git_diff",
    "get_git_diff_full",
    "get_git_changed_files",
    "get_modified_files",
    "git_add_all",
    "git_commit",
    "git_reset_hard",
    "selective_rollback",
    "preserve_failed_work",
]
