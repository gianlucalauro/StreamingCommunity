#!/usr/bin/env python3
import os
import sys

from StreamingCommunity.Util.os import os_summary


def main():
    os_summary.init()
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webgui.settings")
    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    main()
