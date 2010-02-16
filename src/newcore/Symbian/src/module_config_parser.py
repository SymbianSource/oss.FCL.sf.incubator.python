# Copyright (c) 2008-2009 Nokia Corporation
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

import os
import string
import zipfile
import modulefinder
import template_engine
import fileutil
import test_module_dependency_cfg
from shellutil import *

base_modules_zip = "python25.zip"
repo_modules_zip = "python25_repo.zip"
module_in_path = 'modulename_in.txt'

comment = r"""/*This file was generated by module_config_parser.py present in
the newcore\Symbian\src directory.*/
"""

mmp_part1 = r"""
TARGETTYPE    dll

CAPABILITY    ${{DLL_CAPABILITIES}}
${{COMPILER_FLAGS}}
EPOCALLOWDLLDATA

SYSTEMINCLUDE    \epoc32\include\python25
SYSTEMINCLUDE    \epoc32\include\stdapis
SYSTEMINCLUDE    \epoc32\include

// libc and euser are always needed when using main() entry point
LIBRARY python25.lib libc.lib euser.lib
LIBRARY libpthread.lib libdl.lib libm.lib

SOURCEPATH    ..\..

"""
mmp_part2 = r"""

#if defined(ARMCC)
deffile ..\eabi\ 
#elif defined(WINSCW)
deffile ..\bwins\ 
#elif defined(WINS)
deffile ..\bwins\ 
#else
deffile ..\bmarm\ 
#endif
"""


def bldinf_append(modulelist):
    """Appends all the mmp filenames generated for the new PYDs"""
    bldinf = open('..\\group\\bld.inf.in.template', 'r')
    bldinf_new = open('..\\group\\bld.inf.in', 'w')
    for line in bldinf:
        bldinf_new.write(line)
        if '/*PYD MODULE MMP FILES*/' in line:
            break
    for module in modulelist:
        print "Adding:" + module + ".mmp to bld.inf"
        bldinf_new.write(module + '.mmp\n')
    for line in bldinf:
        if '.mmp' not in line:
            bldinf_new.write(line)
    bldinf_new.close()
    bldinf.close()


def pkg_append(modulelist):
    """Adds the pyd files to the Python core package file"""
    pkgfile = open('..\\group\\python25.pkg.in.template', 'r')
    pkgfile_new = open('..\\group\\python25.pkg.in', 'w')
    for line in pkgfile:
        pkgfile_new.write(line)
        if ';PYDs' in line:
            break
    for module in modulelist:
        print "Adding :" + module + ".pyd to python25.pkg.in"
        pkgfile_new.write(
        '"\\Epoc32\\release\\${{DEVICE_PLATFORM}}\\${{DEVICE_BUILD}}\\%s.pyd" \
        -"!:\\sys\\bin\\%s.pyd"' % (module, module) + '\n')
    for line in pkgfile:
        if '.pyd' not in line:
            pkgfile_new.write(line)
    pkgfile_new.close()
    pkgfile.close()


def genmmpfile(modulename, filename):
    """Generates mmp file for each pyd module"""
    print "Creating :" + modulename + ".mmp.in"
    pyd_mmpfile = open('..\\group\\%s.mmp.in' % (modulename), 'w')
    pyd_mmpfile.write(comment)
    pyd_mmpfile.write('TARGET        ' + PREFIX + modulename + '.pyd')
    pyd_mmpfile.write(mmp_part1)
    pyd_mmp_content = string.split(filename, '|')
    for item in pyd_mmp_content:
        pyd_mmpfile.write(item + '\n')
    pyd_mmpfile.write(mmp_part2)
    pyd_mmpfile.close()


config_part3=r"""
    /* This module lives in marshal.c */
    {"marshal", PyMarshal_Init},

    /* These entries are here for sys.builtin_module_names */
    {"__main__", NULL},
    {"__builtin__", NULL},
    {"sys", NULL},
    {"exceptions", NULL},

    /* Sentinel */
    {0, 0}
};


#ifdef __cplusplus
}
#endif
"""

config_part1 = r"""
#include "Python.h"

#ifdef __cplusplus
extern "C" {
#endif

"""

config_part2 = r"""
extern void PyMarshal_Init(void);
"""


def genconfigdotc(modulelist):
    """Generates config.c from the list of built-in modules
    present in modules.cfg"""
    print " Adding modules : ", modulelist, "to config.c"
    configdotc = open('.\\config.c', 'w')
    configdotc.write(comment)
    configdotc.write("\n /* Refer the file 'modules.cfg' for the list of " +
                     "built-in modules */ \n")
    configdotc.write(config_part1)
    configdotc.write(config_part2)
    for module in modulelist:
        configdotc.write("extern void init" + module + "(void);\n")
    configdotc.write("\nstruct _inittab _PyImport_Inittab[] = {\n")
    for module in modulelist:
        configdotc.write('\t{"' + module + '", init' + module + '},\n')
    configdotc.write(config_part3)
    configdotc.close()
    print "Done"


def pythonmmp_append(file_list):
    """Appends the list of source files(built-in modules) to the
    python25 mmp file"""
    print " Adding files :", file_list, " to python25.mmp.in"
    pythonmmp = open('..\\group\\python25.mmp.in.template', 'r')
    pythonmmp_new = open('..\\group\\python25.mmp.in', 'w')
    for line in pythonmmp:
        pythonmmp_new.write(line)
        if '// built-in module - start' in line:
            break
    pythonmmp_new.write("\n")
    for filename in file_list:
        pythonmmp_new.write("SOURCE        " + filename + "\n")
    for line in pythonmmp:
        if '// built-in module - end' in line:
            pythonmmp_new.write("\n" + line)
            break
    for line in pythonmmp:
        flag = 0
        for item in file_list:
            if item in line:
                flag = 1     # Item already exists in the mmp file, don't write
                break
        if flag == 0:
            pythonmmp_new.write(line)
    pythonmmp_new.close()
    pythonmmp.close()
    print "Done"


def generate_pymodules_zip(base_py_module_paths, base_py_module_names,
                                                                    zip_file):
    """ Creates a zip package picking the files from base_py_module_paths
        and placing them as specified in base_py_module_names"""
    py_zip = zipfile.ZipFile(zip_file, "w")
    for py_path, py_file in zip(base_py_module_paths, base_py_module_names):
        # If the file does not exist then try to run template parser on the
        # corresponding .in file.
        if not os.path.exists(py_path + py_file):
            template_engine.process_file(py_path + py_file + '.in', globals())
        pyc_file = py_file + 'c'
        if os.path.exists(py_path + pyc_file):
            py_file = pyc_file
        py_zip.write(py_path + py_file, py_file, zipfile.ZIP_DEFLATED)
        print "Added :", py_file + " to " + zip_file
    py_zip.close()


def generate_module_repo():
    """Create a directory structure to copy standard modules and dev-modules
       along with their respective metadata files
    """

    module_repo_dir = \
        os.path.abspath('..\\..\\..\\tools\\py2sis\\ensymble\\module-repo\\')
    standard_modules_dir = os.path.join(module_repo_dir, 'standard-modules')
    device_binaries_path = os.path.abspath('\\epoc32\\release\\%s\\%s' %
                                           (DEVICE_PLATFORM, DEVICE_BUILD))
    dev_module_dir = os.path.join(module_repo_dir, 'dev-modules')

    for src_path, dest_path in zip(repo_mod_src_path, repo_mod_dest_path):
        src_path = os.path.abspath(src_path)
        dest_path = os.path.join(standard_modules_dir, dest_path)
        copy_file(src_path, dest_path)

    for src_path, dest_path \
        in zip(cfg_data['ext_modules'], cfg_data['ext_module_names']):
        src_path = os.path.abspath(src_path)
        dest_path = os.path.join(dev_module_dir, dest_path)
        copy_file(src_path, dest_path)

    if os.path.exists(module_repo_dir) and \
        os.path.exists(dev_module_dir):
        content = []
        open(os.path.join(dev_module_dir,
            'module_search_path.cfg'), 'w+').write(str(content))

    for mod in cfg_data['std_repo_pyds']:
        if not \
        os.path.exists(os.path.join(standard_modules_dir, mod)):
            copy_file(os.path.join(device_binaries_path, mod),
                os.path.join(standard_modules_dir, mod))

    for i in range(len(cfg_data['ext_mod_cfg_paths'])):
        abs_cfg_path_src = os.path.join(os.path.abspath(
            cfg_data['ext_mod_cfg_paths'][i]), 'module_config.cfg')
        abs_cfg_path_dest = os.path.join(os.path.abspath(
              '..\\..\\..\\tools\\py2sis\\ensymble\\module-repo\\dev-modules'),
                cfg_data['ext_mod_cfg_names'][i], 'module_config.cfg')
        copy_file(abs_cfg_path_src, abs_cfg_path_dest)

    for i in range(len(cfg_data['ext_pyds'])):
        if not os.path.exists(os.path.join(dev_module_dir,
                                           cfg_data['ext_pyd_names'][i])):
            copy_file(os.path.abspath(cfg_data['ext_pyds'][i]),
            os.path.join(dev_module_dir, cfg_data['ext_pyd_names'][i]))


def readconfig_and_generate():
    """It returns a map of lists of py, pyds, builtin,excluded etc
    """
    global dep_map
    pyd_modules = []
    builtin_modules = []
    base_py_module_paths = []
    base_py_module_names = []
    modulename_list = []
    modulename_in_list = []
    mmp_files = []
    configdotc_list = []
    pkgfile_list = []
    std_repo_pys = []
    std_repo_pyds = []
    repo_py_module_names = []
    repo_py_module_paths = []
    repo_pyds = []
    std_base_pys = []
    ext_modules_path = []
    ext_module_names = []
    ext_modules = []
    ext_pyd_names = []
    ext_pyd_path = []
    ext_pyds = []
    ext_mod_cfg_paths = []
    ext_mod_cfg_names = []
    testapp_pkg_files = []
    # This list is maintained so that the ext modules are not part of
    # module-repo\\standard. But are a part of packaging and going with the
    # runtime
    mod_repo_base_excluded_list = []
    mod_repo_excluded_list = []
    template_engine.process_file('modules.cfg.in', globals())
    config_file = open('modules.cfg', 'r')
    for line in config_file:
        line1 = line.rstrip('\n')
        line = line1.strip()
        if line in ['PYD', 'BUILTIN', 'PY_MODULES', 'EXT-MODULES',
                    'EXT-PYD', 'EXT-MOD-CFGS']:
            module_type = line
            continue
        if line and line[0] != '#':
            if module_type == 'PYD':
                pyd_modules.append(line.split(','))
                # Update the type of the pyd to the dep_map
                mod_map = {}
                try:
                    mod_map['type'] = line.split(',')[2]
                except:
                    mod_map['type'] = 'repo'
                mod_map['deps'] = []
                file_name = line.split(',')[0]
                dep_map[file_name] = mod_map

            elif module_type == 'BUILTIN':
                builtin_modules += line.split('=')
                mod_map = {}
                mod_map['type'] = 'base'
                mod_map['deps'] = []
                dep_map[line.split('=')[0]] = mod_map

            elif module_type == 'PY_MODULES':
                module_data = line.split(':')
                try:
                    py_mod_type = module_data[2]
                except:
                    py_mod_type = 'repo'

                # Update the type of the py to the dep_map
                if module_data[1].endswith('.py'):
                    mod_map = {}
                    mod_map['type'] = py_mod_type
                    dep_map[module_data[1].replace('.py',
                    '').replace('\\', '.')] = mod_map

                    if py_mod_type != 'base':
                        repo_py_module_paths.append(module_data[0])
                        repo_py_module_names.append(module_data[1])
                    else:
                        base_py_module_paths.append(module_data[0])
                        base_py_module_names.append(module_data[1])

            elif module_type == 'EXT-MODULES':
                ext_modules_path.append(line.split(':')[0])
                ext_module_names.append(line.split(':')[1])
                try:
                    ext_mod_type = line.split(':')[2]
                except:
                    ext_mod_type = 'repo'
                ext_modules.append(line.split(':')[0] + \
                    os.path.basename(line.split(':')[1]))

                if ext_mod_type != 'base':
                    repo_py_module_paths.append(line.split(':')[0])
                    repo_py_module_names.append(os.path.basename(\
                                                       line.split(':')[1]))
                    mod_repo_excluded_list.append(line.split(':')[0] + \
                                       os.path.basename(line.split(':')[1]))
                else:
                    base_py_module_paths.append(line.split(':')[0])
                    base_py_module_names.append(
                                        os.path.basename(line.split(':')[1]))
                    mod_repo_base_excluded_list.append(line.split(':')[0] + \
                                          os.path.basename(line.split(':')[1]))

            elif module_type == 'EXT-PYD':
                ext_pyd_path.append(line.split(':')[0])
                ext_pyd_names.append(line.split(':')[1])
                ext_pyds.append(line.split(':')[0] + \
                    os.path.basename(line.split(':')[1]))
                try:
                    ext_pyd_type = line.split(':')[2]
                except:
                    ext_pyd_type = 'repo'
                ext_pyd_file = os.path.basename(os.path.splitext(
                                                line.split(':')[1])[0])
                if ext_pyd_type == 'base':
                    pkgfile_list.append(ext_pyd_file)
                else:
                    testapp_pkg_files.append(ext_pyd_file)

            elif module_type == 'EXT-MOD-CFGS':
                ext_mod_cfg_paths.append(line.split(':')[0])
                ext_mod_cfg_names.append(line.split(':')[1])

    for i in range(len(base_py_module_paths)):
        std_repo_pys.append(base_py_module_paths[i] + base_py_module_names[i])
    for i in range(len(repo_py_module_paths)):
        std_base_pys.append(repo_py_module_paths[i] + \
            repo_py_module_names[i])

    # Remove the ext-modules so that they are not part of standard modules
    for mod in mod_repo_excluded_list:
        std_base_pys.remove(mod)
    for mod in mod_repo_base_excluded_list:
        std_repo_pys.remove(mod)

    config_file.close()
    for module in pyd_modules:
        mmp_list = module[1].split('=')[1]
        genmmpfile(module[0], mmp_list.split('"')[1])
        modulename_list.append(module[0])
        std_repo_pyds.append(PREFIX + module[0] + '.pyd')
        modulename_in_list.append(module[0] + '.mmp.in')
        if 'base' in module:
            pkgfile_list.append(PREFIX + module[0])
        else:
            repo_pyds.append(PREFIX + module[0])

    modulename_in = open(module_in_path, 'w')
    for module in modulename_in_list:
        modulename_in.write(os.path.dirname(os.getcwd()) + '\\group\\' +
                            module + '\n')
    for files in fileutil.all_files(os.path.dirname(os.getcwd()),
                                                    '*.template'):
            files = files.rstrip('.template')
            modulename_in.write(files + '\n')
    modulename_in.close()
    bldinf_append(modulename_list)
    pkg_append(pkgfile_list)

    for x in range(0, len(builtin_modules), 2):
        configdotc_list.append(builtin_modules[x])
        mmp_files.append(builtin_modules[x + 1])
    genconfigdotc(configdotc_list)

    return {"mmp_files": mmp_files,
            "base_py_module_paths": base_py_module_paths,
            "base_py_module_names": base_py_module_names,
            "std_repo_pys": std_repo_pys,
            "std_repo_pyds": std_repo_pyds,
            "repo_py_module_paths": repo_py_module_paths,
            "repo_py_module_names": repo_py_module_names,
            "std_base_pys": std_base_pys,
            "repo_pyds": repo_pyds,
            "ext_module_names": ext_module_names,
            "ext_modules": ext_modules,
            "ext_pyds": ext_pyds,
            "ext_pyd_names": ext_pyd_names,
            "ext_mod_cfg_paths": ext_mod_cfg_paths,
            "ext_mod_cfg_names": ext_mod_cfg_names,
            "testapp_pkg_files": testapp_pkg_files}


def get_py_pyd_files(arg, dirname, files):
    global dirname_list
    pyd_list = []
    for f in files:
        entry = os.path.join(dirname, f)
        if f.endswith('.py'):
            arg.append(entry)
        if f.endswith('.pyd'):
            entry = entry.replace(std_module_search_path + '\\', '')
            entry = entry.replace('\\', '.')
            pyd_list.append(entry)
    if os.path.isfile(os.path.join(dirname, '__init__.py')) and \
        dirname not in dirname_list:
        dirname_list.append(dirname)


def find_dep_modules(src):
    # Get the dependency list for each py files passed
    global dep_map
    global mod_type
    unresolved_dep_mods = []
    py_files = []
    dep_mods = []

    if os.path.isdir(src):
        os.path.walk(src, get_py_pyd_files, py_files)
    else:
        py_files.append(src)

    for f in py_files:
        mf = modulefinder.ModuleFinder(path=[std_module_search_path])
        mf.run_script(f)
        mod_list = []
        for mod in mf.modules.iteritems():
            mod_list.append(mod[0])
        for mod in mf.badmodules.iteritems():
            mod_list.append(mod[0])
        mod_list.sort()
        # The dependencies for "directory entries" are taken to be the sum of
        # all the dependencies of the file in that directory
        if src not in dirname_list:
            mod_map = {}
            f = os.path.splitext(f)[0]
            f = f.replace(std_module_search_path + '\\', '')
            f = f.replace('\\', '.')
            mod_map['deps'] = mod_list
            dep_map[f].update(mod_map)
        else:
            dep_mods = list(set(dep_mods + mod_list))

    return dep_mods


def find_std_pyd_deps(arg, dirname, names):
    # Function to get the deps for standard pyd, (.c extension files)
    global dep_map
    standard_deps = []
    pyd_name = None
    pyd_flag = False
    for name in names:
        standard_deps = []
        if name.endswith('.c') or name.endswith('.h') and not name == 'main.c':
            path = os.path.join(dirname, name)
            fp = open(path, 'r')
            std_modname = name.replace('.h', '').replace('.c', '') + '.pyd'
            for line in fp:
                if "Py_InitModule" in line:
                    try:
                        # This splitting gives us the module name, the key for
                        # dep modules of std modules
                        pyd_name = line.split('"')[1]
                        pyd_flag = True
                    except:
                        continue

                if "PyImport_ImportModule" in line:
                    try:
                        pyd_deps = line.split('"')[1]
                        if pyd_deps not in standard_deps:
                            print "Adding deps:", pyd_deps
                            standard_deps.append(pyd_deps)
                    except:
                        continue

                mod_map = {}
                standard_deps.sort()
                mod_map['deps'] = []
                if pyd_name in dep_map and  \
                    dep_map[pyd_name]['type'] != 'excluded':
                    mod_map['type'] = dep_map[pyd_name]['type']
                    mod_map['deps'] = standard_deps
                    dep_map[pyd_name] = mod_map


def clean():
    """Cleans the files generated by module_config_parser. It assumes that the
       working dir is SRC_DIR
    """
    # Read the module files list to be deleted

    if os.path.exists(module_in_path):
        module_name = open(module_in_path, 'r').readlines()
        for files in module_name:
            if os.path.isfile(files.rstrip()):
                delete_file(files.rstrip())
                delete_file(module_in_path)


if __name__ == "__main__" or __name__ == "__builtin__":
    dep_map = {}
    cfg_data = readconfig_and_generate()
    dirname_list = []
    dep_map.update(eval(open('module_dependency.cfg.template', 'r').read()))

    # The MOD_REPO flag is set to true when it is desired
    # to create a module-repo directory structure, that includes the std_mod,
    # ext_mod, mod_dep_cfg files etc
    if not MOD_REPO:
        pythonmmp_append(cfg_data['mmp_files'])
        generate_pymodules_zip(cfg_data['base_py_module_paths'],
                               cfg_data['base_py_module_names'],
                               base_modules_zip)
        generate_pymodules_zip(cfg_data['repo_py_module_paths'],
                               cfg_data['repo_py_module_names'],
                               repo_modules_zip)
    else:
        print "Generate the Module Repo directory structure"
        repo_mod_src_path = cfg_data['std_repo_pys'] + cfg_data['std_base_pys']
        extn_mod_repo = \
            cfg_data['base_py_module_names'][(len(cfg_data['std_repo_pys'])):]
        extn_mod_base = \
            cfg_data['repo_py_module_names'][(len(cfg_data['std_base_pys'])):]
        for mod in extn_mod_repo:
            cfg_data['base_py_module_names'].remove(mod)
        for mod in extn_mod_base:
            cfg_data['repo_py_module_names'].remove(mod)
        repo_mod_dest_path = cfg_data['base_py_module_names'] + \
                               cfg_data['repo_py_module_names']
        generate_module_repo()

        module_repo_path = \
            os.path.abspath('..\\..\\..\\tools\\py2sis\\ensymble\\module-repo')
        std_module_search_path = os.path.join(module_repo_path,
                                             'standard-modules')
        find_dep_modules(std_module_search_path)

        # Adding the entries of the directories to the cfg file
        for name in dirname_list:
            dir_dep = find_dep_modules(name)
            dir_dep.sort()
            name = name.replace(std_module_search_path + '\\', '')
            name = name.replace('\\', '.')
            mod_map = {}
            # The type of the directory structure is same as that of the
            # __init__.py in the directory
            init_mod = name + '.__init__'
            mod_map['type'] = dep_map[init_mod]['type']
            mod_map['deps'] = dir_dep
            dep_map[name] = mod_map


        # Need to parse the standard modules under 'Modules',
        # 'Objects', 'Python' to get their dependency .
        # The extension module parsing in short
        standard_deps = []
        for path in ['Modules', 'Objects', 'Python', 'PC']:
            os.path.walk(os.path.abspath("..\\..\\" + path),
                         find_std_pyd_deps, None)

        # Write the dependency map in a sorted order
        fp = open(os.path.join(std_module_search_path,
                               'module_dependency.cfg'), 'wb')
        fp.write('{')
        dep_map_keys_list = dep_map.keys()
        dep_map_keys_list.sort()
        for mod in dep_map_keys_list:
            fp.write("'%s': %s,\n" %(mod, str(dep_map[mod])))
        fp.write('}')
        fp.close()
        # Run the module_dependency_cfg test
        test_module_dependency_cfg.test_main()
