# Arua Companion – design

Date: 2026-11-04. Owner: griff_gg. Status: draft for review.

## Why

Since the ROSE Online patch of 3 November 2026 the in-game UI can no longer read or write files. Themes are
fixed folders (`data\ui\themes\<name>\`, picked in Options > Interface > Theme), so the options Arua used to
offer in game (loot lists, marker colour, drop name style, group layout, minimap size, Party Bars) either reset
at every restart or are gone. Martin's ROSE Online Toolbox installs themes and mods; nothing lets a player
*customise* an installed theme any more.

The Arua Companion is that missing settings panel: a small desktop app, started outside the game, that writes
the player's choices into the installed theme files. The next game start (or a UI refresh with Ctrl+F5 while
the game runs) shows them.

Success: a player can set up their loot filter (with item search), marker colour, drop name look and their
group / minimap defaults in one place, press Save, and see it in game, without editing text files or running
scripts.

## Goals (version 1)

1. **Loot lists**: search all game item names, add a name, choose its colour (Yellow, Blue, Purple, Red,
   Green, Rainbow); remove names; profiles (create, rename, delete, choose the active one); the modes
   Dim other drops / Only show filtered drops / filtered name size (Normal, Bigger, Big).
2. **Target marker colour**: the arrows next to a selected player's name (the colours Arua offered before:
   gold, blue and the others in `ice-target-marker*` sprites).
3. **Drop name style** for drops that are *not* in a list, two separate switches plus opacity (griff_gg):
   a dark box behind the name (on/off), a black outline on the text (on/off), opacity 100 / 75 / 50 %.
4. **Defaults that now reset every restart**: group buff rows (1 / 2 / 3), group columns (Auto / 2),
   class icons on/off, minimap size (190–300), Party Bars over group members' heads (Normal / Faded).

## Non-goals (version 1)

- Installing, updating or removing themes (that is Martin's Toolbox).
- Support for themes other than Arua (design so it can come later; see "Other themes").
- An update checker / auto-update.
- Anything inside the running game: no reading or writing game memory, no talking to the game process.

## Anti-goals (a failure even if it works)

- **The ROSE archive keys and any ChaCha20 / VFS decryption code never ship** – not in the app, the repo, a
  release or a message. The app only ever contains the plain item-name list (see "Item list").
- Breaking a theme: after a Save the theme must still load (complete folder, valid Lua, valid styles).
- Touching game data outside `data\ui\themes\arua_*` and the loot filter files in the ROSE Online folder.
- Losing the player's existing loot lists or profiles.

## Constraints

- Windows 10 / 11. The app lives in the **ROSE Online folder** (next to `trose.exe`), so everything Arua-related
  is in one spot.
- The game folder is usually under Program Files: writing needs permission (UAC). Ask for it when saving
  (or at start), never silently fail.
- Inline Lua in theme files must not contain `<` or `&` (game parser); every string the app writes into Lua is
  escaped as `\ddd`.
- Any timer added to a theme must stop on its document's `unload` event (a timer firing at exit crashed the
  game; fixed 2026-11-04).
- The theme files are rebuilt by the Arua build (`Desktop\Arua_themes\build_all.sh`, local only). The app must
  write its settings into marked blocks so a theme update + one Save restores them.

## How it works (decided)

- **Tech** (griff_gg agreed to the proposal): HTML/CSS/JS interface in the Edge WebView2 that ships with
  Windows 10/11, packaged as one `.exe` (builder's choice of wrapper, e.g. Tauri or pywebview + PyInstaller;
  prefer the one antivirus flags least). The interface reuses Arua's real art and colours so it looks like the
  theme (ice panels, gold accents).
- **Open source** in `griff-gg/Arua` (MIT), next to the themes.
- **Storage**: the app's own settings in a file in the ROSE Online folder (e.g. `arua_companion.json`).
  Loot lists stay in `loot_filter.txt` / `loot_filter_profiles.txt` (same format as now), so the existing
  helper and anything else that reads them keeps working.
- **Applying**: on Save the app writes into every installed Arua theme folder (`arua_ice`, `arua_dark`,
  `arua_midnight`, any `arua_*` with a `theme.toml`):
  - loot filter: exactly what `arua_loot_filter.ps1` writes today – `styles\lf_rules.css` and the
    `ARUA-LF-DATA` block in `game\dropped_item_labels.html` and `game\options_bgfx.html`
    (byte-identical output to the helper for the same input; the helper is the reference implementation);
  - everything else: a new marked settings block, e.g. `-- ARUA-SETTINGS-BEGIN ... -- ARUA-SETTINGS-END`,
    in the theme files that need it (group window, minimap, nameplates, drop labels), plus small generated
    style sheets for purely visual options (marker colour, drop name box/opacity, Party Bars). The theme's
    scripts read the settings block at start. Theme-side support for these blocks is part of this project
    (Arua build changes), not only the app.
- After Save the app says: "Saved. Restart the game, or press Ctrl+F5 in game to reload the UI."

## Item list (decided)

- The app ships a plain list of item names (with category, e.g. weapon / armour / material), e.g.
  `items.json`, ~18,600 names.
- It is extracted **locally on griff_gg's PC only**, by hand, after each game patch, from the game's own item
  tables. The extraction tool stays local (anti-goal above). The list in the repo is just text.
- Search: type 2+ letters, show matches (case-insensitive substring), click one, choose its colour.
- Names must match exactly what shows on the ground (checked 2026-11-04: all tested names matched). Players can
  still type a name that is not in the list.

## Other themes (later)

The app should keep theme-specific knowledge in one place (which files / blocks a setting touches), so support
for another theme can be added as a separate "theme profile" later. Version 1 only knows Arua.

## Left to the builder

- Exact screen layout (one window with tabs or sections: Loot filter, Markers & drops, Group & minimap).
- The wrapper (Tauri vs pywebview) and the build/packaging steps.
- How the theme scripts read the settings block, as long as there is no timer and no file access.
- Error handling and messages (plain language), backups of files before writing (recommended: keep a copy of
  each file the app changes, next to it or in an `arua_companion_backup` folder).
- Tests: at minimum, the loot filter output matches `arua_loot_filter.ps1` byte for byte on the same input,
  and every theme still passes `validate.py` after a Save.

## Calls made by Claude (please check)

- The `Arua Loot Filter.bat` helper stays until the app is released; both write the same files.
- The `.exe` ships as a GitHub release download and in `game-folder\` of the repo.
- Marker colours offered are the ones Arua already has art for (`ice-target-marker*` sprites).

- Version 1 is Arua only; other themes are designed for, not built.
- Drop name opacity offered as 100 / 75 / 50 % (you mentioned 50 %).
- The app keeps the existing loot file format instead of a new one.
- Backups of changed files before each Save.
- Asks for Windows permission when saving if the folder is not writable.
