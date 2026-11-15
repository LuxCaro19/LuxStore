"""
Lanzador de escritorio para LuxStore (Punto de Venta y Gestión Comercial).
Inicia el servidor interno Waitress y abre la ventana nativa sin navegador mediante PyWebView.
"""
import os
import sys
import socket
import threading
import time
from pathlib import Path
import urllib.request

# Ajustar sys.path si es ejecutable congelado con PyInstaller
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(getattr(sys, '_MEIPASS', Path(sys.executable).parent))
    sys.path.insert(0, str(BASE_DIR))
else:
    BASE_DIR = Path(__file__).resolve().parent

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

from django.core.management import call_command
from django.contrib.staticfiles.handlers import StaticFilesHandler
from django.contrib.auth.models import User
from config.wsgi import application
import waitress
import webview


def inicializar_sistema():
    """Ejecuta migraciones automáticas y crea usuario administrador si la BD es nueva."""
    try:
        call_command('migrate', interactive=False)

        # Si no hay usuarios creados, crear el administrador por defecto
        if User.objects.count() == 0:
            User.objects.create_superuser(
                username='admin',
                email='admin@luxstore.local',
                password='admin',
                first_name='Administrador'
            )
            print("Cuenta inicial creada: usuario 'admin' / contrasena 'admin'")
    except Exception as e:
        print(f"Error durante inicializacion de base de datos: {e}")


def encontrar_puerto_libre(puerto_inicial=8000, max_intentos=50):
    """Busca un puerto libre en el sistema para evitar conflictos si 8000 esta ocupado."""
    for puerto in range(puerto_inicial, puerto_inicial + max_intentos):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', puerto)) != 0:
                return puerto
    return puerto_inicial


def iniciar_servidor_waitress(puerto):
    """Levanta el servidor WSGI en segundo plano."""
    wsgi_app = StaticFilesHandler(application)
    # Escucha en 0.0.0.0 para permitir que telefonos en la misma red Wi-Fi puedan conectarse
    waitress.serve(
        wsgi_app,
        host='0.0.0.0',
        port=puerto,
        threads=8,
        _quiet=True
    )


def esperar_servidor(url, timeout=15):
    """Espera a que el servidor web responda antes de abrir la ventana."""
    inicio = time.time()
    while time.time() - inicio < timeout:
        try:
            with urllib.request.urlopen(url, timeout=1):
                return True
        except Exception:
            time.sleep(0.2)
    return False


def main():
    inicializar_sistema()
    puerto = encontrar_puerto_libre()
    url = f"http://127.0.0.1:{puerto}/"

    # Iniciar Waitress en un hilo daemon
    servidor_thread = threading.Thread(
        target=iniciar_servidor_waitress,
        args=(puerto,),
        daemon=True
    )
    servidor_thread.start()

    # Esperar a que el servidor este listo
    esperar_servidor(url)

    # Crear la ventana nativa de escritorio
    window = webview.create_window(
        title="LuxStore - Punto de Venta",
        url=url,
        width=1280,
        height=820,
        min_size=(960, 600),
        text_select=False,
    )

    # Iniciar bucle de eventos nativo de Windows (WebView2)
    webview.start(private_mode=False)


if __name__ == '__main__':
    main()
