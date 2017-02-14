import time
import serial as ser

class _numato_gpio:
    def __init__(self, com_port_number):
        # Dummy baud rate used as USB to RS232 ignores it.
        self._ser = ser.Serial(com_port_number, baud=9600)
        self._io_num = None
        self._adc_num = None

    def _write(self, string):
        return self._ser(string.encode())

    def _read(self):
        return str(self._ser.read())

    def _write_read(self, string):
        self._write(string)
        r = self._read()
        return r

    def read_pin(self, pin_number):
        return int(self._read())

    def write_pin(self, state):
        state = int(state)
        assert state in (0, 1)
        return self._write(state)

    def get_version(self):
        return self._write_read('ver')

    def get_id(self):
        return self._write_read('id get')

    def set_id(self, name):
        name = str(name)
        assert len(name) < 8
        name = name.rjust(8, '0')
        self.set_id(name)
        return self.get_id()

    def adc_read(self, channel, average_pts=1, average_delay_sec=0):
        channel = int(channel)
        assert 0 <= channel <= self._adc_num - 1
        if average > 1:
            volt_bits = 0
            for _ in range(average):
                volt_bits += int(self._write_read('adc read %i' % channel))
                if average_delay_sec:
                    time.sleep(average_delay_sec)
            volt_bits /= average_pts
        else:
            volt_bits = int(self._write_read('adc read %i' % channel))
        return volt_bits

    def adc_read_voltage(self, channel, average_pts=1, average_delay_sec=0):
        channel = int(channel)
        volt_bits = self.adc_read(channel, average_pts, average_delay_sec)
        volt = volt_bits / 1024. * 5.
        return volt

    def gpio_set(self, pin):
        pin = int(pin)
        assert 0 <= pin <= self._io_num
        self._write_read('gpio set %i' % pin)
        return self.gpio_state(pin)

    def gpio_clear(self, pin):
        pin = int(pin)
        assert 0 <= pin <= self._io_num
        self._write_read('gpio clear %i' % pin)
        return self.gpio_state(pin)

    def gpio_read(self, pin):
        pin = int(pin)
        assert 0 <= pin <= self._io_num
        gpio_state = bin(self._write_read('gpio read %i' % pin))
        return gpio_state

    def gpio_readall(self):
        self.gpio_io_direction(0x00)
        byte_str = self._write_read('gpio readall')
        pin_state_list = [bool(int(i)) for i in byte_str[::-1]]
        return pin_state_list

    def gpio_writeall(self, state):
        self.gpio_io_direction(0xff)
        state = int(state)
        assert 0 <= state <= 255
        self._write('gpio writeall %s' % hex(state)[2:])
        return self.gpio_readall()

    def gpio_io_mask_set(self, masked_channel_list):
        # Masked channels will not be affected by
        # `writeall` and `iodir` commands.
        mask = 0xff
        for channel in masked_channel_list:
            assert 0 <= channel <= self._io_num - 1
            mask &= ~(1 << channel)
        self._write('gpio iomask %s' % hex(mask)[2:])
        return mask

    def gpio_io_direction(self, direction):
        direction = int(direction)
        assert 0 <= direction <= 255
        self._write('gpio iodir %s' % hex(direction)[2:])
        return direction

class numato_gpio_8(_numato_gpio):
    def __init__(self, com_port_number):
        numato_gpio.__init__(self, com_port_number)
        self._io_num = 8
        self._adc_num = 6
