add_library(nodes_library SHARED
    window.c
    dictionary.c
    blocks.c)
add_library(nodes_gui::nodes_library ALIAS nodes_library)
set_property(TARGET nodes_library PROPERTY POSITION_INDEPENDENT_CODE ON)
set_property(TARGET raylib PROPERTY POSITION_INDEPENDENT_CODE ON)

target_link_libraries(
    nodes_library
    PRIVATE raylib
)
target_include_directories(nodes_library PRIVATE "${raylib_SOURCE_DIR}/src" "${raygui_SOURCE_DIR}/src")
target_include_directories(nodes_library ${WARNING_GUARD} PUBLIC $<BUILD_INTERFACE:${PROJECT_SOURCE_DIR}/include>
                                                                 $<BUILD_INTERFACE:${PROJECT_BINARY_DIR}/include>)
add_custom_command(TARGET nodes_library POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_CURRENT_SOURCE_DIR}/resources
    ${CMAKE_CURRENT_BINARY_DIR}/resources)


set(CMAKE_LIBRARY_DIR "${CMAKE_SOURCE_DIR}/lib")
add_custom_command(TARGET nodes_library POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy_directory
    ${CMAKE_CURRENT_SOURCE_DIR}/resources
    ${CMAKE_LIBRARY_DIR}/resources)
add_custom_command(TARGET nodes_library POST_BUILD
    COMMAND ${CMAKE_COMMAND} -E copy
    ${CMAKE_CURRENT_BINARY_DIR}/libnodes_library.so
    ${CMAKE_LIBRARY_DIR}/libnodes_library.so)