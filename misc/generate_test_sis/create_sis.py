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

# usage :create_sis.py <number of sis files to be merged in one instance>

import sys
import os
import glob


def create_sis_files():
    tests = open('tests_list.txt', 'r').read().split('\n')
    tests_exe_f = open('tests_exe.txt', 'w')
    uid = 0xe0000000
    testcase_dir = "."
    for test in tests:
        if test:
            test = test + '.py'
            test_file = os.path.join(testcase_dir, test)
            uid += 1
            try:
                os.system('python ensymble.py py2sis %s --heapsize=100K,16M '
                          '--sourcecode --profile=console --uid 0x%x' %
                          (test_file, uid))
                app = os.path.splitext(os.path.basename(test_file))[0]
                tests_exe_f.write('%s_0x%x\n' % (app, uid))
            except Exception, e:
                print e


def create_merged_sis():
    sis_files = glob.glob('*.sis')
    start = 0
    try:
        sis_count = int(sys.argv[1])
    except:
        sis_count = 10
    end = start + sis_count

    while(start < len(sis_files)):
        sis_files_list = ' '
        for a in range(start, min(end, len(sis_files))):
            sis_files_list += ' ' + sis_files[a]

        os.system('python ensymble.py py2sis run_test.py --profile=console')
        os.system('python ensymble.py mergesis run_test_v1_0_0.sis ' +
                  sis_files_list + ' run_test_' +  str(start) + '.sis')
        start = end
        end += sis_count


if __name__ == "__main__":
    create_sis_files()
    create_merged_sis()
