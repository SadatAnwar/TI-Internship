# coding=utf-8
import shutil
import traceback
import re
from global_variables import *
import atp_from_template_writer
import atp_to_assembler
import jtag_driver
import debugger_cape
import operator
from src.python.websocket_server import framPageSocket
from mem_dump_er import MemLoadEr, MemReadEr

log = logging.getLogger(__name__)
""" The intention of this file is to contain code and class that are relavent to executing a complete test"""

compiledTestSequences = {}


def compileTest(tests, uid):
    compiledTests = []
    for test in tests:
        testName = str(test['Name'])
        testObject = Test(testName, test['Type'], test["Param"])
        if testObject not in compiledTests:
            try:
                framPageSocket.sendData('progress:::%s' % str(testName))
                compiledTests.append(testObject)
                testObject.compile()
                log.info('UI:::GREEN:::10:::Compiled %s' % testName)
                framPageSocket.sendData('success:::%s' % str(testName))
            except Exception, e:
                log.error('UI:::RED:::10:::Error compiling test :%s' % e)
                log.error(traceback.format_exc())
                framPageSocket.sendData('error:::%s:::%s' % (testName, e))
        else:
            # The object is already present in the list, we will reuse the same object
            for i in range(0, len(compiledTests)):
                if testObject == compiledTests[i]:
                    testObject = compiledTests[i]
                    break
            compiledTests.append(testObject)
        compiledTestSequences[uid] = compiledTests
    return list(compiledTestSequences.keys())


def executeTests(UID):
    compiledTests = compiledTestSequences.get(UID)
    for test in compiledTests:
        test.execute()


class Test(object):
    def __init__(self, name, type, params):
        self.name = name
        self.type = type
        self.RESET_PRU = True
        self.VERIFY_RESULT = False
        log.debug(self.type)
        self.testInstanceSeq = []
        self.tempFolder = os.path.join(project_folder, tempF, name)
        if not os.path.exists(self.tempFolder):
            log.info('Creating folder %s' % self.tempFolder)
            os.makedirs(self.tempFolder)
        self.atpFolder = os.path.join(self.tempFolder, atpF)
        self.atpFile = os.path.join(self.atpFolder, name + '.atp')
        self.params = params

    def compile(self):
        if self.type == 'INTERFACE_T':
            self.result = '{0:016b}'.format(int(self.params['RESULT0'], 16)) + '{0:016b}'.format(
                int(self.params['RESULT1'], 16))
            self.data = '{0:08b}'.format(int(self.params['MEMORY'], 16)) + '{0:08b}'.format(
                int(self.params['DATA'], 16)) + '{0:08b}'.format(int(self.params['ALGORITHM'], 16)) + '{0:08b}'.format(
                int(self.params['SETTING'], 16)) + '{0:08b}'.format(
                int(self.params['RESULTTYPE'], 16)) + '{0:08b}'.format(
                int(self.params['PARAM1'], 16)) + '{0:016b}'.format(int(self.params['PARAM2'], 16))
            config.read(CONFIG_FILE)
            self.templateFolder = config.get('FRAM_SETTING', 'atptesttemplate_path')
            self.template = os.path.join(self.templateFolder, config.get("FRAM_SETTING", "ATP_TEST_TEMPLATE"))
            atpWriter = atp_from_template_writer.AtpFromTemplateWriter(self.template)
            atpWriter.generateATP(self.data, self.atpFile)
            self.testInstanceSeq = self._makeFRAMTestSeq()
        if self.type == 'FRAME_T':
            log.info(self.type)
            self.data = {
                'Memory': os.path.join(project_folder, frame_test_F, frameMemoryFiles,
                                       self.params.get('MEMORY', 'blank')),
                'Pattern': os.path.join(project_folder, frame_test_F, patternsF, self.params.get('SETTING', 'blank')),
                'Algorithm': int(self.params.get('ALGORITHM', '0'), 16),
                'MemStart': int(self.params['PARAM1'], 16),
                'MemSize': int(self.params['PARAM2'], 16)
            }
            self.testInstanceSeq = sorted(self._makeFrameTestSeq())

    def _makeFRAMTestSeq(self):
        """We will parse the file and break it into sequence of different tests"""
        testInstances = []
        self.VERIFY_RESULT = True
        with open(self.atpFile, 'rU') as inputFile:
            lines = inputFile.readlines()
            part = 0
            fileName = os.path.join(self.atpFolder, '%s__%s.atp' % (self.name, '{0:02}'.format(part)))
            outFile = open(fileName, 'w')
            for i in range(0, len(lines)):
                line = lines[i]
                if len(line) > 1:
                    # If the line is an analoge test
                    if '<<DAC>>' in line or '<<ADC>>' in line:
                        # Close the file that is currently being written and create a digitalTestInstance object
                        outFile.close()
                        testInstances.append(DigitalTestInstance(part, fileName, self.tempFolder))
                        # Create the AnalogTestObject for this line
                        if '<<DAC>>' in line:
                            ## The idea is to create an analogTestInstance that will do all DAC related tests here
                            DACInstance = []
                            for x in range(0, 3):
                                if self.params['EXT%sMODE' % x] == '0':
                                    # if the DAC is NC then we set it to 0v
                                    part += 1
                                    DACInstance.append([DACTestInstance(part, x + 2, 0)])
                                elif self.params['EXT%sMODE' % x] == '1' or self.params['EXT%sMODE' % x] == '3':
                                    part += 1
                                    # Check if the entered value is for a schmoo
                                    try:
                                        dacVoltages = float(self.params['EXT%sFORCE' % x])
                                        DACInstance.append([DACTestInstance(part, x + 2, dacVoltages)])
                                    except ValueError:
                                        # the data present is for a schmoo
                                        dacVoltages = self.params['EXT%sFORCE' % x].split(';')
                                        if len(dacVoltages) > 1:
                                            # it was a ; separated list of discreet voltages
                                            dacInstances = []
                                            for volt in dacVoltages:
                                                dacInstances.append(DACTestInstance(part, x + 2, float(volt)))
                                            DACInstance.append(dacInstances)
                                        else:
                                            # the string is of the format X to Y step Z
                                            dacVoltageRange = self.params['EXT%sFORCE' % x].split(' ')
                                            start = float(dacVoltageRange[0])
                                            end = float(dacVoltageRange[2])
                                            step = float(dacVoltageRange[4])
                                            dacInstances = []
                                            while start <= end:
                                                dacInstances.append(DACTestInstance(part, x + 2, start))
                                                start += step
                                            DACInstance.append(dacInstances)
                            testInstances.append(DACInstance)
                        elif '<<ADC>>' in line:
                            for x in range(0, 3):
                                if self.params['EXT%sMODE' % x] == '1' or self.params['EXT%sMODE' % x] == '2':
                                    part += 1
                                    # TODO create a ADCTest instance and then measure current
                                    # TODO FCMV
                                    pass

                        # Start a new file
                        part += 1
                        fileName = os.path.join(self.atpFolder, '%s__%s.atp' % (self.name, '{0:02}'.format(part)))
                        outFile = open(fileName, 'w')
                        continue
                    outFile.write(line)
            testInstances.append(DigitalTestInstance(part, fileName, self.tempFolder))
            outFile.close()
            return testInstances

    def _makeFrameTestSeq(self):
        part = 0
        self.RESET_PRU = False
        testInstances = set()
        # for x in range(0, 3):
        #     if self.params['EXT%sMODE' % x] == '0':
        #         # if the DAC is NC then we set it to 0v
        #         part += 1
        #         testInstances.add(DACTestInstance(part, x + 2, 0))
        #     if self.params['EXT%sMODE' % x] == '1' or self.params['EXT%sMODE' % x] == '3':
        #         part += 1
        #         testInstances.add(
        #             DACTestInstance(part, x + 2, float(self.params['EXT%sFORCE' % x])))
        # for x in range(0, 3):
        #     if self.params['EXT%sMODE' % x] == '1' or self.params['EXT%sMODE' % x] == '2':
        #         part += 1
        #         # TODO create a ADCTest instance and then measure current
        #         # TODO FCMV
        #         pass
        if self.data['Algorithm'] == 0:
            pass
        if self.data['Algorithm'] == 1:
            # Read the memory from device
            part += 1
            memoryFile = self.data['Memory']
            template = self.data['Pattern']
            memStart = self.data['MemStart']
            memSize = self.data['MemSize']
            testInstances.add(MemoryReadTestInstance(part, memoryFile, template, memStart, memSize))
        if self.data['Algorithm'] == 2:
            # write memory to device
            part += 1
            memoryFile = self.data['Memory']
            template = self.data['Pattern']
            testInstances.add(MemoryLoadTestInstance(part, memoryFile, template))
        if self.data['Algorithm'] == 3:
            # Run the pattern present in the settings
            part += 1
            atpFileToBeExecuted = self.data['Pattern']
            testInstances.add(DigitalTestInstance(part, atpFileToBeExecuted, self.tempFolder))
        if self.data['Algorithm'] == 4:
            # Reset JTAG
            self.RESET_PRU = True
            part += 1
            blankFile = os.path.join(project_folder, frame_test_F, '_blank')
            testInstances.add(DigitalTestInstance(part, blankFile, self.tempFolder))
        return testInstances

    def execute(self):
        self._execute(self.testInstanceSeq)
        return

    def _execute(self, testSeq):
        """THe _execute is supposed to take in a sequence as a parameter and and execute call the execute method on
        all instances inside the seq"""
        if self.RESET_PRU:
            reset = True
        else:
            reset = False
        for i in range(0, len(testSeq)):
            seq = testSeq[i]
            if type(seq) is list:
                # this is an array of DAC tests so do some fancy stuff here...
                # since we have 3 DAC channels, this array will always have 3 lists, each list will contain the
                # instances of DAC Test for the relevant channel.
                for dac1 in seq[0]:
                    dac1.execute(reset)
                    for dac2 in seq[1]:
                        dac2.execute(reset)
                        for dac3 in seq[2]:
                            dac3.execute(reset)
                            self._execute(testSeq[i + 1:])
                # once control comes here, break out of loop as all the instances beyond this point have already
                # been executed in a recurrsive manner
                break
            else:
                log.info('UI:::GREEN:::10:::Executing instance:%s [%s] of %s' % (seq.seq, seq.type, self.name))
                result = seq.execute(reset)
                if self.VERIFY_RESULT:
                    if len(result) == 32:
                        if self.result == result:
                            log.info('UI:::GREEN:::20:::TEST: %s - PASSED' % self.name)
                            pass
                        else:
                            log.error('UI:::RED:::20:::TEST: %s - FAILED (Expected: %s)' % (self.name, self.result))
                            pass
                reset = False
                self.RESET_PRU = False
        return

    def __eq__(self, other):
        return self.name == other.name


class TestInstance(object):
    def __init__(self, seq, type):
        self.seq = seq
        self.type = type

    def __cmp__(self, other):
        return cmp(self.seq, other.seq)

    def execute(self, test):
        return

    def getResults(self):
        return


class MemoryLoadTestInstance(TestInstance):
    def __init__(self, seq, dumpFile, template):
        super(MemoryLoadTestInstance, self).__init__(seq, 'MemoryLoad')
        self.name = os.path.split(dumpFile)
        self.name = self.name[len(self.name) - 1]
        self.memoryDumpHandler = MemLoadEr(inputFile=dumpFile, templateATP=template)
        self.memoryDumpHandler.writeTempATP()
        self.validResult = self.memoryDumpHandler.writeAssemblers()
        self.binFiles = self.memoryDumpHandler.compileBinaries('bin')
        shutil.rmtree(self.memoryDumpHandler.ASSEMBLER_FOLDER)

    def execute(self, reset):
        return self.memoryDumpHandler.execute(reset)

    def getResults(self):
        return jtag_driver.compareResults(self.validResult)

    def __len__(self):
        return len(self.binFiles)

    def __hash__(self):
        return hash(self.name)


class MemoryReadTestInstance(TestInstance):
    def __init__(self, seq, memFile, template, startAdd, memSize):
        super(MemoryReadTestInstance, self).__init__(seq, 'MemoryRead')
        self.name = os.path.split(memFile)
        self.name = self.name[len(self.name) - 1]
        log.debug('Start address: %s  and size : %s' % (hex(startAdd), memSize))
        self.memoryDumpHandler = MemReadEr(memFile, template, startAdd, memSize)
        self.memoryDumpHandler.writeTempATP()
        self.validResult = self.memoryDumpHandler.writeAssemblers()
        self.binFiles = self.memoryDumpHandler.compileBinaries('bin')
        shutil.rmtree(self.memoryDumpHandler.ASSEMBLER_FOLDER)

    def execute(self, reset):
        return self.memoryDumpHandler.execute(reset)

    def getResults(self):
        return jtag_driver.compareResults(self.validResult)

    def __len__(self):
        return len(self.binFiles)

    def __hash__(self):
        return hash(self.name)


class DigitalTestInstance(TestInstance):
    def __init__(self, seq, atpFile, tmpFolder):
        super(DigitalTestInstance, self).__init__(seq, 'Digital')
        self.name = os.path.split(atpFile)
        self.name = self.name[len(self.name) - 1]
        asseblerWriter = atp_to_assembler.AtpToAssembler(atpFile)
        assemblerFolder = os.path.join(tmpFolder, asseblerF, self.name)
        self.validResult = asseblerWriter.convertToAssembler(assemblerFolder)
        binaryFolder = os.path.join(tmpFolder, binaryF, self.name)
        self.binaryFiles = asseblerWriter.compileAssemblerFiles(binaryFolder)

    def execute(self, reset):
        if len(self.binaryFiles) > 1:
            driver = jtag_driver.JTAGDriver(self.binaryFiles)
            driver.executeJTAGCommands(resetPRU=reset)
            if len(self.validResult) > 0:
                result = jtag_driver.compareResults(self.validResult)
                if len(result) > 1:
                    log.info('UI:::GREEN:::20:::Captured data is: %s (%s)' % (result, hex(int(result, 2)).upper()))
                    return result
                else:
                    return ''
        else:
            log.debug('%s contains no executible parts' % self.name)
        return ''

    def getResults(self):
        return jtag_driver.compareResults(self.validResult)

    def __hash__(self):
        return hash(self.name)

    def __len__(self):
        return len(self.binaryFiles)


class DACTestInstance(TestInstance):
    def __init__(self, seq, channel, voltage):
        super(DACTestInstance, self).__init__(seq, 'DAC')
        self.dac = debugger_cape.DAC(int(channel))
        self.voltage = voltage

    def execute(self, reset):
        self.dac.setVoltage(self.voltage)
        log.info('UI:::GREEN:::10:::Voltage (%sV) set on DAC channel %s' % (self.voltage, self.dac.channel))
        return ''

    def getResults(self):
        return 'Voltage on DAC-%s: %sV' % (self.dac.channel, self.voltage)


class ADCTestInstance(TestInstance):
    def __init__(self, seq, channel):
        super(ADCTestInstance, self).__init__(seq, 'ADC')
        self.adc = debugger_cape.ADC(channel)

    def execute(self, test):
        self.adc.readCurrent()

    def getResults(self):
        return self.adc.readCurrent()

# Test
if __name__ == '__main__':
    data = {'RESULT0': '0x000A',
            'RESULT1': '0x0000',
            'RESULTTYPE': '0x01',
            'PARAM2': '0x0000',
            'PARAM1': '0x08',
            'DATA': '0x11',
            'EXT0HIGHLIMIT': '0',
            'EXT1MODE': '0',
            'EXT0MODE': '3',
            'USERF': '0x2000',
            'MEASC': '0',
            'EXT1FORCE': '0',
            'TNUM': '211002100',
            'EXT2HIGHLIMIT': '0',
            'ALGORITHM': '0x08',
            'EXT2MODE': '0',
            'EXT0FORCE': '1.35',
            'SETTING': '0x01',
            'EXT2LOWLIMIT': '0',
            'EXT1LOWLIMIT': '0',
            'EXT1HIGHLIMIT': '0',
            'EXT0LOWLIMIT': '0',
            'EXT2FORCE': '0',
            'MEMORY': '0x03'}

    container = []
    name = 'Test_Example1'
    bla = Test(name, 'FRAME_T', data)
    bla2 = Test(name, 'FRAME_T', data)
    container.append(bla)
    if container.__contains__(bla2):
        container.append(bla)
