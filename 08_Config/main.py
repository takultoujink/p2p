# =========================================================
# YOLO + BARCODE + 2 SERVO + FIRESTORE (GUI + HOTKEY)
# =========================================================

import time
import serial
import cv2
import firebase_admin
from firebase_admin import credentials, firestore
from ultralytics import YOLO

# ===============================
# CONFIG
# ===============================
COM_PORT = "COM3"
BAUD_RATE = 9600

CAM_ID = 0
MODEL_PATH = "yolo11n.pt"

BOTTLE_CLASS_ID = 39          # ขวดน้ำ (COCO)
YOLO_CONFIDENCE = 0.3

SESSION_TIMEOUT = 30
POINT_PER_BOTTLE = 1
DETECT_COOLDOWN = 1.2
STABLE_FRAMES = 2

# ===============================
# FIREBASE
# ===============================
cred = credentials.Certificate(
    r"c:\Users\Asus\Desktop\new app scan\08_Config\serviceAccountKey.json"
)
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

db = firestore.client()
print("✅ Firebase connected")

# ===============================
# ARDUINO
# ===============================
arduino = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
time.sleep(2)
print("✅ Arduino connected")

def send_cmd(cmd):
    arduino.write(f"{cmd}\n".encode())
    time.sleep(0.15)

# ===============================
# CAMERA
# ===============================
cap = None
GUI_ENABLED = True

def cam_on():
    global cap, GUI_ENABLED
    cap = cv2.VideoCapture(CAM_ID, cv2.CAP_DSHOW)
    if not cap.isOpened():
        raise RuntimeError("❌ Cannot open USB camera")

    # 🛡️ ป้องกัน imshow crash
    try:
        cv2.namedWindow("YOLO Detection", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("YOLO Detection", 800, 600)
    except cv2.error:
        GUI_ENABLED = False
        print("⚠️ GUI disabled (opencv-headless detected)")

    print("📷 Camera ON")

def cam_off():
    global cap
    if cap:
        cap.release()
        cap = None
    if GUI_ENABLED:
        cv2.destroyAllWindows()
    print("📷 Camera OFF")

# ===============================
# YOLO
# ===============================
model = YOLO(MODEL_PATH)
print("✅ YOLO ready")

# ===============================
# FIRESTORE
# ===============================
def write_bottle(student_id, confidence):
    db.collection("bottles").add({
        "studentId": student_id,
        "confidence": confidence,
        "timestamp": firestore.SERVER_TIMESTAMP
    })

def add_score(student_id):
    db.collection("users").document(student_id).set({
        "score": firestore.Increment(POINT_PER_BOTTLE),
        "updatedAt": firestore.SERVER_TIMESTAMP
    }, merge=True)

# ===============================
# DETECT (Bottle Only + GUI)
# ===============================
def detect_bottle():
    ret, frame = cap.read()
    if not ret:
        return False, 0.0

    # ✅ แสดงภาพทันที
    if GUI_ENABLED:
        cv2.imshow("YOLO Detection", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            raise KeyboardInterrupt

    bottle_found = False
    confidence = 0.0

    results = model(frame, conf=YOLO_CONFIDENCE, verbose=False)

    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            conf = float(box.conf[0])

            if cls == BOTTLE_CLASS_ID and conf >= YOLO_CONFIDENCE:
                bottle_found = True
                confidence = conf

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0), 2)
                cv2.putText(
                    frame,
                    f"BOTTLE {conf:.2f}",
                    (x1, y1-10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.8,
                    (0,255,0),
                    2
                )
                break

    return bottle_found, confidence

# ===============================
# SESSION
# ===============================
def start_session(student_id):
    print(f"\n🔓 SESSION START: {student_id}")

    send_cmd("INLET_OPEN")
    cam_on()

    last_activity = time.time()
    last_detect = 0
    stable_count = 0
    servo_open = False

    try:
        while True:
            detected, conf = detect_bottle()

            if detected:
                stable_count += 1

                if not servo_open:
                    send_cmd("90")
                    servo_open = True

                if stable_count >= STABLE_FRAMES:
                    if time.time() - last_detect > DETECT_COOLDOWN:
                        send_cmd("SORT_PLASTIC")
                        write_bottle(student_id, conf)
                        add_score(student_id)
                        print(f"✅ +1 คะแนน (conf={conf:.2f})")

                        last_detect = time.time()
                        stable_count = 0

                last_activity = time.time()

            else:
                stable_count = 0
                if servo_open:
                    send_cmd("0")
                    servo_open = False

            if time.time() - last_activity > SESSION_TIMEOUT:
                break

    except KeyboardInterrupt:
        print("🛑 Session interrupted by user")

    send_cmd("INLET_LOCK")
    send_cmd("0")
    cam_off()
    print("🔒 SESSION END")

# ===============================
# BARCODE LOOP
# ===============================
print("📦 Ready for barcode scan...")
print("👉 กด Q ที่หน้ากล้องเพื่อปิดโปรแกรม")

try:
    while True:
        student_id = input().strip()
        if student_id:
            start_session(student_id)

except KeyboardInterrupt:
    print("\n👋 Program stopped")
    cam_off()
    arduino.close()