cmake_minimum_required(VERSION 3.20)

# Also allow `cmake -S native -B build/native` without a parent application.
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
  project(tetorica_soundchip_native_core LANGUAGES C CXX)
  include(CTest)
endif()

get_filename_component(TETORICA_SDK_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
option(TETORICA_NATIVE_BUILD_TESTS "Build the standalone Native core tests" ON)
option(TETORICA_NATIVE_BUILD_EXAMPLES "Build the standalone Native examples" ON)

# First independently buildable component. The Native-owned provider explicitly
# instantiates adapter templates without changing the pinned ymfm source bytes.
# No Rust, Tauri, CPAL, device, or fetch is used.
add_library(tetorica_native_ym2612 STATIC
  reference/tauri/native_genesis_ym2612.cpp
  src/ymfm_opn_provider.cpp
  "${TETORICA_SDK_ROOT}/vendor/ymfm/ymfm_ssg.cpp"
  "${TETORICA_SDK_ROOT}/vendor/ymfm/ymfm_adpcm.cpp"
)
add_library(tetorica::ym2612 ALIAS tetorica_native_ym2612)
target_compile_features(tetorica_native_ym2612 PUBLIC cxx_std_14)
target_include_directories(tetorica_native_ym2612
  PUBLIC
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${CMAKE_CURRENT_LIST_DIR}/reference/tauri"
  PRIVATE
    "${TETORICA_SDK_ROOT}/vendor/ymfm"
    "${TETORICA_SDK_ROOT}/wasm"
)
if(MSVC)
  target_compile_options(tetorica_native_ym2612 PRIVATE /EHsc)
endif()

add_library(tetorica_native_ym2151 STATIC
  reference/tauri/native_genesis_ym2151.cpp
  src/ymfm_opm_provider.cpp
)
add_library(tetorica::ym2151 ALIAS tetorica_native_ym2151)
target_compile_features(tetorica_native_ym2151 PUBLIC cxx_std_14)
target_include_directories(tetorica_native_ym2151
  PUBLIC
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${CMAKE_CURRENT_LIST_DIR}/reference/tauri"
  PRIVATE
    "${TETORICA_SDK_ROOT}/vendor/ymfm"
    "${TETORICA_SDK_ROOT}/wasm"
)
if(MSVC)
  target_compile_options(tetorica_native_ym2151 PRIVATE /EHsc)
endif()

add_library(tetorica_native_segapsg STATIC
  reference/tauri/native_genesis_game_gear.cpp
  "${TETORICA_SDK_ROOT}/vendor/ymfm/segapsg.cpp"
)
add_library(tetorica::segapsg ALIAS tetorica_native_segapsg)
target_compile_features(tetorica_native_segapsg PUBLIC cxx_std_14)
target_include_directories(tetorica_native_segapsg
  PUBLIC
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${CMAKE_CURRENT_LIST_DIR}/reference/tauri"
  PRIVATE
    "${TETORICA_SDK_ROOT}/vendor/ymfm"
)
if(MSVC)
  target_compile_options(tetorica_native_segapsg PRIVATE /EHsc)
endif()

add_library(tetorica_native_ym2413 STATIC
  reference/tauri/native_genesis_ym2413.cpp
  src/ymfm_opl_provider.cpp
  "${TETORICA_SDK_ROOT}/vendor/ymfm/ymfm_adpcm.cpp"
  "${TETORICA_SDK_ROOT}/vendor/ymfm/ymfm_pcm.cpp"
)
add_library(tetorica::ym2413 ALIAS tetorica_native_ym2413)
target_compile_features(tetorica_native_ym2413 PUBLIC cxx_std_14)
target_include_directories(tetorica_native_ym2413
  PUBLIC
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${CMAKE_CURRENT_LIST_DIR}/reference/tauri"
  PRIVATE
    "${TETORICA_SDK_ROOT}/vendor/ymfm"
    "${TETORICA_SDK_ROOT}/wasm"
)
if(MSVC)
  target_compile_options(tetorica_native_ym2413 PRIVATE /EHsc)
endif()

add_library(tetorica_native_ay8910 STATIC
  reference/tauri/native_genesis_ay8910.cpp
  "${TETORICA_SDK_ROOT}/vendor/mame-ay8910/ay8910.cpp"
)
add_library(tetorica::ay8910 ALIAS tetorica_native_ay8910)
target_compile_features(tetorica_native_ay8910 PUBLIC cxx_std_14)
target_include_directories(tetorica_native_ay8910
  PUBLIC
    "${CMAKE_CURRENT_LIST_DIR}/include"
    "${CMAKE_CURRENT_LIST_DIR}/reference/tauri"
  PRIVATE
    "${TETORICA_SDK_ROOT}/vendor/mame-ay8910"
)
if(MSVC)
  target_compile_options(tetorica_native_ay8910 PRIVATE /EHsc)
endif()

if(TETORICA_NATIVE_BUILD_EXAMPLES)
  add_executable(tetorica_genesis_wav examples/genesis_wav.cpp)
  target_link_libraries(tetorica_genesis_wav PRIVATE tetorica::ym2612 tetorica::segapsg)
  if(MSVC)
    target_compile_options(tetorica_genesis_wav PRIVATE /EHsc)
  endif()
  add_executable(tetorica_master_system_wav examples/master_system_wav.cpp)
  target_link_libraries(tetorica_master_system_wav PRIVATE tetorica::ym2413 tetorica::segapsg)
  if(MSVC)
    target_compile_options(tetorica_master_system_wav PRIVATE /EHsc)
  endif()
  add_executable(tetorica_msx_wav examples/msx_wav.cpp)
  target_link_libraries(tetorica_msx_wav PRIVATE tetorica::ay8910 tetorica::ym2413)
  if(MSVC)
    target_compile_options(tetorica_msx_wav PRIVATE /EHsc)
  endif()
endif()

if(TETORICA_NATIVE_BUILD_TESTS)
  # A Release configuration must execute the fixture's assertions as well.
  enable_testing()
  add_executable(tetorica_ym2612_fixture tests/ym2612_fixture.cpp)
  target_link_libraries(tetorica_ym2612_fixture PRIVATE tetorica::ym2612)
  if(MSVC)
    target_compile_options(tetorica_ym2612_fixture PRIVATE /UNDEBUG /EHsc)
  else()
    target_compile_options(tetorica_ym2612_fixture PRIVATE -UNDEBUG)
  endif()
  add_test(NAME tetorica.ym2612.self_test
    COMMAND tetorica_ym2612_fixture --self-test)

  add_executable(tetorica_ym2151_fixture tests/ym2151_fixture.cpp)
  target_link_libraries(tetorica_ym2151_fixture PRIVATE tetorica::ym2151)
  if(MSVC)
    target_compile_options(tetorica_ym2151_fixture PRIVATE /UNDEBUG /EHsc)
  else()
    target_compile_options(tetorica_ym2151_fixture PRIVATE -UNDEBUG)
  endif()
  add_test(NAME tetorica.ym2151.self_test
    COMMAND tetorica_ym2151_fixture --self-test)

  add_executable(tetorica_segapsg_fixture tests/segapsg_fixture.cpp)
  target_link_libraries(tetorica_segapsg_fixture PRIVATE tetorica::segapsg)
  if(MSVC)
    target_compile_options(tetorica_segapsg_fixture PRIVATE /UNDEBUG /EHsc)
  else()
    target_compile_options(tetorica_segapsg_fixture PRIVATE -UNDEBUG)
  endif()
  add_test(NAME tetorica.segapsg.self_test
    COMMAND tetorica_segapsg_fixture --self-test)

  add_executable(tetorica_ym2413_fixture tests/ym2413_fixture.cpp)
  target_link_libraries(tetorica_ym2413_fixture PRIVATE tetorica::ym2413)
  if(MSVC)
    target_compile_options(tetorica_ym2413_fixture PRIVATE /UNDEBUG /EHsc)
  else()
    target_compile_options(tetorica_ym2413_fixture PRIVATE -UNDEBUG)
  endif()
  add_test(NAME tetorica.ym2413.self_test
    COMMAND tetorica_ym2413_fixture --self-test)

  add_executable(tetorica_ay8910_fixture tests/ay8910_fixture.cpp)
  target_link_libraries(tetorica_ay8910_fixture PRIVATE tetorica::ay8910)
  if(MSVC)
    target_compile_options(tetorica_ay8910_fixture PRIVATE /UNDEBUG /EHsc)
  else()
    target_compile_options(tetorica_ay8910_fixture PRIVATE -UNDEBUG)
  endif()
  add_test(NAME tetorica.ay8910.self_test
    COMMAND tetorica_ay8910_fixture --self-test)
endif()
