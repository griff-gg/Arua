"""Remove Windows' "downloaded from the internet" mark from the app's own files.

Explorer copies that mark onto every file it extracts from a downloaded zip, and
.NET then refuses to load Python.Runtime.dll, so the window never opens.
Must run before webview is imported. Uses only the standard library."""
import os


def unblock_tree(root):
    """Delete the Zone.Identifier stream of every file under root. Returns how many were removed."""
    removed = 0
    for dp, _, files in os.walk(str(root)):
        for name in files:
            try:
                os.remove(os.path.join(dp, name) + ':Zone.Identifier')
                removed += 1
            except OSError:
                pass
    return removed
