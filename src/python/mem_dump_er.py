"""
This file is intended to take care of all the programs related to parsing the ATP pattern and generating
assemblers for writing a mory dump from a text file
"""

from atp_from_template_writer import AtpFromTemplateWriter
from atp_to_assembler import AtpToAssembler
from global_variables import *
import jtag_driver

log = logging.getLogger(__name__)
# 4w ATP file signal sequence
TEST = 0
TCK = 1
TMS = 2
TDI = 3
TDO = 4
RST = 5


def toBin(i, l):
    binary_string = bin(i)[2:]
    if len(binary_string) < l:
        padding = l - len(binary_string)
        binary_string = '0' * padding + binary_string
    return binary_string


class MemoryControl(object):
    def __init__(self, memoryFile, templateATP):
        Config.read(CONFIG_FILE)
        if templateATP is None:
            templateATP = Config.get("FRAM_SETTING", "atp_mem_wr_template")
            self.TEMPLATE_FOLDER = os.path.join(project_folder, Config.get("FRAM_SETTING", "atp_mem_template_folder"))
            self.TEMPLATE_ATP = os.path.join(self.TEMPLATE_FOLDER, templateATP)
            self.tempAtpFile = os.path.join(project_folder, Config.get("FRAM_SETTING", "mem_dump_atp"))
        else:
            self.TEMPLATE_FOLDER = os.path.dirname(templateATP)
            self.TEMPLATE_ATP = templateATP
            self.tempAtpFile = os.path.join(self.TEMPLATE_FOLDER, tempF, 'temp.atp')
        if memoryFile is None:
            memoryFile = 'dump.txt'
            self.MEM_FILE_FOLDER = os.path.join(project_folder, Config.get("FRAM_SETTING", "mem_dump_file_folder"))
            self.MEM_FILE = os.path.join(self.MEM_FILE_FOLDER, memoryFile)
            self.ASSEMBLER_FOLDER = os.path.join(project_folder,
                                                 Config.get("FRAM_SETTING", "mem_dump_assembler_folder"))
        else:
            self.MEM_FILE_FOLDER = os.path.dirname(memoryFile)
            self.MEM_FILE = memoryFile
            self.ASSEMBLER_FOLDER = os.path.join(self.MEM_FILE_FOLDER, tempF, asseblerF)
        self.dump = None
        self.BIN_FOLDER = None
        self.assemblyWriter = None
        self.BIN_FILES = None
        self.templateWriter = AtpFromTemplateWriter(self.TEMPLATE_ATP)
        return

    def writeAssemblers(self):
        return self.assemblyWriter.convertToAssembler(self.ASSEMBLER_FOLDER)

    def writeTempATP(self):
        return

    def compileBinaries(self, folder):
        self.BIN_FOLDER = os.path.join(self.MEM_FILE_FOLDER, self.MEM_FILE.replace('.', '_'), folder)
        try:
            self.BIN_FILES = self.assemblyWriter.compileAssemblerFiles(self.BIN_FOLDER)
            return self.BIN_FILES
        except Exception, e:
            log.error(e)
            raise e

    def execute(self, reset):
        return


class MemLoadEr(MemoryControl):
    def __init__(self, inputFile=None, templateATP=None):
        super(MemLoadEr, self).__init__(inputFile, templateATP)

    def readMemFromFile(self):
        with open(self.MEM_FILE) as input:
            self.dump = input.readlines()
        return

    def writeTempATP(self):
        """ if the Temp file exists, delete it and then create a new temp file, add the parts before the write_mem_word
        to the start of the temp file"""
        if os.path.isfile(self.tempAtpFile):
            os.remove(self.tempAtpFile)
            log.warn('File %s already exsists, will be overwritten')
        self.templateWriter.generateATP(self.makeAddressValuePairsFromDump(), self.tempAtpFile)
        log.info('Successfully completed, file %s created' % self.tempAtpFile)
        self.assemblyWriter = AtpToAssembler(self.tempAtpFile)
        return self.tempAtpFile

    def makeAddressValuePairsFromDump(self):
        """This function is to convert the memory dump into an address value pair which will then be coupled with
        the write_mem_word """
        addressValueList = []
        with open(self.MEM_FILE, 'rU') as input:
            lines = input.readlines()
            for line in lines:
                line = line.replace('\n', '')
                if line.startswith('@'):
                    # This line contains the start address, so we extract it
                    s = line.replace('@', '')
                    address = int(s, 16)
                elif len(line) > 1 and 'q' not in line:
                    # This line contains the data, we need to extract
                    data = line.split()
                    if len(data) % 2 != 0:
                        log.error('Memory dump file doesnot contain even data bits in one line')
                        log.error('error in line %s, contains only %s elements' % (line, len(data)))
                        raise Exception('MemoryDump')
                    for i in range(0, len(data), 2):
                        d = data[i + 1] + data[i]
                        addressValueList.append({toBin(address, 20): toBin(int(d, 16), 16)})
                        # log.debug('address: %s   data: %s' % (hex(address).upper(), d))
                        address += 2
            input.close()
        return addressValueList

    def execute(self, reset):
        driver = jtag_driver.JTAGDriver(self.BIN_FILES)
        driver.executeJTAGCommands(resetPRU=reset)
        return jtag_driver.compareResults(self.assemblyWriter.atpOutputSeq)


class MemReadEr(MemoryControl):
    def __init__(self, memoryFile, templateATP, startAddr, memSize):
        super(MemReadEr, self).__init__(memoryFile, templateATP)
        self.startAdd = startAddr
        self.memSize = memSize
        return

    def writeTempATP(self):
        if os.path.isfile(self.tempAtpFile):
            os.remove(self.tempAtpFile)
            log.warn('File %s already exsists, will be overwritten')
        addresses = []
        for i in range(0, self.memSize, 2):
            addresses.append(toBin(self.startAdd + i, 20))
        log.debug('address computed, memory will be read from a total of %s address location' % len(addresses))
        self.templateWriter.generateATP(addresses, self.tempAtpFile)
        self.assemblyWriter = AtpToAssembler(self.tempAtpFile)
        return self.tempAtpFile

    def execute(self, reset):
        driver = jtag_driver.JTAGDriver(self.BIN_FILES)
        driver.executeJTAGCommands(resetPRU=reset)
        dataRead = jtag_driver.compareResults(self.assemblyWriter.atpOutputSeq)
        dataLines = []
        for i in range(0, len(dataRead), 8 * 16):
            dataLines.append(dataRead[i: i + (8 * 16)])
        log.debug('length of data recorded from device : %s' % len(dataRead))
        log.debug('data will be written to : %s' % self.MEM_FILE)
        with open(self.MEM_FILE, 'wb') as outFile:
            outFile.write('@%s\n' % hex(self.startAdd)[2:].upper())
            for x in range(0, len(dataLines)):
                dataLine = dataLines[x]
                for i in range(0, len(dataLine), 16):
                    data1 = dataLine[i: (i + 8)]
                    data2 = dataLine[i + 8: (i + 16)]
                    data1 = hex(int(data1, 2))[2:].upper()
                    if len(data1) == 1:
                        data1 = '0' + data1
                    data2 = hex(int(data2, 2))[2:].upper()
                    if len(data2) == 1:
                        data2 = '0' + data2
                    outFile.write('%s %s ' % (data2, data1))
                outFile.write('\n')
            outFile.write('p\n')
        return dataRead


if __name__ == '__main__':
    data = ['1', '1', '0', '0', '1', '1', '0', '1', '1', '0', '1', '0', '1', '0', '1', '1', '0', '0', '0', '1', '0', '0', '1', '0', '1', '1', '1', '0', '1', '1', '1', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '0', '1', '1', '0', '1', '0', '0', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '1', '1', '0', '0', '1', '1', '0', '1', '1', '0', '1', '0', '1', '0', '1', '1', '0', '0', '0', '1', '0', '0', '1', '0', '1', '1', '1', '0', '1', '1', '1', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '0', '1', '1', '0', '1', '0', '0', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '1', '1', '1', '0', '0', '1', '1', '0', '1', '1', '0', '1', '0', '1', '0', '1', '1', '0', '0', '0', '1', '0', '0', '1', '0', '1', '1', '1', '0', '1', '1', '1', '1', '0', '1', '0', '1', '0', '1', '0', '1', '0', '0', '1', '1', '0', '1', '0', '0']
    dataRead = ''.join(data)
    dataLines = []
    for i in range(0, len(dataRead), 8 * 16):
            dataLines.append(dataRead[i: i + (8 * 16)])
    for y in range (0, len(dataLines)):
        data = dataLines[y]
        for x in range(0, len(data), 16):
            data1 = data[x: (x + 8)]
            data2 = data[x + 8: (x + 16)]
            data1 = hex(int(data1, 2))[2:].upper()
            data2 = hex(int(data2, 2))[2:].upper()
            print('%s %s ' % (data2, data1))
