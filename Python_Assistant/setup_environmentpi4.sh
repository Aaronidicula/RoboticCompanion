#!/bin/bash

# ═══════════════════════════════════════════════════════════
# Robotic Companion — Pi 4 Clean Setup Script
# Raspberry Pi OS 64-bit (Bookworm) | 4GB RAM
# Run from: ~/RoboticCompanion/
# Usage: bash Python_Assistant/setup_environmentpi4.sh
# ═══════════════════════════════════════════════════════════

set -e  # Stop on any error

VENV_NAME="rbcmp"
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"  # Always resolves to RoboticCompanion/
VENV_DIR="$REPO_DIR/$VENV_NAME"
VENV_PIP="$VENV_DIR/bin/pip"
VENV_PYTHON="$VENV_DIR/bin/python"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   Robotic Companion — Pi 4 Setup             ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "📁 Repo dir : $REPO_DIR"
echo "🐍 Venv dir : $VENV_DIR"
echo ""

# ── STEP 1: ARCHITECTURE CHECK ────────────────────────────
echo "── Step 1: Architecture check ──"
arch=$(uname -m)
echo "   Architecture: $arch"
if [ "$arch" != "aarch64" ]; then
    echo "⚠️  Warning: Expected aarch64 (ARM64). Got: $arch"
    echo "   This script is designed for Raspberry Pi 4 (64-bit OS)."
    read -p "   Continue anyway? (y/N): " confirm
    [ "$confirm" = "y" ] || { echo "Aborted."; exit 1; }
fi
echo "   ✅ OK"
echo ""

# ── STEP 2: SWAP (critical for 4GB Pi) ───────────────────
echo "── Step 2: Swap setup (2GB) ──"

# Ensure dphys-swapfile is installed first
if ! command -v dphys-swapfile &>/dev/null; then
    echo "   dphys-swapfile not found — installing..."
    sudo apt-get update -qq
    sudo apt-get install -y dphys-swapfile
fi

if [ -f /etc/dphys-swapfile ]; then
    current_swap=$(grep CONF_SWAPSIZE /etc/dphys-swapfile | cut -d= -f2)
    echo "   Current swap size: ${current_swap}MB"
    if [ "$current_swap" = "2048" ]; then
        echo "   ✅ Swap already at 2GB, skipping"
    else
        sudo dphys-swapfile swapoff
        sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
        sudo dphys-swapfile setup
        sudo dphys-swapfile swapon
        echo "   ✅ Swap set to 2GB"
    fi
else
    echo "   ⚠️  Could not configure swap via dphys-swapfile — skipping (check your OS's swap mechanism manually)"
fi
echo ""

# ── STEP 3: SYSTEM DEPENDENCIES ──────────────────────────
echo "── Step 3: System dependencies ──"
sudo apt-get update -qq
sudo apt-get install -y \
    python3-pip \
    python3-venv \
    python3-dev \
    ffmpeg \
    portaudio19-dev \
    libasound2-dev \
    espeak \
    curl \
    git \
    alsa-utils \
    dphys-swapfile
echo "   ✅ System packages installed"
echo ""

# ── STEP 4: OLLAMA ────────────────────────────────────────
echo "── Step 4: Ollama ──"
if command -v ollama &>/dev/null; then
    echo "   Ollama already installed: $(ollama --version 2>/dev/null || echo 'version unknown')"
    echo "   ✅ Skipping install"
else
    echo "   Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    echo "   ✅ Ollama installed"
fi
echo ""

# ── STEP 5: CLEAN OLD VENV ───────────────────────────────
echo "── Step 5: Venv cleanup ──"
if [ -d "$VENV_DIR" ]; then
    echo "   Found existing venv at $VENV_DIR"
    echo "   Removing it for a clean install..."
    rm -rf "$VENV_DIR"
    echo "   ✅ Old venv removed"
else
    echo "   No existing venv found"
fi
echo ""

# ── STEP 6: CREATE FRESH VENV ────────────────────────────
echo "── Step 6: Creating fresh venv ($VENV_NAME) ──"
python3 -m venv "$VENV_DIR"
echo "   ✅ Venv created at $VENV_DIR"
echo ""

# ── STEP 7: UPGRADE PIP ──────────────────────────────────
echo "── Step 7: Upgrading pip ──"
$VENV_PIP install --upgrade pip --quiet
echo "   ✅ pip upgraded to $($VENV_PIP --version | cut -d' ' -f2)"
echo ""

# ── STEP 8: ROBOT PACKAGES (no PyTorch — not needed) ─────
echo "── Step 8: Installing robot packages ──"
echo "   NOTE: Skipping PyTorch/Transformers — robot uses Ollama, not HuggingFace"
echo "   Installing..."
$VENV_PIP install --quiet \
    ollama \
    pyserial \
    gTTS \
    pygame \
    SpeechRecognition \
    PyAudio \
    numpy \
    psutil \
    requests
echo "   ✅ Robot packages installed"
echo ""

# ── STEP 9: WRITE REQUIREMENTS.TXT ───────────────────────
echo "── Step 9: Writing requirements.txt ──"
cat > "$REPO_DIR/requirements.txt" << 'EOF'
# Robotic Companion — Pi 4 requirements
# PyTorch NOT included — robot uses Ollama for inference
ollama>=0.1.0
pyserial>=3.5
gTTS>=2.3.0
pygame>=2.5.0
SpeechRecognition>=3.10.0
PyAudio>=0.2.14
numpy>=1.21.0
psutil>=5.9.0
requests>=2.28.0
EOF
echo "   ✅ requirements.txt written"
echo ""

# ── STEP 10: START OLLAMA SERVICE ────────────────────────
echo "── Step 10: Starting Ollama service ──"
# Kill any existing ollama process first
pkill ollama 2>/dev/null || true
sleep 1
ollama serve &>/tmp/ollama.log &
OLLAMA_PID=$!
echo "   Waiting for Ollama to start (PID: $OLLAMA_PID)..."
sleep 5

# Check it's actually running
if ! curl -s http://localhost:11434 &>/dev/null; then
    echo "   ⚠️  Ollama didn't start cleanly, waiting 5 more seconds..."
    sleep 5
fi
echo "   ✅ Ollama service running"
echo ""

# ── STEP 11: PULL TINYLLAMA ──────────────────────────────
echo "── Step 11: Pulling tinyllama base model ──"
echo "   This downloads ~637MB — takes a few minutes..."
ollama pull tinyllama
echo "   ✅ tinyllama pulled"
echo ""

# ── STEP 12: CREATE ROBO-FAST MODEL ──────────────────────
echo "── Step 12: Creating robo-fast model ──"

# Remove old robo-fast if exists
ollama rm robo-fast 2>/dev/null && echo "   Removed old robo-fast" || true

# Write Modelfile
cat > "$REPO_DIR/Modelfile" << 'EOF'
FROM tinyllama

SYSTEM """You are Robo, a friendly educational robot that talks to children.
Use very simple words. Be short, clear and positive.
Always answer in one sentence only."""

PARAMETER temperature 0.3
PARAMETER repeat_penalty 1.5
PARAMETER num_predict 20
PARAMETER num_ctx 512
EOF

ollama create robo-fast -f "$REPO_DIR/Modelfile"
echo "   ✅ robo-fast model created"
echo ""

# ── STEP 13: VERIFY EVERYTHING ───────────────────────────
echo "── Step 13: Verification ──"
echo ""

echo "   📦 Installed packages:"
$VENV_PIP list | grep -E "ollama|gTTS|pygame|pyserial|SpeechRecognition|PyAudio|numpy|psutil"

echo ""
echo "   🤖 Ollama models:"
ollama list

echo ""
echo "   🧪 Testing robo-fast..."
RESPONSE=$(ollama run robo-fast "what is the sun?" 2>/dev/null)
echo "   Q: what is the sun?"
echo "   A: $RESPONSE"

echo ""
echo "   💾 Disk usage:"
df -h / | tail -1
echo "   Venv size: $(du -sh $VENV_DIR | cut -f1)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   ✅ Setup Complete!                          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""
echo "🎯 To run your robot:"
echo "   1. source $VENV_DIR/bin/activate"
echo "   2. ollama serve &"
echo "   3. python3 $REPO_DIR/Python_Assistant/Testing_Stage/assistant_tinyllama.py"
echo ""
echo "💡 Pi 4 tips:"
echo "   - Swap is now 2GB — keep it"
echo "   - robo-fast response time: ~5-10s per reply"
echo "   - Run 'htop' to monitor RAM while robot runs"
echo "   - Ollama log: /tmp/ollama.log"
echo ""
