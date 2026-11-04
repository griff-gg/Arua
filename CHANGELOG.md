# Arua changelog

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
