import board
import busio
import displayio
from fourwire import FourWire
import neopixel
import terminalio
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import label
from adafruit_st7735r import ST7735R
import random
import time
import math
import digitalio
import adafruit_adxl34x
import time

def i2c_scan(i2c):
    print("Scanning I2C bus...")
    while not i2c.try_lock():
        pass
    try:
        devices = i2c.scan()
        if devices:
            print("I2C addresses found:", [hex(device) for device in devices])
        else:
            print("No I2C devices found.")
    finally:
        i2c.unlock()

mosi_pin = board.GP19
clk_pin = board.GP18
reset_pin = board.GP22
cs_pin = board.GP17
dc_pin = board.GP20

i2c = busio.I2C(scl=board.GP15, sda=board.GP10)
i2c_scan(i2c)
time.sleep(2)

DEVICE_ADDR = 0x53
DEVICE_ID_REG = 0x00
while not i2c.try_lock():
    pass
try:
    result = bytearray(1)
    i2c.writeto(DEVICE_ADDR, bytes([DEVICE_ID_REG]))
    i2c.readfrom_into(DEVICE_ADDR, result)
    print("ADXL345 Device ID register:", hex(result[0]))
finally:
    i2c.unlock()
time.sleep(1)
adxl345 = adafruit_adxl34x.ADXL345(i2c)

displayio.release_displays()

spi = busio.SPI(clock=clk_pin, MOSI=mosi_pin)
display_bus = FourWire(spi, command=dc_pin, chip_select=cs_pin, reset=reset_pin)

WIDTH = 168
HEIGHT = 130
BORDER = 5

display = ST7735R(display_bus, width=WIDTH, height=HEIGHT, bgr=True)
display.rotation = 1

splash = displayio.Group()
display.root_group = splash

color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0x000000

bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

big_font = bitmap_font.load_font("fonts/Arial-16.bdf")
counter_text = "0"
counter_area = label.Label(big_font, text=counter_text, color=0xFFFFFF, x=0, y=60)

counter_area.x = (WIDTH - counter_area.bounding_box[2]) // 2
splash.append(counter_area)

num_pixels = 5
pixels = neopixel.NeoPixel(board.GP2, num_pixels)
pixels.brightness = 0.3

animation_speed = 0.01
color_offset = 0

green_shades = [
    (0, 255, 0),
    (0, 200, 50),
    (50, 255, 100),
    (0, 180, 0),
    (20, 255, 80),
    (0, 220, 30),
    (10, 255, 20),
    (0, 160, 0),
]

current_shade_index = 0

def interpolate_color(color1, color2, factor):
    r1, g1, b1 = color1
    r2, g2, b2 = color2
    r = int(r1 + (r2 - r1) * factor)
    g = int(g1 + (g2 - g1) * factor)
    b = int(b1 + (b2 - b1) * factor)
    return (r, g, b)

actions = ["Dodge Left!", "Dodge Right!", "Jump Up!", "Duck Down!"]
current_action = random.choice(actions)
last_action_time = time.monotonic()

fail = False

while True:
    if fail:
        counter_area.text = "FAIL"
        counter_area.x = (WIDTH - counter_area.bounding_box[2]) // 2
        for i in range(num_pixels):
            pixels[i] = (255, 0, 0)
        pixels.show()
        time.sleep(0.01)
        continue

    now = time.monotonic()

    x, y, z = adxl345.acceleration

    DODGE_LEFT = x < -5
    DODGE_RIGHT = x > 5
    JUMP_UP = z < 7
    DUCK_DOWN = z > 7

    if 'ACTION_TIMEOUT' not in globals():
        ACTION_TIMEOUT = 10.0
    if 'SLEEP_INTERVAL' not in globals():
        SLEEP_INTERVAL = 0.03
    if 'success_count' not in globals():
        success_count = 0

    if current_action == "Dodge Left!":
        if DODGE_LEFT:
            success_count += 1
            if success_count % 5 == 0:
                ACTION_TIMEOUT = max(3.0, ACTION_TIMEOUT - 1.0)
                SLEEP_INTERVAL = max(0.01, SLEEP_INTERVAL - 0.005)
            current_action = random.choice(actions)
            last_action_time = now
        elif now - last_action_time >= ACTION_TIMEOUT:
            fail = True
            continue
    elif current_action == "Dodge Right!":
        if DODGE_RIGHT:
            success_count += 1
            if success_count % 5 == 0:
                ACTION_TIMEOUT = max(3.0, ACTION_TIMEOUT - 1.0)
                SLEEP_INTERVAL = max(0.01, SLEEP_INTERVAL - 0.005)
            current_action = random.choice(actions)
            last_action_time = now
        elif now - last_action_time >= ACTION_TIMEOUT:
            fail = True
            continue
    elif current_action == "Jump Up!":
        if JUMP_UP:
            success_count += 1
            if success_count % 5 == 0:
                ACTION_TIMEOUT = max(3.0, ACTION_TIMEOUT - 1.0)
                SLEEP_INTERVAL = max(0.01, SLEEP_INTERVAL - 0.005)
            current_action = random.choice(actions)
            last_action_time = now
        elif now - last_action_time >= ACTION_TIMEOUT:
            fail = True
            continue
    elif current_action == "Duck Down!":
        if DUCK_DOWN:
            success_count += 1
            if success_count % 5 == 0:
                ACTION_TIMEOUT = max(3.0, ACTION_TIMEOUT - 1.0)
                SLEEP_INTERVAL = max(0.01, SLEEP_INTERVAL - 0.005)
            current_action = random.choice(actions)
            last_action_time = now
        elif now - last_action_time >= ACTION_TIMEOUT:
            fail = True
            continue

    counter_area.text = current_action
    counter_area.x = (WIDTH - counter_area.bounding_box[2]) // 2

    current_shade = green_shades[current_shade_index]
    next_shade = green_shades[(current_shade_index + 1) % len(green_shades)]
    interpolated_color = interpolate_color(current_shade, next_shade, color_offset)

    for i in range(num_pixels):
        pixels[i] = interpolated_color
    pixels.show()

    color_offset += animation_speed
    if color_offset >= 1.0:
        color_offset = 0
        current_shade_index = (current_shade_index + 1) % len(green_shades)

    time.sleep(SLEEP_INTERVAL)
