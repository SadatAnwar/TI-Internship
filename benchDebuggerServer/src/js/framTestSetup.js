/*
 This file contains the functions that are used specifically by the testSetup.html page
 */

// get the JSON test object so that we can read the parameters and populate the page

var test;

var dropDowns = {
    /*
     Drop down variables for FRAM TEST section
     */
    algorithm: document.getElementById('algorithmDropdown'),
    memory: document.getElementById('memoryDropdown'),
    data: document.getElementById('dataDropdown'),
    setting: document.getElementById('settingDropdown'),
    resultTyp: document.getElementById('resultTypDropdown'),
    // Analog 0-2 Mode Drop downs
    modeAn0: document.getElementById('analog0modeDropdown'),
    modeAn1: document.getElementById('analog1modeDropdown'),
    modeAn2: document.getElementById('analog2modeDropdown'),

    //Drop downs for the frame section
    frameAlgorithm: document.getElementById('frameAlgorithm'),
    framePattern: document.getElementById('framePattern'),
    frameFile: document.getElementById('frameFile'),
    frameVddMode: document.getElementById('frameVddMode'),
    frameModeAn0: document.getElementById('frameMode0'),
    frameModeAn1: document.getElementById('frameMode1'),
    frameModeAn2: document.getElementById('frameMode2'),

    //Valid values for DropDOWNS
    dropDownList: {
        ALGORITHM: {
            "P_UTILITY": 0,
            "P_WIR": 1,
            "P_WR": 2,
            "P_MARCH6N": 3,
            "P_BINARY": 5,
            "P_WRITE": 6,
            "P_READ": 7,
            "P_RETENT": 8,
            "P_IREF": 9,
            "P_SACOMP": 10,
            "P_IDD": 11,
            "P_ECC": 12,
            "P_WAKEUP": 13,
            "P_PARA": 14,
            "P_FLOWINIT": 128,
            "P_PARADELTA": 129
        },
        MEMORY: {
            "P_NA": 0,
            "P_CUSTOM": 128,
            "P_MAIN": 1,
            "P_MAIN_CNFROWSINFO": 9,
            "P_MAIN_CNFROWSINT": 17,
            "P_MAIN_CNFROWS": 3,
            "P_MAIN_CNFROWS_DUMMYWL": 7,
            "P_MAIN_CNFROWSINFO_DUMMYWL": 13,
            "P_MAIN_CNFROWSINT_DUMMYWL": 21,
            "P_CNFROWSINFO": 8,
            "P_CNFROWSINT": 16,
            "P_CNFROWS": 2,
            "P_CNFROWS_DUMMYWL": 6,
            "P_CNFROWSINFO_DUMMYWL": 12,
            "P_CNFROWSINT_DUMMYWL": 20
        },
        DATA: {
            "P_ZERO": 0,
            "P_ONE": 1,
            "P_CHECKERBOARD": 2,
            "P_INV_CHECKERBOARD": 3
        },
        SETTING: {
            "P_FUNC_DEFAULT": 0,
            "P_FUNC_2T2C": 1,
            "P_FUNC_2T2C_MRG": 2,
            "P_FUNC_1T1C_MRG": 3,
            "P_FUNC_1T1C_MRG_INT": 4,
            "P_FUNC_1T1C_MRG_OP": 5,
            "P_FUNC_2T2C_MRG_OP": 6,
            "P_FUNC_SA_COMP": 7,
            "P_FUNC_WRINTREG": 8,
            "P_PARA_LEAK_WL_E": 64,
            "P_PARA_LEAK_WL_O": 65,
            "P_PARA_LEAK_BL": 66,
            "P_PARA_LEAK_BLB": 67,
            "P_PARA_IDDQ": 68,
            "P_PARA_IDDA": 69,
            "P_PARA_WLS": 70,
            "P_PARA_T2B_E": 71,
            "P_PARA_T2B_O": 72,
            "P_PARA_W2B_E": 73,
            "P_PARA_W2B_O": 74,
            "P_PARA_B2B_E": 75,
            "P_PARA_B2B_O": 76,
            "P_PARA_P2B_E": 77,
            "P_PARA_P2B_O": 78,
            "P_PARA_VDDF": 79,
            "P_MW_2T2C_ZEROES": 128,
            "P_MW_2T2C_ONES": 129,
            "P_MW_2T2C_CHK_1": 130,
            "P_MW_2T2C_CHK_2": 131,
            "P_MW_2T2C_ICHK_1": 132,
            "P_MW_2T2C_ICHK_2": 133,
            "P_MW_1T1C_ZEROES": 134,
            "P_MW_1T1C_ONES": 135,
            "P_MW_1T1C_CHK_1": 136,
            "P_MW_1T1C_CHK_2": 137,
            "P_MW_1T1C_ICHK_1": 138,
            "P_MW_1T1C_ICHK_2": 139
        },
        RESULTTYPE: {
            "P_NA": 0,
            "P_PassFail": 1,
            "P_Parameter": 2,
            "P_BFC": 4,
            "P_BFM": 8,
            "P_PassFail_BFM": 9,
            "P_PassFail_Repair": 17,
            "P_PassFail_Repair_BFM": 25
        },

        MODE: {
            'P_NC': 0,
            'P_FVMC': 1,
            'P_FCMV': 2,
            'P_FV': 3
        },

        FRAME_ALGORITHM: {
            'No Action': 0,
            'Read Memory': 1,
            'Write Memory': 2,
            'Run Pattern': 3,
            'Reset JTAG':4
        },
        FRAME_VDD_MODE: {
            'Not Connected': 0,
            '3 V': 1,
            'Connect to Analog-0': 2
        },

        FRAME_PATTERN: function () {
            $.get('/', {
                'function_id': 'getFilesInFolder',
                'param1': 'FramePattern'
            }, function (return_value) {
                var result = JSON.parse(return_value);
                addListToDropDown('framePattern', JSON.parse(result.Result));
            })
        },
        FRAME_FILE: function () {
            $.get('/', {
                'function_id': 'getFilesInFolder',
                'param1': 'FrameFiles'
            }, function (return_value) {
                var result = JSON.parse(return_value);
                addListToDropDown('frameFile', JSON.parse(result.Result));
                var select = $('#frameFile').selectize({
                    create: true,
                    sortField: 'text',
                    onOptionAdd: function(value, data){
                        $.post("/", {
                            function_id: 'uploadFiles',
                            param1: 'FrameFiles',
                            param2: value,
                            param3: ' '
                        });
                        this.addItem(value);
                    }
                });
                dropDowns.dropDownList.FRAME_FILE = select[0].selectize;
            })
        }()

    }
};
var textField = {
    // analog 0-2 text fields
    forceAn0: document.getElementById('analog0force'),
    forceAn1: document.getElementById('analog1force'),
    forceAn2: document.getElementById('analog2force'),

    lwLmtAn0: document.getElementById('analog0lowLimit'),
    lwLmtAn1: document.getElementById('analog1lowLimit'),
    lwLmtAn2: document.getElementById('analog2lowLimit'),

    hILmtAn0: document.getElementById('analog0highLimit'),
    hILmtAn1: document.getElementById('analog1highLimit'),
    hILmtAn2: document.getElementById('analog2highLimit'),

    //text fields from the frame Setup
    frameMemStart: document.getElementById('frameMemStart'),
    frameMemSize: document.getElementById('frameMemSize'),
    frameForce0: document.getElementById('frameForce0'),
    frameForce1: document.getElementById('frameForce1'),
    frameForce2: document.getElementById('frameForce2'),

    frameLowLimit0: document.getElementById('frameLowLimit0'),
    frameLowLimit1: document.getElementById('frameLowLimit1'),
    frameLowLimit2: document.getElementById('frameLowLimit2'),

    frameHighLimit0: document.getElementById('frameHighLimit0'),
    frameHighLimit1: document.getElementById('frameHighLimit1'),
    frameHighLimit2: document.getElementById('frameHighLimit2')
};

/*
 First we need to populate the dropdown for the options
 each pop up is to be populated with the data present in the respective arrays,
 this function should be called when the page loads
 */
function loadDropdowns() {
    addKeyValueToDropDown(dropDowns.algorithm, dropDowns.dropDownList.ALGORITHM);
    addKeyValueToDropDown(dropDowns.memory, dropDowns.dropDownList.MEMORY);
    addKeyValueToDropDown(dropDowns.data, dropDowns.dropDownList.DATA);
    addKeyValueToDropDown(dropDowns.setting, dropDowns.dropDownList.SETTING);
    addKeyValueToDropDown(dropDowns.resultTyp, dropDowns.dropDownList.RESULTTYPE);

    addKeyValueToDropDown(dropDowns.modeAn0, dropDowns.dropDownList.MODE);
    addKeyValueToDropDown(dropDowns.modeAn1, dropDowns.dropDownList.MODE);
    addKeyValueToDropDown(dropDowns.modeAn2, dropDowns.dropDownList.MODE);

    //From frame page
    //dropDowns.dropDownList.FRAME_FILE();
    dropDowns.dropDownList.FRAME_PATTERN();
    addKeyValueToDropDown(dropDowns.frameAlgorithm, dropDowns.dropDownList.FRAME_ALGORITHM);
    addKeyValueToDropDown(dropDowns.frameVddMode, dropDowns.dropDownList.FRAME_VDD_MODE);
    addKeyValueToDropDown(dropDowns.frameModeAn0, dropDowns.dropDownList.MODE);
    addKeyValueToDropDown(dropDowns.frameModeAn1, dropDowns.dropDownList.MODE);
    addKeyValueToDropDown(dropDowns.frameModeAn2, dropDowns.dropDownList.MODE);

}
var Setup = function (test) {
    this.test = test;
    this.type = this.test.Type;
    this.makeCurrentSelections = function () {
        if (this.type == 'INTERFACE_T') {
            var title = document.getElementById('testSetupTitle');
            title.innerHTML = 'Test Setup: ' + this.test.FileName + ' / ' + this.test.Name;
            // now preselect the current settings
            var algorithm = parseInt(this.test.Param.ALGORITHM);
            var memory = parseInt(this.test.Param.MEMORY);
            var data = parseInt(this.test.Param.DATA);
            var setting = parseInt(this.test.Param.SETTING);
            var resultType = parseInt(this.test.Param.RESULTTYPE);
            // Analog values
            var analogMode0 = parseFloat(this.test.Param.EXT0MODE);
            var analogMode1 = parseFloat(this.test.Param.EXT1MODE);
            var analogMode2 = parseFloat(this.test.Param.EXT2MODE);

            textField.forceAn0.value = this.test.Param.EXT0FORCE==null?'0':this.test.Param.EXT0FORCE;
            textField.forceAn1.value = this.test.Param.EXT1FORCE==null?'0':this.test.Param.EXT1FORCE;
            textField.forceAn2.value = this.test.Param.EXT2FORCE==null?'0':this.test.Param.EXT2FORCE;

            textField.lwLmtAn0.value = parseFloat(this.test.Param.EXT0LOWLIMIT);
            textField.lwLmtAn1.value = parseFloat(this.test.Param.EXT1LOWLIMIT);
            textField.lwLmtAn2.value = parseFloat(this.test.Param.EXT2LOWLIMIT);

            textField.hILmtAn0.value = parseFloat(this.test.Param.EXT0HIGHLIMIT);
            textField.hILmtAn1.value = parseFloat(this.test.Param.EXT1HIGHLIMIT);
            textField.hILmtAn2.value = parseFloat(this.test.Param.EXT2HIGHLIMIT);


            selectOptionInList(algorithm, dropDowns.algorithm);
            selectOptionInList(memory, dropDowns.memory);
            selectOptionInList(data, dropDowns.data);
            selectOptionInList(setting, dropDowns.setting);
            selectOptionInList(resultType, dropDowns.resultTyp);

            selectOptionInList(analogMode0, dropDowns.modeAn0);
            selectOptionInList(analogMode1, dropDowns.modeAn1);
            selectOptionInList(analogMode2, dropDowns.modeAn2);
        } else if (this.type == 'FRAME_T') {
            var title = document.getElementById('frameSetupTitle');
            title.innerHTML = 'Test Setup: ' + this.test.FileName + ' / ' + this.test.Name;
            var algorithm = parseInt(this.test.Param.ALGORITHM);
            selectOptionInList(algorithm, dropDowns.frameAlgorithm);
            $('#frameAlgorithm').trigger('change');
            selectOptionInList(this.test.Param.SETTING, dropDowns.framePattern);
            dropDowns.dropDownList.FRAME_FILE.addItem(this.test.Param.MEMORY);
            textField.frameMemStart.value = this.test.Param.PARAM1==null?'':this.test.Param.PARAM1;
            textField.frameMemSize.value = this.test.Param.PARAM2==null?'':this.test.Param.PARAM2;

        }
    }
    this.saveModifiedTest = function () {
        if (this.type == 'INTERFACE_T') {
            this.test.Param.TEMPLATE = this.type;
            //Save digital parameters
            this.test.Param.ALGORITHM = '0x' + parseInt(dropDowns.algorithm.options[dropDowns.algorithm.selectedIndex].value).toString(16).toUpperCase();
            this.test.Param.MEMORY = '0x' + parseInt(dropDowns.memory.options[dropDowns.memory.selectedIndex].value).toString(16).toUpperCase();
            this.test.Param.DATA = '0x' + parseInt(dropDowns.data.options[dropDowns.data.selectedIndex].value).toString(16).toUpperCase();
            this.test.Param.SETTING = '0x' + parseInt(dropDowns.setting.options[dropDowns.setting.selectedIndex].value).toString(16).toUpperCase();
            this.test.Param.RESULTTYPE = '0x' + parseInt(dropDowns.resultTyp.options[dropDowns.resultTyp.selectedIndex].value).toString(16).toUpperCase();
            //analog
            this.test.Param.EXT0MODE = dropDowns.modeAn0.options[dropDowns.modeAn0.selectedIndex].value;
            this.test.Param.EXT1MODE = dropDowns.modeAn1.options[dropDowns.modeAn1.selectedIndex].value;
            this.test.Param.EXT2MODE = dropDowns.modeAn2.options[dropDowns.modeAn2.selectedIndex].value;

            this.test.Param.EXT0FORCE = textField.forceAn0.value;
            this.test.Param.EXT1FORCE = textField.forceAn1.value;
            this.test.Param.EXT2FORCE = textField.forceAn2.value;

            this.test.Param.EXT0LOWLIMIT = textField.lwLmtAn0.value;
            this.test.Param.EXT1LOWLIMIT = textField.lwLmtAn1.value;
            this.test.Param.EXT2LOWLIMIT = textField.lwLmtAn2.value;

            this.test.Param.EXT0HIGHLIMIT = textField.hILmtAn0.value;
            this.test.Param.EXT1HIGHLIMIT = textField.hILmtAn1.value;
            this.test.Param.EXT2HIGHLIMIT = textField.hILmtAn2.value;

            call_GET("updateTestInFile", JSON.stringify(this.test));
        } else if (this.type == 'FRAME_T') {
            this.test.Param.TEMPLATE = this.type;

            this.test.Param.ALGORITHM = '0x' + parseInt(dropDowns.frameAlgorithm.options[dropDowns.frameAlgorithm.selectedIndex].value).toString(16).toUpperCase();
            this.test.Param.DATA = '0x' + parseInt(dropDowns.frameVddMode.options[dropDowns.frameVddMode.selectedIndex].value).toString(16).toUpperCase();
            this.test.Param.MEMORY = dropDowns.dropDownList.FRAME_FILE.getValue();
            this.test.Param.SETTING = dropDowns.framePattern.options[dropDowns.framePattern.selectedIndex].value;
            this.test.Param.PARAM1 = textField.frameMemStart.value == '' ? '0x0' : textField.frameMemStart.value;
            this.test.Param.PARAM2 = textField.frameMemSize.value == '' ? '0x0' : textField.frameMemSize.value;
            //analog
            this.test.Param.EXT0MODE = dropDowns.frameModeAn0.options[dropDowns.frameModeAn0.selectedIndex].value;
            this.test.Param.EXT1MODE = dropDowns.frameModeAn1.options[dropDowns.frameModeAn1.selectedIndex].value;
            this.test.Param.EXT2MODE = dropDowns.frameModeAn2.options[dropDowns.frameModeAn2.selectedIndex].value;

            this.test.Param.EXT0FORCE = textField.frameForce0.value;
            this.test.Param.EXT1FORCE = textField.frameForce1.value;
            this.test.Param.EXT2FORCE = textField.frameForce2.value;

            this.test.Param.EXT0LOWLIMIT = textField.frameLowLimit0.value;
            this.test.Param.EXT1LOWLIMIT = textField.frameLowLimit1.value;
            this.test.Param.EXT2LOWLIMIT = textField.frameLowLimit2.value;

            this.test.Param.EXT0HIGHLIMIT = textField.frameHighLimit0.value;
            this.test.Param.EXT1HIGHLIMIT = textField.frameHighLimit1.value;
            this.test.Param.EXT2HIGHLIMIT = textField.frameHighLimit2.value;

            call_GET("updateTestInFile", JSON.stringify(this.test));
        }
    }
};

function makeCurrentSelections() {
    var setup = new Setup(test);
    setup.makeCurrentSelections();
}

function addNewTestToFile(fileName) {
    var title = document.getElementById('setupModalWindowTitle');
    title.innerHTML = 'Test Setup: ';
    var saveFileName = document.createElement('text');
    saveFileName.setAttribute('id', 'saveTestFileName');
    saveFileName.innerHTML = fileName + ' / ';
    title.appendChild(saveFileName);
    var inputTestName = document.createElement('input');
    inputTestName.setAttribute('id', 'inputNewTestName');
    title.appendChild(inputTestName);
}

function setupSetupPage() {
    var testName = document.getElementById('inputNewTestName').value;
    if (testName.trim().length < 1) {
        humaneAlert('Test name cannot be empty');
        return;
    }
    var testType = document.getElementById('testTypeDropDown').value;
    $('#setupModalWindow').modal('hide');
    if (testType == 'INTERFACE_T') {
        $('#framTestSetupModalWindow').modal({
            show: true,
            backdrop: 'static',
            keyboard: false
        });
    } else if (testType == 'FRAME_T') {
        $('#frameSetupModalWindow').modal({
            show: true,
            backdrop: 'static',
            keyboard: false
        });
    }
    test = {
        FileName: selectedFlow,
        Type: testType,
        Name: testName.trim().replace(/ /g, '_'),
        Param: {}
    };
    var setup = new Setup(test);
    setup.makeCurrentSelections();
}
/*
 To save the modified test, we must first send the updated test python server and then handle the rest there
 to get the new test, we must update the current test with the updated parameters
 */

function saveModifiedTest() {
    var setup = new Setup(test);
    setup.saveModifiedTest();

}

function uploadFrameFile(evt) {
    var f = evt.target.files[0];
    if (f) {
        var r = new FileReader();
        r.onload = function (e) {
            var contents = e.target.result;
            var fileName = escape(f.name);
            $.post("/", {
                function_id: 'uploadFiles',
                param1: 'FrameFiles',
                param2: fileName,
                param3: contents
            }, function () {
                $.get('/', {
                    'function_id': 'getFilesInFolder',
                    'param1': 'FrameFiles'
                }, function (return_value) {
                    var result = JSON.parse(JSON.parse(return_value).Result);
                    for (var r in result){
                        if(dropDowns.dropDownList.FRAME_FILE.getOption(result[r]).length == 0){
                            dropDowns.dropDownList.FRAME_FILE.addOption({value:result[r], text:result[r]}, true);
                            notify('Upload success');
                        }
                    }
                    dropDowns.dropDownList.FRAME_FILE.refreshItems();
                })
            });
        };
        r.readAsText(f);
    } else {
        humaneAlert("Failed to load file");
    }
}
function upladFramePattern(evt) {
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
                    selectOptionInList(fileName, dropDowns.framePattern);
                    notify('Upload success');
                })
            })
        };
        r.readAsText(f);
    }
}

function deleteFramePattern() {
    var deleteFramePattern = " ";
    if (dropDowns.framePattern.options.length > 0) {
        deleteFramePattern = dropDowns.framePattern.
            options[dropDowns.framePattern.selectedIndex].value;
    }
    deleteFile('FramePattern', deleteFramePattern, function () {
        $.get('/', {
            'function_id': 'getFilesInFolder',
            'param1': 'FramePattern'
        }, function (return_value) {
            var result = JSON.parse(return_value);
            addListToDropDown('framePattern', JSON.parse(result.Result));
            dropDowns.dropDownList.FRAME_PATTERN = JSON.parse(result.Result);
        })
    });
}

function deleteFrameFile() {
    var fileToDelete = dropDowns.dropDownList.FRAME_FILE.getValue();
    if (fileToDelete == 'blank'){
        humaneAlert('This is a system file, cannot be deleted');
        return;
    }
    deleteFile('FrameFiles', fileToDelete, function () {
        dropDowns.dropDownList.FRAME_FILE.removeOption(fileToDelete);
        dropDowns.dropDownList.FRAME_FILE.addItem('blank');
    });
}