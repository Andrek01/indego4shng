//*************************************************************
// ValidateEncodeResponse -checks the login-button
//*************************************************************

function ValidateEncodeResponse(response)
{
var myResult = ""
var temp = ""
var objResponse = JSON.parse(response)
for (x in objResponse.Proto)
    {
      temp = temp + objResponse.Proto[x]+"\n";
    }

document.getElementById("txt_Result").value = temp;
document.getElementById("txtEncoded").innerHTML = objResponse.Params.encoded
document.getElementById("text_session_id").innerHTML = objResponse.Params.SessionID
document.getElementById("text_experitation").innerHTML = objResponse.Params.timeStamp
if (objResponse.Params.logged_in == true)
    {
     document.getElementById("grafic_logged_in").src = "static/img/lamp_green.png"
     document.getElementById("text_logged_in").innerHTML = "logged in"

    }
else
    {
     document.getElementById("grafic_logged_in").src = "static/img/lamp_red.png"
     document.getElementById("text_logged_in").innerHTML = "logged off"
    }
}

//*******************************************
// Button Handler for Encoding credentials
//*******************************************

function BtnEncode(result)
{
      user = document.getElementById("txtUser").value;
      pwd = document.getElementById("txtPwd").value;
      store2config = document.getElementById("store_2_config").checked;
      encoded=user+":"+pwd;
      encoded=btoa(encoded);
	$.ajax({
		url: "store_credentials.html",
		type: "GET",
		data: { encoded : encoded,
			user : user,
		   	pwd : pwd,
			store_2_config : store2config
		      },
		contentType: "application/json; charset=utf-8",
		success: function (response) {
				ValidateEncodeResponse(response);
		},
		error: function () {
            document.getElementById("txt_Result").innerHTML = "Error while Communication !";
		}
	});
  return
}

//*******************************************
// Function to Store Color
//*******************************************

function StoreColor(Color) {
	$.ajax({
		url: "store_color.html",
		type: "GET",
		data: { newColor : Color,
              } ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {console.log('OK-setting Colour-Code')},
		error: function () {console.log('error-setting Colour-Code')}
	});
  return
}

//*******************************************
// Function to add_svg_images
//*******************************************

function Store_add_svg(Value) {
	$.ajax({
		url: "store_add_svg.html",
		type: "GET",
		data: { add_svg_str : Value,
              } ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {console.log('OK add_svg_image stored')},
		error: function () {console.log('error-add_svg_image stored')}
	});
  return
}

//*******************************************
// Function to Store State-Trigger-Events
//*******************************************

function StoreStateTrigger(TriggerItem, Value) {
	$.ajax({
		url: "store_state_trigger.html",
		type: "GET",
		data: { Trigger_State_Item : TriggerItem,
                newState : Value
              } ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {console.log('OK-setting Trigger-State')},
		error: function () {console.log('error-setting Trigger-State')}
	});
  return
}

//*******************************************
// Function to Store Alarm-Trigger-Events
//*******************************************

function StoreAlarmTrigger(TriggerItem, Value) {
	$.ajax({
		url: "store_alarm_trigger.html",
		type: "GET",
		data: { Trigger_Alarm_Item : TriggerItem,
                newAlarm : Value
              } ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {console.log('OK-setting Trigger-Alarm')},
		error: function () {console.log('error-setting Trigger-Alarm')}
	});
  return
}

//*******************************************
// Handler for Selecting State-Triggers
//*******************************************

function selectStateTrigger(SelectID)
{
    mySelect = document.getElementById(SelectID)
    myValue = mySelect.options[mySelect.options.selectedIndex].text
    StoreStateTrigger(SelectID, myValue)
}

//*******************************************
// Handler for Selecting Alarm-Triggers
//*******************************************

function selectAlarmTrigger(SelectID)
{
    mySelect = document.getElementById(SelectID)
    myValue = mySelect.value
    StoreAlarmTrigger(SelectID, myValue)
}


//*******************************************
// Button Handler for saving Colour
//*******************************************

function SaveColor(picker)
{
    newColor = picker.toHEXString()
    StoreColor(newColor)
}

