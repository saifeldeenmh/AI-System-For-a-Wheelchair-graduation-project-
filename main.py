import sys
import time
import threading
import pygame
import serial
import platform
import os
import config
from utils.voice_engine import speak, listen_text, r, mic
from utils.ai_logic import predict_intent
from utils.controller_logic import predict_controller_intent
from utils.face_control import run_face_control
from utils.data_handler import (
    save_appointment_details,
    display_appointments,
    cancel_appointment,
    parse_time
)
from services.alarm_service import alarm_check_thread

os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'
os.environ['USE_TORCH'] = '0'
os.environ['USE_TF'] = '1'

# ====================================================
# 1. عزل مكتبة الأزرار (GPIO)
# ====================================================
if platform.system() == "Windows":
    HAS_GPIO = False
    print("💻 Running on Windows: GPIO features disabled.")
else:
    HAS_GPIO = True
    os.environ["GPIOZERO_PIN_FACTORY"] = "lgpio"
    from gpiozero import Button

# ====================================================
# 2. تحديد مسار مكتبة التعرف على الوجه
# ====================================================
if platform.system() == "Windows":
    FACE_LIB_PATH = r"C:\Users\CompuMarts\Downloads\Final_graduation_VoiceSystemLAST\face regontion lib"
else:
    FACE_LIB_PATH = "/home/saif/Desktop/Final_graduation_VoiceSystem/face regontion lib"

if FACE_LIB_PATH not in sys.path:
    sys.path.insert(0, FACE_LIB_PATH)

try:
    from face_auth_service import run_face_authentication  # type: ignore
except ModuleNotFoundError as e:
    print(f"⚠️ Error loading face_auth_service: {e}")

    def run_face_authentication(ser=None, max_attempts=3, timeout_per_attempt=30):
        print("💻 Windows: Face auth skipped, auto-authenticated.")
        return True
# ====================================================
# 3. استدعاء باقي ملفات المشروع
# ====================================================


def get_am_pm():
    while True:
        res = listen_text("هل الموعد صباحاً أم مساءً؟")
        if not res:
            speak("لم أسمعك جيداً، هل الموعد صباحاً أم مساءً؟")
            continue
        res_normalized = res.strip().lower()
        if "صباح" in res_normalized:
            return "AM"
        if "مساء" in res_normalized:
            return "PM"


def get_appointment_day():
    while True:
        res = listen_text("هل الموعد يومياً أم في يوم محدد من الأسبوع؟")
        if not res:
            speak("لم أسمعك جيداً، هل الموعد يومياً أم في يوم محدد؟")
            continue

        res_norm = res.strip().lower()
        if "يوميا" in res_norm or "كل يوم" in res_norm:
            return "يومياً"

        days_map = {
            "السبت": "السبت", "الأحد": "الأحد", "الاحد": "الأحد",
            "الإثنين": "الإثنين", "الاثنين": "الإثنين", "التنين": "الإثنين",
            "الثلاثاء": "الثلاثاء", "التلات": "الثلاثاء",
            "الأربعاء": "الأربعاء", "الاربعاء": "الأربعاء", "الاربع": "الأربعاء",
            "الخميس": "الخميس", "الجمعة": "الجمعة", "الجمعه": "الجمعة"
        }

        for word, correct_day in days_map.items():
            if word in res_norm:
                return correct_day

        speak("لم أتعرف على اليوم، قل مثلاً يومياً أو يوم السبت.")


def schedule_appointment_flow():
    appointment_type = listen_text("ما هو نوع الموعد؟")
    if not appointment_type:
        return

    appointment_time = None
    while True:
        time_raw = listen_text("ما هو وقت الموعد؟")
        if not time_raw:
            speak("لم أسمعك جيداً، يرجى قول الوقت.")
            continue

        parsed_res = parse_time(time_raw)
        if parsed_res == "invalid":
            speak("عفواً، هذا الوقت غير صحيح.")
        elif parsed_res == "not_found":
            speak("لم أسمع توقيتاً واضحاً، من فضلك قل الساعة مرة أخرى؟")
        else:
            appointment_time = parsed_res
            break

    am_pm = get_am_pm()
    if not am_pm:
        return

    appointment_day = get_appointment_day()
    if not appointment_day:
        return

    save_appointment_details(
        config.EXCEL_PATH, appointment_type, appointment_time, am_pm, appointment_day)

    time.sleep(1.5)


# =============================================
# 🔴 كلمات تفعيل كل مود
# =============================================
ASSISTANT_KEYWORDS = [
    "المساعد الصوتي", "مساعد صوتي", "المساعد"
]
CONTROLLER_KEYWORDS = [
    "التحكم الصوتي", "التحكم بالصوت", "المتحكم الصوتي"
]
FACE_KEYWORDS = [
    "التحكم بالوجه", "الوجه", "التحكم الوجهي", "التحكم باستخدام الوجه"
]


def detect_mode_switch(text) -> bool:
    """
    لو الكلام فيه كلمة تبديل مود بترجع True وبتعمل التبديل.
    لو مفيش بترجع False عشان الكلام يتعالج عادي.
    """
    text_norm = text.strip()

    if any(kw in text_norm for kw in ASSISTANT_KEYWORDS):
        if config.CURRENT_MODE == "assistant":
            speak("أنت بالفعل في نظام المساعد الصوتي")
        else:
            config.CURRENT_MODE = "assistant"
            speak("تم التبديل إلى نظام المساعد الصوتي")
            print("\n📅 MODE: Assistant")
        return True

    if any(kw in text_norm for kw in CONTROLLER_KEYWORDS):
        if config.CURRENT_MODE == "controller":
            speak("أنت بالفعل في نظام التحكم الصوتي")
        else:
            config.CURRENT_MODE = "controller"
            speak("تم التبديل إلى نظام التحكم الصوتي")
            print("\n🕹️ MODE: Controller")
        return True

    if any(kw in text_norm for kw in FACE_KEYWORDS):
        if config.CURRENT_MODE == "face_control":
            speak("أنت بالفعل في نظام التحكم بالوجه")
        else:
            config.CURRENT_MODE = "face_control"
            speak("تم التبديل إلى نظام التحكم بالوجه")
            print("\n😶 MODE: Face Control")
            threading.Thread(target=run_face_control,
                             args=(ser,), daemon=True).start()
        return True

    return False


if __name__ == "__main__":
    pygame.mixer.init()

    try:
        ser = serial.Serial(config.SERIAL_PORT, config.BAUD_RATE, timeout=1)
        ser.flush()
        print(f"✅ Serial connected on {config.SERIAL_PORT}")
    except Exception as e:
        print(f"⚠️ Serial Error: {e}")
        ser = None

    print("=" * 50)
    print("  Wheelchair Voice Assistant")
    print("  Starting Face Authentication...")
    print("=" * 50)

    authenticated = run_face_authentication(
        ser=ser,
        max_attempts=3,
        timeout_per_attempt=30
    )

    if not authenticated:
        print("[System] Access denied. Shutting down.")
        sys.exit(1)

    # =============================================
    # الزرار فاضل موجود كـ backup بس مش إجباري
    # =============================================
    if HAS_GPIO:
        try:
            btn = Button(config.TOGGLE_PIN, bounce_time=0.2)
            btn.when_pressed = lambda: detect_mode_switch("التحكم الصوتي")
            print(f"✅ Hardware Button initialized on GPIO {config.TOGGLE_PIN}")
        except Exception as e:
            print(f"⚠️ Button Error: {e}")

    with mic as source:
        print("Calibrating microphone...")
        r.adjust_for_ambient_noise(source, duration=1)

    threading.Thread(target=alarm_check_thread, args=(
        config.EXCEL_PATH,), daemon=True).start()

    speak("مرحباً ، النظام الصوتي جاهز")

    while not config.SHUTDOWN_FLAG:
        if config.LISTENING_ACTIVE:
            try:
                # 1. المايك دايما شغال وبيسمع في كل الأوضاع
                user_text = listen_text()
                if not user_text:
                    continue

                # =============================================
                # 🔴 2. تحقق من تبديل المود الأول قبل أي حاجة
                # =============================================
                if detect_mode_switch(user_text):
                    continue

                # 3. لو إنت في وضع الوجه ومقلتش كلمة تبديل، تجاهل باقي التحليل
                # (عشان الكاميرا هي اللي سايقة دلوقتي مش المايك)
                if config.CURRENT_MODE == "face_control":
                    continue

                # =============================================
                # 4. تحليل الأوامر العادية لباقي الأوضاع
                # =============================================
                if config.CURRENT_MODE == "assistant":
                    intent, conf = predict_intent(user_text)
                    print(
                        f"Predicted intent (Assistant): {intent}, confidence: {conf:.2f}")

                    if intent == "Schedule_Appointment":
                        schedule_appointment_flow()
                        time.sleep(1)
                    elif intent == "Query_Appointments":
                        display_appointments()
                        time.sleep(1)
                    elif intent == "Cancel_Appointment":
                        speak("ما هو الموعد الذي تريد إلغاءه؟")
                        u = listen_text()
                        if u:
                            msg = cancel_appointment(u)
                            speak(msg)
                        time.sleep(1)
                    else:
                        pass

                elif config.CURRENT_MODE == "controller":
                    intent, conf = predict_controller_intent(user_text)

                    if conf >= config.CONTROLLER_CONFIDENCE:
                        print(
                            f"✅ ACTION: [{intent}] | Confidence: {conf*100:.1f}%")

                        if ser:
                            serial_message = f"{intent}\n"
                            ser.write(serial_message.encode('utf-8'))
                            print(
                                f"📡 Sent to Serial: {serial_message.strip()}")
                    else:
                        print(
                            f"⚠️ Intent unclear. Confidence ({conf*100:.1f}%) is below threshold.")

            except Exception as e:
                print("خطأ في النظام:", e)
        else:
            time.sleep(0.1)
