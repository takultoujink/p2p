# Firebase Cloud Functions - Google Sheets Integration Guide

## 📋 Overview

This guide shows you how to integrate Firestore data with Google Sheets using Firebase Cloud Functions. Data from your Firestore database will automatically sync to Google Sheets in real-time.

## 🚀 Setup Steps

### Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Create sheets with these names (or customize in the code):
   - **BottleCollection** - for bottle collection records
   - **UserRegistration** - for user signup data
   - **DailySummary** - for daily statistics

### Step 2: Get Your Google Sheet ID

1. Open your Google Sheet
2. Copy the ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID_HERE/edit
                                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
   ```

### Step 3: Set Up Google Service Account

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your Firebase project
3. Go to **Service Accounts** (under IAM & Admin)
4. Firebase automatically creates a service account for you
5. The service account email looks like: `firebase-adminsdk-xxxxx@projectname.iam.gserviceaccount.com`

### Step 4: Share Your Google Sheet with Service Account

1. In your Google Sheet, click **Share**
2. Paste the service account email
3. Grant **Editor** access
4. Click **Share**

### Step 5: Update the Cloud Function

Replace `YOUR_GOOGLE_SHEET_ID_HERE` in `index.ts` with your actual Google Sheet ID:

```typescript
const SPREADSHEET_ID = '1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7Q8R9S0T'; // Your actual ID
```

### Step 6: Configure Collection Names (Optional)

Update the Firestore collection names if needed:

```typescript
// Current: triggers on 'bottles' collection
.document('bottles/{documentId}')

// If you want to change:
.document('yourCollectionName/{documentId}')
```

### Step 7: Set Up Google Sheets Columns

Set up your Google Sheet columns to match the order in `rowData`:

#### BottleCollection Sheet:
| Column | Header | Example |
|--------|--------|---------|
| A | Timestamp | 2024/12/03 14:30:00 |
| B | Count | 5 |
| C | Points | 5 |
| D | Status | บันทึกแล้ว |
| E | User ID | user123 |
| F | Device Type | mobile |

#### UserRegistration Sheet:
| Column | Header | Example |
|--------|--------|---------|
| A | Registration Date | 2024/12/03 10:00:00 |
| B | Email | user@example.com |
| C | Display Name | John Doe |
| D | Team Color | ทีมแดง |
| E | User ID | user123 |
| F | Status | ผู้ใช้ใหม่ |

#### DailySummary Sheet:
| Column | Header | Example |
|--------|--------|---------|
| A | Date | 2024/12/03 23:59:00 |
| B | Type | สรุปรายวัน |
| C | Total Bottles | 150 |
| D | Total Points | 150 |
| E | Active Users | 5 |
| F | Avg/User | 30 |

### Step 8: Deploy Cloud Functions

```bash
cd functions
npm install
npm run deploy
```

Or deploy specific functions:

```bash
firebase deploy --only functions:addFirestoreDataToSheet
firebase deploy --only functions:addUserDataToSheet
firebase deploy --only functions:syncBottleStats
```

## 🔧 Functions Included

### 1. `addFirestoreDataToSheet`
- **Triggers**: When a new bottle document is created
- **Action**: Appends bottle data to Google Sheet
- **Sheet**: BottleCollection

### 2. `addUserDataToSheet`
- **Triggers**: When a new user document is created
- **Action**: Records user registration data
- **Sheet**: UserRegistration

### 3. `syncBottleStats`
- **Triggers**: Daily at 11:59 PM (Bangkok time)
- **Action**: Syncs daily statistics
- **Sheet**: DailySummary

## 📝 Customization Examples

### Example 1: Add More Fields to Bottle Data

Edit `index.ts`:

```typescript
const rowData = [
  newValue?.timestamp ? new Date(newValue.timestamp.toDate()).toLocaleString('th-TH') : '',
  newValue?.count || 0,
  newValue?.points || 0,
  newValue?.status || 'บันทึกแล้ว',
  newValue?.userId || '',
  newValue?.deviceType || '',
  newValue?.location || '', // Add new field
  newValue?.notes || '', // Add new field
];
```

Update sheet range:
```typescript
range: 'BottleCollection!A:H', // Extended to column H
```

### Example 2: Trigger on Document Update (Not Just Create)

```typescript
export const updateFirestoreDataToSheet = functions.firestore
  .document('bottles/{documentId}')
  .onUpdate(async (change, context) => {
    // ... your code
  });
```

### Example 3: Add Custom Query

```typescript
// Only append bottles with count > 10
await batchAppendFirestoreToSheet(
  SPREADSHEET_ID,
  'BottleCollection!A:F',
  'bottles',
  ['timestamp', 'count', 'points', 'status', 'userId', 'deviceType'],
  (query) => query.where('count', '>', 10)
);
```

## 🛠️ Troubleshooting

### Issue: "Permission denied" Error

**Solution**:
1. Check that the service account email is shared in the Google Sheet
2. Verify the Sheet ID is correct
3. Ensure the service account has Editor access

### Issue: Data Not Appearing in Sheet

**Troubleshooting**:
1. Check Firebase Cloud Functions logs: `firebase functions:log`
2. Verify collection name matches in code
3. Confirm Google Sheet column order matches `rowData` array
4. Check that data exists in Firestore

### Issue: Timestamp Format Wrong

**Solution**: Adjust the locale in `formatTimestamp()`:
```typescript
.toLocaleString('en-US') // English
.toLocaleString('th-TH') // Thai
.toLocaleString('ja-JP') // Japanese
```

## 🔐 Security Best Practices

1. **Never commit credentials** - Service account keys are stored securely in Firebase
2. **Use environment variables** for Sheet ID:
   ```typescript
   const SPREADSHEET_ID = process.env.GOOGLE_SHEET_ID || 'YOUR_SHEET_ID';
   ```
3. **Limit API scopes** - Only request necessary permissions
4. **Monitor usage** - Check Cloud Functions quotas and costs

## 📊 Example Firestore Data Structure

```javascript
// Bottle document
{
  timestamp: Timestamp,
  count: 5,
  points: 5,
  status: "บันทึกแล้ว",
  userId: "user123",
  deviceType: "mobile",
  location: "ห้องเรียน",
  notes: "ขวดพลาสติกใส"
}

// User document
{
  email: "user@example.com",
  displayName: "John Doe",
  teamColor: "ทีมแดง",
  createdAt: Timestamp,
  updatedAt: Timestamp
}
```

## 🚀 Advanced Features

### Using Helper Functions

```typescript
import {
  appendRowToSheet,
  formatTimestamp,
  docToSheetRow,
  batchAppendFirestoreToSheet
} from './sheets-helper';

// Append single row
await appendRowToSheet(
  SPREADSHEET_ID,
  'Sheet1!A:D',
  ['Value1', 'Value2', 'Value3', 'Value4']
);

// Read from sheet
import { getSheetData } from './sheets-helper';
const data = await getSheetData(SPREADSHEET_ID, 'Sheet1!A:D');
console.log('Sheet data:', data);
```

## 📞 Support

For issues or questions:
1. Check Firebase documentation: https://firebase.google.com/docs/functions
2. Check Google Sheets API docs: https://developers.google.com/sheets/api
3. Review Cloud Functions logs in Firebase Console
4. Check error messages in function logs

## ✅ Verification Checklist

- [ ] Google Sheet created and configured
- [ ] Sheet ID copied to `index.ts`
- [ ] Service account shared with Google Sheet
- [ ] Column headers set up in Google Sheet
- [ ] Cloud Functions deployed successfully
- [ ] Test data added to Firestore
- [ ] Verify data appears in Google Sheet
- [ ] Check Cloud Functions logs for errors

---

**Last Updated**: December 2024
**Version**: 1.0
