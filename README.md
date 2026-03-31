# 🤖 Robotic Companion with Personality


A voice-interactive **robotic companion for children** that responds with **speech, emotion, and gestures**, combining **rule-based logic** with **local AI reasoning** — fully offline and privacy-friendly.

This project integrates:
- **ESP32 (LCD + Servo + Button)**
- **Python AI Brain**
- **Phi-3-mini (via Ollama)**
- **Speech-to-Text (Wit.ai)**
- **Text-to-Speech (gTTS)**

---

## ✨ Key Features

- 🎤 **Voice interaction** (speech recognition)
- 🧠 **Hybrid intelligence**
  - Rule-based responses for safety & accuracy
  - AI model fallback for open conversation
- 😊 **Personality & emotions**
  - LCD displays emotion
  - Servo gestures (wave, nod, shake)
- 🔊 **Speech output**
- 🔌 **ESP32 hardware integration**
- 📴 **Offline-first AI**
  - No paid API required
  - ChatGPT support optional (future)
- 🔐 **Privacy-friendly**
  - Runs locally on your machine

---

## 🧱 System Architecture

User (Voice/Text)
↓
Python Assistant
├── Rule Engine
├── Math / Topic Router
├── Ollama (Phi-3-mini)
├── Text-to-Speech
└── Serial / WiFi Output
↓
ESP32
├── LCD (Emotion)
├── Servo (Gesture)
└── Button (State Control)


---

## 🧰 Hardware Used

- ESP32-C3 (or compatible ESP32)
- 16x2 I2C LCD
- SG90 Servo Motor
- Push Button
- Jumper wires
- Speaker (optional, simulated in software)

---

## 🖥️ Software Stack

| Component | Tech |
|--------|------|
| AI Model | Phi-3-mini (Ollama) |
| Language | Python 3.10+ |
| Speech-to-Text | Wit.ai |
| Text-to-Speech | gTTS |
| Hardware Control | PySerial |
| Display | Adafruit LiquidCrystal |
| OS | Ubuntu 22.04+ |

---

## 🚀 Getting Started

### 1️⃣ Clone Repository

```bash
git clone <https://github.com/Aaronidicula/hackathon_code_repos.git>
cd Robotic_Companion_With_Personality

2️⃣ Create Python Virtual Environment

python3 -m venv venv
source venv/bin/activate

3️⃣ Install Dependencies

pip install -r requirements.txt

    ⚠️ Do NOT install flash-attn manually
    Ollama already handles GPU acceleration.

4️⃣ Install Ollama & Model

curl -fsSL https://ollama.com/install.sh | sh
ollama pull phi3:mini
ollama serve

Verify:

ollama run phi3:mini

5️⃣ Environment Variables

Create your Wit.ai account and set:

export WIT_AI_KEY="your_wit_ai_access_token"

6️⃣ Connect ESP32

Update serial port in Python code:

SERIAL_PORT = "/dev/ttyUSB0"

Common values:

    /dev/ttyUSB0

    /dev/ttyACM0

7️⃣ Flash ESP32 Code

Open the Arduino sketch from:

/esp32/

    Select ESP32-C3

    Upload sketch

    Open Serial Monitor @ 115200 baud

8️⃣ Run the Assistant

python main.py

You can:

    Speak using microphone 🎤

    Press the button to activate listening

    See emotions on LCD

    Watch servo gestures

    Hear spoken replies

🧪 Example Interaction

You: What is 1 + 1?
Robot: 1 plus 1 equals 2 😊

You: Tell me a joke
Robot: Why did the robot go to school? To improve its byte! 🤖

🛡️ Safety & Design Choices

    Rule-based math and factual answers

    No direct model output to hardware

    AI fallback only for safe, open questions

    Explicit intent routing

    Child-friendly language prompts

📁 Repository Structure

Robotic_Companion_With_Personality/
│
├── Python_Assistant/
│   └── main.py
│
├── esp32/
│   └── esp32_robot.ino
│
├── requirements.txt
├── .gitignore
└── README.md

🔮 Future Improvements

    WiFi communication (ESP32 ↔ Python)

    Conversation memory

    Emotion intensity levels

    Camera + face detection

    On-device inference (MicroPython + SLM)

    Mobile app controller

🏁 Hackathon Pitch Summary

    “A friendly robotic companion for children that listens, thinks, speaks, and reacts with emotion — built entirely with offline AI and affordable hardware.”

📜 License

MIT License
Free to use, modify, and extend.
🙌 Credits

Built by Aaron
Inspired by assistive robotics, education, and human-AI interaction.
