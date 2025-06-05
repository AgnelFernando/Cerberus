import asyncio
from enum import Enum
import logging
import threading
import time
import cv2
from go1pylib.go1 import Go1, Go1Mode
from go1pylib.mqtt.state import Go1State
from grid_map import CellStatus, GridMap
from object_detector import ObjectDetector
from collections import defaultdict, deque

# Initialize logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Direction(Enum):
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right" 


class PatrolService:
    def __init__(self, dog: Go1, detector: ObjectDetector):
        self.dog = dog
        self.detector = detector
        self.person_stopped = False 
        self.thresholds = [0.6, 0.4, 0.4, 0.8]  
        self.running = False 
        self.move_duration = 200  # ms
        self.move_speed = 0.1  # m/s
        self.us_history = defaultdict(lambda: deque(maxlen=15))
        self.us_distances = {Direction.FRONT: 0.0, Direction.RIGHT: 0.0, Direction.LEFT: 0.0, Direction.BACK: 0.0}
        self.neighbor = {Direction.FRONT: CellStatus.UNKNOWN, Direction.RIGHT:CellStatus.UNKNOWN, 
                         Direction.LEFT:CellStatus.UNKNOWN, Direction.BACK: CellStatus.UNKNOWN} 
        self.grid_map = GridMap()  
        
    def update_us_data(self, state: Go1State) -> None:
        for dir in Direction:
            value = state.robot.us_data.get(dir.value, 0.0)

            if value >= 2.0:
                value = 2.0

            self.us_history[dir].append(value)
            avg = sum(self.us_history[dir]) / len(self.us_history[dir])
            avg = max(0.0, min(avg, 2.0))  
            value = round(avg, 1)
            self.us_distances[dir] = value
            if value >= 2.0 or value == 0.0:
                self.neighbor[dir] = CellStatus.UNKNOWN
            elif value < self.thresholds[0]:
                self.neighbor[dir] = CellStatus.OCCUPIED
            else:
                self.neighbor[dir] = CellStatus.FREE


    async def start_patrol(self):
        self.dog.set_mode(Go1Mode.WALK)
        logger.info("Starting patrol...")
        self.running = True
        self.dog.set_led_color(0, 255, 0) # green

        while self.running:
            self.grid_map.update_map(self.neighbor)
            if self.detector.is_waving_detected():
                self.dog.set_led_color(255, 255, 255)
                logger.info("Waving detected! Performing special action!")
                await self.stop_movement()  # Stop
                self.dog.set_mode(Go1Mode.STRAIGHT_HAND1)
                await asyncio.sleep(5)  # stay standing 5 sec

            else:
                if self.person_stopped:
                    logger.info("No person detected. Resuming patrol.")
                    self.dog.set_mode(Go1Mode.WALK)
                    self.person_stopped = False

                dir = self.grid_map.move_robot() 

                match dir:
                    case Direction.FRONT:
                        await self.dog.go_forward(self.move_speed, self.move_duration)                      
                    case Direction.BACK:            
                        await self.dog.go_backward(self.move_speed, self.move_duration)
                    case Direction.LEFT:
                        await self.dog.go_left(self.move_speed, self.move_duration)
                    case Direction.RIGHT:
                        await self.dog.go_right(self.move_speed, self.move_duration)
                    case _:
                        logger.info("No valid move direction found. Stopping.")
                        await self.stop_movement()

                await self.stop_movement()
                await asyncio.sleep(0.5)  # Pause before next move



    async def stop_movement(self):
        """Stops all movement."""
        await self.dog.go_forward(0, 200)

    def stop_patrol(self):
        """Stops the patrol service."""
        logger.info("Stopping patrol...")
        self.running = False

async def main():
    dog = Go1()
    dog.init()

    # Wait for MQTT connection
    timeout = 10
    start_time = time.time()
    while not dog.mqtt.connected and (time.time() - start_time) < timeout:
        await asyncio.sleep(0.1)

    if not dog.mqtt.connected:
        logger.error("Failed to connect to robot")
        return
    
    detector = ObjectDetector()

    patrol_service = PatrolService(dog, detector)

    dog.on_go1_state_change += patrol_service.update_us_data

    detection_thread = threading.Thread(target=run_detection, args=(detector,), daemon=True)
    detection_thread.start()

    try:
        await patrol_service.start_patrol()
    except KeyboardInterrupt:
        patrol_service.stop_patrol()
    finally:
        await dog.go_forward(0, 500)  

def run_detection(detector: ObjectDetector):
    try:
        while True:
            _ = detector.detect_and_display()
            if cv2.waitKey(1) == 27:  # ESC key
                break
    finally:
        detector.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Program interrupted by user")
