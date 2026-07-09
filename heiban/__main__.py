#!/usr/bin/env python3
"""
HeiBan — run as module
Usage: python -m heiban input.md -o output.docx
"""

from .cli_new import main

if __name__ == "__main__":
    main()
