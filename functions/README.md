# Firebase Cloud Functions - Firestore to Google Sheets Integration

## 📁 Directory Structure

```
functions/
├── src/
│   ├── index.ts              # Main Cloud Functions
│   └── sheets-helper.ts      # Helper utilities for Google Sheets API
├── lib/                      # Compiled JavaScript (auto-generated)
├── package.json             # Dependencies
├── tsconfig.json            # TypeScript configuration
├── GOOGLE_SHEETS_SETUP.md   # Detailed setup guide
├── deploy.sh               # Deployment script (Linux/Mac)
├── deploy.ps1              # Deployment script (Windows)
└── README.md               # This file
```

## 🎯 What This Does

Automatically syncs data from your Firestore database to Google Sheets:

- **Real-time Sync**: New Firestore documents trigger automatic Sheet updates
- **Automatic Timestamps**: Firestore timestamps are formatted automatically
- **Daily Reports**: Optional scheduled function for daily summaries
- **Error Handling**: Graceful error handling and logging
- **Multi-sheet Support**: Send different data to different sheets

## 🚀 Quick Start (5 minutes)

### 1. Install Dependencies
```bash
cd functions
npm install
```

### 2. Set Up Google Sheet
1. Create a Google Sheet at https://sheets.google.com
2. Copy the Sheet ID from the URL
3. Create sheets named: `BottleCollection`, `UserRegistration`, `DailySummary`

### 3. Update Configuration
Edit `src/index.ts` and replace:
```typescript
const SPREADSHEET_ID = 'YOUR_GOOGLE_SHEET_ID_HERE';
```

### 4. Share Sheet with Firebase
1. In your Sheet, click **Share**
2. Add this email: `firebase-adminsdk-xxxxx@your-project-id.iam.gserviceaccount.com`
3. Grant **Editor** access

### 5. Deploy
```bash
# Option 1: Linux/Mac
./deploy.sh

# Option 2: Windows PowerShell
.\deploy.ps1

# Option 3: Manual
npm run build
firebase deploy --only functions
```

## 📝 Available Functions

### 1. `addFirestoreDataToSheet` (onCreate)
- **Trigger**: New document in `bottles` collection
- **Output**: Appends to `BottleCollection` sheet
- **Data**: timestamp, count, points, status, userId, deviceType

### 2. `addUserDataToSheet` (onCreate)
- **Trigger**: New document in `users` collection
- **Output**: Appends to `UserRegistration` sheet
- **Data**: registration date, email, displayName, teamColor, userId, status

### 3. `syncBottleStats` (Scheduled)
- **Trigger**: Daily at 11:59 PM Bangkok time
- **Output**: Appends to `DailySummary` sheet
- **Data**: date, type, totalBottles, totalPoints, activeUsers, avgPerUser

## 🛠️ Using Helper Functions

### Append Single Row
```typescript
import { appendRowToSheet } from './sheets-helper';

await appendRowToSheet(
  SPREADSHEET_ID,
  'Sheet1!A:D',
  ['Value1', 'Value2', 'Value3', 'Value4']
);
```

### Read from Sheet
```typescript
import { getSheetData } from './sheets-helper';

const data = await getSheetData(SPREADSHEET_ID, 'Sheet1!A:D');
console.log('Retrieved data:', data);
```

### Update Range
```typescript
import { updateSheetData } from './sheets-helper';

await updateSheetData(
  SPREADSHEET_ID,
  'Sheet1!A1:D10',
  [['New', 'Data', 'Here', '!'], ...]
);
```

### Format Timestamps
```typescript
import { formatTimestamp } from './sheets-helper';

const formatted = formatTimestamp(firestoreTimestamp, 'th-TH');
// Output: "2024/12/03 14:30:00"
```

## 📊 Sheet Column Setup

### BottleCollection
```
A: Timestamp
B: Count
C: Points
D: Status
E: User ID
F: Device Type
```

### UserRegistration
```
A: Registration Date
B: Email
C: Display Name
D: Team Color
E: User ID
F: Status
```

### DailySummary
```
A: Date
B: Type
C: Total Bottles
D: Total Points
E: Active Users
F: Avg/User
```

## 🔧 Customization

### Change Collection Name
Edit `src/index.ts`:
```typescript
export const addFirestoreDataToSheet = functions.firestore
  .document('YOUR_COLLECTION/{documentId}')  // ← Change here
  .onCreate(async (snapshot, context) => {
```

### Add More Fields
Edit `rowData` array:
```typescript
const rowData = [
  newValue?.field1 || '',
  newValue?.field2 || '',
  newValue?.customField || '',  // ← Add here
];
```

### Change Schedule
Edit the `syncBottleStats` function:
```typescript
functions.pubsub
  .schedule('every day 23:59')  // ← Cron format
  .timeZone('Asia/Bangkok')
```

For cron syntax help, see: https://crontab.guru/

## 📋 Firestore Document Structure

### bottles collection
```javascript
{
  timestamp: Timestamp,        // Auto-generated
  count: 5,                   // Number of bottles
  points: 5,                  // Points earned
  status: "บันทึกแล้ว",        // Status
  userId: "user123",          // Firebase UID
  deviceType: "mobile",       // Device type
  location: "ห้องเรียน",       // Optional location
  notes: "ขวดพลาสติก"         // Optional notes
}
```

### users collection
```javascript
{
  email: "user@example.com",
  displayName: "John Doe",
  teamColor: "ทีมแดง",
  createdAt: Timestamp,
  updatedAt: Timestamp,
  studentId: "ST12345",       // Optional
  status: "active"            // Optional
}
```

## 🐛 Troubleshooting

### ❌ "Permission Denied"
```
Error: The caller does not have permission to access the requested resource
```
**Solution**: 
- Share your Google Sheet with the service account email
- Verify the service account has Editor access
- Wait a few minutes for permissions to propagate

### ❌ "Spreadsheet Not Found"
```
Error: Requested spreadsheetId does not exist
```
**Solution**:
- Check the SPREADSHEET_ID is correct
- Verify you copied the full ID from the URL
- Make sure the sheet hasn't been deleted

### ❌ "Range not found"
```
Error: Requested range is not found in spreadsheet
```
**Solution**:
- Verify sheet names exist (BottleCollection, UserRegistration, etc.)
- Check the range format: `SheetName!A:F`
- Create missing sheets

### ❌ Data Not Appearing
**Troubleshooting**:
1. Check Cloud Functions logs:
   ```bash
   firebase functions:log
   ```
2. Verify Firestore document structure
3. Check Google Sheet permissions
4. Verify column order matches `rowData` array

## 📊 Monitoring

### View Logs
```bash
firebase functions:log

# Or filter by function name
firebase functions:log --only addFirestoreDataToSheet
```

### View Execution Metrics
In Firebase Console → Functions → See memory, duration, errors

### Test Manually
```bash
# Add test data to Firestore
firebase firestore:delete bottles/test-doc  # Clean up after
```

## 🚀 Deployment

### Deploy All Functions
```bash
firebase deploy --only functions
```

### Deploy Specific Function
```bash
firebase deploy --only functions:addFirestoreDataToSheet
```

### Production Deployment
```bash
firebase deploy --only functions --force
```

## ⚙️ Environment Variables

Add to `functions/.env` (not version controlled):
```
GOOGLE_SHEET_ID=1A2B3C4D5E6F7G8H9I0J1K2L3M4N5O6P7
```

Update `src/index.ts`:
```typescript
const SPREADSHEET_ID = process.env.GOOGLE_SHEET_ID || 'YOUR_SHEET_ID';
```

## 📚 Resources

- [Firebase Cloud Functions Docs](https://firebase.google.com/docs/functions)
- [Google Sheets API Docs](https://developers.google.com/sheets/api)
- [Firestore Data Types](https://firebase.google.com/docs/firestore/manage-data/data-types)
- [Cron Syntax Reference](https://crontab.guru/)

## ✅ Verification Checklist

- [ ] `npm install` completed
- [ ] SPREADSHEET_ID updated
- [ ] Google Sheet shared with service account
- [ ] Sheet columns created and named
- [ ] `npm run build` succeeds
- [ ] `firebase deploy --only functions` succeeds
- [ ] Test data added to Firestore
- [ ] Data appears in Google Sheet
- [ ] No errors in `firebase functions:log`

## 💡 Best Practices

1. **Use environment variables** for sensitive data
2. **Test locally** before deploying (if using emulator)
3. **Monitor quotas** - Google Sheets API has rate limits
4. **Set up alerts** for failed functions
5. **Version control** your TypeScript, not compiled JS
6. **Document changes** to field mappings

## 🆘 Getting Help

1. Check [Troubleshooting section](#-troubleshooting) above
2. Review [GOOGLE_SHEETS_SETUP.md](./GOOGLE_SHEETS_SETUP.md) for detailed setup
3. Check Firebase Console Logs
4. Review error messages carefully
5. Verify all prerequisites are met

---

**Last Updated**: December 2024  
**Status**: Production Ready  
**Maintenance**: Active
