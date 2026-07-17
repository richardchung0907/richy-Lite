param (
    [string]$AppId = $env:ADMOB_ANDROID_APP_ID,
    [string]$InterstitialId = $env:ADMOB_ANDROID_UNIT_ID,
    [string]$BannerId = $env:ADMOB_ANDROID_BANNER_UNIT_ID
)

if ([string]::IsNullOrWhiteSpace($AppId)) {
    $AppId = Read-Host "Enter AdMob App ID (leave blank for test ID)"
    if ([string]::IsNullOrWhiteSpace($AppId)) {
        $AppId = "ca-app-pub-3940256099942544~3347511713"
    }
}

if ([string]::IsNullOrWhiteSpace($InterstitialId)) {
    $InterstitialId = Read-Host "Enter Interstitial Unit ID (leave blank for test ID)"
    if ([string]::IsNullOrWhiteSpace($InterstitialId)) {
        $InterstitialId = "ca-app-pub-3940256099942544/1033173712"
    }
}

if ([string]::IsNullOrWhiteSpace($BannerId)) {
    $BannerId = Read-Host "Enter Banner Unit ID (leave blank for test ID)"
    if ([string]::IsNullOrWhiteSpace($BannerId)) {
        $BannerId = "ca-app-pub-3940256099942544/6300978111"
    }
}

$env:ADMOB_ANDROID_APP_ID = $AppId

Write-Host "Building Android App Bundle..."
Write-Host "App ID: $AppId"
Write-Host "Interstitial ID: $InterstitialId"
Write-Host "Banner ID: $BannerId"

flutter build appbundle --release `
  --dart-define=ADMOB_ANDROID_UNIT_ID=$InterstitialId `
  --dart-define=ADMOB_ANDROID_BANNER_UNIT_ID=$BannerId
