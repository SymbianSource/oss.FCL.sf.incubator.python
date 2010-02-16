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
import e32
import time
import datetime

start_time = datetime.datetime(2009, 07, 10, 16, 0, 0)
end_time = datetime.datetime(2009, 07, 10, 17, 0, 0)


class SynchronousCalendarTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.contacts_handle = None
        self.calendar_handle = scriptext.load('Service.Calendar',
                                              'IDataSource')

    def test_meeting_entry(self):
        """ Add a meeting and check if its added properly"""
        calendar_id = self.calendar_handle.call('Add',
              {'Type': u'CalendarEntry',
               'Item': {'Type': u'Meeting',
                        'Description': u'Project Planning',
                        'StartTime': start_time,
                        'EndTime': end_time}})

        meeting_list = self.calendar_handle.call('GetList',
                                    {'Type': u'CalendarEntry',
                                     'Filter': {'CalendarName': u'C:Calendar',
                                                'Type': u'Meeting'}})

        for entry in meeting_list:
            if calendar_id in entry['id']:
                self.assert_(entry['Description'] == 'Project Planning' and
                             entry['StartTime'] == start_time and
                             entry['EndTime'] == end_time)

    def test_import_calentry(self):
        """ Import a calendar entry"""
        self.calendar_handle.call('Import', {'Type': u'CalendarEntry',
            'Data': {'FileName': u'C:\\data\\python\\importfile.txt',
                     'Format': u'VCal'}})

    def test_export_calentry(self):
        """ Export a calendar entry"""
        self.calendar_handle.call('Export', {'Type': u'CalendarEntry',
            'Data': {'Format': u'VCal',
                     'FileName': u'C:\\data\\python\\importfile.txt'}})


class ASynchronousCalendarTest(unittest.TestCase):

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
        service_handle = scriptext.load('Service.Calendar', 'IDataSource')
        return service_handle


def test_main():
    test.test_support.run_unittest(SynchronousCalendarTest,
                                   ASynchronousCalendarTest)


if __name__ == "__main__":
    test_main()
