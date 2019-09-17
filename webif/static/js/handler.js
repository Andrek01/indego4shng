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
      //document.getElementById("txtEncoded").value = encoded;
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
// Function to Save Command-Let
//*******************************************

function StoreColor(Color) {
	$.ajax({
		url: "store_color.html",
		type: "GET",
		data: { newColor : Color,
              } ,
		contentType: "application/json; charset=utf-8",
		success: function (response) {console.log('error-setting Colour-Code')},
		error: function () {console.log('OK-setting Colour-Code')}
	});
  return
}



//*******************************************
// Button Handler for saving Colour
//*******************************************

function SaveColor(picker)
{
    newColor = picker.toHEXString()
    StoreColor(newColor)
}

