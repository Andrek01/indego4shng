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
var calType = ""

var activeOrgPredictive = 0
var activeOrgCalendar = 0
var activeNewPredictive = 0
var activeNewCalendar = 0

var CalCount = 0
var m_CalCount = 0
var p_CalCount = 0



function EnableCalendar(calType)
{
	// document.getElementById("myH3").firstChild.textContent = "Mähkalender"
	if (calType == 'M')
		{ CalCount = m_CalCount}
	else
		{ CalCount = p_CalCount }
			
	for (actCal in CalCount)
		{
		 var strActCal = CalCount[actCal]
		 if (calType == 'M')
			 { var myCal = "mow_cal_"+strActCal }
		 else
			 { var myCal = "pred_cal_"+strActCal }
		 // Show Collapsible for transmitted Calendars
		 document.getElementById(myCal).style.display="block"
	     if (calType == 'M')
		 { document.getElementById("mow_caption_"+strActCal).firstChild.textContent = "Mähkalender ("+strActCal+")"}
		 else
		 { document.getElementById("pred_caption_"+strActCal).firstChild.textContent = "Ausschlusskalender ("+strActCal+")"}
		 if (CalCount.length > 1)
			{
			 // Show labels for transmitted Calendars
			 var strCaption = calType + '-caption_cal_'+strActCal
			 document.getElementById(strCaption).style.display="block"			
			}
		}
	if (CalCount.length == 1)
		{
		 var strActCal = CalCount[0]
		 var strCaption = calType + '-caption_cal_6'
		 document.getElementById(strCaption).style.display="block"			
		 document.getElementById(strCaption).value = CalCount[0]
		}
}
	
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

function ReDrawActCalendar(actCal, type)
{
	if (type == 'M')
		{
		  CalCount = m_CalCount
		  activeCalendar = activeNewCalendar
		}
	else
		{
		  CalCount = p_CalCount
		  activeCalendar = activeNewPredictive
		}

	// Create round Corner for ON
    var activeDay = type + "-caption_cal_6"	     
    document.getElementById(activeDay).classList.add("ui-first-child")
	
	i=0
	while (i <= 6)
		{
	  	 var activeDay = type + "-cal_"+parseInt(i)
	  	 if (activeCalendar == i)
	  		 { document.getElementById(activeDay).checked = true }
	  	 else
			 { document.getElementById(activeDay).checked = false }

	     $(document.getElementById(activeDay)).checkboxradio("refresh")
		 i += 1
		}

	if (CalCount.length == 1 && activeCalendar != "0")
	{
	  	 var activeDay = type + "-cal_6"
  		 document.getElementById(activeDay).checked = true 
	     $(document.getElementById(activeDay)).checkboxradio("refresh")
	}

}

function GetActCalendar(type)
{
	i=0
	while (i <= 6)
		{
	  	 var activeDay = type + "-cal_"+parseInt(i)
	  	 if ( document.getElementById(activeDay).checked == true)
	  		 {
	  		  if (i == 6) 		// Spezialfall - nur ein Kalender EIN/AUS
	  		  i = CalCount[0]
	  		  break
	  		 }
		 i += 1
		}
	return i
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
    newCalendar = $.extend( true, [], orgCalendar );
	UpdateTable(orgCalendar,'indego-draw-calendar','indego-calendar','m')	
	
    activeNewCalendar =  activeOrgCalendar
	ReDrawActCalendar(activeNewCalendar, 'M');
}

function SaveChanges_mow()
{
	activeNewCalendar = GetActCalendar('M')
	io.write('indego.calendar_sel_cal',activeNewCalendar)
	//activeOrgCalendar = activeNewCalendar
	
	io.write('indego.calendar_list',newCalendar[0])
    //orgCalendar = $.extend( true, [], newCalendar );
	io.write('indego.calendar_save', true)
}

// Functions for Predictive Calendar
function CancelChanges_pred()
{
    newPredictiveCalendar = $.extend( true, [], orgPredictiveCalendar );
    UpdateTable(orgPredictiveCalendar,'indego-pred-draw-calendar','indego-pred-calendar','p')

    activeNewPredictive = activeOrgPredictive
	ReDrawActCalendar(activeNewPredictive, 'P');

}

function SaveChanges_pred()
{
	activeNewPredictive = GetActCalendar('P')
	io.write('indego.calendar_predictive_sel_cal',activeNewPredictive)
    //activeOrgPredictive = activeNewPredictive

	
	io.write('indego.calendar_predictive_list',newPredictiveCalendar[0])
    //orgPredictiveCalendar = $.extend( true, [], newPredictiveCalendar );
	io.write('indego.calendar_predictive_save', true)
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
    if (mode == "Edit")
    	{
    	 //Remove the old Key/Value
    	if (calType == 'm')
    	{ delete newCalendar[0][oldKey]	}
    	else 
    	{ delete newPredictiveCalendar[0][oldKey]	}
    	}
	if (calType == 'm')
		{
		 newCalendar[0][myKey]=myEntry
		 UpdateTable(newCalendar,'indego-draw-calendar','indego-calendar',calType)
		}
	else
		{
		 newPredictiveCalendar[0][myKey]=myEntry
		 UpdateTable(newPredictiveCalendar,'indego-pred-draw-calendar','indego-pred-calendar',calType)
		}
	
	
    popup.className = 'overlayHidden';

}


	
	
function BtnEdit(click_item)
{
 console.log("BtnEdit from element :"+click_item);
 myKey = click_item.substring(6,21)
 oldKey = myKey
 actCalendar = click_item.substring(6,7)
 calType = click_item.substring(0,1)
 if (calType == 'm')
	 { myObj = newCalendar[0][myKey] }
 else
 	 { myObj = newPredictiveCalendar[0][myKey] }

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
	myKey = click_item.substring(8,21)
	calType = click_item.substring(0,1)
	if (calType == 'm')
		{
		 delete newCalendar[0][myKey]
		 UpdateTable(newCalendar,'indego-draw-calendar','indego-calendar',calType)
		}
	else
		{
		 delete newPredictiveCalendar[0][myKey]
		 UpdateTable(newPredictiveCalendar,'indego-pred-draw-calendar','indego-pred-calendar',calType)
		}
 
}

function BtnAdd(click_item)
{
 console.log("BtnAdd from element :"+click_item);
 InitWindow()
 actCalendar = click_item.substring(5,6)
 calType = click_item.substring(0,1)
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
    		 if (key == 'Params')
        	 {
        	  continue
        	 }
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
             if (key == 'Params')
            	 {
            	  continue
            	 }
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
	                "<button id='"+preFix+"edit_"  + key + "' onclick=BtnEdit(this.id)> Edit</button>" +
	                "<button id='"+preFix+"delete_"+ key + "' onclick=BtnDelete(this.id)>Del</button>" +
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
                    "<button id='" +preFix+ "add_"+String(i) + "' onclick=BtnAdd(this.id)>Eintrag hinzu</button>" +
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
  },

 _update: function(response)
 {

    // wenn keine Daten vorhanden, dann ist kein item mit den eigenschaften hinterlegt und es wird nichts gemacht
    if (response.length === 0)
    {
      notify.error("Indego widget", "No Calendar found ");
      return;
    }

    for (var key in response[0])
     {
  	 if (response[0].hasOwnProperty(key))
        {
          if (key = 'Params')
        	  {
        	   m_CalCount = response[0][key]['CalCount']
        	  }
        }

     }
    orgCalendar = $.extend( true, [], response );     
    newCalendar = $.extend( true, [], response );
    EnableCalendar('M')
    UpdateTable(orgCalendar,'indego-draw-calendar','indego-calendar','m')
    ReDrawActCalendar(activeNewCalendar, 'M')
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
},

_update: function(response)
{

 // wenn keine Daten vorhanden, dann ist kein item mit den eigenschaften hinterlegt und es wird nichts gemacht
 if (response.length === 0)
 {
   notify.error("Indego widget", "No predictive Calendar found ");
   return;
 }
 
 for (var key in response[0])
 {
	 if (response[0].hasOwnProperty(key))
    {
      if (key = 'Params')
    	  {
    	   p_CalCount = response[0][key]['CalCount']
    	  }
    }

 }

 orgPredictiveCalendar = $.extend( true, [], response );     
 newPredictiveCalendar = $.extend( true, [], response );

 EnableCalendar('P')
 UpdateTable(orgPredictiveCalendar,'indego-pred-draw-calendar','indego-pred-calendar','p')
 ReDrawActCalendar(activeNewPredictive, 'P')

}
});

//*****************************************************
// Widget for active calendar
//*****************************************************
$.widget("sv.calendar_sel_cal", $.sv.widget, {

initSelector: 'div[data-widget="indego.calendar_sel_cal"]',
	options: {
		mode: '',
		id: ''
	},

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
 notify.error("Indego widget", "No active predictive Calendar found ");
 return;
}

var type = this.options.mode
if (type == 'P')
	{
  	 activeOrgPredictive = parseInt(response[0]);     
  	 activeNewPredictive = parseInt(response[0]);     
  	 ReDrawActCalendar(activeNewPredictive, type)
	}
else 
	{
	 activeOrgCalendar = parseInt(response[0]);     
  	 activeNewCalendar = parseInt(response[0]);     
  	 ReDrawActCalendar(activeNewCalendar, type);
	}



}
});

//*****************************************************
//Widget for Symbols
//*****************************************************
$.widget("sv.symbol", $.sv.widget, {

	initSelector: '[data-widget="indego.symbol"]',
	
	options: {
		mode: '',
		val: '',
		id: ''
	},

	_create: function()
	{
		this._super()
  	    var id = this.options.id;
	},
	_update: function(response)
    {
		// response will be an array, if more then one item is requested
		var bit = (this.options.mode == 'and');
		if (response instanceof Array) {
			for (var i = 0; i < response.length; i++) {
				if (this.options.mode == 'and') {
					bit = bit && (response[i] == this.options.val);
				}
				else {
					bit = bit || (response[i] == this.options.val);
				}
			}
		}
		else {
			bit = (response == this.options.val);
		}
		if (bit) {
			this.element.show();

		}
		else {
			this.element.hide();
		}
	}
});
//*****************************************************
//Widget for Mow-Mode (Calendar = 1, off = 0, smart = 2
//*****************************************************
$.widget("sv.mode_active", $.sv.widget, {

	initSelector: 'span[data-widget="indego.run_mode"]',

	options: {
		mode : 0
	},

	_create: function() {
		this._super();

		var shortpressEvent = function(event) {
			// get the list of values
			var list_val = String(this.options.vals).explode();
			// get the index of the memorised value
			var old_idx = list_val.indexOf(this._current_val);
			// compute the next index
			var new_idx = (old_idx + 1) % list_val.length;
			// get next value
			var new_val = list_val[new_idx];
			// send the value to driver
			io.write(this.options.item, new_val);
			// memorise the value for next use
			this._current_val = new_val;
			/*
			// activity indicator
			var target = $(event.delegateTarget);
			var indicatorType = this.options['indicator-type'];
			var indicatorDuration = this.options['indicator-duration'];
			if(indicatorType && indicatorDuration > 0) {
				// add one time event to stop indicator
				target.one('stopIndicator',function(event) {
					clearTimeout(target.data('indicator-timer'));
					event.stopPropagation();
					var prevColor = target.attr('data-col');
					if(prevColor != null) {
						if(prevColor != 'icon1')
							target.removeClass('icon1').find('svg').removeClass('icon1');
						if(prevColor != 'blink')
							target.removeClass('blink').find('svg').removeClass('blink');
						if(prevColor == 'icon1' || prevColor == 'icon0')
							prevColor = '';
						target.css('color', prevColor).find('svg').css('fill', prevColor).css('stroke', prevColor);
					}
				})
				// set timer to stop indicator after timeout
				.data('indicator-timer', setTimeout(function() { target.trigger('stopIndicator') }, indicatorDuration*1000 ));
				// start indicator
				if(indicatorType == 'icon1' || indicatorType == 'icon0' || indicatorType == 'blink') {
					target.addClass(indicatorType).find('svg').addClass(indicatorType);
					indicatorType = '';
				}
				target.css('color', indicatorType).find('svg').css('fill', indicatorType).css('stroke', indicatorType);
			}
			*/
		}

		/*
		// replicate ui-first-child and ui-last-child if first resp. last sibling of tag 'a' has it
		if(this.element.children('a:first').hasClass('ui-first-child'))
			this.element.children('a').addClass('ui-first-child');
		if(this.element.children('a:last').hasClass('ui-last-child'))
			this.element.children('a').addClass('ui-last-child');
		// display first control as default
		this.element.after(this.element.children('a[data-widget="basic.stateswitch"]:first'));
		*/
	},

	_update: function(response) {
		// get list of values
		var list_val = String(this.options.vals).explode();
		// get received value
		var val = response.toString().trim();
		// hide all states
		this.element.next('a[data-widget="basic.stateswitch"][data-index]').insertBefore(this.element.children('a:eq(' + this.element.next('a[data-widget="basic.stateswitch"][data-index]').attr('data-index') + ')'));
		// stop activity indicator
		this.element.children('a[data-widget="basic.stateswitch"]').trigger('stopIndicator');
		// show the first corrseponding to value. If none corrseponds, the last one will be shown by using .addBack(':last') and .first()
		this.element.after(this.element.children('a[data-widget="basic.stateswitch"]').filter('[data-val="' + val + '"]:first').addBack(':last').first());
		// memorise the value for next use
		this._current_val = val;
	},

});

