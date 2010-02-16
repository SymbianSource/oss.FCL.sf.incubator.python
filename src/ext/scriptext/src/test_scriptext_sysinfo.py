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


class SynchronousSysInfoTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.sysinfo_handle = None
        self.sysinfo_handle = scriptext.load('Service.SysInfo', 'ISysInfo')

    def test_setinfo(self):
        """ Make a request to set vibra mode"""
        self.sysinfo_handle.call("SetInfo", {"Entity": u"General",
                                               "Key": u"VibraActive",
                                               "SystemData": {"Status": 1}})

    def test_getinfo(self):
        """ Get system information"""
        itr = self.sysinfo_handle.call("GetInfo", {"Entity": u"General",
                                               "Key": u"VibraActive",
                                               "SystemData": {"Status": 1}})


class AsynchronousSysInfoTest(unittest.TestCase):

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
        service_handle = scriptext.load('Service.SysInfo', 'ISysInfo')
        return service_handle

    def test_cancel_request(self):
        """Cancel an outstanding request"""

        def print_location_area(trans_id, event_id, output_params):
            if sysinfo_trans_id == trans_id:
                if event_id == scriptext.EventCanceled:
                    print "Operation Canceled"
                else:
                    print "Event_id was not scriptext.EventCanceled"
            else:
                print "Invalid transaction ID received"
            self.check_error_and_signal(output_params)

        # Make a request to query the required information
        sysinfo_handle = self.do_load()
        sysinfo_trans_id = sysinfo_handle.call("GetInfo",
                                              {"Entity": u"Network",
                                               "Key": u"LocationArea"},
                                                callback=print_location_area)
        try:
            sysinfo_handle.call('Cancel', {'TransactionID': sysinfo_trans_id})
        except scriptext.ScriptextError, err:
            print "Error canceling request ", err


def test_main():
    test.test_support.run_unittest(SynchronousSysInfoTest,
                                   AsynchronousSysInfoTest)


if __name__ == "__main__":
    test_main()
