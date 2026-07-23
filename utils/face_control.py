import mediapipe as mp
import cv2
import subprocess
import numpy as np
import config
import platform  # ضفنا المكتبة دي عشان نعرف نظام التشغيل

mp_face_mesh = mp.solutions.face_mesh


def run_face_control(ser=None):
    face_mesh = mp_face_mesh.FaceMesh()
    print("[FaceControl] Starting face control mode...")
    current_os = platform.system()
    last_direction = ""

    # ====================================================
    # دالة داخلية لتحليل الوجه (عشان منكررش الكود مرتين)
    # ====================================================
    def process_face(frame, current_last_direction):
        height, width, _ = frame.shape
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(frame_rgb)
        direction = "stop"

        if results.multi_face_landmarks:
            for face_landmarks in results.multi_face_landmarks:
                x_nose = int(face_landmarks.landmark[5].x * width)
                y_nose = int(face_landmarks.landmark[5].y * height)
                x_left_eye = int(face_landmarks.landmark[33].x * width)
                y_left_eye = int(face_landmarks.landmark[33].y * height)
                x_right_eye = int(face_landmarks.landmark[263].x * width)
                y_right_eye = int(face_landmarks.landmark[263].y * height)

                left_nose = abs(x_nose - x_left_eye)
                right_nose = abs(x_nose - x_right_eye)

                eye_center_y = (y_left_eye + y_right_eye) / 2
                vertical_diff = y_nose - eye_center_y
                horizontal_diff = abs(left_nose - right_nose)

                if horizontal_diff < 20 and abs(vertical_diff - 40) < 15:
                    direction = "stop"
                elif horizontal_diff >= 20:
                    if left_nose > right_nose:
                        direction = "left"
                    else:
                        direction = "right"
                elif vertical_diff < 25:
                    direction = "up"
                elif vertical_diff > 55:
                    direction = "down"

        if direction != current_last_direction:
            print(f"[FaceControl] Direction: {direction}")
            if ser:
                ser.write(f"{direction}\n".encode('utf-8'))
                print(f"📡 Sent to Serial: {direction}")

        return direction

    # ====================================================
    # تشغيل الكاميرا حسب نظام التشغيل
    # ====================================================
    try:
        if current_os == "Windows":
            print("[Windows] Opening camera for Face Control...")
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                print("[Windows] Error: Could not open camera.")
                return

            while config.CURRENT_MODE == "face_control":
                ret, frame = cap.read()
                if not ret:
                    continue

                # تحليل الفريم وتحديث الاتجاه
                last_direction = process_face(frame, last_direction)

                # عرض الشاشة عشان تتاكد إن الكاميرا شايفاك في فترة التجربة
                cv2.imshow("Face Control Mode - Testing", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        elif current_os == "Linux":
            print("[Raspberry Pi] Opening camera via subprocess...")
            cmd = [
                'rpicam-vid', '-t', '0',
                '--width', '640', '--height', '480',
                '--framerate', '10',
                '--codec', 'mjpeg',
                '-o', '-', '-n'
            ]
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            buffer = b""

            while config.CURRENT_MODE == "face_control":
                buffer += process.stdout.read(4096)
                start = buffer.find(b'\xff\xd8')
                end = buffer.find(b'\xff\xd9')

                if start == -1 or end == -1:
                    continue

                jpg_data = buffer[start:end+2]
                buffer = buffer[end+2:]

                frame = cv2.imdecode(np.frombuffer(
                    jpg_data, dtype=np.uint8), cv2.IMREAD_COLOR)
                if frame is None:
                    continue

                # تحليل الفريم وتحديث الاتجاه
                last_direction = process_face(frame, last_direction)

    finally:
        if current_os == "Windows" and 'cap' in locals():
            cap.release()
            cv2.destroyAllWindows()
        elif current_os == "Linux" and 'process' in locals():
            process.terminate()

        face_mesh.close()
        print("[FaceControl] Face control stopped.")
