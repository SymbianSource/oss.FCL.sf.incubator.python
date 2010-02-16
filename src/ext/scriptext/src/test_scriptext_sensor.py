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


class SynchronousSensorTest(unittest.TestCase):

    def __init__(self, methodName='runTest'):
        unittest.TestCase.__init__(self, methodName=methodName)
        self.sensor_handle = None
        try:
            self.sensor_handle = scriptext.load('Service.Sensor', 'ISensor')
        except Exception, err:
            self.fail(str(err))

    def test_find_sensor_channel(self):
        """FindSensorChannel"""
        search_criteria = ("AccelerometerAxis", "AccelerometerDoubleTapping",
                           "Orientation", "Rotation")
        for i in search_criteria:
            result = self.sensor_handle.call('FindSensorChannel',
                              {'SearchCriterion': unicode(i)})
            count_items = len(result)
            if count_items == 0:
                self.fail('Could not find sensor channel: ' + i)

    def test_get_channel_property(self):
        """Trying to get the channel property"""
        result = self.sensor_handle.call('FindSensorChannel',
                                   {'SearchCriterion': u'Orientation'})
        channel_property_result = self.sensor_handle.call('GetChannelProperty',
                 {'ChannelInfoMap': {
                   'ChannelId': result[0]['ChannelId'],
                   'ContextType': result[0]['ContextType'],
                   'Quantity': result[0]['Quantity'],
                   'ChannelType': result[0]['ChannelType'],
                   'Location': result[0]['Location'],
                   'VendorId': result[0]['VendorId'],
                   'DataItemSize': result[0]['DataItemSize'],
                   'ChannelDataTypeId': result[0]['ChannelDataTypeId']},
                   'PropertyId': u'DataRate'})
        if len(channel_property_result) != 5:
            self.fail('GetChannelProperty failed')


class AsynchronousSensorTest(unittest.TestCase):

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
        service_handle = scriptext.load('Service.Sensor', 'ISensor')
        return service_handle

    def test_register_notification(self):
        """ Register an asynchronous notification first and then try to
            cancel it"""

        def sensor_callback(trans_id, event_id, input_params):
            output_params = {}
            if sensor_id == trans_id:
                if event_id != scriptext.EventCanceled:
                    if "DataType" not in input_params["ReturnValue"]:
                        ouput_params['TestFailureReason'] = \
                                input_params["ReturnValue"]["ErrorMessage"]
                    sensor_handle.call('Cancel',
                                   {'TransactionID': trans_id})
            else:
                output_params['TestFailureReason'] = "Invalid transaction" + \
                                                     "ID received"
            self.check_error_and_signal(output_params)

        sensor_handle = self.do_load()
        result = sensor_handle.call('FindSensorChannel',
                                   {'SearchCriterion': u'Orientation'})
        sensor_id = sensor_handle.call('RegisterForNotification', {
                  'ListeningType': u'ChannelData',
                  'ChannelInfoMap': {
                  'ChannelId': result[0]['ChannelId'],
                  'ContextType': result[0]['ContextType'],
                  'Quantity': result[0]['Quantity'],
                  'ChannelType': result[0]['ChannelType'],
                  'Location': result[0]['Location'],
                  'VendorId': result[0]['VendorId'],
                  'DataItemSize': result[0]['DataItemSize'],
                  'ChannelDataTypeId': result[0]['ChannelDataTypeId']}},
                                   callback=sensor_callback)


        self.timer.after(30, self.ao_timer_callback)
        self.lock.wait()
        self.failIf(self.async_request_failed, self.output_params)


def test_main():
    test.test_support.run_unittest(SynchronousSensorTest,
                                   AsynchronousSensorTest)

if __name__ == "__main__":
    test_main()
