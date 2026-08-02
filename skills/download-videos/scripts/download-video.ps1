param(
    [Parameter(Mandatory)]
    [string]$Url,
    [string]$OutputDirectory = 'D:\VideoDownloads',
    [switch]$DryRun,
    [switch]$BilibiliSubtitlesOnly
)

$ErrorActionPreference = 'Stop'

$ytDlp = 'D:\CodexVideoLearning\bin\yt-dlp.exe'
$bbDown = 'D:\Tools\CodexVideoDownloader\bin\BBDown.exe'
$cookieFile = 'D:\Tools\CodexVideoDownloader\secrets\cookies.txt'

foreach ($toolPath in @($ytDlp, $bbDown)) {
    if (-not (Test-Path -LiteralPath $toolPath)) {
        throw "Required downloader is missing: $toolPath"
    }
}

if (-not (Test-Path -LiteralPath $cookieFile)) {
    throw "Required cookie file is missing: $cookieFile"
}

$uri = [Uri]$Url
if ($uri.Scheme -notin @('http', 'https')) {
    throw 'Only HTTP and HTTPS video URLs are supported.'
}

New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

$hostName = $uri.Host.ToLowerInvariant()
$isBilibili = $hostName -eq 'bilibili.com' -or
    $hostName.EndsWith('.bilibili.com') -or
    $hostName -eq 'b23.tv'

if ($isBilibili) {
    $tool = $bbDown
    $bilibiliCookie = @(
        foreach ($line in Get-Content -LiteralPath $cookieFile -Encoding utf8) {
            $candidate = if ($line.StartsWith('#HttpOnly_')) { $line.Substring(10) } else { $line }
            $fields = $candidate -split "`t", 7
            if ($fields.Count -ge 7 -and $fields[0] -like '*bilibili.com') {
                '{0}={1}' -f $fields[5], $fields[6]
            }
        }
    ) -join '; '
    $argList = @($Url, '--work-dir', $OutputDirectory, '--cookie', $bilibiliCookie, '--skip-ai', 'false')
    if ($BilibiliSubtitlesOnly) {
        $argList += '--sub-only'
    }
}
else {
    $tool = $ytDlp
    $argList = @('--cookies', $cookieFile, '--js-runtimes', 'node', '--remote-components', 'ejs:github', '--write-subs', '--write-auto-subs', '--sub-langs', 'zh-Hans,zh-Hant,zh-CN,zh-TW,zh', '--no-playlist', '--merge-output-format', 'mp4', '-P', $OutputDirectory, $Url)
}

if ($DryRun) {
    $redactNext = $false
    $displayArgs = foreach ($arg in $argList) {
        if ($redactNext) {
            $redactNext = $false
            '<redacted>'
        }
        elseif ($arg -in @('--cookie', '-c')) {
            $redactNext = $true
            $arg
        }
        else {
            $arg
        }
    }
    Write-Output "Tool: $tool"
    Write-Output ('Arguments: ' + ($displayArgs -join ' | '))
    exit 0
}

& $tool @argList
if ($LASTEXITCODE -ne 0) {
    throw "Download failed with exit code $LASTEXITCODE."
}
