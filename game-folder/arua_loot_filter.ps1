# Arua Loot Filter: turns loot_filter.txt (+ loot_filter_profiles.txt) in the ROSE Online folder into
# styles\lf_rules.css in every installed theme that has one (Arua Ice / Dark / Midnight).
# The game reads that file when it starts: restart the game after running this.
# Same rules as the old in-game Save (Options > Loot Filter), plus the saved modes
# (dim others / only filtered / name size) built in, because the UI can no longer read them.
#
#   -GameDir <path>   ROSE Online folder (default: the folder this script is in)
#   -OutFile <file>       write one css file there instead of into the themes (for testing)
#   -NoModes          leave the modes out (exactly what the old in-game Save wrote)
param([string]$GameDir = $PSScriptRoot, [string]$OutFile = '', [switch]$NoModes)

$ErrorActionPreference = 'Stop'
$utf8 = New-Object System.Text.UTF8Encoding($false)
$order = @('yellow', 'blue', 'purple', 'red', 'green', 'rainbow')
$colors = @{
    yellow = 'rgb(255, 226, 84)'; blue = 'rgb(150, 230, 255)'; purple = 'rgb(205, 140, 255)'
    red = 'rgb(255, 96, 96)'; green = 'rgb(120, 235, 120)'; rainbow = 'animated'
}

function Read-Lines([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return @() }
    $text = [System.IO.File]::ReadAllText($path, $utf8)
    return $text -split "`r?`n"
}

function Split-Names([string]$text) {
    $acc = New-Object System.Collections.Generic.List[string]
    foreach ($part in ($text -split ',')) {
        $n = $part.Trim()
        if ($n -ne '') { $acc.Add($n) }
    }
    return , $acc
}

# djb2 over the UTF-8 bytes, same as the Lua LF.hash
function Get-Hash([string]$text) {
    [long]$h = 5381
    foreach ($b in $utf8.GetBytes($text)) { $h = ($h * 33 + $b) % 1000000007 }
    return $h.ToString()
}

function Get-Sig($lists) {
    $parts = foreach ($k in $order) { if ($null -ne $lists[$k]) { $lists[$k] } else { '' } }
    return Get-Hash ($parts -join '|')
}

function Read-Lists([string]$path) {
    $lists = @{ only_filtered = $false; dim_others = $false; name_size = $null }
    foreach ($k in $order) { $lists[$k] = '' }
    foreach ($line in (Read-Lines $path)) {
        if ($line -match '^\s*([A-Za-z_]+)\s*=(.*)$') {
            $key = $Matches[1]; $value = $Matches[2]
            if ($colors.ContainsKey($key)) { $lists[$key] = $value }
            if ($key -eq 'only_filtered') { $lists.only_filtered = $value -match '^\s*1' }
            if ($key -eq 'dim_others') { $lists.dim_others = $value -match '^\s*1' }
            if ($key -eq 'name_size' -and $value -match '(\d)') { $lists.name_size = [int]$Matches[1] }
        }
    }
    return $lists
}

function Read-Profiles([string]$path) {
    $names = New-Object System.Collections.Generic.List[string]
    $by = @{}; $active = $null; $cur = $null
    foreach ($line in (Read-Lines $path)) {
        if ($line -match '^\s*\[(.*?)\]\s*$') {
            $sec = $Matches[1]
            $cur = @{}; foreach ($k in $order) { $cur[$k] = '' }
            if (-not $by.ContainsKey($sec)) { $names.Add($sec) }
            $by[$sec] = $cur
        } elseif ($line -match '^\s*([A-Za-z_]+)\s*=(.*)$') {
            $key = $Matches[1]; $value = $Matches[2]
            if ($key -eq 'active' -and $null -eq $cur) { $active = $value.Trim() }
            elseif ($null -ne $cur -and $colors.ContainsKey($key)) { $cur[$key] = $value }
        }
    }
    return @{ names = $names; by = $by; active = $active }
}

function Add-Block($lines, $lists, [string]$tag) {
    $R = '#dropped-item-labels-root.' + $tag
    $lines.Add('/* set ' + $tag + ' ' + (Get-Sig $lists) + ' */')
    $all = New-Object System.Collections.Generic.List[string]
    $per = @{}
    foreach ($key in $order) {
        $names = New-Object System.Collections.Generic.List[string]
        foreach ($n in (Split-Names $lists[$key])) {
            $n = $n -replace '["\\]', ''
            if ($n -ne '') { $names.Add($n); $all.Add($n) }
        }
        $per[$key] = $names
    }
    $rule = {
        param($names, [string]$pre, [string]$suf, [string]$body)
        if ($names.Count -eq 0) { return }
        $parts = foreach ($n in $names) { $R + $pre + ' .dropped-item[lf-name="' + $n + '"]' + $suf }
        $lines.Add(($parts -join ",`n") + ' { ' + $body + ' }')
    }
    $pulse = 'animation: 1.3s sine-in-out infinite alternate lf-pulse;'
    & $rule $all '' '' 'overflow: visible; font-size: 22dp;'
    & $rule $all '.lf-sz1' '' 'font-size: 18dp;'
    & $rule $all '.lf-sz0' '' 'font-size: 15dp;'
    & $rule $all '' ' .lf-beam-wrap' 'display: block;'
    & $rule $all '' ' .lf-text' 'color: rgb(255, 255, 255);'
    & $rule $all '' ' .lf-beam' $pulse
    & $rule $all '' ' .lf-base' $pulse
    & $rule $all '' ' .lf-core' 'animation: 1.3s sine-in-out infinite alternate lf-pulse-core;'
    & $rule $all '' ' .lf-shine' 'animation: 1.9s linear infinite lf-shine;'
    & $rule $all '.lf-only' '' 'display: inline-block;'
    & $rule $all '.lf-dim' '' 'opacity: 1;'
    foreach ($key in $order) {
        $names = $per[$key]
        if ($key -eq 'rainbow') {
            $rb = 'animation: 1.3s sine-in-out infinite alternate lf-pulse, 3s linear infinite lf-rainbow-beam;'
            & $rule $names '' '' 'font-effect: outline(1dp rgb(36, 24, 60)), glow(2dp rgb(255, 255, 255));'
            & $rule $names '' ' .lf-text' 'animation: 3s linear infinite lf-rainbow-text;'
            & $rule $names '' ' .lf-beam' $rb
            & $rule $names '' ' .lf-base' $rb
        } else {
            $c = $colors[$key]
            & $rule $names '' ' .lf-beam' ('image-color: ' + $c + ';')
            & $rule $names '' ' .lf-base' ('image-color: ' + $c + ';')
            & $rule $names '' '' ('font-effect: outline(1dp ' + $c + '), glow(3dp ' + $c + ');')
        }
    }
    return , $all
}

$listFile = Join-Path $GameDir 'loot_filter.txt'
if (-not (Test-Path -LiteralPath $listFile) -and $OutFile -eq '') {
    $template = @(
        '# Arua loot filter. Type exact item names (as they show on the ground), comma separated.',
        '# Listed drops get a coloured glow, a bigger name and a light beam. Rarest colour wins.',
        '# Save this file, run "Arua Loot Filter.bat", then restart the game.',
        'yellow=',
        'blue=',
        'purple=',
        'red=',
        'green=',
        'rainbow=',
        '# 1 = hide drops that are not listed / 1 = show them at half opacity',
        'only_filtered=0',
        'dim_others=0',
        '# size of listed names: 0 = normal, 1 = bigger, 2 = big',
        'name_size=2')
    try {
        [System.IO.File]::WriteAllText($listFile, ($template -join "`r`n") + "`r`n", $utf8)
        Write-Host "Created $listFile - type your item names in it, save, and run this again."
        Start-Process notepad.exe -ArgumentList ('"' + $listFile + '"')
        exit 0
    } catch { }
}
$lists = Read-Lists $listFile
$prof = Read-Profiles (Join-Path $GameDir 'loot_filter_profiles.txt')

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add('/* generated by the Loot Filter (Options > Loot Filter > Save). Do not edit. */')
$lines.Add('.lf-rules-ok { display: block; }')
$all = Add-Block $lines $lists 'lfp-none'
foreach ($name in $prof.names) { [void](Add-Block $lines $prof.by[$name] ('lfp-' + (Get-Hash $name))) }

if (-not $NoModes -and $all.Count -gt 0) {
    # Saved modes, active from the start (the labels can no longer read loot_filter.txt).
    # Same effect as the classes the in-game switches set; skipped once the UI sets .lf-live.
    $B = '#dropped-item-labels-root.lfp-none:not(.lf-live)'
    $sel = { param([string]$suf) ($all | ForEach-Object { $B + ' .dropped-item[lf-name="' + $_ + '"]' + $suf }) -join ",`n" }
    $lines.Add('/* saved modes: only_filtered=' + [int]$lists.only_filtered + ' dim_others=' + [int]$lists.dim_others + ' name_size=' + $lists.name_size + ' */')
    if ($lists.only_filtered) {
        $lines.Add($B + ' .dropped-item { display: none; }')
        $lines.Add((& $sel '') + ' { display: inline-block; }')
    } elseif ($lists.dim_others) {
        $lines.Add($B + ' .dropped-item { opacity: 0.5; }')
        $lines.Add((& $sel '') + ' { opacity: 1; }')
    }
    if ($lists.name_size -eq 1) { $lines.Add((& $sel '') + ' { font-size: 18dp; }') }
    if ($lists.name_size -eq 0) { $lines.Add((& $sel '') + ' { font-size: 15dp; }') }
}
$css = ($lines -join "`n") + "`n"

if ($OutFile -ne '') {
    [System.IO.File]::WriteAllText($OutFile, $css, $utf8)
    Write-Host "written $OutFile"
    return
}

$themes = Join-Path $GameDir 'data\ui\themes'
$targets = @(Get-ChildItem -LiteralPath $themes -Directory -ErrorAction SilentlyContinue |
    Where-Object { Test-Path -LiteralPath (Join-Path $_.FullName 'styles\lf_rules.css') })
if ($targets.Count -eq 0) { Write-Host 'No Arua theme found in' $themes; exit 1 }

# Program Files usually needs permission: if we cannot write, ask Windows (UAC) and run again elevated.
$canWrite = $true
try {
    foreach ($t in $targets) {
        $fs = [System.IO.File]::Open((Join-Path $t.FullName 'styles\lf_rules.css'), 'Open', 'ReadWrite')
        $fs.Close()
    }
} catch { $canWrite = $false }
if (-not $canWrite) {
    Write-Host 'Asking Windows for permission to write into the game folder...'
    $args2 = '-NoProfile -ExecutionPolicy Bypass -File "' + $PSCommandPath + '" -GameDir "' + $GameDir + '"'
    try {
        Start-Process powershell.exe -Verb RunAs -ArgumentList $args2 -Wait
    } catch {
        Write-Host 'Permission was not given - nothing changed.'
        exit 1
    }
    exit 0
}

# Lua data block for the in-game Loot Filter (Options shows the lists; labels know the active profile).
# Inline Lua in the UI may not contain '<' or '&': escape them (and quotes / backslashes) as \ddd.
function ConvertTo-LuaString([string]$s) {
    $sb = New-Object System.Text.StringBuilder
    [void]$sb.Append("'")
    foreach ($ch in $s.ToCharArray()) {
        switch ($ch) {
            '\' { [void]$sb.Append('\092') }
            "'" { [void]$sb.Append('\039') }
            '<' { [void]$sb.Append('\060') }
            '&' { [void]$sb.Append('\038') }
            default {
                if ([int]$ch -lt 32) { continue }
                if ([int]$ch -gt 127) { foreach ($b in $utf8.GetBytes([string]$ch)) { [void]$sb.Append('\' + $b.ToString('000')) } }
                else { [void]$sb.Append($ch) }
            }
        }
    }
    [void]$sb.Append("'")
    return $sb.ToString()
}
function ConvertTo-LuaLists($l, [string]$extra) {
    $parts = foreach ($k in $order) { $k + ' = ' + (ConvertTo-LuaString $l[$k]) }
    return '{ ' + $extra + ($parts -join ', ') + ' }'
}
$modes = 'only_filtered = ' + $(if ($lists.only_filtered) { 'true' } else { 'false' }) + ', dim_others = ' + $(if ($lists.dim_others) { 'true' } else { 'false' }) + ', '
if ($null -ne $lists.name_size) { $modes += 'name_size = ' + $lists.name_size + ', ' }
$profLua = foreach ($name in $prof.names) { '        ' + (ConvertTo-LuaLists $prof.by[$name] ('name = ' + (ConvertTo-LuaString $name) + ', ')) + ',' }
$activeLua = if ($prof.active -and $prof.by.ContainsKey($prof.active)) { ConvertTo-LuaString $prof.active } else { 'nil' }
$dataLua = @(
    '-- ARUA-LF-DATA-BEGIN (written by "Arua Loot Filter.bat" from loot_filter.txt; do not edit by hand)',
    'local LF_DATA = {',
    ('    lists = ' + (ConvertTo-LuaLists $lists $modes) + ','),
    '    profiles = {') + @($profLua) + @(
    '    },',
    ('    active = ' + $activeLua + ','),
    '}',
    '-- ARUA-LF-DATA-END') -join "`n"
if ($dataLua -match '[<&]') { Write-Host 'internal error: data block contains < or &'; exit 1 }

$names = $all.Count
Write-Host ("Loot filter: {0} item names, {1} profiles" -f $names, $prof.names.Count)
foreach ($t in $targets) {
    $p = Join-Path $t.FullName 'styles\lf_rules.css'
    [System.IO.File]::WriteAllText($p, $css, $utf8)
    $blocks = 0
    foreach ($rel in 'game\dropped_item_labels.html', 'game\options_bgfx.html') {
        $h = Join-Path $t.FullName $rel
        if (-not (Test-Path -LiteralPath $h)) { continue }
        $src = [System.IO.File]::ReadAllText($h, $utf8)
        $rx = New-Object System.Text.RegularExpressions.Regex('-- ARUA-LF-DATA-BEGIN[^\n]*\n.*?-- ARUA-LF-DATA-END', 'Singleline')
        if ($rx.IsMatch($src)) {
            $src = $rx.Replace($src, [System.Text.RegularExpressions.MatchEvaluator] { param($m) $dataLua }, 1)
            [System.IO.File]::WriteAllText($h, $src, $utf8)
            $blocks++
        }
    }
    Write-Host '  updated' $t.Name "(rules + $blocks script blocks)"
}
Write-Host 'Done. Restart the game to see it.'
