"""Writes the exe's file properties (version, publisher) for PyInstaller --version-file.
    python tools/version_info.py <out file>"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
COMPANY = 'Griff inc.'

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={v}, prodvers={v}, mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', '{company}'),
      StringStruct('FileDescription', 'Arua Companion'),
      StringStruct('FileVersion', '{s}'),
      StringStruct('InternalName', 'Arua Companion'),
      StringStruct('OriginalFilename', 'Arua Companion.exe'),
      StringStruct('ProductName', 'Arua'),
      StringStruct('ProductVersion', '{s}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main(out: str) -> None:
    s = (REPO / 'VERSION').read_text(encoding='utf-8').strip()
    parts = [int(x) for x in s.split('.')][:4]
    v = tuple(parts + [0] * (4 - len(parts)))
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(TEMPLATE.format(v=v, s=s, company=COMPANY), encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1])
