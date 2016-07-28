#!/usr/bin/python

"""
This is the main server script that runs to host the entire application. All functions that are
to be executed at the server side must first be registered with the server using the

BBIOServer.registerFunction(function, functionName)

this registeres the function with its name as ID (so make sure no functions have same name !obvious)
and then the function needs to call the call_function javascript function and properly implement it
or just create a GET request with the function function_id parameter specifying the function name,
also NOTE: the do_GET function has to be modified evetytime a new function is added to work nicely with it.

"""

import json
import shutil
import threading
import time
import sys
import src.python.flow_parser as parser
import src.python.server as benchDebuggerServer
from src.python.mem_dump_er import MemLoadEr
from src.python.global_variables import *
from src.python.test_execution import compileTest, executeTests
from src.python.websocket_server import framPageSocket

try:
    import src.python.jtag_driver as JTAG
except:
    pass
__main__ = 'BenchDebugger'
log = logging.getLogger(__name__)


# Global handlers
memoryDumpHandler = MemLoadEr()
# This list maps the file type to a folder in the project structure
folderTypes = {'Flows': 'flows',
               'ATPMemWriteTemplate': os.path.join('memoryDump', 'atpMemWriteTemplate'),
               'ATPTestTemplate': 'atpTestTemplate',
               'MemDump': os.path.join('memoryDump', 'dump.txt'),
               'LogFiles': 'logs',
               'FramePattern': os.path.join(frame_test_F, patternsF),
               'FrameFiles': os.path.join(frame_test_F, frameMemoryFiles)
               }

# Start the web-socket server
executeTest = True
testExecutionInProgress = False

def executeTestThread(UID, logFileName, executionTimes, executionDelay):
    """This function executes the test for more than one times, the test is stopped by setting the
    executeTest boolean to false, this will prevent the loop form starting next time. since this loops the
    cpu this method must be called in a seperate thread, or else everything will hang."""
    global executeTest
    global testExecutionInProgress
    testExecutionInProgress = True
    try:
        logHelper.setTestFileLog(logFileName)
        if int(executionTimes) == 0:
            while executeTest:
                try:
                    executeTests(UID)
                except Exception, e:
                    log.error(e)
                    log.error('UI:::RED:::20:::%s' % str(e))
                    time.sleep(2)
                log.info('UI:::lightBlue:::10:::Sleep %s seconds' % executionDelay)
                time.sleep(int(executionDelay))
            log.info('UI:::YELLOW:::20:::Execution stopped')
            framPageSocket.sendData('alert:::Execution stopped')
        else:
            for i in range(0, int(executionTimes)):
                if not executeTest:
                    framPageSocket.sendData('alert:::Execution stopped')
                    break
                try:
                    executeTests(UID)
                    log.info('UI:::lightBlue:::10:::Sleep %s seconds' % executionDelay)
                except Exception, e:
                    log.error(e)
                    log.error('UI:::RED:::20:::%s' % str(e))
                    raise
                time.sleep(int(executionDelay))
            log.info('UI:::GREEN:::20:::Execution complete')
    except Exception, e:
        log.error(e)
    logHelper.removeTestFileLog()
    testExecutionInProgress = False
    return

#################################################################################################
#################################################################################################
# Functions that we will be using are to be defined here and then attached to the main server   #
# using the registerFunction along with a unique name, this name should be used by javascript   #
# to link the function                                                                          #
#################################################################################################
#################################################################################################
# Function declaration scheme:                                                                  #
# 1. The function name used in this script should be used exactly in the javascript call_GET    #
#    and call_POST calls. The javascript must also contain the exact number of parameters, in   #
#    the right sequence to execute the functions here correctly.                                #
# 2. The return value of the function here MUST be (parameter, functionName) where parameter    #
#    is the parameters that the function inside the javascript code will be called when the call#
#    returns. The parameter has certain keywords that will trigger specific actions on the web- #
#    page (all case insensitive):
#           1. OK - The javascript will show a green success message, saying (functionName)     #
#              retured with success message.
#           2. SILENT - This keyword will make sure the najascript call-back does nothing, so   #
#              call will be silent and go un-noticed to the user.
#           3. ERROR - If the parameter, contains the word error inside it will trigger an error#
#              alert message on the UI which is a RED notification box, to give a visual error  #
#              feeldback.
#           4. For all other values, the callBack function will consider the parameter, to be a #
#              single text parameter for a javascript function named functionName and will call #
#              this function along with parameter. Usually (but not always) the parameter is a  #
#              JSON string and is further parsed inside the called function to get more meaning-#
#              ful data and then work on it.
#################################################################################################
#################################################################################################
defaultFunctions = dir()


def restartServer():
    log.info('Restarting server')
    logHelper.ws.close()
    log.debug('logging web-socket closed')
    framPageSocket.close()
    log.debug('fram page web socket closed')
    server.stop()
    log.debug('http server closed')
    name = __file__
    if project_folder not in name:
        name = os.path.join(project_folder, name)
    time.sleep(10)
    log.debug('restarting server now.... %s' % name)
    os.execv(sys.executable, [sys.executable] + [name])


def logger(functionName, message, level="LOG"):
    if level == 'LOG':
        log.debug("CALLED from %s: \t%s" % (functionName, message))
    if level == 'ERROR':
        log.error("CALLED from %s: \t%s" % (functionName, message))


def readFlows():
    flowParser = parser.flowFileParser()
    flows_folder = os.path.join(project_folder, "flows")
    logger("readFlows", "Reading Flows folder: %s" % flows_folder)
    return_data = flowParser.parseAllFiles()
    return return_data, 'processFlows'


# Udate a test in the flow file
def updateTestInFile(JSONObject):
    flowParser = parser.flowFileParser()
    ret = flowParser.updateFile(JSONObject)
    if ret.lower() == 'ok':
        return readFlows()
    else:
        return 'ERROR', ''


def uploadFiles(folderType, fileName, contents):
    log.debug('uploading file %s file name' % fileName)
    if folderType in folderTypes:
        try:
            folder = os.path.join(project_folder, folderTypes[folderType])
            file_name = os.path.join(folder, fileName)
            # there is only one memory dump called dump.txt
            if folderType in 'uploadMemDump':
                file_name = folder
                config.read(CONFIG_FILE)
                config.set("FRAM_SETTING", "DUMP_FILE_NAME", fileName)
                with open(CONFIG_FILE, 'wb') as configfile:
                    config.write(configfile)
                with open(file_name, 'w') as f:
                    f.write(contents)
                return file_name, 'processMemoryDump'
            else:
                config.read(CONFIG_FILE)
                config.set("FRAM_SETTING", folderType + '_path', folder)
                with open(file_name, 'w') as f:
                    f.write(contents)
                with open(CONFIG_FILE, 'wb') as configfile:
                    config.write(configfile)
        except IOError as (errno, strerror):
            logger('uploadFiles', message="I/O error(%s): {%s}" % (errno, strerror), level='ERROR')
            return "Error", ''
    else:
        logger('uploadFiles', 'Upload type couldnot be matched to a folder', level='ERROR')
        return "Error", ''
    return '', 'onPageLoad'


def getFilesInFolder(folderType):
    if folderType in 'MemDump':
        config.read(CONFIG_FILE)
        files = config.get('FRAM_SETTING', 'DUMP_FILE_NAME')
    else:
        folder = os.path.join(project_folder, folderTypes[folderType])
        mtime = lambda f: os.stat(os.path.join(folder, f)).st_mtime
        files = [f for f in list(sorted(os.listdir(folder), key=mtime)) if os.path.isfile(os.path.join(folder, f))]
    return json.dumps(files), ''


def getConfigValues():
    config.read(CONFIG_FILE)
    return json.dumps(config._sections), ''


def deleteFilesInFolder(folderType, fileName):
    folder = os.path.join(project_folder, folderTypes[folderType])
    fileName = os.path.join(folder, fileName)
    try:
        if os.path.isfile(fileName):
            os.remove(fileName)
            return '', 'onPageLoad'
        else:
            logger('deleteFilesInFolder', 'File %s doesnot exist' % fileName)
            return "Error", ''
    except IOError:
        logger('deleteFilesInFolder', 'IO Error, unable to delete %s' % fileName)
        return 'Error', ''


# The testExecutionLock makes sure that there is only one test being executed at one time
def executeTestSequence(UID, executionTimes, executionDelay):
    global executeTest
    executeTest = True
    config.read(CONFIG_FILE)
    testLog = config.get('LOGGING', 'testlogfile')
    logFileName = None
    if testLog == '1':
        timestr = time.strftime("%d-%m.%H%M%S")
        logFileName = os.path.join(project_folder, 'logs', 'TestExecutionLog-%s.log' % timestr)
        log.info('Will be logged to file %s' % logFileName)

    try:
        if int(executionTimes) == 1:
            logHelper.setTestFileLog(logFileName)
            for i in range(0, int(executionTimes)):
                executeTests(UID)
            logHelper.removeTestFileLog()
        else:
            threading.Thread(target=executeTestThread,
                             args=(UID, logFileName, executionTimes, executionDelay,)).start()
    except Exception, e:
        logHelper.removeTestFileLog()
        log.error(e)
        return 'Error: %s' % e, ''
    return 'OK', ''

#Line added in branch1
#Line added in branch1
def stopRunningTest():
    global executeTest
    executeTest = False
    log.info('Stopping test...')
    return 'OK', ''


def checkTestExecutionProgress():
    global testExecutionInProgress
    if testExecutionInProgress:
        framPageSocket.sendData('open:::logs')
    return 'silent', ''


def compileTestSequence(JSONObject):
    tests = json.loads(JSONObject)
    compiledTests = compileTest(tests, JSONObject)
    return compiledTests, 'updateCompiledTest'


def deleteFlowFileWithName(fileName):
    flowParser = parser.flowFileParser()
    ret = flowParser.deleteFlowFileWithName(fileName)
    if ret.lower() == 'ok':
        return 'reload', ''
    else:
        return ret, ''


def deleteSelectedTestFromFile(testName, fileName):
    flowParser = parser.flowFileParser()
    try:
        ret = flowParser.deleteSelectedTestFromFile(testName, fileName)
        if ret.lower() == 'ok':
            return readFlows()
        else:
            log.error(ret)
            return ret, ''
    except Exception, e:
        log.error(e)
        return 'Error', ''


def updateUserLogIn(username, password):
    if os.path.isfile(CONFIG_FILE):
        config.read(CONFIG_FILE)
        config.set("AUTHENTICATION", "UserName", username)
        config.set("AUTHENTICATION", 'Password', password)
        with open(CONFIG_FILE, 'wb') as configfile:
            config.write(configfile)
        return "OK", ''
    else:
        logger('updateUserLogIn', 'Unable to locate "config.ini". Please make sure it is present in the project folder')
        return "ERROR", ''


def updateFRAMSettings(testTemplate, memWriteTemplate, consoleLog, webLog, testlogfile):
    if os.path.isfile(CONFIG_FILE):
        config.read(CONFIG_FILE)
        config.set("FRAM_SETTING", "ATP_TEST_TEMPLATE", testTemplate)
        config.set("FRAM_SETTING", 'ATP_MEM_WR_TEMPLATE', memWriteTemplate)
        config.set("LOGGING", 'loglevel', consoleLog)
        config.set("LOGGING", 'webLogLevel', webLog)
        config.set("LOGGING", 'testlogfile', testlogfile)
        logHelper.setWebLogLevel(int(webLog))
        with open(CONFIG_FILE, 'wb') as configfile:
            config.write(configfile)
        return "OK", ''
    else:
        logger('updateUserLogIn', 'Unable to locate "config.ini". Please make sure it is present in the project folder')
        return "ERROR", ''


def processMemoryDump():
    global memoryDumpHandler
    return memoryDumpHandler.writeTempATP(), 'makeMemDumpAssembly'


def makeMemDumpAssembly():
    global memoryDumpHandler
    outSeq = memoryDumpHandler.assemblyWriter.convertToAssembler(
        os.path.join(project_folder, 'memoryDump', 'assembler'))
    return len(memoryDumpHandler.assemblyWriter.assemblerFilesCreated), 'makeMemDumpBinary'


def makeMemDumpBinary():
    global memoryDumpHandler
    binFiles = memoryDumpHandler.compileBinaries('bin')
    # we can now delete the assembler folder, as that data is useless
    assemblerFolder = os.path.join(project_folder, 'memoryDump', 'assembler')
    # remove the folder recurssively
    shutil.rmtree(assemblerFolder)
    # Now write all this to the config file to make it permanent
    log.debug(memoryDumpHandler.BIN_FOLDER)
    config.read(CONFIG_FILE)
    config.set("BIN_FILES", "MEM_DUMP_BIN_FOLDER", memoryDumpHandler.BIN_FOLDER)
    config.set("BIN_FILES", "MEM_DUMP_BIN_COUNT", len(binFiles))
    with open(CONFIG_FILE, 'wb') as configfile:
        config.write(configfile)
    return len(binFiles), ''


def writeDeviceMem():
    # First read the config file, for the bin folder and the number of binary files to varify if all is correct
    config.read(CONFIG_FILE)
    binFileFolder = config.get('BIN_FILES', 'mem_dump_bin_folder')
    binFileCount = config.get('BIN_FILES', 'mem_dump_bin_count')
    log.debug('Folder: "%s" Count of Files:%s' % (binFileFolder, binFileCount))
    # now we read the folder and match the file count
    binFiles = [os.path.join(binFileFolder, f) for f in os.listdir(binFileFolder) if f.endswith('.bin')]
    # varify count
    if len(binFiles) != int(binFileCount):
        log.error('Count of binary files doesnot match!')
    else:
        try:
            driver = JTAG.JTAGDriver(binFiles)
            driver.executeJTAGCommands()
            try:
                JTAG.compareResults(memoryDumpHandler.assemblyWriter.atpOutputSeq)
            except Exception, e:
                log.error(e)
                log.warning(
                    "The result could not be varified, as the server was restarted after uploading a memory file")
            return 'OK', ''
        except Exception, e:
            log.error('Error writing memory dump over JTAG ERROR:%s' % e)
            return 'Error: %s' % e, ''


def toggleJTAGPower():
    # check if the JTAG interface has power, and then toggle it
    if JTAG.JTAGPower:
        state = JTAG.powerDownJTAG()
    else:
        state = JTAG.powerUpJTAG()
    log.info('JTAG Power state is: %s will be toggled' % state)
    return checkJTAGPower()


def checkJTAGPower():
    # handle the checking powerlogic, for now always return off
    if JTAG.JTAGPower:
        powerState = 'on'
    else:
        powerState = 'off'
        log.debug('JTAG power state checked, status is ' + powerState)
    return powerState, 'handleJTAGPower'

#################################################################################################
#################################################################################################
# End of user defined functions for web server
#################################################################################################
#################################################################################################

myFunctions = list(set(dir()) - set(defaultFunctions))
# Remove the variable defaultFunct
# register the functions with their names
server = benchDebuggerServer.BBIOServer()
for function in myFunctions:
    # Just to be sure we are adding only functions
    if hasattr(locals()[function], '__call__'):
        server.registerFunction(function, locals()[function])

logging.debug("All functions registered successfully, starting server.....")
# Start the server
server.start()
