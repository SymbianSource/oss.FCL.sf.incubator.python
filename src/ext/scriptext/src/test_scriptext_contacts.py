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

sync_error_message = {
  "invalid_key": "(1002, 'Contacts : Add : Invalid Field Key : NickName')",
  "id_missing": "(1003, 'Contacts : Delete : List of Ids is missing')",
  "invalid_cmd": "(1004, 'Contacts : Requested command not supported')"}


class SynchronousScriptextCallsTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.contacts_handle = None
        self.list_of_contactIDs = []
        # Load the service
        self.contacts_handle = scriptext.load('Service.Contact', 'IDataSource')

    def contactlist(self):
        """Get the contactIds in a list"""
        list_val = self.contacts_handle.call('GetList',
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
        self.contacts_handle.call('Add', {'Type': u'Contact',
                 'Data': self.get_contactmap(u'Mark', u'Benson', u'123456')})

        itr = self.contacts_handle.call('GetList',
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
            self.contacts_handle.call('Delete', {'Type': u'Contact',
                                   'Data': {'DBUri': u'cntdb://c:contacts.cdb',
                                   'CntIdList': self.list_of_contactIDs}})

            # When the contacts' is empty, GetList fails with error code 1012
            list_val = self.contacts_handle.call('GetList',
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
        self.contacts_handle = scriptext.load('Service.Contact', 'IDataSource')
        self.contacts_handle = scriptext.load('Service.Contact', 'IDataSource')

    def test_err_requestservice_label(self):
        """Trying to request a service with illegal Label"""
        try:
            # Test with label `NickName` which is not defined
            # expected to raise SErrServiceNotSupported
            self.contacts_handle.call('Add', {'Type': u'Contact',
                 'Data': {'NickName': {'Label': u'firstname',
                 'Value': u'Anand'}}})
        except Exception, err:
            self.failUnlessEqual(sync_error_message["invalid_key"], str(err))

    def test_err_requestservice_unsupported(self):
        """Trying to request an unsupported service"""
        try:
            # Test with command `Send` which is not defined in Contact
            # expected to raise SErrServiceNotSupported
            self.contacts_handle.call('Add', {'Type': u'Contact',
                 'Data': {'FirstName': {'Label': u'firstname',
                 'Value': u'Anand'}}})
        except Exception, err:
            self.failUnlessEqual(sync_error_message["invalid_cmd"], str(err))

    def test_err_loadservice(self):
        """ Trying to load an unsupported Service"""
        try:
            self.contacts_handle = scriptext.load('Service.Unsupported',
                                              'Interface')
        except Exception, err:
            self.failUnlessEqual(
            "(-5, 'error attaching requested services')", str(err))


class AsynchronousScriptextCallsTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.lock = e32.Ao_lock()
        self.timer = e32.Ao_timer()
        #self.signal = e32.Ao_signal()
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
        service_handle = scriptext.load('Service.Contact', 'IDataSource')
        return service_handle

    def test_export_contacts(self):
        """ Export contacts to a file in VCARD format
        """

        def contacts_callback(trans_id, event_id, input_params):
            output_params = {}
            if trans_id == contacts_id:
                if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "Error code: ",\
                                  str(input_params["ReturnValue"]["ErrorCode"])
                    if "ErrorMessage" in str(input_params["ReturnValue"]):
                        output_params['TestFailureReason'] += \
                                   input_params["ReturnValue"]["ErrorMessage"]
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        contacts_handle = self.do_load()
        list_contacts = contacts_handle.call('GetList', {'Type': u'Contact',
                                         'Filter': {'SearchVal': u'Mark'}})
        for i in list_contacts:
            req_id = i['id']

        contacts_id = contacts_handle.call('Export', {
                      'Type': u'Contact',
                      'Data': {
                      'DestinationFile': u'c:\\Data\\python\\contactlist.vcf',
                      'id': unicode(req_id)}}, callback=contacts_callback)
        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)

    def test_import_contacts(self):
        """ Test import contacts from a file provided the file is in
        VCARD format.
        """

        def contacts_callback(trans_id, event_id, input_params):
            output_params = {}
            if trans_id == contacts_trans_id:
                if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "Error code: ",\
                                  str(input_params["ReturnValue"]["ErrorCode"])
                    if "ErrorMessage" in str(input_params["ReturnValue"]):
                        output_params['TestFailureReason'] += \
                                   input_params["ReturnValue"]["ErrorMessage"]
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        contacts_handle = self.do_load()
        contacts_trans_id = contacts_handle.call('Import', {
                        'Type': u'Contact',
                        'Data':{'SourceFile': u'c:\\Data\\python\\VCARD.txt'}},
                                 callback=contacts_callback)

        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)

    def test_organise(self):
        """ Organise contacts to associate/disassociate from a group."""

        def contacts_callback(trans_id, event_id, input_params):
            output_params = {}
            if trans_id == contacts_id:
                if event_id != scriptext.EventCompleted:
                    output_params['TestFailureReason'] = "Error code: ",\
                                  str(input_params["ReturnValue"]["ErrorCode"])
                    if "ErrorMessage" in str(input_params["ReturnValue"]):
                        output_params['TestFailureReason'] += \
                                   input_params["ReturnValue"]["ErrorMessage"]
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        contacts_handle = self.do_load()
        contacts_handle.call('Add', {'Type': u'Contact',
                 'Data': self.get_contactmap(u'Mark', u'Benson', u'123456')})

        list_contacts = contacts_handle.call('GetList', {'Type': u'Contact',
                                         'Filter': {'SearchVal': u'Mark'}})
        for i in list_contacts:
            req_id = i['id']
        contacts_handle.call('Add', {'Type': u'Group',
                                     'Data':{'GroupLabel': u'Friends'}})
        list_groups = contacts_handle.call('GetList', {'Type': u'Group'})
        req_groupid = []
        for j in list_groups:
            req_groupid.append(j['id'])

        contacts_id = contacts_handle.call('Organise', {
                        'Type': u'Group',
                        'Data': {'id': unicode(req_groupid[0]),
                   'IdList': [req_id]},
                   'OperationType': u'Associate'}, callback=contacts_callback)

        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)

    def get_contactmap(self, firstname, lastname, phone):
        # Helper function that returns a map which can be used to add contact
        # currently only firstname, lastname, phone num are supported
        return {'FirstName': {'Label': u'first name', 'Value': firstname},
                'LastName': {'Label': u'last name', 'Value': lastname},
                'MobilePhoneGen': {'Label': u'mobile', 'Value': phone}}


def test_main():
    test.test_support.run_unittest(SynchronousScriptextCallsTest,
                                   AsynchronousScriptextCallsTest)

if __name__ == "__main__":
    test_main()
