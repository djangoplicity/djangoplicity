#!/usr/bin/env python
import sys

if __name__ == "__main__":
    from django.conf import settings
    settings.configure(DEBUG=True)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
