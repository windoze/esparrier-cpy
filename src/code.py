import barrier

from secrets import secrets
from utils import *

# Initialize everything
initialize()

# Connect to the WiFi network
connect_to_wifi()

import usb_hid
from adafruit_hid.mouse import Mouse
mouse = Mouse(usb_hid.devices)

client = barrier.BarrierClient(server = secrets["SERVER"], port = secrets["PORT"], width = 2560, height = 1440, name = secrets["SCREEN_NAME"])
client.run()
