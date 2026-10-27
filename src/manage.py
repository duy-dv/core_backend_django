#!/usr/bin/env python
"""Điểm chạy các lệnh quản trị Django: migrate, runserver, test..."""

import os
import sys


def main():
    """Chạy lệnh được truyền vào từ CMD hoặc terminal."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không nạp được Django. Hãy activate venv và cài requirements.txt trước."
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
