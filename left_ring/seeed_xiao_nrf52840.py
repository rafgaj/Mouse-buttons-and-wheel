# SPDX-FileCopyrightText: 2017 Scott Shawcroft, written for Adafruit Industries
# SPDX-FileCopyrightText: Copyright (c) 2022 Phil Underwood for Underwood Underground
#
# SPDX-License-Identifier: MIT
"""
`seeed_xiao_nrf52840`
================================================================================

Provides access to onboard battery management (and accelerometer and microphone for
the Sense model)


* Author(s): Phil Underwood

Implementation Notes
--------------------

**Hardware:**

* `Seeed Xiao nRF52840 (Sense)
  <https://www.seeedstudio.com/Seeed-XIAO-BLE-Sense-nRF52840-p-5253.html>`_

**Software and Dependencies:**

* Adafruit CircuitPython firmware for the supported boards:
  https://circuitpython.org/downloads

* Adafruit's LSM6DS library: https://github.com/adafruit/Adafruit_CircuitPython_LSM6DS
"""

import time

import board
import busio
import digitalio
import analogio
from audiobusio import PDMIn
import microcontroller

from adafruit_lsm6ds.lsm6ds3 import LSM6DS3

try:
    from circuitpython_typing import WriteableBuffer
except ImportError:
    pass


class IMU(LSM6DS3):
    """
    IMU on Seeed XIAO nRF52840 Sense (only available on Sense models).
    This is an LSM6DS3 chip, and provides accelerometer and gyro readings.
    See https://docs.circuitpython.org/projects/lsm6dsox/en/latest/api.html for more details
    """

    def __init__(self):
        """
        Create an IMU instance. There are no arguments needed
        """
        # turn on IMU
        self.pwr_pin = digitalio.DigitalInOut(board.IMU_PWR)
        self.pwr_pin.direction = digitalio.Direction.OUTPUT
        self.pwr_pin.value = True
        # wait 50ms for device to turn on (datasheet states typical 35ms)
        time.sleep(0.05)

        # set up i2c
        self.i2c_bus = busio.I2C(board.IMU_SCL, board.IMU_SDA)

        # finally initialise self
        super().__init__(self.i2c_bus, address=0x6A)

    def deinit(self) -> None:
        """
        Turn off device and release resources
        """
        self.pwr_pin.value = False
        self.pwr_pin.deinit()
        self.i2c_bus.deinit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()


class Mic(PDMIn):
    """
    On-board  Microphone for Seeed XIAO nRF52840 Sense. Only available on Sense
    boards
    """

    def __init__(self, oversample: int = 64):
        """Create a `Mic` object. This allows you to record audio signals from the onboard
        microphone. The sample rate is fixed at 16000 and the bit depth is fixed at 16

        :param int oversample: Number of single bit samples to decimate into a
          final sample. Must be divisible by 8. Default is 64

        Record 16-bit unsigned samples to buffer::

          import audiobusio
          import board

          # Prep a buffer to record into. The array interface doesn't allow for
          # constructing with a set size so we append to it until we have the size
          # we want.
          b = array.array("H")
          for i in range(200):
              b.append(0)
          with Mic(sample_rate=16000) as mic:
              mic.record(b, len(b))"""

        self.pwr_pin = digitalio.DigitalInOut(board.MIC_PWR)
        self.pwr_pin.direction = digitalio.Direction.OUTPUT
        self.pwr_pin.value = True

        super().__init__(
            board.PDM_CLK,
            board.PDM_DATA,
            sample_rate=16000,
            bit_depth=16,
            mono=True,
            oversample=oversample,
            startup_delay=0.01,
        )

    def record(self, destination: WriteableBuffer, destination_length: int) -> None:
        # pylint: disable=useless-super-delegation
        # Just here so we can generate documentation
        """Records destination_length bytes of samples to destination. This is
        blocking.

        An IOError may be raised when the destination is too slow to record the
        audio at the given rate. For internal flash, writing all 1s to the file
        before recording is recommended to speed up writes.

        :return: The number of samples recorded. If this is less than ``destination_length``,
          some samples were missed due to processing time."""
        return super().record(destination, destination_length)

    def deinit(self):
        """
        Turn off the microphone and release all resources
        """
        super().deinit()
        self.pwr_pin.value = False
        self.pwr_pin.deinit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()


class Battery:
    """
    Seeed XIAO nRF52840 battery management functions
    """

    CHARGE_50MA: int = 0
    CHARGE_100MA: int = 1

    def __init__(self):
        """
        Create a Battery management object
        """
        self._charge_status = digitalio.DigitalInOut(board.CHARGE_STATUS)
        self._charge_status.direction = digitalio.Direction.INPUT
        self._charge_status.pull = digitalio.Pull.UP

        self._charge_speed = digitalio.DigitalInOut(microcontroller.pin.P0_13)
        self._charge_speed.direction = digitalio.Direction.INPUT

        self._read_batt_enable = digitalio.DigitalInOut(board.READ_BATT_ENABLE)
        self._read_batt_enable.direction = digitalio.Direction.INPUT

        self._vbat = analogio.AnalogIn(board.VBATT)

    @property
    def charge_status(self) -> bool:
        """
        Battery charge status; `True` if Battery fully charged, `False` otherwise
        """
        return not self._charge_status.value

    @property
    def voltage(self) -> float:
        """
        Battery voltage in volts
        """
        # set READ_BATT_ENABLE to sink to allow voltage reading
        self._read_batt_enable.direction = digitalio.Direction.OUTPUT
        self._read_batt_enable.value = False
        # wait a little bit to allow voltage to settle
        time.sleep(0.003)
        # we need to take 10 readings in quick succession. The nrf port
        # selects a very short acquisition time, which is not enough with
        # a really high impedance input like we are using, so if we take several
        # readings, the later ones will be more accurate
        for _i in range(9):
            _ = self._vbat.value
        value = (self._vbat.value / 65535.0) * self._vbat.reference_voltage * 3.1
        self._read_batt_enable.direction = digitalio.Direction.INPUT
        return value

    @property
    def charge_current(self) -> int:
        """
        Battery charge current, either Battery.CHARGE_50MA or Battery.CHARGE_100MA
        """
        if self._charge_speed.direction == digitalio.Direction.INPUT:
            return self.CHARGE_50MA
        return self.CHARGE_100MA

    @charge_current.setter
    def charge_current(self, value: int):
        if value == self.CHARGE_50MA:
            self._charge_speed.direction = digitalio.Direction.INPUT
        elif value == self.CHARGE_100MA:
            self._charge_speed.direction = digitalio.Direction.OUTPUT
            self._charge_speed.value = False
        else:
            raise ValueError("value must be either CHARGE_50MA or CHARGE_100MA")

    def deinit(self) -> None:
        """
        Release all resources
        """
        self._charge_status.deinit()
        self._charge_speed.deinit()
        self._read_batt_enable.deinit()
        self._vbat.deinit()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.deinit()


__version__ = "v1.0.1"
__repo__ = "https://github.com/furbrain/CircuitPython_seeed_xiao_nRF52840.git"
