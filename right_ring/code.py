import time
import board
import digitalio
import supervisor
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
print(f"Charge status (True-full charged, False-otherwise): {battery.charge_status}")
print(f"Voltage: {battery.voltage}V")
battery.charge_current = battery.CHARGE_50MA  # Setting charge current to high
print(f"Charge current (0-50mA, 1-100mA): {battery.charge_current}")

# setup bluetooth
hid = HIDService()
device_info = DeviceInfoService(software_revision=adafruit_ble.__version__)
advertisement = ProvideServicesAdvertisement(hid)
advertisement.appearance = 961
scan_response = Advertisement()
scan_response.complete_name = "Right Mouse Ring"
ble = adafruit_ble.BLERadio()

# set buttons
# left_BTN_input = digitalio.DigitalInOut(board.D0)
# left_BTN_input.switch_to_input(digitalio.Pull.UP)
# left_BTN = Button(left_BTN_input)
# right_BTN_input = digitalio.DigitalInOut(board.D3)
# right_BTN_input.switch_to_input(digitalio.Pull.UP)
# right_BTN = Button(right_BTN_input)
left_BTN = digitalio.DigitalInOut(board.D0)
left_BTN.direction = Direction.INPUT
left_BTN.pull = Pull.UP
right_BTN = digitalio.DigitalInOut(board.D3)
right_BTN.direction = Direction.INPUT
right_BTN.pull = Pull.UP
scrollup_BTN = digitalio.DigitalInOut(board.D2)
scrollup_BTN.direction = Direction.INPUT
scrollup_BTN.pull = Pull.UP
scrolldown_BTN = digitalio.DigitalInOut(board.D1)
scrolldown_BTN.direction = Direction.INPUT
scrolldown_BTN.pull = Pull.UP

# set mouse
mouse = Mouse(hid.devices)

while True:
    ble.start_advertising(advertisement, scan_response)
    print("Advertising...")
    while not ble.connected:
        print("Connecting...")
        blue_led.value = False
        time.sleep(0.5)
        blue_led.value = True
        time.sleep(0.5)
        pass
    # Now we're connected
    ble.stop_advertising()
    print(f"Connected {ble.connections}")
    # print(ble.connections)

    while ble.connected:

        blue_led.value = False  # turn on BLUE LED
        green_led.value = True  # reset LED status
        red_led.value = True  # reset LED status

        # read buttons state
        # left_BTN.update()
        # right_BTN.update()

        if left_BTN.value is False:
            mouse.click(Mouse.LEFT_BUTTON)
            print("Left Button is pressed")
            blue_led.value = True
            green_led.value = False
            time.sleep(0.2)
        elif right_BTN.value is False:
            mouse.click(Mouse.RIGHT_BUTTON)
            print("Right Button is pressed")
            blue_led.value = True
            green_led.value = False
            time.sleep(0.2)
        elif not scrollup_BTN.value:
            mouse.move(wheel=1)
            print("Up Button is pressed")
            blue_led.value = True
            green_led.value = False
            time.sleep(0.1)
        elif not scrolldown_BTN.value:
            mouse.move(wheel=-1)
            print("Down Button is pressed")
            blue_led.value = True
            green_led.value = False
            time.sleep(0.1)
    ble.start_advertising(advertisement)
