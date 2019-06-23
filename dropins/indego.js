// ----------------------------------------------------------------------------
// ---   indego.js   ----------------------------------------------------------
// ----------------------------------------------------------------------------
//
// Indego-Widget für Kalender-Handling
//
// Darstellung der Indego-Kalender Einträge  in Form eine Tabelle mit den Einträgen
// Bearbeiten, löschen und speichern von Kalendereinträgen
// (c) Andre Kohler		- 2019
//
//
// ----- indego.calendar -------------------------------------------------------


var actCalendar = ""
var orgCalendar = ""
var newCalendar = ""
var mode = ""
var oldKey = ""

	
	
function DrawCalendar(TableName, CalNo, preFix)
{
	var myDays = ["Mo","Di","Mi","Do","Fr","Sa","So"]
	d=0
	myHtml = ""
	h=0
	myHtml += "<tr>"
	myHtml += "<th></th>"
	while (h<=23)
		{
		myHtml += "<th width=5px height=10px style='border:1px solid #000000;border-collapse: collapse;'>"+String(h)
		myHtml += "</th>"
		h += 1
		}
	myHtml += "</tr>"	
	while (d <=6)
		{
		myHtml += "<tr>"
		myHtml += "<td width=5px height=10px style='border:1px solid #000000;border-collapse: collapse'>"+myDays[d]+"</td>"
		h=0
		while (h<=23)
			{
			myHtml += "<td id="+preFix+'-'+CalNo+"-"+String(d)+"-"+String(h) +" width=5px height=10px style='border:1px solid #000000;border-collapse: collapse'>"
			myHtml += "</td>"
			h += 1
			}
		myHtml += "</tr>"
		d += 1
		}
	$("#"+TableName).html(myHtml)
}


function ValidateEntry(CalNo,Days,myStartTime,myEndTime)
{
	var msg = ""
	var DayCount = new Array(0,0,0,0,0,0,0) 
	var myDays = ["Montag","Dienstag","Mittwocch","Donnerstag","Freitag","Samstag","Sonntag"]
	i = -1
    while (i < newCalendar.length)
    {
   	 i += 1
     calendar = newCalendar[i]
     for (var key in calendar)
      {
    	 if (key.substring(0,1) != CalNo)
    		 {
    		  continue
    		 }
    	 if (calendar.hasOwnProperty(key))
	        {
    		  counter = 0
    		  while (counter <= 6)
    			  {
    			  if (counter =6)
    				  { console.log("")}
    			  if (calendar[key].Days.search(String(counter)) != -1 &&
    				   Days.search(String(counter)) != -1)
    			   		{ DayCount[counter] += 1 }
    			   if (DayCount[counter]>=2)
    				   {
    				    msg = "Sie haben für "+myDays[counter]+" mehr als zwei Mähzeiten erfasst\r\n"
    				    msg += "Bitte korrigieren, es sind pro Kalender und Tag nur zwei Mähzeiten vorgesehen\r\n"
    				    break
    				   }
    			   counter += 1
    			  }
            }
      }

    }
 // Check Times - are they usefull ?
 if (myStartTime >= myEndTime)
	 {
	  msg += "\r\nDie Startzeit ist grösser oder gleich der Endzeit, bitte korrigieren\r\n"
	 }
 if (Days == "")
 {
  msg += "Bitte eine Tag wählen"
 }
 return msg
}


function CancelChanges_mow()
{
	UpdateTable(orgCalendar,'indego-draw-calendar','indego-calendar','m')	
}

function SaveChanges_mow()
{
	io.write('indego.calendar_list',newCalendar[0])
}

// Functions for Predictive Calendar
function CancelChanges_pred()
{
	UpdateTable(orgPredictiveCalendar,'indego-draw-calendar','indego-calendar','p')	
}

function SaveChanges_pred()
{
	io.write('indego.calendar_predictive_list',newPredictiveCalendar[0])
}

function InitWindow()
{
	i=0
    while (i <= 6)
    	{
    	 actDay = "day_"+String(i)
		 $("#"+actDay).prop("checked",false)
		 $("#"+actDay).checkboxradio("refresh")
		 i += 1
    	}
}

function ShowEntryWindow()
{ 
    popup.className = 'overlay';
}

function CloseEntryWindowByCancel()
{
    popup.className = 'overlayHidden';
}

// Stores the given values to the list
function CloseEntryWindowByOK()
{
    StartTime = document.getElementById("t_von").value
    EndTime   = document.getElementById("t_bis").value
    myKey = actCalendar+"-"+StartTime+"-"+EndTime
    DayArray = ""
    i=0
    while (i <= 6)
    	{
    	 actDay = "day_"+String(i)
    	 DayState = document.getElementById(actDay).checked
    	 if (DayState == true)
    		  {
    		   if (DayArray.length > 0)
    			   { DayArray += ","}
    		   DayArray += String(i)
    		  }
    	 i += 1
    	}
    msg = ValidateEntry(actCalendar, DayArray,StartTime,EndTime)
    if (msg.length != 0)
    	{
	     alert(msg)
	     return
    	}
    console.log("Key :"+myKey + ' DayArray :' + DayArray);
    myEntry = {"Days":DayArray, "Start": StartTime, "End" : EndTime, "Key":myKey}
    if (mode = "Edit")
    	{
    	 //Remove the old Key/Value
    	delete newCalendar[0][oldKey]
    	}
    newCalendar[0][myKey]=myEntry
    popup.className = 'overlayHidden';
    UpdateTable(newCalendar,'indego-draw-calendar','indego-calendar','m')
}


	
	
function BtnEdit(click_item)
{
 console.log("BtnEdit from element :"+click_item);
 myKey = click_item.substring(5,20)
 oldKey = myKey
 actCalendar = click_item.substring(5,6)
 myObj = newCalendar[0][myKey]
 document.getElementById("t_von").value = myObj.Start
 document.getElementById("t_bis").value = myObj.End
 i=0
 while (i <= 6)
 	{
	 actDay = "day_"+String(i)
	 if (myObj.Days.search(String(i)) != -1)
	 {
		 document.getElementById(actDay).checked = true
		 $('#'+actDay).prop('checked',true);
		 $("#"+actDay).checkboxradio("refresh")
     }
	 else
	 {
		 document.getElementById(actDay).checked = false
		 $('#'+actDay).prop('checked',false);
		 $("#"+actDay).checkboxradio("refresh")
     }
	 
	 i += 1
 	}
 mode = "Edit"
 ShowEntryWindow();
}

function BtnDelete(click_item)
{
	console.log("BtnDelete from element :"+click_item);
	myKey = click_item.substring(7,20)
	delete newCalendar[0][myKey]
	UpdateTable(newCalendar,'indego-draw-calendar','indego-calendar','m')
 
}

function BtnAdd(click_item)
{
 console.log("BtnAdd from element :"+click_item);
 InitWindow()
 actCalendar = click_item.substring(4,5)
 mode = "Add"
 ShowEntryWindow();
}

function FillDrawingCalendar(myCal,myColour, preFix)
{
	var myTable = new Array(5)
    i=0
    while (i < myCal.length)
    {
     calendar = myCal[i]
     retValTime = ""
     retvalDays = ""
     for (var key in calendar)
      {
    	 if (calendar.hasOwnProperty(key))
	        {
    		 myIndex = parseInt(key[0]) // which Calendar 1/2/3/4/5
    		 myArray = calendar[key].Days.split(",")
             for (var numberOfEntry = 0; numberOfEntry < myArray.length; numberOfEntry++)
    		 {
              actHour = parseFloat(calendar[key].Start.substring(0,2))
              while (actHour <= parseFloat(calendar[key].End.substring(0,2)))
            	  {
            	   myID = preFix+'-'+myIndex+"-"+myArray[numberOfEntry]+"-"+String(actHour)
            	   myCell=document.getElementById(myID)
            	   myCell.bgColor=myColour
            	   
            	   actHour += 1
            	  }
    		 };
	        }
      }
     i += 1
    }
}


function UpdateTable(myCal,preFixDrawCalender, preFixEntryCalendar, preFix)
{
	var myTable = new Array(5)
    i=0
    while (i < myCal.length)
    {
     calendar = myCal[i]
     retValTime = ""
     retvalDays = ""
     for (var key in calendar)
      {
    	 if (calendar.hasOwnProperty(key))
	        {
	          myIndex = parseInt(key[0])
	          retValTime = '<tr><td>'+calendar[key].Start + '-' + calendar[key].End+'</td>' ;
	          retvalDays = '<td>'
			  if (calendar[key].Days.search("0") != -1) { retvalDays +=  'Mo ' }
			  if (calendar[key].Days.search("1") != -1) { retvalDays +=  'Di ' }
			  if (calendar[key].Days.search("2") != -1) { retvalDays +=  'Mi ' }
			  if (calendar[key].Days.search("3") != -1) { retvalDays +=  'Do ' }
			  if (calendar[key].Days.search("4") != -1) { retvalDays +=  'Fr ' }
			  if (calendar[key].Days.search("5") != -1) { retvalDays +=  'Sa ' }
			  if (calendar[key].Days.search("6") != -1) { retvalDays +=  'So'  }
	          retvalDays = retvalDays + '</td>' 
	          myRow = retValTime + retvalDays  
	          myRow +="<td>" +
	          "<div class='indegoControl' style='float: right'>" +
	              "<div data-role='controlgroup' data-type='horizontal' data-inline='true' data-mini='true'>" +
	                "<button id='edit_"  + key + "' onclick=BtnEdit(this.id)> Edit</button>" +
	                "<button id='delete_"+ key + "' onclick=BtnDelete(this.id)>Del</button>" +
	              "</div>" +
	            "</div>" +
	 		"</td>" +
			"</tr>"
	          console.log(key, calendar[key].Start);
	          myTable[myIndex] += myRow
	        }
      }
     i += 1
    }
    i = 1
    while (i <= 5)
     {
      myTable[i] += "<tr><td colspan='3' style='align: left>'"+
              "<div class='indegoadd'>" +
                  "<div data-role='controlgroup' data-type='horizontal' data-inline='true' data-mini='true'>" +
                    "<button id='"+ "add_"+String(i) + "' onclick=BtnAdd(this.id)>Eintrag hinzu</button>" +
                  "</div>" +
                "</div>" +
		'</td></tr>'
      i += 1
     }
    i = 1
    // Now draw the calendars
    while (i <= 5)
     {
        $('#'+  preFixEntryCalendar+ '-'+ String(i)).html(myTable[i]);
        DrawCalendar(preFixDrawCalender+"-"+String(i),i,preFix)
        i +=1
     }


    // Fill the Drawing Calendars
    // First the Mowing-Calendar
    if (preFix == 'm')
    	{ Colour = "#0099000"}
    else
    	{ Colour = "#DC143C"}
    FillDrawingCalendar(myCal,Colour,preFix)

	
}

//******************************************************
// Widget for Mowing calendar
//******************************************************
$.widget("sv.indego_calendar", $.sv.widget, {

  initSelector: 'div[data-widget="indego.calendar"]',

  _create: function()
  {
    this._super();
    var id = this.options.id;
  },

 _update: function(response)
 {

    // wenn keine Daten vorhanden, dann ist kein item mit den eigenschaften hinterlegt und es wird nichts gemacht
    if (response.length === 0)
    {
      notify.error("Indego widget", "No Calendar found ");
      return;
    }
    orgCalendar = $.extend( true, [], response );     
    newCalendar = $.extend( true, [], response );

    UpdateTable(orgCalendar,'indego-draw-calendar','indego-calendar','m')
  }
});


//******************************************************
//Widget for smartMow excluding times calendar
//******************************************************
$.widget("sv.calendar_predictive_list", $.sv.widget, {

initSelector: 'div[data-widget="indego.calendar_predictive_list"]',

_create: function()
{
  this._super();
  var id = this.options.id;
},

_update: function(response)
{

 // wenn keine Daten vorhanden, dann ist kein item mit den eigenschaften hinterlegt und es wird nichts gemacht
 if (response.length === 0)
 {
   notify.error("Indego widget", "No predictive Calendar found ");
   return;
 }
 orgPredictiveCalendar = $.extend( true, [], response );     
 newPredictiveCalendar = $.extend( true, [], response );

 //indego-pred-calendar-1
 //indego-pred-draw-calendar-1
 UpdateTable(orgPredictiveCalendar,'indego-pred-draw-calendar','indego-pred-calendar','p')
 //UpdateTable(orgPredictiveCalendar)
}
});
