/**
 * Created by x0234668 on 7/27/2015.
 */
debuggerApp.controller('setupController', ['$scope','$location', function($scope) {

    $scope.onPageLoad = function () {
        data = {
            'function_id': 'getFilesInFolder',
            'param1': 'ATPTestTemplate'
        };
        updateDropdown('ATPTestTemplateDropDown', httpGet('getFilesInFolder?' + EncodeQueryData(data)));

        data = {
            'function_id': 'getFilesInFolder',
            'param1': 'ATPMemWriteTemplate'
        };
        updateDropdown('ATPMemWriteTemplateDropDown', httpGet('getFilesInFolder?' + EncodeQueryData(data)));

        var data = {
            'function_id': 'getFilesInFolder',
            'param1': 'MemDump'
        };
        var text = httpGet('getFilesInFolder?' + EncodeQueryData(data));
        document.getElementById('memDumpFileName').innerHTML = text;
        // Function that are to be run when the page loads, eg populate drop-downs
    };

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

    function updateDropdown(dropdownID, list) {
        var element = document.getElementById(dropdownID);
        //Remove the old stuff
        while (element.lastChild) {
            element.removeChild(element.lastChild);
        }
        // append the new stuff
        for (var i = 0; i < list.length; i++) {
            var option = document.createElement('option');
            option.text = list[i];
            option.value = list[i];
            element.appendChild(option);
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
        call_GET('updateFRAMSettings', testTemplateATP, memWriteTemplate);
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

    function deleteFile(folder, filename) {
        call_GET('deleteFilesInFolder', folder, filename);
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
    $scope.onpageLoad();
}]);