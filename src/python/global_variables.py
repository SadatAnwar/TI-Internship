__author__ = 'x0234668'

import logging
import os
import ConfigParser
import platform
import log_color as logHelper
if platform.system() == 'Windows':
    project_folder = os.environ["BENCH_DEBUGGER"]
else:
    project_folder = '/root/benchDebugger'
CONFIG_FILE = os.path.join(project_folder, "config.ini")
# Get a hold of the config file
Config = ConfigParser.ConfigParser()
# log file
config = ConfigParser.RawConfigParser()
config.read(CONFIG_FILE)
logFileName = config.get('LOGGING', 'logFileName')
logToFile = config.getboolean('LOGGING', 'logToFile')
logLevel = int(config.get('LOGGING', 'logLevel'))
webLogLevel = int(config.get('LOGGING', 'webloglevel'))
logHelper.setWebLogLevel(int(webLogLevel))
LOG_FILE = os.path.join(project_folder, logFileName)
if not logToFile:
    LOG_FILE = None
logging.basicConfig(level=logLevel, filename=LOG_FILE,
                    format='[%(levelname)s] %(name)s:(%(threadName)-s): %(message)s')

# Define some usualy used variables for folder names
tempF = 'temp'
asseblerF = 'assembler'
binaryF = 'bin'
atpF = 'atp'
frame_test_F = 'frame_test'
patternsF = 'patterns'
frameMemoryFiles = 'files'
systemAlive = True

def killSystem():
    global systemAlive
    systemAlive = False

def isSystemAlive():
    return systemAlive
