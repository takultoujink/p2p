import * as functions from 'firebase-functions';
import * as admin from 'firebase-admin';
import { google } from 'googleapis';

admin.initializeApp(); // Initialize Firebase Admin SDK

// ***************************************************************
// ****  IMPORTANT: Replace with your Google Sheet ID  ****
// ***************************************************************
const SPREADSHEET_ID = 'YOUR_GOOGLE_SHEET_ID_HERE';

/**
 * Cloud Function: Add Firestore Data to Google Sheet
 * Triggers when a new document is created in the specified collection
 * Automatically appends the data to your Google Sheet
 */
export const addFirestoreDataToSheet = functions.firestore
  .document('bottles/{documentId}') // Change 'bottles' to your collection name
  .onCreate(async (snapshot, context) => {
    const newValue = snapshot.data();

    // Prepare data for Google Sheet
    const rowData = [
      newValue?.timestamp ? new Date(newValue.timestamp.toDate()).toLocaleString('th-TH') : '',
      newValue?.count || 0,
      newValue?.points || 0,
      newValue?.status || 'บันทึกแล้ว',
      newValue?.userId || '',
      newValue?.deviceType || '',
      // Add more fields from your Firestore document as needed
    ];

    try {
      // Authenticate with Google API using the default service account
      const auth = new google.auth.GoogleAuth({
        scopes: ['https://www.googleapis.com/auth/spreadsheets'], // Required scope for Google Sheets
      });
      const authClient = await auth.getClient();

      // Create an instance of the Google Sheets API
      const sheets = google.sheets({ version: 'v4', auth: authClient as any });

      // Append the data to your Google Sheet
      await sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: 'BottleCollection!A:F', // Adjust the sheet name and range as per your sheet columns
        valueInputOption: 'USER_ENTERED', // How the input data should be interpreted
        resource: {
          values: [rowData],
        },
      });

      console.log('Successfully appended data to Google Sheet.', {
        documentId: context.params.documentId,
        rowData: rowData,
      });
      return null;
    } catch (error) {
      console.error('Error appending data to Google Sheet:', error);
      // It's good practice to re-throw the error to indicate function failure
      throw new functions.https.HttpsError('internal', 'Failed to append data to Google Sheet', error);
    }
  });

/**
 * Cloud Function: Add User Data to Google Sheet
 * Triggers when a new user document is created
 * Records user registration data
 */
export const addUserDataToSheet = functions.firestore
  .document('users/{userId}')
  .onCreate(async (snapshot, context) => {
    const userData = snapshot.data();

    // Prepare user data for Google Sheet
    const rowData = [
      new Date().toLocaleString('th-TH'),
      userData?.email || '',
      userData?.displayName || '',
      userData?.teamColor || 'ไม่ได้เลือก',
      context.params.userId,
      'ผู้ใช้ใหม่',
    ];

    try {
      const auth = new google.auth.GoogleAuth({
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });
      const authClient = await auth.getClient();

      const sheets = google.sheets({ version: 'v4', auth: authClient as any });

      await sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: 'UserRegistration!A:F',
        valueInputOption: 'USER_ENTERED',
        resource: {
          values: [rowData],
        },
      });

      console.log('Successfully recorded user registration:', context.params.userId);
      return null;
    } catch (error) {
      console.error('Error recording user to Google Sheet:', error);
      throw new functions.https.HttpsError('internal', 'Failed to record user data', error);
    }
  });

/**
 * Cloud Function: Sync Bottle Collection Stats
 * Runs daily to update summary statistics in Google Sheet
 */
export const syncBottleStats = functions.pubsub
  .schedule('every day 23:59')
  .timeZone('Asia/Bangkok')
  .onRun(async (context) => {
    try {
      const db = admin.firestore();
      
      // Get all bottle documents
      const bottlesSnapshot = await db.collectionGroup('bottles').get();
      
      let totalBottles = 0;
      let totalPoints = 0;
      const bottlesByUser: { [key: string]: number } = {};

      bottlesSnapshot.docs.forEach((doc) => {
        const data = doc.data();
        totalBottles += data.count || 0;
        totalPoints += data.points || 0;
        
        if (data.userId) {
          bottlesByUser[data.userId] = (bottlesByUser[data.userId] || 0) + (data.count || 0);
        }
      });

      // Prepare summary data
      const summaryData = [
        new Date().toLocaleString('th-TH'),
        'สรุปรายวัน',
        totalBottles,
        totalPoints,
        Object.keys(bottlesByUser).length,
        Math.round(totalBottles / (Object.keys(bottlesByUser).length || 1)),
      ];

      const auth = new google.auth.GoogleAuth({
        scopes: ['https://www.googleapis.com/auth/spreadsheets'],
      });
      const authClient = await auth.getClient();

      const sheets = google.sheets({ version: 'v4', auth: authClient as any });

      await sheets.spreadsheets.values.append({
        spreadsheetId: SPREADSHEET_ID,
        range: 'DailySummary!A:F',
        valueInputOption: 'USER_ENTERED',
        resource: {
          values: [summaryData],
        },
      });

      console.log('Daily stats synchronized successfully');
      return null;
    } catch (error) {
      console.error('Error syncing bottle stats:', error);
      throw new functions.https.HttpsError('internal', 'Failed to sync stats', error);
    }
  });
