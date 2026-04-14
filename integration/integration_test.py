import json
from pathlib import Path
from collections import defaultdict

# It checks:
# 1. No collision in same lane/direction
# 2. At most one green light per intersection per timestep
# 3. At most one vehicle at an intersection per timestep
# 4. No vehicle enters an intersection on red
# 5. Every vehicle visits B, C, D in any order and returns to A = (-2, 58)

V_GROUP_FILE = Path("traffic_sim_output/v_group_messages.json")
I_GROUP_FILE = Path("traffic_sim_output/i_group_messages.json")

A = (-2, 58)
A_MID = (-1, 58)
B = (0, 0)
C = (58, 0)
D = (58, 58)

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

STOP = 0
UP = 1
RIGHT = 2
DOWN = 3
LEFT = 4
GREEN = 0
RED = 1


def lane_key(position, direction):
    x, y = position
    if direction in (RIGHT, LEFT):
        return ("horizontal", y, direction)
    if direction in (UP, DOWN):
        return ("vertical", x, direction)
    return ("stopped", x, y)


def same_slot_same_lane_direction(v1, v2):
    p1 = (v1["x"], v1["y"])
    p2 = (v2["x"], v2["y"])
    if p1 != p2:
        return False
    if p1 == A:
        return False
    if p1 in INTERSECTION_IDS_BY_POS:
        return True
    return lane_key(p1, v1["direction"]) == lane_key(p2, v2["direction"])


def approach_light_name(move_direction):
    if move_direction == RIGHT:
        return "light_left"
    if move_direction == LEFT:
        return "light_right"
    if move_direction == UP:
        return "light_down"
    if move_direction == DOWN:
        return "light_top"
    return None


with open(V_GROUP_FILE, "r", encoding="utf-8") as f:
    v_data = json.load(f)

with open(I_GROUP_FILE, "r", encoding="utf-8") as f:
    i_data = json.load(f)

v_messages = v_data["messages"]
i_messages = i_data["messages"]

v_by_timestep = {msg["timestep"]: msg for msg in v_messages}
i_by_timestep = {msg["timestep"]: msg for msg in i_messages}
common_timesteps = sorted(set(v_by_timestep.keys()) & set(i_by_timestep.keys()))

collision_errors = []
light_errors = []
intersection_capacity_errors = []
red_light_errors = []
route_errors = []
final_position_errors = []

vehicle_history = defaultdict(list)
all_vehicle_ids = set()

for t in common_timesteps:
    v_msg = v_by_timestep[t]
    i_msg = i_by_timestep[t]
    vehicles = v_msg["vehicles"]
    intersections_payload = i_msg["intersections"]

    for vehicle in vehicles:
        vid = vehicle["vehicle_id"]
        all_vehicle_ids.add(vid)
        vehicle_history[vid].append(
            ((vehicle["x"], vehicle["y"]), vehicle["direction"], vehicle["state"], t)
        )

    # 1. Collision check
    for i in range(len(vehicles)):
        for j in range(i + 1, len(vehicles)):
            if same_slot_same_lane_direction(vehicles[i], vehicles[j]):
                collision_errors.append({
                    "timestep": t,
                    "vehicle_1": vehicles[i]["vehicle_id"],
                    "vehicle_2": vehicles[j]["vehicle_id"],
                    "position": (vehicles[i]["x"], vehicles[i]["y"]),
                    "direction": vehicles[i]["direction"],
                })

    # 2. At most one green per intersection
    for item in intersections_payload:
        green_count = sum(
            1 for key, value in item.items()
            if key.startswith("light_") and value == GREEN
        )
        if green_count > 1:
            light_errors.append({
                "timestep": t,
                "intersection_id": item["intersection_id"],
                "green_count": green_count,
            })

    # 3. At most one vehicle at an intersection
    vehicles_at_intersections = defaultdict(list)
    for vehicle in vehicles:
        pos = (vehicle["x"], vehicle["y"])
        if pos in INTERSECTION_IDS_BY_POS:
            vehicles_at_intersections[pos].append(vehicle["vehicle_id"])

    for pos, vehicle_ids in vehicles_at_intersections.items():
        if len(vehicle_ids) > 1:
            intersection_capacity_errors.append({
                "timestep": t,
                "intersection_id": INTERSECTION_IDS_BY_POS[pos],
                "position": pos,
                "vehicles": vehicle_ids,
            })

# 4. Red light violation check using t -> t+1 transitions
for idx in range(len(common_timesteps) - 1):
    t = common_timesteps[idx]
    t_next = common_timesteps[idx + 1]

    # Only compare consecutive timesteps
    if t_next != t + 1:
        continue

    v_now = v_by_timestep[t]
    v_next = v_by_timestep[t_next]
    i_now = i_by_timestep[t]

    next_vehicle_map = {v["vehicle_id"]: v for v in v_next["vehicles"]}
    intersection_map = {item["intersection_id"]: item for item in i_now["intersections"]}

    for vehicle in v_now["vehicles"]:
        vid = vehicle["vehicle_id"]
        if vid not in next_vehicle_map:
            continue

        current_pos = (vehicle["x"], vehicle["y"])
        next_pos = (next_vehicle_map[vid]["x"], next_vehicle_map[vid]["y"])
        direction = vehicle["direction"]

        if next_pos in INTERSECTION_IDS_BY_POS and next_pos != current_pos:
            intersection_id = INTERSECTION_IDS_BY_POS[next_pos]
            light_name = approach_light_name(direction)
            if light_name is None:
                continue

            light_state = intersection_map[intersection_id].get(light_name, GREEN)
            if light_state == RED:
                red_light_errors.append({
                    "timestep": t,
                    "vehicle_id": vid,
                    "intersection_id": intersection_id,
                    "from": current_pos,
                    "to": next_pos,
                    "direction": direction,
                })

# 5. Route validation
for vid in sorted(all_vehicle_ids):
    path = [entry[0] for entry in vehicle_history[vid]]
    visited = set(path)

    missing = []
    if B not in visited:
        missing.append("B")
    if C not in visited:
        missing.append("C")
    if D not in visited:
        missing.append("D")
    if A not in visited:
        missing.append("A(-2,58)")

    if missing:
        route_errors.append({
            "vehicle_id": vid,
            "missing": missing,
        })

    if path:
      last_position = path[-1]
      ended_at_a = (last_position == A) or (last_position == A_MID)
      if not ended_at_a:
          final_position_errors.append({
              "vehicle_id": vid,
              "last_position": last_position,
              "expected": f"{A} or {A_MID} if vehicle was removed immediately after reaching A",
          })

print("\n" + "=" * 80)
print("VALIDATION SUMMARY")
print("=" * 80)

print(f"Timesteps checked: {len(common_timesteps)}")
print(f"Vehicles observed: {len(all_vehicle_ids)}")
print(f"Same-lane collisions: {len(collision_errors)}")
print(f"Multi-green violations: {len(light_errors)}")
print(f"Multiple vehicles at one intersection: {len(intersection_capacity_errors)}")
print(f"Red-light violations: {len(red_light_errors)}")
print(f"Route completion violations: {len(route_errors)}")
print(f"Vehicles not ending at A = (-2, 58): {len(final_position_errors)}")

if (
    len(collision_errors) == 0
    and len(light_errors) == 0
    and len(intersection_capacity_errors) == 0
    and len(red_light_errors) == 0
    and len(route_errors) == 0
    and len(final_position_errors) == 0
):
    print("\nOverall result: PASS")
else:
    print("\nOverall result: FAIL")

print("\n" + "=" * 80)
print("DETAILED ERRORS")
print("=" * 80)

if collision_errors:
    print("\nSame-lane collisions:")
    for err in collision_errors[:20]:
        print(err)

if light_errors:
    print("\nMulti-green violations:")
    for err in light_errors[:20]:
        print(err)

if intersection_capacity_errors:
    print("\nMultiple vehicles at same intersection:")
    for err in intersection_capacity_errors[:20]:
        print(err)

if red_light_errors:
    print("\nRed-light violations:")
    for err in red_light_errors[:20]:
        print(err)

if route_errors:
    print("\nRoute completion violations:")
    for err in route_errors[:20]:
        print(err)

if final_position_errors:
    print("\nVehicles not ending at A = (-2, 58):")
    for err in final_position_errors[:20]:
        print(err)
