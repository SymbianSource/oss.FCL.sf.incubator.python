#!/usr/bin/env python

################################################################################
# Copyright (c) 2007 Nokia Corporation
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

import os
import os.path
import sys

topdir=os.getcwd()

sys.path.append(os.path.join(topdir,'my_lib'))
import my_lib.fact

def factorial (fact_num):
	fact_val = my_lib.fact.fact (fact_num)
	print 'The factorial of %s = %s' %(fact_num, fact_val)
