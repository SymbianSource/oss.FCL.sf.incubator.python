# Copyright (c) 2008 Nokia Corporation
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
import random
import e32

sync_error_message = {
  "invalid_key": "(1002, 'Contacts : Add : Invalid Field Key : NickName')",
  "id_missing": "(1003, 'Contacts : Delete : List of Ids is missing')",
  "invalid_cmd": "(1004, 'Contacts : Requested command not supported')"}

async_error_message = {
  "invalid_callback": "callable expected",
  "async_on_sync": "(1002, 'SysInfo: SetInfo: ASync Version Not Supported')",
  "invalid_input": "(1003, 'SysInfo: GetInfo: Entity: Input Parameter " +
                   "Missing')",
  "sync_on_async": "(1012, 'SysInfo: GetInfo: ')"}


class SynchronousScriptextCallsTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.scriptexthandle = None
        self.list_of_contactIDs = []
        # Load the service
        self.scriptexthandle = scriptext.load('Service.Contact', 'IDataSource')

    def contactlist(self):
        """Get the contactIds in a list"""
        list_val = self.scriptexthandle.call('GetList',
                                                    {'Type': u'Contact'})
        # iterate for the label 'id and append to list
        for i in list_val:
            cnt_id = i['id']
            self.list_of_contactIDs.append(cnt_id)

        return list_val

    def get_contactmap(self, firstname, lastname, phone):
        # Helper function that returns a map which can be used to add contact
        # currently only firstname, lastname, phone num are supported
        return {'FirstName': {'Label': u'first name', 'Value': firstname},
                'LastName': {'Label': u'last name', 'Value': lastname},
                'MobilePhoneGen': {'Label': u'mobile', 'Value': phone}}

    def test_addcontact(self):
        """Add a contact to phonebook"""
        self.scriptexthandle.call('Add', {'Type': u'Contact',
                 'Data': self.get_contactmap(u'Mark', u'Benson', u'123456')})

        itr = self.scriptexthandle.call('GetList',
              {'Type': u'Contact', 'Filter': {'SearchVal': u'Mark'}})

        found_test_contact = False
        for i in itr:
            ct = i['FirstName']
            test_firstname = ct['Value']

            ct = i['LastName']
            test_lastname = ct['Value']

            if test_firstname == u'Mark' and test_lastname == u'Benson':
                found_test_contact = True

        if not found_test_contact:
            self.fail("Could not find the added contact")

    def test_removecontacts(self):
        """Deleting all contacts in DB"""
        try:
            self.contactlist()
            self.scriptexthandle.call('Delete', {'Type': u'Contact',
                                   'Data': {'DBUri': u'cntdb://c:contacts.cdb',
                                   'CntIdList': self.list_of_contactIDs}})

            # When the contacts' is empty, GetList fails with error code 1012
            list_val = self.scriptexthandle.call('GetList',
                                                     {'Type': u'Contact'})
        except Exception, err:
            self.failUnlessEqual(sync_error_message["id_missing"], str(err))
        else:
            # Exception not raised implies that
            # deleting all contacts was not successful
            self.fail("All contact delete failed")

    def test_keys(self):
        """Check the contact labels"""
        #request the getlist and then iterate from the start
        contact_list = self.contactlist()
        for i in contact_list:
            len_len = len(i)
            # The Map is expected to have four items
            # contactid, first name, last name, phone num
            if len_len != 4:
                self.fail("Contact map length expected to be 4")

            if 'id' not in i:
                self.fail("map iter does not contain the key - 'id'")

    def test_multi_loadservices(self):
        """Consecutive loading of the service"""
        self.scriptexthandle = scriptext.load('Service.Contact', 'IDataSource')
        self.scriptexthandle = scriptext.load('Service.Contact', 'IDataSource')

    def test_err_requestservice_label(self):
        """Trying to request a service with illegal Label"""
        try:
            # Test with label `NickName` which is not defined
            # expected to raise SErrServiceNotSupported
            self.scriptexthandle.call('Add', {'Type': u'Contact',
                 'Data': {'NickName': {'Label': u'firstname',
                 'Value': u'Anand'}}})
        except Exception, err:
            self.failUnlessEqual(sync_error_message["invalid_key"], str(err))

    def test_err_requestservice_unsupported(self):
        """Trying to request an unsupported service"""
        try:
            # Test with command `Send` which is not defined in Contact
            # expected to raise SErrServiceNotSupported
            self.scriptexthandle.call('Send', {'Type': u'Contact',
                 'Data': {'FirstName': {'Label': u'firstname',
                 'Value': u'Anand'}}})
        except Exception, err:
            self.failUnlessEqual(sync_error_message["invalid_cmd"], str(err))

    def test_err_loadservice(self):
        """ Trying to load an unsupported Service"""
        try:
            self.scriptexthandle = scriptext.load('Service.Unsupported',
                                              'Interface')
        except Exception, err:
            self.failUnlessEqual(
            "(-5, 'error attaching requested services')", str(err))


# Added mapping here as interface names are not consistent
# Retained services not used in the testcase as well for future use
service_map = {'messaging': ['Service.Messaging', 'IMessaging'],
               'contacts': ['Service.Contact', 'IDataSource'],
               'calendar': ['Service.Calendar', 'IDataSource'],
               'logging': ['Service.Logging', 'IDataSource'],
               'sysinfo': ['Service.SysInfo', 'ISysInfo']}


class AsynchronousScriptextCallsTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.lock = e32.Ao_lock()
        self.timer = e32.Ao_timer()

    def setUp(self):
        self.async_request_failed = False
        self.output_params = {}

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

    def do_load(self, generic_service_name):
        service_handle = scriptext.load(service_map[generic_service_name][0],
                                          service_map[generic_service_name][1])
        return service_handle

    def test_cancel_request(self):
        """ Test cancelling of an asynchronous request"""

        def log_callback(trans_id, event_id, output_params):
            if trans_id == log_getlist_trans_id:
                if event_id != scriptext.EventCanceled:
                    output_params['TestFailureReason'] = "Async callback " + \
                                                "hit before cancel was called"
            else:
                output_params['TestFailureReason'] = "Invalid transaction " + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        logging_object = self.do_load("logging")

        def add_log_entries(no_of_entries):
            global log_id
            log_id = {}
            while no_of_entries > 0:
                no_of_entries -= 1
                event_type = random.randint(0, 4)
                direction = random.randint(0, 6)
                phone_number = random.randint(1, 10000000)
                log_id[no_of_entries] = logging_object.call("Add",
                                         {"Type": u"Log", "Item":
                                         {"EventType": event_type,
                                         "Direction": direction,
                                       "PhoneNumber": unicode(phone_number)}})

        # Adding lots of entries so that 'GetList' takes a lot of time and
        # which makes it easier to test 'Cancel'
        add_log_entries(100)
        log_getlist_trans_id = logging_object.call("GetList",
                                    {"Type": u"Log"}, callback=log_callback)
        logging_object.call("Cancel",
                                       {"TransactionID": log_getlist_trans_id})

        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)
        # Delete all the entries added
        for x in range(100):
            logging_object.call("Delete",
                                        {"Type": u"Log", "Data":
                                        {"id": log_id[x]}})

    def test_string_and_no_return_value(self):
        """ Test return value types from async request  - No return value in
            output params and string return value
        """

        def log_delete_callback(trans_id, event_id, output_params):
            if trans_id == log_delete_trans_id:
                if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "'event_id' " + \
                        "was not EventCompleted"
                elif "ReturnValue" in output_params:
                    output_params['TestFailureReason'] = "output_params of" + \
                                   " callback function had 'ReturnValue' key"
            else:
                output_params['TestFailureReason'] = "Invalid transaction " + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        def log_add_callback(trans_id, event_id, output_params):
            if trans_id == log_add_trans_id:
                if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "'event_id' " + \
                        "was not EventCompleted"
                elif not isinstance(output_params["ReturnValue"], unicode):
                    output_params['TestFailureReason'] = "'ReturnValue' " + \
                        "was not a string"
            else:
                output_params['TestFailureReason'] = "Invalid transaction " + \
                                                    "ID received"
            self.check_error_and_signal(output_params)

        logging_object = self.do_load("logging")
        log_add_trans_id = logging_object.call("Add",
                                    {"Type": u"Log", "Item":
                                    {"EventType": 0,
                                     "Direction": 0,
                                     "PhoneNumber": unicode(123456789)}},
                                     callback=log_add_callback)

        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)
        # Delete the log entry just added. Delete's output params will
        # not have 'ReturnValue'
        log_delete_trans_id = logging_object.call("Delete",
                                {"Type": u"Log", "Data":
                                {"id": self.output_params["ReturnValue"]}},
                                callback=log_delete_callback)
        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)

    def test_map_return_value(self):
        """ Test scriptext.ScriptextMapWrapper return value type
            from async request.
        """

        def sysinfo_callback(trans_id, event_id, output_params):
            if trans_id == sysinfo_trans_id:
                if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "'event_id' " + \
                        "was not EventCompleted"
                elif (0 > int(output_params['ReturnValue']['Status']) > 100):
                    output_params['TestFailureReason'] = "ReturnValue's " + \
                                 "data was incorrect"
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        sysinfo_object = self.do_load("sysinfo")
        sysinfo_trans_id = sysinfo_object.call("GetInfo",
         {"Entity": u"Battery", "Key": u"BatteryStrength"},
         callback=sysinfo_callback)

        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)

    def test_iterable_return_value(self):
        """ Test Iterable return value type from async request"""

        def log_callback(trans_id, event_id, output_params):
            if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "'event_id' " + \
                        "was not EventCompleted"
            elif trans_id == logging_trans_id:
                for item in output_params["ReturnValue"]:
                    if not isinstance(item, scriptext.ScriptextMapWrapper):
                        output_params['TestFailureReason'] = "ReturnValue " + \
                            "is not an iterable map"
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        logging_object = self.do_load("logging")
        logging_object.call("Add",
                                    {"Type": u"Log", "Item":
                                    {"EventType": 1,
                                     "Direction": 1,
                                     "PhoneNumber": unicode(123456789)}})
        logging_trans_id = logging_object.call("GetList",
                                    {"Type": u"Log"}, callback=log_callback)

        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)

    def test_invalid_callback(self):
        """ Test invalid callback value in request service call """

        sysinfo_list = []
        sysinfo_object = self.do_load("sysinfo")
        try:
            # Passing a list as callback should raise TypeError
            sysinfo_object.call("GetInfo",
                              {"Entity": u"Network", "Key": u"NetworkMode"},
                              callback=sysinfo_list)
        except TypeError, err:
            self.failUnlessEqual(async_error_message['invalid_callback'],
                                 str(err))

    def test_async_request_on_sync_api(self):
        """ Test asynchronous request on an API that supports only
            synchronous requests
        """

        def sysinfo_callback(trans_id, event_id, output_params):
            pass

        sysinfo_object = self.do_load("sysinfo")
        try:
            # 'SetInfo' supports only synchronous requests
            sysinfo_object.call("SetInfo",
                              {"Entity": u"General", "Key": u"VibraActive",
                              "SystemData": {"Status": u"1"}},
                              callback=sysinfo_callback)
        except scriptext.ScriptextError, err:
            self.failUnlessEqual(async_error_message['async_on_sync'],
                                 str(err))

    def test_sync_on_async_api(self):
        """ Test synchronous request on an API that supports only
            asynchronous requests
        """

        sysinfo_object = self.do_load("sysinfo")
        try:
            # GetInfo on Battery's BatteryStrength supports only Async requests
            sysinfo_trans_id = sysinfo_object.call("GetInfo",
                            {"Entity": u"Battery", "Key": u"BatteryStrength"})
        except scriptext.ScriptextError, err:
            self.failUnlessEqual(async_error_message['sync_on_async'],
                                 str(err))

    def test_invalid_input_params(self):
        """ Test async request with invalid input parameters """

        def sysinfo_callback(trans_id, event_id, output_params):
            pass

        sysinfo_object = self.do_load("sysinfo")
        try:
            # There is no input parameter Type "Ent" for "GetInfo" call
            sysinfo_object.call("GetInfo",
                              {"Ent": u"General", "Key": u"NetworkMode"},
                              callback=sysinfo_callback)
        except scriptext.ScriptextError, err:
            self.failUnlessEqual(async_error_message['invalid_input'],
                                 str(err))


def test_main():
    test.test_support.run_unittest(SynchronousScriptextCallsTest,
                                   AsynchronousScriptextCallsTest)

if __name__ == "__main__":
    test_main()
