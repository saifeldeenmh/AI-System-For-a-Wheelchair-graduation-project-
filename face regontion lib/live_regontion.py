import platform
import face_recognition
import cv2
import pickle
import os
import time
import subprocess
import platform

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACE_PKL_PATH = os.path.join(BASE_DIR, "my_face.pkl")
TEMP_IMAGE = "/tmp/face_frame.jpg"


def capture_frame():
    current_os = platform.system()

    if current_os == "Windows":
        print("[Windows] Opening camera...")
        cap = cv2.VideoCapture(0)

        if not cap.isOpened():
            print("[Windows] Error: Could not open camera.")
            return None

        # تسخين الكاميرا عشان اللقطة متطلعش سودة
        time.sleep(2)

        ret, frame = cap.read()
        cap.release()

        if ret:
            print("[Windows] Frame captured successfully!")
            # عرض الصورة اللي اتلقطت لمدة ثانية عشان تتأكد منها
            cv2.imshow("Captured Face - Testing", frame)
            cv2.waitKey(1500)  # هيعرضها ثانية ونص ويقفل أوتوماتيك
            cv2.destroyAllWindows()
            return frame
        else:
            print("[Windows] Error: Could not read frame.")
            return None

    # =====================================================
    # 2. حالة التشغيل على الراسبيري باي (اللينكس)
    # =====================================================
    elif current_os == "Linux":
        try:
            # ده كود الراسبيري باي، بيلقط الصورة ويحفظها في ملف
            result = subprocess.run(
                ["libcamera-jpeg", "-o", "temp_frame.jpg", "-t", "1", "-n"],
                capture_output=True,
                text=True
            )

            # بنقرا الصورة اللي اتلقطت عشان السيستم يحللها
            frame = cv2.imread("temp_frame.jpg")
            return frame

        except Exception as e:
            print(f"[Raspberry Pi] Error capturing frame: {e}")
            return None


def verify_owner(ser=None, tolerance=0.5, timeout_seconds=30) -> bool:
    if not os.path.exists(FACE_PKL_PATH):
        print("[FaceAuth] ERROR: my_face.pkl not found!")
        return False

    with open(FACE_PKL_PATH, "rb") as f:
        my_encoding = pickle.load(f)

    start_time = time.time()
    authenticated = False

    print("[FaceAuth] Starting face verification... Look at the camera.")

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout_seconds:
            print("[FaceAuth] Timeout! No owner detected.")
            break

        frame = capture_frame()
        if frame is None:
            print("[FaceAuth] Could not capture frame, retrying...")
            time.sleep(1)
            continue

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, locations)

        if not encodings:
            print(
                f"[FaceAuth] No face detected, retrying... ({int(timeout_seconds - elapsed)}s left)")
            time.sleep(0.5)
            continue

        for encoding, (top, right, bottom, left) in zip(encodings, locations):
            match = face_recognition.compare_faces(
                [my_encoding], encoding, tolerance=tolerance)
            distance = face_recognition.face_distance(
                [my_encoding], encoding)[0]

            if match[0]:
                print(f"[FaceAuth] ? Owner found! Distance: {distance:.2f}")
                authenticated = True
            else:
                print(f"[FaceAuth] ? Unknown face. Distance: {distance:.2f}")

        if authenticated:
            if ser:
                ser.write(b'o')
                print("[FaceAuth] Serial sent: o")
            break

    return authenticated
