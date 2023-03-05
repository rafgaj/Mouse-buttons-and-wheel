# Mouse-buttons-and-wheel
## Description
![Rings](/images/rings.png)

HID controller with 4 buttons. There are: left mouse click, right mouse click, wheel up and wheel down as buttons. Built on the basis of the "Seeed Studio XIAO nRF52840" microcontroller and programmed in CircuitPython. Cotroller is connecting with PC by Bluetooth.

The code was created for the need of easy mouse control with VR headset. Microcontroller is a core part of Ring made of according the [instruction](https://www.instructables.com/Ring-With-Mouse-Buttons-Wheel/).

## Pre-work with the microcontroller
1. Download CircuitPython .uf2 dedicated loader from [here](https://circuitpython.org/board/Seeed_XIAO_nRF52840_Sense/).
2. Installing CircuitPython on the microcontroller according the [instruction](https://learn.adafruit.com/welcome-to-circuitpython).
3. Add CircuitPython library files. Can be download from the [official libraries](https://circuitpython.org/libraries) on the CircuitPython website. Required libriaries are:
    - /adafruit_ble
    - /adafruit_ble_adafruit
    - /adafruit_bluefruit_connect
    - /adafruit_bus_device
    - /adafruit_hid
    - /adafruit_lsm6ds
    - /adafruit_register
    - adafruit_debouncer.mpy
    - adafruit_ticks.mpy
    - simpleio.mpy

    Unzip downloaded library file and copy required files onto the CIRCUITPY drive into the /lib directory.

    >**Note**: The libraries are included in the release files but may be out of date. If you don't care about the latest versions, you can skip this step.
4. To have control with battery charging current download the latest version of *[seeed_xiao_nrf52840.py](https://pypi.org/project/circuitpython-seeed-xiao-nrf52840/)* or take it from release and place directly on the CIRCUITPY drive. 
    >**Note**: *seeed_xiao_nrf52840.py* is included in the release files but may be out of date. If you don't care about the latest versions, you can skip this step.

## Programming the microcontroller
Copy the files: *code.py* onto the CIRCUITPY directly. Respectively for the left and right Ring. Reconnect device. Will be visible for Bluetooth and ready to connect.