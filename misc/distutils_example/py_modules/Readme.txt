

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



This is an example that uses distutils to create a python package with an extension file 

Create an installation file for windows
---------------------------------------

python setup.py bdist_wininst

This creates an installation file under the dist dir.
This file can be used to install the module for windows environment.


Creating a source distribution
------------------------------

python setup.py sdist

This creates a distribution zip file under the dist dir.


Install using distribution file
-------------------------------

python setup.py install