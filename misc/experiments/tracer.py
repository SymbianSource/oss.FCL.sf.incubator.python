################################################################################
# Copyright (c) 2010 Nokia Corporation
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
################################################################################

# From http://www.dalkescientific.com/writings/diary/archive/2005/04/20/tracing_python_code.html
import sys
import linecache
import random

def traceit(frame, event, arg):
    if event == "line":
        lineno = frame.f_lineno
        filename = frame.f_globals.get("__file__", "<nofilename>")
        if filename == "<stdin>":
            filename = "traceit.py"
        if (filename.endswith(".pyc") or
            filename.endswith(".pyo")):
            filename = filename[:-1]
        name = frame.f_globals.get("__name__", "<noname>")
        line = linecache.getline(filename, lineno)
        # Modify the name below to trace only a particular .py file
        if name in ['httplib']:
            print "%s:%s: %s" % (name, lineno, line.rstrip())
    return traceit
