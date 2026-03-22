from pyngrok import ngrok
import subprocess
import sys
import time
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hardware_store.settings')

ngrok.set_auth_token('3BIErQrqv6Ubkth40q7G3NUrwo6_3fAin1NGu1cgSbwDhCYoz')

django_process = subprocess.Popen(
    [sys.executable, 'manage.py', 'runserver', '--noreload'],
)

time.sleep(3)

tunnel = ngrok.connect(8000)
print("\n" + "="*50)
print("Your app is LIVE at:")
print(tunnel.public_url)
print("="*50)
print("\nShare this URL with anyone!")
print("Press CTRL+C to stop\n")

try:
    django_process.wait()
except KeyboardInterrupt:
    django_process.terminate()
    ngrok.disconnect(tunnel.public_url)
    ngrok.kill()
    print("\nServer stopped.")