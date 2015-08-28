# coding=utf-8
""" This class is used to convert an ATP file into assembler source
    :parameter the input ATP file and the Name of the folder where the assembler files are to be produced"""
import subprocess
from global_variables import *

log = logging.getLogger(__name__)

# lines in file
def file_len(fileName):
    with open(fileName) as f:
        for i, l in enumerate(f):
            pass
    return i + 1


# Add lines to file
def addLineToFile(file_name, line):
    with open(file_name, "ab+") as out:
        out.writelines(line)
        out.close()


class AtpToAssembler(object):
    def __init__(self, inputFile):
        """ The inputFile and outputFolder have to be complete PATH to file and folder.
         This is not default to any folder.
         the J4W flag indicates if the parser is to run for 2 wire of 4 wire mode"""
        self.validSignals = ['FIX1US', 'JTAG', 'TCLK']
        # Check if the input file given is already a valid file
        if os.path.isfile(inputFile):
            self.input = inputFile
        elif project_folder not in inputFile:
            # if the test above fails, try checking if the path is inside the project folder, if not add
            # it and try again
            self.input = os.path.join(project_folder, inputFile)
            if not os.path.isfile(self.input):
                raise Exception('Invalid ATP file for %s' % inputFile)
        self.J4W = self.__analyzeFile__()
        self.headerFolder = 'headers_4W'
        if not self.J4W:
            self.headerFolder = 'headers_2W'
        self.fileExt = '.p'
        self.commentPattern = ['//', '/*']
        self.numberFormat = '{0:04d}'
        self.headerFile = os.path.join(project_folder, "src", self.headerFolder, "header.hp")
        self.footerFile = os.path.join(project_folder, "src", self.headerFolder, "footer.hp")
        self.includeStatement = '#include'
        self.assemblerFilesCreated = []
        self.atpOutputSeq = []

        if self.J4W:
            self.TEST = 0
            self.TCK = 1
            self.TMS = 2
            self.TDI = 3
            self.TDO = 4
            self.RST = 5
            self.bitLength = 6
        else:
            self.TEST = 0
            self.RST = 1
            self.TDO = 1
            self.bitLength = 2

    # Write the footer to the file
    def endFileWithFooter(self, file_name):
        # check if the file has any relevant lines
        if file_len(file_name) > 2:
            log.debug(file_name + " created.")
            with open(file_name, "ab+") as out:
                out.writelines("#include \"" + self.footerFile + "\"\n")
                out.close()
            self.assemblerFilesCreated.append(file_name)
        else:
            log.debug(file_name + " is empty, will be deleted.")
            os.remove(file_name)

    # Write the header to the file inside the assemblerDirectory and return full file name
    def createFileWithHeader(self, assemblerDirectory, file_name):
        file_name = os.path.join(assemblerDirectory, file_name + self.fileExt)
        if os.path.isfile(file_name):
            log.warn(file_name + " already exists, will now be deleted.")
            os.remove(file_name)
        with open(file_name, "ab+") as out:
            out.writelines('#include "' + self.headerFile + '"\n')
            out.close()
        return file_name

    def __analyzeFile__(self):
        """Analyze if the input file is a 2 wire or 4wire jtag
        If it is unable to detect, it will default to a 4wire JTAG format"""
        with open(self.input, 'rU') as inputFile:
            # Read all the lines, and then parse them one by one
            lines = inputFile.readlines()
            for line in lines:
                if ' > ' in line and (any(x in line for x in self.validSignals)):
                    line = line[line.index('>'):]
                    for x in self.validSignals:
                        line = line.replace(x, '')
                    line = line.replace(" ", "")
                    line = line[:line.index(";")]
                    signals = sum(line.count(x) for x in ('1', '0', 'X', 'A', 'C', 'D', 'H', 'L'))
                    if signals < 6:
                        log.info('2W JTAG File, will be parsed using 2W directives')
                        return False
                    else:
                        log.info('4W JTAG File, will be parsed using 4W directives')
                        return True
        log.warn('Unable to detect template type, defaulting to 4W')
        return True

    # Parse each line in an ATP file, this method will do the common bit, before it splits into the specific 2/4 W
    # method to handle the specific file type
    def __processLine__(self, line):
        """This method will process a line, and then based on the template (2W or 4W) redirect to the
        specified function to get the output"""
        directiveLength = line.index(">")
        directive = line[:directiveLength]
        line = line[directiveLength + 1:]
        line = line[:line.index(";")]
        bits = line[-self.bitLength:]
        signal = line[:-self.bitLength]
        if directive.startswith("repeat"):
            if "FIX1US" in line:
                directive = directive.replace("repeat", "")
                if self.J4W:
                    return self.__4WSignal__(signal, bits, rep=directive)
                else:
                    return self.__2WSignal__(signal, bits, rep=directive)
            else:
                directive = directive.replace("repeat", "")
                output_line = []
                if self.J4W:
                    if signal == "TCLK":
                        if bits[self.TDI] == "0":
                            signal = "TCLK_CLR_TDI"
                        else:
                            signal = "TCLK_SET_TDI"
                    for rep in range(0, int(directive)):
                        output_line.append(self.__4WSignal__(signal, bits))
                        # add the line to file
                    return output_line
                else:
                    for rep in range(0, int(directive)):
                        output_line.append(self.__2WSignal__(signal, bits))
                        # add the line to file
                    return output_line
        else:
            if bits[self.TDO] in ['H', 'L', 'C']:
                if bits[self.TDO] == 'H':
                    self.atpOutputSeq.append('1')
                if bits[self.TDO] == 'L':
                    self.atpOutputSeq.append('0')
                if bits[self.TDO] == 'C':
                    self.atpOutputSeq.append('C')
                # To capture data we use the JTAG_IN signal
                signal = 'JTAG_IN'
            if 'halt' in directive:
                return ''
                # signal = "JTAG_END   //"
            if 'ign' in directive:
                return ''
            if self.J4W:
                # add the line to file
                return self.__4WSignal__(signal, bits)
            else:
                return self.__2WSignal__(signal, bits)

    def __4WSignal__(self, signal, bits, rep=None):
        """This method will process text line and write 4W specific assembler line"""
        comment = ''
        if signal == "TCLK":
            if bits[self.TDI] == "0":
                signal = "TCLK_CLR_TDI"
            else:
                signal = "TCLK_SET_TDI"
        elif signal == 'JTAG_IN':
            comment = "// " + bits[self.TDO]
        bit_seq = bits[self.RST] + bits[self.TEST] + bits[self.TDI] + bits[self.TMS] + bits[self.TCK]
        if rep is not None:
            outputLine = "%s \t 0b000%s, %s \t%s\n" % (signal, bit_seq, str(rep), comment)
        else:
            outputLine = "%s \t 0b000%s \t%s\n" % (signal, bit_seq, comment)
        return outputLine

    def __2WSignal__(self, signal, bits, rep=None):
        """ This method will process a TEXT line and output 2w specific assembler line"""
        if bits[self.RST] == '1':
            # RST_OUT should be 1 only when it s 1 in the file, for all other values, it should be 0
            REST_OUT = '1'
        else:
            REST_OUT = '0'
        TEST_OUT = bits[self.TEST]
        comment = ''
        if signal in ['JTAG_IN']:
            comment = "// TDO " + bits[self.RST]
        if rep is not None:
            output_line = '%s \t %s, %s, %s \t%s\n' % (signal, TEST_OUT, REST_OUT, str(rep), comment)
        else:
            output_line = '%s \t %s, %s \t%s\n' % (signal, TEST_OUT, REST_OUT, comment)
        return output_line

    def convertToAssembler(self, outputFolder):
        """Converts a the input file given when the AtpToAssembler was created, to an Assembler file ar the
        outputFolder"""
        fileNumber = 0
        assemblerName = None
        # Check if the output folder exists, if it doesnt, create it
        if not os.path.isdir(outputFolder):
            os.makedirs(outputFolder)
        with open(self.input, 'rU') as input:
            # Read all the lines, and then parse them one by one
            lines = input.readlines()
            for i in range(0, len(lines)):
                line = lines[i]
                # check if the line is a comment, if its a comment, it might contain the #include
                if any(line.startswith(x) for x in self.commentPattern):
                    # if line has a #include statement, start a new assembler file, and name it with the
                    # macro name
                    if self.includeStatement in line:
                        # remove #include from file name
                        line = line.replace(self.includeStatement, '')
                        if assemblerName is not None:
                            # end the old file, add a footer include
                            self.endFileWithFooter(assemblerName)
                            fileNumber += 1
                        # Set the name for the new file
                        assemblerName = self.numberFormat.format(fileNumber) + '_' + ''.join(
                            e for e in line if e.isalnum()).replace("edt", "")
                        assemblerName = self.createFileWithHeader(outputFolder, assemblerName)
                        continue
                    continue
                # Skip lines that are too short, no relevant data
                if len(line) < 3:
                    continue
                # Check for lines that describe a signal
                if ">" in line and (any(x in line for x in self.validSignals)):
                    line = line.replace(" ", "")
                    assemblerLine = self.__processLine__(line)
                    with open(assemblerName, "ab+") as out:
                        out.writelines(assemblerLine)
        # Append footer to the last file created and then exit
        if assemblerName is not None:
            self.endFileWithFooter(assemblerName)
        return self.atpOutputSeq

    def compileAssemblerFiles(self, binaryFolder):
        if not os.path.isdir(binaryFolder):
            log.debug('Creating folder %s' % binaryFolder)
            os.makedirs(binaryFolder)
        else:
            # if it already existed, delete all files in dir and recompile
            for fi in [os.path.join(binaryFolder, f) for f in os.listdir(binaryFolder) if
                       os.path.isfile(os.path.join(binaryFolder, f))]:
                os.remove(fi)

        binaryFiles = []
        try:
            for fileName in self.assemblerFilesCreated:
                try:
                    subprocess.check_output("pasm -b " + fileName, shell=True, cwd=binaryFolder)
                    binFileCreated = os.path.split(fileName)
                    binFileCreated = binFileCreated[len(binFileCreated) - 1].replace('.p', '.bin')
                    binFileCreated = os.path.join(binaryFolder, binFileCreated)
                    log.debug('Successfully compiled %s at %s' % (fileName, binFileCreated))
                    binaryFiles.append(binFileCreated)
                    # delete the assembler file as they are practically usless beyond this point.
                    os.remove(fileName)
                    log.debug('%s assembler file deleted' % fileName)
                except subprocess.CalledProcessError, e:
                    log.error(e)
            log.info('%s binary files compiled successfully, failed files %s' % (
                len(binaryFiles), len(self.assemblerFilesCreated) - len(binaryFiles)))
            # add p files from header folder (reset PRU, Initialize Input, end Input)
            headerFolder = os.path.join(project_folder, 'src', self.headerFolder)
            pFiles = [os.path.join(headerFolder, f) for f in os.listdir(headerFolder) if
                      os.path.isfile(os.path.join(headerFolder, f)) and f.endswith('.p')]
            for p in pFiles:
                subprocess.check_output("pasm -b " + p, shell=True, cwd=binaryFolder)
                binFileCreated = os.path.split(p)
                binFileCreated = binFileCreated[len(binFileCreated) - 1].replace('.p', '.bin')
                binFileCreated = os.path.join(binaryFolder, binFileCreated)
                log.debug('Successfully compiled %s at %s' % (p, binFileCreated))
                binaryFiles.append(binFileCreated)
        except Exception, e:
            log.error(e)
            # raise
        return binaryFiles


if __name__ == '__main__':
    # Test
    import jtag_driver

    a = AtpToAssembler(os.path.join('patterns', 'led_test_4w.atp'))
    ouotput = os.path.join(project_folder, tempF, asseblerF)
    a.convertToAssembler(ouotput)
    binFiles = a.compileAssemblerFiles(os.path.join(project_folder, 'temp', 'bin'))
    print (binFiles)
    jtag_driver.powerDownJTAG()
    jtag_driver.powerUpJTAG()
    driver = jtag_driver.JTAGDriver(binFiles)
    driver.executeJTAGCommands()
    driver.logPRUMemContents()
    jtag_driver.compareResults(a.atpOutputSeq)
