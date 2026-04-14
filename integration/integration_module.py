from __future__ import annotations

import json
import random
from collections import deque
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple


class Direction(IntEnum):
    STOP = 0
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4


class LightStatus(IntEnum):
    GREEN = 0
    RED = 1


GRID_MAX = 58
X_LINES = (0, 29, 58)
Y_LINES = (0, 29, 58)

A = (-2, 58)
A_MID = (-1, 58)
B = (0, 0)
C = (58, 0)
D = (58, 58)
DESTINATIONS = (B, C, D)

INTERSECTIONS = {
    "I1": (0, 0),
    "I2": (29, 0),
    "I3": (58, 0),
    "I4": (0, 29),
    "I5": (29, 29),
    "I6": (58, 29),
    "I7": (0, 58),
    "I8": (29, 58),
    "I9": (58, 58),
}
INTERSECTION_IDS_BY_POS = {position: intersection_id for intersection_id, position in INTERSECTIONS.items()}

DIR_TO_DELTA = {
    Direction.UP: (0, 1),
    Direction.RIGHT: (1, 0),
    Direction.DOWN: (0, -1),
    Direction.LEFT: (-1, 0),
}

LEFT_TURN = {
    Direction.UP: Direction.LEFT,
    Direction.RIGHT: Direction.UP,
    Direction.DOWN: Direction.RIGHT,
    Direction.LEFT: Direction.DOWN,
}

RIGHT_TURN = {
    Direction.UP: Direction.RIGHT,
    Direction.RIGHT: Direction.DOWN,
    Direction.DOWN: Direction.LEFT,
    Direction.LEFT: Direction.UP,
}


def is_intersection(position: Tuple[int, int]) -> bool:
    return position in INTERSECTION_IDS_BY_POS


def is_driveable(position: Tuple[int, int]) -> bool:
    x, y = position
    on_main_grid = (0 <= x <= GRID_MAX and y in Y_LINES) or (0 <= y <= GRID_MAX and x in X_LINES)
    on_a_spur = y == 58 and x in (-2, -1)
    return on_main_grid or on_a_spur


def add_step(position: Tuple[int, int], direction: int) -> Tuple[int, int]:
    dx, dy = DIR_TO_DELTA[Direction(direction)]
    return position[0] + dx, position[1] + dy


def is_uturn(previous_direction: int, new_direction: int) -> bool:
    return (Direction(previous_direction), Direction(new_direction)) in {
        (Direction.LEFT, Direction.RIGHT),
        (Direction.RIGHT, Direction.LEFT),
        (Direction.UP, Direction.DOWN),
        (Direction.DOWN, Direction.UP),
    }


def approach_light_name(move_direction: int) -> str:
    direction = Direction(move_direction)
    if direction == Direction.RIGHT:
        return "light_left"
    if direction == Direction.LEFT:
        return "light_right"
    if direction == Direction.UP:
        return "light_down"
    if direction == Direction.DOWN:
        return "light_top"
    raise ValueError(f"Unsupported direction for light lookup: {move_direction}")


def lane_key(position: Tuple[int, int], direction: int) -> Tuple[str, int, int]:
    x, y = position
    direction_enum = Direction(direction)
    if direction_enum in (Direction.RIGHT, Direction.LEFT):
        return ("horizontal", y, int(direction_enum))
    return ("vertical", x, int(direction_enum))


def same_lane_same_direction(
    pos_a: Tuple[int, int],
    dir_a: int,
    pos_b: Tuple[int, int],
    dir_b: int,
) -> bool:
    return lane_key(pos_a, dir_a) == lane_key(pos_b, dir_b)


def same_slot_conflict(
    pos_a: Tuple[int, int],
    dir_a: int,
    pos_b: Tuple[int, int],
    dir_b: int,
) -> bool:
    if pos_a != pos_b:
        return False
    if pos_a == A:
        return False
    if is_intersection(pos_a):
        return True
    return same_lane_same_direction(pos_a, dir_a, pos_b, dir_b)


def swap_conflict(
    old_a: Tuple[int, int],
    new_a: Tuple[int, int],
    dir_a: int,
    old_b: Tuple[int, int],
    new_b: Tuple[int, int],
    dir_b: int,
) -> bool:
    if old_a == A or old_b == A:
        return False
    if old_a != new_b or old_b != new_a or old_a == new_a:
        return False
    if is_intersection(old_a) or is_intersection(old_b):
        return True
    return same_lane_same_direction(old_a, dir_a, old_b, dir_b)


def ordered_turn_directions(direction: int, turn_preference: Sequence[str]) -> List[int]:
    direction_enum = Direction(direction)
    mapping = {
        "straight": direction_enum,
        "left": LEFT_TURN[direction_enum],
        "right": RIGHT_TURN[direction_enum],
    }
    result: List[int] = []
    for label in turn_preference:
        candidate = mapping[label]
        if not is_uturn(direction_enum, candidate) and int(candidate) not in result:
            result.append(int(candidate))
    return result


def successors(
    position: Tuple[int, int],
    direction: int,
    turn_preference: Sequence[str],
) -> List[Tuple[Tuple[int, int], int]]:
    if position == A:
        return [(A_MID, int(Direction.RIGHT))]

    if not is_intersection(position):
        next_position = add_step(position, direction)
        if is_driveable(next_position):
            return [(next_position, direction)]
        return []

    result: List[Tuple[Tuple[int, int], int]] = []
    for next_direction in ordered_turn_directions(direction, turn_preference):
        next_position = add_step(position, next_direction)
        if is_driveable(next_position):
            result.append((next_position, next_direction))
    return result


def shortest_distance(
    start_position: Tuple[int, int],
    start_direction: int,
    target_position: Tuple[int, int],
    turn_preference: Sequence[str],
    cache: Dict[Tuple[Tuple[int, int], int, Tuple[int, int], Tuple[str, ...]], Optional[int]],
) -> Optional[int]:
    key = (start_position, start_direction, target_position, tuple(turn_preference))
    if key in cache:
        return cache[key]

    start_state = (start_position, start_direction)
    queue = deque([(start_state, 0)])
    visited = {start_state}

    while queue:
        (position, direction), distance = queue.popleft()
        if position == target_position:
            cache[key] = distance
            return distance

        for next_state in successors(position, direction, turn_preference):
            if next_state not in visited:
                visited.add(next_state)
                queue.append((next_state, distance + 1))

    cache[key] = None
    return None


@dataclass
class VehicleState:
    vehicle_id: str
    x: int
    y: int
    direction: int
    state: int

    def position(self) -> Tuple[int, int]:
        return self.x, self.y

    @classmethod
    def from_dict(cls, data: Dict) -> "VehicleState":
        return cls(
            vehicle_id=data["vehicle_id"],
            x=data["x"],
            y=data["y"],
            direction=data.get("direction", int(Direction.STOP)),
            state=data.get("state", int(Direction.STOP)),
        )


@dataclass
class Intersection:
    intersection_id: str
    x: int
    y: int
    lights: Dict[str, int]
    light_priority: List[str] = field(default_factory=list)
    active_green: Optional[str] = None
    green_duration: int = 0
    min_green_time: int = 10
    max_green_time: int = 20

    def __post_init__(self) -> None:
        default_priority = ["light_top", "light_right", "light_down", "light_left"]
        self.light_priority = [light for light in default_priority if light in self.lights]

    def set_green(self, green_light: str) -> None:
        for light_name in self.lights:
            self.lights[light_name] = int(LightStatus.GREEN if light_name == green_light else LightStatus.RED)
        if self.active_green == green_light:
            self.green_duration += 1
        else:
            self.active_green = green_light
            self.green_duration = 1

    def move_priority_to_end(self, light_name: str) -> None:
        if light_name in self.light_priority:
            self.light_priority.remove(light_name)
            self.light_priority.append(light_name)

    def to_dict(self) -> Dict:
        payload = {
            "intersection_id": self.intersection_id,
            "x": self.x,
            "y": self.y,
        }
        payload.update(self.lights)
        return payload


class RoadInfrastructure:
    def __init__(self) -> None:
        self.timestep = 0
        self.intersections = self._build_intersections()
        self.vehicles: Dict[str, VehicleState] = {}
        self.stop_commands: Dict[str, Dict] = {}
        self.collision_log: List[Dict] = []

    def _build_intersections(self) -> Dict[str, Intersection]:
        configs = [
            ("I1", 0, 0, ["light_top", "light_right"]),
            ("I2", 29, 0, ["light_top", "light_right", "light_left"]),
            ("I3", 58, 0, ["light_top", "light_left"]),
            ("I4", 0, 29, ["light_top", "light_right", "light_down"]),
            ("I5", 29, 29, ["light_top", "light_right", "light_down", "light_left"]),
            ("I6", 58, 29, ["light_top", "light_down", "light_left"]),
            ("I7", 0, 58, ["light_right", "light_down"]),
            ("I8", 29, 58, ["light_right", "light_down", "light_left"]),
            ("I9", 58, 58, ["light_down", "light_left"]),
        ]
        intersections: Dict[str, Intersection] = {}
        for intersection_id, x, y, light_names in configs:
            intersections[intersection_id] = Intersection(
                intersection_id=intersection_id,
                x=x,
                y=y,
                lights={light_name: int(LightStatus.RED) for light_name in light_names},
            )
        return intersections

    def receive_vehicle_message(self, message: Dict) -> None:
        self.timestep = message["timestep"]
        self.vehicles = {
            vehicle_data["vehicle_id"]: VehicleState.from_dict(vehicle_data)
            for vehicle_data in message.get("vehicles", [])
        }

    def approaching_intersection(self, vehicle: VehicleState) -> Optional[Tuple[Intersection, str]]:
        if vehicle.direction == int(Direction.STOP):
            return None
        next_position = add_step(vehicle.position(), vehicle.direction)
        intersection_id = INTERSECTION_IDS_BY_POS.get(next_position)
        if not intersection_id:
            return None
        intersection = self.intersections[intersection_id]
        light_name = approach_light_name(vehicle.direction)
        if light_name not in intersection.lights:
            return None
        return intersection, light_name

    def _choose_next_green(
        self,
        intersection: Intersection,
        counts: Dict[str, int],
        best_count: int,
    ) -> Optional[str]:
        for light_name in intersection.light_priority:
            if counts.get(light_name, 0) == best_count and best_count > 0:
                return light_name
        for light_name in intersection.light_priority:
            if counts.get(light_name, 0) > 0:
                return light_name
        return intersection.active_green

    def update_lights(self) -> None:
      waiting_counts = {
          intersection_id: {light_name: 0 for light_name in intersection.lights}
          for intersection_id, intersection in self.intersections.items()
      }

      # Count vehicles waiting at each light
      for vehicle in self.vehicles.values():
          approach_info = self.approaching_intersection(vehicle)
          if approach_info is None:
              continue
          intersection, light_name = approach_info
          waiting_counts[intersection.intersection_id][light_name] += 1

      for intersection_id, intersection in self.intersections.items():
          counts = waiting_counts[intersection_id]
          total_waiting = sum(counts.values())

          # If no cars → keep current light (no unnecessary switching)
          if total_waiting == 0:
              if intersection.active_green is not None:
                  intersection.set_green(intersection.active_green)
              continue

          current_green = intersection.active_green
          current_count = counts.get(current_green, 0) if current_green else 0

          # 🚦 CASE 1: No active green yet → pick best
          if current_green is None:
              best_light = max(counts, key=lambda l: counts[l])
              intersection.set_green(best_light)
              intersection.move_priority_to_end(best_light)
              continue

          # 🚦 CASE 2: Enforce minimum green time (HARD CONSTRAINT)
          if intersection.green_duration < intersection.min_green_time:
              intersection.set_green(current_green)
              continue

          # 🚦 CASE 3: If cars still flowing → extend green (like real signals)
          if current_count > 0 and intersection.green_duration < intersection.max_green_time:
              intersection.set_green(current_green)
              continue

          # 🚦 CASE 4: Switch only if another direction has significantly more demand
          best_light = max(counts, key=lambda l: counts[l])
          best_count = counts[best_light]

          # Avoid unnecessary switching if similar load
          if best_light != current_green and best_count > current_count:
              intersection.set_green(best_light)
              intersection.move_priority_to_end(best_light)
          else:
              # Otherwise keep current to avoid oscillation
              intersection.set_green(current_green)


    def next_slot_blocked(self, vehicle: VehicleState) -> Optional[str]:
        if vehicle.direction == int(Direction.STOP):
            return None
        next_position = add_step(vehicle.position(), vehicle.direction)
        for other in self.vehicles.values():
            if other.vehicle_id == vehicle.vehicle_id:
                continue
            if same_slot_conflict(next_position, vehicle.direction, other.position(), other.direction):
                return other.vehicle_id
        return None

    def red_light_stop(self, vehicle: VehicleState) -> Optional[str]:
        approach_info = self.approaching_intersection(vehicle)
        if approach_info is None:
            return None
        intersection, light_name = approach_info
        if intersection.lights[light_name] == int(LightStatus.RED):
            return intersection.intersection_id
        return None

    def generate_stop_commands(self) -> Dict[str, Dict]:
        commands: Dict[str, Dict] = {}
        for vehicle in self.vehicles.values():
            reasons: List[str] = []
            blocker = self.next_slot_blocked(vehicle)
            if blocker is not None:
                reasons.append(f"Next slot occupied by {blocker}")
            red_light_intersection = self.red_light_stop(vehicle)
            if red_light_intersection is not None:
                reasons.append(f"Red light at {red_light_intersection}")
            commands[vehicle.vehicle_id] = {
                "should_stop": bool(reasons),
                "reasons": reasons,
            }
        self.stop_commands = commands
        return commands

    def detect_collisions(self) -> List[Dict]:
        collisions: List[Dict] = []
        vehicle_list = list(self.vehicles.values())
        seen_pairs = set()

        for i, vehicle_a in enumerate(vehicle_list):
            for vehicle_b in vehicle_list[i + 1:]:
                if not same_slot_conflict(
                    vehicle_a.position(),
                    vehicle_a.direction,
                    vehicle_b.position(),
                    vehicle_b.direction,
                ):
                    continue

                key = tuple(sorted((vehicle_a.vehicle_id, vehicle_b.vehicle_id)))
                if key in seen_pairs:
                    continue
                seen_pairs.add(key)

                record = {
                    "timestep": self.timestep,
                    "position": [vehicle_a.x, vehicle_a.y],
                    "vehicles": [vehicle_a.vehicle_id, vehicle_b.vehicle_id],
                    "type": "collision",
                }
                collisions.append(record)
                self.collision_log.append(record)
        return collisions

    def build_i_group_message(self) -> Dict:
        return {
            "timestep": self.timestep,
            "group": "i-group",
            "intersections": [intersection.to_dict() for intersection in self.intersections.values()],
            "stop_commands": self.stop_commands,
        }

    def step(self, vehicle_message: Dict) -> Dict:
        self.receive_vehicle_message(vehicle_message)
        self.update_lights()
        self.generate_stop_commands()
        collisions = self.detect_collisions()
        return {
            "i_group_message": self.build_i_group_message(),
            "collisions": collisions,
        }


@dataclass
class Vehicle:
    vehicle_id: str
    destination_order: Sequence[Tuple[int, int]]
    turn_preference: Sequence[str]
    release_time: int
    x: int = A[0]
    y: int = A[1]
    direction: int = int(Direction.RIGHT)
    state: int = int(Direction.STOP)
    target_index: int = 0
    completed: bool = False

    def position(self) -> Tuple[int, int]:
        return self.x, self.y

    def route_targets(self) -> List[Tuple[int, int]]:
        return [*self.destination_order, A]

    def current_target(self) -> Tuple[int, int]:
        return self.route_targets()[self.target_index]

    def advance_target_if_needed(self) -> None:
        while not self.completed and self.position() == self.current_target():
            self.target_index += 1
            if self.target_index >= len(self.route_targets()):
                self.completed = True
                self.state = int(Direction.STOP)
                return


class VGroupSimulator:
    def __init__(self, num_vehicles: int = 12, release_gap: int = 4, seed: int = 7) -> None:
        self.rng = random.Random(seed)
        self.timestep = 0
        self.vehicles: List[Vehicle] = []
        self.distance_cache: Dict[
            Tuple[Tuple[int, int], int, Tuple[int, int], Tuple[str, ...]],
            Optional[int],
        ] = {}

        for index in range(num_vehicles):
            destination_order = self.rng.sample(list(DESTINATIONS), k=len(DESTINATIONS))
            turn_preference = self.rng.sample(["straight", "left", "right"], k=3)
            self.vehicles.append(
                Vehicle(
                    vehicle_id=f"V{index + 1}",
                    destination_order=destination_order,
                    turn_preference=turn_preference,
                    release_time=index * release_gap,
                )
            )

    def released_vehicles(self) -> List[Vehicle]:
        return [
            vehicle
            for vehicle in self.vehicles
            if not vehicle.completed and self.timestep >= vehicle.release_time
        ]

    def has_remaining_vehicles(self) -> bool:
        return any(not vehicle.completed for vehicle in self.vehicles)

    def snapshot(self) -> Dict:
        return {
            "timestep": self.timestep,
            "group": "v-group",
            "vehicles": [
                {
                    "vehicle_id": vehicle.vehicle_id,
                    "x": vehicle.x,
                    "y": vehicle.y,
                    "direction": vehicle.direction,
                    "state": vehicle.state,
                }
                for vehicle in sorted(self.released_vehicles(), key=lambda item: item.vehicle_id)
            ],
        }

    def light_allows_move(self, vehicle: Vehicle, next_position: Tuple[int, int], i_group_message: Dict) -> bool:
        if not is_intersection(next_position):
            return True
        intersection_id = INTERSECTION_IDS_BY_POS[next_position]
        light_payload = next(
            item for item in i_group_message["intersections"] if item["intersection_id"] == intersection_id
        )
        light_name = approach_light_name(vehicle.direction)
        return light_payload.get(light_name, int(LightStatus.GREEN)) == int(LightStatus.GREEN)

    def choose_move(
        self,
        vehicle: Vehicle,
        current_states: Dict[str, Tuple[Tuple[int, int], int]],
        planned_moves: Dict[str, Tuple[Tuple[int, int], int]],
        i_group_message: Dict,
    ) -> Tuple[Tuple[int, int], int]:
        vehicle.advance_target_if_needed()
        if vehicle.completed or self.timestep < vehicle.release_time:
            return vehicle.position(), vehicle.direction

        candidates = successors(vehicle.position(), vehicle.direction, vehicle.turn_preference)
        candidates.append((vehicle.position(), vehicle.direction))
        scored_candidates: List[Tuple[int, int, int, int]] = []

        for next_position, next_direction in candidates:
            if is_uturn(vehicle.direction, next_direction):
                continue

            if next_position != vehicle.position() and not self.light_allows_move(vehicle, next_position, i_group_message):
                continue

            blocked = False
            for other_vehicle_id, (other_position, other_direction) in current_states.items():
                if other_vehicle_id == vehicle.vehicle_id:
                    continue

                if other_vehicle_id in planned_moves:
                    other_next_position, other_next_direction = planned_moves[other_vehicle_id]
                else:
                    other_next_position, other_next_direction = other_position, other_direction

                if same_slot_conflict(next_position, next_direction, other_next_position, other_next_direction):
                    blocked = True
                    break

                if swap_conflict(
                    vehicle.position(),
                    next_position,
                    vehicle.direction,
                    other_position,
                    other_next_position,
                    other_direction,
                ):
                    blocked = True
                    break

            if blocked:
                continue

            distance = shortest_distance(
                next_position,
                next_direction,
                vehicle.current_target(),
                vehicle.turn_preference,
                self.distance_cache,
            )
            if distance is None:
                continue

            wait_penalty = 100 if next_position == vehicle.position() else 0
            scored_candidates.append((distance + wait_penalty, next_position[0], next_position[1], next_direction))

        if not scored_candidates:
            return vehicle.position(), vehicle.direction

        scored_candidates.sort()
        _, x, y, next_direction = scored_candidates[0]
        return (x, y), next_direction

    def apply_step(self, i_group_message: Dict) -> Dict:
        current_states = {
            vehicle.vehicle_id: (vehicle.position(), vehicle.direction)
            for vehicle in self.released_vehicles()
        }
        planned_moves: Dict[str, Tuple[Tuple[int, int], int]] = {}

        for vehicle in sorted(self.released_vehicles(), key=lambda item: (item.release_time, item.vehicle_id)):
            planned_moves[vehicle.vehicle_id] = self.choose_move(
                vehicle,
                current_states,
                planned_moves,
                i_group_message,
            )

        for vehicle in self.released_vehicles():
            next_position, next_direction = planned_moves[vehicle.vehicle_id]
            previous_position = vehicle.position()
            vehicle.x, vehicle.y = next_position
            vehicle.direction = next_direction
            vehicle.state = int(Direction.STOP) if next_position == previous_position else next_direction
            vehicle.advance_target_if_needed()

        self.vehicles = [vehicle for vehicle in self.vehicles if not vehicle.completed]
        self.timestep += 1
        return self.snapshot()


class CombinedTrafficSimulator:
    def __init__(
        self,
        num_vehicles: int = 12,
        release_gap: int = 4,
        max_steps: int = 300,
        seed: int = 7,
        output_dir: str = "traffic_sim_output",
    ) -> None:
        self.max_steps = max_steps
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.v_group_log_path = self.output_dir / "v_group_messages.json"
        self.i_group_log_path = self.output_dir / "i_group_messages.json"

        self.v_group = VGroupSimulator(num_vehicles=num_vehicles, release_gap=release_gap, seed=seed)
        self.i_group = RoadInfrastructure()
        self.history: List[Dict] = []

        self._initialize_message_logs()

    def _write_json(self, path: Path, payload: Dict) -> None:
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _read_json(self, path: Path) -> Dict:
        return json.loads(path.read_text(encoding="utf-8"))

    def _initialize_message_logs(self) -> None:
        self._write_json(self.v_group_log_path, {"group": "v-group", "messages": []})
        self._write_json(self.i_group_log_path, {"group": "i-group", "messages": []})

    def _append_message(self, path: Path, message: Dict) -> None:
        payload = self._read_json(path)
        payload["messages"].append(message)
        self._write_json(path, payload)

    def _read_latest_message(self, path: Path) -> Dict:
        payload = self._read_json(path)
        messages = payload.get("messages", [])
        if not messages:
            raise ValueError(f"No messages found in {path}")
        return messages[-1]

    def run(self) -> Dict:
        while self.v_group.has_remaining_vehicles() and self.v_group.timestep < self.max_steps:
            timestep = self.v_group.timestep

            v_message = self.v_group.snapshot()
            self._append_message(self.v_group_log_path, v_message)

            i_input = self._read_latest_message(self.v_group_log_path)
            i_result = self.i_group.step(i_input)
            i_message = i_result["i_group_message"]
            self._append_message(self.i_group_log_path, i_message)

            v_input = self._read_latest_message(self.i_group_log_path)
            post_move_snapshot = self.v_group.apply_step(v_input)

            self.history.append(
                {
                    "timestep": timestep,
                    "vehicles_before_move": v_message,
                    "i_group_message": i_message,
                    "vehicles_after_move": post_move_snapshot,
                    "collisions_detected": i_result["collisions"],
                }
            )

        summary = {
            "completed_timesteps": len(self.history),
            "remaining_vehicles": len([vehicle for vehicle in self.v_group.vehicles if not vehicle.completed]),
            "collisions_logged_by_i_group": len(self.i_group.collision_log),
            "history_file": str(self.output_dir / "combined_history.json"),
            "v_group_messages_file": str(self.v_group_log_path),
            "i_group_messages_file": str(self.i_group_log_path),
            "final_v_state_file": str(self.output_dir / "final_v_state.json"),
            "final_i_state_file": str(self.output_dir / "final_i_state.json"),
        }

        self._write_json(self.output_dir / "combined_history.json", {"history": self.history, "summary": summary})
        self._write_json(self.output_dir / "final_v_state.json", self.v_group.snapshot())
        self._write_json(self.output_dir / "final_i_state.json", self.i_group.build_i_group_message())
        self._write_json(self.output_dir / "summary.json", summary)
        return summary


# Colab-friendly run cell
simulator = CombinedTrafficSimulator(
    num_vehicles=100,
    release_gap=4,
    max_steps=100000,
    seed=7,
    output_dir="traffic_sim_output",
)

summary = simulator.run()
print(json.dumps(summary, indent=2))
