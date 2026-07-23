# services/alarm_service.py
import time
import threading
import pygame
# استيراد الثوابت من الـ config
from config import ALARM_FILE_PATH, ALARM_DURATION, playsound_stop_flag, SHUTDOWN_FLAG
# استيراد الدوال اللي هنحتاجها من الـ utils
from utils.voice_engine import speak
from utils.data_handler import get_current_alarms

def play_alarm_thread(file_path):
    """تشغيل المنبه في قناة منفصلة لضمان استقرار ويندوز."""
    try:
        # استخدام Sound لمنع التداخل مع كلام المساعد
        alarm_sound = pygame.mixer.Sound(file_path)
        
        # تشغيل الصوت في حلقة تكرارية
        channel = alarm_sound.play(loops=-1)
        print("--- Sound started playing (Safe Channel) ---")
        
        # الانتظار ومراقبة العلم للإيقاف
        while not playsound_stop_flag.is_set():
            time.sleep(0.2)
            
        # إيقاف الصوت فوراً عند رفع العلم
        channel.stop()
        print("--- Sound stopped cleanly ---")
        
    except Exception as e:
        print(f"Error in alarm thread: {e}")

def alarm_check_thread(excel_path):
    """خيط مراقبة الساعة ومطابقتها مع مواعيد الإكسل."""
    print("Alarm Thread: Monitoring started.")

    # 🔴 قاموس لتحويل أرقام الأيام في بايثون لأسماء عربية
    arabic_days = {
        0: "الإثنين", 1: "الثلاثاء", 2: "الأربعاء", 
        3: "الخميس", 4: "الجمعة", 5: "السبت", 6: "الأحد"
    }

    while not SHUTDOWN_FLAG:
        # جلب المواعيد من الإكسل بتنسيق 24 ساعة
        current_alarms = get_current_alarms(excel_path)
        
        if current_alarms:
            now = time.localtime()
            current_day_name = arabic_days[now.tm_wday] # 🔴 معرفة اليوم الحالي
            
            # 🔴 استلام الـ day من القائمة
            for h, m, name, alarm_day in current_alarms:
                
                # 🔴 شرط جديد: هل المنبه يومياً أو يطابق اليوم الحالي؟
                day_matches = (alarm_day == "يومياً") or (alarm_day == current_day_name)

                # التأكد من مطابقة اليوم والساعة والدقيقة
                if day_matches and now.tm_hour == h and now.tm_min == m and time.time() % 60 < 5:
                    print(f"ALARM TRIGGERED: {h:02d}:{m:02d} - {name} ({alarm_day})")
                    
                    # 1. تنبيه صوتي باسم الموعد
                    speak(f"حان الآن موعدك، وهو {name}")
                    
                    try:
                        playsound_stop_flag.clear()  # إعادة تعيين العلم لبدء الصوت

                        # 2. تشغيل صوت المنبه في خيط منفصل
                        alarm_t = threading.Thread(
                            target=play_alarm_thread, args=(ALARM_FILE_PATH,))
                        alarm_t.start()

                        # 3. الانتظار للمدة المحددة في الـ config
                        time.sleep(ALARM_DURATION)

                        # 4. إيقاف الصوت بشكل نظيف
                        playsound_stop_flag.set()
                        alarm_t.join(timeout=1)
                        print(f"Alarm terminated cleanly.")

                    except Exception as e:
                        print(f"Error during alarm playback: {e}")

                    # تجنب تكرار التنبيه في نفس الدقيقة
                    time.sleep(60 - ALARM_DURATION if ALARM_DURATION < 60 else 1)

        # فحص كل 5 ثوانٍ لتقليل استهلاك المعالج
        time.sleep(5)
        
    print("Alarm Thread: Stopped.")