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


class SynchronousMessagingTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.messaging_handle = None
        self.messaging_handle = scriptext.load('Service.Messaging',
                                                               'IMessaging')

#    def test_sendmessage(self):
#        """Send SMS to the number specified"""
#        try:
#            self.messaging_handle.call('Send', {'MessageType': u'SMS',
#                                              'To': u'9741497390',
#                                              'BodyText': u'Hi'})
#        except:
#            print "Error Sending SMS"

    def test_invalid_requestservice(self):
        """Trying to request a service with illegal Label"""
        try:
            # Test with label `ToNumber` which is not defined
            # expected to raise SErrServiceNotSupported
            self.messaging_handle.call('Send', {'MessageType': u'SMS',
                                              'ToNumber': u'12345678',
                                              'BodyText': u'Hi'})
        except:
            print "Invalid Label"

    def test_getlist_inbox(self):
        """Iterate through inbox and print the SMS 'Sender' IDs"""
        try:
            sms_iter = self.messaging_handle.call('GetList',
                                                       {'Type': u'Inbox'})
        except:
            print "Error doing getlist"

    def test_requestservice_unsupported(self):
        """Trying to request an unsupported service"""
        try:
            # Test with command `SendSMS` which is not defined in Contact
            # expected to raise SErrServiceNotSupported
            self.messaging_handle.call('SendSMS', {'MessageType': u'SMS',
                                              'ToNumber': u'12345678',
                                              'BodyText': u'Hi'})
        except:
            print "Invalid request service"

    def test_delete_sms(self):
        """Delete an SMS"""
        try:
            self.messaging_handle.call('Delete',
                                 {'MessageId': u'123'})
        except:
            print "Error deleting SMS :"

    def test_change_status(self):
        """Set SMS message status as Unread"""
        try:
            self.messaging_handle.call('ChangeStatus',
                                 {'MessageId': id_list[message_index],
                                  'Status': u'Unread'})
        except:
            print "Error setting message status to Unread"


class AsynchronousMessagingTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.lock = e32.Ao_lock()
        self.timer = e32.Ao_timer()

    def do_load(self):
        service_handle = scriptext.load('Service.Messaging', 'IMessaging')
        return service_handle

    def test_cancel_request(self):
        """ Test cancelling of an asynchronous request"""

        def sms_send_callback(trans_id, event_id, output_params):
            if sms_trans_id == trans_id:
                if event_id == scriptext.EventCanceled:
                    print "SMS Send Canceled"
                else:
                    print "Event_id was not scriptext.EventCanceled"
            else:
                print "Invalid transaction ID received"
            self.lock.signal()

        messaging_handle = self.do_load()
        # Adding lots of entries so that 'GetList' takes a lot of time and
        # which makes it easier to test 'Cancel'
        try:
            sms_trans_id = messaging_handle.call('Send', {
                                              'MessageType': u'SMS',
                                              'To': u'12345678',
                                              'BodyText': u'Hi'},
                                              callback=sms_send_callback)

            messaging_handle.call("Cancel",
                                       {"TransactionID": sms_trans_id})

            self.lock.wait()
        except:
            print "Error cancelling request"


def test_main():
    test.test_support.run_unittest(SynchronousMessagingTest)

if __name__ == "__main__":
    test_main()
