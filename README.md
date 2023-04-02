Barrier Client for ESP32S3
==========================

This is a port of the [Barrier](https://github.com/debauchee/barrier) client to the ESP32S3 written in [CircuitPython](https://circuitpython.org/).

Thanks to [Noskcaj19](https://github.com/Noskcaj19) for the idea and the initial implementation at [https://github.com/Noskcaj19/hardware-kvm](https://github.com/Noskcaj19/hardware-kvm).

This project is a prototype so the performance is not great, you can feel some lags even when pressing a single key. 

The development and test are done one [M5Atom S3 Lite](http://docs.m5stack.com/en/core/AtomS3%20Lite), but any other ESP32-S3 based board should work.

Installation
------------

1. Download and flash the latest [CircuitPython](https://adafruit-circuit-python.s3.amazonaws.com/index.html?prefix=bin/m5stack_atoms3_lite/) to your board.
2. After the reset, the device appears as a USB disk on the computer, copy all files under `src` to its root directory.
3. Edit `secret.py` and set necessary parameters, includes WiFi, barrier server settings, and the screen name.
4. On Barrier server, make sure you've
    * Disable the "Enable SSL" option.
    * Disable the "Use relative mouse moves" option, (even though the mouse still won't work well.)
    * Add corresponding screen into Barrier server configuration, otherwise the server will reject the connection.
5. As the mouse still doesn't work properly, auto switching may also not work, so you may need to configure a hotkey to switch between screens on the Barrier server.

TODO:
- [ ] Mouse still doesn't quite work, looks we need the Absolute mode as USB device cannot get current cursor position.
- [ ] Many key mappings are still missing, namely macOs specific keys, e.g. LaunchPad and MissionControl.
- [ ] Screen size is hardcoded, as USB device cannot get current screen size.
- [ ] SSL support.
- [ ] Performance tuning.