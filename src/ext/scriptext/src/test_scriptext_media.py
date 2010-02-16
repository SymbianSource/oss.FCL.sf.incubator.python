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


class AsynchronousScriptextCallsTest(unittest.TestCase):

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
        service_handle = scriptext.load('Service.MediaManagement',
                                        'IDataSource')
        return service_handle

    def test_get_list(self):
        """ Get list media applications and cancel
        """

        def media_callback(trans_id, event_id, input_params):
            output_params = {}
            if media_trans_id == trans_id:
                if event_id != scriptext.EventCanceled:
                    print "processing.."
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)
        media_handle = self.do_load()
        media_trans_id = media_handle.call('GetList', {'Type': u'FileInfo',
                                 'Filter': {'FileType': u'Music'},
                                 'Sort': {'Key': u'FileName',
                                          'Order': u'Ascending'}},
                                          callback=media_callback)
        time.sleep(2)
        media_handle.call('Cancel',
                                   {'TransactionID': media_trans_id})
        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)


def test_main():
    test.test_support.run_unittest(AsynchronousScriptextCallsTest)


if __name__ == "__main__":
    test_main()
