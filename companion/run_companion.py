"""Entry point for the packaged app (PyInstaller)."""
import os
import sys

if getattr(sys, 'frozen', False):
    # Files extracted from a downloaded zip are blocked; clear that before .NET loads (see unblock.py).
    # Only the app's own bundle folder (_internal), never anything else next to the exe.
    from arua_companion.unblock import unblock_tree
    unblock_tree(sys._MEIPASS)

from arua_companion.app import main

if __name__ == "__main__":
    main()
