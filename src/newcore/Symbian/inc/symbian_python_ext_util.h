/* Copyright (c) 2005-2009 Nokia Corporation
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

/*
 *  symbian_python_ext_util.h
 *
 *  Utilities for Symbian OS specific Python extensions.
 */

#ifndef __SPY_EXT_UTIL_H
#define __SPY_EXT_UTIL_H

#include "Python.h"
#include <e32math.h>
#include <e32std.h>
#include <datetime.h>
#include <tz.h>

#define KErrPython (-50)
#define PyDateTime_IMPORT \
        PyDateTimeAPI = (PyDateTime_CAPI*) PyCObject_Import("datetime", \
                                                            "datetime_CAPI")
#define PyDateTime_FromDateAndTime(year, month, day, hour, min, sec, usec) \
	      PyDateTimeAPI->DateTime_FromDateAndTime(year, month, day, hour, \
		    min, sec, usec, Py_None, PyDateTimeAPI->DateTimeType)
_LIT(KUnixEpoch, "19700000:");

#ifdef __cplusplus
extern "C" {
#endif
  DL_IMPORT(PyObject*) SPyErr_SymbianOSErrAsString(int err);
  DL_IMPORT(PyObject*) SPyErr_SetFromSymbianOSErr(int);
  DL_IMPORT(int) SPyAddGlobal(PyObject *, PyObject *);
  DL_IMPORT(int) SPyAddGlobalString(char *, PyObject *);
  DL_IMPORT(PyObject*) SPyGetGlobal(PyObject *);
  DL_IMPORT(PyObject*) SPyGetGlobalString(char *);
  DL_IMPORT(void) SPyRemoveGlobal(PyObject *);
  DL_IMPORT(void) SPyRemoveGlobalString(char *);

  DL_IMPORT(TReal) epoch_as_TReal(void);
  DL_IMPORT(TReal) time_as_UTC_TReal(const TTime&);
  DL_IMPORT(void) pythonRealAsTTime(TReal timeValue, TTime&);
  DL_IMPORT(PyObject *) ttimeAsPythonFloat(const TTime&);
  PyAPI_FUNC(TInt64) epoc_to_unix_time(TTime);
  PyAPI_FUNC(PyObject *) epoch_to_datetime(TTime, TBool convert_to_local=true);
  PyAPI_FUNC(TTime) datetime_to_epoch(PyObject *);

#ifdef __cplusplus
}
#endif
#define RETURN_ERROR_OR_PYNONE(error) \
if (error != KErrNone)\
  return SPyErr_SetFromSymbianOSErr(error);\
else {\
  Py_INCREF(Py_None);\
  return Py_None;\
}

#endif /* __SPY_EXT_UTIL_H */
