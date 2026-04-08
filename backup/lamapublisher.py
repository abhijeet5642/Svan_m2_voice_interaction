import json
import random
import numpy as np
from datetime import datetime, timezone, timedelta
from cyclonedds.domain import DomainParticipant
from cyclonedds.topic import Topic
from cyclonedds.pub import DataWriter
from cyclonedds.idl import IdlStruct
from cyclonedds.idl.types import uint8, float32, array
from dataclasses import dataclass

@dataclass
class JoyData_(IdlStruct, typename="xterra::msg::dds_::JoyData_"):
    priority: uint8
    axes:    array[float32, 6]
    buttons: array[uint8,  12]

class DDSPublisher:
    def __init__(self, topic_name="rt/experiment/joystick_data"):
        self.participant = DomainParticipant()
        self.topic = Topic(self.participant, topic_name, JoyData_)
        self.writer = DataWriter(self.participant, self.topic)
        
        # --- FIX 2: Tracking the whole signature instead of just mode ---
        self.last_signature = None
        self.button_hold_ticks = 0
        
        print(f" DDS Publisher initialized on topic: '{topic_name}'")

    def publish_movement(self, state_dict):
        mode = state_dict.get("mode", 1)
        vx = state_dict.get("x_velocity", 0.0)
        vy = state_dict.get("y_velocity", 0.0)
        wz = state_dict.get("yaw_velocity", 0.0)

        # Map axes
        axes = np.zeros(6, dtype=np.float32)
        if mode == 4: 
            axes[1] = float(np.clip(vx, -1.0, 1.0)) 
            axes[0] = float(np.clip(vy, -1.0, 1.0))
            axes[3] = float(np.clip(wz, -1.0, 1.0))

        # --- FIX 1: The "Stale Message" Hack (Keep this!) ---
        # Injecting invisible micro-noise keeps the connection alive
        axes[5] = random.uniform(-0.0001, 0.0001)

        # --- FIX 2 REVISION: Strict Mode Tracking ---
        # ONLY click the button if the actual mode changes (e.g., Stand -> Move).
        # Do NOT click the button if only the speeds change!
        if mode != getattr(self, 'last_mode', -1):
            self.last_mode = mode
            self.button_hold_ticks = 10  # Hold button for 10 frames

        buttons = np.zeros(12, dtype=np.uint8)
        
        # Output the '1' if we are in the middle of a simulated click
        if self.button_hold_ticks > 0:
            if mode == 0:
                buttons[0] = 1 
            elif mode == 1:
                buttons[1] = 1 
            elif mode == 4:
                buttons[2] = 1 
            
            self.button_hold_ticks -= 1  # Count down

        self.writer.write(JoyData_(
            priority=50,
            axes=axes.tolist(),
            buttons=buttons.tolist()
        ))
        
      # --- SMART LOGGING ---
        # Only print to the console when the command actually changes, preventing 20Hz spam!
        current_signature = f"{mode}_{vx}_{vy}_{wz}"
        if getattr(self, 'last_print_signature', None) != current_signature:
            ist_offset = timezone(timedelta(hours=5, minutes=30))
            ist_time = datetime.now(ist_offset).strftime('%d-%m-%Y %I:%M:%S %p')
            print(f"[{ist_time}] [DDS_NODE]: Published to Robot: {json.dumps(state_dict)}")
            self.last_print_signature = current_signature

# Create the singleton instance
robot_publisher = DDSPublisher()