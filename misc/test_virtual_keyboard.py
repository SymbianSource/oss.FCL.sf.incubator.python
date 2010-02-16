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
#
"""

    This piece of code tests for the popping up of virtual keyboard wherever
    applicable on a touch device, when PyS60 functionality is accessed.
    The modules covered for testing are appuifw, globalui, key_codes and
    btsocket.
"""

import appuifw
import globalui
import e32
import key_codes
import keycapture
import btsocket
import socket
import time

teams = [u'Team A', u'Team B', u'Team C', u'Team D']
team_members = [u"John", u"Harry", u"Joe", u"Tom", u"Evan",
                u"Mary"]
choice_list = [u"Good", u"Bad", u"Ugly"]
text_to_show = u"Testing in progress.."
note_type = ["error", "warn", "info", "confirm", "charging", "wait",
                 "not_charging", "battery_low", "recharge_battery"]


def query_func():
    # This function accepts different types of input from the user
    appuifw.query(u"Your designation :", "text")
    appuifw.query(u"SSN", "number")
    appuifw.query(u"DOB", "date")
    appuifw.query(u"Time of the day:", "time")
    appuifw.query(u"Your password:", "code")
    appuifw.query(u"Still wanna continue", "query")


def test_appuifw():
    """ Call different api's of appuifw like query, multi_query,
        selection_list, multi_selection_list, popup_menu and check if these
        respond to user input appropriately.

    """
    first, last = appuifw.multi_query(u"First Name", u"Last Name")
    appuifw.note(u"Enter these fields to proceed, " + first, "info")
    query_func()
    selected_team = appuifw.selection_list(choices=teams, search_field=1)
    if selected_team == 1:
        appuifw.note(u"Nice team to be in", "info")
        team_members_list = appuifw.multi_selection_list(team_members,
                            style='checkbox', search_field=1)
        appuifw.note(u"Lets verify it again", "info")
        team_members_list = appuifw.multi_selection_list(team_members,
                            style='checkmark', search_field=1)
        appuifw.note(u"Verification Done", "conf")
    option = appuifw.popup_menu(choice_list, u"How was the experience?")
    if option == 0:
        appuifw.note(u"Thank You", "info")
    else:
        appuifw.note(u"Loads to improve on!!", "error")


def test_globalui():
    """ Call global_query, global_note, global_msg_query and global_popup_menu
        of globalui module and test for their response to key press.

    """
    i = 0
    for i in note_type:
        globalui.global_note(text_to_show, i)
    time.sleep(20)
    result = globalui.global_query(u"Do you want to continue?")
    if result == 1:
        globalui.global_note(u"Pressed yes")
    else:
        globalui.global_note(u"Pressed no")
    time.sleep(2)
    result = globalui.global_msg_query(u"i am global message", u"MyHeader")
    result = globalui.global_popup_menu([u"Good", u"Better", u"Best"])
    print "Selected item is: " + str(result)


def test_socket():
    """ Tests the btsocket module for selection of access point and displays
        the selected value. Also checks if a device can be selected to connect
        via bluetooth.

    """
    options = [u"discover", u"select_access_point"]
    menu_index = appuifw.popup_menu(options, u"Select")
    if menu_index == 0:
        btsocket.bt_discover()
    else:
        access_point_id = btsocket.select_access_point()
        for access_point in btsocket.access_points():
            if access_point['iapid'] == access_point_id:
                appuifw.note(u"The access point selected is: " + \
                unicode(access_point['name']))
                break


def test_key_codes():
    """ Test for various key codes associated with keys of a particular device.
        The codes for the respective keys are provided in the key_codes module.

    """

    def up():
        appuifw.note(u"Arrow up was pressed")

    def two():
        appuifw.note(u"Key 2 was pressed")

    def yes():
        appuifw.note(u"Call key is pressed")

    def no():
        appuifw.note(u"Call end")

    def menu():
        appuifw.note(u"Menu key")

    canvas = appuifw.Canvas()
    appuifw.app.body = canvas
    canvas.text((0, 24), u'These keys are being tested for press :')
    canvas.text((0, 48), u'Up, Yes, No, Menu, Key2')
    canvas.bind(key_codes.EKeyUpArrow, up)
    canvas.bind(key_codes.EKey2, two)
    canvas.bind(key_codes.EKeyMenu, menu)
    canvas.bind(key_codes.EKeyYes, yes)
    canvas.bind(key_codes.EKeyNo, no)


def test_keycapture():
    """ Returns key codes of the keys pressed on devices"""

    def quit():
        appuifw.app.exit_key_handler = None
        script_lock.signal()
        capturer.stop()

    def cb_capture(key):
        appuifw.note(u'Key code of last key press :' + unicode(capturer.last_key()))

    script_lock = e32.Ao_lock()
    appuifw.app.exit_key_handler = quit
    capturer = keycapture.KeyCapturer(cb_capture)
    capturer.keys = (keycapture._find_all_keys())
    capturer.start()
    script_lock.wait()


if __name__ == "__main__":
    lock = e32.Ao_lock()
    appuifw.app.menu = [
    (u'test appuifw', test_appuifw),
    (u'test globalui', test_globalui),
    (u'test btsocket', test_socket),
    (u'test key_codes', test_key_codes),
    (u'test_keycapture', test_keycapture),
    (u'Exit', lock.signal)]

    def exit_handler():
        lock.signal()

    appuifw.app.exit_key_handler = exit_handler
    lock.wait()
