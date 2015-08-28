from global_variables import *

log = logging.getLogger(__name__)


class AtpFromTemplateWriter(object):
    """ This class is used to write ATP files from template and data. The template file has to passed in as a
     parameter for the constructor, and the class then maps to this file. Later data can be passed into this
     class and the output will be a final ATP file. """

    def __init__(self, templateFile):
        self.loop = False
        self.endIndex = None
        self.startIndex = None
        self.WriteMem = False
        self.ReadMem = False
        self.addressBit = 0
        self.dataBit = 0
        self.loopTemplate = []
        self.templateFile = templateFile
        if os.path.isfile(self.templateFile):
            log.debug('%s File will be used as template' % self.templateFile)
        elif project_folder not in self.templateFile:
            log.warn('%s Template file doesnot exist, trying to find file at %s' % (
                self.templateFile, os.path.join(project_folder, self.templateFile)))
            if os.path.isfile(os.path.join(project_folder, templateFile)):
                self.templateFile = os.path.join(project_folder, templateFile)
                log.debug('Template found %s, will be used. ' % self.templateFile)
        else:
            raise IOError('Template File doesnot exist')
        self.__analyzeATP__()

    def __analyzeATP__(self):
        """ Analyze the ATP file  """
        guessed = False
        # First look for a loop statement
        with open(self.templateFile, 'rU') as template:
            lines = template.readlines()
            for i in range(0, len(lines)):
                line = lines[i]
                if self.loop and self.endIndex is None and not guessed:
                    # Guess the type of loop
                    if '#include' in line:
                        if 'writememword' in line.lower():
                            self.WriteMem = True
                            guessed = True
                        if 'readmemword' in line.lower():
                            self.ReadMem = True
                            guessed = True
                if line.startswith('//') or line.startswith('/*'):
                    # Ignore lines that are comments
                    continue

                if 'loop' in line and 'end' not in line:
                    # The file does contain a loop, set the self.loop flag to true, now try to guess if its
                    # a writeMem word loop or readMem loop (usually only 2 types)
                    self.loop = True
                    self.startIndex = i
                if 'end_loop' in line:
                    if not self.startIndex:
                        raise ATPTemplateException('Invalid ATP Template, end_loop encountered without any start')
                    self.endIndex = i
                    break
            if self.loop and self.endIndex is None:
                # We validate the loop
                raise ATPTemplateException('Invalid ATP Template, no end_loop statement found')

            if self.loop:
                # If the file has a valid loop, then we save this part
                for i in range(self.startIndex + 1, self.endIndex):
                    line = lines[i]
                    self.loopTemplate.append(line)

            for i in range(0, len(lines)):
                # Count the number of A's and D's to validate the Data when we get it
                line = lines[i]
                if not line.startswith('/') and len(line) > 43:
                    if line[43] == 'A':
                        self.addressBit += 1
                    elif line[43] == 'D':
                        self.dataBit += 1
            log.info('Template has %s D\'s and %s A\'s' % (self.dataBit, self.addressBit))

    def generateATP(self, data, atpFile):
        """ Here the data has to be relevant to the template with which the object is created"""
        if os.path.isfile(atpFile):
            os.remove(atpFile)
            log.warn('File %s already exsists, will be overwritten' % atpFile)
        if self.WriteMem:
            self._writeMemWordLoop(data, atpFile)
        elif self.ReadMem:
            self._readMemWordLoop(data, atpFile)
        else:
            self._overlayDataOnTemplate(data, atpFile)

    def _overlayDataOnTemplate(self, data, atpFile):
        # First we check the size of data we have, i.e. total bits
        bits = len(data)
        b = 0
        if bits != self.dataBit:
            raise ATPTemplateException(
                'Bits in input(%s) dont match number of place holders(%s) in template' % (bits, self.dataBit))
        dir = os.path.dirname(atpFile)
        if not os.path.exists(dir):
            os.makedirs(dir)
        with open(atpFile, 'w') as temp:
            with open(self.templateFile, 'rU') as template:
                lines = template.readlines()
            for i in range(0, len(lines)):
                # Write the part of the file before the loop
                line = lines[i]
                if not (line.startswith('//') or line.startswith('/*')) and len(line) > 43:
                    if line[43] == 'D':
                        line = line[:43] + data[b] + line[44:]
                        b += 1
                temp.write(line)

    def _writeMemWordLoop(self, data, atpFile):
        if not os.path.isdir(os.path.dirname(atpFile)):
            os.makedirs(os.path.dirname(atpFile))
        with open(atpFile, 'w') as temp:
            with open(self.templateFile, 'rU') as template:
                lines = template.readlines()
            for i in range(0, self.startIndex):
                # Write the part of the file before the loop
                line = lines[i]
                temp.write(line)
            for addrData in data:
                # Iterate over all the elements in address data pair and loop over the write_mem_word segment
                add = addrData.keys()[0]
                data = addrData[add]
                addressBit = 0
                dataBit = 0
                for line in self.loopTemplate:
                    if len(line) > 43:
                        if line[43] == 'A':
                            line = line[:43] + add[addressBit] + line[44:]
                            addressBit += 1
                        elif line[43] == 'D':
                            line = line[:43] + data[dataBit] + line[44:]
                            dataBit += 1
                    if len(line) < 5 or line.startswith('//') or line.startswith('/*'):
                        if "#include" not in line:
                            continue
                        if '#include' in line:
                            line = '//#include "i_WriteMemWord.edt" %s  %s\n' % (
                                hex(int(add, 2)).upper(), hex(int(data, 2)).upper())
                    temp.write(line)
                temp.write('\n')
            for i in range(self.endIndex + 1, len(lines)):
                # Write the part after the loop
                line = lines[i]
                temp.write(line)

    def _readMemWordLoop(self, address, atpFile):
        if not os.path.isdir(os.path.dirname(atpFile)):
            os.makedirs(os.path.dirname(atpFile))
        with open(atpFile, 'w') as temp:
            with open(self.templateFile, 'rU') as template:
                lines = template.readlines()
            for i in range(0, self.startIndex):
                # Write the part of the file before the loop
                line = lines[i]
                temp.write(line)
            for add in address:
                addressBit = 0
                for line in self.loopTemplate:
                    if len(line) > 43:
                        if line[43] == 'A':
                            line = line[:43] + add[addressBit] + line[44:]
                            addressBit += 1
                    if len(line) < 5 or line.startswith('//') or line.startswith('/*'):
                        if "#include" not in line:
                            continue
                        if '#include' in line:
                            line = '//#include "i_ReadMemWord.edt" %s  \n' % (hex(int(add, 2)).upper())
                    temp.write(line)
                temp.write('\n')
            for i in range(self.endIndex + 1, len(lines)):
                # Write the part after the loop
                line = lines[i]
                temp.write(line)

class ATPTemplateException(Exception):
    def __init__(self, message):
        self.message = 'ATPTemplateException :' + message
        log.error(self.message)

# Test Case
if __name__ == '__main__':
    a = AtpFromTemplateWriter(os.path.join(project_folder, 'atpTestTemplate', 'FRAM_template.atp'))
    data = '{0:064b}'.format(0x03)
    a.generateATP(data, os.path.join(project_folder, 'temp', 'test123.atp'))
