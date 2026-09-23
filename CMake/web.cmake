# Browser build, configured with emcmake. SDL2, zlib and libpng come from
# emscripten ports; everything else is fetched and built from source with the
# same -pthread flags so every object can share wasm memory.

include(FetchContent)

# ogg and vorbis still declare cmake_minimum_required below 3.5.
set(CMAKE_POLICY_VERSION_MINIMUM 3.5)
set(CMAKE_POLICY_DEFAULT_CMP0077 NEW)
set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(BUILD_TESTING OFF CACHE BOOL "" FORCE)

set(USE_OPENGLES ON CACHE BOOL "" FORCE)
add_compile_definitions(USE_OPENGLES=1)

set(WEB_PORT_FLAGS -sUSE_SDL=2 -sUSE_ZLIB=1 -sUSE_LIBPNG=1)
add_compile_options(-pthread -fexceptions ${WEB_PORT_FLAGS})
add_link_options(-pthread -fexceptions ${WEB_PORT_FLAGS})

# The find modules below need the port libraries on disk at configure time.
execute_process(
    COMMAND ${EMSCRIPTEN_ROOT_PATH}/embuilder build zlib libpng-mt sdl2-mt
    RESULT_VARIABLE WEB_EMBUILDER_RESULT
)
if(NOT WEB_EMBUILDER_RESULT EQUAL 0)
    message(FATAL_ERROR "embuilder failed to build the emscripten ports")
endif()

set(WEB_SYSROOT "${EMSCRIPTEN_SYSROOT}")
if(NOT WEB_SYSROOT)
    set(WEB_SYSROOT "${CMAKE_SYSROOT}")
endif()
set(ZLIB_INCLUDE_DIR "${WEB_SYSROOT}/include" CACHE PATH "" FORCE)
set(ZLIB_LIBRARY "${WEB_SYSROOT}/lib/wasm32-emscripten/libz.a" CACHE FILEPATH "" FORCE)
set(PNG_PNG_INCLUDE_DIR "${WEB_SYSROOT}/include" CACHE PATH "" FORCE)
set(PNG_LIBRARY "${WEB_SYSROOT}/lib/wasm32-emscripten/libpng-mt.a" CACHE FILEPATH "" FORCE)

add_library(SDL2::SDL2 INTERFACE IMPORTED GLOBAL)
set_target_properties(SDL2::SDL2 PROPERTIES
    INTERFACE_COMPILE_OPTIONS "-sUSE_SDL=2"
    INTERFACE_LINK_OPTIONS "-sUSE_SDL=2"
)
set(SDL2_FOUND TRUE)
set(SDL2_INCLUDE_DIRS "")

set(tinyxml2_BUILD_TESTING OFF)
FetchContent_Declare(tinyxml2
    GIT_REPOSITORY https://github.com/leethomason/tinyxml2.git
    GIT_TAG 10.0.0
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)
set(JSON_BuildTests OFF)
FetchContent_Declare(nlohmann_json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG v3.11.3
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)
FetchContent_Declare(spdlog
    GIT_REPOSITORY https://github.com/gabime/spdlog.git
    GIT_TAG v1.15.3
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)

set(BUILD_TOOLS OFF)
set(BUILD_REGRESS OFF)
set(BUILD_OSSFUZZ OFF)
set(BUILD_EXAMPLES OFF)
set(BUILD_DOC OFF)
set(ENABLE_BZIP2 OFF)
set(ENABLE_LZMA OFF)
set(ENABLE_ZSTD OFF)
set(ENABLE_OPENSSL OFF)
set(ENABLE_GNUTLS OFF)
set(ENABLE_MBEDTLS OFF)
set(ENABLE_COMMONCRYPTO OFF)
set(ENABLE_WINDOWS_CRYPTO OFF)
FetchContent_Declare(libzip
    GIT_REPOSITORY https://github.com/nih-at/libzip.git
    GIT_TAG v1.11.4
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)

set(INSTALL_DOCS OFF)
FetchContent_Declare(Ogg
    GIT_REPOSITORY https://github.com/xiph/ogg.git
    GIT_TAG v1.3.5
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)
FetchContent_Declare(Vorbis
    GIT_REPOSITORY https://github.com/xiph/vorbis.git
    GIT_TAG v1.3.7
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)
set(OPUS_BUILD_PROGRAMS OFF)
set(OPUS_BUILD_TESTING OFF)
set(OPUS_INSTALL_PKG_CONFIG_MODULE OFF)
set(OPUS_INSTALL_CMAKE_CONFIG_MODULE OFF)
FetchContent_Declare(Opus
    GIT_REPOSITORY https://github.com/xiph/opus.git
    GIT_TAG v1.5.2
    GIT_SHALLOW TRUE
    OVERRIDE_FIND_PACKAGE
)
# opusfile 0.12 ships no CMake build; its decoder is four C files.
FetchContent_Declare(OpusFile
    GIT_REPOSITORY https://github.com/xiph/opusfile.git
    GIT_TAG v0.12
    GIT_SHALLOW TRUE
)

FetchContent_MakeAvailable(tinyxml2 nlohmann_json spdlog libzip Ogg Vorbis Opus OpusFile)

add_library(opusfile STATIC
    ${opusfile_SOURCE_DIR}/src/info.c
    ${opusfile_SOURCE_DIR}/src/internal.c
    ${opusfile_SOURCE_DIR}/src/opusfile.c
    ${opusfile_SOURCE_DIR}/src/stream.c
)
target_include_directories(opusfile PUBLIC ${opusfile_SOURCE_DIR}/include ${opus_SOURCE_DIR}/include)
target_link_libraries(opusfile PUBLIC Ogg::ogg Opus::opus)

# Desktop builds find these headers in the system include path. soh includes
# opus as <opus/opus.h>, so its headers are staged under an opus/ directory.
file(GLOB WEB_OPUS_HEADERS "${opus_SOURCE_DIR}/include/*.h")
file(COPY ${WEB_OPUS_HEADERS} DESTINATION "${CMAKE_BINARY_DIR}/web-include/opus")
include_directories(
    "${CMAKE_CURRENT_LIST_DIR}/web-include"
    "${CMAKE_BINARY_DIR}/web-include"
    "${libzip_SOURCE_DIR}/lib"
    "${libzip_BINARY_DIR}"
    "${tinyxml2_SOURCE_DIR}"
    "${opus_SOURCE_DIR}/include"
    "${opusfile_SOURCE_DIR}/include"
    "${ogg_SOURCE_DIR}/include"
    "${ogg_BINARY_DIR}/include"
    "${vorbis_SOURCE_DIR}/include"
)

# The names soh links, which its Find modules create on desktop.
add_library(Vorbis::vorbis ALIAS vorbis)
add_library(Vorbis::vorbisenc ALIAS vorbisenc)
add_library(Vorbis::vorbisfile ALIAS vorbisfile)
add_library(Opusfile::Opusfile ALIAS opusfile)
foreach(pkg OpusFile Opusfile)
    file(WRITE "${CMAKE_FIND_PACKAGE_REDIRECTS_DIR}/${pkg}Config.cmake" "")
endforeach()
