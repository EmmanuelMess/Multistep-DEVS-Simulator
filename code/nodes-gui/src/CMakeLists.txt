add_subdirectory(library)

add_executable(example_window main.c)
add_executable(nodes_gui::example_window ALIAS example_window)

target_link_libraries(example_window raylib nodes_gui::nodes_library)
target_include_directories(example_window PRIVATE "${raylib_SOURCE_DIR}/src" "${raygui_SOURCE_DIR}/src")
target_include_directories(example_window ${WARNING_GUARD} PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
                                                                  $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/include>)

# Web Configurations
if (${PLATFORM} STREQUAL "Web")
  set_target_properties(example_window PROPERTIES SUFFIX ".html") # Tell Emscripten to build an example.html file.
  set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -s USE_GLFW=3 -s ASSERTIONS=1 -s WASM=1 -s ASYNCIFY -s GL_ENABLE_GET_PROC_ADDRESS=1")
endif()

# Checks if OSX and links appropriate frameworks (Only required on MacOS)
if (APPLE)
  target_link_libraries(example_window "-framework IOKit")
  target_link_libraries(example_window "-framework Cocoa")
  target_link_libraries(example_window "-framework OpenGL")
endif()