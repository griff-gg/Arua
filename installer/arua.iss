; Arua setup: installs the three Arua themes and the Arua Companion into the ROSE Online folder.
; Build with installer\build_installer.ps1 (it rebuilds the Companion first).

#define AppVer Trim(FileRead(FileOpen(AddBackslash(SourcePath) + "..\VERSION")))
; Test builds only: ISCC /DPriv=lowest installs without admin into a test folder.
#ifndef Priv
  #define Priv "admin"
#endif

[Setup]
AppId={{6F3B2A71-5C0E-4E3B-9A57-2D8C4F1E0A93}
AppName=Arua
AppVersion={#AppVer}
AppVerName=Arua {#AppVer}
AppPublisher=Griff inc.
VersionInfoCompany=Griff inc.
VersionInfoVersion={#AppVer}
AppPublisherURL=https://github.com/griff-gg/Arua
DefaultDirName={code:DefaultRoseDir}
AppendDefaultDirName=no
DirExistsWarning=no
UsePreviousAppDir=yes
DisableProgramGroupPage=yes
DefaultGroupName=Arua
PrivilegesRequired={#Priv}
OutputDir=Output
OutputBaseFilename=Arua-{#AppVer}-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\companion\ui\arua.ico
WizardImageFile=wizard.bmp
WizardSmallImageFile=wizard_small.bmp
UninstallDisplayName=Arua {#AppVer} (ROSE Online theme)
UninstallDisplayIcon={app}\Arua Companion\Arua Companion.exe

[Messages]
SelectDirLabel3=Pick your ROSE Online folder: the one with trose.exe in it.
SelectDirBrowseLabel=Setup found the folder below. If ROSE Online is somewhere else, click Browse.

[Types]
Name: full; Description: "Arua Companion and all three themes"
Name: custom; Description: "Pick the themes"; Flags: iscustom

[Components]
Name: companion; Description: "Arua Companion (settings, theme install, updates)"; Types: full custom; Flags: fixed
Name: ice; Description: "Arua Ice (light ice blue and gold)"; Types: full
Name: dark; Description: "Arua Dark (navy and gold)"; Types: full
Name: midnight; Description: "Arua Midnight (graphite and silver)"; Types: full

[Tasks]
Name: desktopicon; Description: "Desktop shortcut for the Arua Companion"
Name: removerose; Description: "Remove the old Arua files in data\ui\themes\rose (left by Arua before 3 November 2026; they break the default theme)"; Check: OldRoseFolderExists

[InstallDelete]
; Fresh copy on update (no stale files); a theme left unticked is removed.
Type: filesandordirs; Name: "{app}\data\ui\themes\arua_ice"
Type: filesandordirs; Name: "{app}\data\ui\themes\arua_dark"
Type: filesandordirs; Name: "{app}\data\ui\themes\arua_midnight"
Type: filesandordirs; Name: "{app}\Arua Companion"
Type: filesandordirs; Name: "{app}\data\ui\themes\rose"; Tasks: removerose
; The 0.1.0 helper, replaced by the Companion.
Type: files; Name: "{app}\Arua Loot Filter.bat"
Type: files; Name: "{app}\arua_loot_filter.ps1"

[Files]
Source: "..\themes\arua_ice\*"; DestDir: "{app}\data\ui\themes\arua_ice"; Components: ice; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\themes\arua_dark\*"; DestDir: "{app}\data\ui\themes\arua_dark"; Components: dark; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\themes\arua_midnight\*"; DestDir: "{app}\data\ui\themes\arua_midnight"; Components: midnight; Flags: recursesubdirs createallsubdirs ignoreversion
Source: "..\game-folder\Arua Companion\*"; DestDir: "{app}\Arua Companion"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{group}\Arua Companion"; Filename: "{app}\Arua Companion\Arua Companion.exe"; WorkingDir: "{app}\Arua Companion"
Name: "{group}\Uninstall Arua"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Arua Companion"; Filename: "{app}\Arua Companion\Arua Companion.exe"; WorkingDir: "{app}\Arua Companion"; Tasks: desktopicon

[Run]
Filename: "{app}\Arua Companion\Arua Companion.exe"; Description: "Open the Arua Companion now"; Flags: postinstall nowait skipifsilent runasoriginaluser
; quiet update started from the Companion (/RELAUNCH): open it again when done
Filename: "{app}\Arua Companion\Arua Companion.exe"; Flags: nowait runasoriginaluser; Check: IsRelaunch

[UninstallDelete]
; Files the Companion changed or added inside the Arua folders. Your loot lists, settings and
; arua_companion_backup in the ROSE Online folder are kept.
Type: filesandordirs; Name: "{app}\data\ui\themes\arua_ice"
Type: filesandordirs; Name: "{app}\data\ui\themes\arua_dark"
Type: filesandordirs; Name: "{app}\data\ui\themes\arua_midnight"
Type: filesandordirs; Name: "{app}\Arua Companion"

[Code]
function IsRoseDir(Dir: String): Boolean;
begin
  Result := FileExists(AddBackslash(Dir) + 'trose.exe');
end;

function DefaultRoseDir(Param: String): String;
var
  Candidates: array of String;
  I: Integer;
begin
  SetArrayLength(Candidates, 4);
  Candidates[0] := ExpandConstant('{commonpf64}\ROSE Online');
  Candidates[1] := ExpandConstant('{commonpf32}\ROSE Online');
  Candidates[2] := 'C:\ROSE Online';
  Candidates[3] := 'D:\ROSE Online';
  Result := Candidates[0];
  for I := 0 to GetArrayLength(Candidates) - 1 do
    if IsRoseDir(Candidates[I]) then
    begin
      Result := Candidates[I];
      Exit;
    end;
end;

function OldRoseFolderExists: Boolean;
begin
  Result := DirExists(ExpandConstant('{app}\data\ui\themes\rose'));
end;

function GameIsRunning: Boolean;
var
  Wmi, Procs: Variant;
begin
  Result := False;
  try
    Wmi := CreateOleObject('WbemScripting.SWbemLocator');
    Procs := Wmi.ConnectServer('.', 'root\CIMV2').ExecQuery(
      'SELECT ProcessId FROM Win32_Process WHERE Name = ''trose.exe''');
    Result := Procs.Count > 0;
  except
  end;
end;

function IsRelaunch: Boolean;
begin
  Result := Pos('/RELAUNCH', Uppercase(GetCmdTail)) > 0;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  Themes: String;
begin
  { a theme added later from the Companion stays ticked on an update. Not in silent mode: there
    /COMPONENTS (from the Companion's Update button) decides. }
  if (CurPageID = wpSelectComponents) and not WizardSilent then
  begin
    Themes := AddBackslash(WizardDirValue) + 'data\ui\themes\';
    if DirExists(Themes + 'arua_ice') then WizardSelectComponents('ice');
    if DirExists(Themes + 'arua_dark') then WizardSelectComponents('dark');
    if DirExists(Themes + 'arua_midnight') then WizardSelectComponents('midnight');
  end;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if (CurPageID = wpSelectDir) and not IsRoseDir(WizardDirValue) then
  begin
    MsgBox('There is no trose.exe in this folder.' + #13#10 +
           'Pick the ROSE Online folder (the one with trose.exe).', mbError, MB_OK);
    Result := False;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if GameIsRunning then
    Result := 'ROSE Online is running. Close the game, then click Back and Next to try again.';
end;
