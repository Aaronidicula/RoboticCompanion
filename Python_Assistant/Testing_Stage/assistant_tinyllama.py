#!/usr/bin/env python3
"""
Robotic Companion - Final Version for Raspberry Pi 4
- Audio output via USB card (plughw:3,0) → PAM8403 → Speaker
- Persistent memory with deque
- Arduino UNO R4 WiFi serial communication
- Voice input via MAX9814 → USB audio card
"""

import re
import os
import time
import random
import json
import subprocess
from collections import deque

# ── SUPPRESS JACK + ALSA WARNINGS ────────────────────
os.environ['JACK_NO_AUDIO_RESERVATION'] = '1'
os.environ['JACK_START_SERVER'] = '0'
os.environ['AUDIODEV'] = 'hw:3,0'

import ctypes
ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int,
                                       ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)
def py_error_handler(filename, line, function, err, fmt):
    pass
c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
asound = ctypes.cdll.LoadLibrary('libasound.so.2')
asound.snd_lib_error_set_handler(c_error_handler)

import speech_recognition as sr
import ollama
import serial
from gtts import gTTS

# ── CONFIG ───────────────────────────────────────────
MODEL_NAME       = "robo-fast"
SERIAL_PORT      = "/dev/ttyACM0"
SERIAL_BAUD      = 9600
MEMORY_LIMIT     = 50
MEMORY_FILE      = os.path.expanduser("~/RoboticCompanion/memory.json")
SERIAL_CMD_DELAY = 0.08

# ── FORCE AUDIO TO 3.5mm JACK ────────────────────────
print("🔊 Forcing audio output to 3.5mm jack...")
try:
    subprocess.run(["amixer", "cset", "numid=3", "1"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    print("✅ Audio forced to 3.5mm jack")
except:
    print("⚠️  Could not force audio output")

print("✅ Audio system ready (USB card → PAM8403 → Speaker)")

# ── SERIAL TO ARDUINO ─────────────────────────────────
ser = None
try:
    ser = serial.Serial(SERIAL_PORT, SERIAL_BAUD, timeout=1)
    time.sleep(2)
    ser.reset_input_buffer()
    print(f"✅ Arduino UNO R4 connected on {SERIAL_PORT}")
except Exception as e:
    print(f"⚠️  Arduino not connected: {e} — continuing without hardware")

# ── OLLAMA CHECK ──────────────────────────────────────
print("⏳ Warming up model...")
try:
    ollama.chat(model=MODEL_NAME,
                messages=[{'role': 'user', 'content': 'hi'}],
                options={'num_predict': 5})
    print("✅ Ollama model ready")
except Exception as e:
    print(f"❌ Ollama error: {e}")
    exit(1)

print("-" * 60)

# ── PERSISTENT MEMORY ────────────────────────────────
topic_memory = deque(maxlen=MEMORY_LIMIT)
last_topic   = {"keyword": None, "reply": None, "subject": None}

def memory_load():
    global topic_memory
    try:
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                data = json.load(f)
            loaded = data.get("topics", [])
            topic_memory = deque(loaded, maxlen=MEMORY_LIMIT)
            print(f"✅ Memory loaded — {len(topic_memory)} topics remembered")
        else:
            print("ℹ️  No memory file — starting fresh")
    except Exception as e:
        print(f"⚠️  Memory load error: {e} — starting fresh")
        topic_memory = deque(maxlen=MEMORY_LIMIT)

def memory_save_file():
    try:
        os.makedirs(os.path.dirname(MEMORY_FILE), exist_ok=True)
        with open(MEMORY_FILE, 'w') as f:
            json.dump({"topics": list(topic_memory)}, f, indent=2)
    except Exception as e:
        print(f"⚠️  Memory save error: {e}")

def memory_save(subject: str, reply: str):
    if not subject or not reply:
        return
    subject = subject.lower().strip()
    for entry in topic_memory:
        if entry.get("subject") == subject:
            entry["reply"] = reply
            memory_save_file()
            return
    topic_memory.append({"subject": subject, "reply": reply})
    memory_save_file()
    print(f"   [memory: saved '{subject}' | total: {len(topic_memory)}/{MEMORY_LIMIT}]")

def memory_lookup(subject: str) -> str | None:
    """Look up a subject in memory. Returns reply if found."""
    if not subject:
        return None
    subject = subject.lower().strip()
    # Exact match first
    for entry in topic_memory:
        if entry.get("subject") == subject:
            return entry.get("reply")
    # Partial match
    for entry in topic_memory:
        s = entry.get("subject", "")
        if subject in s or s in subject:
            return entry.get("reply")
    return None

def memory_status() -> str:
    if not topic_memory:
        return "Memory is empty"
    subjects = [e.get("subject", "?") for e in topic_memory]
    return f"Memory ({len(topic_memory)}/{MEMORY_LIMIT}): {', '.join(subjects)}"

memory_load()

# ── SERIAL HELPERS ────────────────────────────────────
def serial_send(command: str):
    if not (ser and ser.is_open):
        return
    try:
        ser.write(f"{command}\n".encode())
        delay = 0.18 if command.startswith("SPEAK:") else SERIAL_CMD_DELAY
        time.sleep(delay)
    except Exception as e:
        print(f"Serial write error: {e}")

def send_to_arduino(emotion: str, gesture: str = None, speak_text_str: str = None):
    if not (ser and ser.is_open):
        return
    if speak_text_str:
        clean = re.sub(r'\*+', '', speak_text_str)[:16].strip()
        serial_send(f"SPEAK:{clean}")
    serial_send(f"EMOTION:{emotion}")
    if gesture and gesture not in {"nod", "idle", "cheer"}:
        serial_send(f"GESTURE:{gesture}")
    print(f"→ Sent to Arduino: emotion={emotion} gesture={gesture}")

# ── AUDIO ─────────────────────────────────────────────
def speak_text(text: str):
    try:
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save("/tmp/response.mp3")
        os.system(
            "ffmpeg -y -i /tmp/response.mp3 "
            "-af 'volume=3.0' "
            "-ar 48000 -ac 1 /tmp/response_clean.wav "
            "2>/dev/null"
        )
        os.system("aplay -D plughw:3,0 /tmp/response_clean.wav 2>/dev/null")
    except Exception as e:
        print(f"TTS error: {e}")

# ── FORMAT HELPER ─────────────────────────────────────
def format_response(reply, emotion, gesture, source):
    return {"reply": reply.strip(), "emotion": emotion,
            "gesture": gesture, "source": source}

# ── SUBJECT EXTRACTOR ─────────────────────────────────
def extract_subject(text: str) -> str | None:
    t = text.lower().strip()
    conversational = ["can you", "can we", "what can", "what do you",
                      "how are you", "are you"]
    if any(t.startswith(c) for c in conversational):
        return None

    patterns = [
        r'what (?:is|are|was|were) (?:a |an |the )?(.+?)[\?]*$',
        r'tell me (?:about |more about )?(?:a |an |the )?(.+?)[\?]*$',
        r'who (?:is|was) (?:a |an |the )?(.+?)[\?]*$',
        r'how (?:does|do|did) (?:a |an |the )?(.+?) '
        r'(?:work|form|happen|grow|live|move)[\?]*$',
        r'explain (?:a |an |the )?(.+?)[\?]*$',
        r'(?:tell|show|teach) me (?:a |an |the )?(.+?)[\?]*$',
        r'(?:what|how) about (?:a |an |the )?(.+?)[\?]*$',
    ]
    for pattern in patterns:
        match = re.search(pattern, t)
        if match:
            subject = match.group(1).strip()
            subject = re.sub(r'\?+$', '', subject).strip()
            subject = re.sub(r'\s*(please|now|today)\s*$', '', subject).strip()
            if len(subject) >= 2:
                return subject

    words = re.sub(r'[^\w\s]', '', t).split()
    stopwords = {"what", "is", "are", "a", "an", "the", "tell", "me",
                 "about", "how", "does", "do", "who", "was", "were",
                 "explain", "more", "hi", "hey", "hello"}
    content_words = [w for w in words if w not in stopwords]
    if content_words:
        return content_words[-1]
    return None

# ── RULE ENGINE ───────────────────────────────────────
def rule_engine(text: str) -> dict | None:
    t = text.lower().strip()

    greetings = {"hi", "hello", "hey", "hiya", "howdy",
                 "good morning", "good afternoon", "good evening"}
    farewells  = {"bye", "goodbye", "see you", "see ya",
                  "goodnight", "good night"}
    identity   = {"what is your name", "who are you", "your name",
                  "what are you", "are you a robot"}
    howru      = {"how are you", "how are you doing",
                  "are you ok", "how do you feel"}

    if any(g in t for g in greetings):
        return format_response(
            "Hello! I am Robo, your learning buddy!",
            "happy", "wave", "rule")
    if any(f in t for f in farewells):
        return format_response(
            "Goodbye! Come talk to me again soon!",
            "calm", "wave", "rule")
    if any(i in t for i in identity):
        return format_response(
            "I am Robo, a friendly learning robot built just for you!",
            "excited", "wave", "rule")
    if any(h in t for h in howru):
        return format_response(
            "I am great thank you! I love talking to you!",
            "happy", "nod", "rule")
    return None

# ── MATH HANDLER ──────────────────────────────────────
def simple_math_router(text: str) -> str | None:
    expr = re.sub(r'\s+', '', text)
    if re.fullmatch(r'-?\d+(?:\.\d+)?[+\-*/]-?\d+(?:\.\d+)?', expr):
        return expr
    return None

def safe_solve_math(expr: str) -> dict | None:
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        readable = (expr.replace("*", " times ")
                       .replace("/", " divided by ")
                       .replace("+", " plus ")
                       .replace("-", " minus "))
        return format_response(
            f"{readable} equals {result}!",
            "happy", "nod", "rule")
    except Exception:
        return None

# ── STATIC TOPICS ─────────────────────────────────────
TOPICS = {
    "how to make":      ("You can make things by learning, practising, and asking grown ups to help!",
                         "happy", "nod"),
    "how do you make":  ("Great question! You learn step by step with help from teachers and grown ups!",
                         "happy", "nod"),
    "solar system":     ("Our solar system has one sun, eight planets, and many moons, comets, and asteroids!",
                         "excited", "nod"),
    "black hole":       ("A black hole is a place in space where gravity is so strong that nothing can escape it!",
                         "excited", "nod"),
    "square":           ("A square is a shape with four equal sides and four corners!", "happy", "nod"),
    "circle":           ("A circle is a perfectly round shape, like a ball or the sun!", "happy", "nod"),
    "triangle":         ("A triangle is a shape with three sides and three corners!", "happy", "nod"),
    "rectangle":        ("A rectangle is like a square but two sides are longer!", "happy", "nod"),
    "photosynthesis":   ("Plants use sunlight, water, and air to make their own food — that is photosynthesis!",
                         "happy", "nod"),
    "lightning":        ("Lightning is a giant spark of electricity that flashes in the sky during storms!",
                         "excited", "nod"),
    "thunder":          ("Thunder is the loud sound lightning makes when it heats the air really fast!",
                         "calm", "nod"),
    "earthquake":       ("An earthquake is when the ground shakes because the Earth is moving underneath!",
                         "calm", "nod"),
    "volcano":          ("A volcano is a mountain that can shoot out hot melted rock called lava!",
                         "excited", "nod"),
    "rainbow":          ("A rainbow appears when sunlight shines through raindrops and makes beautiful colors!",
                         "excited", "nod"),
    "gravity":          ("Gravity is an invisible force that pulls things down to the ground!", "happy", "nod"),
    "mountain":         ("A mountain is a very tall piece of land that rises high above everything around it!",
                         "excited", "nod"),
    "desert":           ("A desert is a very dry place that gets very little rain and can be very hot!",
                         "calm", "nod"),
    "forest":           ("A forest is a large area full of trees where many animals live!", "happy", "nod"),
    "ocean":            ("The ocean is a huge body of salty water that covers most of our planet!",
                         "excited", "nod"),
    "river":            ("A river is a long flowing stream of fresh water that travels to the sea!",
                         "happy", "nod"),
    "cloud":            ("Clouds are made of tiny water droplets floating high up in the sky!", "happy", "nod"),
    "rain":             ("Rain is water that falls from clouds in the sky when they get too full!",
                         "happy", "nod"),
    "snow":             ("Snow is frozen water that falls from clouds as tiny white flakes!", "excited", "nod"),
    "wind":             ("Wind is moving air — when air flows from one place to another it makes wind!",
                         "happy", "nod"),
    "fire":             ("Fire is hot and bright — it gives us light and warmth but we must be careful!",
                         "calm", "nod"),
    "water":            ("Water is a clear liquid we drink to stay healthy — it covers most of our planet!",
                         "happy", "nod"),
    "ice":              ("Ice is frozen water — water gets so cold it turns solid and hard!", "happy", "nod"),
    "air":              ("Air is all around us even though we cannot see it — we breathe it to stay alive!",
                         "happy", "nod"),
    "seed":             ("A seed is a tiny thing that grows into a plant when you give it water and sunlight!",
                         "happy", "nod"),
    "flower":           ("Flowers are the colorful parts of plants that smell nice and attract bees!",
                         "happy", "nod"),
    "telescope":        ("A telescope is a tool that makes faraway things like stars look much bigger!",
                         "happy", "nod"),
    "asteroid":         ("An asteroid is a large rock that travels through space — millions orbit the sun!",
                         "excited", "nod"),
    "comet":            ("A comet is a ball of ice and rock that travels through space with a glowing tail!",
                         "excited", "nod"),
    "astronaut":        ("An astronaut is a person who travels into space to explore it!", "excited", "nod"),
    "satellite":        ("A satellite is a machine we send into space that goes around the Earth!",
                         "happy", "nod"),
    "galaxy":           ("A galaxy is a huge group of billions of stars all held together in space!",
                         "excited", "nod"),
    "rocket":           ("A rocket is a very fast machine that can fly all the way into space!",
                         "excited", "nod"),
    "neptune":          ("Neptune is the farthest planet from the sun and has the strongest winds!",
                         "excited", "nod"),
    "uranus":           ("Uranus is a blue green planet that spins on its side!", "excited", "nod"),
    "saturn":           ("Saturn has beautiful rings around it made of ice and rocks!", "excited", "nod"),
    "jupiter":          ("Jupiter is the biggest planet — all other planets could fit inside it!",
                         "excited", "nod"),
    "mars":             ("Mars is called the red planet because its soil is red!", "excited", "nod"),
    "venus":            ("Venus is the hottest planet even though it is not the closest to the sun!",
                         "excited", "nod"),
    "mercury":          ("Mercury is the smallest planet and the closest one to the sun!", "excited", "nod"),
    "pluto":            ("Pluto is a small dwarf planet at the very edge of our solar system!",
                         "excited", "nod"),
    "planet":           ("A planet is a huge round object that goes around a star. Earth is our planet!",
                         "excited", "nod"),
    "earth":            ("Earth is our home planet! It has land, oceans, and air for us to breathe!",
                         "happy", "nod"),
    "moon":             ("The moon goes around the Earth and lights up the night sky!", "excited", "nod"),
    "star":             ("Stars are huge balls of fire very far away in space — the sun is our closest star!",
                         "excited", "nod"),
    "sun":              ("The sun is a giant ball of fire in the sky that gives us light and warmth!",
                         "excited", "nod"),
    "dinosaur":         ("Dinosaurs were amazing animals that lived millions of years ago!", "excited", "nod"),
    "butterfly":        ("Butterflies start as caterpillars and grow wings to become beautiful fliers!",
                         "excited", "nod"),
    "elephant":         ("Elephants are the biggest land animals and have a long trunk to pick things up!",
                         "excited", "nod"),
    "penguin":          ("Penguins are birds that cannot fly but they are amazing swimmers!", "excited", "nod"),
    "tiger":            ("Tigers are big wild cats with orange and black stripes — they are very fast!",
                         "excited", "nod"),
    "whale":            ("Whales are the biggest animals on Earth and they live in the ocean!", "excited", "nod"),
    "horse":            ("Horses are strong animals that people ride and they love to run fast!", "excited", "nod"),
    "snake":            ("Snakes are long animals with no legs that slide along the ground!", "calm", "nod"),
    "frog":             ("Frogs start as tadpoles in water and grow legs to jump on land!", "excited", "nod"),
    "lion":             ("Lions are called the king of the jungle — they are big strong cats!", "excited", "nod"),
    "bird":             ("Birds have wings and feathers and most of them can fly high in the sky!",
                         "excited", "nod"),
    "fish":             ("Fish live in water and breathe through gills instead of lungs like us!",
                         "happy", "nod"),
    "dog":              ("Dogs are friendly animals that love to play and are great friends to humans!",
                         "excited", "wave"),
    "cat":              ("Cats are fluffy animals that love to sleep and purr when they are happy!",
                         "happy", "nod"),
    "bee":              ("Bees make honey and help flowers grow by carrying pollen from flower to flower!",
                         "happy", "nod"),
    "brain":            ("Your brain is like a computer in your head that controls everything you do!",
                         "excited", "nod"),
    "heart":            ("Your heart pumps blood all around your body to keep you alive and healthy!",
                         "happy", "nod"),
    "bone":             ("Bones are the hard parts inside your body that hold you up like a frame!",
                         "happy", "nod"),
    "eye":              ("Your eyes let you see all the beautiful colors and shapes in the world!",
                         "happy", "nod"),
    "multiplication":   ("Multiplication is like adding the same number many times really fast!",
                         "happy", "nod"),
    "subtraction":      ("Subtraction means taking away a number to get a smaller number!", "happy", "nod"),
    "subtract":         ("Subtraction means taking away a number to get a smaller number!", "happy", "nod"),
    "multiply":         ("Multiplication is like adding the same number many times really fast!",
                         "happy", "nod"),
    "addition":         ("Addition means adding numbers together to get a bigger number!", "happy", "nod"),
    "fraction":         ("A fraction is a part of a whole thing, like half a pizza!", "happy", "nod"),
    "geometry":         ("Geometry is the study of shapes like circles, squares, and triangles!",
                         "happy", "nod"),
    "divide":           ("Division means splitting a number into equal parts!", "happy", "nod"),
    "number":           ("Numbers help us count things — one, two, three, all the way to infinity!",
                         "happy", "nod"),
    "zero":             ("Zero means nothing at all — it is the smallest whole number!", "happy", "nod"),
    "sum":              ("A sum is the answer you get when you add numbers together!", "happy", "nod"),
    "internet":         ("The internet connects computers all over the world so people can share information!",
                         "happy", "nod"),
    "computer":         ("A computer is a smart machine that can store and work with lots of information!",
                         "happy", "nod"),
    "robot":            ("A robot is a machine that can do jobs — just like me!", "excited", "wave"),
    "exercise":         ("Exercise means moving your body to stay healthy and strong!", "excited", "wave"),
    "family":           ("Family are the special people who love and take care of you!", "happy", "wave"),
    "friend":           ("Friends are people who care about you and love to spend time with you!",
                         "happy", "wave"),
    "sleep":            ("Sleep helps your body and brain rest and grow strong overnight!", "calm", "nod"),
    "food":             ("Food gives our body energy to grow, play, and stay healthy!", "happy", "nod"),
    "sunflower":        ("Sunflowers follow the sun across the sky — that is called heliotropism!",
                         "excited", "nod"),
    "color":            ("Colors make the world beautiful — red, blue, yellow, green and so many more!",
                         "excited", "nod"),
    "music":            ("Music is made of sounds put together to make something beautiful to hear!",
                         "excited", "wave"),
    "book":             ("Books are full of amazing stories and facts that take you on adventures!",
                         "happy", "nod"),
    "game":             ("Games are fun activities that help you learn and play with friends!",
                         "excited", "wave"),
    "school":           ("School is where you learn amazing new things and make great friends!",
                         "happy", "nod"),
    "joke":             ("Why did the robot go to school? To improve its byte! Ha ha!", "excited", "shake"),
}

# ── TOPIC EXTRAS ──────────────────────────────────────
TOPIC_EXTRAS = {
    "square":        "A square has four corners called right angles and all sides are exactly the same length!",
    "circle":        "A circle has no corners — every point on it is the same distance from the center!",
    "triangle":      "There are different kinds of triangles — some have equal sides and some do not!",
    "rectangle":     "A rectangle has four right angle corners just like a square but two sides are longer!",
    "sun":           "The sun is so big that one million Earths could fit inside it!",
    "moon":          "The moon has no air or wind so astronaut footprints are still there today!",
    "star":          "Stars look small because they are very far away — some are even bigger than our sun!",
    "earth":         "The Earth is about 4.5 billion years old and spins around once every 24 hours!",
    "planet":        "There are eight planets — Mercury, Venus, Earth, Mars, Jupiter, Saturn, Uranus, Neptune!",
    "rain":          "Rain is collected in rivers and lakes and that is the water we drink every day!",
    "dinosaur":      "Some dinosaurs were as tall as a five story building and some were as small as a chicken!",
    "robot":         "Robots are built using motors, sensors, and computers that tell them what to do!",
    "photosynthesis":"Plants store the food they make in their leaves, stems, and roots!",
    "gravity":       "Gravity keeps us on the ground and keeps the Earth going around the sun!",
    "heart":         "Your heart beats about 100000 times every single day without stopping!",
    "brain":         "Your brain has about 86 billion tiny cells called neurons that send messages!",
    "butterfly":     "A butterfly goes through four stages — egg, caterpillar, cocoon, and then butterfly!",
    "bee":           "A bee visits about 2000 flowers every day to collect nectar to make honey!",
    "elephant":      "Elephants never forget — they have an amazing memory and can remember friends for years!",
    "water":         "Water can be a liquid, solid like ice, or a gas like steam depending on temperature!",
    "volcano":       "The hot melted rock inside a volcano is called magma — it becomes lava when it comes out!",
    "rainbow":       "A rainbow always has seven colors — red, orange, yellow, green, blue, indigo, and violet!",
    "computer":      "The first computer was as big as a whole room but now computers fit in your pocket!",
    "internet":      "Billions of people use the internet every day to learn, talk, and share things!",
    "geometry":      "Geometry is used by architects and engineers to design buildings and bridges!",
    "ocean":         "The ocean is so deep that the tallest mountain on Earth could fit inside it!",
    "dog":           "Dogs have an amazing sense of smell that is 10000 times better than humans!",
    "cat":           "Cats sleep for about 12 to 16 hours every day!",
    "snow":          "Every single snowflake has a unique shape — no two are ever exactly the same!",
    "lightning":     "Lightning is five times hotter than the surface of the sun!",
    "seed":          "Some seeds can stay in the ground for hundreds of years before they start to grow!",
    "music":         "Music can make you feel happy, calm, or excited — it affects your brain in amazing ways!",
    "book":          "Reading books helps your brain grow stronger and learn new words every day!",
    "fish":          "There are more than 30000 different kinds of fish living in oceans and rivers!",
    "bird":          "Some birds fly from one end of the Earth to the other every year!",
    "lion":          "A group of lions is called a pride and they live and hunt together as a family!",
    "whale":         "Blue whales are the largest animals that have ever lived on Earth!",
    "rocket":        "Rockets work by pushing hot gas downward really fast which pushes the rocket upward!",
    "astronaut":     "Astronauts train for years before going to space and must learn to live without gravity!",
    "galaxy":        "Our galaxy is called the Milky Way and it has over 200 billion stars in it!",
    "flower":        "Flowers use their bright colors and sweet smell to attract bees and butterflies!",
    "ice":           "Icebergs are huge chunks of ice — most of the ice is hidden underwater!",
    "cloud":         "One fluffy cloud can weigh as much as 500000 kilograms even though it floats!",
    "wind":          "The fastest wind ever recorded on Earth was over 400 kilometers per hour in a tornado!",
    "forest":        "Forests are home to more than half of all animal and plant species on Earth!",
    "mountain":      "Mount Everest is the tallest mountain and it is still slowly growing taller!",
    "sleep":         "While you sleep your brain sorts everything you learned that day and stores it!",
    "food":          "Eating lots of different colorful fruits and vegetables keeps your body strong!",
    "exercise":      "Just 30 minutes of exercise a day makes your heart, brain, and muscles stronger!",
    "pluto":         "Pluto was called a planet for 76 years but in 2006 scientists reclassified it!",
    "mars":          "Mars has the tallest volcano in the solar system — three times taller than Everest!",
    "jupiter":       "Jupiter has a giant storm called the Great Red Spot spinning for 300 years!",
    "saturn":        "Saturn is so light that if you found a big enough bathtub it would float in water!",
    "solar system":  "Our solar system takes 225 million years for the sun to orbit the Milky Way galaxy!",
    "black hole":    "The nearest black hole to Earth is about 1000 light years away so we are safe!",
    "comet":         "Halley's Comet visits our solar system every 75 years — next visit will be in 2061!",
}

# ── TOPIC HANDLER ─────────────────────────────────────
def topic_handler(text: str) -> dict | None:
    t = text.lower()

    subject = extract_subject(text) or t
    cached  = memory_lookup(subject)
    if cached:
        last_topic["keyword"] = subject
        last_topic["reply"]   = cached
        last_topic["subject"] = subject
        print(f"   [memory: hit '{subject}']")
        return {"reply": cached, "emotion": "happy",
                "gesture": "nod", "source": "memory"}

    sorted_topics = sorted(TOPICS.items(), key=lambda x: len(x[0]), reverse=True)
    for keyword, (reply, emotion, gesture) in sorted_topics:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, t):
            last_topic["keyword"] = keyword
            last_topic["reply"]   = reply
            last_topic["subject"] = keyword
            memory_save(keyword, reply)
            return {"reply": reply, "emotion": emotion,
                    "gesture": gesture, "source": "topic"}
    return None

# ── FOLLOW-UP HANDLER ─────────────────────────────────
FOLLOWUP_PHRASES = [
    "tell me more", "more about", "tell me about it",
    "what else", "and then", "more please", "say more",
    "explain more", "can you explain", "i want to know more",
]

def followup_handler(text: str) -> dict | None:
    t = text.lower().strip()
    if not any(phrase in t for phrase in FOLLOWUP_PHRASES):
        return None

    keyword = last_topic.get("keyword")
    subject = last_topic.get("subject")

    if keyword and keyword in TOPIC_EXTRAS:
        extra = TOPIC_EXTRAS[keyword]
        memory_save(f"{keyword} more", extra)
        return format_response(extra, "excited", "nod", "followup")

    if subject:
        for key in TOPIC_EXTRAS:
            if key in subject or subject in key:
                extra = TOPIC_EXTRAS[key]
                return format_response(extra, "excited", "nod", "followup")

    if subject:
        cached = memory_lookup(subject)
        if cached:
            return format_response(
                f"I remember — {cached} Want to ask me something new?",
                "happy", "nod", "followup")

    if last_topic.get("reply"):
        return format_response(
            f"I said: {last_topic['reply']} Ask me something new to learn more!",
            "happy", "nod", "followup")

    return format_response(
        "Ask me about something and I will remember it for next time!",
        "happy", "nod", "followup")

# ── AI FALLBACK ───────────────────────────────────────
FALLBACKS = [
    "That is a great question! I am still learning about that one!",
    "Wow, I need to think more about that — ask me something else!",
    "I do not know that yet, but you can look it up with a grown up!",
    "That is tricky! Ask a teacher or parent about that one!",
]

def model_response(user_input: str) -> dict:
    prompt = f"A friendly robot says one simple sentence to a child about: {user_input} -"
    try:
        resp = ollama.chat(
            model=MODEL_NAME,
            messages=[{'role': 'user', 'content': prompt}],
            options={
                'num_predict':    20,
                'temperature':    0.3,
                'repeat_penalty': 1.5,
                'num_thread':     4,
                'stop':           ['!', '?', '.'],
            }
        )
        answer = resp['message']['content'].strip()
        answer = re.sub(r'[^\x00-\x7F]+', '', answer).strip()

        bad_phrases = ["sure", "i cannot", "as an ai", "i am unable",
                       "friendly robot", "simple sentence", "without any",
                       "also known as", "minor planet", "planetoid"]
        if len(answer) < 10 or any(b in answer.lower() for b in bad_phrases):
            answer = ""

    except Exception as e:
        print(f"Ollama error: {e}")
        answer = ""

    final_answer = answer or random.choice(FALLBACKS)

    subject = extract_subject(user_input)
    if subject and answer:
        memory_save(subject, final_answer)

    last_topic["keyword"] = subject
    last_topic["reply"]   = final_answer
    last_topic["subject"] = subject

    return format_response(final_answer, "happy", "nod", "model")

# ── PROCESS ───────────────────────────────────────────
def process(user_input: str) -> dict:
    t = user_input.lower().strip()

    if math_expr := simple_math_router(user_input):
        return safe_solve_math(math_expr) or model_response(user_input)

    if followup := followup_handler(user_input):
        return followup

    if len(t.split()) <= 4:
        if rule := rule_engine(user_input):
            if not topic_handler(user_input):
                return rule

    if topic := topic_handler(user_input):
        return topic

    if rule := rule_engine(user_input):
        return rule

    start = time.time()
    result = model_response(user_input)
    print(f"   [inference: {time.time() - start:.1f}s]")
    return result

# ── VOICE INPUT ───────────────────────────────────────
def get_voice_input() -> str:
    r = sr.Recognizer()
    r.dynamic_energy_threshold = False
    r.energy_threshold = 50
    r.pause_threshold = 0.8

    mic = sr.Microphone(device_index=1, sample_rate=48000)

    try:
        with mic as source:
            print("🎤 Listening...")
            audio = r.listen(source, timeout=10, phrase_time_limit=8)
            print("⏳ Processing...")

        text = r.recognize_google(audio)
        print(f"You said: {text}")
        return text.strip()

    except sr.WaitTimeoutError:
        print("⏱️  No speech detected")
        return ""
    except sr.UnknownValueError:
        print("❓ Could not understand")
        return ""
    except Exception as e:
        print(f"🎤 Voice error: {e}")
        return ""

# ── MAIN LOOP ─────────────────────────────────────────
print(f"\n🤖 Robo ready! Speak to me. (say 'quit' or 'bye' to stop)\n")
print(f"   {memory_status()}\n")

while True:
    try:
        user_input = get_voice_input()

        if not user_input:
            continue

        if user_input.lower() == "memory":
            print(memory_status())
            continue

        if user_input.lower() in {"quit", "exit", "bye", "goodbye"}:
            print("👋 Shutting down...")
            speak_text("Goodbye! See you soon!")
            serial_send("END")
            break

        print(f"You: {user_input}")

        final = process(user_input)

        print(f"\n🤖 Robo: {final['reply']}")
        print(f"   [emotion={final['emotion']} | gesture={final['gesture']} | source={final['source']}]\n")

        send_to_arduino(
            emotion=final['emotion'],
            gesture=final.get('gesture'),
            speak_text_str=final['reply']
        )

        speak_text(final['reply'])

    except KeyboardInterrupt:
        print("\n👋 Shutting down...")
        speak_text("Goodbye!")
        serial_send("END")
        break
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        traceback.print_exc()
        speak_text("Oops, let us try again!")
        continue

# ── CLEANUP ───────────────────────────────────────────
if ser and ser.is_open:
    ser.close()
    print("Serial port closed.")
