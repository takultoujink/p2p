#!/bin/bash

# Firebase Cloud Functions - Quick Deployment Script
# This script helps you deploy the Google Sheets integration functions

echo "🚀 Firebase Cloud Functions - Google Sheets Integration Deployment"
echo "=================================================================="
echo ""

# Check if in functions directory
if [ ! -f "package.json" ]; then
    echo "❌ Error: package.json not found. Please run this script from the functions directory."
    exit 1
fi

# Step 1: Check dependencies
echo "📦 Step 1: Checking dependencies..."
if ! grep -q "firebase-functions" package.json; then
    echo "⚠️  firebase-functions not found in package.json"
    echo "Installing dependencies..."
    npm install firebase-functions firebase-admin googleapis
fi

# Step 2: Remind user to set Google Sheet ID
echo ""
echo "🔑 Step 2: Google Sheet Configuration"
echo "-----------------------------------"
echo "Please ensure you have:"
echo "1. Created a Google Sheet"
echo "2. Copied the Sheet ID from the URL"
echo "3. Updated the SPREADSHEET_ID in src/index.ts"
echo ""
read -p "Have you updated the SPREADSHEET_ID? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Please update SPREADSHEET_ID first, then run this script again."
    exit 1
fi

# Step 3: Compile TypeScript
echo ""
echo "🔨 Step 3: Compiling TypeScript..."
npm run build || { echo "❌ Build failed"; exit 1; }

# Step 4: Deploy
echo ""
echo "📤 Step 4: Deploying Cloud Functions..."
firebase deploy --only functions

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "📊 Next steps:"
    echo "1. Open your Google Sheet and verify columns are set up"
    echo "2. Add test data to Firestore: bottles collection"
    echo "3. Check Google Sheet - data should appear automatically"
    echo "4. Monitor logs: firebase functions:log"
else
    echo "❌ Deployment failed. Check error messages above."
    exit 1
fi
