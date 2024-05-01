import os
import time
import board
import digitalio
import supervisor
import storage
from adafruit_hid.mouse import Mouse
from adafruit_debouncer import Button
from digitalio import DigitalInOut, Direction, Pull
from seeed_xiao_nrf52840 import Battery

# imports needed for bluetooth
import adafruit_ble
from adafruit_ble.advertising import Advertisement
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.standard.hid import HIDService
from adafruit_ble.services.standard.device_info import DeviceInfoService

from config import config as hand_config

# Logging Levels
LLVL={'debug': 0, 'info': 1, 'warn': 2, 'error':3}

# config defaults
config = {
    'charge_current': Battery.CHARGE_50MA,
    'log_level': 'info',
    'log_to_disk': True,
    # Scroll settings
    'sp_initial': 0.2,
    'sp_accel': 0.02,
    'sp_max': 0.03,
}
config.update(hand_config)

# Set up logfile - rotate old ones.
logfile_handle = None
if config['log_to_disk']:
    try:
        storage.remount("/",readonly=False)
        if "logfile.log" in os.listdir():
            os.rename("logfile.log","logfile.log.0")
        for i in reversed(range(3)):
            if f"logfile.log.{i}" in os.listdir():
                os.rename(f"logfile.log.{i}",f"logfile.log.{i+1}")
        logfile_handle = open("logfile.log","w")
    except (OSError, RuntimeError):
        pass

def logtime():
    cur_time = time.localtime()
    return f"{cur_time.tm_hour:02d}:{cur_time.tm_min:02d}:{cur_time.tm_sec:02d}"

# function to log a message to console, and if possible
# to a file on disk
def log(level,message):
    if LLVL[level] >= LLVL[config['log_level']]:
        log_line = logtime()+" "+message
        print(log_line)
        if logfile_handle is not None:
            logfile_handle.write(log_line+"\n")
            logfile_handle.flush()

# try to capture failures. - if the program crashes the backtrace
# will be logged when the program restarts.
supervisor.set_next_code_file(filename='code.py', reload_on_error=True)
backtrace = supervisor.get_previous_traceback()
if backtrace is not None:
    log('error',"Previous run crashed.. backtrace follows...")
    log('error',backtrace)

# set LEDs
blue_led = DigitalInOut(board.LED_BLUE)
blue_led.direction = Direction.OUTPUT
green_led = DigitalInOut(board.LED_GREEN)
green_led.direction = Direction.OUTPUT
red_led = DigitalInOut(board.LED_RED)
red_led.direction = Direction.OUTPUT
blue_led.value = True  # turn off LED
green_led.value = True  # turn off LED
red_led.value = True  # turn off LED

# Battery set
battery = Battery()
log('info',f"Charge status (True-full charged, False-otherwise): {battery.charge_status}")
log('info',f"Voltage: {battery.voltage}V")
battery.charge_current = config['charge_current']  # Setting charge current to high
log('info',f"Charge current (0-50mA, 1-100mA): {battery.charge_current}")

# setup bluetooth
hid = HIDService()
device_info = DeviceInfoService(software_revision=adafruit_ble.__version__)
advertisement = ProvideServicesAdvertisement(hid)
advertisement.appearance = 961
scan_response = Advertisement()
scan_response.complete_name = config['complete_name']
ble = adafruit_ble.BLERadio()

# set buttons
left_BTN = digitalio.DigitalInOut(config['left_btn'])
left_BTN.direction = Direction.INPUT
left_BTN.pull = Pull.UP
right_BTN = digitalio.DigitalInOut(config['right_btn'])
right_BTN.direction = Direction.INPUT
right_BTN.pull = Pull.UP
scrollup_BTN = digitalio.DigitalInOut(config['scrollup_btn'])
scrollup_BTN.direction = Direction.INPUT
scrollup_BTN.pull = Pull.UP
scrolldown_BTN = digitalio.DigitalInOut(config['scrolldown_btn'])
scrolldown_BTN.direction = Direction.INPUT
scrolldown_BTN.pull = Pull.UP

# set mouse
mouse = Mouse(hid.devices)
i = 1

def battery_leds():
    # set green/orange/red LED based on battery state.
    # 3.7V lithium ion battery can be considered dead (completely discharged) at a voltage of 3.4V
    volts = battery.voltage
    if volts > 3.7:
        green_led.value = False  # turn off LED
    elif volts > 3.5:
        green_led.value = False
        red_led.value = False
    else:
        # below 3.5
        red_led.value = False

def leds_off():
    blue_led.value = True  # reset LED status
    green_led.value = True  # reset LED status
    red_led.value = True  # reset LED status

scroll_sleep = config['sp_initial']

while True:
    if not ble.connected:
        ble.start_advertising(advertisement, scan_response)
        log('info',"Advertising...")
        while not ble.connected:
            log('info',"Connecting...")
            blue_led.value = False
            time.sleep(0.5)
            blue_led.value = True
            time.sleep(0.5)
            pass
        # Now we're connected
        ble.stop_advertising()
        log('info',f"Connected {ble.connections}")

    while ble.connected:

        if i == 80000:
            blue_led.value = False
            time.sleep(0.1)
            i = 0
        elif i == 40000:
            battery_leds()
            time.sleep(0.1)
            i = i+1
        else:
            leds_off()
            i = i+1

        if left_BTN.value is False:
            # mouse.click(Mouse.LEFT_BUTTON)
            mouse.press(Mouse.LEFT_BUTTON)
            while left_BTN.value is False:
                pass
            mouse.release(Mouse.LEFT_BUTTON)
            log('info',"Left Button is pressed")
            # blue_led.value = True
            # green_led.value = False
            # time.sleep(0.2)  # sleep for debounce
        elif right_BTN.value is False:
            # mouse.click(Mouse.RIGHT_BUTTON)
            mouse.press(Mouse.RIGHT_BUTTON)
            while right_BTN.value is False:
                pass
            mouse.release(Mouse.RIGHT_BUTTON)
            log('info',"Right Button is pressed")
            # blue_led.value = True
            # green_led.value = False
            # time.sleep(0.2)  # sleep for debounce
        elif not scrollup_BTN.value:
            mouse.move(wheel=1)
            log('info',"Up Button is pressed")
            # blue_led.value = True
            # green_led.value = False
            time.sleep(scroll_sleep)  # sleep for debounce
            if scroll_sleep > config['sp_max']:
                scroll_sleep -= config['sp_accel']
        elif not scrolldown_BTN.value:
            mouse.move(wheel=-1)
            log('info',"Down Button is pressed")
            # blue_led.value = True
            # green_led.value = False
            time.sleep(scroll_sleep)  # sleep for debounce
            if scroll_sleep > config['sp_max']:
                scroll_sleep -= config['sp_accel']
        else:
            if scroll_sleep != config['sp_initial']:
                log('info',"scroll_sleep reset")
                scroll_sleep = config['sp_initial']
    log('info','Not Connected (lost connection)')
    # ble.start_advertising(advertisement)

