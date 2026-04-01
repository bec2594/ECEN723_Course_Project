"""
ECEN723 Spring 2026 - Traffic System Project
Phase A: i-group Infrastructure Module
Complete Version - Vehicle stop detection, Traffic light control, Violation detection
"""

import json
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import IntEnum
import random

# ============== Constants Definition ==============

class Direction(IntEnum):
    """State encoding [1]"""
    STOP = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4

class LightStatus(IntEnum):
    """Traffic light encoding [1]"""
    GREEN = 0
    RED = 1

# System parameters
GRID_SIZE = 60  # Distance from B to C is 60 slots [1]


# ============== Data Classes ==============

@dataclass
class Vehicle:
    """Vehicle data structure"""
    vehicle_id: str
    x: int
    y: int
    direction: int
    state: int
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Vehicle':
        return cls(
            vehicle_id=data["vehicle_id"],
            x=data["x"],
            y=data["y"],
            direction=data.get("direction", Direction.STOP),
            state=data.get("state", Direction.STOP)
        )
    
    def to_dict(self) -> Dict:
        return {
            "vehicle_id": self.vehicle_id,
            "x": self.x,
            "y": self.y,
            "direction": self.direction,
            "state": self.state
        }


@dataclass
class Intersection:
    """Intersection class"""
    intersection_id: str
    x: int
    y: int
    lights: Dict[str, int] = field(default_factory=dict)
    # Priority queue for traffic light rotation: top, right, down, left
    light_priority: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        # Initialize priority queue based on available lights
        default_order = ["light_top", "light_right", "light_down", "light_left"]
        self.light_priority = [d for d in default_order if d in self.lights]
    
    def set_light(self, direction: str, status: int):
        """Set light status for specific direction"""
        if direction in self.lights:
            self.lights[direction] = status
    
    def get_light(self, direction: str) -> Optional[int]:
        """Get light status for specific direction"""
        return self.lights.get(direction, None)
    
    def set_green(self, direction: str):
        """Set specified direction to green, others to red (at most one green at any time) [2]"""
        for d in self.lights:
            self.lights[d] = LightStatus.GREEN if d == direction else LightStatus.RED
    
    def set_all_red(self):
        """Set all lights to red"""
        for d in self.lights:
            self.lights[d] = LightStatus.RED
    
    def get_green_direction(self) -> Optional[str]:
        """Get current green light direction"""
        for d, status in self.lights.items():
            if status == LightStatus.GREEN:
                return d
        return None
    
    def move_direction_to_end(self, direction: str):
        """Move the specified direction to the end of priority queue"""
        if direction in self.light_priority:
            self.light_priority.remove(direction)
            self.light_priority.append(direction)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary format"""
        result = {
            "intersection_id": self.intersection_id,
            "x": self.x,
            "y": self.y
        }
        result.update(self.lights)
        return result


@dataclass
class Violation:
    """Violation record"""
    timestep: int
    violation_type: str
    vehicle_id: str
    details: Dict


# ============== Main Module Class ==============

class RoadInfrastructure:
    """
    Road Infrastructure Class
    i-group responsibilities [1]:
    - Build the complete road infrastructure model
    - Define and maintain the map/coordinate system
    - Decide when a vehicle should stop and when it should move
    - Design the traffic light control algorithm
    - Output the traffic light status for each timestep
    """
    
    def __init__(self):
        self.timestep: int = 0
        self.intersections: Dict[str, Intersection] = {}
        self.vehicles: Dict[str, Vehicle] = {}
        self.stop_commands: Dict[str, Dict] = {}
        self.violations: List[Violation] = []
        self.collision_log: List[Dict] = []
        
        self._initialize_intersections()
    
    def _initialize_intersections(self):
        """
        Initialize 9 intersections [1]
        Coordinate system: B is (0,0), C direction is x-axis, A direction is y-axis
        D corresponds to (58,58)
        """
        intersection_configs = [
            # Bottom layer (y=0)
            ("I1", 0, 0, ["light_top", "light_right"]),
            ("I2", 29, 0, ["light_top", "light_right", "light_left"]),
            ("I3", 58, 0, ["light_top", "light_left"]),
            # Middle layer (y=29)
            ("I4", 0, 29, ["light_top", "light_right", "light_down"]),
            ("I5", 29, 29, ["light_top", "light_right", "light_down", "light_left"]),
            ("I6", 58, 29, ["light_top", "light_down", "light_left"]),
            # Top layer (y=58)
            ("I7", 0, 58, ["light_right", "light_down"]),
            ("I8", 29, 58, ["light_right", "light_down", "light_left"]),
            ("I9", 58, 58, ["light_down", "light_left"]),
        ]
        
        for int_id, x, y, directions in intersection_configs:
            intersection = Intersection(
                intersection_id=int_id,
                x=x,
                y=y,
                lights={d: LightStatus.RED for d in directions}
            )
            self.intersections[int_id] = intersection
    
    # ============== Vehicle Ahead Detection ==============
    
    def check_next_slot_occupied(self, vehicle: Vehicle) -> Tuple[bool, Optional[str]]:
        """
        Check if the next slot in front of the vehicle is occupied [2]
        Rule: A vehicle cannot move if there is another car in the next slot
        
        Returns:
            (should_stop, blocking_vehicle_id)
        """
        if vehicle.direction == Direction.STOP:
            return False, None
        
        # Calculate next slot position based on direction
        next_x, next_y = vehicle.x, vehicle.y
        
        if vehicle.direction == Direction.UP:
            next_y = vehicle.y + 1
        elif vehicle.direction == Direction.DOWN:
            next_y = vehicle.y - 1
        elif vehicle.direction == Direction.RIGHT:
            next_x = vehicle.x + 1
        elif vehicle.direction == Direction.LEFT:
            next_x = vehicle.x - 1
        
        # Check if any vehicle is at the next slot
        for other_id, other in self.vehicles.items():
            if other_id == vehicle.vehicle_id:
                continue
            
            if other.x == next_x and other.y == next_y:
                return True, other_id
        
        return False, None
    
    # ============== Traffic Light Detection ==============
    
    def check_red_light(self, vehicle: Vehicle) -> Tuple[bool, Optional[str]]:
        """
        Check if vehicle needs to stop at red light
        
        Returns:
            (should_stop, intersection_id)
        """
        for int_id, intersection in self.intersections.items():
            if vehicle.x == intersection.x and vehicle.y == intersection.y:
                # Vehicle is at intersection
                light_dir = self._direction_to_light(vehicle.direction)
                if light_dir and light_dir in intersection.lights:
                    if intersection.lights[light_dir] == LightStatus.RED:
                        return True, int_id
        
        return False, None
    
    def _direction_to_light(self, direction: int) -> Optional[str]:
        """Convert vehicle direction to corresponding light direction"""
        mapping = {
            Direction.UP: "light_top",
            Direction.RIGHT: "light_right",
            Direction.DOWN: "light_down",
            Direction.LEFT: "light_left"
        }
        return mapping.get(direction)
    
    # ============== Traffic Light Control Algorithm ==============
    
    def traffic_light_algorithm(self):
        """
        Traffic light control algorithm [1][2]
        Rules:
        - At any time, at most 1 light can be green at each intersection
        - If no cars at intersection, do not change lights
        - If only 1 car at intersection, give it green light
        - If 2+ cars at intersection, use priority queue rotation
        """
        for int_id, intersection in self.intersections.items():
            vehicles_at_intersection = self._get_vehicles_at_intersection(int_id)
            
            if len(vehicles_at_intersection) == 0:
                # No cars at intersection - do not change lights
                pass
            elif len(vehicles_at_intersection) == 1:
                # Only 1 car - give it green light directly
                vehicle = vehicles_at_intersection[0]
                light_dir = self._direction_to_light(vehicle.direction)
                if light_dir and light_dir in intersection.lights:
                    intersection.set_green(light_dir)
            else:
                # 2+ cars - use priority queue rotation
                self._priority_queue_lights(intersection, vehicles_at_intersection)
    
    def _get_vehicles_at_intersection(self, intersection_id: str) -> List[Vehicle]:
        """Get vehicles at the intersection"""
        intersection = self.intersections.get(intersection_id)
        if not intersection:
            return []
        
        vehicles_at = []
        for vehicle in self.vehicles.values():
            if vehicle.x == intersection.x and vehicle.y == intersection.y:
                vehicles_at.append(vehicle)
        
        return vehicles_at
    
    def _priority_queue_lights(self, intersection: Intersection, vehicles: List[Vehicle]):
        """
        Priority queue based traffic light control
        Order: top, right, down, left
        Find the first direction with a car and valid light, set green, move to end of queue
        """
        # Get directions that have waiting vehicles
        waiting_directions = set()
        for vehicle in vehicles:
            light_dir = self._direction_to_light(vehicle.direction)
            if light_dir:
                waiting_directions.add(light_dir)
        
        # Find the first direction in priority queue that has car and has light
        for direction in intersection.light_priority:
            if direction in waiting_directions and direction in intersection.lights:
                # Set this direction to green
                intersection.set_green(direction)
                # Move this direction to the end of priority queue
                intersection.move_direction_to_end(direction)
                break
    
    # ============== Stop Commands Generation ==============
    
    def generate_stop_commands(self) -> Dict[str, Dict]:
        """
        Determine which vehicles need to stop [2]
        Return format: {vehicle_id: {should_stop, reasons}}
        """
        self.stop_commands = {}
        
        for v_id, vehicle in self.vehicles.items():
            should_stop = False
            reasons = []
            
            # 1. Check if next slot is occupied [2]
            next_occupied, blocking_id = self.check_next_slot_occupied(vehicle)
            if next_occupied:
                should_stop = True
                reasons.append(f"Next slot occupied by {blocking_id}")
            
            # 2. Check red light
            at_red_light, int_id = self.check_red_light(vehicle)
            if at_red_light:
                should_stop = True
                reasons.append(f"Red light at intersection {int_id}")
            
            self.stop_commands[v_id] = {
                "should_stop": should_stop,
                "reasons": reasons
            }
        
        return self.stop_commands
    
    # ============== Violation Detection ==============
    
    def check_collisions(self) -> List[Dict]:
        """
        Detect collisions [2]
        If at any moment there is more than one car in the same slot, it counts as collision
        """
        collisions = []
        positions = {}
        
        for v_id, vehicle in self.vehicles.items():
            pos = (vehicle.x, vehicle.y)
            if pos in positions:
                collision = {
                    "timestep": self.timestep,
                    "position": pos,
                    "vehicles": [positions[pos], v_id],
                    "type": "collision"
                }
                collisions.append(collision)
                self.collision_log.append(collision)
            else:
                positions[pos] = v_id
        
        return collisions
    
    def check_red_light_violations(self) -> List[Dict]:
        """
        Detect red light violations [2]
        A car must stop at red light
        """
        violations = []
        
        for v_id, vehicle in self.vehicles.items():
            # Vehicle must be in moving state to count as violation
            if vehicle.state == Direction.STOP:
                continue
            
            at_red_light, int_id = self.check_red_light(vehicle)
            if at_red_light:
                violation = {
                    "timestep": self.timestep,
                    "vehicle_id": v_id,
                    "intersection_id": int_id,
                    "type": "red_light_violation"
                }
                violations.append(violation)
                self.violations.append(Violation(
                    timestep=self.timestep,
                    violation_type="red_light",
                    vehicle_id=v_id,
                    details={"intersection_id": int_id}
                ))
        
        return violations
    
    def check_opposite_direction(self) -> List[Dict]:
        """
        Detect opposite direction driving [2]
        A car cannot run in a lane opposite its driving direction
        """
        violations = []
        
        for v_id, vehicle in self.vehicles.items():
            is_violation = False
            
            # On horizontal road
            if vehicle.y in [0, 29, 58]:
                # Check if moving in vertical direction (except at intersection)
                if vehicle.x not in [0, 29, 58]:
                    if vehicle.direction in [Direction.UP, Direction.DOWN]:
                        is_violation = True
            
            # On vertical road
            if vehicle.x in [0, 29, 58]:
                # Check if moving in horizontal direction (except at intersection)
                if vehicle.y not in [0, 29, 58]:
                    if vehicle.direction in [Direction.LEFT, Direction.RIGHT]:
                        is_violation = True
            
            if is_violation:
                violation = {
                    "timestep": self.timestep,
                    "vehicle_id": v_id,
                    "position": (vehicle.x, vehicle.y),
                    "direction": vehicle.direction,
                    "type": "opposite_direction"
                }
                violations.append(violation)
        
        return violations
    
    # ============== Communication Interface ==============
    
    def receive_vehicle_data(self, json_data: str) -> bool:
        """
        Receive vehicle data from v-group [1]
        Format includes: timestep, group, vehicles array
        """
        try:
            data = json.loads(json_data)
            self.timestep = data.get("timestep", self.timestep)
            
            # Clear and reload vehicle data
            self.vehicles.clear()
            for v_data in data.get("vehicles", []):
                vehicle = Vehicle.from_dict(v_data)
                self.vehicles[vehicle.vehicle_id] = vehicle
            
            print(f"[i-group] Received timestep {self.timestep} vehicle data, total {len(self.vehicles)} vehicles")
            return True
            
        except json.JSONDecodeError as e:
            print(f"[i-group] JSON parse error: {e}")
            return False
        except Exception as e:
            print(f"[i-group] Data processing error: {e}")
            return False
    
    def generate_output(self) -> str:
        """
        Generate output JSON format [1]
        Compliant with meeting record defined i-group -> v-group format
        """
        output = {
            "timestep": self.timestep,
            "group": "i-group",
            "intersections": [
                intersection.to_dict() 
                for intersection in self.intersections.values()
            ],
            "stop_commands": self.stop_commands
        }
        return json.dumps(output, indent=2)
    
    def step(self, vehicle_json: Optional[str] = None) -> Dict:
        """
        Execute one time step
        Returns: Dictionary containing output data and detection results
        """
        # 1. Receive vehicle data
        if vehicle_json:
            self.receive_vehicle_data(vehicle_json)
        
        # 2. Execute traffic light control algorithm
        self.traffic_light_algorithm()
        
        # 3. Generate stop commands
        self.generate_stop_commands()
        
        # 4. Detect violations
        collisions = self.check_collisions()
        red_light_violations = self.check_red_light_violations()
        opposite_violations = self.check_opposite_direction()
        
        # 5. Output results
        result = {
            "output_json": self.generate_output(),
            "collisions": collisions,
            "red_light_violations": red_light_violations,
            "opposite_direction_violations": opposite_violations,
            "stop_commands": self.stop_commands
        }
        
        # 6. Update timestep
        self.timestep += 1
        
        return result
    
    def get_statistics(self) -> Dict:
        """Get statistics data"""
        return {
            "total_timesteps": self.timestep,
            "total_collisions": len(self.collision_log),
            "total_violations": len(self.violations),
            "current_vehicles": len(self.vehicles)
        }
