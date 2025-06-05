from typing import Dict, Callable
from enum import Enum
import json
import logging
from ..state import Go1State
from ..topics import FirmwareSubTopic, UltraSonicSubTopic

logger = logging.getLogger(__name__)

class RobotName(Enum):
    """Robot model names."""
    LAIKAGO = (1, "Laikago")
    ALIENGO = (2, "Aliengo")
    A1 = (3, "A1")
    GO1 = (4, "Go1")
    B1 = (5, "B1")

    @classmethod
    def get_name(cls, value: int) -> str:
        """Get robot name from value."""
        return next((item.value[1] for item in cls if item.value[0] == value), "")

class RobotModel(Enum):
    """Robot model variants."""
    AIR = (1, "AIR")
    PRO = (2, "PRO")
    EDU = (3, "EDU")
    PC = (4, "PC")
    XX = (5, "XX")

    @classmethod
    def get_model(cls, value: int) -> str:
        """Get model name from value."""
        return next((item.value[1] for item in cls if item.value[0] == value), "")

class RobotReceiver:
    """Handler for robot-related messages."""
    
    @staticmethod
    def distance_to_warning(distance: int) -> float:
        """
        Convert distance to warning level.
        
        Args:
            distance: Distance value in centimeters
            
        Returns:
            Warning level between 0 and 1
        """
        if distance > 30:
            return 0.0
        elif distance < 10:
            return 1.0
        else:
            return 0.2 + (0.8 * (30 - distance)) / 20

    @staticmethod
    def handle_firmware_version(data: Go1State, message: bytes, data_view: 'DataView') -> None:
        """
        Process firmware version message and update Go1State.
        
        Args:
            data: Current Go1 state to update
            message: Raw message bytes
            data_view: DataView instance for parsing binary data
        """
        try:
            # Update temperature readings
            data.robot.temps = [data_view.get_uint8(i + 8) for i in range(20)]

            # Process mode and gait type if message is long enough
            if data_view.byte_length > 28:
                data.robot.mode = data_view.get_uint8(28)
                data.robot.gait_type = data_view.get_uint8(29)

                # Update robot state based on mode and gait type
                if data.robot.mode == 2:
                    if data.robot.gait_type == 2:
                        data.robot.state = "run"
                    elif data.robot.gait_type == 3:
                        data.robot.state = "climb"
                    elif data.robot.gait_type == 1:
                        data.robot.state = "walk"

            # Process extended information if message is long enough
            if data_view.byte_length >= 44:
                # Get robot name and model
                name = RobotName.get_name(data_view.get_uint8(0))
                model = RobotModel.get_model(data_view.get_uint8(1))
                
                if name:
                    data.robot.sn.product = f"{name}_{model}"

                # Update serial number if valid
                if data_view.get_uint8(2) < 255:
                    data.robot.sn.id = (
                        f"{data_view.get_uint8(2)}-"
                        f"{data_view.get_uint8(3)}-"
                        f"{data_view.get_uint8(4)}["
                        f"{data_view.get_uint8(5)}]"
                    )

                # Update hardware version if valid
                if data_view.get_uint8(36) < 255:
                    data.robot.version.hardware = (
                        f"{data_view.get_uint8(36)}."
                        f"{data_view.get_uint8(37)}."
                        f"{data_view.get_uint8(38)}"
                    )

                # Update software version
                data.robot.version.software = (
                    f"{data_view.get_uint8(39)}."
                    f"{data_view.get_uint8(40)}."
                    f"{data_view.get_uint8(41)}"
                )

        except Exception as e:
            logger.error(f"Error processing firmware version message: {str(e)}")
            # Keep previous values in case of error
            return

    @staticmethod
    def handle_ultrasonic_data(data: Go1State, message: bytes, data_view: 'DataView') -> None:
        """
        Process ultrasonic sensor data and update Go1State.
        
        Args:
            data: Current Go1 state to update
            message: Raw message bytes
            data_view: DataView instance for parsing binary data
        """
        payload = json.loads(message.decode('utf-8'))

        data.robot.us_data = {
            'front': payload.get('front', 10.0),
            'right': payload.get('right', 10.0),
            'left': payload.get('left', 10.0),
            'back': payload.get('back', 10.0)
        }
        
# Create receiver dictionary mapping topics to handler methods
robot_receivers: Dict[FirmwareSubTopic, Callable] = {
    FirmwareSubTopic.FIRMWARE_VERSION: RobotReceiver.handle_firmware_version,
    UltraSonicSubTopic.ULTRASONIC_DATA: RobotReceiver.handle_ultrasonic_data,
}