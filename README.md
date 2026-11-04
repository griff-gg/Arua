# Arua – a ROSE Online UI theme

A full reskin of the ROSE Online interface: light ice-blue panels with gold highlights, plus a
**Dark** (navy and gold) and a **Midnight** (graphite and silver) version, and a few extras
(loot filter with light beams, target element counters, DPS meter, group and party improvements).
Only UI files: no game data, no changes to the game itself.

Made by **griff_gg**. Built for the ROSE Online patch of **3 November 2026**.

## Install

1. Close the game.
2. Used an older Arua (before the 3 November 2026 patch)? Delete the folder
   `ROSE Online\data\ui\themes\rose` if it exists. Older Arua versions put their files there; with
   them in place the default theme breaks after the patch.
3. Copy the three folders from `themes\` into `ROSE Online\data\ui\themes\`:
   `arua_ice`, `arua_dark`, `arua_midnight`.
4. Copy everything in `game-folder\` into the `ROSE Online` folder itself (the one with `trose.exe`):
   the `Arua Companion` folder, `Arua Loot Filter.bat` and `arua_loot_filter.ps1`.
5. Start the game, open **Options > Interface > Theme** and pick **Arua Ice**, **Arua Dark** or
   **Arua Midnight**.

The game remembers the theme. To go back to the original look, pick **ROSE**.

## Arua Companion

Since the 3 November 2026 patch the game's UI can no longer save settings, so Arua has a small
settings app: **ROSE Online\Arua Companion\Arua Companion.exe**. Open it (outside the game or while
it runs), change what you like and press **Save**. Then restart the game, or press **Ctrl+F5** in game
to reload the UI.

- **Loot filter**: search all item names, click a colour dot to add an item to that list, remove names,
  profiles, Only show filtered drops / Dim other drops, filtered name size.
- **Markers & drops**: target marker colour (red / blue / green); drop names that are not in your lists:
  dark box behind the name, black outline, opacity 100 / 75 / 50 %.
- **Group & minimap**: buff rows, columns, class icons, minimap size, Party Bars (normal / faded).

It writes into every installed Arua theme and keeps a copy of each file it changes in
`ROSE Onlinerua_companion_backup\`. The first time, Windows may ask for permission to write into the
game folder. **Update item list** downloads the newest item list from this repository (only when you
click it); the app never touches the running game.

## Loot filter

Listed drops get a coloured glow, a bigger name and a light beam. Six lists, by rarity: Yellow, Blue,
Purple, Red, Green and Rainbow (the rarer colour wins if a name is in two lists).

- **Your lists** live in `loot_filter.txt` in the ROSE Online folder (and profiles in
  `loot_filter_profiles.txt`). Easiest: edit them in the **Arua Companion**. Without the app: edit them in
  Notepad, then double-click **Arua Loot Filter.bat** and restart the game. The first time, it creates `loot_filter.txt` with short instructions.
  If the game is in Program Files, Windows asks for permission to write there.
- **In game** (Options > Loot Filter) you can switch profiles, Dim other drops, Only show filtered
  drops and the name size at once. You can also add names there: they work right away, but only for
  that session. To keep them, put them in `loot_filter.txt` and run the helper again.
- Saved lists cost nothing while you play. Names you add in game for the session use a small timer
  that marks matching drops; it stops when you switch back to a saved profile or restart.
- Run **Arua Loot Filter.bat** again after you install a new Arua version.

## What's in it

- Every window themed: inventory, character, skills, quests, chat, shops, storage, item mall, mail,
  crafting, clan, party, group, minimap, world map, options and more.
- **Group window**: buff rows (1 / 2 / 3), a fixed 2-column layout, class icons next to members
  (open Group Manager once per session so it knows the classes), stun / sleep / poison / slow frames
  on members (FX button).
- **Target**: the target's element and the elements it is weak against, on the target bar and next to
  the targeted monster's name; a DPS meter.
- **Minimap**: resizable (dot grip, bottom left), x,y and time on the collapsed bar.
- Character info with a 3D preview, fuel dial when riding a cart, zone name title card, see-through
  player shop signs, quickbar and side menu restyled.

## Known limits

The 3 November 2026 patch removed file access from UI scripts, so the UI can no longer save settings
itself:

- Group buff rows / columns, class icons on/off and the minimap size changed in game reset when you
  restart; set your defaults in the **Arua Companion**.
- Loot filter lists are saved with the Companion or the helper (see above), not from the Options window.
- The element icon and DPS meter on the target bar are always on.

## Files

- `themes\arua_ice`, `themes\arua_dark`, `themes\arua_midnight`: the three themes. Each is a complete
  theme folder, as the game requires.
- `game-folder\`: the Arua Companion app and the loot filter helper (PowerShell, built into Windows).
- `companion\`: the Companion's source (Python + pywebview), tests and the item-name list (`data\items.json`).

## Credits

- Arua styling, art and extras: griff_gg.
- Base interface files: Rednim Games, published at
  [rednimgames/rose-public](https://github.com/rednimgames/rose-public). Arua is built on them.
- Nunito font: SIL Open Font License (`font/nunito/OFL.txt` in each theme).

## License

Arua's own work is MIT licensed (see `LICENSE`). The base interface files from Rednim Games keep
their own terms.
