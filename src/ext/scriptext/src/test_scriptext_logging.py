# Copyright (c) 2009 Nokia Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import test.test_support
import unittest
# In case the module is not loaded, test_scriptext
# would be skipped - "No module named scriptext"
import scriptext
import time
import e32
count1 = 0
count2 = 0
event_type_list = [0, 1, 2, 3, 4]
# Corresponds to EKLogCallEventType,EKLogDataEventType, EKLogFaxEventType,
# EKLogShortMessageEventType, EKLogPacketDataEventType respectively


class SynchronousLoggingTest(unittest.TestCase):
    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.logging_handle = None
        self.logging_handle = scriptext.load('Service.Logging', 'IDataSource')      
        
    def test_getlist(self):
        """ Get list of logs"""
        logging_info = self.logging_handle.call('GetList', {'Type': u'Log',})
        for item in logging_info:
            event_type = item['EventType']
            if event_type not in event_type_list:
                self.fail('Event Type is invalid')
            remote_party = item['RemoteParty']
            if 'Direction' in item:
                direction = item['Direction'] 
            event_time = ['EventTime']
            sub = item['Subject']
            phone_no = item['PhoneNumber']
            description = item['Description']
            event_data = item['EventData']

    def test_add(self):
        """ Add a log"""
        log_id = self.logging_handle.call('Add',
                                               {'Type': u'Log',
                                                'Item': {'EventType': 0,}})
            
    def test_delete(self):
        """ Delete a log"""
        log_id = self.logging_handle.call('Add', {'Type': u'Log', 
                                                  'Item': {'EventType': 3,
                                                  'Direction': 1,
                                                  'EventDuration': 2, 
                                                  'DeliveryStatus': 1,
                                                  'PhoneNumber': u'666'}})
        self.logging_handle.call('Delete', {'Type': u'Log', 
                                            'Data': {'id': log_id,}}) 

class AsynchronousLoggingTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.lock = e32.Ao_lock()
        self.timer = e32.Ao_timer()
        self.async_request_failed = False
        
    def ao_timer_callback(self):
        self.async_request_failed = True
        self.output_params['TestFailureReason'] = "Wait timeout. Callback" + \
                                    "function for the async request not hit"
        self.lock.signal()

    def check_error_and_signal(self, output_params):
        if 'TestFailureReason' in output_params:
            self.async_request_failed = True
        self.output_params = output_params
        self.timer.cancel()
        self.lock.signal()

    def do_load(self):
        service_handle = scriptext.load('Service.Logging', 'IDataSource')
        return service_handle


def test_main():
    test.test_support.run_unittest(SynchronousLoggingTest,
                                   AsynchronousLoggingTest)


if __name__ == "__main__":
    test_main()