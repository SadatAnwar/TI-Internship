
debuggerApp.controller('framController', ['$scope','$location', function($scope) {
    /*
     Functions required for the FRAM page
     */
    $scope.onpageLoad = function () {
        // the routines that are to be executed when the page is loaded.
        //1. Check the power of the JTAG (JTAG VCC) and change the color of the button
        call_GET($scope, 'checkJTAGPower');

        call_GET($scope, 'readFlows');
    };


    /*
     Handles the JTAG Power button
     */
    $scope.handleJTAGPower = function (state) {
        try {
            if (state.toLowerCase() == 'off') {
                jtagPower = false;
                document.getElementById('powerJTAG').classList.remove('btn-success');
                document.getElementById('powerJTAG').classList.add('btn-danger');
                document.getElementById('powerJTAG').innerHTML = 'power on JTAG'
            }
            if (state.toLowerCase() == 'on') {
                jtagPower = true;
                document.getElementById('powerJTAG').classList.add('btn-success');
                document.getElementById('powerJTAG').classList.remove('btn-danger');
                document.getElementById('powerJTAG').innerHTML = 'power off JTAG'
            }
        } catch (e) {
            //maybe this is a call that doesnot change the state but only updates the status, we then use the last state
            if (jtagPower) {
                document.getElementById('powerJTAG').classList.add('btn-success');
                document.getElementById('powerJTAG').classList.remove('btn-danger');
            } else {
                document.getElementById('powerJTAG').classList.remove('btn-success');
                document.getElementById('powerJTAG').classList.add('btn-danger');
            }
        }
    };

    /*
     The power is toggled at the server end, so that there are no accidental faults
     */
    $scope.toggleJTAGPower= function () {
        call_GET(this, 'toggleJTAGPower');
    };


//
//  Functions that are called after data from Python server is returned
//
    $scope.globalFlow = [];

    /*
     The method is called after the python server returns for the readFlows python call, once the call returns, it provides an argument Flows,
     this is a JSON object array that can have 1 or more Flows inside, each Flow has an array of tests, and each test has a test name and parameters
     this function takes these values and populates the global variables defined above to store the current state of the software
     */
    $scope.processFlows = function (flows) {
        // the result is an array of all the tests in a flow and may contain multiple flows (depending on files present in the folder)
        for (var i = 0; i < flows.length; i++) { // iterate all the flows and get the test and all its parameters
            flowName = flows[i].FileName;
            // now assign the test to the flow
            // first check if its already added to $scope.globalFlow or not
            var contains = false;
            for (var x = 0; x < $scope.globalFlow.length; x++) {
                if (flowName == $scope.globalFlow[x].FileName) {
                    contains = true;
                    break;
                }
            }
            if (contains) {
                $scope.globalFlow[x] = jQuery.extend(true, {}, flows[i]);
                continue;
            }
            $scope.globalFlow.push(jQuery.extend(true, {}, flows[i]));
        }
        $scope.updateFlowSelect();
    };
    $scope.flowView = [];
    $scope.updateFlowSelect = function() {
        for (var i = 0; i < $scope.globalFlow.length; i++) {
            flowName = $scope.globalFlow[i].FileName;
            // now populate the list in the HTML
            link = document.createElement('a');
            //Create a display name, remove FRAM_ and then crop from 0, till next _
            if (flowName.indexOf("FRAM_") > -1 && flowName.indexOf("__", flowName.indexOf("__") + 1)) {
                displayName = flowName.substring(5, flowName.length);
                displayName = displayName.substring(0, displayName.indexOf('__'));
                $scope.flowView.push(displayName);
                text = document.createTextNode(displayName);
            } else {
                text = document.createTextNode(flowName);
                $scope.flowView.push(flowName);
            }
            // if the ID already exists, i.e the element has already been created, go on to the next one
            if (document.getElementById(flowName)) {
                continue
            }
            link.setAttribute('class', 'list-group-item');
            link.setAttribute('id', flowName);
            link.setAttribute('onclick', 'javascript:loadTest("' + flowName + '"); return false;');
            link.setAttribute('href', '../flows/' + $scope.globalFlow[i].FileName);
            link.appendChild(text);
            document.getElementById('flowSelect').appendChild(link);
        }
        $scope.loadTest($scope.selectedFlow);
    };

    $scope.selectedFlow = null;

    $scope.loadTest = function (flow) {
        // update the flow currently selected
        if (flow) {
            $scope.selectedFlow = flow;
        } else {
            return;
        }
        //first remove the present elements in the Test List
        var testList = document.getElementById('testSelect');
        while (testList.lastChild) {
            testList.removeChild(testList.lastChild);
        }
        var tests;
        for (var i = 0; i, $scope.globalFlow.length; i++) {
            if (flow == $scope.globalFlow[i].FileName) {
                tests = $scope.globalFlow[i].Tests;
                break;
            }
        }
        for (var i = 0; i < tests.length; i++) {
            test = tests[i].Name;
            link = document.createElement('a');
            text = document.createTextNode(test);
            if (document.getElementById('test_' + test)) {
                continue
            }

            link.setAttribute('class', 'list-group-item');
            link.setAttribute('id', 'test_' + test);
            link.setAttribute('href', 'javascript:selectTest("' + test + '","' + flow + '")');
            link.appendChild(text);
            testList.appendChild(link);
        }
        if (tests.length > 0) {
            document.getElementById('addNewTest').setAttribute('onclick', 'javascript:addNewTestToFile("' + flow + '")');
            document.getElementById('addNewTest').setAttribute('data-target', "#setupModalWindow");
        } else {
            document.getElementById('addNewTest').setAttribute('onclick', 'javascript:alert("Cannot add to empty file, please make sure file has at least one test")');
            document.getElementById('addNewTest').setAttribute('data-target', "");
        }
        $scope.updateFlowSelectView();
    };

    $scope.updateFlowSelectView = function () {
        if ($scope.selectedFlow) {
            //firest remove the highlight from the old owner
            var flowSelectElements = document.getElementById('flowSelect').childNodes;
            for (var i = 0; i < flowSelectElements.length; i++) {
                if (flowSelectElements[i].nodeName == "A") {
                    flowSelectElements[i].classList.remove('list-group-item-danger');
                }
            }
            var selection = document.getElementById($scope.selectedFlow);
            selection.classList.add("list-group-item-danger");
            var deleteButton = document.getElementById("delFlow");
            deleteButton.setAttribute('onclick', 'javascript:deleteFlow("' + $scope.selectedFlow + '")');
            var downloadButton = document.getElementById("downloadFlow");
            downloadButton.setAttribute ('href', '../flows/'+$scope.selectedFlow);
        }
    };


    $scope.currentSelectedTest = null;

    $scope.selectTest = function (testName, flowName) {
        var found = false;
        var flowIndex = -1;
        for (var x = 0; x < $scope.globalFlow.length; x++) {
            if (flowName == $scope.globalFlow[x].FileName) {
                flowIndex = x;
                break;
            }
        }
        for (var i = 0; i < $scope.globalFlow[flowIndex].Tests.length; i++) {
            if (testName == $scope.globalFlow[flowIndex].Tests[i].Name) {
                $scope.currentSelectedTest = $scope.globalFlow[flowIndex].Tests[i];
                $scope.currentSelectedTest['FileName'] = $scope.globalFlow[flowIndex].FileName;
                document.getElementById('delTest').setAttribute('onclick', 'javascript:deleteSelectedTest("' + testName + '","' + $scope.globalFlow[flowIndex].FileName + '")');
                found = true;
                $scope.updateTestSelectView();
                break;
            }
        }
    };


    $scope.updateTestSelectView =  function () {
        var testList = document.getElementById('testSelect');
        var testElements = testList.getElementsByTagName('*');
        for (var i = 0; i < testElements.length; i++) {
            e = testElements[i];
            if (e.classList.contains("list-group-item-danger")) {
                e.classList.remove("list-group-item-danger");
            }
        }
        var selection = document.getElementById('test_' + $scope.currentSelectedTest.Name);
        selection.classList.add("list-group-item-danger");
    };

    $scope.testSequence = [];

    $scope.addTestToSeq = function () {
        var found = false;
        for (var x = 0; x < $scope.globalFlow.length; x++) {
            for (var i = 0; i < $scope.globalFlow[x].Tests.length; i++) {
                if ($scope.currentSelectedTest == $scope.globalFlow[x].Tests[i]) {
                    $scope.testSequence.push($scope.globalFlow[x].Tests[i]);
                    found = true;
                    break;
                }
            }
            if (found) {
                break;
            }
        }
        $scope.updateTestSeq();
    };

    $scope.addAllTestSeq = function () {
        //Add all tests of the current flow to test seq
        // current seslected flow is in variable selectedFlow
        // first clear the current testSeq list
        for (var x = 0; x < $scope.globalFlow.length; x++) {
            if ($scope.selectedFlow == $scope.globalFlow[x].FileName) {
                $scope.testSequence = JSON.parse(JSON.stringify($scope.globalFlow[x].Tests));
                break;
            }
        }
        $scope.updateTestSeq();
    };


    $scope.removeTestSeq = function (i, test) {
        if (test) {
            var index = i;
            $scope.testSequence.splice(index, 1);
        } else { /// The call came from the delete button, and so we delete the test that is currently selected from test select list and if not present do nothing
            for (var i = 0; i < $scope.testSequence.length; i++) {
                if ($scope.currentSelectedTest == $scope.testSequence[i]) {
                    index = i;
                    $scope.testSequence.splice(index, 1);
                    break;
                }
            }
        }
        $scope.updateTestSeq();
    };

    $scope.removeAllTestSeq = function () {
        $scope.testSequence = [];
        $scope.updateTestSeq();
    };

    function updateTestSeq() {
        var seq = document.getElementById('sequence');
        //first remove the present elements in the Test List
        while (seq.lastChild) {
            seq.removeChild(seq.lastChild);
        }
        //now add the new ones
        for (var i = 0; i < $scope.testSequence.length; i++) {
            link = document.createElement('a');
            text = document.createTextNode($scope.testSequence[i].Name);
            link.setAttribute('class', 'list-group-item');
            link.setAttribute('id', 'testSeq_' + $scope.testSequence[i].Name);
            link.setAttribute('href', 'javascript:removeTestSeq(' + i + ',"' + $scope.testSequence[i].Name + '")');
            link.appendChild(text);
            seq.appendChild(link);
        }
    }

    $scope.runTestSeq = function () {
        // Send the cuttent testSequence object as string to the Python server and that should then take care of the
        //execution
        call_POST('executeTestSequence', JSON.stringify($scope.testSequence));
    };

    $scope.readSingleFile = function (evt) {
        var f = evt.target.files[0];
        if (f) {
            var r = new FileReader();
            r.onload = function (e) {
                var contents = e.target.result;
                var fileName = escape(f.name);
                call_GET("uploadFiles", 'Flows', fileName, contents);

            };
            r.readAsText(f);
        } else {
            humaneAlert("Failed to load file");
        }
    };

    $scope.getParameterByName = function (name) {
        var match = new RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
        return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
    };

    $scope.modifySelectedTest = function () {
        if ($scope.currentSelectedTest) {
            test = $scope.currentSelectedTest;
            makeCurrentSelections();
        }
    };

    $scope.deleteFlow = function (flowName) {
        call_GET('deleteFlowFileWithName', flowName);
    };

    $scope.deleteSelectedTest = function (testName, fileName) {
        call_GET('deleteSelectedTestFromFile', testName, fileName);
    };

    if (window.File && window.FileReader && window.FileList && window.Blob) {
        document.getElementById('fileUpload').addEventListener('change', $scope.readSingleFile, false);
    } else {
        humaneAlert('The File APIs are not fully supported by your browser.');
    }
    $scope.onpageLoad();
}]);