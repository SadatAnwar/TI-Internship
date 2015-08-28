import time

__author__ = 'x0234668'
""" This class is going to drive all the jtag communications. It will take a list of binary files as in input
 this list should also contain the INPUT PRU bin and the reset PRU bin. The class will take care of """

import struct
import mmap
from global_variables import *

log = logging.getLogger(__name__)
try:
    import pypruss
    pyprussImport = True
except ImportError:
    pyprussImport = False
    pass


def powerUpJTAG():
    try:
        global JTAGPower
        """Function will power off the device"""
        GPIO0_offset = 0x44E07000
        GPIO0_size = 0x44E07fff - GPIO0_offset
        GPIO_OE = 0x134
        GPIO_SETDATAOUT = 0x194
        VCC = 1 << 23
        with open("/dev/mem", "r+b") as f:
            mem = mmap.mmap(f.fileno(), GPIO0_size, offset=GPIO0_offset)
        reg = struct.unpack("<L", mem[GPIO_OE:GPIO_OE + 4])[0]
        mem[GPIO_OE:GPIO_OE + 4] = struct.pack("<L", reg & ~VCC)
        mem[GPIO_SETDATAOUT:GPIO_SETDATAOUT + 4] = struct.pack("<L", VCC)
        JTAGPower = True
        return JTAGPower
    except Exception, e:
        log.error('!!! FATAL ERROR !!! : Unable to power up JTAG %s' % e)
        raise


def powerDownJTAG():
    global JTAGPower
    try:
        """Function will power off the device"""
        GPIO0_offset = 0x44E07000
        GPIO0_size = 0x44E07fff - GPIO0_offset
        GPIO_OE = 0x134
        GPIO_CLEARDATAOUT = 0x190
        VCC = 1 << 23
        with open("/dev/mem", "r+b") as f:
            mem = mmap.mmap(f.fileno(), GPIO0_size, offset=GPIO0_offset)
        reg = struct.unpack("<L", mem[GPIO_OE:GPIO_OE + 4])[0]
        mem[GPIO_OE:GPIO_OE + 4] = struct.pack("<L", reg & ~VCC)
        mem[GPIO_CLEARDATAOUT:GPIO_CLEARDATAOUT + 4] = struct.pack("<L", VCC)
        JTAGPower = False
        return JTAGPower
    except Exception, e:
        log.error('!!!!!FATAL ERROR!!!!!: Unable to power down JTAG: %s' % e)
        raise


def resetPRUMem(blocks=100):
    PRU_ICSS = 0x4A300000
    PRU_ICSS_LEN = 512 * 1024
    RAM0_START = 0x00000000
    with open("/dev/mem", "r+b") as f:
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    for x in range(0, blocks):
        ddr_mem[RAM0_START + (x * 4):RAM0_START + (x * 4) + 4] = struct.pack('<L', 0)


def readOutPRUMem(blocks=50):
    """The :param blocks: 0 will make it print complete memory till the
    terminate sequence is reached.
    """
    PRU_ICSS = 0x4A300000
    PRU_ICSS_LEN = 512 * 1024
    RAM0_START = 0x00000000
    TERMINATE_SEQ = '0xabcdef12L'
    with open("/dev/mem", "r+b") as f:
        ddr_mem = mmap.mmap(f.fileno(), PRU_ICSS_LEN, offset=PRU_ICSS)
    endReached = False
    x = 0
    memContents = []
    lines_printed = 0
    try:
        while not endReached:
            lines_printed += 1
            local = struct.unpack('L', ddr_mem[RAM0_START + (x * 4):RAM0_START + (x * 4) + 4])
            x += 1
            if str(hex(local[0])) == TERMINATE_SEQ or lines_printed == blocks:
                if lines_printed == blocks:
                    log.warn("Scanned %s lines of memory but still couldnot find the exit pattern, quitting" % blocks)
                break
            memContents.append('{0:032b}'.format(local[0]))
    except:
        pass
    return memContents


def compareResults(fileOutput):
    """Compare the results of the PRU memory content to a expected output array created while converting
    ATP to assembler"""
    PRUMemContents = readOutPRUMem(0)
    fileOutput = ''.join(fileOutput)
    desiredOutput = []
    totalOutputValue = 0
    match = True
    captureData = []
    for i in range(0, len(fileOutput), 32):
        desiredOutput.append(fileOutput[i:i + 32])
    if len(desiredOutput[len(desiredOutput) - 1]) < 32:
        desiredOutput[len(desiredOutput) - 1] = '0' * (32 - len(desiredOutput[len(desiredOutput) - 1])) + \
                                                desiredOutput[len(desiredOutput) - 1]
    for i in range(0, len(desiredOutput)):
        totalOutputValue += int(PRUMemContents[i + 1])
        matchLine = True
        for x in range(0, 32):
            if desiredOutput[i][x] != PRUMemContents[i + 1][x]:
                if desiredOutput[i][x] != 'C':
                    match = False
                    matchLine = False
                else:
                    captureData.append(PRUMemContents[i + 1][x])
        if not matchLine:
            if totalOutputValue > 0:
                log.error('UI:::RED:::20:::EXPECTED :- %s' % desiredOutput[i])
                log.error('UI:::RED:::20:::RECEIVED :- %s' % PRUMemContents[i+1])
    if match:
        log.info('UI:::GREEN:::10:::Handshake bits are a perfect match')
    elif not match:
        if totalOutputValue == 0:
            log.warn('UI:::YELLOW:::10:::No output received from device, make sure device is connected properly')
        else:
            log.error('UI:::RED:::20:::The hand shake seemed to have some error')
    log.debug('captured data %s' % str(captureData))
    if len(captureData) > 0:
        return ''.join(captureData)
    log.debug('return from compareResults success')
    return ''

def runOnPRU(PRU, binFile, interrupt=1):
    try:
        pypruss.init()  # Init the PRU
        pypruss.open(interrupt)  # Open PRU  PRU1_ARM_INTERRUPT
        pypruss.pruintc_init()  # Init the interrupt controller
        pypruss.exec_program(PRU, binFile)
        log.info('PRU %s executing %s' % (PRU, os.path.split(binFile)[len(os.path.split(binFile)) - 1]))
        pypruss.wait_for_event(interrupt)  # Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
        pypruss.clear_event(interrupt)  # Clear the event
        pypruss.exit()
    except Exception, e:
        log.error(e)
        pypruss.exit()
        raise Exception('Error executing file %s on PRU' % binFile)


#####
# Steps for executing a list of bins
# 1. First sort all the binaries
# 2. Make sure there is a reset.bin and an inputReceiver.bin
# 3a. First run the reset.bin (maybe make this an optional step that is done by default)
# 3b. clear PRU memory
# 4. Start the inputPRU.bin
# 5. loop through the list of all other bins
# 6. Conclude and clean up
# Since I haven't figured out how to check if the state is powerd one or not we will powerdown and set
# state to false=off and True=On

# Power Properties
try:
    powerDownJTAG()
    pass
except Exception, e:
    log.debug(e)
    pass
JTAGPower = False

# Reset and receive Bin
resetBinName = 'reset.bin'
receiveBinName = 'inputReceiver_PRU0.bin'
endJTAGBinName = 'endJTAG.bin'

# PRU Usage
drivingPRU = 1  # PRU 1 drives the JTAG pins
receivingPRU = 0  # PRU 0 receives the data from device

########

class JTAGDriver(object):
    def __init__(self, binFiles):
        self.binaryFiles = binFiles
        self.binaryFiles.sort()
        self.PRUMemContents = []
        # Check through all the files and select the reset and input files
        for binF in self.binaryFiles:
            if resetBinName in binF:
                self.resetBin = binF
                log.debug('reset binary: %s' % binF)
            if receiveBinName in binF:
                self.inputBinary = binF
                log.debug('input binary: %s' % binF)
            if endJTAGBinName in binF:
                self.endJTAGBinary = binF
                log.debug('endJTAG binary: %s' % binF)
        if self.resetBin is None or self.inputBinary is None:
            log.error('Reset binary or Input Binary not found in list of binary files')
            raise Exception('Reset binary or Input Binary not found in list of binary files')

    def resetPRU(self):
        """ Reset both the PRUs this is to be called only before we start a new JTAG"""
        for i in range(0, 2):
            runOnPRU(i, self.resetBin)
        return True

    def endJTAG(self):
        """Send the END_JTAG command to clear PRU mem content and record data"""
        runOnPRU(1, self.endJTAGBinary)
        #pypruss.wait_for_event(0)  # Wait for event 0 which is connected to PRU0_ARM_INTERRUPT
        #pypruss.clear_event(0)  # Clear the event
        #pypruss.exit()
        return True

    def initReceiver(self, clearMem=True, copyMem=False, memBlock=100):
        """Initialize the input receiver
        1. copy out the memory content if set, default false
        2. Reset the moemory contents if set, default True
        3. Start the receiver binary on the receiving PRU"""
        if copyMem:
            self.PRUMemContents = readOutPRUMem(blocks=0)
        if clearMem:
            resetPRUMem(memBlock)
            log.info('PRU Memory Cleared %s blocks' % memBlock)
        pypruss.init()  # Init the PRU
        pypruss.open(0)  # Open PRU event 0 which is PRU0_ARM_INTERRUPT
        pypruss.pruintc_init()  # Init the interrupt controller
        pypruss.exec_program(receivingPRU, self.inputBinary)  # Load firmware for input recording
        pypruss.clear_event(0)
        pypruss.exit()

    def executeJTAGCommands(self, resetPRU=True):
        """First check if the vcc is high"""
        if not JTAGPower:
            log.error('UI:::RED:::20:::No power on JTAG, please power on first')
            # raise Exception('No power on JTAG, please power on first')
        if resetPRU:
            self.resetPRU()
        # Receiver is always started, as it is ended when this function ends
        self.initReceiver(clearMem=resetPRU)
        exeFiles = [f for f in self.binaryFiles if
                    (resetBinName not in f) and (receiveBinName not in f) and (endJTAGBinName not in f)]

        for binary in exeFiles:
            runOnPRU(drivingPRU, binary)
        # now clear PRU MEM data
        self.endJTAG()

    def logPRUMemContents(self, handShakeBits=None):
        if handShakeBits is not None:
            handShakeBits = ''.join(handShakeBits)
        self.PRUMemContents = readOutPRUMem()
        i = 0
        totalVal = 0
        for line in range(1, len(self.PRUMemContents)):
            totalVal += int(self.PRUMemContents[line])
            log.info('{0:03d}'.format(line) + '(from Dev) : ' + self.PRUMemContents[line])
            if handShakeBits is not None:
                log.info(
                    '{0:03d}'.format(line) + '(from Fil) : ' + handShakeBits[32 * (line - 1):(32 * (line - 1)) + 32])
            i += 1
        if totalVal == 0:
            log.warn('The output is 0, please make sure the device is connected')
