import os
import subprocess

g_force_full_rebuild=False

def get_install_dir(target, lib_name):
    root_dir = os.getcwd()
    install_dir = root_dir+"/installed_ext/"+target+"/"+lib_name
    return install_dir


def get_build_dir(target, lib_name):
    root_dir = os.getcwd()
    build_dir = root_dir+"/build/"+target+"/"+lib_name
    return build_dir

def get_binary_dir(target):
    root_dir = os.getcwd()
    install_dir = root_dir+"/Binaries/"+target
    return install_dir

def decorate_cmake_command(command, new_definition):
    return command + " {}".format(new_definition)

def build_lib(lib_name, extra_definitions, target="Debug", force_full_rebuild = g_force_full_rebuild):
    build_dir = get_build_dir(target, lib_name)

    if not force_full_rebuild:
        if os.path.exists(build_dir):
            print("Build directory for {} already exist. Skipping.".format(lib_name))
            return 1
    else:
        if os.path.exists(build_dir):
            os.removedirs(build_dir)

    os.makedirs(build_dir, exist_ok=True)
    install_dir = get_install_dir(target, lib_name)

    cmake_command = "cmake ../../../{}".format(lib_name)
    cmake_command = decorate_cmake_command(
        cmake_command, "-DCMAKE_INSTALL_PREFIX={}".format(install_dir))
    cmake_command = decorate_cmake_command(
        cmake_command, "-DBUILD_SHARED_LIBS=ON")
    cmake_command = decorate_cmake_command(
        cmake_command, "-DCMAKE_BUILD_TYPE={}".format(target))
    cmake_command = decorate_cmake_command(
        cmake_command, "-DMSVC_MP_THREAD_COUNT=10")

    for definition in extra_definitions:
        cmake_command = decorate_cmake_command(
            cmake_command, definition)

    subprocess.check_call(cmake_command,
                          cwd=build_dir)
    subprocess.check_call(
        "cmake --build . --config {}".format(target), cwd=build_dir)

    install_command = "cmake --install ."
    install_command = decorate_cmake_command(
        install_command, "--config {}".format(target))
    subprocess.check_call(install_command, cwd=build_dir)

    return 0

def copytree_from_installed_to_binaries(lib_name, target, folder):
    installed_dir = get_install_dir(target, lib_name)
    binary_dir = get_binary_dir(target)

    import shutil
    shutil.copytree(installed_dir+"/"+folder, binary_dir +
                    "/"+folder, dirs_exist_ok=True)
    return

def build_tbb(target):
    lib_name = "tbb"
    extra_command = []
    extra_command.append("-DTBB_BUILD_TESTS=OFF")
    extra_command.append("-DCMAKE_DEBUG_POSTFIX=_debug")
    if build_lib(lib_name, extra_command, target):
        return 1

    trees_to_copy = ["bin"]

    for tree in trees_to_copy:
        copytree_from_installed_to_binaries(lib_name, target, tree)

    return



def build_OpenUSD(target):
    lib_name = "OpenUSD"
    extra_command = []
    tbb_install_dir = get_install_dir(target, "tbb")
    osd_install_dir = get_install_dir(target, "OpenSubdiv")

    extra_command.append("-DTBB_ROOT_DIR={}".format(tbb_install_dir))
    extra_command.append("-DOPENSUBDIV_ROOT_DIR={}".format(osd_install_dir))
    extra_command.append("-DOPENSUBDIV_USE_GPU=ON")
    extra_command.append("-DPXR_BUILD_TESTS=OFF")
    extra_command.append("-DTBB_USE_DEBUG_BUILD=0")

    if build_lib(lib_name, extra_command, target):
        return 1

    # trees_to_copy = ["lib"]

    # for tree in trees_to_copy:
    #     copytree_from_installed_to_binaries(lib_name, target, tree)
    installed_dir = get_install_dir(target, lib_name)
    binary_dir = get_binary_dir(target)

    import shutil
    shutil.copytree(installed_dir+"/"+"lib", binary_dir +
                    "/"+"bin", dirs_exist_ok=True)

def build_OpenSubdiv(target):
    lib_name = "OpenSubdiv"
    extra_command = []
    extra_command.append("-DNO_OPENCL=ON")
    extra_command.append("-DNO_DX=ON")
    extra_command.append("-DNO_EXAMPLES=ON")
    extra_command.append("-DNO_TUTORIALS=ON")

    if build_lib(lib_name, extra_command, target):
        return 1

    trees_to_copy = ["bin"]

    for tree in trees_to_copy:
        copytree_from_installed_to_binaries(lib_name, target, tree)

    return 0

def build(target="Debug"):
    print("Begin building USTC_CG_2024 Dependencies.")
    os.makedirs("./Binaries", exist_ok=True)
    os.makedirs("./build", exist_ok=True)

    build_tbb(target)
    build_OpenSubdiv(target)
    build_OpenUSD(target)

    return


if __name__ == "__main__":
    build("RelWithDebInfo")
    build("Release")
