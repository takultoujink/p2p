# Firebase Cloud Functions - Quick Deployment Script (Windows PowerShell)
# This script helps you deploy the Google Sheets integration functions

Write-Host "🚀 Firebase Cloud Functions - Google Sheets Integration Deployment" -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Green
Write-Host ""

# Check if in functions directory
if (-not (Test-Path "package.json")) {
    Write-Host "❌ Error: package.json not found. Please run this script from the functions directory." -ForegroundColor Red
    exit 1
}

# Step 1: Check dependencies
Write-Host "📦 Step 1: Checking dependencies..." -ForegroundColor Yellow
$packageContent = Get-Content "package.json" -Raw
if (-not ($packageContent -match "firebase-functions")) {
    Write-Host "⚠️  firebase-functions not found in package.json" -ForegroundColor Yellow
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    npm install firebase-functions firebase-admin googleapis
}

# Step 2: Remind user to set Google Sheet ID
Write-Host ""
Write-Host "🔑 Step 2: Google Sheet Configuration" -ForegroundColor Yellow
Write-Host "-----------------------------------" -ForegroundColor Yellow
Write-Host "Please ensure you have:" -ForegroundColor Cyan
Write-Host "1. Created a Google Sheet" -ForegroundColor Cyan
Write-Host "2. Copied the Sheet ID from the URL" -ForegroundColor Cyan
Write-Host "3. Updated the SPREADSHEET_ID in src/index.ts" -ForegroundColor Cyan
Write-Host ""

$confirm = Read-Host "Have you updated the SPREADSHEET_ID? (y/n)"
if ($confirm -ne 'y' -and $confirm -ne 'Y') {
    Write-Host "❌ Please update SPREADSHEET_ID first, then run this script again." -ForegroundColor Red
    exit 1
}

# Step 3: Compile TypeScript
Write-Host ""
Write-Host "🔨 Step 3: Compiling TypeScript..." -ForegroundColor Yellow
npm run build
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Build failed" -ForegroundColor Red
    exit 1
}

# Step 4: Deploy
Write-Host ""
Write-Host "📤 Step 4: Deploying Cloud Functions..." -ForegroundColor Yellow
firebase deploy --only functions

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✅ Deployment successful!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Next steps:" -ForegroundColor Green
    Write-Host "1. Open your Google Sheet and verify columns are set up" -ForegroundColor Cyan
    Write-Host "2. Add test data to Firestore: bottles collection" -ForegroundColor Cyan
    Write-Host "3. Check Google Sheet - data should appear automatically" -ForegroundColor Cyan
    Write-Host "4. Monitor logs: firebase functions:log" -ForegroundColor Cyan
} else {
    Write-Host "❌ Deployment failed. Check error messages above." -ForegroundColor Red
    exit 1
}
