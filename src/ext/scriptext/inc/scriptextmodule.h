/* Copyright (c) 2008 - 2009 Nokia Corporation
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

#ifndef SCRIPTEXTMODULE_H_
#define SCRIPTEXTMODULE_H_

#include <e32base.h>
#include <e32cons.h>
#include <e32hashtab.h>
#include <string.h>

#include <liwvariant.h>
#include <liwservicehandler.h>
#include <liwgenericparam.h>
#include <LiwVariantType.hrh>

#include <RTSecManager.h>
#include <RTSecMgrUtility.h>
#include <RTSecMgrScriptSession.h>
#include <RTSecMgrCommonDef.h>
#include "serviceerrno.h"
#include "symbian_python_ext_util.h"
#include <Python.h>

_LIT8(KErrCode, "ErrorCode");
_LIT8(KErrMessage, "ErrorMessage");
_LIT8(KReturnValue, "ReturnValue");
_LIT8(KTransactionID, "TransactionID");
_LIT8(KLiwCancelCmd, "Cancel");

#define ERROR_CODE "ErrorCode"
#define ERROR_MSG  "ErrorMessage"
#define RETURN_VAL "ReturnValue"

class CPyPromptHandler : public MSecMgrPromptHandler
{      
    public:
    TInt Prompt(RPromptDataList& aPromptDataList , TExecutableID /*aExecID  = KAnonymousScript*/)
    {
        for(TInt i(0);i!=aPromptDataList.Count();++i)            
            aPromptDataList[i]->SetUserSelection(RTUserPrompt_OneShot);                
        return EPromptOk;
    }
        
    void SetPromptOption(TSecMgrPromptUIOption aPromptUiOption)
    {    
    }
              
    TSecMgrPromptUIOption PromptOption() const
    {
        return RTPROMPTUI_DEFAULT;
    }
    
};

class CLiwCallback : public MLiwNotifyCallback
{
public:   
    static CLiwCallback* NewL();
    void ConstructL();
    void RegisterCallbackL(TInt, PyObject *);
    TInt HandleNotifyL(TInt, TInt, CLiwGenericParamList&, const CLiwGenericParamList&);
    void Reset();
    ~CLiwCallback();

private:
    PyObject *iPy_callback;
    RHashMap <TInt, PyObject*> *iCallbackRegister;
    CLiwCallback();
    PyObject* GetRegisteredCallbackL(TInt);
    TInt UnregisterCallback(TInt);
};
#endif /*SCRIPTEXTMODULE_H_*/
