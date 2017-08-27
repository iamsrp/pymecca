#!/usr/bin/python
#
# Simple stuff to control a Meccanoid
#

# Requires:
#  apt-get install python-bluez
#  apt-get install ipython
#  apt-get install python-dev
#  pip install pygatt

from pygatt.exceptions import NotConnectedError

import bluetooth
import pygatt

# ----------------------------------------------------------------------

# The servo IDs, some are unused as yet
UNKNOWN0_SERVO       = 0
RIGHT_ELBOW_SERVO    = 1
RIGHT_SHOULDER_SERVO = 2
LEFT_SHOULDER_SERVO  = 3
LEFT_ELBOW_SERVO     = 4
UNKNOWN5_SERVO       = 5
UNKNOWN6_SERVO       = 6
UNKNOWN7_SERVO       = 7

# The handle to use when sending commands
_HANDLE = 0x001f

# ----------------------------------------------------------------------

class Meccanoid(object):
    """
    Simple class for controlling the Meccanoid
    """
    def __init__(self):
        """
        Constructor.
        """
        super(Meccanoid, self).__init__()

        self._gatt = pygatt.GATTToolBackend()
        self._gatt.start()
        self._device = None

        # These are stateful so we remember them and mutate accordingly
        self._servos = \
            [0x08,
             0x7f, 0x80, 0x00, 0xff, 0x80, 0x7f, 0x7f, 0x7f,
             0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01, 0x01]
        self._servo_lights = \
            [0x0c,
             0x00, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04,
             0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x04, 0x00]
        self._chest_lights = \
            [0x1c,
             0x00, 0x00, 0x00, 0x00,
             0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        # These numbers make it yawn and say "I'm awake", and then
        # waggle its arms about
        self._im_awake =\
            (0x19, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d, 0x1d)
        

    def connect(self, address='c4:be:84:d4:68:1b'):
        """
        Connect to the Meccanoid at the given Bluetooth address.

        You can find it by doing:
            sudo hcitool lescan
        at the command line.
        """

        if self._device is None:
            # Connect to it
            self._device = self._gatt.connect(address)

            # Send a wheel move of zero to make the meccanoid see us
            self.move(0, 0)

            # Say "I'm awake"
            self._send(self._im_awake)

            # Put arms into their start state
            self._send(self._servos)

            # Set the lights to blue
            self.eye_lights(0x0, 0x0, 0x7)


    def disconnect(self):
        """
        Disconnect from the Meccanoid.
        """
        if self._device is not None:
            self._device.disconnect()
            self._device = None


    def servo(self, servo, value):
        """
        Set a servo value.
        
        The servo numbers are constants in this module.
        The value is between 0x00 and 0xff.
        """

        servo = int(servo)

        if 0 <= servo and servo <= 7:
            # Cap to a byte
            value = self._cap(int(value))

            # These guys are reversed, handle that for the user
            if (servo == LEFT_SHOULDER_SERVO or
                servo == RIGHT_ELBOW_SERVO) and value != 0x80:
                value = 0xff - value

            # Set the values
            self._servos[servo + 1] = value

        else:
            raise ValueError("Bad servo index: %s" % servo)

        self._send(self._servos)


    def servo_light(self, servo, value):
        """
        Set the servo light to a given colour.
        """

        if value == 'black' or value == 'off':
            value = 0x00
        elif value == 'red':
            value = 0x01
        elif value == 'green':
            value = 0x02
        elif value == 'yellow':
            value = 0x03
        elif value == 'blue':
            value = 0x04
        elif value == 'magenta':
            value = 0x05
        elif value == 'cyan':
            value = 0x06
        elif value == 'white' or value == 'on':
            value = 0x07
        else:
            raise ValueError('Unknown colour for servo: "%s"' % value)

        if 0 <= servo and servo <= 7:
            self._servo_lights[servo + 1] = value

        else:
            raise ValueError("Bad servo index: %s" % servo)

        self._send(self._servo_lights)


    def chest_light(self, light, on):
        """
        Set the on/off state of a chest light.

        The light is a value between 0 and 3.
        """

        if 0 <= light and light <= 3:
            if on:
                value = 0x01
            else:
                value = 0x00

            self._chest_lights[light + 1] = value
                
        else:
            raise ValueError("Bad light index: %s" % light)

        self._send(self._chest_lights)


    def move(self, right_speed=0x00, left_speed=0x00):
        """
        Move the wheels. The speed values are in the range [-255, 255], where a 
        negative value means "backwards".
        """

        # By default do nothing
        right_dir = 0x00
        left_dir  = 0x00

        # Make your move
        if right_speed > 0:
            right_dir   = 0x01
            right_speed = self._cap(right_speed)
        else:
            right_dir   = 0x02
            right_speed = self._cap(-right_speed)

        if left_speed > 0:
            left_dir   = 0x01
            left_speed = self._cap(left_speed)
        else:
            left_dir   = 0x02
            left_speed = self._cap(-left_speed)

        # Send the command
        self._send((0x0d, left_dir, right_dir, int(left_speed), int(right_speed),
                    0xff, 0xff, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00))


    def eye_lights(self, r, g, b):
        """
        Set the eye lights to a specific colour. RGB values between 0 and 7.
        """

        r = int(min(0x7, max(0x0, r)))
        g = int(min(0x7, max(0x0, g)))
        b = int(min(0x7, max(0x0, b)))

        self._send((0x11, 0x00, 0x00,
                    g << 3 | r,
                    b,
                    0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00))


    def _send(self, values):
        """
        Send a command to the unit.
        """

        if self._device is None:
            raise NotConnectedError()

        try:
            checksum = 0
            for v in values:
                checksum += v

            payload = tuple(values) + ((checksum >> 8) & 0xff, checksum & 0xff)

            self._device.char_write_handle(_HANDLE, payload)

        except NotConnectedError:
            self._device = None
            raise


    def _cap(self, value):
        """
        Cap between 0x00 and 0xff.
        """
        return max(0x00, min(0xff, value))
