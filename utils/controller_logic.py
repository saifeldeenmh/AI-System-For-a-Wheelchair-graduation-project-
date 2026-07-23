# utils/controller_logic.py
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import numpy as np
import pickle
import config

print("⏳ Loading BLSTM Voice Controller Model...")
try:
    # تحميل الموديل
    controller_model = load_model(config.BLSTM_MODEL_PATH)

    # تحميل التوكنايزر
    with open(config.TOKENIZER_PATH, 'rb') as handle:
        controller_tokenizer = pickle.load(handle)

    # تحميل الـ Label Encoder
    with open(config.LABEL_ENCODER_PATH, 'rb') as handle:
        controller_label_encoder = pickle.load(handle)

    print("✅ BLSTM Model & Tools Loaded Successfully!")
except Exception as e:
    print(f"❌ Error loading BLSTM model: {e}")


def predict_controller_intent(text):
    """توقع أمر الحركة بناءً على النص باستخدام BLSTM"""
    try:
        # 1. تحويل النص لأرقام
        seq = controller_tokenizer.texts_to_sequences([text])

        # 2. توحيد الطول (Padding)
        padded = pad_sequences(seq, maxlen=config.MAX_LEN, padding='post')

        # 3. التوقع
        prediction_probs = controller_model.predict(padded, verbose=0)[0]

        # 4. استخراج أعلى نسبة وأعلى كلاس
        confidence = np.max(prediction_probs)
        predicted_class_idx = np.argmax(prediction_probs)

        # 5. تحويل الرقم لاسم الكلاس (مثل 'right', 'up')
        predicted_class = controller_label_encoder.inverse_transform(
            [predicted_class_idx])[0]

        return predicted_class, float(confidence)

    except Exception as e:
        print(f"⚠️ Prediction Error: {e}")
        return "unknown", 0.0
