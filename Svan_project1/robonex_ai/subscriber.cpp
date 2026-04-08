#include <iostream>
#include <chrono>
#include <thread>

// Include the CycloneDDS C++ API
#include "dds/dds.hpp"

// Include the headers we just generated from your IDL
#include "JoyData.hpp"

using namespace org::eclipse::cyclonedds;

int main() {
    try {
        std::cout << "Starting C++ Subscriber Node..." << std::endl;

        // 1. Create a Domain Participant (joining the DDS network)
        dds::domain::DomainParticipant participant(domain::default_id());

        // 2. Create the Topic 
        dds::topic::Topic<xterra::msg::dds_::JoyData_> topic(participant, "rt/experiment/joystick_data");

        // 3. Create the DataReader
        dds::sub::DataReader<xterra::msg::dds_::JoyData_> reader(participant, topic);

        std::cout << " Listening for commands from the AI Brain..." << std::endl;

        // 4. The Listening Loop
        while (true) {
            // Take any new messages
            auto samples = reader.take();

            for (const auto& sample : samples) {
                if (sample.info().valid()) {
                    const auto& msg = sample.data();
                    
                    // Print the mapped velocities that the robot motors will use!
                    std::cout << "\n--- NEW COMMAND RECEIVED ---" << std::endl;
                    // std::cout << "Priority: " << static_cast<int>(msg.priority()) << std::endl;
                    std::cout << "Y-Velocity (Left/Right): " << msg.axes()[0] << std::endl;
                    std::cout << "X-Velocity (Fwd/Back):   " << msg.axes()[1] << std::endl;
                    std::cout << "Yaw-Velocity (Turn):     " << msg.axes()[3] << std::endl;
                }
            }
            
            std::this_thread::sleep_for(std::chrono::milliseconds(20));
        }

    } catch (const dds::core::Exception& e) {
        std::cerr << " DDS Error: " << e.what() << std::endl;
        return 1;
    }

    return 0;
}