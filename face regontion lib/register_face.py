import face_recognition
import numpy as np
import pickle
import cv2
import random


def register_face_from_video(video_path, num_frames=30, output_path="my_face.pkl"):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print("ERROR: Can't open video file!")
        return

    # جيب العدد الكلي للفريمات
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Total frames in video: {total_frames}")

    if total_frames < num_frames:
        print(
            f"WARNING: Video has less than {num_frames} frames, using all frames.")
        selected_indices = list(range(total_frames))
    else:
        # اختار 30 فريم عشوائي
        selected_indices = sorted(random.sample(
            range(total_frames), num_frames))

    print(f"Selected {len(selected_indices)} random frames...")

    encodings = []

    for idx in selected_indices:
        # روح للفريم المطلوب
        cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
        ret, frame = cap.read()

        if not ret:
            print(f"  Frame {idx}: Could not read, skipping...")
            continue

        # cv2 بيقرا BGR، face_recognition محتاج RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # face detection الأول عشان نتأكد في وجه
        face_locations = face_recognition.face_locations(
            rgb_frame, model="hog")

        if len(face_locations) == 0:
            print(f"  Frame {idx}: No face detected, skipping...")
            continue

        # استخرج encoding أول وجه في الفريم
        results = face_recognition.face_encodings(
            rgb_frame, known_face_locations=face_locations)

        if results:
            encodings.append(results[0])
            print(f"  Frame {idx}: ✓ Face encoded ({len(encodings)} so far)")

    cap.release()

    if len(encodings) == 0:
        print("\nERROR: No faces found in any frame!")
        return

    # حساب المتوسط لكل الـ encodings
    my_encoding = np.mean(encodings, axis=0)

    with open(output_path, "wb") as f:
        pickle.dump(my_encoding, f)

    print(f"\nSuccess! Registered face from {len(encodings)} frames.")
    print(f"Saved to: {output_path}")


# ---- الاستخدام ----
register_face_from_video(
    video_path= "/home/saif/Desktop/Final_graduation_VoiceSystem/face regontion lib/WhatsApp Video 2026-04-26 at 4.05.25 PM.mp4",
    num_frames=30,
    output_path="/home/saif/Desktop/Final_graduation_VoiceSystem/face regontion lib/my_face.pkl"
)
