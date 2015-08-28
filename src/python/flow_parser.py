from __future__ import print_function
import csv
import json
from global_variables import *

log = logging.getLogger(__name__)


class flowFileParser(object):
    def __init__(self):
        self.ignore = [
            'BIN',
            'JOB',
            'SOFTBIN',
            'PARAC'
        ]
        # Initialize the folder path and the files available
        self.flows_folder = os.path.join(project_folder, "flows")
        self.flow_files = [f for f in os.listdir(self.flows_folder) if
                           os.path.isfile(os.path.join(self.flows_folder, f))]
        # Object variables to store the return
        self.flows = []

    def parseFile(self, file):
        # Parse the file as a CSV
        with open(file, "rt") as f:
            reader = csv.DictReader(f)
            # Array of all the tests defined in this file
            # this will make sure the order of the tests defined in the file is
            # consistant with the order that we get here
            tests = []

            # Each row represents a test with a name and has parameters
            for row in reader:
                for key in row.keys():
                    if key in self.ignore:
                        row.pop(key)
                test = {"Name": row.pop("TEST"), 'Type': row.pop('TEMPLATE'), "Param": row}
                tests.append(test)
            return tests

    def parseAllFiles(self):
        # Get all the tests available in each of the file presetn in the folder
        for file in self.flow_files:
            # Each file has a list of tests called a flow
            # Flow in file is a dict of the file name and Flow which contains the array of all the tests (ordered)
            flowInFile = {"FileName": file, "Tests": self.parseFile(os.path.join(self.flows_folder, file))}

            # The flows variable is an array of all the FlowInFile and so will be ordered with the way the files are
            # read, so alphabetically (assiming the list of files returns an alphabetically sorted list)
            self.flows.append(flowInFile)
        return self.flows

    # This method is supposed to update the flow file which has been modified by the UI
    # the data sent back from the Server is a JSON object that contains the file name and
    # the
    def updateFile(self, JSONObject):

        updatedTest = json.loads(JSONObject)
        fileToBeModified = updatedTest["FileName"]
        fileToBeModified = os.path.join(self.flows_folder, fileToBeModified)
        testToBeModified = updatedTest["Name"]
        tempFile = os.path.join(self.flows_folder, "temp")
        try:
            # Now first we read the original rows in the file, and the copy them with modified data into a new temp file
            # after this is done for the whole file, we delete the original one and rename this one to the original file
            with open(fileToBeModified, "rt") as original:
                with open(tempFile, "wb") as out:
                    reader = csv.DictReader(original)
                    writer = csv.DictWriter(out, delimiter=',', fieldnames=reader.fieldnames)
                    writer.writeheader()
                    templateRow = None
                    found = False
                    for row in reader:
                        if row["TEST"] == testToBeModified:
                            found = True
                            for key in updatedTest['Param'].iterkeys():
                                row[key] = updatedTest['Param'][key]
                        writer.writerow(row)
                        templateRow = row
                    if not found:
                        templateRow["TEST"] = testToBeModified
                        for key in updatedTest['Param'].iterkeys():
                            try:
                                templateRow[key] = updatedTest['Param'].get(key, '')
                            except:
                                templateRow[key] = ''
                        writer.writerow(templateRow)
            if updatedTest['Type'] == 'FRAME_T':
                memoryFile = updatedTest['Param'].get('MEMORY', 'blank')
                memoryFile = os.path.join(project_folder,frame_test_F, frameMemoryFiles, memoryFile)
                if not os.path.isfile(memoryFile):
                    os.makedirs(os.path.dirname(memoryFile))
            # Now that the file is done, we delete the old file, and rename this new file as the original one
            os.remove(fileToBeModified)
            os.rename(tempFile, fileToBeModified)
            return "OK"
        except Exception, e:
            log.error('Error in updating flow file %s. ERROR:%s' % (fileToBeModified, e))

    def deleteSelectedTestFromFile(self, testName, fileName):
        fileToBeModified = os.path.join(self.flows_folder, fileName)
        testToBeDeleted = testName
        tempFile = os.path.join(self.flows_folder, "temp")
        with open(fileToBeModified, "rt") as original:
            with open(tempFile, "wb") as out:
                reader = csv.DictReader(original)
                writer = csv.DictWriter(out, delimiter=',', fieldnames=reader.fieldnames)
                writer.writeheader()
                for row in reader:
                    if row["TEST"] != testToBeDeleted:
                        writer.writerow(row)
        # Now that the file is done, we delete the old file, and rename this new file as the original one
        os.remove(fileToBeModified)
        os.rename(tempFile, fileToBeModified)
        return "OK"

    def deleteFlowFileWithName(self, name):
        try:
            os.remove(os.path.join(self.flows_folder, name))
            return "OK"
        except Exception, e:
            log.error('Error while deleting flow file %s, error message:%s' % (name, e))
            return e
