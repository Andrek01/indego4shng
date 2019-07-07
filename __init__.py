#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2018 Marco Düchting                   Marco.Duechting@gmx.de
#  Copyright 2018 Bernd Meiners                     Bernd.Meiners@mail.de
#########################################################################
#  This file is part of SmartHomeNG.   
#
#  Sample plugin for new plugins to run with SmartHomeNG version 1.4 and
#  upwards.
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from lib.module import Modules
from lib.model.smartplugin import *
from lib.item import Items
from lib.shtime import Shtime
from datetime import datetime

import time
import base64
import os
import ast
import datetime
import json
import http.client
from dateutil import tz
import sys


import requests
from _ast import Or



# If a package is needed, which might be not installed in the Python environment,
# import it like this:
#
# try:
#     import <exotic package>
#     REQUIRED_PACKAGE_IMPORTED = True
# except:
#     REQUIRED_PACKAGE_IMPORTED = False


class Indego(SmartPlugin):
    """
    Main class of the Indego Plugin. Does all plugin specific stuff and provides
    the update functions for the items
    """
    PLUGIN_VERSION = '1.6.0'

    def __init__(self, sh, *args, **kwargs):
        """
        Initalizes the plugin. The parameters describe for this method are pulled from the entry in plugin.conf.

        :param sh:  **Deprecated**: The instance of the smarthome object. For SmartHomeNG versions 1.4 and up: **Don't use it**!
        :param *args: **Deprecated**: Old way of passing parameter values. For SmartHomeNG versions 1.4 and up: **Don't use it**!
        :param **kwargs:**Deprecated**: Old way of passing parameter values. For SmartHomeNG versions 1.4 and up: **Don't use it**!

        If you need the sh object at all, use the method self.get_sh() to get it. There should be almost no need for
        a reference to the sh object any more.

        The parameters *args and **kwargs are the old way of passing parameters. They are deprecated. They are imlemented
        to support oder plugins. Plugins for SmartHomeNG v1.4 and beyond should use the new way of getting parameter values:
        use the SmartPlugin method get_parameter_value(parameter_name) instead. Anywhere within the Plugin you can get
        the configured (and checked) value for a parameter by calling self.get_parameter_value(parameter_name). It
        returns the value in the datatype that is defined in the metadata.
        """
        from bin.smarthome import VERSION
        if '.'.join(VERSION.split('.', 2)[:2]) <= '1.5':
            self.logger = logging.getLogger(__name__)

        # get the parameters for the plugin (as defined in metadata plugin.yaml):
        #   self.param1 = self.get_parameter_value('param1')

        self.user = self.get_parameter_value('user')
        self.password = self.get_parameter_value('password')
        self.img_pfad = self.get_parameter_value('img_pfad')
        self.cycle = self.get_parameter_value('cycle')
        self.indego_url = self.get_parameter_value('indego_url')
        self.parent_item = self.get_parameter_value('parent_item')
        
        self.items = Items.get_instance()
        self.shtime = Shtime.get_instance()

        self.expiration_timestamp = 0
        self.logged_in = False
        
        self.context_id = ''
        self.user_id = ''
        self.alm_sn = ''
        self.alert_reset = True
        self.auth()
        self.logged_in = self.check_auth()

        self.add_keys = {}
        self.cal_update_count = 0
        self.cal_update_running = False
        
        self.cal_upate_count_pred = 0
        self.cal_pred_update_running = False
        
        self.calendar_count = []

        # Check for initialization errors:
        if not self.indego_url:
           self._init_complete = False
           return

        if not self.parent_item:
           self._init_complete = False
           return

        # The following part of the __init__ method is only needed, if a webinterface is being implemented:

        # if plugin should start even without web interface
        self.init_webinterface()

        # if plugin should not start without web interface
        # if not self.init_webinterface():
        #     self._init_complete = False

        return

    def run(self):
        """
        Run method for the plugin
        """
        self.logger.debug("Run method called")
        self.alive = True

        # start the refresh timers
        self.scheduler_add('state', self.state, cycle = self.cycle)
        self.scheduler_add('alert', self.alert, cycle=30)
        self.scheduler_add('get_calendars', self.get_calendars, cycle=30)
        self.scheduler_add('check_login_state', self.check_login_state, cycle=90)
        self.scheduler_add('device_date', self.device_data, cycle=6000)
        self.scheduler_add('get_weather', self.get_weather, cycle=600)
        self.scheduler_add('get_next_time', self.get_next_time, cycle=300)
        self.scheduler_add('get_smart_frequency', self.get_smart_frequency, cycle=500)
        # if you need to create child threads, do not make them daemon = True!
        # They will not shutdown properly. (It's a python bug)

    def stop(self):
        """
        Stop method for the plugin
        """
        self.get_sh().scheduler.remove('state')
        self.get_sh().scheduler.remove('alert')
        self.get_sh().scheduler.remove('device_date')
        self.get_sh().scheduler.remove('get_weather')
        self.get_sh().scheduler.remove('get_next_time')
        self.get_sh().scheduler.remove('get_smart_frequency')
        self.delete_auth()   # Log off
        self.logger.debug("Stop method called")
        self.alive = False

    def parse_item(self, item):
        """
        Default plugin parse_item method. Is called when the plugin is initialized.
        The plugin can, corresponding to its attribute keywords, decide what to do with
        the item in future, like adding it to an internal array for future reference
        :param item:    The item to process.
        :return:        If the plugin needs to be informed of an items change you should return a call back function
                        like the function update_item down below. An example when this is needed is the knx plugin
                        where parse_item returns the update_item function when the attribute knx_send is found.
                        This means that when the items value is about to be updated, the call back function is called
                        with the item, caller, source and dest as arguments and in case of the knx plugin the value
                        can be sent to the knx with a knx write function within the knx plugin.
        """
        if self.has_iattr(item.conf, 'indego_command'):
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format( item, 'indego_command', self.get_iattr_value(item.conf, 'indego_command')))
            return self.send_command

        if self.has_iattr(item.conf, 'indego_smart'):
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'indego_smart', self.get_iattr_value(item.conf, 'indego_smart')))
            return self.set_smart

        if self.has_iattr(item.conf, 'indego_frequency'):
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'indego_frequency',self.get_iattr_value(item.conf, 'indego_frequency')))
            return self.set_smart_frequency

        if self.has_iattr(item.conf, 'indego_add_key'):
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'indego_add_key', self.get_iattr_value(item.conf, 'indego_add_key')))
            self.add_keys[item.conf['indego_add_key']] = item
        

        if item._name ==  self.parent_item+'.calendar_list':
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'calendar_list', self.get_iattr_value(item.conf, 'calendar_list')))
            return self.update_item
        
        if item._name ==  self.parent_item+'.calendar_predictive_list':
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'calendar_list', self.get_iattr_value(item.conf, 'calendar_list')))
            return self.update_item
        
        if item._name ==  self.parent_item+'.calendar_sel_cal':
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'calendar_list', self.get_iattr_value(item.conf, 'calendar_list')))
            return self.update_item

        if item._name ==  self.parent_item+'.calendar_predictive_sel_cal':
            self.logger.debug("Item '{}' has attribute '{}' found with {}".format(item, 'calendar_list', self.get_iattr_value(item.conf, 'calendar_list')))
            return self.update_item
        
        return None

    def parse_logic(self, logic):
        """
        Default plugin parse_logic method
        """
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    


    def update_item(self, item, caller=None, source=None, dest=None):
        """
        Item has been updated
    
        This method is called, if the value of an item has been updated by SmartHomeNG.
        It should write the changed value out to the device (hardware/interface) that
        is managed by this plugin.
    
        :param item: item to be updated towards the plugin
        :param caller: if given it represents the callers name
        :param source: if given it represents the source
        :param dest: if given it represents the dest
        """

        if caller != self.get_shortname():
            # code to execute, only if the item has not been changed by this this plugin:
            self.logger.info("Update item: {}, item has been changed outside this plugin".format(item.id()))
    
            if self.has_iattr(item.conf, 'foo_itemtag'):
                self.logger.debug("update_item was called with item '{}' from caller '{}', source '{}' and dest '{}'".format(item,caller,source,dest))
            
            if item._name == self.parent_item+'.calendar_list':
                myList = item()
                ResultItem = self.items.return_item(self.parent_item+'.calendar_result')
                ResultItem(str("speichern gestartet"),self.get_shortname())
                self.parse_list_2_cal(myList, self.calendar)
                # Now Save the Calendar on Bosch-API
                self.cal_update_count = 0
                self.auto_mow_cal_update()

            if item._name == self.parent_item+'.calendar_predictive_list':
                self.set_childitem('calendar_predictive_result',"speichern gestartet")
                myList = item()
                self.parse_list_2_cal(myList, self.predictive_calendar)
                # Now Save the Calendar on Bosch-API
                self.upate_count_pred = 0
                self.auto_pred_cal_update()
            
            if item._name == self.parent_item+'.calendar_sel_cal':
                self.set_childitem('calendar_result',"speichern gestartet")
                # Now Save the Calendar on Bosch-API
                self.cal_update_count = 0
                self.auto_mow_cal_update()
            
            if  item._name == self.parent_item+'.calendar_predictive_sel_cal':
                self.set_childitem('calendar_predictive_result',"speichern gestartet")
                # Now Save the Calendar on Bosch-API
                self.upate_count_pred = 0
                self.auto_pred_cal_update()

    
    def check_login_state(self):
        actTimeStamp = time.time()
        if self.expiration_timestamp < actTimeStamp+600:
            self.delete_auth()
            self.auth()
            self.logged_in = self.check_auth()
            self.set_childitem('online', self.logged_in)
            actDate = datetime.datetime.now()
            self.logger.info("refreshed Session-ID at : {}".format(actDate.strftime('Date: %a, %d %b %H:%M:%S %Z %Y')))
        else:
            self.logger.info("Session-ID {} is still valid".format(self.context_id))
            
    def auto_pred_cal_update(self):
        self.cal_upate_count_pred += 1
        self.cal_pred_update_running = True
        
        actCalendar = self.get_childitem('calendar_predictive_sel_cal')
        # set actual Calendar in Calendar-structure
        myCal = self.get_childitem('calendar_predictive')
        myCal['sel_cal'] = actCalendar
        self.set_childitem('calendar_predictive',myCal)
        
        myResult = self.store_calendar(self.predictive_calendar(),'predictive/calendar')
        
        if self.cal_upate_count_pred <=3:
            if myResult != 200:
                if self.cal_upate_count_pred == 1:
                    self.scheduler_add('auto_pred_cal_update', self.auto_pred_cal_update, cycle=60)
                myMsg = "Mäher konnte nicht erreicht werden"
                myMsg += "nächster Versuch in 60 Sekunden"
                myMsg += "Anzahl Versuche : " + str(self.cal_update_count)
            else:
                self.cal_pred_update_running = False
                self.cal_upate_count_pred = 0
                try:
                    self.get_sh().scheduler.remove('auto_pred_cal_update')
                except:
                    pass
                myMsg = "Ausschlusskalender wurde gespeichert"

        else: # Bereits drei Versuche getätigt
            try:
                self.get_sh().scheduler.remove('auto_pred_cal_update')
            except:
                pass
            myMsg = "Ausschlusskalender konnte nach drei Versuchen nicht"
            myMsg += "nicht gespeichert werden."
            myMsg += "Speichern abgebrochen"
            self.cal_pred_update_running = False
            self.cal_upate_count_pred = 0
        
        self.set_childitem('calendar_predictive_result',myMsg)

            

    def auto_mow_cal_update(self):
        self.cal_update_count += 1
        self.cal_update_running = True

        actCalendar = self.get_childitem('calendar_sel_cal')
        # set actual Calendar in Calendar-structure
        myCal = self.get_childitem('calendar')
        myCal['sel_cal'] = actCalendar
        self.set_childitem('calendar',myCal)
        
        myResult = self.store_calendar(self.calendar(),'calendar')
        if self.cal_update_count <=3:
            if myResult != 200:
                if self.cal_update_count == 1:
                    self.scheduler_add('auto_mow_cal_update', self.auto_mow_cal_update, cycle=60)
                myMsg = "Mäher konnte nicht erreicht werden"
                myMsg += "nächster Versuch in 60 Sekunden"
                myMsg += "Anzahl Versuche : " + str(self.cal_update_count)
            else:
                self.cal_update_running = False
                self.cal_update_count = 0
                try:
                    self.get_sh().scheduler.remove('auto_cal_update')
                except:
                    pass
                myMsg = "Mähkalender wurde gespeichert"

        else: # Bereits drei Versuche getätigt
            try:
                self.get_sh().scheduler.remove('auto_mow_cal_update')
            except:
                pass
            myMsg = "Mähkalender konnte nach drei Versuchen nicht"
            myMsg += "nicht gespeichert werden."
            myMsg += "Speichern abgebrochen"
            self.cal_update_running = False
            self.cal_update_count = 0
        
        self.set_childitem('calendar_result',myMsg)
    
    
    def get_calendars(self):    
        try:
            if not self.cal_update_running:
                # get the mowing calendar
                self.calendar = self.items.return_item(self.parent_item + '.' + 'calendar')
                # Only for Tests
                #myTest = {'cals': [{'cal': 2, 'days': [{'slots': [{'EnMin': 30, 'En': True, 'StHr': 12, 'EnHr': 19, 'StMin': 0}, {'En': False}], 'day': 0}, {'slots': [{'EnMin': 0, 'En': True, 'StHr': 11, 'EnHr': 19, 'StMin': 30}, {'EnMin': 0, 'En': True, 'StHr': 6, 'EnHr': 9, 'StMin': 30}], 'day': 2}, {'slots': [{'EnMin': 0, 'En': True, 'StHr': 12, 'EnHr': 20, 'StMin': 0}, {'En': False}], 'day': 4}]}], 'sel_cal': 2}
                #self.calendar(myTest, 'indego')
                self.calendar(self.get_calendar(), 'indego')
                calendar_list = self.items.return_item(self.parent_item + '.' + 'calendar_list')
                calendar_list(self.parse_cal_2_list(self.calendar._value),'indego')
                self.act_Calender = self.items.return_item(self.parent_item + '.' + 'calendar_sel_cal')
                self.act_Calender(self.get_active_calendar(self.calendar()),'indego')
            if not self.cal_update_running:
                # get the predictve calendar for smartmowing
                self.predictive_calendar = self.items.return_item(self.parent_item + '.' + 'calendar_predictive')
                self.predictive_calendar(self.get_predictive_calendar(), 'indego')
                predictive_calendar_list = self.items.return_item(self.parent_item + '.' + 'calendar_predictive_list')
                predictive_calendar_list(self.parse_cal_2_list(self.predictive_calendar._value),'indego')
                self.act_pred_Calender = self.items.return_item(self.parent_item + '.' + 'calendar_predictive_sel_cal')
                self.act_pred_Calender(self.get_active_calendar(self.predictive_calendar()),'indego')
        except Exception as e:
            self.logger.warning("Problem fetching Calendars: {0}".format(e))

    def fetch_url(self, url, username=None, password=None, timeout=2, body=None):
        try:
            response = requests.post(url,auth=(username,password), json=body)
        except Exception as e:
            self.logger.warning("Problem fetching {0}: {1}".format(url, e))
            return False

        if response.status_code == 200 or response.status_code == 201:
            content = response.json()
            try:
                expiration_timestamp = int(str(response.cookies._cookies['api.indego.iot.bosch-si.com']['/']).split(',')[11].split('=')[1])
                 
            except:
                pass
        else:
            self.logger.warning("Problem fetching {0}: {1} {2}".format(url, resp.status, resp.reason))
            content = False
        
        return content,expiration_timestamp
    
    def get_childitem(self, itemname):
        """
        a shortcut function to get value of an item if it exists
        :param itemname:
        :return:
        """
        item = self.items.return_item(self.parent_item + '.' + itemname)  
        if (item != None):
            return item()
        else:
            self.logger.warning("Could not get item '{}'".format(self.parent_item+'.'+itemname))    
    
    
    def set_childitem(self, itemname, value ):
        """
        a shortcut function to set an item with a given value if it exists
        :param itemname:
        :param value:
        :return:
        """
        item = self.items.return_item(self.parent_item + '.' + itemname)  
        if (item != None): 
            item(value, 'indego')
        else:
            self.logger.warning("Could not set item '{}' to '{}'".format(self.parent_item+'.'+itemname, value))

    def get_url(self, url, contextid=None, timeout=40, method='GET'):
        headers = {'Content-Type': 'application/json'}
        headers['Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        headers['x-im-context-id'] = contextid
        plain = True
        if url.startswith('https'):
            plain = False
        lurl = url.split('/')
        host = lurl[2]
        purl = '/' + '/'.join(lurl[3:])
        if plain:
            conn = http.client.HTTPConnection(host, timeout=timeout)
        else:
            conn = http.client.HTTPSConnection(host, timeout=timeout)
        try:
            conn.request(method, purl, headers=headers)
        except Exception as e:
            self.logger.warning("Problem fetching {0}: {1}".format(url, e))
            conn.close()
            return False
        resp = conn.getresponse()
        if resp.status == 401:
            self.logger.warning("get_url returned 401, reconnecting and trying again")
            self.set_childitem('online', False)
            self.auth()
            try:
                conn.request(method, purl, headers=headers)
                resp = conn.getresponse()
            except Exception as e:
                self.logger.warning("Problem fetching {0}: {1}".format(url, e))
                conn.close()
                return False
            
            
        if resp.status == 200 or resp.status == 201:
            content = resp.read()
        else:
            self.logger.warning("Problem fetching {0}: {1} {2}".format(url, resp.status, resp.reason))
            content = False
        conn.close()
        return content

    def put_url(self, url, contextid=None, state=None, timeout=2):
        headers = {'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'}
        headers = {'Content-Type': 'application/json'}
        plain = True
        if url.startswith('https'):
            plain = False
        lurl = url.split('/')
        host = lurl[2]
        purl = '/' + '/'.join(lurl[3:])
        if plain:
            conn = http.client.HTTPConnection(host, timeout=timeout)
        else:
            conn = http.client.HTTPSConnection(host, timeout=timeout)
            headers['x-im-context-id'] = contextid
        body = state
        try:
            conn.request("PUT", purl, body=body, headers=headers)
        except Exception as e:
            self.logger.warning("Problem fetching {0}: {1}".format(url, e))
            conn.close()
            return False
        # resp = conn.getresponse()
        # content = resp.read()
        conn.close()
        self.logger.debug(
            'put gesendet an URL: ' + str(url) + 'context id: ' + str(contextid) + 'command: ' + str(state))
        return True

    def send_command(self, item, command=None, caller=None, source=None, dest=None):
        if self.has_iattr(item.conf, 'indego_command'):
            command = self.get_iattr_value(item.conf,'indego_command')
            self.logger.debug("Function Command " + command + ' ' + str(item()))
            if item():
                message = self.put_url(self.indego_url + 'alms/' + self.alm_sn + '/state', self.context_id, command, 10)
                self.logger.debug("Command " + command + ' gesendet! ' + str(message))

    def set_smart(self, item, command=None, caller=None, source=None, dest=None):
        self.logger.debug("Smart Mode Command " + str(item()))
        if item():
            self.logger.debug("SMAAAAAAAAAAAAAAAAAAAAART aktivieren")
            command = '{"enabled": true}'
        else:
            self.logger.debug("SMAAAAAAAAAAAAAAAAAAAAART deaktivieren")
            command = '{"enabled": false}'
        self.logger.debug("Smart URL: " + self.indego_url + 'alms/' + self.alm_sn + '/predictive')
        message = self.put_url(self.indego_url + 'alms/' + self.alm_sn + '/predictive', self.context_id, command, 10)
        self.logger.debug("Smart Command " + command + ' gesendet! ' + str(message))

    def set_smart_frequency(self, item, frequency=0, caller=None, source=None, dest=None):
        frequency = str(item())
        command = '{"user_adjustment": ' + frequency + '}'
        self.logger.debug("frequency smart " + command + ' ' + str(item()))
        message = self.put_url(self.indego_url + 'alms/' + self.alm_sn + '/predictive/useradjustment', self.context_id,
                               command, 10)
        self.logger.debug("Command " + command + ' gesendet! ' + str(message))

    def delete_auth(self):
        '''
        DELETE https://api.indego.iot.bosch-si.com/api/v1/authenticate
        x-im-context-id: {contextId}
        '''
        headers = {'Content-Type': 'application/json',
                   'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'x-im-context-id' : self.context_id
                  }
        url = self.indego_url + 'authenticate'
        try:
            response = requests.delete(url,auth=(self.user,self.password), headers=headers)
            
        except Exception as e:
            self.logger.warning("Problem logging off {0}: {1}".format(url, e))
            return False

        if (response.status_code == 200 or response.status_code == 201): 
            self.logger.info("Your logged off successfully")
            return True
        else:
            self.logger.info("Log off was not successfull : {0}".format(response.status_code))
            return False

    def store_calendar(self, myCal = None, myName = ""):
        '''
        PUT https://api.indego.iot.bosch-si.com/api/v1/alms/{serial}/calendar
        x-im-context-id: {contextId}
        '''
        
        url = "{}alms/{}/{}".format( self.indego_url, self.alm_sn, myName)
        
        headers = {
                   'x-im-context-id' : self.context_id
                  }

        try:
            response = requests.put(url, headers=headers, json=myCal)
        except err as Exception:
            self.logger.warning("Error during saving Calendar-Infos Error {}".format(err))
            return None
            
        if response.status_code == 200:
            self.logger.info("Set correct Calendar settings for {}".format(myName))
        else:
            self.logger.info("Error during saving Calendar settings for {} HTTP-Status :{}".format(myName, response.status_code))

        return response.status_code            

        
    
    def check_auth(self):
        '''
        GET https://api.indego.iot.bosch-si.com/api/v1/authenticate/check
        Authorization: Basic bWF4Lm11c3RlckBhbnl3aGVyZS5jb206c3VwZXJzZWNyZXQ=
        x-im-context-id: {contextId}
        '''
        headers = {'Content-Type': 'application/json',
                   'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                   'x-im-context-id' : self.context_id
                  }
        url = self.indego_url + 'authenticate/check'
        
        try:
            response = requests.get(url,auth=(self.user,self.password), headers=headers)
            
            
        except Exception as e:
            self.logger.warning("Problem checking Authentication {0}: {1}".format(url, e))
            return False

        if response.status_code == 200 or response.status_code == 201:
            content = response.json()
            self.logger.info("Your are still logged in to the Bosch-Web-API")
            return True
        else:
            self.logger.info("Your are not logged in to the Bosch-Web-API")
            return False

        
        
    def auth(self):
        auth_response,expiration_timestamp = self.fetch_url(self.indego_url + 'authenticate', self.user, self.password, 25,
                                       {"device":"","os_type":"Android","os_version":"4.0","dvc_manuf":"unknown","dvc_type":"unknown"})
        if auth_response == False:
            self.logger.error('AUTHENTICATION INDEGO FAILED! Plugin not working now.')
        else:
            self.expiration_timestamp = expiration_timestamp
            self.logger.debug("String Auth: " + str(auth_response))
            self.context_id = auth_response['contextId']
            self.logger.info("context ID received " + self.context_id)
            self.user_id = auth_response['userId']
            self.logger.info("User ID received " + self.user_id)
            self.alm_sn = auth_response['alm_sn']
            self.logger.info("Serial received " + self.alm_sn)
    
    def get_predictive_calendar(self):
        '''
        GET
        https://api.indego.iot.bosch-si.com/api/v1/alms/{serial}/predictive/calendar
        x-im-context-id: {contextId}
        '''
        url = "{}alms/{}/predictive/calendar".format( self.indego_url, self.alm_sn)
        
        headers = {
                   'x-im-context-id' : self.context_id
                  }

        try:
            response = requests.get(url, headers=headers)
        except err as Exception:
            self.logger.warning("Error during getting predictive Calendar-Infos")
            return None
            
        if response.status_code == 200 or response.status_code == 201:
            content = response.json()
            self.logger.info("Got correct predictive Calendar settings for smartmowing")
            return content

    
    def get_calendar(self):
        '''
        GET
        https://api.indego.iot.bosch-si.com/api/v1/alms/{serial}/calendar
        x-im-context-id: {contextId}
        '''
        url = "{}alms/{}/calendar".format( self.indego_url, self.alm_sn)
        
        headers = {
                   'x-im-context-id' : self.context_id
                  }

        try:
            response = requests.get(url, headers=headers)
        except err as Exception:
            self.logger.warning("Error during getting Calendar-Infos")
            return None
            
        if response.status_code == 200 or response.status_code == 201:
            content = response.json()
            self.logger.info("Got correct Calendar settings for mowing")
            return content
    
    def clear_calendar(self, myCal = None):
        for cal_item in myCal['cals']:
            myCalendarNo = cal_item['cal']
            for days in cal_item['days']:
                myDay = days['day']
                for slots in days['slots']:
                    slots['En'] = False
                    slots['StHr'] = "00"
                    slots['StMin'] = "00"
                    slots['EnHr'] = "00"
                    slots['EnMin'] = "00"

        return myCal
    
            
    def build_new_calendar(self, myList = None):
        
        selected_calendar = self.get_childitem('calendar_sel_cal')
        newCal = {}
        newCal['sel_cal'] = selected_calendar
        newCal['cals'] = []
        newCal['cals'].append({'cal':selected_calendar})  #['cal'] = selected_calendar
        newCal['cals'][0]['days'] = []
    
        for myKey in myList:
            if (myKey == "Params"):
                continue
            NewEntry = {}
            Start = ""
            End = ""
            Days  = ""
            myCalNo = 0
    
            calEntry = myList[myKey].items()
    
            for myEntry in  calEntry:
                if (myEntry[0] =='Start'):
                    Start = myEntry[1]
                elif (myEntry[0] == 'End'):
                    End = myEntry[1]
                elif (myEntry[0] == 'Days'):
                    Days = myEntry[1]
                elif (myEntry[0] == 'Key'):
                    myCalNo = int(myEntry[1][0:1])-1
            for day in Days.split((',')):
                newSlot = {
                            'StHr' : Start[0:2],
                            'StMin' : Start[3:5],
                            'EnHr' : End[0:2],
                            'EnMin' : End[3:5],
                            'En' : True
                           }
                newDay = {
                            'slots': [newSlot],
                            'day' : int(day)
                         }
                dayFound = False
                for x in newCal['cals'][0]['days']:
                    if x['day'] == int(day):
                        oldSlot = x['slots']
                        x['slots'].append(newSlot)
                        dayFound = True
                        break
                if not dayFound:
                    newCal['cals'][0]['days'].append(newDay)

        return newCal
            
    def parse_list_2_cal(self,myList = None, myCal = None):
        if (len(self.calendar_count) < 5):
            myCal._value = self.build_new_calendar(myList)
            print ('Breakpoint')
        else:
            self.clear_calendar(myCal._value)
            for myKey in myList:
                if (myKey == "Params"):
                    continue
                Start = ""
                End = ""
                Days  = ""
                myCalNo = 0
                calEntry = myList[myKey].items()
                for myEntry in  calEntry:
                    if (myEntry[0] =='Start'):
                        Start = myEntry[1]
                    elif (myEntry[0] == 'End'):
                        End = myEntry[1]
                    elif (myEntry[0] == 'Days'):
                        Days = myEntry[1]
                    elif (myEntry[0] == 'Key'):
                        myCalNo = int(myEntry[1][0:1])-1
                # Now Fill the Entry in the Calendar
                for day in Days.split((',')):
                    if (myCal._value['cals'][myCalNo]['days'][int(day)]['slots'][0]['En'] == True):
                        actSlot = 1
                    else:
                        actSlot = 0
                    myCal._value['cals'][myCalNo]['days'][int(day)]['slots'][actSlot]['StHr'] = Start[0:2]
                    myCal._value['cals'][myCalNo]['days'][int(day)]['slots'][actSlot]['StMin'] = Start[3:5]
                    myCal._value['cals'][myCalNo]['days'][int(day)]['slots'][actSlot]['EnHr'] = End[0:2]
                    myCal._value['cals'][myCalNo]['days'][int(day)]['slots'][actSlot]['EnMin'] = End[3:5]
                    myCal._value['cals'][myCalNo]['days'][int(day)]['slots'][actSlot]['En'] = True  

        self.logger.info("Calendar was updated Name :'{}'".format(myCal._name))
    
    def get_active_calendar(self, myCal = None):    
        # First get active Calendar
        activeCal = myCal['sel_cal']
        return activeCal
    
    
    def parse_cal_2_list(self, myCal = None):
        myList = {}
        myList['Params']={}
        myCalList = []
        for cal_item in myCal['cals']:
            print (cal_item)
            myCalendarNo = cal_item['cal']
            if not(myCalendarNo in myCalList):
                myCalList.append(int(myCalendarNo))
            for days in cal_item['days']:
                myDay = days['day']
                print (days)
                for slots in days['slots']:
                    print (slots)
                    #for slot in slots:
                    myEnabled = slots['En']
                    if (myEnabled):
                        try:
                            myStartTime1 = str('%0.2d' %slots['StHr'])+':'+str('%0.2d' %slots['StMin'])
                        except Exception as err:
    
                            myStartTime1 = '00:00'
                        try:
                            myEndTime1 = str('%0.2d' %slots['EnHr'])+':'+str('%0.2d' %slots['EnMin'])
                        except:
                            myEndTime1 = '00:00'
                        myKey = str(myCalendarNo)+'-'+myStartTime1+'-'+myEndTime1
                        myDict = {
                                    'Key':myKey,
                                    'Start' : myStartTime1,
                                    'End'   : myEndTime1,
                                    'Days'  : str(myDay)
                                 }
                        if not myKey in str(myList):
                            myList[myKey] = myDict
    
                        else:
                            if (myStartTime1 != '00:00:' and myEndTime1 != '00:00'):
                                myList[myKey]['Days'] = myList[myKey]['Days']+','+str(myDay)

        myList['Params']['CalCount'] = myCalList
        self.calendar_count = myCalList
        return myList
    
    def get_next_time(self):
            url = "{}alms/{}/predictive/nextcutting?last=YYYY-MM-DDTHH:MM:SS%2BHH:MM".format( self.indego_url, self.alm_sn)
            try:
                result = self.get_url( url, self.context_id, 10)
            except Exception as e:
                self.logger.warning("Problem fetching {0}: {1}".format(url, e))        
            else:
                try:
                    self.logger.debug("Next time raw" + str(result)) # net_time was here
                    next_time = result.decode(encoding='UTF-8', errors='ignore')
                    next_time = json.loads(next_time)
                    next_time = next_time['mow_next']
    
                    self.logger.debug("Next time raw 2: " + str(next_time))
                    # next_time = next_time[:-6]
                    # next_time = datetime.datetime.strptime(next_time,'%Y-%m-%dT%H:%M:%S').replace(tzinfo=tz.gettz('UTC')).astimezone(self.get_sh().tzinfo())
                    # #datetime.datetime.strptime(next_time,'%Y-%m-%dT%H:%M:%S+02:00').replace(tzinfo=self.get_sh().tzinfo())
                    next_time = next_time.replace(":", "")
                    next_time = datetime.datetime.strptime(next_time, '%Y-%m-%dT%H%M%S%z')
                    self.logger.debug("Next time final " + str(next_time))
                    self.set_childitem('next_time',next_time)
                except Exception as e:
                    self.logger.warning("Problem to decode {0} in function get_next_time(): {1}".format(result, e))
                    
                
    def get_weather(self):
        try:
            weather = self.get_url(self.indego_url +'alms/'+ self.alm_sn +'/predictive/weather',self.context_id,10)
            weather = weather.decode(encoding='UTF-8',errors='ignore')
            weather = json.loads(weather)
        except err as Exception:
            return 
        
        for i in weather['LocationWeather']['forecast']['intervals']:
            position = str(weather['LocationWeather']['forecast']['intervals'].index(i))
            self.logger.debug("POSITION "+str(position))
            for x in i:
                wertpunkt = x
                wert = str(i[x])
                self.logger.debug("ITEEEEEM "+'indego.weather.int_'+position+'.'+wertpunkt)
                if wertpunkt == 'dateTime':
                    #wert = wert.replace('+00:00','+0000')
                    self.logger.debug("DATE__TIME "+ wert)
                    wert= datetime.datetime.strptime(wert,'%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=self.shtime.tzinfo())
                if wertpunkt == 'wwsymbol_mg2008':
                    self.logger.debug("WERTPUNKT "+ str(wertpunkt))
                    if wert == '110000' or wert ==  '111000' or wert == '211000' or wert ==  '210000':
                        self.logger.debug("WERTCHEN SPELLS "+ wert)
                        self.set_childitem('weather.int_'+position+'.'+'spells',True)
                        self.set_childitem('weather.int_'+position+'.'+'Sonne',False)
                        self.set_childitem('weather.int_'+position+'.'+'Wolken',False)
                        self.set_childitem('weather.int_'+position+'.'+'Regen',False)
                        self.set_childitem('weather.int_'+position+'.'+'Gewitter',False)
                    elif wert == '100000' or wert ==  '200000':
                        self.logger.debug("WERTCHEN SONNE "+ wert)
                        self.set_childitem('weather.int_'+position+'.'+'spells',False)
                        self.set_childitem('weather.int_'+position+'.'+'Sonne',True)
                        self.set_childitem('weather.int_'+position+'.'+'Wolken',False)
                        self.set_childitem('weather.int_'+position+'.'+'Regen',False)
                        self.set_childitem('weather.int_'+position+'.'+'Gewitter',False)
                    elif wert == '220000' or wert == '121000' or wert == '120000' or wert == '330000' or wert == '320000':
                        self.logger.debug("WERTCHEN WOLKEN "+ wert)
                        self.set_childitem('weather.int_'+position+'.'+'spells',False)
                        self.set_childitem('weather.int_'+position+'.'+'Sonne',False)
                        self.set_childitem('weather.int_'+position+'.'+'Wolken',True)
                        self.set_childitem('weather.int_'+position+'.'+'Regen',False)
                        self.set_childitem('weather.int_'+position+'.'+'Gewitter',False)
                    elif wert == '122000' or wert == '331000' or wert == '221000' or wert == '321000':
                        self.logger.debug("WERTCHEN REGEN "+ wert)
                        self.set_childitem('weather.int_'+position+'.'+'spells',False)
                        self.set_childitem('weather.int_'+position+'.'+'Sonne',False)
                        self.set_childitem('weather.int_'+position+'.'+'Wolken',False)
                        self.set_childitem('weather.int_'+position+'.'+'Regen',True)
                        self.set_childitem('weather.int_'+position+'.'+'Gewitter',False)
                    elif wert == '110001' or wert == '113001' or wert == '123001' or wert == '223001' or wert == '213001' or wert == '210001':
                        self.logger.debug("WERTCHEN GEWITTER "+ wert)
                        self.set_childitem('weather.int_'+position+'.'+'spells',False)
                        self.set_childitem('weather.int_'+position+'.'+'Sonne',False)
                        self.set_childitem('weather.int_'+position+'.'+'Wolken',False)
                        self.set_childitem('weather.int_'+position+'.'+'Regen',False)
                        self.set_childitem('weather.int_'+position+'.'+'Gewitter',True)
                self.set_childitem('weather.int_'+position+'.'+wertpunkt,wert)

        for i in weather['LocationWeather']['forecast']['days']:
            position_day = str(weather['LocationWeather']['forecast']['days'].index(i))
            self.logger.debug("POSITION_day "+str(position_day))
            for x in i:
                wertpunkt_day = x
                wert_day = str(i[x])
                self.logger.debug("ITEEEEEM DAY "+'indego.weather.day_'+position_day+'.'+wertpunkt_day)
                if wertpunkt_day == 'date':
                    wert_day = datetime.datetime.strptime(wert_day,'%Y-%m-%d').replace(tzinfo=self.shtime.tzinfo())
                    days = ["Montag","Dienstag","Mittwoch","Donnerstag","Freitag","Samstag","Sonntag"]
                    dayNumber = wert_day.weekday()
                    wochentag = days[dayNumber]
                    self.logger.debug("WOCHENTAG GEWITTER "+ wochentag)
                    self.set_childitem('weather.day_'+position_day+'.'+'wochentag',wochentag)
                    self.set_childitem('weather.day_'+position_day+'.'+wertpunkt_day,wert_day)

    def alert(self):
        self.logger.debug("ÄLÄRMCHEN START")
        alert_response = self.get_url(self.indego_url + 'alerts', self.context_id, 10)
        if alert_response == False:
            self.logger.debug("No Alert or error")
            self.alert_reset = False
        else:
            self.logger.debug("ALARM ELSE")
            alert_response = alert_response.decode(encoding='UTF-8', errors='ignore')
            self.logger.debug("Alärmchen: " + str(alert_response))
            alert_response = json.loads(alert_response)
            self.logger.debug("Alärmchen 2: " + str(alert_response))
            if len(alert_response) == 0:
                self.logger.debug("No new Alert Messages")

            else:
                self.logger.warning("alert_response " + str(alert_response))
                alerts = len(alert_response)
                self.logger.debug("ALERTS " + str(alerts))
                if len(alert_response) == 1:
                    alert_latest = alert_response[0]
                    self.alert_reset = False
                else:
                    # alert_latest = ast.literal_eval(alert_response[0]+'}')
                    self.logger.debug("ALERTerS " + str(alert_response[len(alert_response) - 1]))
                    alert_latest = alert_response[len(alert_response) - 1]
                    self.alert_reset = True

                alert_id = alert_latest['alert_id']
                self.set_childitem('alert_id',alert_id)
                self.logger.debug("alert_id " + str(alert_id))

                alert_message = alert_latest['message'].replace(
                    ' Bitte folgen Sie den Anweisungen im Display des Mähers.', '')
                self.set_childitem('alert_message',alert_message)
                self.logger.debug("alert_message " + str(alert_message))

                alert_date = datetime.datetime.strptime(alert_latest['date'], '%Y-%m-%dT%H:%M:%S.%fZ').replace(
                    tzinfo=tz.gettz('UTC')).astimezone(
                    self.shtime.tzinfo())  # alert_date = datetime.datetime.strptime(alert_latest['date'],'%Y-%m-%dT%H:%M:%S.%fZ')
                self.set_childitem('alert_date',alert_date)
                self.logger.debug("alert_date " + str(alert_date))

                alert_headline = alert_latest['headline']
                self.set_childitem('alert_headline',alert_headline)
                self.logger.debug("alert_headline  " + str(alert_headline))

                alert_flag = alert_latest['flag']
                self.set_childitem('alert_flag',alert_flag)
                self.logger.debug("alert_flag " + str(alert_flag))

                self.alert_delete(alert_id)

    def get_smart_frequency(self):
        self.logger.debug("getting smart frequency")
        smart_frequency_response = self.get_url(self.indego_url + 'alms/' + self.alm_sn + '/predictive/useradjustment',
                                                self.context_id)
        smart_frequency_response = smart_frequency_response.decode(encoding='UTF-8', errors='strict')
        smart_frequency_response = json.loads(smart_frequency_response)
        frequency = smart_frequency_response['user_adjustment']
        self.set_childitem('SMART.frequenz',frequency)
        self.logger.debug("smart_frequenz " + str(frequency))

    def alert_delete(self, alert_id):
        self.logger.debug("deleting alert_id " + str(alert_id))
        self.get_url(self.indego_url + 'alerts/' + alert_id, self.context_id, 50, 'DELETE')

    def device_data(self):
        self.logger.debug('device_date')
        device_data_response = self.get_url(self.indego_url + 'alms/' + self.alm_sn, self.context_id)
        if device_data_response == False:
            self.logger.error('Device Data disconnected')
        else:
            self.logger.debug('device data RAW: ' + str(device_data_response))
            device_data_response = device_data_response.decode(encoding='UTF-8', errors='ignore')
            self.logger.debug('device date stringtanga: ' + device_data_response)
            # device_data_response = str(device_data_response).replace('false','False').replace('true','True')
            device_data_response = json.loads(device_data_response)
            self.logger.debug('device date JASON: ' + str(device_data_response))

            alm_sn = device_data_response['alm_sn']
            self.set_childitem('alm_sn',alm_sn)
            self.logger.debug("alm_sn " + str(alm_sn))

            if 'alm_name' in device_data_response:
                alm_name = device_data_response['alm_name']
                self.set_childitem('alm_name',alm_name)
                self.logger.debug("alm_name " + str(alm_name))

            service_counter = device_data_response['service_counter']
            self.set_childitem('service_counter',service_counter)
            self.logger.debug("service_counter " + str(service_counter))

            needs_service = device_data_response['needs_service']
            self.set_childitem('needs_service',needs_service)
            self.logger.debug("needs_service " + str(needs_service))

            alm_mode = device_data_response['alm_mode']
            self.set_childitem('alm_mode',alm_mode)
            if alm_mode == 'smart':
                self.logger.debug("ALM_MODE smaAAAAArt")
                self.set_childitem('SMART', True)
            else:
                self.logger.debug("ALM_MODE MANUAAAAAAAAL")
                self.set_childitem('SMART', False)
            self.logger.debug("alm_mode " + str(alm_mode))

            bareToolnumber = device_data_response['bareToolnumber']
            self.set_childitem('bareToolnumber',bareToolnumber)
            self.logger.debug("bareToolnumber " + str(bareToolnumber))

            if 'alm_firmware_version' in device_data_response:
                alm_firmware_version = device_data_response['alm_firmware_version']
                if alm_firmware_version != self.get_sh().indego.alm_firmware_version():
                    self.set_childitem('alm_firmware_version.before',self.get_sh().indego.alm_firmware_version())
                    self.set_childitem('alm_firmware_version.changed', self.shtime.now() )
                    self.logger.info(
                        "indego updated firmware from " + self.get_sh().indego.alm_firmware_version() + ' to ' + str(
                            alm_firmware_version))

                    self.set_childitem('alm_firmware_version',alm_firmware_version)
                self.logger.debug("alm_firmware_version " + str(alm_firmware_version))

    def state(self):
        state__str = {0: ['Lese Status', 'unknown'], 257: ['lädt', 'dock'], 258: ['docked', 'dock'],
                      259: ['Docked-Softwareupdate', 'dock'], 260: ['Docked', 'dock'], 261: ['docked', 'dock'],
                      262: ['docked - lädt Karte', 'dock'], 263: ['docked-speichert Karte', 'dock'],
                      513: ['mäht', 'moving'], 514: ['bestimme Ort', 'moving'], 515: ['lade Karte', 'moving'],
                      516: ['lerne Garten', 'moving'], 517: ['Pause', 'pause'], 518: ['schneide Rand', 'moving'],
                      519: ['stecke fest', 'hilfe'], 769: ['fährt in Station', 'moving'],
                      770: ['fährt in Station', 'moving'], 771: ['fährt zum Laden in Station', 'moving'],
                      772: ['fährt in Station – Mähzeit beendet', 'moving'],
                      773: ['fährt in Station - überhitzt', 'help'], 774: ['fährt in Station', 'moving'],
                      775: ['fährt in Station - fertig gemäht', 'moving'],
                      776: ['fährt in Station - bestimmt Ort', 'moving'], 1025: ['Diagnosemodus', 'unknown'],
                      1026: ['Endoflive', 'hilfe'], 1281: ['Softwareupdate', 'dock'],
                      1537: ['Stromsparmodus','dock'],
                      64513:['wacht auf','dock']}
        state_response = self.get_url(self.indego_url + 'alms/' + self.alm_sn + '/state', self.context_id)

        # now reconnection in get_url directly
        # if state_response == False:
        #	self.logger.error('Indego disconnected')
        #	self.set_childitem('online',False)
        #	self.auth()

        if state_response != False:
            state_response = state_response.decode(encoding='UTF-8', errors='ignore')
            self.set_childitem('online', True)
            self.logger.debug("indego state received " + str(state_response))
            states = json.loads(state_response)

            if 'error' in states:
                error_code = states['error']
                self.set_childitem('stateError',error_code)
                self.logger.error("error_code " + str(error_code))
            else:
                error_code = 0
                self.set_childitem('stateError',error_code)

            state_code = states['state']
            self.set_childitem('stateCode',state_code)
            self.logger.debug("state code " + str(state_code))
            if state__str[state_code][1] == 'dock':
                self.logger.debug('indego docked')
                self.alert_reset = True
                self.set_childitem('docked', True)
                self.set_childitem('moving', False)
                self.set_childitem('pause', False)
                self.set_childitem('help', False)
            if state__str[state_code][1] == 'moving':
                self.logger.debug('indego moving')
                self.alert_reset = True
                self.set_childitem('mowedDate', self.shtime.now())
                self.set_childitem('docked', False)
                self.set_childitem('moving', True)
                self.set_childitem('pause', False)
                self.set_childitem('help', False)
            if state__str[state_code][1] == 'pause':
                self.logger.debug('indego pause')
                self.alert_reset = True
                self.set_childitem('docked', False)
                self.set_childitem('moving', False)
                self.set_childitem('pause', True)
                self.set_childitem('help', False)
            if state__str[state_code][1] == 'hilfe':
                self.logger.debug('indego hilfe')
                self.set_childitem('docked', False)
                self.set_childitem('moving', False)
                self.set_childitem('pause', False)
                self.set_childitem('help', True)
                if self.alert_reset == True:
                    self.logger.debug("Alert aufgefrufen, self_alert_reset = True")
                    self.alert()
                else:
                    self.logger.debug("Alert nicht aufgefrufen, self_alert_reset = False")

            state_str = state__str[state_code][0]
            self.set_childitem('state_str', state_str )
            self.logger.debug("state str " + state_str)

            mowed = states['mowed']
            self.set_childitem('mowedPercent', mowed)
            self.logger.debug("mowed " + str(mowed))

            mowmode = states['mowmode']
            self.set_childitem('mowmode',mowmode)
            self.logger.debug("mowmode  " + str(mowmode))

            total_operate = states['runtime']['total']['operate']
            self.set_childitem('runtimeTotalOperationMins',total_operate)
            self.logger.debug("total_operate " + str(total_operate))

            total_charge = states['runtime']['total']['charge']
            self.set_childitem('runtimeTotalChargeMins',total_charge)
            self.logger.debug("total_charge " + str(total_charge))

            session_operate = states['runtime']['session']['operate']
            self.set_childitem('runtimeSessionOperationMins',session_operate)
            self.logger.debug("session_operate " + str(session_operate))

            session_charge = states['runtime']['session']['charge']
            self.set_childitem('runtimeSessionChargeMins',session_charge)
            self.logger.debug("session_charge " + str(session_charge))

            if 'xPos' in states:
                xPos = states['xPos']
                self.set_childitem('xPos',xPos)
                self.logger.debug("xPos " + str(xPos))

                yPos = states['yPos']
                self.set_childitem('yPos',yPos)
                self.logger.debug("yPos " + str(yPos))

                svg_xPos = states['svg_xPos']
                self.set_childitem('svg_xPos',svg_xPos)
                self.logger.debug("svg_xPos " + str(svg_xPos))

                svg_yPos = states['svg_yPos']
                self.set_childitem('svg_yPos',svg_yPos)
                self.logger.debug("svg_yPos " + str(svg_yPos))

            if 'config_change' in states and 'config_change' in self.add_keys:
                config_change = states['config_change']
                self.items.return_item(str(self.add_keys['config_change']))(config_change)
                self.logger.debug("config_change " + str(config_change))

            if 'mow_trig' in states and 'mow_trig' in self.add_keys:
                mow_trig = states['mow_trig']
                self.items.return_item(str(self.add_keys['mow_trig']))(mow_trig)
                self.logger.debug("mow_trig " + str(mow_trig))

            # if 'map_update_available' in states and 'mow_trig' in self.add_keys:
            #	mow_trig = states['map_update_available']
            #	self.get_sh().return_item(str(self.add_keys['mow_trig']),mow_trig)
            #	self.logger.debug("mow_trig "+str(mow_trig))

            map_update = states['map_update_available']
            self.logger.debug("map_update " + str(map_update))
            self.set_childitem('mapUpdateAvailable',map_update)
            if map_update:
                self.logger.debug('lade neue Karte')
                garden = self.get_url(self.indego_url + 'alms/' + self.alm_sn + '/map', self.context_id, 120)
                if garden == False:
                    self.logger.warning('Map returned false')
                else:
                    with open(self.img_pfad, 'wb') as outfile:
                        outfile.write(garden)
                        self.logger.debug('You have a new MAP')
                        self.set_childitem('mapSvgCacheDate',self.shtime.now())

    def init_webinterface(self):
        """"
        Initialize the web interface for this plugin

        This method is only needed if the plugin is implementing a web interface
        """
        try:
            self.mod_http = Modules.get_instance().get_module(
                'http')  # try/except to handle running in a core version that does not support modules
        except:
            self.mod_http = None
        if self.mod_http == None:
            self.logger.error("Not initializing the web interface")
            return False

        import sys
        if not "SmartPluginWebIf" in list(sys.modules['lib.model.smartplugin'].__dict__):
            self.logger.warning("Web interface needs SmartHomeNG v1.5 and up. Not initializing the web interface")
            return False

        # set application configuration for cherrypy
        webif_dir = self.path_join(self.get_plugin_dir(), 'webif')
        config = {
            '/': {
                'tools.staticdir.root': webif_dir,
            },
            '/static': {
                'tools.staticdir.on': True,
                'tools.staticdir.dir': 'static'
            }
        }

        # Register the web interface as a cherrypy app
        self.mod_http.register_webif(WebInterface(webif_dir, self),
                                     self.get_shortname(),
                                     config,
                                     self.get_classname(), self.get_instance_name(),
                                     description='')

        return True



# ------------------------------------------
#    Webinterface of the plugin
# ------------------------------------------

import cherrypy
from jinja2 import Environment, FileSystemLoader


class WebInterface(SmartPluginWebIf):

    def __init__(self, webif_dir, plugin):
        """
        Initialization of instance of class WebInterface

        :param webif_dir: directory where the webinterface of the plugin resides
        :param plugin: instance of the plugin
        :type webif_dir: str
        :type plugin: object
        """
        self.logger = logging.getLogger(__name__)
        self.webif_dir = webif_dir
        self.plugin = plugin
        self.tplenv = self.init_template_environment()

    @cherrypy.expose
    def index(self, reload=None):
        """
        Build index.html for cherrypy

        Render the template and return the html file to be delivered to the browser

        :return: contents of the template after beeing rendered 
        """
        tmpl = self.tplenv.get_template('index.html')
        # add values to be passed to the Jinja2 template eg: tmpl.render(p=self.plugin, interface=interface, ...)
        return tmpl.render(p=self.plugin)


