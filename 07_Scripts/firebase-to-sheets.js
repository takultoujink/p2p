// Firebase to Google Sheets Integration
// ไฟล์นี้ใช้สำหรับการเชื่อมต่อ Firebase กับ Google Sheets

(function(window) {
  'use strict';

  // URL ของ Google Apps Script Web App
  const GOOGLE_APPS_SCRIPT_URL = 'https://script.google.com/macros/s/AKfycbxyx6DazKYWcL8nq0HkAS5qoO5CBA0kP6I_0XgLno8/exec';

  // Google Sheet ID (ใส่ ID ของ Google Sheets ที่คุณสร้างไว้)
  // คุณสามารถหา Sheet ID ได้จาก URL ของ Google Sheets
  // ตัวอย่าง: https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
  const DEFAULT_GOOGLE_SHEET_ID = '1qemalIVHWjZ_7uTrlyTZ6I1B9MqoD6gyyv9_E5fiOmQ'; // Google Sheet ID ของ P2P User Data

  // ฟังก์ชันสำหรับส่งข้อมูลจาก Firebase ไปยัง Google Sheets
  async function sendDataToGoogleSheets(data, sheetId, sheetName = 'Sheet1', range = 'A1') {
  try {
    // ตรวจสอบว่ามีข้อมูลที่จะส่งหรือไม่
    if (!data || Object.keys(data).length === 0) {
      console.error('ไม่มีข้อมูลที่จะส่งไปยัง Google Sheets');
      return { success: false, error: 'ไม่มีข้อมูลที่จะส่ง' };
    }

    // ตรวจสอบว่ามี Sheet ID หรือไม่
    if (!sheetId) {
      console.error('ไม่ได้ระบุ Google Sheet ID');
      return { success: false, error: 'ไม่ได้ระบุ Google Sheet ID' };
    }

    // แปลงข้อมูลเป็นรูปแบบที่ Google Sheets API ต้องการ
    const formattedData = formatDataForSheets(data);

    // URL สำหรับเรียกใช้ Google Apps Script Web App
    const scriptUrl = GOOGLE_APPS_SCRIPT_URL;
    
    // ตรวจสอบว่าได้ตั้งค่า URL แล้วหรือไม่
    if (!scriptUrl || scriptUrl.includes('YOUR_GOOGLE_APPS_SCRIPT_WEB_APP_URL')) {
      console.warn('กรุณาตั้งค่า Google Apps Script URL ใน firebase-to-sheets.js');
      return { success: false, error: 'ยังไม่ได้ตั้งค่า Google Apps Script URL' };
    }

    // ส่งข้อมูลไปยัง Google Apps Script Web App
    const response = await fetch(scriptUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        sheetId: sheetId,
        sheetName: sheetName,
        range: range,
        data: formattedData
      })
    });

    const result = await response.json();
    
    if (result.success) {
      console.log('ส่งข้อมูลไปยัง Google Sheets สำเร็จ');
      return { success: true, result };
    } else {
      console.error('เกิดข้อผิดพลาดในการส่งข้อมูล:', result.error);
      return { success: false, error: result.error };
    }
  } catch (error) {
    console.error('เกิดข้อผิดพลาดในการส่งข้อมูลไปยัง Google Sheets:', error);
    return { success: false, error: error.message };
  }
}

// ฟังก์ชันสำหรับแปลงข้อมูลให้อยู่ในรูปแบบที่ Google Sheets ต้องการ
function formatDataForSheets(data) {
  // ถ้าข้อมูลเป็น Array อยู่แล้ว ให้ใช้ได้เลย
  if (Array.isArray(data)) {
    return data;
  }
  
  // ถ้าเป็น Object ให้แปลงเป็น Array ของ Arrays
  // โดยแถวแรกเป็นชื่อคอลัมน์ และแถวถัดไปเป็นข้อมูล
  if (typeof data === 'object' && data !== null) {
    // กรณีเป็น Array ของ Objects
    if (Array.isArray(Object.values(data)[0])) {
      const headers = Object.keys(data);
      const rows = [];
      
      // เพิ่ม headers เป็นแถวแรก
      rows.push(headers);
      
      // หาจำนวนแถวสูงสุด
      const maxRows = Math.max(...headers.map(header => data[header].length));
      
      // สร้างแถวข้อมูล
      for (let i = 0; i < maxRows; i++) {
        const row = headers.map(header => {
          return data[header][i] !== undefined ? data[header][i] : '';
        });
        rows.push(row);
      }
      
      return rows;
    }
    
    // กรณีเป็น Object ธรรมดา
    const headers = Object.keys(data);
    const values = Object.values(data);
    return [headers, values];
  }
  
  // กรณีอื่นๆ ให้ส่งเป็น Array เดียว
  return [[data]];
}

// ฟังก์ชันสำหรับดึงข้อมูลจาก Firebase และส่งไปยัง Google Sheets
  async function syncFirebaseToSheets(database, path, sheetId, sheetName = 'Sheet1', range = 'A1') {
  try {
    // ดึงข้อมูลจาก Firebase
    const snapshot = await database.ref(path).once('value');
    const data = snapshot.val();
    
    // ส่งข้อมูลไปยัง Google Sheets
    return await sendDataToGoogleSheets(data, sheetId, sheetName, range);
  } catch (error) {
    console.error('เกิดข้อผิดพลาดในการซิงค์ข้อมูล:', error);
    return { success: false, error: error.message };
  }
}

// ฟังก์ชันสำหรับตั้งค่าการซิงค์อัตโนมัติ
  function setupAutoSync(database, path, sheetId, sheetName = 'Sheet1', range = 'A1', intervalMinutes = 60) {
  // ซิงค์ข้อมูลครั้งแรก
  syncFirebaseToSheets(database, path, sheetId, sheetName, range);
  
  // ตั้งเวลาซิงค์ข้อมูลอัตโนมัติ
  const intervalMs = intervalMinutes * 60 * 1000;
  const intervalId = setInterval(() => {
    syncFirebaseToSheets(database, path, sheetId, sheetName, range);
  }, intervalMs);
  
  // ส่งคืน intervalId เพื่อให้สามารถยกเลิกการซิงค์ได้ในภายหลัง
  return intervalId;
}

// ฟังก์ชันสำหรับยกเลิกการซิงค์อัตโนมัติ
  function stopAutoSync(intervalId) {
  if (intervalId) {
    clearInterval(intervalId);
    console.log('ยกเลิกการซิงค์อัตโนมัติแล้ว');
    return true;
  }
  return false;
}

// ฟังก์ชันสำหรับส่งข้อมูลผู้ใช้ใหม่ไป Google Sheets
  async function sendUserRegistrationToSheets(userData, sheetId, sheetName = 'Users') {
  try {
    // เตรียมข้อมูลสำหรับส่งไป Google Sheets
    const sheetData = {
      timestamp: new Date().toISOString(),
      action: 'register',
      uid: userData.uid || '',
      displayName: userData.displayName || '',
      email: userData.email || '',
      studentId: userData.studentId || '',
      teamColor: userData.teamColor || '',
      provider: userData.provider || 'email',
      createdAt: userData.createdAt || new Date().toISOString()
    };

    return await sendDataToGoogleSheets(sheetData, sheetId, sheetName);
  } catch (error) {
    console.error('เกิดข้อผิดพลาดในการส่งข้อมูลการลงทะเบียน:', error);
    return { success: false, error: error.message };
  }
}

// ฟังก์ชันสำหรับส่งข้อมูลการเข้าสู่ระบบไป Google Sheets
  async function sendUserLoginToSheets(userData, sheetId, sheetName = 'LoginLogs') {
  try {
    // เตรียมข้อมูลสำหรับส่งไป Google Sheets
    const sheetData = {
      timestamp: new Date().toISOString(),
      action: 'login',
      uid: userData.uid || '',
      displayName: userData.displayName || '',
      email: userData.email || '',
      provider: userData.provider || 'email',
      loginTime: new Date().toISOString()
    };

    return await sendDataToGoogleSheets(sheetData, sheetId, sheetName);
  } catch (error) {
    console.error('เกิดข้อผิดพลาดในการส่งข้อมูลการเข้าสู่ระบบ:', error);
    return { success: false, error: error.message };
  }
}



// ฟังก์ชันสำหรับส่งข้อมูลการเก็บขวดไป Google Sheets
  async function sendBottleDataToSheets(bottleData, sheetId, sheetName = 'BottleCollection') {
  try {
    // เตรียมข้อมูลสำหรับส่งไป Google Sheets
    const sheetData = {
      timestamp: new Date().toISOString(),
      action: 'bottle_collection',
      uid: bottleData.uid || '',
      displayName: bottleData.displayName || '',
      email: bottleData.email || '',
      bottlesAdded: bottleData.bottlesAdded || 0,
      totalBottles: bottleData.totalBottles || 0,
      todayBottles: bottleData.todayBottles || 0,
      weeklyBottles: bottleData.weeklyBottles || 0,
      points: bottleData.points || 0,
      location: bottleData.location || 'Dashboard',
      deviceType: bottleData.deviceType || 'Web'
    };

    return await sendDataToGoogleSheets(sheetData, sheetId, sheetName);
  } catch (error) {
    console.error('เกิดข้อผิดพลาดในการส่งข้อมูลการเก็บขวด:', error);
    return { success: false, error: error.message };
  }
}

// ฟังก์ชันสำหรับตั้งค่า Google Sheets ID และ URL
  function configureGoogleSheets(scriptUrl, defaultSheetId) {
  // บันทึกการตั้งค่าใน localStorage
  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('googleAppsScriptUrl', scriptUrl);
    localStorage.setItem('defaultGoogleSheetId', defaultSheetId);
  }
  
  // อัปเดต URL ในไฟล์
  window.GOOGLE_APPS_SCRIPT_URL = scriptUrl;
  window.DEFAULT_GOOGLE_SHEET_ID = defaultSheetId;
  
  console.log('ตั้งค่า Google Sheets เรียบร้อยแล้ว');
  return { success: true, scriptUrl, defaultSheetId };
}

// ฟังก์ชันสำหรับดึงการตั้งค่า Google Sheets
  function getGoogleSheetsConfig() {
  let scriptUrl = window.GOOGLE_APPS_SCRIPT_URL;
  let defaultSheetId = window.DEFAULT_GOOGLE_SHEET_ID;
  
  // ถ้าไม่มีใน window ให้ลองดึงจาก localStorage
  if (!scriptUrl && typeof localStorage !== 'undefined') {
    scriptUrl = localStorage.getItem('googleAppsScriptUrl');
    defaultSheetId = localStorage.getItem('defaultGoogleSheetId');
  }
  
  return { scriptUrl, defaultSheetId };
  }

  // Expose functions to window object
  window.FirebaseToSheets = {
    sendDataToGoogleSheets,
    syncFirebaseToSheets,
    setupAutoSync,
    stopAutoSync,
    sendUserRegistrationToSheets,
    sendUserLoginToSheets,
    sendBottleDataToSheets,
    configureGoogleSheets,
    getGoogleSheetsConfig,
    GOOGLE_APPS_SCRIPT_URL,
    DEFAULT_GOOGLE_SHEET_ID
  };

  // For backward compatibility
  window.sendDataToGoogleSheets = sendDataToGoogleSheets;
  window.sendUserRegistrationToSheets = sendUserRegistrationToSheets;
  window.sendUserLoginToSheets = sendUserLoginToSheets;
  window.sendBottleDataToSheets = sendBottleDataToSheets;

})(window);