/*
Common function that are needed for multiple pages
 */
var humaneLog = humane.create({
    addnCls: 'humane-flatty-success',
    timeout: 3000
});
function notify (message){
    humaneLog.remove();
    humaneLog.queue = [];
    humaneLog.log(message);
}
var humaneAlertObject = humane.create({
    addnCls: 'humane-flatty-error',
    timeout: 3000
});

function humaneAlert(message){
    humaneAlertObject.remove();
    humaneAlertObject.queue = [];
    humaneAlertObject.log(message);
}

var jtagPower = false;


function createPost(path, params, method) {
    method = method || "post"; // Set method to post by default if not specified.

    // The rest of this code assumes you are not using a library.
    // It can be made less wordy if you use one.
    var form = document.createElement("form");
    form.setAttribute("method", method);
    form.setAttribute("action", path);

    for (var key in params) {
        if (params.hasOwnProperty(key)) {
            var hiddenField = document.createElement("input");
            hiddenField.setAttribute("type", "hidden");
            hiddenField.setAttribute("name", key);
            hiddenField.setAttribute("value", params[key]);

            form.appendChild(hiddenField);
        }
    }

    document.body.appendChild(form);
    form.submit();
}

function call_GET(function_id) {
    /*
     This function is used to make calls to the PYTHON server, the function has to have a min of one argument, called the function_id,
     this is used by the server to which function it has to execute. More parameters can be added and are encoded as param1, param2, .... and so on
     The function makes an ajax call to the server and based on the reply moves forward.
     The Python function returns as JSON data that has member FunctionName which tells this js, where to start execution next and optional parameters
     */
    var params = {};
    params["function_id"] = function_id;
    if (arguments.length > 1) {
        for (var i = 1; i < arguments.length; i++) {
            params["param" + i] = arguments[i];
        }
    }
    $.get("/", params, callBack);
}



function call_POST(function_id) {
    /*
     This function is used to make POST (similar to the GET) calls to the PYTHON server, the function has to have a min of one argument, called the function_id,
     this is used by the server to which function it has to execute. More parameters can be added and are encoded as param1, param2, .... and so on
     The function makes an ajax call to the server and based on the reply moves forward.
     The Python function returns as JSON data that has member FunctionName which tells this js, where to start execution next and optional parameters
     */
    var params = {};
    params["function_id"] = function_id;
    if (arguments.length > 1) {
        for (var i = 1; i < arguments.length; i++) {
            params["param" + i] = arguments[i];
        }
    }
    //$.post("/", params, callBack);
    $.ajax({
        type: "POST",
        url: "/",
        data: params,
        success: callBack,
        error:callBack
    });
}

/*
 Universal callback for GET and POST request, handles the way the page will react to the data returned
 from the server
 */
function callBack(return_value) {
    var result = JSON.parse(return_value);
    var functionName = result.FunctionName;
    var parameter = result.Result;
    if (parameter.toString().toLowerCase() == 'ok') {
        notify(functionName + ' returned success');
        if (window.location.href.indexOf('fram.html')> -1){
            call_GET('readFlows');
        }
    } else if (parameter.toString().toLowerCase().indexOf("error") > -1) {
        humaneAlert("Encountered an error:" + parameter + ", please check server log for a more detailed report");
    } else if (parameter.toString().toLowerCase() == 'reload') {
        location.reload();
    } else if (parameter.toString().toLowerCase() == 'silent') {
        return;
    } 
    else {
        try {
            window[functionName](parameter);
        } catch (e) {
            humaneAlert(e + ' Function Name =' + functionName);
        }
    }
}


// Synchronous call to get the contents of folders
function httpGet(theUrl) {
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.open("GET", theUrl, false);
    xmlHttp.send(null);
    var result = JSON.parse(xmlHttp.responseText);
    try {
        return JSON.parse(result.Result);
    } catch (e) {
        return result.Result;
    }
}

// Encode parameters into a GET style string to be appended at the end of the URL
function EncodeQueryData(data) {
    var ret = [];
    for (var d in data)
        ret.push(encodeURIComponent(d) + "=" + encodeURIComponent(data[d]));
    return ret.join("&");
}

/*
 this function takes care of the populating for the dropDown list
 */
function addKeyValueToDropDown(element, list) {
    if (element){
        for (var key in list) {
            if (list.hasOwnProperty(key)) {
                var option = document.createElement('option');
                option.text = key;
                option.value = list[key];
                element.appendChild(option);
            }
        }
    } else {
        return;
    }
}
/*
Update a selection drop down
*/
function addListToDropDown(dropDownID, list) {
    var element = document.getElementById(dropDownID);
    //Remove the old stuff
    element.innerHTML = '';
    // append the new stuff
    for (var i = 0; i < list.length; i++) {
        var option = document.createElement('option');
        option.text = list[i];
        option.value = list[i];
        element.appendChild(option);
    }
}
/*
This will pre-select the item in a dropDown list
 */
function selectOptionInList(optionValue, list) {
    for (var i = 0; i < list.options.length; i++) {
        if (list.options[i].value == optionValue) {
            list.selectedIndex = i;
            break;
        }
    }
}
/*
Delete files from folder
 */
function deleteFile(folder, filename, callBack) {
    if (callBack == null){
        call_GET('deleteFilesInFolder', folder, filename);
    }
    else {
        $.get('/', {
            function_id: 'deleteFilesInFolder',
            param1: folder,
            param2: filename
        }, callBack);
    }
}

function uploadFile(){
    var f = evt.target.files[0];
    if (f) {
        var r = new FileReader();
        r.onload = function (e) {
            var contents = e.target.result;
            var fileName = escape(f.name);
            $.post("/", {
                function_id: 'uploadFiles',
                param1: 'FramePattern',
                param2: fileName,
                param3: contents
            }, function () {
                $.get('/', {
                    'function_id': 'getFilesInFolder',
                    'param1': 'FramePattern'
                }, function (return_value) {
                    var result = JSON.parse(return_value);
                    addListToDropDown('framePattern', JSON.parse(result.Result));
                    dropDowns.dropDownList.FRAME_PATTERN = JSON.parse(result.Result);
                })
            })
            call_POST('uploadFiles', "FramePattern", fileName, contents);
        };
        r.readAsText(f);
    }
}