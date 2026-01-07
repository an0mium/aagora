"""
Safety modules for nomic loop.

Provides:
- checksums: Protected file integrity verification
- backups: Backup and restore functionality
"""

from .checksums import (
    PROTECTED_FILES,
    SAFETY_PREAMBLE,
    compute_file_checksum,
    init_protected_checksums,
    verify_protected_files_unchanged,
    get_protected_checksums,
)
from .backups import (
    create_backup,
    restore_backup,
    get_latest_backup,
    verify_protected_files,
    list_backups,
)

__all__ = [
    # Checksums
    "PROTECTED_FILES",
    "SAFETY_PREAMBLE",
    "compute_file_checksum",
    "init_protected_checksums",
    "verify_protected_files_unchanged",
    "get_protected_checksums",
    # Backups
    "create_backup",
    "restore_backup",
    "get_latest_backup",
    "verify_protected_files",
    "list_backups",
]
