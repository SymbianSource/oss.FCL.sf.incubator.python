/*     
* Copyright (c) 2008 Nokia Corporation
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
* ====================================================================
*/

#include <stdio.h>

// This is a GCCE toolchain workaround needed when compiling with GCCE
// and using main() entry point
#ifdef __GCCE__
#include <staticlibinit_gcce.h>
#endif


int main(int argc, char *argv[])
{
    FILE *fp = fopen("c:\\data\\python\\test\\start_exe_tempfile.txt", "w");
    fprintf(fp, "%s", argv[1]);
    fclose(fp);
    return 0;
}
