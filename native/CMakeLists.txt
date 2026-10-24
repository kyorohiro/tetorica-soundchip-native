cmake_minimum_required(VERSION 3.20)

# Also allow `cmake -S native -B build/native` without a parent application.
if(CMAKE_SOURCE_DIR STREQUAL CMAKE_CURRENT_SOURCE_DIR)
  project(tetorica_soundchip_native_core LANGUAGES C CXX)
  include(CTest)
endif()

get_filename_component(TETORICA_SDK_ROOT "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
option(TETORICA_NATIVE_BUILD_TESTS "Build the standalone Native core tests" ON)

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
endif()
