import webview
import threading
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hardware_store.settings')
django.setup()

from django.core.management import call_command

def start_django():
    call_command('runserver', '--noreload')

thread = threading.Thread(target=start_django)
thread.daemon = True
thread.start()

import time
time.sleep(2)

webview.create_window(
    'Hardware Store Management System',
    'http://127.0.0.1:8000/dashboard/',
    width=1280,
    height=800,
    resizable=True,
)
webview.start()