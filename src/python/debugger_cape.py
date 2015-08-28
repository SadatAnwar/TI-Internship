# coding=utf-8
#
#
# This file is intended to act as a liberary for the functions available on the Bench Debugger Cape
# it is not intended to work as a script.
# author Sadat Anwar 2015 Texas Instruments
import time
from global_variables import *

log = logging.getLogger(__name__)
try:
    import bbio
except ImportError:
    pass


class DAC(object):
    """Class for using the SPI interface on the beagle bone to communicate with the
    DAC on the bench debugger"""
    # variable Make sure only one of the 4 channels can be passed as the first byte of data
    # self.channel = enum(A=0x00, B=0x02, C=0x04, D=0x06)
    byte_0 = 0  # LSBs
    byte_1 = 0  # MSBs
    byte_2 = 0  # Control byte

    def __init__(self, channel, freq=1000000, control=1):
        # initialize the SPI 0 interface
        self.channel = channel
        ch = 0
        if freq > 15000000:
            self.freq = 15000000
        if freq < 500000:
            self.freq = 500000
        else:
            self.freq = freq
        self.dac = bbio.SPI0
        if channel != 1 and channel != 2 and channel != 3 and channel != 4:
            raise Exception("Invalid channel specified")
        else:
            if channel == 1:
                ch = 0
            if channel == 2:
                ch = 2
            if channel == 3:
                ch = 4
            if channel == 4:
                ch = 6

            self.byte_2 = (control << 4) + ch

    def voltage_to_bits(self, voltage, range_min=0, range_max=2.5):
        """

        :rtype : bytearray
        """
        numerical = voltage * (0xFFFF / (range_max - range_min))
        if numerical > 0xFFFF:
            numerical = 0xFFFF
        self.byte_1 = int(numerical) >> 8
        self.byte_0 = int(numerical) & 0x00FF

    def setVoltage(self, voltage):
        self.voltage_to_bits(voltage)
        bytes_to_write = [self.byte_2, self.byte_1, self.byte_0]
        log.debug('Voltage set on DAC-%s: %s v' % (self.channel, voltage))
        # Initiate the SPI communication channel
        self.dac.begin()
        self.dac.setClockMode(0, 1)
        # configure the clock frequency
        self.dac.setMaxFrequency(0, self.freq)
        self.dac.write(0, bytes_to_write)
        self.dac.end()


def twos_comp(val, bits):
    """compute the 2's compliment of int value val"""
    if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
        val -= 1 << bits  # compute negative value
    return val


def xfrange(start, stop, step):
    while start < stop:
        yield start
        start += step


class ADC:
    def __init__(self, channel, freq=500000, vRef=1.525, internalClock=True):
        # initialize the SPI1 interface
        self.vRef = vRef
        self.voltageThreshold = 200 / 1000  # (200 mV)
        # the Vref is set by ch1 of the dac
        d1 = DAC(1)
        d1.setVoltage(self.vRef)

        if freq > 15000000:
            self.freq = 15000000
        if freq < 50000:
            self.freq = 50000
        else:
            self.freq = freq
        # Assign the control to class variable
        self.adc = bbio.SPI1

        # set the control byte (first set bit 7 to 1)
        self.controlByte = 1 << 3
        if channel != 1 and channel != 2 and channel != 3 and channel != 4:
            raise Exception("Invalid channel specified")
        else:
            if channel == 1:
                ch = 1
                self.LSB = bbio.GPIO0_27
                self.MSB = bbio.GPIO2_1
            if channel == 2:
                ch = 5
                self.LSB = bbio.GPIO0_27
                self.MSB = bbio.GPIO2_1
            if channel == 3:
                ch = 2
                self.LSB = bbio.GPIO0_27
                self.MSB = bbio.GPIO2_1
            if channel == 4:
                ch = 6
                self.LSB = bbio.GPIO0_27
                self.MSB = bbio.GPIO2_1
        self.controlByte += ch

        if internalClock:
            mode = 6
        else:
            mode = 7

        self.controlByte = self.controlByte << 4 | mode
        log.debug('Control byte for ADC-%s: %s' % (channel, hex(self.controlByte)))

    def readVoltage(self, samples=10):
        avgVolt = 0
        # basic configurations for SPI communication
        self.adc.begin()
        self.adc.setClockMode(0, 0)
        # configure the clock frequency
        self.adc.setMaxFrequency(0, self.freq)
        for x in range(0, samples):
            controlInput = self.adc.transfer(0, [self.controlByte])
            if controlInput[0] != 0:
                log.error('Control data write returned non zero response :%s ' % controlInput[0])
            time.sleep(0.001)
            inputData = self.adc.transfer(0, [0x00, 0x00, 0x00])
            sampleVolt = self.convertToVoltage(inputData)
            avgVolt += sampleVolt
        self.adc.end()
        avgVolt /= samples
        return avgVolt

    def convertToVoltage(self, input):
        """We convert the data received into valid voltages. The data is
        represented as 16bits 2's compliment, with first bit as sign.
        also, the first bit of the data received is always a 0, so """
        digitalData = input[0] << 9 | input[1] << 1 | input[2] >> 7
        digitalData &= 0xFFFF
        signedInt = twos_comp(digitalData, 16)
        positiveSignedData = signedInt + 0x8000
        volts = positiveSignedData * ((2 * self.vRef) / 0xFFFF)
        return volts

    def selectResistance(self, resistance=5):
        bbio.pinMode(self.LSB, bbio.OUTPUT)
        bbio.pinMode(self.MSB, bbio.OUTPUT)
        if resistance == 5:
            bbio.digitalWrite(self.LSB, bbio.HIGH)
            bbio.digitalWrite(self.MSB, bbio.HIGH)
        elif resistance == 105:
            bbio.digitalWrite(self.LSB, bbio.HIGH)
            bbio.digitalWrite(self.MSB, bbio.LOW)
        elif resistance == 1005:
            bbio.digitalWrite(self.LSB, bbio.LOW)
            bbio.digitalWrite(self.MSB, bbio.HIGH)
        else:
            bbio.digitalWrite(self.LSB, bbio.LOW)
            bbio.digitalWrite(self.MSB, bbio.LOW)
            resistance = 0
        return resistance

    def readCurrent(self, r=5, gain=50, samples=10):
        resistance = self.selectResistance(r)
        volt = self.readVoltage(samples)
        if volt > self.voltageThreshold or r == 1005:
            volt /= gain
            current = volt / resistance
            log.info('Current with %sohm :%sA' % (r, current))
            return current
        else:
            if r == 5:
                return self.readCurrent(r=105)
            elif r == 105:
                return self.readCurrent(r=1005)


if __name__ == '__main__':
    # test
    dac2 = DAC(2)
    adc1 = ADC(4, freq=2000000)
    for v in xfrange(0, 2.6, 0.10):
        dac2.setVoltage(v)
        volt1 = adc1.readVoltage()
        current1 = adc1.readCurrent()
        log.debug('Voltage on DAC set to:%s v : Voltage on ADC:%s v' % (v, volt1))
