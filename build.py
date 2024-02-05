import os
import subprocess

g_force_full_rebuild = False
g_boost_dir = "C:/local/boost_1_83_0/"


def get_install_dir(target, lib_name):
    root_dir = os.getcwd().replace("\\", "/")
    install_dir = root_dir + "/SDK/" + target + "/" + lib_name
    return install_dir


def get_build_dir(target, lib_name):
    root_dir = os.getcwd().replace("\\", "/")
    build_dir = root_dir + "/build/" + target + "/" + lib_name
    return build_dir


def get_binary_dir(target):
    root_dir = os.getcwd().replace("\\", "/")
    install_dir = root_dir + "/Binaries/" + target
    return install_dir


def decorate_cmake_command(command, new_definition):
    return command + " {}".format(new_definition)


def build_lib(
    lib_name, extra_definitions, target="Debug", force_full_rebuild=g_force_full_rebuild
):
    build_dir = get_build_dir(target, lib_name)

    # if not force_full_rebuild:
    #     if os.path.exists(build_dir):
    #         print("Build directory for {} already exist. Skipping.".format(lib_name))
    #         return 1
    # else:
    #     if os.path.exists(build_dir):
    #         os.removedirs(build_dir)

    os.makedirs(build_dir, exist_ok=True)
    install_dir = get_install_dir(target, lib_name)

    cmake_command = "cmake ../../../{}".format(lib_name)
    cmake_command = decorate_cmake_command(
        cmake_command, "-DCMAKE_INSTALL_PREFIX={}".format(install_dir)
    )
    cmake_command = decorate_cmake_command(cmake_command, "-DBUILD_SHARED_LIBS=ON")
    cmake_command = decorate_cmake_command(
        cmake_command, "-DCMAKE_BUILD_TYPE={}".format(target)
    )
    cmake_command = decorate_cmake_command(cmake_command, "-DMSVC_MP_THREAD_COUNT=10")

    for definition in extra_definitions:
        cmake_command = decorate_cmake_command(cmake_command, definition)

    subprocess.check_call(cmake_command, cwd=build_dir)
    subprocess.check_call(
        "cmake --build . --config {} -- /m:10".format(target), cwd=build_dir
    )

    install_command = "cmake --install ."
    install_command = decorate_cmake_command(
        install_command, "--config {}".format(target)
    )
    subprocess.check_call(install_command, cwd=build_dir)

    return 0


def build_tbb(target):
    lib_name = "tbb"
    extra_command = []
    extra_command.append("-DTBB_BUILD_TESTS=OFF")
    extra_command.append("-DCMAKE_DEBUG_POSTFIX=_debug")
    if build_lib(lib_name, extra_command, target):
        return 1

    return


def build_OpenSubdiv(target):
    lib_name = "OpenSubdiv"
    extra_command = []
    extra_command.append("-DNO_OPENCL=ON")
    extra_command.append("-DNO_DX=ON")
    extra_command.append("-DNO_EXAMPLES=ON")
    extra_command.append("-DNO_TUTORIALS=ON")

    if build_lib(lib_name, extra_command, target):
        return 1

    return 0


def copy_boost(target):
    print("Copying boost to SDK...")
    lib_name = "boost"
    boost_install_dir = get_install_dir(target, "boost")
    boost_install_dir = get_install_dir(target, lib_name)

    copy_folder_list = ["lib64-msvc-14.3", "boost"]

    import shutil
    import os

    for folder in copy_folder_list:
        if not os.path.exists(boost_install_dir + "/" + folder):
            shutil.copytree(
                g_boost_dir + "/" + folder,
                boost_install_dir + "/" + folder,
                dirs_exist_ok=True,
            )

    lib_dir = boost_install_dir + "/" + "lib64-msvc-14.3"
    if os.path.exists(lib_dir + "/cmake"):
        shutil.rmtree(lib_dir + "/cmake")
    for file in os.listdir(lib_dir):
        if file.startswith("libboost"):
            os.remove(lib_dir + "/" + file)
            continue
        if file.endswith(".pdb"):
            os.remove(lib_dir + "/" + file)
            continue
        if target == "Debug":
            if not "-gd-" in file:
                os.remove(lib_dir + "/" + file)
                continue
        else:
            if "-gd-" in file:
                os.remove(lib_dir + "/" + file)
                continue

def clean_pbd(lib_dir):
    for root, dirs, files in os.walk(lib_dir):
        for file in files:
            if file.endswith(".pdb"):
                os.remove(root + "/" + file)
                continue


def find_python():
    import sys
    import pathlib

    python_location = pathlib.Path(sys.executable).parent
    return str(python_location).replace("\\", "/")


def fix_USD_cmake_config(target):
    # Fix generated pxrTargets
    lib_name = "OpenUSD"
    tbb_install_dir = get_install_dir(target, "tbb")
    osd_install_dir = get_install_dir(target, "OpenSubdiv")
    installed_dir = get_install_dir(target, lib_name)
    import sys

    python_location = find_python()
    import shutil

    if not os.path.exists(installed_dir + "/cmake/pxrTargets-original.cmake"):
        shutil.copyfile(
            installed_dir + "/cmake/pxrTargets.cmake",
            installed_dir + "/cmake/pxrTargets-original.cmake",
        )
    print(python_location + "/include")
    with open(installed_dir + "/cmake/pxrTargets-original.cmake", "rt") as fin:
        with open(installed_dir + "/cmake/pxrTargets.cmake", "wt") as fout:
            for line in fin:
                replaced = (
                    line.replace("C:/local/boost_1_83_0", "${_IMPORT_PREFIX}/../boost")
                    .replace(tbb_install_dir, "${_IMPORT_PREFIX}/../tbb")
                    .replace(osd_install_dir, "${_IMPORT_PREFIX}/../OpenSubdiv")
                    .replace(python_location + "/include", "${Python3_INCLUDE_DIR}")
                )
                fout.write(replaced)
    return


def build_blosc(target):
    lib_name = "c-blosc"
    extra_command = []
    already_built = build_lib(lib_name, extra_command, target) != 0
    return already_built


def build_zlib(target):
    lib_name = "zlib"
    extra_command = []
    already_built = build_lib(lib_name, extra_command, target) != 0
    return already_built


def build_openexr(target):
    lib_name = "openexr"
    extra_command = [
        "-DOPENEXR_INSTALL_TOOLS=OFF",
        "-DOPENEXR_INSTALL_EXAMPLES=OFF",
        # Force OpenEXR to build and use a separate Imath library
        # instead of looking for one externally. This ensures that
        # OpenEXR and other dependencies use the Imath library
        # built via this script.
        "-DOPENEXR_FORCE_INTERNAL_IMATH=ON",
        "-DBUILD_TESTING=OFF",
    ]
    already_built = build_lib(lib_name, extra_command, target) != 0
    return already_built


def build_openvdb(target):
    build_blosc(target)
    build_zlib(target)

    lib_name = "openvdb"
    extra_command = []
    tbb_install_dir = get_install_dir(target, "tbb")
    zlib_install_dir = get_install_dir(target, "zlib")
    blosc_install_dir = get_install_dir(target, "c-blosc")

    extra_command.append("-DTBB_ROOT={}".format(tbb_install_dir))
    extra_command.append("-DBLOSC_ROOT={}".format(blosc_install_dir))
    extra_command.append("-DZLIB_ROOT={}".format(zlib_install_dir))
    extra_command.append("-DOPENVDB_BUILD_NANOVDB=ON")
    extra_command.append("-DOPENVDB_CORE_STATIC=OFF")
    extra_command.append("-DUSE_EXPLICIT_INSTANTIATION=OFF")
    extra_command.append("-DMSVC_COMPRESS_PDB=OFF")
    extra_command.append("-DNANOVDB_USE_OPENVDB=ON")
    extra_command.append("-DNANOVDB_USE_BLOSC=ON")
    extra_command.append("-DDISABLE_DEPENDENCY_VERSION_CHECKS=ON")

    # It seems that openvdb has problem detecting existing built binaries.
    already_built = build_lib(lib_name, extra_command, target) != 0
    return already_built


def build_MaterialX(target):
    lib_name = "MaterialX"
    extra_command = ["-DMATERIALX_BUILD_SHARED_LIBS=ON",
                        '-DMATERIALX_BUILD_TESTS=OFF']
    already_built = build_lib(lib_name, extra_command, target) != 0
    return already_built


def build_OpenUSD(target):
    build_openexr(target)
    lib_name = "OpenUSD"
    extra_command = []
    install_dir = get_install_dir(target, lib_name)

    tbb_install_dir = get_install_dir(target, "tbb")
    extra_command.append("-DTBB_ROOT_DIR={}".format(tbb_install_dir))

    osd_install_dir = get_install_dir(target, "OpenSubdiv")
    extra_command.append("-DOPENSUBDIV_ROOT_DIR={}".format(osd_install_dir))
    extra_command.append("-DOPENSUBDIV_USE_GPU=ON")

    mtlx_install_dir = get_install_dir(target, "MaterialX") + "/lib/cmake/MaterialX/"
    extra_command.append("-DMaterialX_DIR={}".format(mtlx_install_dir))
    extra_command.append("-DPXR_ENABLE_MATERIALX_SUPPORT=ON")

    openvdb_install_dir = get_install_dir(target, "openvdb")
    extra_command.append("-DOPENVDB_LOCATION={}".format(openvdb_install_dir))
    extra_command.append("-DPXR_ENABLE_OPENVDB_SUPPORT=ON")

    openexr_install_dir = get_install_dir(target, "openexr")
    extra_command.append("-DOPENEXR_LOCATION={}".format(openexr_install_dir))
    # It doesn't need a support flag

    extra_command.append("-DPXR_BUILD_TESTS=OFF")
    extra_command.append("-DPXR_USE_DEBUG_PYTHON=OFF")

    if not target == "Debug":
        extra_command.append("-DTBB_USE_DEBUG_BUILD=0")


    already_built = build_lib(lib_name, extra_command, target) != 0

    copy_boost(target)
    clean_pbd(install_dir)
    fix_USD_cmake_config(target)

    return already_built


def build(target="Debug"):
    print("Begin building USTC_CG_2024 Dependencies. Target {0}".format(target))
    # os.makedirs("./Binaries", exist_ok=True)
    os.makedirs("./build", exist_ok=True)

    build_tbb(target)
    build_OpenSubdiv(target)
    build_openvdb(target=target)
    build_MaterialX(target=target)
    build_OpenUSD(target)

    return


if __name__ == "__main__":
    build("Release")
    build("Debug")
