import requests
import json
import serial
import time
from ultralytics import YOLO
import cv2

# ================= Firebase =================
FIREBASE_BASE_URL = "https://takultoujink-default-rtdb.asia-southeast1.firebasedatabase.app/scanner"

def send_barcode_to_firebase(barcode):
    url = f"{FIREBASE_BASE_URL}/{barcode}.json"
    data = {
        "status": "ACTIVE",
        "last_update": int(time.time()),
        "penalty": 0
    }
    requests.put(url, json=data)
    print(f"✅ Firebase confirmed barcode: {barcode}")

def add_penalty(barcode):
    url = f"{FIREBASE_BASE_URL}/{barcode}/penalty.json"
    r = requests.get(url)
    current = r.json() or 0
    requests.put(url, json=current + 1)
    print("⚠️ Non-bottle detected → penalty +1")

# ================= Serial =================
PORT = "COM3"
BAUD = 9600
SEND_DELAY = 1.0
ser = serial.Serial(PORT, BAUD, timeout=1)
time.sleep(2)

# ================= YOLO =================
model = YOLO("yolo11n.pt")
BOTTLE_CLASS_ID = 39
CONF_THRESHOLD = 0.67

# ================= Camera =================
CAM_ID = 0
WIN_NAME = "Bottle Detection"
DEVICE = "cpu"
IMG_SIZE = 640

# ================= State =================
active_barcode = None
last_send_time = 0

print("System ready")
print("Camera running...")
print("Scan barcode anytime...")

# ================= Main Loop =================
for r in model.predict(
    source=CAM_ID,
    stream=True,
    device=DEVICE,
    conf=CONF_THRESHOLD,
    imgsz=IMG_SIZE,
    verbose=False
):

    frame = r.plot()
    detected_classes = []

    if r.boxes is not None:
        detected_classes = r.boxes.cls.tolist()

    current_time = time.time()

    # ---------- Serial to Arduino ----------
    if current_time - last_send_time >= SEND_DELAY:
        if BOTTLE_CLASS_ID in detected_classes:
            ser.write(b"90\n")
        else:
            ser.write(b"0\n")
        last_send_time = current_time

    # ---------- Firebase Logic ----------
    if active_barcode:
        if detected_classes and BOTTLE_CLASS_ID not in detected_classes:
            add_penalty(active_barcode)

    cv2.imshow(WIN_NAME, frame)

    # ---------- Keyboard Input ----------
    key = cv2.waitKey(1) & 0xFF

    # ESC = exit
    if key == 27:
        break

    # B = scan barcode
    if key == ord('b'):
        barcode = input("Scan barcode: ")
        active_barcode = barcode
        send_barcode_to_firebase(barcode)

cv2.destroyAllWindows()
ser.close()         

