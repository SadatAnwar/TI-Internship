/*
 Common function that are needed for multiple pages
 */
var notify = humane.spawn({
    addnCls: 'humane-flatty-success',
    timeout: 3000
});
var alert = humane.spawn({
    addnCls: 'humane-flatty-error',
    timeout: 3000
});

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

function call_GET(object, function_id) {
    /*
     This function is used to make calls to the PYTHON server, the function has to have a min of one argument, called the function_id,
     this is used by the server to which function it has to execute. More parameters can be added and are encoded as param1, param2, .... and so on
     The function makes an ajax call to the server and based on the reply moves forward.
     The Python function returns as JSON data that has member FunctionName which tells this js, where to start execution next and optional parameters
     */
    var params = {};
    params["function_id"] = function_id;
    if (arguments.length > 2) {
        for (var i = 2; i < arguments.length; i++) {
            params["param" + i] = arguments[i];
        }
    }
    $.get("/", params, function (ret){
        callBack(object, ret);
    });
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
    $.post("/", params, callBack);
}

/*
 Universal callback for GET and POST request, handles the way the page will react to the data returned
 from the server
 */
function callBack(object , return_value) {
    result = JSON.parse(return_value);
    functionName = result.FunctionName;
    parameter = result.Result;
    if (parameter.toString().toLowerCase() == 'ok') {
        notify(functionName + ' returned success');
        if (window.location.href.includes('fram.html')){
            call_GET('readFlows');
        }
    } else if (parameter.toString().toLowerCase().indexOf("error") > -1) {
        alert("Encountered an error:" + parameter + ", please check server log for a more detailed report");
    } else if (parameter.toString().toLowerCase() == 'reload') {
        location.reload();
    } else {
        try {
            object[functionName](parameter);
        } catch (e) {
            alert(e + ' Function Name =' + functionName);
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
/**
 * Created by x0234668 on 7/27/2015.
 */
