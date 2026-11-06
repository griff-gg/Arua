# Arua changelog

## 0.2.1 – 2026-11-06

- New: **Arua-0.2.1-Setup.exe** installs everything: finds the ROSE Online folder, lets you tick the
  themes you want, installs the Arua Companion with a Start menu shortcut, and can be uninstalled from
  Windows Settings > Apps.
- New: **updates from the Companion**. A gold Update button appears when a new Arua release is out; one
  click installs it and reopens the Companion. Your lists and settings are applied to new theme files
  automatically (no more pressing Save after an update).
- New: Companion **Themes** tab: add or remove Arua Ice / Dark / Midnight, check for updates.
- New: Arua icon and logo (app, setup, Start menu).
- Fixed: in the Companion, the Loot filter page showed on top of the other tabs.
- Fixed: the Companion did not open after extracting the release zip with Windows Explorer
  ("Failed to resolve Python.Runtime.Loader.Initialize"). Windows blocked the downloaded files; the
  Companion now unblocks its own files when it starts.

## 0.2.0 – 2026-11-05

- New: **Arua Companion**, a settings app in the ROSE Online folder (`Arua Companion\Arua Companion.exe`):
  loot lists with item search (all game item names), colours and profiles; target marker colour; drop name
  box / outline / opacity; group buff rows, columns, class icons, minimap size and Party Bars defaults.
  Saves into every installed Arua theme (with backups); Ctrl+F5 in game reloads the UI.
  The window is the Arua frame itself (no Windows title bar; drag the title band, X in the frame).
  Profiles: click one to load it; edits only change a profile when you press Save changes or New.
- Themes: settings blocks for the group window and minimap, and a drop name style sheet, filled in by
  the Companion. The Loot Filter tab in game now points to the Companion.
- Removed: the `Arua Loot Filter.bat` helper (the Companion does the same and more). Delete
  `Arua Loot Filter.bat` and `arua_loot_filter.ps1` from your ROSE Online folder.
- Known issue (game client, not Arua): the game can crash on close when it started with a custom theme
  selected. Switching theme once per session avoids it. Reported to and reproduced by the ROSE team.

## 0.1.0 – 2026-11-04

First release for the ROSE Online patch of 3 November 2026.

- Arua is now three real themes in their own folders: **Arua Ice**, **Arua Dark** and
  **Arua Midnight**, picked in Options > Interface > Theme. The old in-game Theme switch is gone.
- Rebuilt on Rednim's new interface files: new tabs, window sounds, the movable HUD, slot rows that no
  longer wrap at odd UI scales, the click-through quest tracker, clan member name tooltips, the new
  nameplate and shop sign layout, and the new group / party window structure.
- Player shop: the Trade button and selected-item line are gone (the game removed them); trade with a
  double-click or by dragging.
- Character stats show the totals (the game no longer gives the base values).
- Loot filter: lists are saved with the new **Arua Loot Filter.bat** helper. In game you can switch
  profiles and modes at once, and add names for the session.
- Targeted monster: "[name] element | counter elements" on one line.
- Group Options: class icons on/off switch (was in Options > Add-ons).
- Performance: the group window no longer scans the whole window several times a second; the minimap
  has no always-running timer; timers only run while their feature is in use.
- Fixed: a crash when closing the game; squares and red / yellow states behind buttons; unreadable
  hover text on gold buttons in Dark / Midnight; titles cut off in a few windows; HUD status icon log
  spam.
- Removed from Options > Add-ons (they can no longer work): Theme cards, Party Bars, Target Marker
  colour, Target Bar switches.

## 0.0.92 and earlier

Released through the ROSE Online Toolbox as files in `data\ui\themes\rose` (before the 3 November 2026
patch). That install method no longer works after the patch: see Install in the README.
