// Google Apps Script สำหรับรับข้อมูลจาก Firebase และบันทึกลง Google Sheets
// ไฟล์นี้ต้องนำไปสร้างใน Google Apps Script และเผยแพร่เป็น Web App

/**
 * ฟังก์ชันหลักสำหรับรับข้อมูลจาก POST request และบันทึกลง Google Sheets
 * @param {Object} e - Event object ที่มีข้อมูลจาก POST request
 * @return {Object} - ผลลัพธ์การดำเนินการ
 */
function doPost(e) {
  try {
    // ตรวจสอบว่ามีข้อมูลส่งมาหรือไม่
    if (!e.postData || !e.postData.contents) {
      return ContentService
        .createTextOutput(JSON.stringify({
          success: false,
          error: 'ไม่มีข้อมูลที่ส่งมา'
        }))
        .setMimeType(ContentService.MimeType.JSON)
        .setHeader('Access-Control-Allow-Origin', '*')
        .setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        .setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    }

    // แปลงข้อมูล JSON ที่ส่งมา
    const requestData = JSON.parse(e.postData.contents);
    const { sheetId, sheetName = 'Sheet1', data, action = 'append' } = requestData;

    // ตรวจสอบข้อมูลที่จำเป็น
    if (!sheetId || !data) {
      return ContentService
        .createTextOutput(JSON.stringify({
          success: false,
          error: 'ไม่ได้ระบุ sheetId หรือ data'
        }))
        .setMimeType(ContentService.MimeType.JSON)
        .setHeader('Access-Control-Allow-Origin', '*')
        .setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        .setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    }

    // เปิด Google Sheets
    const spreadsheet = SpreadsheetApp.openById(sheetId);
    let sheet = spreadsheet.getSheetByName(sheetName);
    
    // ถ้าไม่มี sheet ให้สร้างใหม่
    if (!sheet) {
      sheet = spreadsheet.insertSheet(sheetName);
    }

    // บันทึกข้อมูลตาม action ที่ระบุ
    let result;
    if (action === 'append') {
      // ถ้าเป็น BottleCollection sheet ให้ใช้ฟังก์ชันเฉพาะ
      if (sheetName === 'BottleCollection') {
        result = handleBottleCollectionData(sheet, data);
      } else {
        result = appendDataToSheet(sheet, data);
      }
    } else if (action === 'update') {
      result = updateSheetData(sheet, data, requestData.range);
    } else {
      // ถ้าเป็น BottleCollection sheet ให้ใช้ฟังก์ชันเฉพาะ
      if (sheetName === 'BottleCollection') {
        result = handleBottleCollectionData(sheet, data);
      } else {
        result = appendDataToSheet(sheet, data); // default เป็น append
      }
    }

    return ContentService
      .createTextOutput(JSON.stringify({
        success: true,
        message: 'บันทึกข้อมูลสำเร็จ',
        result: result
      }))
      .setMimeType(ContentService.MimeType.JSON)
      .setHeader('Access-Control-Allow-Origin', '*')
      .setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
      .setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  } catch (error) {
    console.error('เกิดข้อผิดพลาด:', error);
    return ContentService
      .createTextOutput(JSON.stringify({
        success: false,
        error: error.toString()
      }))
      .setMimeType(ContentService.MimeType.JSON)
      .setHeader('Access-Control-Allow-Origin', '*')
      .setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
      .setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
  }
}

/**
 * ฟังก์ชันสำหรับเพิ่มข้อมูลใหม่ลงใน sheet
 * @param {Sheet} sheet - Google Sheets object
 * @param {Array|Object} data - ข้อมูลที่จะเพิ่ม
 * @return {Object} - ผลลัพธ์การดำเนินการ
 */
function appendDataToSheet(sheet, data) {
  try {
    // ตรวจสอบว่า sheet มี header หรือไม่
    const lastRow = sheet.getLastRow();
    
    // ถ้าเป็นข้อมูลผู้ใช้ (Object)
    if (typeof data === 'object' && !Array.isArray(data)) {
      // ถ้ายังไม่มี header ให้เพิ่ม header ก่อน
      if (lastRow === 0) {
        const headers = Object.keys(data);
        sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      }
      
      // เพิ่มข้อมูลใหม่
      const values = Object.values(data);
      const newRow = lastRow + 1;
      sheet.getRange(newRow, 1, 1, values.length).setValues([values]);
      
      return {
        rowsAdded: 1,
        lastRow: newRow,
        data: values
      };
    }
    
    // ถ้าเป็น Array ของข้อมูล
    if (Array.isArray(data)) {
      const numRows = data.length;
      const numCols = Math.max(...data.map(row => Array.isArray(row) ? row.length : 1));
      
      const newRow = lastRow + 1;
      sheet.getRange(newRow, 1, numRows, numCols).setValues(data);
      
      return {
        rowsAdded: numRows,
        lastRow: newRow + numRows - 1,
        data: data
      };
    }
    
    // ถ้าเป็นข้อมูลแบบอื่นๆ
    const newRow = lastRow + 1;
    sheet.getRange(newRow, 1).setValue(data);
    
    return {
      rowsAdded: 1,
      lastRow: newRow,
      data: [data]
    };
    
  } catch (error) {
    throw new Error('เกิดข้อผิดพลาดในการเพิ่มข้อมูล: ' + error.toString());
  }
}

/**
 * ฟังก์ชันสำหรับอัปเดตข้อมูลใน sheet
 * @param {Sheet} sheet - Google Sheets object
 * @param {Array} data - ข้อมูลที่จะอัปเดต
 * @param {string} range - ช่วงที่จะอัปเดต (เช่น 'A1:C10')
 * @return {Object} - ผลลัพธ์การดำเนินการ
 */
function updateSheetData(sheet, data, range = 'A1') {
  try {
    if (!Array.isArray(data)) {
      throw new Error('ข้อมูลสำหรับการอัปเดตต้องเป็น Array');
    }
    
    const numRows = data.length;
    const numCols = Math.max(...data.map(row => Array.isArray(row) ? row.length : 1));
    
    // ถ้าไม่ได้ระบุ range ให้ใช้ A1 เป็นจุดเริ่มต้น
    const targetRange = sheet.getRange(range).resize(numRows, numCols);
    targetRange.setValues(data);
    
    return {
      rowsUpdated: numRows,
      colsUpdated: numCols,
      range: range,
      data: data
    };
    
  } catch (error) {
    throw new Error('เกิดข้อผิดพลาดในการอัปเดตข้อมูล: ' + error.toString());
  }
}

/**
 * ฟังก์ชันเฉพาะสำหรับจัดการข้อมูลการเก็บขวด
 * @param {Sheet} sheet - Google Sheets object
 * @param {Object} bottleData - ข้อมูลการเก็บขวด
 * @return {Object} - ผลลัพธ์การดำเนินการ
 */
function handleBottleCollectionData(sheet, bottleData) {
  try {
    // ตรวจสอบว่า sheet มี header หรือไม่
    const lastRow = sheet.getLastRow();
    
    // ถ้ายังไม่มี header ให้เพิ่ม header สำหรับ BottleCollection
    if (lastRow === 0) {
      const headers = [
        'Timestamp',
        'Action',
        'User ID',
        'Display Name',
        'Email',
        'Bottles Added',
        'Total Bottles',
        'Today Bottles',
        'Weekly Bottles',
        'Points',
        'Location',
        'Device Type'
      ];
      sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
      
      // จัดรูปแบบ header
      const headerRange = sheet.getRange(1, 1, 1, headers.length);
      headerRange.setFontWeight('bold');
      headerRange.setBackground('#4285f4');
      headerRange.setFontColor('white');
    }
    
    // เตรียมข้อมูลสำหรับเพิ่มลง sheet
    const rowData = [
      bottleData.timestamp || new Date().toISOString(),
      bottleData.action || 'bottle_collection',
      bottleData.uid || '',
      bottleData.displayName || '',
      bottleData.email || '',
      bottleData.bottlesAdded || 0,
      bottleData.totalBottles || 0,
      bottleData.todayBottles || 0,
      bottleData.weeklyBottles || 0,
      bottleData.points || 0,
      bottleData.location || 'Dashboard',
      bottleData.deviceType || 'Web'
    ];
    
    // เพิ่มข้อมูลใหม่
    const newRow = lastRow + 1;
    sheet.getRange(newRow, 1, 1, rowData.length).setValues([rowData]);
    
    return {
      success: true,
      rowsAdded: 1,
      lastRow: newRow,
      data: rowData
    };
    
  } catch (error) {
    throw new Error('เกิดข้อผิดพลาดในการจัดการข้อมูลการเก็บขวด: ' + error.toString());
  }
}

/**
 * ฟังก์ชันสำหรับทดสอบการทำงาน (สามารถเรียกใช้ใน Apps Script Editor)
 */
function testFunction() {
  // ข้อมูลทดสอบ
  const testData = {
    sheetId: '1qemalIVHWjZ_7uTrlyTZ6I1B9MqoD6gyyv9_E5fiOmQ', // ใส่ Sheet ID จริงที่นี่
    sheetName: 'TestSheet',
    data: {
      timestamp: new Date().toISOString(),
      name: 'ทดสอบ',
      email: 'test@example.com',
      action: 'register'
    },
    action: 'append'
  };
  
  // จำลอง POST request
  const mockEvent = {
    postData: {
      contents: JSON.stringify(testData)
    }
  };
  
  // เรียกใช้ฟังก์ชัน doPost
  const result = doPost(mockEvent);
  console.log('ผลลัพธ์การทดสอบ:', result.getContent());
}

/**
 * ฟังก์ชันสำหรับรับ GET request (สำหรับทดสอบ)
 */
function doGet(e) {
  return ContentService
    .createTextOutput(JSON.stringify({
      message: 'Google Apps Script สำหรับ Firebase to Sheets ทำงานปกติ',
      timestamp: new Date().toISOString(),
      status: 'active'
    }))
    .setMimeType(ContentService.MimeType.JSON)
    .setHeader('Access-Control-Allow-Origin', '*')
    .setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    .setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');
}

/**
 * ฟังก์ชันสำหรับจัดการ OPTIONS request (CORS preflight)
 */
function doOptions(e) {
  return ContentService
    .createTextOutput('')
    .setMimeType(ContentService.MimeType.TEXT)
    .setHeader('Access-Control-Allow-Origin', '*')
    .setHeader('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    .setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    .setHeader('Access-Control-Max-Age', '86400');
}