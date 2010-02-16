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


class SynchronousAppManagerCallsTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.scriptexthandle = None
        # Load the service
        self.scriptexthandle = scriptext.load('Service.AppManager',
                                              'IAppManager')

    def test_applist(self):
        """Get the list of Applications on the Phone"""
        list_val = self.scriptexthandle.call('GetList',
                   {'Type': u'Application', })


def test_main():
    test.test_support.run_unittest(SynchronousAppManagerCallsTest)

if __name__ == "__main__":
    test_main()
