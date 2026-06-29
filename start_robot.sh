#!/bin/bash
# start_robot.sh — boot wrapper for the robotic companion assistant
# Called from crontab via: @reboot /home/robotpi/RoboticCompanion/start_robot.sh

REPO_DIR="/home/robotpi/RoboticCompanion" #robotpi is my root name. change the root name according to your pi root name
VENV_DIR="$REPO_DIR/rbcmp"
LOG_DIR="$REPO_DIR/logs"
mkdir -p "$LOG_DIR"

echo "$(date): boot script started" >> "$LOG_DIR/boot.log"

# Give USB (Arduino, USB mic/sound card) and Wi-Fi a few seconds to settle.
# Bump this up if your Arduino takes longer to enumerate or Wi-Fi is slow to connect.
sleep 15

# Reapply the calibrated mic mixer levels (Capture/Mic/AGC) for the USB sound
# card directly, instead of relying on alsa-restore.service — that service
# runs too early in boot for USB cards and loses these settings every reboot.
# Re-save anytime levels are re-tuned with:
# Wait for RoboMic to appear before restoring mixer state
echo "$(date): waiting for RoboMic..." >> "$LOG_DIR/boot.log"
for i in {1..10}; do
    grep -q "RoboMic" /proc/asound/cards && break
    echo "$(date): RoboMic not yet ready, retry $i/10" >> "$LOG_DIR/boot.log"
    sleep 2
done

echo "$(date): restoring mic mixer state" >> "$LOG_DIR/boot.log"
alsactl --file ~/RoboticCompanion/mic_state_robobic.conf restore RoboMic
alsactl --file ~/RoboticCompanion/spk_state_robospk.conf restore RoboSpk

# Hard-set Mic Capture Volume to 10 (36%, 3dB) after restore
# This overrides the chip's hardware default of 28 (100%, 30dB)
# which resets on full power-off regardless of alsactl
amixer -c RoboMic sset Mic 10,10 cap >> "$LOG_DIR/boot.log" 2>&1
amixer -c RoboMic sset 'Auto Gain Control' off >> "$LOG_DIR/boot.log" 2>&1
echo "$(date): mic gain forced to 10/28 (3dB)" >> "$LOG_DIR/boot.log"

# Verify it took
amixer -c RoboMic sget Mic >> "$LOG_DIR/boot.log" 2>&1

# Hard-set speaker volume after restore
# Replace 'Speaker' and value with whatever amixer -c RoboSpk shows
amixer -c RoboSpk sset Speaker 27,27 >> "$LOG_DIR/boot.log" 2>&1
amixer -c RoboSpk sset Mic 0 >> "$LOG_DIR/boot.log" 2>&1
echo "$(date): speaker volume forced" >> "$LOG_DIR/boot.log"

# Verify it took
amixer -c RoboSpk sget Speaker >> "$LOG_DIR/boot.log" 2>&1
# Make sure Ollama is actually responding before the assistant tries to use it.
# If it's already running as a systemd service this check just passes through.
if ! curl -s http://localhost:11434 >/dev/null 2>&1; then
    echo "$(date): ollama not responding, starting it..." >> "$LOG_DIR/boot.log"
    nohup ollama serve >> "$LOG_DIR/ollama.log" 2>&1 &
    sleep 5
fi

source "$VENV_DIR/bin/activate"

echo "$(date): launching assistant" >> "$LOG_DIR/boot.log"
python3 "$REPO_DIR/Python_Assistant/Testing_Stage/assistant_tinyllama.py" >> "$LOG_DIR/assistant.log" 2>&1 #For tempporary working script is put inside 
#Python_Assistant/Testing_Stage and after all the testing the working script will be moved to Python_Assistant dir 
