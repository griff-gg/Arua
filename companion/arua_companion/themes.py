"""Finding the installed Arua themes and editing their files safely."""
import shutil
from pathlib import Path


def find_arua_themes(game: Path) -> list[Path]:
    root = Path(game) / 'data' / 'ui' / 'themes'
    if not root.is_dir():
        return []
    return sorted(p for p in root.glob('arua_*') if p.is_dir() and (p / 'theme.toml').is_file())


def replace_block(text: str, begin: str, end: str, new_block: str) -> tuple[str, int]:
    """Replace every region from a line starting with `begin` to the next line starting with `end`
    (both inclusive) with new_block. Keeps the file's line endings."""
    nl = '\r\n' if '\r\n' in text else '\n'
    block = new_block.replace('\r\n', '\n').replace('\n', nl)
    lines = text.split(nl)
    out, i, count = [], 0, 0
    while i < len(lines):
        if lines[i].lstrip().startswith(begin):
            j = i + 1
            while j < len(lines) and not lines[j].lstrip().startswith(end):
                j += 1
            if j == len(lines):          # no end marker: leave the rest alone
                out.extend(lines[i:])
                break
            out.append(block)
            count += 1
            i = j + 1
            continue
        out.append(lines[i])
        i += 1
    return nl.join(out), count


def can_write(paths: list[Path]) -> bool:
    try:
        for p in paths:
            p = Path(p)
            if p.is_file():
                with open(p, 'ab'):
                    pass
            elif p.is_dir():
                probe = p / '.arua_write_test'
                probe.write_bytes(b'')
                probe.unlink()
    except OSError:
        return False
    return True


def backup(file: Path, game: Path, theme: str | None) -> None:
    """Copy file to <game>/arua_companion_backup/[<theme>/]<path relative to the theme or game>."""
    file, game = Path(file), Path(game)
    if not file.is_file():
        return
    base = game / 'data' / 'ui' / 'themes' / theme if theme else game
    dest = game / 'arua_companion_backup' / (theme or '') / file.relative_to(base)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(file, dest)


def read_text(path: Path) -> str:
    with open(path, encoding='utf-8', newline='') as f:
        return f.read()


def write_text(path: Path, text: str) -> None:
    with open(path, 'w', encoding='utf-8', newline='') as f:
        f.write(text)
