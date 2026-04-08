cmake_minimum_required(VERSION 3.10)
project(svan_subscriber)

# 1. Use modern C++ standards
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 2. Find the CycloneDDS C++ libraries we installed
find_package(CycloneDDS-CXX REQUIRED)

# 3. Tell the compiler to build an executable program using both our files
add_executable(subscriber_node 
    subscriber.cpp 
    JoyData.cpp
)

# 4. Link the DDS network tools to our new program
target_link_libraries(subscriber_node CycloneDDS-CXX::ddscxx)