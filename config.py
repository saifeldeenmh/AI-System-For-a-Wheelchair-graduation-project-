import platform
import os
import threading

# ==========================================
# 1. اكتشاف نظام التشغيل وتحديد المسار الأساسي
# ==========================================
OS_TYPE = platform.system()

if OS_TYPE == "Windows":
    # مسارات وإعدادات اللاب توب (Windows)
    BASE_DIR = r"C:\Users\CompuMarts\Downloads\Final_graduation_VoiceSystemLAST"
    SERIAL_PORT = 'COM3' 
else:
    # مسارات وإعدادات الراسبيري باي (Linux)
    BASE_DIR = "/home/saif/Desktop/Final_graduation_VoiceSystem"
    SERIAL_PORT = '/dev/serial0'

# ==========================================
# 2. مسارات الملفات (ديناميكية عشان تشتغل في أي مكان)
# ==========================================
# مسارات المساعد الصوتي والمنبه
MODEL_PATH = os.path.join(BASE_DIR, "bert_model_AR_EG")
EXCEL_PATH = os.path.join(BASE_DIR, "appointment.xlsx")
ALARM_FILE_PATH = os.path.join(
    BASE_DIR, "ticking-and-ringing-of-an-old-spring-alarm-clock-sound-effect-338285.mp3")

# مسارات التحكم الصوتي (BLSTM)
BLSTM_MODEL_PATH = os.path.join(BASE_DIR, "voice_control_blstm_model.keras")
TOKENIZER_PATH = os.path.join(BASE_DIR, "tokenizer.pickle")
LABEL_ENCODER_PATH = os.path.join(BASE_DIR, "label_encoder.pickle")

# ==========================================
# 3. إعدادات المساعد الصوتي والمنبه
# ==========================================
CONFIDENCE_THRESHOLD = 0.99
SIMILARITY_THRESHOLD = 90
ALARM_DURATION = 20
CLASS_NAMES = ['Cancel_Appointment',
               'Query_Appointments', 'Schedule_Appointment']

# ==========================================
# 4. إعدادات التحكم الحركي (الكرسي)
# ==========================================
MAX_LEN = 5
CONTROLLER_CLASSES = ['down', 'left', 'right', 'stop', 'up']
CONTROLLER_CONFIDENCE = 0.98

# ==========================================
# 5. إعدادات النظام العامة والهاردوير
# ==========================================
CURRENT_MODE = "assistant"
TOGGLE_PIN = 17
BAUD_RATE = 9600

LISTENING_ACTIVE = True
SHUTDOWN_FLAG = False
playsound_stop_flag = threading.Event()
