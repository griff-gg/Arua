"""Entry point for the packaged app (PyInstaller)."""
import os
import sys

if getattr(sys, 'frozen', False):
    # Files extracted from a downloaded zip are blocked; clear that before .NET loads (see unblock.py).
    from arua_companion.unblock import unblock_tree
    unblock_tree(os.path.dirname(sys.executable))

from arua_companion.app import main

if __name__ == "__main__":
    main()
