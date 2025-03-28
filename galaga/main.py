from machine import Pin, ADC, PWM, I2C
import ssd1306
import neopixel
import time
import random

# Configuración del joystick
joy_x = ADC(Pin(34))
joy_y = ADC(Pin(35))
joy_x.atten(ADC.ATTN_11DB)
joy_y.atten(ADC.ATTN_11DB)

# Configuración de la pantalla OLED
i2c = I2C(0, scl=Pin(22), sda=Pin(21))
oled = ssd1306.SSD1306_I2C(128, 64, i2c)

# Configuración del Neopixel (vidas)
neopixel_pin = 13
num_leds = 3
np = neopixel.NeoPixel(Pin(neopixel_pin), num_leds)

# Configuración del buzzer
buzzer = PWM(Pin(27), freq=1000, duty=0)

def beep():
    buzzer.duty(512)
    time.sleep(0.2)
    buzzer.duty(0)

def actualizar_vidas(vidas):
    for i in range(num_leds):
        np[i] = (0, 255, 0) if i < vidas else (0, 0, 0)
    np.write()

# Variables del juego
nave_x = 60
vidas = 3
puntaje = 0
balas = []
balas_enemigos = []
enemigos = []
enemigo_timer = 0
enemigo_velocidad = 1
enemigo_direccion = 1
enemigos_generados = 0

def generar_enemigos():
    global enemigos, enemigo_timer, enemigos_generados
    if time.ticks_ms() - enemigo_timer > 2000 and len(enemigos) < enemigos_generados / 2 + 1:
        for i in range(5):
            enemigos.append({'x': i * 20, 'y': 20, 'tipo': random.randint(0, 2)})
        enemigo_timer = time.ticks_ms()
        enemigos_generados = len(enemigos)

def mover_nave():
    global nave_x, balas
    x_val = joy_x.read()
    y_val = joy_y.read()

    if x_val < 1500 and nave_x > 0:
        nave_x -= 2
    if x_val > 2500 and nave_x < 120:
        nave_x += 2

    if y_val < 1000:
        balas.append({'x': nave_x + 4, 'y': 54})

def mover_enemigos():
    global balas_enemigos, enemigo_velocidad, enemigo_direccion
    for enemigo in enemigos:
        enemigo['x'] += enemigo_velocidad * enemigo_direccion
        if enemigo['x'] < 0 or enemigo['x'] > 120:
            enemigo_direccion *= -1
            enemigo['y'] += 10
        if random.randint(0, 100) < 2:
            balas_enemigos.append({'x': enemigo['x'], 'y': enemigo['y']})

def mover_balas():
    global balas, enemigos, puntaje
    balas_nuevas = []
    for bala in balas:
        bala['y'] -= 2
        if bala['y'] > 0:
            balas_nuevas.append(bala)
        for enemigo in enemigos:
            if abs(bala['x'] - enemigo['x']) < 4 and abs(bala['y'] - enemigo['y']) < 4:
                enemigos.remove(enemigo)
                puntaje += 10
                beep()
                break
    balas = balas_nuevas

def mover_balas_enemigos():
    global balas_enemigos, vidas
    balas_enemigos_nuevas = []
    for bala in balas_enemigos:
        bala['y'] += 2
        if bala['y'] < 64:
            balas_enemigos_nuevas.append(bala)
        if abs(bala['x'] - nave_x - 4) < 4 and abs(bala['y'] - 55) < 4:
            vidas -= 1
            beep()
            actualizar_vidas(vidas)
            balas_enemigos.remove(bala)
    balas_enemigos = balas_enemigos_nuevas

def dibujar_linea(oled, x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        oled.pixel(x0, y0, color)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def dibujar_nave(oled, x, y):
    dibujar_linea(oled, x, y + 8, x + 8, y + 8, 1)
    dibujar_linea(oled, x + 2, y + 6, x + 6, y + 6, 1)
    dibujar_linea(oled, x + 3, y + 4, x + 5, y + 4, 1)
    dibujar_linea(oled, x + 4, y + 2, x + 4, y + 2, 1)
    dibujar_linea(oled, x + 4, y, x + 4, y, 1)

def dibujar_enemigo(oled, x, y, tipo):
    if tipo == 0:
        oled.pixel(x, y, 1)
        oled.pixel(x + 1, y, 1)
        oled.pixel(x, y + 1, 1)
        oled.pixel(x + 1, y + 1, 1)
    elif tipo == 1:
        oled.pixel(x, y, 1)
        oled.pixel(x + 2, y, 1)
        oled.pixel(x + 1, y + 1, 1)
    else:
        dibujar_linea(oled, x, y, x + 2, y, 1)
        dibujar_linea(oled, x + 1, y, x + 1, y + 2, 1)

def dibujar():
    oled.fill(0)
    oled.text(f'Puntaje: {puntaje}', 0, 0)
    dibujar_nave(oled, nave_x, 55)
    for enemigo in enemigos:
        dibujar_enemigo(oled, enemigo['x'], enemigo['y'], enemigo['tipo'])
    for bala in balas:
        oled.pixel(bala['x'], bala['y'], 1)
    for bala in balas_enemigos:
        oled.pixel(bala['x'], bala['y'], 1)
    oled.show()

def juego():
    global puntaje, vidas, enemigo_velocidad, enemigo_timer, enemigos_generados
    actualizar_vidas(vidas)
    enemigo_timer = time.ticks_ms()
    enemigos_generados = 0
    while vidas > 0:
        generar_enemigos()
        mover_nave()
        mover_enemigos()
        mover_balas()
        mover_balas_enemigos()
        dibujar()
        time.sleep(0.1)
        if puntaje > 50:
            enemigo_velocidad = 2
        if puntaje > 100:
            enemigo_velocidad = 3
    oled.fill(0)
    oled.text('GAME OVER', 30, 30)
    oled.show()

juego()