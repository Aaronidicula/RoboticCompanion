#!/bin/bash

# Robotic Companion - Pi 4 Environment Setup
# Tested on Raspberry Pi OS 64-bit (Bookworm)

echo "🚀 Setting up Robotic Companion Environment on Pi 4..."

# Check 64-bit — required for Ollama and most ML packages
arch=$(uname -m)
echo "🖥️  Architecture: $arch"
if [ "$arch" != "aarch64" ]; then
    echo "⚠️  Warning: Not ARM64. Some packages may not install correctly."
fi

# ── SWAP SETUP (critical for Pi 4 with 4GB RAM) ──────
echo "💾 Configuring swap (2GB)..."
sudo dphys-swapfile swapoff
sudo sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/' /etc/dphys-swapfile
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
echo "✅ Swap set to 2GB"

# ── SYSTEM DEPENDENCIES ───────────────────────────────
echo "📦 Installing system dependencies..."
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
    git

# ── OLLAMA INSTALL ────────────────────────────────────
echo "🤖 Installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh
echo "✅ Ollama installed"

# ── PYTHON VENV ───────────────────────────────────────
echo "🐍 Creating virtual environment..."
python3 -m venv rbcmp
# Use venv pip directly — avoids subshell activation issues
VENV_PIP="./rbcmp/bin/pip"
VENV_PYTHON="./rbcmp/bin/python"

echo "⬆️  Upgrading pip..."
$VENV_PIP install --upgrade pip

# ── PYTORCH (ARM64 — no custom index needed) ──────────
echo "🔥 Installing PyTorch for ARM64..."
$VENV_PIP install torch torchvision torchaudio

# ── TRANSFORMERS & ML ─────────────────────────────────
echo "🤗 Installing Transformers..."
$VENV_PIP install transformers==4.40.0 datasets accelerate

# ── ROBOT-SPECIFIC PACKAGES ───────────────────────────
echo "🤖 Installing robot packages..."
$VENV_PIP install \
    ollama \
    pyserial \
    gTTS \
    pygame \
    SpeechRecognition \
    numpy \
    pandas \
    scikit-learn \
    tqdm \
    psutil

# ── REQUIREMENTS.TXT (Pi 4 accurate versions) ─────────
echo "📋 Writing requirements.txt..."
cat > requirements.txt << EOF
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
transformers==4.40.0
datasets>=2.0.0
accelerate>=0.20.0
ollama>=0.1.0
pyserial>=3.5
gTTS>=2.3.0
pygame>=2.5.0
SpeechRecognition>=3.10.0
numpy>=1.21.0
pandas>=1.3.0
scikit-learn>=1.0.0
tqdm>=4.64.0
psutil>=5.9.0
EOF

# ── ROBO-FAST MODEL SETUP ─────────────────────────────
echo "🧠 Setting up robo-fast model..."

# Pull base model first
ollama pull tinyllama

# Create Modelfile for robo-fast
cat > Modelfile << 'EOF'
FROM tinyllama

SYSTEM """You are Robo, a friendly educational robot that talks to children.
Use very simple words. Be short, clear and positive.
Always answer in one sentence only."""

PARAMETER temperature 0.3
PARAMETER repeat_penalty 1.5
PARAMETER num_predict 20
PARAMETER num_ctx 512
EOF

# Build robo-fast
ollama create robo-fast -f Modelfile
echo "✅ robo-fast model created"

# ── PROJECT STRUCTURE ─────────────────────────────────
echo "📁 Creating project structure..."
mkdir -p {data,models,logs,training}

# ── VERIFY ────────────────────────────────────────────
echo ""
echo "🔍 Verifying setup..."
ollama list
$VENV_PYTHON -c "import torch; print(f'PyTorch: {torch.__version__}')"
$VENV_PYTHON -c "import transformers; print(f'Transformers: {transformers.__version__}')"
$VENV_PYTHON -c "import ollama; print('Ollama Python: OK')"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate venv:     source rbcmp/bin/activate"
echo "2. Start Ollama:      ollama serve"
echo "3. Run your robot:    python3 Python_Assistant/Testing_Stage/assistant_tinyllama.py"
echo ""
echo "💡 Pi 4 tips:"
echo "- Keep swap at 2GB — model needs it"
echo "- Use SSD over microSD for faster model loading"
echo "- Run 'htop' to monitor RAM while robot is running"
echo "- TinyLlama response time: ~5-10s per reply on Pi 4"
