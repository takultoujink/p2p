/**
 * Google Sheets Integration Helper
 * This file contains utility functions for Google Sheets integration
 */

import * as admin from 'firebase-admin';
import { google } from 'googleapis';

// Initialize Firestore
const db = admin.firestore();

/**
 * Interface for sheet row data
 */
interface SheetRowData {
  [key: string]: any;
}

/**
 * Get Google Sheets API instance
 */
export async function getSheetsAPI() {
  const auth = new google.auth.GoogleAuth({
    scopes: ['https://www.googleapis.com/auth/spreadsheets'],
  });
  const authClient = await auth.getClient();
  return google.sheets({ version: 'v4', auth: authClient as any });
}

/**
 * Append a single row to Google Sheet
 * @param spreadsheetId - Your Google Sheet ID
 * @param range - The range to append to (e.g., 'Sheet1!A:D')
 * @param rowData - Array of values for the row
 */
export async function appendRowToSheet(
  spreadsheetId: string,
  range: string,
  rowData: any[]
): Promise<void> {
  try {
    const sheets = await getSheetsAPI();

    await sheets.spreadsheets.values.append({
      spreadsheetId,
      range,
      valueInputOption: 'USER_ENTERED',
      resource: {
        values: [rowData],
      },
    });

    console.log(`Successfully appended row to ${range}`);
  } catch (error) {
    console.error(`Error appending to ${range}:`, error);
    throw error;
  }
}

/**
 * Append multiple rows to Google Sheet
 * @param spreadsheetId - Your Google Sheet ID
 * @param range - The range to append to
 * @param rowsData - Array of rows, each row is an array of values
 */
export async function appendRowsToSheet(
  spreadsheetId: string,
  range: string,
  rowsData: any[][]
): Promise<void> {
  try {
    const sheets = await getSheetsAPI();

    await sheets.spreadsheets.values.append({
      spreadsheetId,
      range,
      valueInputOption: 'USER_ENTERED',
      resource: {
        values: rowsData,
      },
    });

    console.log(`Successfully appended ${rowsData.length} rows to ${range}`);
  } catch (error) {
    console.error(`Error appending rows to ${range}:`, error);
    throw error;
  }
}

/**
 * Get data from Google Sheet
 * @param spreadsheetId - Your Google Sheet ID
 * @param range - The range to read from
 */
export async function getSheetData(
  spreadsheetId: string,
  range: string
): Promise<any[][]> {
  try {
    const sheets = await getSheetsAPI();

    const response = await sheets.spreadsheets.values.get({
      spreadsheetId,
      range,
    });

    return response.data.values || [];
  } catch (error) {
    console.error(`Error reading from ${range}:`, error);
    throw error;
  }
}

/**
 * Update a range in Google Sheet
 * @param spreadsheetId - Your Google Sheet ID
 * @param range - The range to update
 * @param rowsData - The new data
 */
export async function updateSheetData(
  spreadsheetId: string,
  range: string,
  rowsData: any[][]
): Promise<void> {
  try {
    const sheets = await getSheetsAPI();

    await sheets.spreadsheets.values.update({
      spreadsheetId,
      range,
      valueInputOption: 'USER_ENTERED',
      resource: {
        values: rowsData,
      },
    });

    console.log(`Successfully updated ${range}`);
  } catch (error) {
    console.error(`Error updating ${range}:`, error);
    throw error;
  }
}

/**
 * Clear a range in Google Sheet
 * @param spreadsheetId - Your Google Sheet ID
 * @param range - The range to clear
 */
export async function clearSheetData(
  spreadsheetId: string,
  range: string
): Promise<void> {
  try {
    const sheets = await getSheetsAPI();

    await sheets.spreadsheets.values.clear({
      spreadsheetId,
      range,
    });

    console.log(`Successfully cleared ${range}`);
  } catch (error) {
    console.error(`Error clearing ${range}:`, error);
    throw error;
  }
}

/**
 * Format Firestore timestamp to readable string
 * @param timestamp - Firestore timestamp
 * @param locale - Locale for date formatting (default: 'th-TH')
 */
export function formatTimestamp(
  timestamp: FirebaseFirestore.Timestamp | undefined,
  locale: string = 'th-TH'
): string {
  if (!timestamp) return '';
  try {
    return new Date(timestamp.toDate()).toLocaleString(locale);
  } catch (error) {
    console.warn('Error formatting timestamp:', error);
    return '';
  }
}

/**
 * Convert Firestore document to sheet row
 * @param doc - Firestore document data
 * @param fieldOrder - Array of field names in desired order
 */
export function docToSheetRow(
  doc: FirebaseFirestore.DocumentData | undefined,
  fieldOrder: string[]
): any[] {
  if (!doc) return fieldOrder.map(() => '');
  
  return fieldOrder.map((field) => {
    const value = doc[field];
    
    // Handle different data types
    if (value === undefined || value === null) {
      return '';
    } else if (value.toDate && typeof value.toDate === 'function') {
      // Firestore Timestamp
      return formatTimestamp(value);
    } else if (typeof value === 'object') {
      return JSON.stringify(value);
    } else {
      return value.toString();
    }
  });
}

/**
 * Batch append firestore documents to Google Sheet
 * @param spreadsheetId - Your Google Sheet ID
 * @param range - The range to append to
 * @param collectionPath - Path to Firestore collection
 * @param fieldOrder - Order of fields in sheet
 * @param queryConstraints - Optional query constraints
 */
export async function batchAppendFirestoreToSheet(
  spreadsheetId: string,
  range: string,
  collectionPath: string,
  fieldOrder: string[],
  queryConstraints?: any
): Promise<void> {
  try {
    let query: any = db.collection(collectionPath);

    if (queryConstraints) {
      query = queryConstraints(query);
    }

    const snapshot = await query.get();
    const rowsData: any[][] = [];

    snapshot.forEach((doc) => {
      const row = docToSheetRow(doc.data(), fieldOrder);
      rowsData.push(row);
    });

    if (rowsData.length > 0) {
      await appendRowsToSheet(spreadsheetId, range, rowsData);
    }
  } catch (error) {
    console.error('Error in batch append:', error);
    throw error;
  }
}
