import subprocess

# Triggers an immediate safe shutdown
def trigger_system_halt():
	subprocess.run(["sudo", "poweroff"])
