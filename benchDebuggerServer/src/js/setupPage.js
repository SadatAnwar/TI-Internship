var CONSOLE_LOG = {
    'Detailed': 10,
    'Feedback': 20,
    'Warning':30,
    'Error Only':40
};
var WEB_LOG = {
    'Expert': 10,
    'Default': 20
};
var LOG_FILE = {
    'Yes': 1,
    'No': 0
};
function onPageLoad() {
    var data = {
        'function_id': 'getFilesInFolder',
        'param1': 'ATPTestTemplate'
    };
    $.get('/', data, function (return_value) {
        var result = JSON.parse(return_value);
        addListToDropDown('ATPTestTemplateDropDown', JSON.parse(result.Result));
    });

    data = {
        'function_id': 'getFilesInFolder',
        'param1': 'ATPMemWriteTemplate'
    };
    $.get('/', data, function (return_value) {
        var result = JSON.parse(return_value);
        addListToDropDown('ATPMemWriteTemplateDropDown', JSON.parse(result.Result));
    });
    data = {
        'function_id': 'getFilesInFolder',
        'param1': 'MemDump'
    };
    $.get('/', data, function (return_value) {
        var result = JSON.parse(return_value);
        document.getElementById('memDumpFileName').innerHTML = JSON.parse(result.Result);
    });
    var consoleDropDown = document.getElementById('consoleLogLevelDropDown');
    var webDropDown = document.getElementById('webLogLevelDropDown');
    var logToFile = document.getElementById('logToFile');
    addKeyValueToDropDown(consoleDropDown, CONSOLE_LOG);
    addKeyValueToDropDown(webDropDown, WEB_LOG);
    addKeyValueToDropDown(logToFile, LOG_FILE);

    data = {
        'function_id': 'getConfigValues'
    };
    $.get('/', data, function (return_value) {
        var result = JSON.parse(return_value);
        var config = JSON.parse(result.Result);
        var atpTestTemplate = config.FRAM_SETTING.atp_test_template;
        var memWriteTemplate = config.FRAM_SETTING.atp_mem_wr_template;
        var consoleLogLevel = config.LOGGING.loglevel;
        var webLogLevel = config.LOGGING.webloglevel;
        var fileLogLevel = config.LOGGING.weblogtofile;
        selectOptionInList(atpTestTemplate, document.getElementById('ATPTestTemplateDropDown'));
        selectOptionInList(memWriteTemplate, document.getElementById('ATPMemWriteTemplateDropDown'));
        selectOptionInList(consoleLogLevel, consoleDropDown);
        selectOptionInList(webLogLevel, webDropDown);
        selectOptionInList(fileLogLevel, logToFile);
    });
    // Function that are to be run when the page loads, eg populate drop-downs

}
/*
Save the username and password.
Send it to the server and the server will take care of the rest
*/
function saveUserSetting() {
    var userName = document.getElementById('usr');
    var pass = document.getElementById('pwd');

    if (userName.value.length > 3 && pass.value.length > 3) {
        var usr = userName.value;
        var password = pass.value;
        pass.value = "";
        userName.value = "";
        call_GET('updateUserLogIn', usr, password);
    } else {
        humaneAlert("Username and Password must be atleast 3 charecters");
    }
}

function uploadATPTestTemplate(evt) {
    var f = evt.target.files[0];
    if (f) {
        var r = new FileReader();
        r.onload = function(e) {
            var contents = e.target.result;
            var fileName = escape(f.name);
            call_POST('uploadFiles', 'ATPTestTemplate', fileName, contents);
        };
        r.readAsText(f);
    } else {
        humaneAlert("Failed to load file");
    }
}

function uploadATPMemWriteTemplate(evt) {
    var f = evt.target.files[0];
    if (f) {
        var r = new FileReader();
        r.onload = function(e) {
            var contents = e.target.result;
            var fileName = escape(f.name);
            call_POST('uploadFiles', 'ATPMemWriteTemplate', fileName, contents);
        };
        r.readAsText(f);
    } else {
        humaneAlert("Failed to load file");
    }
}

function uploadMemDump(evt) {
    var f = evt.target.files[0];
    if (f) {
        var r = new FileReader();
        r.onload = function(e) {
            var contents = e.target.result;
            var fileName = escape(f.name);
            call_GET('uploadFiles', "MemDump", fileName, contents);
        };
        r.readAsText(f);
    } else {
        humaneAlert("Failed to load file");
    }
}


function saveFRAMSetting() {
    //Read the selected values
    var testTemplateATP = " ";
    if (document.getElementById('ATPTestTemplateDropDown').options.length > 0) {
        testTemplateATP = document.
        getElementById('ATPTestTemplateDropDown').
        options[document.getElementById('ATPTestTemplateDropDown').selectedIndex].value;
    }
    var memWriteTemplate = " ";
    if (document.getElementById('ATPMemWriteTemplateDropDown').options.length > 0) {
        memWriteTemplate = document.
        getElementById('ATPMemWriteTemplateDropDown').
        options[document.getElementById('ATPMemWriteTemplateDropDown').selectedIndex].value;
    }
    var consoleLog = " ";
    if (document.getElementById('consoleLogLevelDropDown').options.length > 0) {
        consoleLog = document.
            getElementById('consoleLogLevelDropDown').
            options[document.getElementById('consoleLogLevelDropDown').selectedIndex].value;
    }
    var webLog = " ";
    if (document.getElementById('webLogLevelDropDown').options.length > 0) {
        webLog = document.
            getElementById('webLogLevelDropDown').
            options[document.getElementById('webLogLevelDropDown').selectedIndex].value;
    }
    var fileLog = " ";
    if (document.getElementById('logToFile').options.length > 0) {
        fileLog = document.
            getElementById('logToFile').
            options[document.getElementById('logToFile').selectedIndex].value;
    }
    call_GET('updateFRAMSettings', testTemplateATP, memWriteTemplate, consoleLog, webLog, fileLog);
}

function deleteTestTemp() {
    var testTemplateATP = " ";
    if (document.getElementById('ATPTestTemplateDropDown').options.length > 0) {
        testTemplateATP = document.getElementById('ATPTestTemplateDropDown').
        options[document.getElementById('ATPTestTemplateDropDown').selectedIndex].value;
    }
    deleteFile('ATPTestTemplate', testTemplateATP);
}

function deleteMemWriteTemp() {
    var memWriteTemplate = " ";
    if (document.getElementById('ATPMemWriteTemplateDropDown').options.length > 0) {
        memWriteTemplate = document.
        getElementById('ATPMemWriteTemplateDropDown').
        options[document.getElementById('ATPMemWriteTemplateDropDown').selectedIndex].value;
    }
    deleteFile('ATPMemWriteTemplate', memWriteTemplate);
}



function processMemoryDump(parameter) {
    notify(parameter + ' file Uploaded, processing now');
    document.getElementById('notify').innerHTML = 'Creating ATP for Memory Dump';
    call_GET('processMemoryDump');
}

function makeMemDumpAssembly() {

    notify('Generating assemblers, this may take a while depending on the size of the memory dump');
    document.getElementById('notify').innerHTML = 'Creating Assembler files for Memory Dump';
    call_GET('makeMemDumpAssembly');
}

function makeMemDumpBinary(count) {
    notify(count + ' assemblers generated, compiling binaries for memory dump');
    document.getElementById('notify').innerHTML = count + ' assembler files created, compiling binary files';
    var params = {function_id: 'makeMemDumpBinary'};
    $.get("/cgi-bin/index", params,
        function (result){
            result = JSON.parse(result);
            if (result.Result > count) {
                var button = '\<button id="writeDeviceMem" type="button" class="btn btn-warning btn-block" ' +
                    'onclick=\'javascript:call_GET("writeDeviceMem")\' data-tooltip="tooltip" title="Write the uploaded memory dump to device, make sure the device is powered on first">write device memory</button>';
                document.getElementById('notify').innerHTML = button;
                notify("Success");
            } else {

                humaneAlert((count - result.Result) + " files failed");
            }
        }
    );
}

function restartServer(){
    call_GET('restartServer');
    var counter = 15;
    var messageElement = document.createElement('h3');
    messageElement.style.color = 'red';
    messageElement.style.textAlign = 'center'
    var title = document.getElementById('pageTitle');
    title.appendChild(messageElement);
    var id = setInterval(function() {
        counter--;
        if(counter < 0) {
            clearInterval(id);
            location.reload();
        } else {
            messageElement.innerHTML = "Server will restart in  " + counter.toString() + " seconds.";
        }
    }, 1000);
}