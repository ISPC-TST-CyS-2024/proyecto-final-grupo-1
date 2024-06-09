import network
import socket
from machine import Pin, PWM
import time
import _thread

# Configuración de los pines de los LEDs
led_pins = {
    'dormitorio': Pin(20, Pin.OUT),
    'comedor': Pin(21, Pin.OUT),
    'cocina': Pin(8, Pin.OUT),
    'heladera_1': Pin(9, Pin.OUT),
    'heladera_2': Pin(10, Pin.OUT)
}

# Configuración del servomotor
cochera_pin = Pin(5)
cochera = PWM(cochera_pin, freq=50)

# Estado para controlar el parpadeo de los LEDs y el servomotor
blinking = False

# Función para configurar la conexión WiFi
def connect_wifi(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    max_attempts = 10
    attempt = 0
    
    while not wlan.isconnected() and attempt < max_attempts:
        print('Intentando conectarse a WiFi... Intento No. ', attempt + 1)
        time.sleep(1)
        attempt += 1

    if wlan.isconnected():
        print('Conección exitosa')
        print('Configuración de red:', wlan.ifconfig())
        return wlan.ifconfig()
    else:
        raise OSError('No se pudo conectar a la red WiFi')

# Función para manejar las solicitudes HTTP
def web_page():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Casa Domotica - Grupo 1</title>
    <style>
        .btn {
            padding: 10px 20px;
            font-size: 16px;
            cursor: pointer;
        }
        .on {
            background-color: green;
            color: white;
        }
        .off {
            background-color: red;
            color: white;
        }
    </style>
</head>
<body>
    <h1>Casa Domotica Grupo 1 - ESP32 c3 y Micropython</h1>
    <p>Controle los dispositivos haciendo click en los botones</p>
    <button class="btn off" id="dormitorio_on" onclick="toggle('dormitorio', 'on')">Dormitorio ON</button>
    <button class="btn on" id="dormitorio_off" onclick="toggle('dormitorio', 'off')">Dormitorio OFF</button><br><br>
    <button class="btn off" id="comedor_on" onclick="toggle('comedor', 'on')">Comedor ON</button>
    <button class="btn on" id="comedor_off" onclick="toggle('comedor', 'off')">Comedor OFF</button><br><br>
    <button class="btn off" id="cocina_on" onclick="toggle('cocina', 'on')">Cocina ON</button>
    <button class="btn on" id="cocina_off" onclick="toggle('cocina', 'off')">Cocina OFF</button><br><br>
    <button class="btn off" id="heladera_on" onclick="toggle('heladera', 'on')">Heladera ON</button>
    <button class="btn on" id="heladera_off" onclick="toggle('heladera', 'off')">Heladera OFF</button><br><br>
    <button class="btn off" id="cochera_on" onclick="toggle('cochera', 'on')">Cochera ON</button>
    <button class="btn on" id="cochera_off" onclick="toggle('cochera', 'off')">Cochera OFF</button><br><br>
    <script>
        function toggle(device, state) {
            var xhr = new XMLHttpRequest();
            xhr.open("GET", '/' + device + '/' + state, true);
            xhr.send();
            updateButtonState(device, state);
        }

        function updateButtonState(device, state) {
            var onButton = document.getElementById(device + '_on');
            var offButton = document.getElementById(device + '_off');
            if (state === 'on') {
                onButton.classList.add('on');
                onButton.classList.remove('off');
                offButton.classList.add('off');
                offButton.classList.remove('on');
            } else {
                onButton.classList.add('off');
                onButton.classList.remove('on');
                offButton.classList.add('on');
                offButton.classList.remove('off');
            }
        }
    </script>
</body>
</html>
"""
    return html

# Función para parpadear los LEDs de la heladera
def blink_leds():
    global blinking
    while blinking:
        led_pins['heladera_1'].on()
        led_pins['heladera_2'].off()
        time.sleep(0.5)
        led_pins['heladera_1'].off()
        led_pins['heladera_2'].on()
        time.sleep(0.5)
    led_pins['heladera_1'].off()
    led_pins['heladera_2'].off()

# Función para mover el servomotor
def move_cochera(on):
    if on:
        cochera.duty(40)  # Mover a 90 grados
    else:
        cochera.duty(115)  # Regresar a 0 grados

def handle_request(request):
    global blinking
    if '/dormitorio/on' in request:
        led_pins['dormitorio'].on()
    if '/dormitorio/off' in request:
        led_pins['dormitorio'].off()
    if '/comedor/on' in request:
        led_pins['comedor'].on()
    if '/comedor/off' in request:
        led_pins['comedor'].off()
    if '/cocina/on' in request:
        led_pins['cocina'].on()
    if '/cocina/off' in request:
        led_pins['cocina'].off()
    if '/heladera/on' in request:
        if not blinking:
            blinking = True
            _thread.start_new_thread(blink_leds, ())
    if '/heladera/off' in request:
        blinking = False
    if '/cochera/on' in request:
        move_cochera(True)
    if '/cochera/off' in request:
        move_cochera(False)

# Conectar a la red WiFi
ssid = 'JO3'
password = 'xpl203502'

try:
    connect_wifi(ssid, password)
except OSError as e:
    print('Failed to connect to WiFi:', e)
    while True:
        pass

# Configurar el servidor web
addr = socket.getaddrinfo('0.0.0.0', 80)[0][-1]
s = socket.socket()
s.bind(addr)
s.listen(1)
print('Server is listening on', addr)

while True:
    cl, addr = s.accept()
    print('Client connected from', addr)
    request = cl.recv(1024)
    request = str(request)
    print('Request:', request)
    handle_request(request)
    response = web_page()
    cl.send('HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n')
    cl.send(response)
    cl.close()
