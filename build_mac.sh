BUILD_TYPE="Release"
USTC_DEP_ROOT="$(pwd)"
# install dir = $SDK_PATH/$BUILD_TYPE/LIBNAME
SDK_PATH="$USTC_DEP_ROOT/SDK"
INSTALL_PREFIX_WITHOUT_LIBNAME="$SDK_PATH/$BUILD_TYPE"
BUILD_DIR="$USTC_DEP_ROOT/build/$BUILD_TYPE"
BINARY_DIR="$USTC_DEP_ROOT/Binaries"

cmake_build() {
  _LIB_NAME=$1
  cmake --build "$BUILD_DIR/$_LIB_NAME" --config "$BUILD_TYPE"
  RET=$?
  if [ $RET -ne 0 ]; then
    echo "Failed to build $_LIB_NAME"
    exit 1
  fi
}

cmake_install() {
  _LIB_NAME=$1
  cmake --install "$BUILD_DIR/$_LIB_NAME"
  RET=$?
  if [ $RET -ne 0 ]; then
    echo "Failed to install $_LIB_NAME"
    exit 1
  fi
}

##################################################################
# tbb: Use system
echo "Build TBB"
mkdir -p "$BUILD_DIR/tbb"
# ==> Configure
cmake -S "$USTC_DEP_ROOT/tbb" -B "$BUILD_DIR/tbb"\
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/tbb" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10 \
  -DTBB_BUILD_TESTS=OFF \
  -DCMAKE_DEBUG_POSTFIX=_debug

if [ $? -ne 0 ]; then
  echo "Failed to configure tbb"
  exit 1
fi

# ==> Build
cmake_build "tbb"
# ==> Install
cmake_install "tbb"

# echo "TBB Build Successful!"

##################################################################
# opensubdiv
echo "Build OpenSubdiv"
mkdir -p $BUILD_DIR/OpenSubdiv
# ==> Configure
cmake -S "$USTC_DEP_ROOT/OpenSubdiv" -B "$BUILD_DIR/OpenSubdiv" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/OpenSubdiv" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10 \
  -DNO_OPENCL=ON \
  -DNO_DX=ON \
  -DNO_EXAMPLES=ON \
  -DNO_TUTORIALS=ON \
  -DNO_OMP=ON \
  -DCMAKE_C_COMPILER=clang\
  -DCMAKE_CXX_COMPILER=clang++
# NOTE: On mac m1, openmp build will fail.

RET=$?
if [ $RET -ne 0 ]; then
  echo "Failed to configure OpenSubdiv"
  exit 1
fi

# ==> Build
cmake_build "OpenSubdiv"
# ==> Install
cmake_install "OpenSubdiv"

echo "OpenSubdiv Build Successful!"

##################################################################
# zlib
echo "Build zlib"
mkdir -p $BUILD_DIR/zlib
# ==> Configure
cmake -S "$USTC_DEP_ROOT/zlib" -B "$BUILD_DIR/zlib" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/zlib" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10

RET=$?
if [ $RET -ne 0 ]; then
  echo "Failed to configure zlib"
  exit 1
fi
# ==> Build
cmake_build "zlib"
# ==> Install
cmake_install "zlib"

echo "zlib Build Successful!"

##################################################################
# openvdb

# ==> Need to build blosc first.
echo "Build Blosc"
mkdir -p "$BUILD_DIR/c-blosc"
cmake -S "$USTC_DEP_ROOT/c-blosc" -B "$BUILD_DIR/c-blosc" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/c-blosc" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10

if [ $? -ne 0 ]; then
  echo "Failed to configure c-blosc"
  exit 1
fi

# ==> Build
cmake_build "c-blosc"
# ==> Install
cmake_install "c-blosc"

echo "Blosc Build Successful!"

# Now Build OpenVDB
echo "Build OpenVDB"
# mv openvdb/cmake/FindTBB.cmake ./FindTBB.cmake.bak
mkdir -p "$BUILD_DIR/openvdb"
cmake -S "$USTC_DEP_ROOT/openvdb" -B "$BUILD_DIR/openvdb" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/openvdb" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10 \
  -DBLOSC_ROOT="$INSTALL_PREFIX_WITHOUT_LIBNAME/c-blosc" \
  -DZLIB_ROOT="$INSTALL_PREFIX_WITHOUT_LIBNAME/zlib" \
  -DOPENVDB_BUILD_NANOVDB=OFF \
  -DOPENVDB_BUILD_UNITTESTS=OFF \
  -DOPENVDB_CORE_STATIC=OFF \
  -DUSE_EXPLICIT_INSTANTIATION=OFF \
  -DDISABLE_DEPENDENCY_VERSION_CHECKS=ON \
  -DUSE_PKGCONFIG=OFF
  # -DTBB_ROOT="$INSTALL_PREFIX_WITHOUT_LIBNAME/tbb" \
  # -DTBB_INCLUDEDIR=$INSTALL_PREFIX_WITHOUT_LIBNAME/tbb/include \
  # -DTBB_LIBRARYDIR=$INSTALL_PREFIX_WITHOUT_LIBNAME/tbb/lib/ \

# NOTE: nanovdb is not supported on mac, disable it, and ignore other relavent options.

# WARNING: This will ignore the installed TBB and use the system TBB, I'm not sure if this is correct.
#          However, the build will fail if I use the installed TBB.

RET=$?
if [ $RET -ne 0 ]; then
  echo "Failed to configure openvdb"
  exit 1
fi

# ==> Build
cmake_build "openvdb"
# ==> Install
# mv ./FindTBB.cmake.bak openvdb/cmake/FindTBB.cmake
cmake_install "openvdb"

echo "OpenVDB Build Successful!"

##################################################################
# MaterialX
echo "Build MaterialX"
mkdir -p "$BUILD_DIR/MaterialX"
cmake -S "$USTC_DEP_ROOT/MaterialX" -B "$BUILD_DIR/MaterialX" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/MaterialX" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10 \
  -DMATERIALX_BUILD_SHARED_LIBS=ON \
  -DMATERIALX_BUILD_TESTS=OFF

RET=$?
if [ $RET -ne 0 ]; then
  echo "Failed to configure MaterialX"
  exit 1
fi

# ==> Build
cmake_build "MaterialX"
# ==> Install
cmake_install "MaterialX"

echo "MaterialX Build Successful!"
##################################################################
# Imath
echo "Build Imath"
mkdir -p "$BUILD_DIR/Imath"
cmake -S "$USTC_DEP_ROOT/Imath" -B "$BUILD_DIR/Imath" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/Imath" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10

RET=$?
if [ $RET -ne 0 ]; then
  echo "Failed to configure Imath"
  exit 1
fi

# ==> Build
cmake_build "Imath"
# ==> Install
cmake_install "Imath"

echo "Imath Build Successful!"

##################################################################
# OpenUSD
echo "Build OpenUSD"
mkdir -p "$BUILD_DIR/OpenUSD"
# python OpenUSD/build_scripts/build_usd.py

# fix a small bug:
sed -i "30 a #include <boost/range/iterator_range.hpp>" \
  OpenUSD/extras/usd/examples/usdObj/streamIO.cpp

cmake -S "$USTC_DEP_ROOT/OpenUSD" -B "$BUILD_DIR/OpenUSD" \
  -G "Ninja" \
  -DTBB_ROOT_DIR="$INSTALL_PREFIX_WITHOUT_LIBNAME/tbb" \
  -DCMAKE_BUILD_TYPE="$BUILD_TYPE" \
  -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX_WITHOUT_LIBNAME/OpenUSD" \
  -DBUILD_SHARED_LIBS=ON \
  -DMSVC_MP_THREAD_COUNT=10 \
  -DOPENSUBDIV_ROOT_DIR="$INSTALL_PREFIX_WITHOUT_LIBNAME/OpenSubdiv" \
  -DOPENSUBDIV_USE_GPU=OFF \
  -DMaterialX_DIR="$INSTALL_PREFIX_WITHOUT_LIBNAME/MaterialX/lib/cmake/MaterialX/" \
  -DPXR_ENABLE_MATERIALX_SUPPORT=ON \
  -DOPENVDB_LOCATION="$INSTALL_PREFIX_WITHOUT_LIBNAME/openvdb" \
  -DPXR_ENABLE_OPENVDB_SUPPORT=ON \
  -DImath_DIR="$INSTALL_PREFIX_WITHOUT_LIBNAME/Imath/lib/cmake/Imath/" \
  -DPXR_BUILD_TESTS=OFF \
  -DBOOST_ROOT="/opt/homebrew/opt/boost@1.83" \
  -DPXR_ENABLE_PYTHON_SUPPORT=OFF
cmake_build "OpenUSD"
cmake_install "OpenUSD"


mkdir SDK/common
wget https://github.com/embree/embree/releases/download/v4.3.1/embree-4.3.1.arm64.macosx.zip -O embree.zip
unzip embree.zip -d "SDK/common/embree"
wget https://github.com/shader-slang/slang/releases/download/v2024.1.5/slang-2024.1.5-macos-aarch64.zip -O slang.zip
unzip slang.zip -d "SDK/common/slang"