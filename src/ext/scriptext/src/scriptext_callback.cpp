/* Copyright (c) 2008 Nokia Corporation
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


#include "scriptextmodule.h"

using namespace LIW;

PyObject* SPyValue_FromVariant(TLiwVariant &);
PyObject* SPyLiwErr_SetString(char *err_string, int err_no=0);
int GetErrorCode(CLiwGenericParamList &aOutParamList);
PyObject* GetErrorMessage(CLiwGenericParamList &aOutParamList, 
                                                      bool aDefaultMsg=true);

CLiwCallback::CLiwCallback()
{
}

CLiwCallback* CLiwCallback::NewL()
{
    CLiwCallback *callbackHandle = new(ELeave) CLiwCallback();
    CleanupStack::PushL(callbackHandle);
    callbackHandle->ConstructL();
    CleanupStack::Pop(callbackHandle);
    return callbackHandle;
}

void CLiwCallback::ConstructL()
{
    iCallbackRegister = new(ELeave) RHashMap<TInt, PyObject*> ();
}

void CLiwCallback::RegisterCallbackL(TInt aTranId, PyObject *aCallback)
{
    iCallbackRegister->InsertL(aTranId, aCallback);
}

PyObject* CLiwCallback::GetRegisteredCallbackL(TInt aTransId)
{
    return iCallbackRegister->FindL(aTransId);
}

TInt CLiwCallback::UnregisterCallback(TInt aTransId)
{
    return iCallbackRegister->Remove(aTransId);
}

void CLiwCallback::Reset()
{
    PyObject *pyFun;
    THashMapIter <TInt, PyObject*> mapIter(*iCallbackRegister);

    while (pyFun=(PyObject*)mapIter.NextValue())
    {
        Py_DECREF(pyFun);
        mapIter.RemoveCurrent();
    }
}

CLiwCallback::~CLiwCallback()
{
    delete iCallbackRegister;
}

TInt CLiwCallback::HandleNotifyL(TInt aTransId, TInt aEventId,
                       CLiwGenericParamList& aEventParamList,
                       const CLiwGenericParamList& /*aInParamList*/)
{
    PyGILState_STATE gstate = PyGILState_Ensure();

    PyObject *callbackArglist = NULL, *callRet = NULL;
    PyObject *retvalWrapper = NULL;
    TInt err = KErrNone;

    PyObject *retDict = PyDict_New();
    if (!retDict)
    {
        PyErr_NoMemory();
        PyErr_Print();
        PyGILState_Release(gstate);
        return -1;
    }

    err = GetErrorCode(aEventParamList);
    PyDict_SetItemString(retDict, ERROR_CODE, Py_BuildValue("i", err));

    if (err != SErrNone)
    {
        PyObject *errMsg;
        if (errMsg = GetErrorMessage(aEventParamList, false))
            PyDict_SetItemString(retDict, ERROR_MSG, errMsg);
    }

    PyObject *callbackFun = NULL;
    TInt leaveCode = KErrNone;
    TRAP(leaveCode, callbackFun = GetRegisteredCallbackL(aTransId));
    if (leaveCode != KErrNone)
    {
        Py_DECREF(retDict);
        SPyLiwErr_SetString("error fetching the callback function", leaveCode);
        PyErr_Print();
        PyGILState_Release(gstate);
        return leaveCode;
    }
    UnregisterCallback(aTransId);

    TInt pos = 0 ;
    const TLiwGenericParam* retValue = \
                                aEventParamList.FindFirst(pos, KReturnValue);
    if (pos != KErrNotFound)
    {
        TLiwVariant retVal = retValue->Value();
        retvalWrapper = SPyValue_FromVariant(retVal);
        retVal.Reset();
        PyDict_SetItemString(retDict, RETURN_VAL, retvalWrapper);
    }

    callbackArglist = Py_BuildValue("(iiO)", aTransId, aEventId, retDict);
    if (!callbackArglist)
    {
        Py_DECREF(retDict);
        Py_DECREF(callbackFun);
        SPyLiwErr_SetString("error creating argument list for callback");
        PyErr_Print();
        PyGILState_Release(gstate);
        return -1;
    }

    callRet = PyEval_CallObject(callbackFun, callbackArglist);
    Py_DECREF(callbackArglist);
    Py_DECREF(callbackFun);

    if (!callRet)
    {
        if (PyErr_Occurred() == PyExc_OSError) 
        {
            PyObject *type, *value, *traceback;
            PyErr_Fetch(&type, &value, &traceback);
            if (PyInt_Check(value))
                err = PyInt_AS_LONG(value);
            Py_XDECREF(type);
            Py_XDECREF(value);
            Py_XDECREF(traceback);
        }
        else
        {
            PyErr_Print();
            err = -1;
        }
    }
    Py_XDECREF(callRet);
    PyGILState_Release(gstate);

    return err;
}
