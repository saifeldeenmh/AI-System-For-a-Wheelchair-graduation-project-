# utils/ai_logic.py
import tensorflow as tf
import numpy as np
# بدل السطر القديم اللي بيضرب إيرور:
# from transformers import BertTokenizerFast, TFAutoModelForSequenceClassification

# استبدله بالسطرين دول:
from transformers import BertTokenizerFast
from transformers.models.bert.modeling_tf_bert import TFBertForSequenceClassification as TFAutoModelForSequenceClassification
# استيراد الإعدادات من ملف الـ config
from config import MODEL_PATH, CLASS_NAMES, CONFIDENCE_THRESHOLD

# 1. تحميل الموديل والـ Tokenizer مرة واحدة عند استدعاء الملف
try:
    intent_model = TFAutoModelForSequenceClassification.from_pretrained(
        MODEL_PATH)
    intent_tokenizer = BertTokenizerFast.from_pretrained(MODEL_PATH)
except Exception as e:
    print(f"❌ Error loading BERT Intent Model: {e}")


def convert_to_bert_format(text_list):
    """تحويل النص لتنسيق يفهمه BERT"""
    return intent_tokenizer(text_list, padding=True, truncation=True, max_length=64, return_tensors="tf")


def predict_intent(text):
    """التنبؤ بنية المستخدم بناءً على النص"""
    inputs = convert_to_bert_format([text])
    outputs = intent_model(inputs)
    logits = outputs.logits
    probabilities = tf.nn.softmax(logits, axis=-1).numpy()[0]

    max_confidence = np.max(probabilities)
    predicted_index = np.argmax(probabilities)

    # التحقق من نسبة التأكد (Confidence)
    if max_confidence >= CONFIDENCE_THRESHOLD:
        return CLASS_NAMES[predicted_index], max_confidence

    return "Unknown", max_confidence
