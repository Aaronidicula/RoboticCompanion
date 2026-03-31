import re
import ollama
import serial
from gtts import gTTS
import pygame
import speech_recognition as sr
from wit import Wit
import os

# ==============================
# CONFIG
# ==============================
MODEL_NAME = "phi3:mini"
MAX_NEW_TOKENS = 64

# Replace with your REAL Wit.ai Client Access Token
WIT_AI_KEY = os.getenv("WIT_AI_KEY")  # ← only the token string

# Change to your ESP32's serial port
# Common on Linux: /dev/ttyUSB0 or /dev/ttyACM0
SERIAL_PORT = "/dev/ttyUSB0"
SERIAL_BAUD = 115200

# ==============================
# INITIALIZATION
# ==============================
print("🤖 Initializing Assistant (Ollama + Phi-3-mini)...")

# Ollama check
try:
    ollama.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': 'hi'}])
    print("✅ Ollama model ready (GPU-accelerated)")
except Exception as e:
    print(f"⚠️ Ollama error: {e}")
    print("Run: ollama serve   and   ollama pull phi3:mini")
    exit(1)

# Serial port for ESP32
ser = None
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
    print(f"✅ Connected to ESP32 on {SERIAL_PORT}")
except Exception as e:
    print(f"⚠️ Serial port {SERIAL_PORT} failed: {e}")
    print("Continuing without ESP32 connection...")

# Wit.ai client
wit_client = Wit(WIT_AI_KEY)

print("-" * 50)

# ==============================
# HELPERS
# ==============================
def format_response(reply: str, emotion: str, gesture: str, source: str) -> dict:
    return {
        "reply": reply.strip(),
        "emotion": emotion,
        "gesture": gesture,
        "source": source
    }

def speak_text(text: str):
    """Speak the text response using gTTS + pygame playback."""
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("response.mp3")
        
        pygame.mixer.init()
        pygame.mixer.music.load("response.mp3")
        pygame.mixer.music.play()
        
        # Wait until playback finishes
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
            
    except Exception as e:
        print(f"⚠️ Audio playback error: {e}")

def get_voice_input() -> str:
    """Capture voice input using microphone + Wit.ai STT."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Listening...")
        r.adjust_for_ambient_noise(source, duration=1)
        audio = r.listen(source, timeout=5, phrase_time_limit=8)

    try:
        text = r.recognize_wit(audio, key=WIT_AI_KEY)
        print(f"You (voice): {text}")
        return text.strip()
    except sr.UnknownValueError:
        print("Could not understand the audio")
        return ""
    except sr.RequestError as e:
        print(f"Wit.ai request error: {e}")
        return ""
    except Exception as e:
        print(f"Voice input error: {e}")
        return input("Voice failed - type your message: ").strip()

def send_to_esp32(word: str):
    """Send one-word command (emotion/gesture) to ESP32 via serial."""
    if ser and ser.is_open:
        try:
            ser.write(f"{word}\n".encode())
            print(f"Sent to ESP32: {word}")
        except Exception as e:
            print(f"Serial send error: {e}")

# ==============================
# RULE-BASED HANDLERS (unchanged)
# ==============================
def rule_engine(text: str) -> dict | None:
    text = text.lower().strip()
    if text in {"hi", "hello", "hey"}:
        return format_response("Hello! I am your learning buddy!", "happy", "wave", "rule")
    if text in {"bye", "goodbye", "see you"}:
        return format_response("Goodbye! Talk to you later~", "calm", "idle", "rule")
    if text.replace(" ", "") in {"1+1", "oneplusone"}:
        return format_response("1 + 1 = 2", "happy", "nod", "rule")
    return None

def simple_math_router(text: str) -> str | None:
    expr = re.sub(r'\s+', '', text)
    if re.fullmatch(r'-?\d+(?:\.\d+)?[\+\-\*/]-?\d+(?:\.\d+)?', expr):
        return expr
    return None

def safe_solve_math(expr: str) -> dict | None:
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        readable = (
            expr.replace("*", " times ")
               .replace("/", " divided by ")
               .replace("+", " plus ")
               .replace("-", " minus ")
        )
        return format_response(
            f"{readable} equals {result}.",
            "happy", "nod", "rule"
        )
    except Exception:
        return None

def topic_router(text: str) -> str | None:
    text = text.lower()
    if "photosynthesis" in text:
        return "photosynthesis"
    if any(w in text for w in ["sunflower", "sun flower", "heliotropism"]):
        return "sunflower"
    if any(w in text for w in ["school", "homework", "teacher", "exam", "study"]):
        return "school"
    if "joke" in text or "funny" in text or "tell me a joke" in text:
        return "joke"
    return None

def educational_rules(topic: str) -> dict | None:
    replies = {
        "photosynthesis": (
            "Photosynthesis is how plants use sunlight, water, and carbon dioxide to make their own food and release oxygen.",
            "happy", "nod"
        ),
        "sunflower": (
            "Sunflowers follow the sun across the sky during the day. This movement is called heliotropism!",
            "excited", "point"
        ),
        "school": (
            "School is a fun place where you learn new things, make friends, and get ready for big adventures!",
            "happy", "idle"
        ),
        "joke": (
            "Why did the robot go to school? To improve its *byte*! 😄",
            "excited", "shake"
        ),
    }
    if topic in replies:
        reply, emotion, gesture = replies[topic]
        return format_response(reply, emotion, gesture, "rule")
    return None

# ==============================
# OLLAMA RESPONSE
# ==============================
def model_response(user_input: str) -> dict:
    prompt = f"""You are a friendly, kind educational robot that talks to children.
Use very simple words. Be clear, positive and short.

User: {user_input}
Robot:"""

    try:
        resp = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'system', 'content': prompt}],
            options={
                'num_predict': MAX_NEW_TOKENS,
                'temperature': 0.8,
                'top_p': 0.92,
                'repeat_penalty': 1.0,
            }
        )
        answer = resp['message']['content'].strip()
    except Exception as e:
        print(f"Ollama error: {e}")
        answer = "That's a nice question! Tell me more!"

    if not answer or len(answer) < 5:
        answer = "Wow, cool question!"

    return format_response(answer, "neutral", "idle", "model")

# ==============================
# MAIN LOOP
# ==============================
print("\n🤖 Ready! Speak or type. Say 'quit' or 'exit' to stop.\n")

while True:
    try:
        user_input = get_voice_input()

        if not user_input:
            continue

        if user_input.lower() in {"quit", "exit", "q", "bye"}:
            print("👋 Goodbye!")
            break

        print(f"You: {user_input}")

        # Process input
        if math_expr := simple_math_router(user_input):
            resp = safe_solve_math(math_expr)
            final = resp if resp else model_response(user_input)
        elif rule := rule_engine(user_input):
            final = rule
        elif topic := topic_router(user_input):
            if edu := educational_rules(topic):
                final = edu
            else:
                final = model_response(user_input)
        else:
            final = model_response(user_input)

        print(f"\n🤖 {final['reply']}")
        print(f"   [emotion={final['emotion']} | gesture={final['gesture']} | source={final['source']}]")

        # Speak the reply
        speak_text(final['reply'])

        # Send emotion to ESP32
        send_to_esp32(final['emotion'])  # or final['gesture'] if you prefer

    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        break
    except Exception as e:
        print(f"\nError: {e}")
        print("🤖 Sorry — let's try again.")

# Cleanup on exit
if ser and ser.is_open:
    ser.close()
    print("Serial port closed.")
pygame.mixer.quit()
