import board
import neopixel_write
import digitalio
import wifi
import socketpool
import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keyboard_layout_us import KeyboardLayoutUS
from adafruit_hid.keycode import Keycode
from adafruit_hid.mouse import Mouse

from key_codes import synergy_to_hid
from secrets import secrets

LED = None
POOL = None
MAX_BUFFER = 1024

mouse = Mouse(usb_hid.devices)
keyboard = Keyboard(usb_hid.devices)

server_button_state = bytearray(512)

def initialize():
    """
    Initialize everything that needs to be initialized.
    """
    
    # Initialize the LED.
    global LED
    LED = digitalio.DigitalInOut(board.NEOPIXEL)
    LED.direction = digitalio.Direction.OUTPUT

def connect_to_wifi():
    """
    Connect to the WiFi network.
    """
    set_led(255, 0, 0)  # Red
    print("Connecting to %s" % secrets["SSID"])
    wifi.radio.connect(secrets["SSID"], secrets["PASSWORD"])
    print("Connected to %s!" % secrets["SSID"])
    set_led(0, 0, 255)  # Blue
    global POOL
    POOL = socketpool.SocketPool(wifi.radio)

def set_led(r, g, b):
    """Set the LED to the given RGB values."""
    # M5Atom S3 Lite uses GRB order
    pixel_off = bytearray([g, r, b])
    neopixel_write.neopixel_write(LED, pixel_off)
    
def connect(host, port):
    print("Connecting to %s:%d" % (host, port))
    # server_ipv4 = ipaddress.ip_address(POOL.getaddrinfo(host, port)[0][4][0])
    s = POOL.socket(POOL.AF_INET, POOL.SOCK_STREAM)
    s.connect((host, port))
    print("Connected to %s:%d" % (host, port))
    set_led(0, 32, 0)  # Dim Green
    return s

def read_int(sock):
    return int.from_bytes(read_buf(sock, 4), "big")

def read_buf(sock, length):
    buffer = bytearray(length)
    received = 0
    if length > MAX_BUFFER:
        # Message too large, but we still need to drain it.
        buffer = bytearray(256)
        while received < length:
            chunk = sock.recv_into(buffer, min(256, length - received))
            received += chunk
        print("Message length %d is too large, discard the message." % length)
        return None
    while received < length:
        chunk = sock.recv_into(memoryview(buffer)[received:], length - received)
        received += chunk
    return buffer

def write_int(sock, value):
    return write_buf(sock, value.to_bytes(4, "big"))

def write_buf(sock, buffer):
    length = len(buffer)
    sent = 0
    while sent < length:
        sent += sock.send(buffer[sent:])
    return sent

def move_mouse_rel(x, y):
    mouse.move(x=x, y=y)
    pass

def mouse_wheel(x, y):
    pass

def mouse_down(button):
    if button==1:
        mouse.press(Mouse.LEFT_BUTTON)
    elif button==2:
        mouse.press(Mouse.MIDDLE_BUTTON)
    elif button==3:
        mouse.press(Mouse.RIGHT_BUTTON)
    else:
        print("Unknown mouse button: %d" % button)

def mouse_up(button):
    if button==1:
        mouse.release(Mouse.LEFT_BUTTON)
    elif button==2:
        mouse.release(Mouse.MIDDLE_BUTTON)
    elif button==3:
        mouse.release(Mouse.RIGHT_BUTTON)
    else:
        print("Unknown mouse button: %d" % button)

key_report = bytearray(6)

def key_down(id, modifier, button):
    key = synergy_to_hid(id)
    print("Key %d->%d down" % (id, key))
    if key == 0:
        return
    server_button_state[button] = key
    for n in range(6):
        if key_report[n] == 0:
            key_report[n] = key
            break
    # if server_button_state[button] == key:
    #     # Key already pressed
    #     return
    keyboard.press(*[c for c in key_report if c!=0])

def key_up(id, modifier, button):
    server_button_state[button] = 0
    key = synergy_to_hid(id)
    print("Key %d->%d up" % (id, key))
    if key == 0:
        return
    for n in range(6):
        if key_report[n] == key:
            key_report[n] = 0
            break
    keyboard.release(key)

