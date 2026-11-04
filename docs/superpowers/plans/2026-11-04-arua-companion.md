# Arua Companion v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A Windows app in the ROSE Online folder that edits loot lists (with item search), the target marker colour, the drop name style and the group / minimap / Party Bars defaults, and writes them into the installed Arua themes.

**Architecture:** A Python package (`companion/arua_companion/`) holds all logic as pure, tested functions: loot filter (port of `arua_loot_filter.ps1`), generators for the generated theme files, a theme writer that replaces marked blocks with backups, settings persistence and item search. A pywebview window shows an HTML/CSS/JS interface in Arua's look and calls the Python `Api`. The Arua theme build (local workspace `C:\Users\nvspa\Desktop\Arua_themes`) gains settings blocks and two generated style sheets the app fills in. PyInstaller builds a folder (`Arua Companion\` with the exe, one-folder mode: starts instantly); `items.json` sits next to the exe as a plain file so a game patch only needs a new list.

**Tech Stack:** Python 3.14, pywebview (Edge WebView2), pytest, PyInstaller (one-folder, windowed); Pillow for exporting Arua art to PNG; urllib for the item list update.

**Spec:** `docs/superpowers/specs/2026-11-04-arua-companion-design.md`

## Global Constraints

- The ROSE archive keys and any ChaCha20 / VFS / BLAKE3 decryption code never enter `C:\Users\nvspa\Desktop\Arua_repo` (no file, no commit, no build input). The item extractor lives only in `C:\Users\nvspa\Desktop\Arua_themes\tools\items\`. Only `companion/data/items.json` (plain names) is shipped.
- Writes only to: `<game>\data\ui\themes\arua_*\` (folders with a `theme.toml`), `<game>\loot_filter.txt`, `<game>\loot_filter_profiles.txt`, `<game>\arua_companion.json`, `<game>\arua_companion_backup\`.
- Never touch the game process. Network only when the player clicks "Update item list" (one GET of `https://raw.githubusercontent.com/griff-gg/Arua/main/companion/data/items.json`).
- Inline Lua written into theme files contains no `<` or `&`; strings use `\ddd` escapes (same as `ConvertTo-LuaString` in `arua_loot_filter.ps1`).
- Loot files keep their existing format (`yellow=a, b` lines; profiles `active=Name` + `[Name]` sections).
- Every changed file gets a backup copy before it is written.
- After Save the app shows exactly: "Saved. Restart the game, or press Ctrl+F5 in game to reload the UI."
- Defaults (= the current Arua look): marker red; drop box off, drop outline on, drop opacity 100; group rows 3, columns Auto, class icons on; minimap 190; Party Bars normal.
- Commits: author `griff-gg <348925957+griff-gg@users.noreply.github.com>`, no Co-Authored-By / "Generated with" lines. Commit locally; push only after griff_gg says yes.

## Review Focus

- Game folder has no Arua theme installed (or only `rose`): Save must say "No Arua theme found in data\ui\themes" and write nothing → test in Task 3.
- Loot files saved by Notepad with a UTF-8 BOM, CRLF, `#` comment lines or unknown keys: names must parse without the BOM, comments/unknown lines are ignored on read → test in Task 1.
- An Arua theme from an older build without the `ARUA-SETTINGS` / `ARUA-LF-DATA` markers: that file is skipped and reported, never corrupted → test in Task 3.
- Item names with `'`, `"`, `\`, `&`, `<` or accents: rules and Lua blocks stay valid (Lua parses, no raw `<`/`&` in Lua) → test in Task 1.
- Game folder not writable (Program Files): the app relaunches itself elevated once; if refused it shows "Windows did not allow writing to the game folder. Nothing was changed." → test of `can_write` in Task 3, relaunch checked by hand in Task 8.

---

### Task 1: Loot filter core (port of the helper)

**Files:**
- Create: `companion/arua_companion/__init__.py` (empty), `companion/arua_companion/lootfilter.py`
- Create: `companion/tests/fixtures/lf_basic/loot_filter.txt`, `.../loot_filter_profiles.txt` (copy griff_gg's current files), `companion/tests/fixtures/lf_basic/expected_lf_rules.css`, `expected_lf_data.lua`
- Test: `companion/tests/test_lootfilter.py`

**Interfaces:**
- Produces:
  - `COLORS: tuple[str, ...] = ('yellow','blue','purple','red','green','rainbow')`
  - `@dataclass Lists: yellow..rainbow: str; only_filtered: bool; dim_others: bool; name_size: int | None`
  - `@dataclass Profile: name: str; lists: dict[str, str]`  (keys = COLORS)
  - `@dataclass Profiles: items: list[Profile]; active: str | None`
  - `read_lists(path: Path) -> Lists`, `write_lists(path: Path, lists: Lists) -> None`
  - `read_profiles(path: Path) -> Profiles`, `write_profiles(path: Path, profiles: Profiles) -> None`
  - `lf_hash(text: str) -> str` (djb2 over UTF-8 bytes, mod 1000000007)
  - `lua_string(s: str) -> str`
  - `build_rules_css(lists: Lists, profiles: Profiles, modes: bool = True) -> str`
  - `build_lf_data(lists: Lists, profiles: Profiles) -> str` (the full block from `-- ARUA-LF-DATA-BEGIN` line to `-- ARUA-LF-DATA-END`)
  - `all_names(lists: Lists, profiles: Profiles) -> list[str]` (every listed name, plain lists + all profiles, deduplicated, order kept)

- [ ] **Step 1: Create the fixtures.** Copy `C:\Program Files\ROSE Online\loot_filter.txt` and `loot_filter_profiles.txt` into `fixtures/lf_basic/`. Generate the expected files with the reference helper:
  `powershell -NoProfile -ExecutionPolicy Bypass -File game-folder\arua_loot_filter.ps1 -GameDir companion\tests\fixtures\lf_basic -OutFile companion\tests\fixtures\lf_basic\expected_lf_rules.css`
  For `expected_lf_data.lua`: run the helper against a scratch copy of a theme in a temp game folder and save the text between (and including) the two `ARUA-LF-DATA` marker lines of `game\options_bgfx.html`.

- [ ] **Step 2: Write the failing tests**

```python
def test_rules_css_matches_helper():
    d = FIX / 'lf_basic'
    css = build_rules_css(read_lists(d / 'loot_filter.txt'), read_profiles(d / 'loot_filter_profiles.txt'))
    assert css == (d / 'expected_lf_rules.css').read_text(encoding='utf-8')

def test_lf_data_matches_helper():
    d = FIX / 'lf_basic'
    block = build_lf_data(read_lists(d / 'loot_filter.txt'), read_profiles(d / 'loot_filter_profiles.txt'))
    assert block == (d / 'expected_lf_data.lua').read_text(encoding='utf-8').rstrip('\n')

def test_hash_matches_lua():
    assert lf_hash('LCF') == '193462042'          # tag seen in the installed rules (lfp-193462042)
    assert lf_hash('test sword') == '764709401'

def test_lua_string_escapes():
    s = lua_string("Knight's Sword, Salt & Pepper <Rare>, Épée")
    assert '<' not in s and '&' not in s
    assert s == "'Knight\\039s Sword, Salt \\038 Pepper \\060Rare>, \\195\\137p\\195\\169e'"

def test_read_lists_bom_crlf_comments(tmp_path):
    p = tmp_path / 'loot_filter.txt'
    p.write_bytes('\ufeffyellow=A, B\r\n# note\r\nfoo=bar\r\ndim_others=1\r\nname_size=0\r\n'.encode('utf-8'))
    l = read_lists(p)
    assert (l.yellow, l.dim_others, l.name_size) == ('A, B', True, 0)

def test_write_read_roundtrip(tmp_path):
    l = Lists(yellow='A', blue='', purple='', red='B', green='', rainbow='', only_filtered=False, dim_others=True, name_size=1)
    write_lists(tmp_path / 'f.txt', l)
    assert read_lists(tmp_path / 'f.txt') == l
```

- [ ] **Step 3: Run tests to verify they fail**
  Run: `cd companion && python -m pytest tests/test_lootfilter.py -q` — Expected: FAIL (module not found).

- [ ] **Step 4: Implement `lootfilter.py`** as a line-by-line port of `game-folder/arua_loot_filter.ps1` (`Read-Lists`, `Read-Profiles`, `Add-Block`, the saved-modes block, `ConvertTo-LuaString`, the `$dataLua` block). Read files with `encoding='utf-8-sig'`. `write_lists` writes the six colour lines, then `only_filtered=`, `dim_others=`, `name_size=` (CRLF line ends, like Notepad). `write_profiles` writes `active=` (if set) then each `[Name]` with six colour lines.

- [ ] **Step 5: Run tests to verify they pass** — same command, Expected: 6 passed.

- [ ] **Step 6: Commit** — `git add companion && git commit -m "Companion: loot filter core (port of the helper)"`

---

### Task 2: Settings and generated theme files

**Files:**
- Create: `companion/arua_companion/settings.py`, `companion/arua_companion/generators.py`
- Test: `companion/tests/test_generators.py`

**Interfaces:**
- Consumes: `lua_string`, `all_names` (Task 1)
- Produces:
  - `MARKERS: dict[str, str] = {'red': '211px 878px', 'blue': '2px 910px', 'green': '38px 910px'}` (32x28 sprites in `imgs/iceinv2.dds`)
  - `@dataclass Settings: marker: str = 'red'; drop_box: bool = False; drop_outline: bool = True; drop_opacity: int = 100; group_rows: int = 3; group_columns: int = 0; class_icons: bool = True; minimap_size: int = 190; party_bars: str = 'normal'`
  - `load_settings(path: Path) -> Settings` (missing / broken file → defaults; out-of-range values → clamped: rows 1..3, columns 0 or 2, opacity one of 100/75/50, minimap 190..300, marker/party_bars unknown → default)
  - `save_settings(path: Path, s: Settings) -> None` (JSON, sorted keys)
  - `world_ui_css(s: Settings) -> str` — the whole `styles/spritesheet_world_ui.css` (same text as the old in-game option wrote, with `src: ../imgs/iceinv2.dds;` and the chosen `MARKERS` position, plus the unchanged `world-ui-1` quest block)
  - `nameplate_bars_css(s: Settings) -> str` — whole `styles/ice_nameplate_gauges.css`: normal = `../imgs/iceinv.dds` with gauge-bg-sm-md `160px 394px 200px 26px`, gauge-red-sm-md `2px 532px 200px 26px`, gauge-bg-sm-sm `160px 394px 200px 26px`, gauge-blue-sm-sm `206px 532px 200px 26px`; faded = `../imgs/ice_np_bars.dds` with bg `2px 2px`, red `2px 32px`, bg-sm-sm `2px 2px`, blue `2px 62px` (all `200px 26px`); both keep the `ice-nameplate-keep` block (`../imgs/gauge.dds`, gauge-purple-sm-sm `1px 52px 99px 4px`)
  - `drops_css(s: Settings, names: list[str]) -> str` — whole `styles/arua_drops.css`, rules on `#dropped-item-labels-root .dropped-item`: box on → `background-color: rgba(10, 18, 32, 200); border-radius: 3dp;`, outline off → `font-effect: none;`, opacity < 100 → `opacity: 0.75` / `0.5`; every name in `names` gets `opacity: 1` back (selector `#dropped-item-labels-root .dropped-item[lf-name="NAME"]`, quotes/backslashes stripped like the rules); always contains `.arua-drops-ok { display: block; }` (a sheet without rules fails to load)
  - `settings_lua(s: Settings) -> str` — block `-- ARUA-SETTINGS-BEGIN (written by Arua Companion; do not edit by hand)` / `local ARUA_SETTINGS = { group_rows = 3, group_columns = 0, class_icons = true, minimap_size = 190 }` / `-- ARUA-SETTINGS-END`

- [ ] **Step 1: Write the failing tests**

```python
def test_defaults_reproduce_current_theme_files():
    s = Settings()
    assert world_ui_css(s) == (THEME / 'styles/spritesheet_world_ui.css').read_text(encoding='utf-8')
    assert nameplate_bars_css(s) == (THEME / 'styles/ice_nameplate_gauges.css').read_text(encoding='utf-8')

def test_marker_blue():
    assert 'world-target-marker: 2px 910px 32px 28px;' in world_ui_css(Settings(marker='blue'))

def test_drops_defaults_are_empty_look():
    css = drops_css(Settings(), [])
    assert 'background-color' not in css and 'font-effect: none' not in css and 'opacity: 0.' not in css
    assert '.arua-drops-ok { display: block; }' in css

def test_drops_box_no_outline_half():
    css = drops_css(Settings(drop_box=True, drop_outline=False, drop_opacity=50), ['Pink Powder'])
    assert 'opacity: 0.5' in css and 'font-effect: none' in css and 'background-color: rgba(10, 18, 32, 200)' in css
    assert '.dropped-item[lf-name="Pink Powder"] { opacity: 1; }' in css

def test_settings_lua_has_no_forbidden_chars():
    lua = settings_lua(Settings(group_rows=1, group_columns=2, class_icons=False, minimap_size=260))
    assert '<' not in lua and '&' not in lua
    assert 'group_rows = 1, group_columns = 2, class_icons = false, minimap_size = 260' in lua

def test_load_settings_clamps(tmp_path):
    p = tmp_path / 's.json'
    p.write_text('{"group_rows": 9, "drop_opacity": 33, "minimap_size": 999, "marker": "pink"}')
    s = load_settings(p)
    assert (s.group_rows, s.drop_opacity, s.minimap_size, s.marker) == (3, 100, 300, 'red')
```
  (`THEME = Path(__file__).resolve().parents[2] / 'themes' / 'arua_ice'` in `conftest.py`; Task 6 updates the theme so its defaults equal these generators' output.)

- [ ] **Step 2: Run tests to verify they fail** — `python -m pytest tests/test_generators.py -q`, Expected: FAIL (import error).
- [ ] **Step 3: Implement `settings.py` and `generators.py`** with the signatures above.
- [ ] **Step 4: Run tests** — Expected: the two `test_defaults_reproduce_current_theme_files` asserts pass only after Task 6; mark that test `@pytest.mark.xfail(strict=True, reason='theme defaults land in Task 6')` now and remove the marker in Task 6. Others: PASS.
- [ ] **Step 5: Commit** — `git commit -m "Companion: settings and generated theme files"`

---

### Task 3: Theme writer and Save

**Files:**
- Create: `companion/arua_companion/themes.py`, `companion/arua_companion/apply.py`
- Test: `companion/tests/test_apply.py` (builds a fake game folder in `tmp_path` by copying `themes/arua_ice` as `arua_ice` and `arua_dark`, plus a `rose` folder without `theme.toml`)

**Interfaces:**
- Consumes: Tasks 1 and 2
- Produces:
  - `find_arua_themes(game: Path) -> list[Path]` — `game/data/ui/themes/arua_*` with a `theme.toml`, sorted
  - `replace_block(text: str, begin: str, end: str, new_block: str) -> tuple[str, int]` — replaces every `begin…end` region (begin marker line to end marker line inclusive) with `new_block`; returns the new text and how many were replaced; keeps the file's line endings
  - `can_write(paths: list[Path]) -> bool` — opens each existing file for append and closes it; False on PermissionError
  - `@dataclass SaveReport: themes: list[str]; skipped: list[str]; error: str | None`
  - `save_all(game: Path, settings: Settings, lists: Lists, profiles: Profiles) -> SaveReport` — writes `loot_filter.txt`, `loot_filter_profiles.txt`, `arua_companion.json`; for each theme: `styles/lf_rules.css` = `build_rules_css`, `styles/spritesheet_world_ui.css`, `styles/ice_nameplate_gauges.css`, `styles/arua_drops.css`, the `ARUA-LF-DATA` block in `game/dropped_item_labels.html` and `game/options_bgfx.html`, the `ARUA-SETTINGS` block in `game/arena_group.html` and `game/minimap.html`. Before writing any file it copies it to `game/arua_companion_backup/<theme>/<relative path>` (overwriting the previous backup). A theme file missing its markers is listed in `skipped` as `"<theme>/<file>: no settings block (old Arua build)"` and left untouched. No Arua theme → `error = "No Arua theme found in data\\ui\\themes"` and nothing is written.

- [ ] **Step 1: Write the failing tests**

```python
def test_save_writes_every_arua_theme(fake_game):
    r = save_all(fake_game, Settings(marker='green', group_rows=2), LISTS, PROFILES)
    assert r.error is None and r.themes == ['arua_dark', 'arua_ice'] and r.skipped == []
    for t in ('arua_dark', 'arua_ice'):
        th = fake_game / 'data/ui/themes' / t
        assert 'world-target-marker: 38px 910px' in (th / 'styles/spritesheet_world_ui.css').read_text()
        assert 'group_rows = 2' in (th / 'game/arena_group.html').read_text(encoding='utf-8')
        assert "active = 'LCF'" in (th / 'game/options_bgfx.html').read_text(encoding='utf-8')
    assert (fake_game / 'arua_companion_backup/arua_ice/game/arena_group.html').exists()

def test_save_leaves_rose_alone(fake_game):
    before = sorted(p.name for p in (fake_game / 'data/ui/themes/rose').rglob('*'))
    save_all(fake_game, Settings(), LISTS, PROFILES)
    assert sorted(p.name for p in (fake_game / 'data/ui/themes/rose').rglob('*')) == before

def test_no_arua_theme(tmp_path):
    (tmp_path / 'data/ui/themes/rose').mkdir(parents=True)
    r = save_all(tmp_path, Settings(), LISTS, PROFILES)
    assert r.error == 'No Arua theme found in data\\ui\\themes'
    assert not (tmp_path / 'loot_filter.txt').exists()

def test_old_build_without_markers_is_skipped(fake_game):
    f = fake_game / 'data/ui/themes/arua_ice/game/minimap.html'
    f.write_text(f.read_text(encoding='utf-8').replace('ARUA-SETTINGS', 'X'), encoding='utf-8')
    before = f.read_text(encoding='utf-8')
    r = save_all(fake_game, Settings(), LISTS, PROFILES)
    assert 'arua_ice/game/minimap.html: no settings block (old Arua build)' in r.skipped
    assert f.read_text(encoding='utf-8') == before

def test_saved_themes_still_validate(fake_game):
    save_all(fake_game, Settings(drop_box=True), LISTS, PROFILES)
    # same checks as Arua_themes/validate.py: every inline Lua parses and has no '<' or '&'
    for html in (fake_game / 'data/ui/themes/arua_ice/game').glob('*.html'):
        for script in re.findall(r'<script>(.*?)</script>', html.read_text(encoding='utf-8'), re.S):
            if html.name != 'speech_bubbles.html':
                assert '<' not in script and '&' not in script
            assert lua_parses(script)           # helper using lupa: load(s) returns a function

def test_can_write(tmp_path):
    f = tmp_path / 'a.txt'; f.write_text('x')
    assert can_write([f]) is True
```
  (`fake_game`, `LISTS`, `PROFILES`, `lua_parses` live in `companion/tests/conftest.py`; `LISTS`/`PROFILES` are read from `fixtures/lf_basic`.)

- [ ] **Step 2: Run to verify they fail** — `python -m pytest tests/test_apply.py -q` → FAIL.
- [ ] **Step 3: Implement `themes.py` and `apply.py`.** `test_save_writes_every_arua_theme` needs the theme from Task 6 (markers present); keep it `xfail(strict=True)` until Task 6, like Task 2.
- [ ] **Step 4: Run tests** → PASS (except the marked ones).
- [ ] **Step 5: Commit** — `git commit -m "Companion: theme writer and save"`

---

### Task 4: Item list and search

**Files:**
- Create (LOCAL ONLY, not in the repo): `C:\Users\nvspa\Desktop\Arua_themes\tools\items\export_items.py`
- Create: `companion/data/items.json`, `companion/arua_companion/items.py`
- Test: `companion/tests/test_items.py`

**Interfaces:**
- Produces:
  - `items.json` format: `{"patch": "2026-11-03", "items": [{"name": "Pink Powder", "cat": "material"}, ...]}`, sorted by name, unique by (name, cat). Categories: weapon, subweapon, cap, body, arms, foot, back, face, jewel, consumable, gem, material, quest, pat (from list_weapon, list_subwpn, list_cap, list_body, list_arms, list_foot, list_back, list_faceitem, list_jewel, list_useitem, list_gemitem, list_natural, list_questitem, list_pat).
  - `load_items(path: Path) -> list[dict]`
  - `search(items: list[dict], query: str, limit: int = 20) -> list[dict]` — case-insensitive substring; fewer than 2 non-space characters → `[]`; names that start with the query come first, then the rest, each group alphabetical.
  - `ITEMS_URL = 'https://raw.githubusercontent.com/griff-gg/Arua/main/companion/data/items.json'`
  - `update_items(dest: Path, fetch=urllib_fetch) -> tuple[bool, str]` — downloads `ITEMS_URL`, checks it parses and has `"items"` with at least 1000 entries, then replaces `dest` (write to `dest.with_suffix('.tmp')`, then `os.replace`). Returns `(True, 'Item list updated: N items (patch P).')` or `(False, 'Could not update the item list: <reason>. The current list is kept.')`; never leaves a broken file. `fetch(url) -> bytes` is injectable for tests.

- [ ] **Step 1: Write `export_items.py` (local).** It imports `vfs.VFS` and `stb_parser.parse_stb_at` from its own folder, reads the 14 tables, takes column 0, strips, drops empty names, and writes `items.json` to the path given as its only argument. Run it: `python C:\Users\nvspa\Desktop\Arua_themes\tools\items\export_items.py companion\data\items.json`. Expected: about 18,600 items; `"Hime"`, `"Ice Key Fragment"`, `"Wooden Sword"` present.
- [ ] **Step 2: Check the repo stays clean** — `git ls-files | findstr /I "vfs chacha blake stb_parser export_items"` must print nothing; `findstr /S /I /M "chacha expand blake3 data.idx" companion\*` must print nothing.
- [ ] **Step 3: Write the failing tests**

```python
def test_search_orders_prefix_first():
    items = [{'name': 'Purple Powder', 'cat': 'material'}, {'name': 'Pink Powder', 'cat': 'material'}, {'name': 'Powder Keg', 'cat': 'consumable'}]
    assert [i['name'] for i in search(items, 'powder')] == ['Powder Keg', 'Pink Powder', 'Purple Powder']

def test_search_needs_two_chars():
    assert search([{'name': 'Hime', 'cat': 'material'}], 'h') == []

def test_shipped_list_has_known_names():
    names = {i['name'] for i in load_items(Path(__file__).resolve().parents[1] / 'data' / 'items.json')}
    assert {'Hime', 'Ice Key Fragment', 'Astarot Feather', 'Wooden Sword'} <= names
```
- Extra tests: `test_update_items_replaces_file` (fake fetch returns a valid list of 1000+ items → file replaced, message has the count) and `test_update_items_keeps_old_on_error` (fake fetch raises `OSError('offline')` or returns `b'{}'` → returns False, old file unchanged).
- [ ] **Step 4: Run, implement `items.py`, run again** → PASS.
- [ ] **Step 5: Commit** — `git add companion/data/items.json companion/arua_companion/items.py companion/tests/test_items.py && git commit -m "Companion: item list and search"`

---

### Task 5: Arua look for the app (art export)

**Files:**
- Create (local tool, may live in the repo — it only reads theme art): `companion/tools/export_art.py`
- Create: `companion/ui/art/*.png`

**Interfaces:**
- Produces PNGs used by Task 7's CSS: `frame-tl.png` … `frame-br.png` (the 9 `ice-frame-*` slices), `panel-*.png` (9 `ice-panel-*`), `tab-l/c/r.png`, `tab-hover-l/c/r.png`, `tab-sel-l/c/r.png`, `corner-tl.png`, `corner-br.png`, `close-n/h/a.png`, `check-off.png`, `check-on.png`, and the three marker sprites `marker-red/blue/green.png` (from `imgs/iceinv2.dds` at the `MARKERS` positions, 32x28). Colours are CSS variables taken from `ice_window.css`: navy `rgb(30, 62, 112)`, gold `rgb(214, 166, 60)`, panel `rgb(236, 244, 251)`.
- `export_art.py <theme dir> <out dir>`: parses `styles/ice_sprites.css` (`@spritesheet` blocks: `src` + `name: x y w h`), opens the `.dds` with Pillow, crops each listed sprite to PNG.

- [ ] **Step 1:** Write `export_art.py`; run `python companion/tools/export_art.py themes/arua_ice companion/ui/art`. Expected: all PNGs above exist and are non-empty (check with `dir companion\ui\art`).
- [ ] **Step 2: Commit** — `git commit -m "Companion: Arua art for the interface"`

---

### Task 6: Theme support (Arua build, local workspace)

**Files (in `C:\Users\nvspa\Desktop\Arua_themes`):**
- Modify: `fixups_live.py` (append a new step, after the existing ones)
- Rebuild: `sh build_all.sh` then copy `build/themes/arua_*` over `C:\Users\nvspa\Desktop\Arua_repo\themes\`

**Interfaces:**
- Produces in every built Arua theme:
  - `-- ARUA-SETTINGS-BEGIN …` / `local ARUA_SETTINGS = nil` / `-- ARUA-SETTINGS-END` in **both** inline scripts of `game/arena_group.html` and in the minimap script of `game/minimap.html`.
  - `game/arena_group.html`: after `local t = read_all()` → `if ARUA_SETTINGS then t.group_rows = tostring(ARUA_SETTINGS.group_rows or 3); t.group_layout = tostring(ARUA_SETTINGS.group_columns or 0) end`; in the class icons script, before `enabled = read_flag()` at the end → `if ARUA_SETTINGS and ARUA_SETTINGS.class_icons == false then local b = doc:GetElementById('arena-group'); if b then b:SetClass('ci-0', true) end end`.
  - `game/minimap.html`: `saved = read_saved()` → `saved = read_saved() or (ARUA_SETTINGS and ARUA_SETTINGS.minimap_size)`.
  - `styles/arua_drops.css` = `drops_css(Settings(), [])` output, linked in `game/dropped_item_labels.html` right after the `lf_rules.css` link: `<link type="text/rcss" href="../styles/arua_drops.css" />`.
  - `styles/spritesheet_world_ui.css` and `styles/ice_nameplate_gauges.css` equal `world_ui_css(Settings())` / `nameplate_bars_css(Settings())` (they already do after fix-ups step 9 and assemble.py; Task 2's test proves it).
- No new timers. Lua must keep passing `validate.py`.

- [ ] **Step 1:** Append the step to `fixups_live.py` (idempotent: skip a file whose text already contains `ARUA-SETTINGS-BEGIN`); write `styles/arua_drops.css` into `merged/styles/`.
- [ ] **Step 2:** Run `sh build_all.sh` (share build, no `--lf`). Expected last lines: `build/themes/arua_ice OK`, `…arua_dark OK`, `…arua_midnight OK`.
- [ ] **Step 3:** Check: `grep -c "ARUA-SETTINGS-BEGIN" build/themes/arua_ice/game/arena_group.html` → `2`; `… minimap.html` → `1`; `grep -c arua_drops.css build/themes/arua_ice/game/dropped_item_labels.html` → `1`.
- [ ] **Step 4:** Copy the three built themes into the repo's `themes\`, remove the `xfail` markers from Tasks 2 and 3, run `cd companion && python -m pytest -q` → all pass.
- [ ] **Step 5: Commit (repo)** — `git add themes companion/tests && git commit -m "Themes: settings blocks and drop style sheet for the Companion"`

---

### Task 7: The window

**Files:**
- Create: `companion/arua_companion/app.py`, `companion/ui/index.html`, `companion/ui/app.css`, `companion/ui/app.js`, `companion/requirements.txt` (`pywebview`, `pytest`, `lupa`, `Pillow`, `pyinstaller`)
- Test: `companion/tests/test_api.py`

**Interfaces:**
- Consumes: everything above.
- Produces: `class Api` (exposed to JS as `window.pywebview.api`), constructed with `game: Path`:
  - `get_state() -> dict` — `{"settings": asdict(Settings), "lists": {...six colours..., "only_filtered", "dim_others", "name_size"}, "profiles": {"items": [{"name", "lists"}], "active"}, "themes": [names], "game": str}`
  - `search(query: str) -> list[dict]`
  - `update_item_list() -> dict` — `{"ok": bool, "message": str}` from `update_items(<app folder>/items.json)`; reloads the list on success.
  - `save(state: dict) -> dict` — `{"ok": bool, "message": str, "skipped": [..]}`; ok message is exactly the Global Constraints text; error → the `SaveReport.error` text.
  - `main()` — game folder = folder of the running exe (or `--game <path>` for development); if `can_write` fails, relaunch elevated once via `ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, args, None, 1)`; if refused, the window still opens and Save shows "Windows did not allow writing to the game folder. Nothing was changed."; window title `Arua Companion`, size 900×640, not resizable below 760×560.
- Screens (one window, three tabs in Arua tab style; selected tab gold):
  1. **Loot filter** — search box (results under it: name + category, six colour dots per result, click a dot = add to that list); the six lists as removable name pills in their colour; profile row (pills, active = gold; buttons New, Rename, Delete); modes: Only show filtered drops, Dim other drops, name size Normal / Bigger / Big.
  2. **Markers & drops** — marker colour Red / Blue / Green (show the sprite); drop names: Dark box (check), Black outline (check), Opacity 100 / 75 / 50.
  3. **Group & minimap** — Buff rows 1/2/3, Columns Auto/2, Class icons on/off, Minimap size slider 190–300, Party Bars Normal / Faded.
  - Footer: Save button (gold), status text line under it. On the Loot filter tab, an "Update item list" button next to the search box (shows the list's patch date).

- [ ] **Step 1: Write the failing tests**

```python
def test_get_state_roundtrip(fake_game):
    api = Api(fake_game)
    st = api.get_state()
    assert st['profiles']['active'] == 'LCF' and 'arua_ice' in st['themes']
    st['settings']['marker'] = 'blue'
    assert api.save(st) == {'ok': True, 'message': 'Saved. Restart the game, or press Ctrl+F5 in game to reload the UI.', 'skipped': []}
    assert Api(fake_game).get_state()['settings']['marker'] == 'blue'

def test_search_through_api(fake_game):
    assert any(i['name'] == 'Pink Powder' for i in Api(fake_game).search('pink'))
```
- [ ] **Step 2: Run → FAIL; implement `app.py` (`Api` + `main`), then the HTML/CSS/JS using the PNGs from Task 5 and the colour variables; run → PASS.**
- [ ] **Step 3: Run by hand:** `python -m arua_companion.app --game "C:\Program Files\ROSE Online"` — the window opens in Arua look, search "pow" shows Pink / Purple Powder, adding a name and pressing Save shows the saved message. (Uses griff_gg's real game folder: back up `data\ui\themes` first.)
- [ ] **Step 4: Commit** — `git commit -m "Companion: window and interface"`

---

### Task 8: Packaging and docs

**Files:**
- Create: `companion/build_exe.ps1`
- Modify: `README.md` (new section "Arua Companion" replacing the helper as the main way; keep the helper section as "without the app"), `CHANGELOG.md` (0.2.0 entry), `VERSION` (`0.2.0`)
- Output: `game-folder/Arua Companion/` (exe + parts + `items.json`)

- [ ] **Step 1:** `build_exe.ps1` runs `python -m PyInstaller --noconfirm --onedir --windowed --name "Arua Companion" --add-data "ui;ui" arua_companion/app.py` from `companion\`, copies `data\items.json` next to the exe (`dist\Arua Companion\items.json`), and copies the whole `dist\Arua Companion\` folder to `..\game-folder\Arua Companion\`. The app reads `items.json` from its own folder (fallback: bundled `data\items.json` when run from source). Expected: `game-folder\Arua Companion\Arua Companion.exe` starts in under a second.
- [ ] **Step 2: Check by hand:** copy the `Arua Companion` folder into `C:\Program Files\ROSE Online\`, double-click the exe: Windows asks for permission once, the window opens, Save works, start the game: marker colour, drop style, buff rows and minimap size are as saved; exit the game cleanly (no crash dump in `%LOCALAPPDATA%\Rednim Games\ROSE Online\data\sentry\reports`).
- [ ] **Step 3: Secret scan before commit** — `findstr /S /I /M "chacha expand blake3 data.idx rose.vfs" game-folder\* companion\*` prints nothing (the exe included).
- [ ] **Step 4: Commit locally** — `git commit -m "Arua 0.2.0: Arua Companion"`. Push only after griff_gg says yes.
