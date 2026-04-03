from __future__ import annotations

import json
import random
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple


# -----------------------------
# Encodings
# -----------------------------
STOP = 0
UP = 1
RIGHT = 2
DOWN = 3
LEFT = 4

GREEN = 0
RED = 1


# -----------------------------
# Map / coordinate system
# B = (0,0), C on +x, A on +y
# -----------------------------
A = (-2, 58)
A_MID = (-1, 58)
A_ENTRY = (0, 58)

B = (0, 0)
C = (58, 0)
D = (58, 58)

DESTINATIONS = (B, C, D)

X_LINES = (0, 29, 58)
Y_LINES = (0, 29, 58)

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
INTERSECTION_IDS_BY_POS = {pos: iid for iid, pos in INTERSECTIONS.items()}

DIR_TO_DELTA = {
    UP: (0, 1),
    RIGHT: (1, 0),
    DOWN: (0, -1),
    LEFT: (-1, 0),
}

LEFT_TURN = {
    UP: LEFT,
    RIGHT: UP,
    DOWN: RIGHT,
    LEFT: DOWN,
}

RIGHT_TURN = {
    UP: RIGHT,
    RIGHT: DOWN,
    DOWN: LEFT,
    LEFT: UP,
}


def is_uturn(prev_dir: int, new_dir: int) -> bool:
    return (prev_dir, new_dir) in {
        (LEFT, RIGHT),
        (RIGHT, LEFT),
        (UP, DOWN),
        (DOWN, UP),
    }


def add_step(position: Tuple[int, int], direction: int) -> Tuple[int, int]:
    dx, dy = DIR_TO_DELTA[direction]
    return position[0] + dx, position[1] + dy


def is_driveable(position: Tuple[int, int]) -> bool:
    x, y = position
    on_main_grid = (0 <= x <= 58 and y in Y_LINES) or (0 <= y <= 58 and x in X_LINES)
    on_a_spur = y == 58 and x in (-2, -1)
    return on_main_grid or on_a_spur


def is_intersection(position: Tuple[int, int]) -> bool:
    return position in INTERSECTION_IDS_BY_POS


def approach_light_name(move_direction: int) -> str:
    if move_direction == RIGHT:
        return "light_left"
    if move_direction == LEFT:
        return "light_right"
    if move_direction == UP:
        return "light_down"
    if move_direction == DOWN:
        return "light_top"
    raise ValueError("bad direction")


def lane_key(position: Tuple[int, int], direction: int) -> Tuple[str, int, int]:
    x, y = position
    if direction in (RIGHT, LEFT):
        return ("horizontal", y, direction)
    return ("vertical", x, direction)


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

    if same_lane_same_direction(pos_a, dir_a, pos_b, dir_b):
        return True

    return False


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

    if same_lane_same_direction(old_a, dir_a, old_b, dir_b):
        return True

    return False

"""
System Specification
A car can see another car in front of it on the same direction with distance no more than
0.5 miles (15 units in position)
"""
def nearest_vehicle_ahead(
    vehicle: "Vehicle",
    vehicles: Sequence["Vehicle"],
) -> Optional["Vehicle"]:
    same_lane_candidates: List[Vehicle] = []
    for other in vehicles:
        if other.vehicle_id == vehicle.vehicle_id or other.remove_next_step:
            continue
        if lane_key((other.x, other.y), other.direction) != lane_key((vehicle.x, vehicle.y), vehicle.direction):
            continue

        if vehicle.direction == RIGHT and other.y == vehicle.y and other.x > vehicle.x:
            same_lane_candidates.append(other)
        elif vehicle.direction == LEFT and other.y == vehicle.y and other.x < vehicle.x:
            same_lane_candidates.append(other)
        elif vehicle.direction == UP and other.x == vehicle.x and other.y > vehicle.y:
            same_lane_candidates.append(other)
        elif vehicle.direction == DOWN and other.x == vehicle.x and other.y < vehicle.y:
            same_lane_candidates.append(other)

    if not same_lane_candidates:
        return None

    if vehicle.direction == RIGHT:
        return min(same_lane_candidates, key=lambda other: other.x)
    if vehicle.direction == LEFT:
        return max(same_lane_candidates, key=lambda other: other.x)
    if vehicle.direction == UP:
        return min(same_lane_candidates, key=lambda other: other.y)
    return max(same_lane_candidates, key=lambda other: other.y)


def ordered_turn_directions(direction: int, turn_preference: Sequence[str]) -> List[int]:
    mapping = {
        "straight": direction,
        "left": LEFT_TURN[direction],
        "right": RIGHT_TURN[direction],
    }
    result: List[int] = []
    for label in turn_preference:
        nd = mapping[label]
        if not is_uturn(direction, nd) and nd not in result:
            result.append(nd)
    return result


def successors(
    position: Tuple[int, int],
    direction: int,
    turn_preference: Sequence[str],
) -> List[Tuple[Tuple[int, int], int]]:
    if position == A:
        return [(A_MID, RIGHT)]

    if not is_intersection(position):
        nxt = add_step(position, direction)
        if is_driveable(nxt):
            return [(nxt, direction)]
        return []

    out: List[Tuple[Tuple[int, int], int]] = []
    for nd in ordered_turn_directions(direction, turn_preference):
        nxt = add_step(position, nd)
        if is_driveable(nxt):
            out.append((nxt, nd))
    return out


def shortest_distance(
    start_pos: Tuple[int, int],
    start_dir: int,
    target_pos: Tuple[int, int],
    turn_preference: Sequence[str],
    cache: Dict[Tuple[Tuple[int, int], int, Tuple[int, int], Tuple[str, ...]], Optional[int]],
) -> Optional[int]:
    key = (start_pos, start_dir, target_pos, tuple(turn_preference))
    if key in cache:
        return cache[key]

    start_state = (start_pos, start_dir)
    queue = deque([(start_state, 0)])
    visited = {start_state}

    while queue:
        (pos, direction), dist = queue.popleft()
        if pos == target_pos:
            cache[key] = dist
            return dist

        for nxt in successors(pos, direction, turn_preference):
            if nxt not in visited:
                visited.add(nxt)
                queue.append((nxt, dist + 1))

    cache[key] = None
    return None


@dataclass
class Vehicle:
    vehicle_id: str
    destination_order: Sequence[Tuple[int, int]]
    turn_preference: Sequence[str]
    release_time: int
    x: int = A[0]
    y: int = A[1]
    direction: int = RIGHT
    state: int = STOP
    target_index: int = 0
    visited_B: bool = False
    visited_C: bool = False
    visited_D: bool = False
    completed: bool = False
    remove_next_step: bool = False

    def position(self) -> Tuple[int, int]:
        return self.x, self.y

    def current_target(self) -> Tuple[int, int]:
        if self.target_index < len(self.destination_order):
            return self.destination_order[self.target_index]
        return A

    def mark_visits(self) -> None:
        pos = self.position()
        if pos == B:
            self.visited_B = True
        elif pos == C:
            self.visited_C = True
        elif pos == D:
            self.visited_D = True

    def all_nodes_visited(self) -> bool:
        return self.visited_B and self.visited_C and self.visited_D

    def advance_target_if_needed(self) -> None:
        self.mark_visits()
        while not self.completed and self.position() == self.current_target():
            if self.target_index < len(self.destination_order):
                self.target_index += 1
            else:
                self.completed = True
                self.remove_next_step = True
                self.state = STOP
                return


class VGroupSimulator:
    def __init__(
        self,
        num_vehicles: int = 4, # changed
        release_gap: int = 4,
        seed: int = 7,
    ) -> None:
        self.rng = random.Random(seed)
        self.timestep = 0
        self.history: List[dict] = []
        self.distance_cache: Dict[
            Tuple[Tuple[int, int], int, Tuple[int, int], Tuple[str, ...]],
            Optional[int]
        ] = {}

        self.num_vehicles = num_vehicles
        self.release_gap = release_gap

        self.vehicles: List[Vehicle] = []
        for i in range(num_vehicles):
            destination_order = self.rng.sample(list(DESTINATIONS), k=len(DESTINATIONS))
            turn_preference = self.rng.sample(["straight", "left", "right"], k=3)
            release_time = i * release_gap

            self.vehicles.append(
                Vehicle(
                    vehicle_id=f"V{i+1}",
                    destination_order=destination_order,
                    turn_preference=turn_preference,
                    release_time=release_time,
                )
            )

    def all_green_message(self) -> dict:
        intersections = []
        for iid, (x, y) in INTERSECTIONS.items():
            payload = {"intersection_id": iid, "x": x, "y": y}
            if y != 58:
                payload["light_top"] = GREEN
            if x != 58:
                payload["light_right"] = GREEN
            if y != 0:
                payload["light_down"] = GREEN
            if x != 0:
                payload["light_left"] = GREEN
            intersections.append(payload)
        return {"timestep": self.timestep, "group": "i-group", "intersections": intersections}

    def light_allows_move(self, vehicle: Vehicle, next_pos: Tuple[int, int], i_group_message: dict) -> bool:
        if not is_intersection(next_pos):
            return True
        intersection = INTERSECTION_IDS_BY_POS[next_pos]
        light_state = None
        for item in i_group_message["intersections"]:
            if item["intersection_id"] == intersection:
                light_state = item
                break
        if light_state is None:
            return True
        light_name = approach_light_name(vehicle.direction)
        return light_state.get(light_name, GREEN) == GREEN

    def choose_move(
        self,
        vehicle: Vehicle,
        planned_moves: Dict[str, Tuple[Tuple[int, int], int]],
        i_group_message: dict,
    ) -> Tuple[Tuple[int, int], int]:
        if vehicle.remove_next_step:
            return vehicle.position(), vehicle.direction

        vehicle.advance_target_if_needed()
        if vehicle.completed:
            return vehicle.position(), vehicle.direction

        if self.timestep < vehicle.release_time:
            return vehicle.position(), vehicle.direction

        candidates = successors(vehicle.position(), vehicle.direction, vehicle.turn_preference)
        candidates.append((vehicle.position(), vehicle.direction))

        legal_candidates: List[Tuple[int, int, int, int]] = []

        for next_pos, next_dir in candidates:
            if is_uturn(vehicle.direction, next_dir):
                continue

            if next_pos != vehicle.position() and not self.light_allows_move(vehicle, next_pos, i_group_message):
                continue

            blocked = False

            for other in self.vehicles:
                if other.vehicle_id == vehicle.vehicle_id or other.remove_next_step:
                    continue

                other_old = other.position()

                if other.vehicle_id in planned_moves:
                    other_new, other_new_dir = planned_moves[other.vehicle_id]
                else:
                    other_new, other_new_dir = other_old, other.direction

                if same_slot_conflict(next_pos, next_dir, other_new, other_new_dir):
                    blocked = True
                    break

                if swap_conflict(
                    vehicle.position(),
                    next_pos,
                    vehicle.direction,
                    other_old,
                    other_new,
                    other.direction,
                ):
                    blocked = True
                    break

            if blocked:
                continue

            intersection_penalty = 0
            if next_pos != vehicle.position() and (is_intersection(vehicle.position()) or is_intersection(next_pos)):
                crossing_count = 0
                for other_id, (other_pos, _) in planned_moves.items():
                    other_vehicle = next(v for v in self.vehicles if v.vehicle_id == other_id)
                    if other_vehicle.position() != other_pos and (
                        is_intersection(other_vehicle.position()) or is_intersection(other_pos)
                    ):
                        crossing_count += 1
                if crossing_count >= 1:
                    intersection_penalty = 1000

            dist = shortest_distance(
                next_pos,
                next_dir,
                vehicle.current_target(),
                vehicle.turn_preference,
                self.distance_cache,
            )
            if dist is None:
                continue

            move_penalty = 0 if next_pos != vehicle.position() else 100
            legal_candidates.append((dist + move_penalty + intersection_penalty, next_pos[0], next_pos[1], next_dir))

        if not legal_candidates:
            return vehicle.position(), vehicle.direction

        legal_candidates.sort()
        _, x, y, direction = legal_candidates[0]
        return (x, y), direction

    def snapshot(self) -> dict:
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
                for vehicle in sorted(self.vehicles, key=lambda v: v.vehicle_id)
                if not vehicle.remove_next_step
            ],
        }

    def step(self) -> None:
        i_group_message = self.all_green_message()
        planned_moves: Dict[str, Tuple[Tuple[int, int], int]] = {}

        for vehicle in sorted(self.vehicles, key=lambda v: (v.release_time, v.vehicle_id)):
            next_pos, next_dir = self.choose_move(vehicle, planned_moves, i_group_message)
            planned_moves[vehicle.vehicle_id] = (next_pos, next_dir)

        for vehicle in self.vehicles:
            if vehicle.remove_next_step:
                continue

            next_pos, next_dir = planned_moves[vehicle.vehicle_id]
            old_pos = vehicle.position()
            vehicle.x, vehicle.y = next_pos
            vehicle.direction = next_dir
            vehicle.state = STOP if next_pos == old_pos else next_dir
            vehicle.advance_target_if_needed()

        self.history.append(self.snapshot())
        self.vehicles = [v for v in self.vehicles if not v.remove_next_step]
        self.timestep += 1

    def run(self, max_steps: int = 1000, output_file: str = "vgroup_history.json") -> List[dict]:
        self.history.append(self.snapshot())

        while self.vehicles and self.timestep < max_steps:
            self.step()

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2)

        return self.history


if __name__ == "__main__":
    num_vehicles = 100
    release_gap = 4

    sim = VGroupSimulator(num_vehicles=num_vehicles, release_gap=release_gap, seed=7)
    sim.run(max_steps=5000, output_file="vgroup_history.json")
    print(f"Wrote {len(sim.history)} timesteps to vgroup_history.json for {num_vehicles} vehicles")