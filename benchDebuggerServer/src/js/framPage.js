/*
Functions required for the FRAM page
 */

function onPageLoad() {
    // the routines that are to be executed when the page is loaded.
    //1. Check the power of the JTAG (JTAG VCC) and change the color of the button
    call_GET('readFlows');
    call_GET('checkJTAGPower');
    call_GET('checkTestExecutionProgress');


}
var host = "ws://" + window.location.hostname + ":6789/";
var socket = new WebSocket(host);
socket.onopen = function(e) {
    console.log('Socket connected');
};

socket.onmessage = function(e) {
    var level = e.data.split(':::')[0];
    var message = e.data.split(':::')[1];
    var errorMessage = e.data.split(':::')[2];
    if (level == 'ping') {
        s.send('pong');
    } else {
        if (level == 'progress') {
            var icon = document.getElementById('icon_overlay_div_' +
                message);
            var text = document.getElementById('test_name_overlay_div_' +
                message);
            icon.setAttribute('class', 'fa fa-spinner fa-spin');
            icon.style.color = 'orange';
            text.style.color = 'orange';
        }
        if (level == 'success') {
            var icon = document.getElementById('icon_overlay_div_' +
                message);
            var text = document.getElementById('test_name_overlay_div_' +
                message);
            icon.style.color = 'green';
            icon.setAttribute('class', 'fa fa-check');
            text.style.color = 'green';
        }
        if (level == 'error') {
            var icon = document.getElementById('icon_overlay_div_' +
                message);
            var text = document.getElementById('test_name_overlay_div_' +
                message);
            if (errorMessage != null){
                text.innerHTML = text.innerHTML + ' \t Error:' + errorMessage;
            }
            icon.style.color = 'red';
            icon.setAttribute('class', 'fa fa-times');
            text.style.color = 'red';
        }
        if (level == 'alert') {
            humaneAlert(message);
        }
        if (level == 'notify') {
            notify(message);
        }
        if (level == 'open') {
            if (message == 'logs') {
                if (myWindow == null || myWindow.closed) {
                    var left = screen.width;
                    var width = $(document).width();
                    var height = $(document).height();
                    window.open('log.html?trigger=0', "LogWindow",
                        "toolbar=No, navigation=No, locationbar= No, scrollbars=yes, resizable=yes, " +
                        "top=5, left=" + left + "px, " +
                        "width=" + width * 0.8 + "px, height=" + height *
                        0.7 + 'px');
                }
            }
        }
    }
};
/*
 Handles the JTAG Power button
 */
function handleJTAGPower(state) {
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
}

/*
 The power is toggled at the server end, so that there are no accidental faults
 */
function toggleJTAGPower() {
    call_GET('toggleJTAGPower');
}


//
//  Functions that are called after data from Python server is returned
//
var globalFlow = [];

/*
 The method is called after the python server returns for the readFlows python call, once the call returns, it provides an argument Flows,
 this is a JSON object array that can have 1 or more Flows inside, each Flow has an array of tests, and each test has a test name and parameters
 this function takes these values and populates the global variables defined above to store the current state of the software
 */
function processFlows(flows) {
    // the result is an array of all the tests in a flow and may contain multiple flows (depending on files present in the folder)
    for (var i = 0; i < flows.length; i++) { // iterate all the flows and get the test and all its parameters
        flowName = flows[i].FileName;
        // now assign the test to the flow
        // first check if its already added to globalFlow or not
        var contains = false;
        for (var x = 0; x < globalFlow.length; x++) {
            if (flowName == globalFlow[x].FileName) {
                contains = true;
                break;
            }
        }
        if (contains) {
            globalFlow[x] = jQuery.extend(true, {}, flows[i]);
            continue;
        }
        globalFlow.push(jQuery.extend(true, {}, flows[i]));
    }
    updateFlowSelect();
}

function updateFlowSelect() {
    for (var i = 0; i < globalFlow.length; i++) {
        flowName = globalFlow[i].FileName;
        // now populate the list in the HTML
        link = document.createElement('a');
        //Create a display name, remove FRAM_ and then crop from 0, till next _
        if (flowName.indexOf("FRAM_") > -1 && flowName.indexOf("__", flowName.indexOf(
                "__") + 1)) {
            displayName = flowName.substring(5, flowName.length);
            displayName = displayName.substring(0, displayName.indexOf('__'));
            text = document.createTextNode(displayName);
        } else {
            text = document.createTextNode(flowName);
        }
        // if the ID already exists, i.e the element has already been created, go on to the next one
        if (document.getElementById(flowName)) {
            continue;
        }
        link.setAttribute('class', 'list-group-item');
        link.setAttribute('id', flowName);
        link.setAttribute('onclick', 'javascript:loadTest("' + flowName +
            '"); return false;');
        link.setAttribute('href', '../flows/' + globalFlow[i].FileName);
        link.appendChild(text);
        document.getElementById('flowSelect').appendChild(link);
    }
    loadTest(selectedFlow);
}

var selectedFlow;

function loadTest(flow) {
    // update the flow currently selected
    if (flow) {
        selectedFlow = flow;
    } else {
        return;
    }
    //first remove the present elements in the Test List
    var testList = document.getElementById('testSelect');
    testList.innerHTML = '';
    var tests;
    for (var i = 0; i, globalFlow.length; i++) {
        if (flow == globalFlow[i].FileName) {
            tests = globalFlow[i].Tests;
            break;
        }
    }
    for (var i = 0; i < tests.length; i++) {
        test = tests[i].Name;
        link = document.createElement('a');
        text = document.createTextNode(test);
        if (document.getElementById('test_' + test)) {
            continue;
        }

        link.setAttribute('class', 'list-group-item');
        link.setAttribute('id', 'test_' + test);
        link.setAttribute('href', 'javascript:selectTest("' + test + '","' +
            flow + '")');
        link.appendChild(text);
        $(link).dblclick(function() {
            addTestToSeq();
        });
        testList.appendChild(link);
    }
    if (tests.length > 0) {
        document.getElementById('addNewTest').setAttribute('onclick',
            'javascript:addNewTestToFile("' + flow + '")');
        document.getElementById('addNewTest').setAttribute('data-target',
            "#setupModalWindow");
    } else {
        document.getElementById('addNewTest').setAttribute('onclick',
            'javascript:alert("Cannot add to empty file, please make sure file has at least one test")'
        );
        document.getElementById('addNewTest').setAttribute('data-target', "");
    }
    updateFlowSelectView();
}

function updateFlowSelectView() {
    if (selectedFlow) {
        //firest remove the highlight from the old owner
        var flowSelectElements = document.getElementById('flowSelect').childNodes;
        for (var i = 0; i < flowSelectElements.length; i++) {
            if (flowSelectElements[i].nodeName == "A") {
                flowSelectElements[i].classList.remove('list-group-item-danger');
            }
        }
        var selection = document.getElementById(selectedFlow);
        selection.classList.add("list-group-item-danger");
        var deleteButton = document.getElementById("delFlow");
        deleteButton.setAttribute('onclick', 'javascript:deleteFlow("' +
            selectedFlow + '")');
        var downloadButton = document.getElementById("downloadFlow");
        downloadButton.setAttribute('href', '../flows/' + selectedFlow);
    }
}


var currentSelectedTest;

function selectTest(testName, flowName) {
    var modTestButton = document.getElementById('modTest');
    modTestButton.setAttribute('onclick', 'javascript:modifySelectedTest()');
    var found = false;
    var flowIndex = -1;
    for (var x = 0; x < globalFlow.length; x++) {
        if (flowName == globalFlow[x].FileName) {
            flowIndex = x;
            break;
        }
    }
    for (var i = 0; i < globalFlow[flowIndex].Tests.length; i++) {
        if (testName == globalFlow[flowIndex].Tests[i].Name) {
            currentSelectedTest = globalFlow[flowIndex].Tests[i];
            currentSelectedTest['FileName'] = globalFlow[flowIndex].FileName;
            document.getElementById('delTest').setAttribute('onclick',
                'javascript:deleteSelectedTest("' + testName + '","' +
                globalFlow[
                    flowIndex].FileName + '")');
            found = true;
            if(currentSelectedTest.Type == 'INTERFACE_T'){
                modTestButton.setAttribute('data-target', '#framTestSetupModalWindow');
            } else if (currentSelectedTest.Type == 'FRAME_T'){
                modTestButton.setAttribute('data-target', '#frameSetupModalWindow');
            }
            updateTestSelectView();
            break;
        }
    }
}


function updateTestSelectView() {
    var testList = document.getElementById('testSelect');
    var testElements = testList.getElementsByTagName('*');
    for (var i = 0; i < testElements.length; i++) {
        e = testElements[i];
        if (e.classList.contains("list-group-item-danger")) {
            e.classList.remove("list-group-item-danger");
        }
    }
    var selection = document.getElementById('test_' + currentSelectedTest.Name);
    selection.classList.add("list-group-item-danger");
}

var testSequence = [];

function addTestToSeq() {
    var found = false;
    for (var x = 0; x < globalFlow.length; x++) {
        for (var i = 0; i < globalFlow[x].Tests.length; i++) {
            if (currentSelectedTest == globalFlow[x].Tests[i]) {
                testSequence.push(globalFlow[x].Tests[i]);
                found = true;
                break;
            }
        }
        if (found) {
            break;
        }
    }
    updateTestSeq();
}

function addAllTestSeq() {
    //Add all tests of the current flow to test seq
    // current seslected flow is in variable selectedFlow
    // first clear the current testSeq list
    for (var x = 0; x < globalFlow.length; x++) {
        if (selectedFlow == globalFlow[x].FileName) {
            testSequence = JSON.parse(JSON.stringify(globalFlow[x].Tests));
            break;
        }
    }
    updateTestSeq();
}


function removeTestSeq(i, test) {
    if (test) {
        var index = i;
        testSequence.splice(index, 1);
    } else { /// The call came from the delete button, and so we delete the test that is currently selected from test select list and if not present do nothing
        for (var i = 0; i < testSequence.length; i++) {
            if (currentSelectedTest == testSequence[i]) {
                index = i;
                testSequence.splice(index, 1);
                break;
            }
        }
    }
    updateTestSeq();
}

function removeAllTestSeq() {
    testSequence = [];
    updateTestSeq();
}

function updateTestSeq() {
    var seq = document.getElementById('sequence');
    var overlayContainer = document.getElementById('overlayContainer')
        //first remove the present elements in the Test List
    seq.innerHTML = '';
    overlayContainer.innerHTML = '';
    overlayContainer.appendChild(document.createTextNode('Tests to be compiled'));
    overlayContainer.appendChild(document.createElement('br'));
    overlayContainer.appendChild(document.createElement('br'));
    //now add the new ones
    for (var i = 0; i < testSequence.length; i++) {
        link = document.createElement('a');
        text = document.createTextNode(testSequence[i].Name);
        link.setAttribute('class', 'list-group-item');
        link.setAttribute('id', 'testSeq_' + testSequence[i].Name);
        link.setAttribute('href', 'javascript:removeTestSeq(' + i + ',"' +
            testSequence[i].Name + '")');
        link.appendChild(text);
        seq.appendChild(link);
        /*
        Add the elements to the overlay div
        */
        if (document.getElementById('test_name_overlay_div_' + testSequence[i].Name)== null){
            var span = document.createElement('span');
            var icon = document.createElement('i');
            icon.setAttribute('id', 'icon_overlay_div_' + testSequence[i].Name)
            icon.setAttribute('class', 'fa fa-minus ');
            var name = document.createElement('text');
            name.setAttribute('id', 'test_name_overlay_div_' + testSequence[i].Name)
            name.setAttribute('class', 'overlayContainerText');
            span.appendChild(icon);
            name.appendChild(document.createTextNode(testSequence[i].Name));
            span.appendChild(name);
            overlayContainer.appendChild(span);
            overlayContainer.appendChild(document.createElement('br'))
        }
    }
}


window.addEventListener('execute', function(e) {
    if (executeTest) {
        var executionTimes = document.getElementById('spinnerTime').value;
        var executionDelay = document.getElementById('spinnerDelay').value;
        call_POST('executeTestSequence', JSON.stringify(testSequence),
            executionTimes, executionDelay);
        executeTest = false;
    }
}, false);

var executeTest = false;

function executeTestSequence() {
    testString = JSON.stringify(testSequence);
    if (!compiledTestId[testString]) {
        humaneAlert('Please compile the test before you execute');
        return;
    }
    // Listen for the event execute, that is
    executeTest = true;

    if (myWindow == null || myWindow.closed) {
        var left = screen.width;
        var width = $(document).width();
        var height = $(document).height();
        myWindow = window.open('log.html', "log",
            "toolbar=No, navigation=No, locationbar= No, scrollbars=yes, resizable=yes, " +
            "top=5, left=" + left + "px, " +
            "width=" + width * 0.8 + "px, height=" + height * 0.7 + 'px');
    } else {
        var executionTimes = document.getElementById('spinnerTime').value;
        var executionDelay = document.getElementById('spinnerDelay').value;
        call_POST('executeTestSequence', JSON.stringify(testSequence),
            executionTimes, executionDelay);
    }
}
var myWindow = null;

function stopTestExecution() {
    call_GET('stopRunningTest');
}

function compileTest() {
    updateTestSeq();
    call_POST('compileTestSequence', JSON.stringify(testSequence));
    var overlayDiv = document.getElementById('overlayDiv');
    overlayDiv.style.visibility = 'visible';
}
compiledTestId = {};

function updateCompiledTest(compiledTest) {
    setTimeout(function(){
        for (var i = 0; i < compiledTest.length; i++) {
            compiledTestId[compiledTest[i]] = true;
        }
        var overlayDiv = document.getElementById('overlayDiv');
        overlayDiv.style.visibility = 'hidden';
    }, 2000);
    
}

function closeChild() {
    myWindow.close();
}

function runTestSeq() {
    call_POST('executeTestSequence', JSON.stringify(testSequence));
}

function readSingleFile(evt) {
    var f = evt.target.files[0];
    if (f) {
        var r = new FileReader();
        r.onload = function(e) {
            var contents = e.target.result;
            var fileName = escape(f.name);
            call_GET("uploadFiles", 'Flows', fileName, contents);

        };
        r.readAsText(f);
    } else {
        humaneAlert("Failed to load file");
    }
}

function getParameterByName(name) {
    var match = new RegExp('[?&]' + name + '=([^&]*)').exec(window.location.search);
    return match && decodeURIComponent(match[1].replace(/\+/g, ' '));
}

function modifySelectedTest() {
    if (currentSelectedTest) {
        test = currentSelectedTest;
        makeCurrentSelections();
    }
}

function deleteFlow(flowName) {
    call_GET('deleteFlowFileWithName', flowName);
}

function deleteSelectedTest(testName, fileName) {
    call_GET('deleteSelectedTestFromFile', testName, fileName);
}
