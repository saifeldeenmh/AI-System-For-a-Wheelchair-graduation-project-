# utils/voice_engine.py
import os
import pygame
import speech_recognition as sr
from gtts import gTTS
import config  # استيراد الملف بالكامل للوصول للأعلام

r = sr.Recognizer()
mic = sr.Microphone(device_index=1)

# التأكد من عمل الميكسر
if not pygame.mixer.get_init():
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()

def speak(text):
    if not text: return
    try:
        lang = 'en' if all(c in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ .,\'?0123456789 ' for c in text) else 'ar'
        tts = gTTS(text=text, lang=lang)
        filename = "voice_temp.mp3"
        tts.save(filename)
        pygame.mixer.music.load(filename)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        pygame.mixer.music.unload() 
        if os.path.exists(filename): os.remove(filename)
    except Exception as e:
        print(f"[TTS ERROR]: {e}")

def listen_text(prompt=None):
    if prompt:
        speak(prompt)
        print(f"Assistant: {prompt}")

    # القراءة مباشرة من المرجع الرئيسي في config
    while config.LISTENING_ACTIVE and not config.SHUTDOWN_FLAG:
        try:
            with mic as source:
                #print("🎤 Listening...")
                audio = r.listen(source, timeout=3, phrase_time_limit=6)

            #print("⏳ Processing...")
            user_text = r.recognize_google(audio, language="ar-EG")

            if user_text:
                clean_text = user_text.strip()
                print(f"User said: {clean_text}")
                return clean_text

        except Exception:
            # التحقق مرة أخرى لو تم الضغط على S أثناء الاستماع
            if not config.LISTENING_ACTIVE or config.SHUTDOWN_FLAG:
                return ""
            continue
    return ""
