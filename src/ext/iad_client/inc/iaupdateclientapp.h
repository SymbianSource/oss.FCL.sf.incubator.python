/* Copyright (c) 2009 Nokia Corporation
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

#ifndef IAUPDATECLIENTAPP_H_
#define IAUPDATECLIENTAPP_H_

#include <f32file.h>
#include <iaupdate.h>
#include <iaupdateobserver.h>
#include <iaupdateparameters.h>
#include <iaupdateresult.h>

NONSHARABLE_CLASS(CIAUpdateClientApp) : public CActive, public MIAUpdateObserver
{
public:
    CIAUpdateClientApp():CActive(CActive::EPriorityStandard){;}
    static CIAUpdateClientApp* NewL();
    void ConstructL();
    ~CIAUpdateClientApp();
    void RunL(){;}
    void DoCancel(){;}
public: // MIAUpdateObserve
    void CheckUpdates();
    virtual void CheckUpdatesComplete(TInt aErrorCode, TInt aAvailableUpdates);
    virtual void UpdateComplete(TInt aErrorCode,
                                CIAUpdateResult* aResultDetails);
    void UpdateQueryComplete(TInt aErrorCode, TBool aUpdateNow){;}
private:
    CIAUpdate* iUpdate;
    CIAUpdateParameters* iParameters;
    CActiveSchedulerWait iWait;
    TBool forcefulUpdate;
};

IMPORT_C void IADClientUpdate();

#endif /*IAUPDATECLIENTAPP_H_*/
