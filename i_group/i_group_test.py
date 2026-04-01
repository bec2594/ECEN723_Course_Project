import json
import random

from i_group_module import RoadInfrastructure, LightStatus, Direction

# ============== Test Module ==============

class TestIGroup:
    """i-group test class"""
    
    def __init__(self):
        self.infrastructure = RoadInfrastructure()
        self.test_results = []
    
    def log_result(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            "test_name": test_name,
            "passed": passed,
            "details": details
        }
        self.test_results.append(result)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")
        if details:
            print(f"         {details}")
    
    def reset(self):
        """Reset test environment"""
        self.infrastructure = RoadInfrastructure()
    
    # ============== Test Cases ==============
    
    def test_initialization(self):
        """Test 1: Intersection initialization"""
        print("\n[Test 1] Intersection Initialization")
        self.reset()
        
        # Check intersection count
        passed = len(self.infrastructure.intersections) == 9
        self.log_result("Intersection count is 9", passed, 
                       f"Actual count: {len(self.infrastructure.intersections)}")
        
        # Check I5 (center intersection) has 4 direction lights
        i5 = self.infrastructure.intersections.get("I5")
        passed = i5 is not None and len(i5.lights) == 4
        self.log_result("I5 has 4 direction lights", passed,
                       f"I5 lights: {i5.lights if i5 else 'None'}")
        
        # Check coordinate correctness [1]
        i9 = self.infrastructure.intersections.get("I9")
        passed = i9 is not None and i9.x == 58 and i9.y == 58
        self.log_result("I9 coordinate is (58,58)", passed,
                       f"I9 coordinate: ({i9.x}, {i9.y})" if i9 else "I9 does not exist")
    
    def test_receive_vehicle_data(self):
        """Test 2: Receive vehicle data"""
        print("\n[Test 2] Receive Vehicle Data")
        self.reset()
        
        # Test normal data [1]
        test_data = json.dumps({
            "timestep": 5,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 29, "y": 29, "direction": 1, "state": 1}
            ]
        })
        
        result = self.infrastructure.receive_vehicle_data(test_data)
        self.log_result("Normal data parse success", result)
        
        passed = len(self.infrastructure.vehicles) == 2
        self.log_result("Vehicle count correct", passed,
                       f"Actual count: {len(self.infrastructure.vehicles)}")
        
        passed = self.infrastructure.timestep == 5
        self.log_result("Timestep update correct", passed,
                       f"timestep: {self.infrastructure.timestep}")
        
        # Test invalid data
        result = self.infrastructure.receive_vehicle_data("invalid json")
        self.log_result("Invalid data handled correctly", not result)
    
    def test_next_slot_detection(self):
        """Test 3: Next slot occupied detection [2]"""
        print("\n[Test 3] Next Slot Occupied Detection")
        self.reset()

        # Case 1: Front vehicle exists, but it can move away this timestep
        # V1 should NOT see next slot as occupied
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 11, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        v1 = self.infrastructure.vehicles["V1"]
        is_occupied, blocking = self.infrastructure.check_next_slot_occupied(v1)
        self.log_result(
            "Next slot NOT occupied if front vehicle can move away",
            (not is_occupied),
            f"blocking: {blocking}"
        )

        # Case 2: Next slot is NOT occupied (vehicle far away)
        self.reset()
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 20, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        v1 = self.infrastructure.vehicles["V1"]
        is_occupied, blocking = self.infrastructure.check_next_slot_occupied(v1)
        self.log_result(
            "Next slot not occupied when far away",
            not is_occupied,
            f"Distance: 10 slots, is_occupied: {is_occupied}"
        )

        # Case 3: Front vehicle exists and is blocked by red light
        # So V1 SHOULD see next slot as occupied
        self.reset()
        self.infrastructure.intersections["I2"].set_all_red()   # I2 = (29, 0)

        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 28, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 29, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        v1 = self.infrastructure.vehicles["V1"]
        is_occupied, blocking = self.infrastructure.check_next_slot_occupied(v1)
        self.log_result(
            "Detect occupied next slot when front vehicle is blocked by red light",
            is_occupied and blocking == "V2",
            f"blocking: {blocking}"
        )

        # Case 4: Vertical direction - front vehicle can move away
        self.reset()
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 10, "direction": 1, "state": 1},
                {"vehicle_id": "V2", "x": 29, "y": 11, "direction": 1, "state": 1}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        v1 = self.infrastructure.vehicles["V1"]
        is_occupied, blocking = self.infrastructure.check_next_slot_occupied(v1)
        self.log_result(
            "UP direction: next slot NOT occupied if front vehicle can move away",
            not is_occupied,
            f"blocking: {blocking}"
        )

        # Case 5: Vehicle with STOP direction should not check
        self.reset()
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 0, "state": 0},
                {"vehicle_id": "V2", "x": 11, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        v1 = self.infrastructure.vehicles["V1"]
        is_occupied, blocking = self.infrastructure.check_next_slot_occupied(v1)
        self.log_result(
            "Stopped vehicle does not check next slot",
            not is_occupied,
            f"V1 direction: STOP, is_occupied: {is_occupied}"
        )
    
    def test_traffic_light_no_cars(self):
        """Test 4: Traffic light - no cars at intersection"""
        print("\n[Test 4] Traffic Light - No Cars at Intersection")
        self.reset()
        
        # Set initial state - all red
        for intersection in self.infrastructure.intersections.values():
            intersection.set_all_red()
        
        # Get I5 initial state
        i5 = self.infrastructure.intersections["I5"]
        initial_state = dict(i5.lights)
        
        # Run algorithm with no vehicles
        self.infrastructure.traffic_light_algorithm()
        
        # Lights should not change
        final_state = dict(i5.lights)
        self.log_result("No change when no cars at intersection", 
                       initial_state == final_state,
                       f"Initial: {initial_state}, Final: {final_state}")
    
    def test_traffic_light_one_car(self):
        """Test 5: Traffic light - one car at intersection"""
        print("\n[Test 5] Traffic Light - One Car at Intersection")
        self.reset()
        
        # One car at I5 going UP
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 29, "direction": 1, "state": 1}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        self.infrastructure.traffic_light_algorithm()
        
        i5 = self.infrastructure.intersections["I5"]
        self.log_result("Single car gets green light directly", 
                       i5.lights.get("light_top") == LightStatus.GREEN,
                       f"I5 lights: {i5.lights}")
        
        # Check only one green light [2]
        green_count = sum(1 for s in i5.lights.values() if s == LightStatus.GREEN)
        self.log_result("At most one green light", green_count <= 1,
                       f"Green count: {green_count}")
    
    def test_traffic_light_multiple_cars(self):
        """Test 6: Traffic light - multiple cars at intersection with priority queue"""
        print("\n[Test 6] Traffic Light - Multiple Cars with Priority Queue")
        self.reset()
        
        # Two cars at I5: one going RIGHT, one going DOWN
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 29, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 29, "y": 29, "direction": 3, "state": 3}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        self.infrastructure.traffic_light_algorithm()
        
        i5 = self.infrastructure.intersections["I5"]
        green_dir = i5.get_green_direction()
        
        # Priority order is: top, right, down, left
        # Since no car going UP, first car with light should be RIGHT
        self.log_result("Priority queue gives RIGHT green first", 
                       green_dir == "light_right",
                       f"Green direction: {green_dir}")
        
        # Check priority queue updated - right should be at end
        self.log_result("Priority queue updated correctly",
                       i5.light_priority[-1] == "light_right",
                       f"Priority queue: {i5.light_priority}")
    
    def test_traffic_light_priority_rotation(self):
        """Test 7: Traffic light priority rotation"""
        print("\n[Test 7] Traffic Light Priority Rotation")
        self.reset()
        
        i5 = self.infrastructure.intersections["I5"]
        
        # Simulate multiple timesteps with cars in different directions
        # Step 1: Cars going RIGHT and DOWN
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 29, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 29, "y": 29, "direction": 3, "state": 3}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        self.infrastructure.traffic_light_algorithm()
        
        first_green = i5.get_green_direction()
        first_priority = list(i5.light_priority)
        
        # Step 2: Same cars, algorithm should rotate
        self.infrastructure.traffic_light_algorithm()
        second_green = i5.get_green_direction()
        
        self.log_result("First iteration gives first available direction green",
                       first_green == "light_right",
                       f"First green: {first_green}")
        
        self.log_result("Second iteration rotates to next direction",
                       second_green == "light_down",
                       f"Second green: {second_green}")
    
    def test_collision_detection(self):
        """Test 8: Collision detection [2]"""
        print("\n[Test 8] Collision Detection")
        self.reset()
        
        # Case 1: Two cars at same position
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 15, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 15, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        
        collisions = self.infrastructure.check_collisions()
        self.log_result("Collision detected", len(collisions) == 1,
                       f"Collision count: {len(collisions)}")
        
        # Case 2: No collision
        self.reset()
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 20, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        
        collisions = self.infrastructure.check_collisions()
        self.log_result("No collision case correct", len(collisions) == 0,
                       f"Collision count: {len(collisions)}")
    
    def test_red_light_violation(self):
        """Test 9: Red light violation detection [2]"""
        print("\n[Test 9] Red Light Violation Detection")
        self.reset()
        
        # Set I5 all red
        self.infrastructure.intersections["I5"].set_all_red()
        
        # Vehicle at I5 and moving
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 29, "direction": 1, "state": 1}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        
        violations = self.infrastructure.check_red_light_violations()
        self.log_result("Red light violation detected", len(violations) == 1,
                       f"Violation count: {len(violations)}")
        
        # Vehicle stopped - no violation
        self.reset()
        self.infrastructure.intersections["I5"].set_all_red()
        
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 29, "direction": 1, "state": 0}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        
        violations = self.infrastructure.check_red_light_violations()
        self.log_result("Stopped vehicle no violation", len(violations) == 0,
                       f"Violation count: {len(violations)}")
    
    def test_stop_commands(self):
        """Test 10: Stop commands generation"""
        print("\n[Test 10] Stop Commands Generation")
        self.reset()

        # Set I5 all red
        self.infrastructure.intersections["I5"].set_all_red()

        # V1 follows V2, but V2 can move away
        # V3 is at red light and should stop
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 11, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V3", "x": 29, "y": 29, "direction": 1, "state": 1}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        commands = self.infrastructure.generate_stop_commands()

        # V1 should NOT stop, because V2 can move away
        v1_stop = commands.get("V1", {}).get("should_stop", False)
        self.log_result("V1 should NOT stop because V2 can move away", not v1_stop,
                    f"V1 command: {commands.get('V1')}")

        # V3 should stop (red light)
        v3_stop = commands.get("V3", {}).get("should_stop", False)
        self.log_result("V3 should stop (red light)", v3_stop,
                    f"V3 command: {commands.get('V3')}")
        
    def test_full_simulation(self):
        """Test 11: Full simulation flow"""
        print("\n[Test 11] Full Simulation Flow")
        self.reset()
        
        # Simulate multiple timesteps
        vehicles_data = [
            {
                "timestep": 0,
                "group": "v-group",
                "vehicles": [
                    {"vehicle_id": "V1", "x": 0, "y": 58, "direction": 2, "state": 2},
                    {"vehicle_id": "V2", "x": 5, "y": 58, "direction": 2, "state": 2},
                    {"vehicle_id": "V3", "x": 29, "y": 50, "direction": 1, "state": 1},
                    {"vehicle_id": "V4", "x": 58, "y": 30, "direction": 3, "state": 3}
                ]
            },
            {
                "timestep": 1,
                "group": "v-group",
                "vehicles": [
                    {"vehicle_id": "V1", "x": 1, "y": 58, "direction": 2, "state": 2},
                    {"vehicle_id": "V2", "x": 6, "y": 58, "direction": 2, "state": 2},
                    {"vehicle_id": "V3", "x": 29, "y": 51, "direction": 1, "state": 1},
                    {"vehicle_id": "V4", "x": 58, "y": 29, "direction": 3, "state": 3}
                ]
            },
            {
                "timestep": 2,
                "group": "v-group",
                "vehicles": [
                    {"vehicle_id": "V1", "x": 2, "y": 58, "direction": 2, "state": 2},
                    {"vehicle_id": "V2", "x": 7, "y": 58, "direction": 2, "state": 2},
                    {"vehicle_id": "V3", "x": 29, "y": 52, "direction": 1, "state": 1},
                    {"vehicle_id": "V4", "x": 58, "y": 28, "direction": 3, "state": 3}
                ]
            }
        ]
        
        all_passed = True
        for data in vehicles_data:
            result = self.infrastructure.step(json.dumps(data))
            
            try:
                output = json.loads(result["output_json"])
                if "timestep" not in output or "intersections" not in output:
                    all_passed = False
            except:
                all_passed = False
        
        self.log_result("Full simulation flow executed successfully", all_passed)
        
        # Check statistics
        stats = self.infrastructure.get_statistics()
        self.log_result("Statistics generated correctly", 
                       stats["total_timesteps"] >= 3,
                       f"Statistics: {stats}")
    
    def test_multiple_vehicles_same_direction(self):
        """Test 12: Multiple vehicles same direction can move together"""
        print("\n[Test 12] Multiple Vehicles Same Direction")
        self.reset()

        # 5 vehicles on same road, same direction, adjacent slots
        # With simultaneous movement semantics, all of them should be able to move
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 5, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 6, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V3", "x": 7, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V4", "x": 8, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V5", "x": 9, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        commands = self.infrastructure.generate_stop_commands()

        for vid in ["V1", "V2", "V3", "V4", "V5"]:
            should_stop = commands.get(vid, {}).get("should_stop", False)
            self.log_result(f"{vid} should NOT stop", not should_stop,
                        f"{vid} command: {commands.get(vid)}")
    
    def test_intersection_crossing(self):
        """Test 13: Intersection crossing [2]"""
        print("\n[Test 13] Intersection Crossing")
        self.reset()
        
        # Multiple cars at intersection - at most 1 can pass [2]
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 29, "y": 29, "direction": 1, "state": 1},
                {"vehicle_id": "V2", "x": 29, "y": 29, "direction": 2, "state": 2},
                {"vehicle_id": "V3", "x": 29, "y": 29, "direction": 4, "state": 4}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        self.infrastructure.traffic_light_algorithm()
        
        i5 = self.infrastructure.intersections["I5"]
        green_count = sum(1 for s in i5.lights.values() if s == LightStatus.GREEN)
        
        self.log_result("At most one green light at intersection", green_count <= 1,
                       f"Green count: {green_count}, Lights: {i5.lights}")
    
    def test_edge_cases(self):
        """Test 14: Edge cases"""
        print("\n[Test 14] Edge Cases")
        self.reset()
        
        # Case 1: Empty vehicle list
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": []
        })
        result = self.infrastructure.receive_vehicle_data(test_data)
        self.log_result("Empty vehicle list handled correctly", 
                       result and len(self.infrastructure.vehicles) == 0)
        
        # Case 2: Vehicles at boundary positions
        self.reset()
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 0, "y": 0, "direction": 1, "state": 1},
                {"vehicle_id": "V2", "x": 58, "y": 58, "direction": 3, "state": 3}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        
        commands = self.infrastructure.generate_stop_commands()
        self.log_result("Boundary position vehicles handled correctly", 
                       "V1" in commands and "V2" in commands)
        
        # Case 3: Vehicle with STOP direction
        self.reset()
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 0, "state": 0}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)
        
        v1 = self.infrastructure.vehicles["V1"]
        is_occupied, _ = self.infrastructure.check_next_slot_occupied(v1)
        self.log_result("Stopped vehicle does not check next slot", not is_occupied)
    
    def test_high_traffic_scenario(self):
        """Test 15: High traffic scenario"""
        print("\n[Test 15] High Traffic Scenario")
        self.reset()
        
        # Create 20 vehicles high traffic scenario
        vehicles = []
        for i in range(20):
            x = (i * 3) % 58
            y = [0, 29, 58][i % 3]
            direction = [1, 2, 3, 4][i % 4]
            if direction == 0:
                direction = 2
            vehicles.append({
                "vehicle_id": f"V{i+1}",
                "x": x,
                "y": y,
                "direction": direction,
                "state": direction
            })
        
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": vehicles
        })
        
        self.infrastructure.receive_vehicle_data(test_data)
        
        passed = len(self.infrastructure.vehicles) == 20
        self.log_result("20 vehicles loaded successfully", passed,
                       f"Actual loaded: {len(self.infrastructure.vehicles)}")
        
        # Execute algorithm
        self.infrastructure.traffic_light_algorithm()
        commands = self.infrastructure.generate_stop_commands()
        
        self.log_result("High traffic stop commands generated", len(commands) == 20,
                       f"Command count: {len(commands)}")
        
        # Collision detection
        collisions = self.infrastructure.check_collisions()
        self.log_result("Collision detection completed", True,
                       f"Collision count: {len(collisions)}")
    
    def test_output_format(self):
        """Test 16: Output format validation [1]"""
        print("\n[Test 16] Output Format Validation")
        self.reset()
        
        test_data = json.dumps({
            "timestep": 5,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2}
            ]
        })
        
        result = self.infrastructure.step(test_data)
        output = json.loads(result["output_json"])
        
        # Check required fields [1]
        has_timestep = "timestep" in output
        has_group = "group" in output and output["group"] == "i-group"
        has_intersections = "intersections" in output
        
        self.log_result("Contains timestep field", has_timestep)
        self.log_result("Contains correct group field", has_group)
        self.log_result("Contains intersections field", has_intersections)
        
        # Check intersection format
        if has_intersections and len(output["intersections"]) > 0:
            intersection = output["intersections"][0]
            has_id = "intersection_id" in intersection
            has_x = "x" in intersection
            has_y = "y" in intersection
            
            self.log_result("Intersection contains id, x, y", has_id and has_x and has_y,
                           f"Example: {intersection}")
            
    def test_following_vehicle_can_move_if_front_vehicle_moves(self):
        """Test 17: following vehicle should not stop if front vehicle can move away"""
        print("\n[Test 17] Following Vehicle Can Move If Front Vehicle Moves")
        self.reset()

        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 10, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 11, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        commands = self.infrastructure.generate_stop_commands()

        v1_stop = commands.get("V1", {}).get("should_stop", False)
        v2_stop = commands.get("V2", {}).get("should_stop", False)

        self.log_result("V2 should NOT stop", not v2_stop,
                    f"V2 command: {commands.get('V2')}")
        self.log_result("V1 should NOT stop because V2 can move away", not v1_stop,
                    f"V1 command: {commands.get('V1')}")
        
    def test_red_light_blocks_entire_queue(self):
        """Test 18: red light at front blocks the whole queue behind"""
        print("\n[Test 18] Red Light Blocks Entire Queue")
        self.reset()

        # Set I2 all red, intersection at (29, 0)
        self.infrastructure.intersections["I2"].set_all_red()

        # V3 is at intersection and blocked by red light
        # V2 is directly behind V3
        # V1 is directly behind V2
        test_data = json.dumps({
            "timestep": 1,
            "group": "v-group",
            "vehicles": [
                {"vehicle_id": "V1", "x": 27, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V2", "x": 28, "y": 0, "direction": 2, "state": 2},
                {"vehicle_id": "V3", "x": 29, "y": 0, "direction": 2, "state": 2}
            ]
        })
        self.infrastructure.receive_vehicle_data(test_data)

        commands = self.infrastructure.generate_stop_commands()

        self.log_result("V3 should stop because of red light",
                    commands.get("V3", {}).get("should_stop", False),
                    f"V3 command: {commands.get('V3')}")

        self.log_result("V2 should stop because V3 cannot move",
                    commands.get("V2", {}).get("should_stop", False),
                    f"V2 command: {commands.get('V2')}")

        self.log_result("V1 should stop because V2 cannot move",
                    commands.get("V1", {}).get("should_stop", False),
                    f"V1 command: {commands.get('V1')}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("=" * 60)
        print("ECEN723 Phase A - i-group Module Complete Test")
        print("=" * 60)
        
        self.test_initialization()
        self.test_receive_vehicle_data()
        self.test_next_slot_detection()
        self.test_traffic_light_no_cars()
        self.test_traffic_light_one_car()
        self.test_traffic_light_multiple_cars()
        self.test_traffic_light_priority_rotation()
        self.test_collision_detection()
        self.test_red_light_violation()
        self.test_stop_commands()
        self.test_full_simulation()
        self.test_multiple_vehicles_same_direction()
        self.test_intersection_crossing()
        self.test_edge_cases()
        self.test_high_traffic_scenario()
        self.test_output_format()
        self.test_following_vehicle_can_move_if_front_vehicle_moves()
        self.test_red_light_blocks_entire_queue()
        
        # Statistics
        print("\n" + "=" * 60)
        print("Test Results Summary")
        print("=" * 60)
        
        passed = sum(1 for r in self.test_results if r["passed"])
        total = len(self.test_results)
        
        print(f"Passed: {passed}/{total}")
        print(f"Failed: {total - passed}/{total}")
        
        if passed == total:
            print("\n[SUCCESS] All tests passed!")
        else:
            print("\n[FAILURE] Some tests failed:")
            for r in self.test_results:
                if not r["passed"]:
                    print(f"  - {r['test_name']}: {r['details']}")
        
        return passed == total


# ============== Simulation Module ==============

class TrafficSimulation:
    """Traffic simulation class"""
    
    def __init__(self):
        self.infrastructure = RoadInfrastructure()
        self.simulation_log = []
    
    def generate_random_vehicles(self, num_vehicles: int, timestep: int) -> str:
        """Generate random vehicle data"""
        vehicles = []
        positions_used = set()
        
        # Valid road positions
        valid_positions = []
        # Horizontal roads y = 0, 29, 58
        for y in [0, 29, 58]:
            for x in range(59):
                valid_positions.append((x, y))
        # Vertical roads x = 0, 29, 58
        for x in [0, 29, 58]:
            for y in range(59):
                if (x, y) not in valid_positions:
                    valid_positions.append((x, y))
        
        for i in range(num_vehicles):
            # Select unused position
            available = [p for p in valid_positions if p not in positions_used]
            if not available:
                break
            
            pos = random.choice(available)
            positions_used.add(pos)
            
            # Determine valid directions based on position
            x, y = pos
            valid_directions = []
            
            if y in [0, 29, 58]:  # Horizontal road
                valid_directions.extend([Direction.LEFT, Direction.RIGHT])
            if x in [0, 29, 58]:  # Vertical road
                valid_directions.extend([Direction.UP, Direction.DOWN])
            
            if not valid_directions:
                valid_directions = [Direction.RIGHT]
            
            direction = random.choice(valid_directions)
            
            vehicles.append({
                "vehicle_id": f"V{i+1}",
                "x": x,
                "y": y,
                "direction": int(direction),
                "state": int(direction)
            })
        
        return json.dumps({
            "timestep": timestep,
            "group": "v-group",
            "vehicles": vehicles
        })
    
    def run_simulation(self, num_steps: int = 1000, num_vehicles: int = 100):
        """Run simulation"""
        print("=" * 60)
        print(f"Traffic Simulation: {num_steps} steps, {num_vehicles} vehicles")
        print("=" * 60)
        
        total_collisions = 0
        total_violations = 0
        
        for step in range(num_steps):
            # Generate vehicle data (in reality, received from v-group)
            vehicle_data = self.generate_random_vehicles(num_vehicles, step)
            
            # Execute one step
            result = self.infrastructure.step(vehicle_data)
            
            # Log
            collisions = len(result["collisions"])
            violations = len(result["red_light_violations"])
            total_collisions += collisions
            total_violations += violations
            
            self.simulation_log.append({
                "timestep": step,
                "collisions": collisions,
                "violations": violations,
                "stop_commands": len([c for c in result["stop_commands"].values() 
                                     if c["should_stop"]])
            })
            
            if step % 100 == 0:
                print(f"Step {step}: collisions={collisions}, violations={violations}, "
                      f"stop_commands={self.simulation_log[-1]['stop_commands']}")
        
        print("\n" + "-" * 60)
        print("Simulation Results Summary:")
        print(f"  Total timesteps: {num_steps}")
        print(f"  Total collisions: {total_collisions}")
        print(f"  Total violations: {total_violations}")
        print(f"  Final statistics: {self.infrastructure.get_statistics()}")


# ============== Utility Functions ==============

def run_tests():
    """Run all tests"""
    tester = TestIGroup()
    tester.run_all_tests()


def run_simulation():
    """Run simulation demo"""
    sim = TrafficSimulation()
    sim.run_simulation(1000, 100)


def show_system_info():
    """Display system information"""
    print("\n" + "=" * 60)
    print("System Information")
    print("=" * 60)
    
    print("\n[Coordinate System] [1]")
    print("  - Reference point: B = (0, 0)")
    print("  - X-axis direction: toward C")
    print("  - Y-axis direction: toward A")
    print("  - Grid size: 60 slots (B to C distance)")
    print("  - D coordinate: (58, 58)")
    
    print("\n[Intersection Positions]")
    infrastructure = RoadInfrastructure()
    for int_id, intersection in infrastructure.intersections.items():
        print(f"  {int_id}: ({intersection.x}, {intersection.y}) - "
              f"Light directions: {list(intersection.lights.keys())}")
    
    print("\n[State Encoding] [1]")
    print("  - STOP = 0")
    print("  - UP = 1")
    print("  - RIGHT = 2")
    print("  - DOWN = 3")
    print("  - LEFT = 4")
    
    print("\n[Traffic Light Encoding] [1]")
    print("  - GREEN = 0")
    print("  - RED = 1")
    
    print("\n[Rules] [2]")
    print("  - At most 1 green light per intersection")
    print("  - Vehicle must stop if next slot is occupied")
    print("  - Vehicle must stop at red light")
    print("  - Cannot drive in opposite direction lane")
    print("  - U-turn not allowed")

def demo_json_formats():
    """Display JSON format examples [1]"""
    print("\n" + "=" * 60)
    print("JSON Format Examples")
    print("=" * 60)
    
    # v-group -> i-group format [1]
    v_to_i_example = {
        "timestep": 12,
        "group": "v-group",
        "vehicles": [
            {
                "vehicle_id": "V1",
                "x": 10,
                "y": 0,
                "direction": 2,
                "state": 0
            },
            {
                "vehicle_id": "V2",
                "x": 30,
                "y": 20,
                "direction": 1,
                "state": 0
            }
        ]
    }
    
    print("\n[v-group -> i-group Format]")
    print(json.dumps(v_to_i_example, indent=2))
    
    # i-group -> v-group format [1]
    infrastructure = RoadInfrastructure()
    infrastructure.timestep = 12
    infrastructure.traffic_light_algorithm()
    
    print("\n[i-group -> v-group Format]")
    print(infrastructure.generate_output())
    
    # Detailed intersection format explanation
    print("\n[Intersection Light Directions]")
    print("  - light_top: Vehicle going UP (direction=1)")
    print("  - light_right: Vehicle going RIGHT (direction=2)")
    print("  - light_down: Vehicle going DOWN (direction=3)")
    print("  - light_left: Vehicle going LEFT (direction=4)")
    
    print("\n[Light Status Values]")
    print("  - 0: GREEN (vehicle can pass)")
    print("  - 1: RED (vehicle must stop)")


def show_system_info():
    """Display system information"""
    print("\n" + "=" * 60)
    print("System Information")
    print("=" * 60)
    
    print("\n[Coordinate System] [1]")
    print("  - Reference point: B = (0, 0)")
    print("  - X-axis direction: toward C")
    print("  - Y-axis direction: toward A")
    print("  - Grid size: 60 slots (B to C distance)")
    print("  - D coordinate: (58, 58)")
    
    print("\n[Intersection Positions]")
    infrastructure = RoadInfrastructure()
    for int_id, intersection in infrastructure.intersections.items():
        print(f"  {int_id}: ({intersection.x}, {intersection.y}) - "
              f"Light directions: {list(intersection.lights.keys())}")
    
    print("\n[State Encoding] [1]")
    print("  - STOP = 0")
    print("  - UP = 1")
    print("  - RIGHT = 2")
    print("  - DOWN = 3")
    print("  - LEFT = 4")
    
    print("\n[Traffic Light Encoding] [1]")
    print("  - GREEN = 0")
    print("  - RED = 1")
    
    print("\n[Rules] [2]")
    print("  - At most 1 green light per intersection")
    print("  - Vehicle must stop if next slot is occupied")
    print("  - Vehicle must stop at red light")
    print("  - Cannot drive in opposite direction lane")
    print("  - U-turn not allowed")
    
    print("\n[Traffic Light Algorithm]")
    print("  - No cars at intersection: Do not change lights")
    print("  - 1 car at intersection: Give green light directly")
    print("  - 2+ cars at intersection: Priority queue rotation")
    print("    Priority order: top -> right -> down -> left")


# ============== Main Entry ==============

def main():
    """Main entry point"""
    print("\n" + "=" * 60)
    print("ECEN723 Spring 2026 - Traffic System Project")
    print("Phase A: i-group Infrastructure Module")
    print("=" * 60)
    
    # 1. Run complete tests
    print("\n" + "=" * 60)
    print("STEP 1: Running Complete Tests")
    print("=" * 60)
    run_tests()
    
    # 2. Run simulation
    print("\n" + "=" * 60)
    print("STEP 2: Running Simulation")
    print("=" * 60)
    run_simulation()
    
    # 3. Show JSON format examples
    print("\n" + "=" * 60)
    print("STEP 3: JSON Format Examples")
    print("=" * 60)
    demo_json_formats()
    
    # 4. Show system info
    print("\n" + "=" * 60)
    print("STEP 4: System Information")
    print("=" * 60)
    show_system_info()
    
    print("\n" + "=" * 60)
    print("All tasks completed!")
    print("=" * 60)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--test":
            run_tests()
        elif arg == "--sim":
            run_simulation()
        elif arg == "--demo":
            demo_json_formats()
        elif arg == "--info":
            show_system_info()
        elif arg == "--help":
            print("Usage: python i_group.py [option]")
            print("Options:")
            print("  --test    Run complete tests")
            print("  --sim     Run simulation (1000 steps, 10 vehicles)")
            print("  --demo    Show JSON format examples")
            print("  --info    Show system information")
            print("  --help    Show this help message")
            print("  (no args) Run all tasks sequentially")
        else:
            print(f"Unknown argument: {arg}")
            print("Use --help for available options")
    else:
        main()    