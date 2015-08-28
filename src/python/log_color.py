#!/usr/bin/env python
# encoding: utf-8
import logging
from websocket_server import ws
# now we patch Python code to add color support to logging.StreamHandler

logFileWriter = False
# The webLogLevel is used to control logging on the webUI
webLogLevel = 20
testLogFile = None


def setWebLogLevel(level):
    global webLogLevel
    webLogLevel = level


def setTestFileLog(name):
    global testLogFile
    testLogFile = name
    pass


def removeTestFileLog():
    global testLogFile
    testLogFile = None
    pass


def add_coloring_to_emit_ansi(fn):
    # add methods we need to the class
    def new(*args):
        logOnUi = False
        levelno = args[1].levelno
        logMessage = str(args[1].msg).split(':::')
        colorText = ''
        level = 0
        if len(logMessage) == 4:
            if logMessage[0] == 'UI':
                logOnUi = True
            colorText = logMessage[1]
            level = int(logMessage[2])
            logText = logMessage[3]
        else:
            logText = str(args[1].msg)
        if levelno >= 50:
            color = '\x1b[31m'  # red
            logLevel = 'CRITICAL'
        elif levelno >= 40:
            color = '\x1b[31m'  # red
            logLevel = 'ERROR'
        elif levelno >= 30:
            color = '\033[93m'  # yellow
            logLevel = 'WARNING'
        elif levelno >= 20:
            color = '\033[92m'  # green
            logLevel = 'INFO'
        else:
            color = '\x1b[0m'  # normal
            logLevel = 'DEBUG'
        if ws is not None and logOnUi and level >= webLogLevel:
            logMsg = '%s:::%s:::%s' % (colorText, logLevel, logText)
            ws.sendData(str(logMsg))
            if testLogFile is not None:
                with open(testLogFile, 'a') as log:
                    log.writelines('[%s]-(%s)-- %s\n' % (logLevel, colorText, logText))
        args[1].msg = color + logText + '\x1b[0m'  # normal
        # print "after"
        return fn(*args)

    return new
# all non-Windows platforms are supporting ANSI escapes so we use them
logging.StreamHandler.emit = add_coloring_to_emit_ansi(logging.StreamHandler.emit)
