#!/bin/bash

# Humanoid Assistant SLM - Environment Setup
# Run this script to set up your development environment on Ubuntu 24.04

echo "🚀 Setting up Humanoid Assistant SLM Environment..."

# Check if Python 3.8+ is available
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
echo "🐍 Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv slm_env
source slm_env/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install PyTorch (CPU version for 8GB RAM efficiency)
echo "🔥 Installing PyTorch..."
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Transformers and related libraries
echo "🤗 Installing Transformers..."
pip install transformers datasets accelerate

# Install utility libraries
echo "🛠️  Installing utilities..."
pip install psutil jupyter matplotlib seaborn wandb

# Install development tools
echo "💻 Installing development tools..."
pip install black flake8 pytest

# Create requirements.txt
echo "📋 Creating requirements.txt..."
cat > requirements.txt << EOF
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0
transformers>=4.53.0
datasets>=2.0.0
accelerate>=0.20.0
psutil>=5.9.0
matplotlib>=3.5.0
seaborn>=0.11.0
wandb>=0.13.0
jupyter>=1.0.0
black>=22.0.0
flake8>=5.0.0
pytest>=7.0.0
numpy>=1.21.0
pandas>=1.3.0
tqdm>=4.64.0
EOF

# Create project structure
echo "📁 Creating project structure..."
mkdir -p {data,models,logs,configs,tests,notebooks}

# Create .gitignore
echo "📝 Creating .gitignore..."
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
slm_env/
env/
ENV/

# Model files
*.bin
*.safetensors
models/downloaded/

# Data
data/raw/
data/processed/
*.csv
*.json
conversation_history.json

# Logs
logs/
*.log

# Jupyter
.ipynb_checkpoints/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Weights & Biases
wandb/
EOF

echo "✅ Environment setup complete!"
echo ""
echo "🎯 Next steps:"
echo "1. Activate the environment: source slm_env/bin/activate"
echo "2. Run the starter script: python humanoid_assistant.py"
echo "3. Or use VS Code: code humanoid_assistant.py"
echo ""
echo "💡 Tips:"
echo "- Monitor RAM usage during training"
echo "- Use 'htop' to monitor system resources"
echo "- Consider using Kaggle for heavy training tasks"
