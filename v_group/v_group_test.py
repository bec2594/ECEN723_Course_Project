import json

STOP = 0
UP = 1
RIGHT = 2
DOWN = 3
LEFT = 4

A = (-2, 58)
B = (0, 0)
C = (58, 0)
D = (58, 58)

X_LINES = {0, 29, 58}
Y_LINES = {0, 29, 58}

INTERSECTIONS = {
    (0, 0): "I1",
    (29, 0): "I2",
    (58, 0): "I3",
    (0, 29): "I4",
    (29, 29): "I5",
    (58, 29): "I6",
    (0, 58): "I7",
    (29, 58): "I8",
    (58, 58): "I9",
}


def load_history(path: str):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "history" in data:
        return data["history"]
    return data


def is_driveable(pos):
    x, y = pos
    on_main_grid = (0 <= x <= 58 and y in Y_LINES) or (0 <= y <= 58 and x in X_LINES)
    on_a_spur = pos in {(-2, 58), (-1, 58)}
    return on_main_grid or on_a_spur


def is_intersection(pos):
    return pos in INTERSECTIONS


def move_direction(prev_pos, curr_pos):
    dx = curr_pos[0] - prev_pos[0]
    dy = curr_pos[1] - prev_pos[1]

    if dx == 0 and dy == 0:
        return STOP
    if dx == 1 and dy == 0:
        return RIGHT
    if dx == -1 and dy == 0:
        return LEFT
    if dx == 0 and dy == 1:
        return UP
    if dx == 0 and dy == -1:
        return DOWN
    return None


def is_uturn(prev_dir, new_dir):
    return (prev_dir, new_dir) in {
        (LEFT, RIGHT),
        (RIGHT, LEFT),
        (UP, DOWN),
        (DOWN, UP),
    }


def lane_key(pos, direction):
    x, y = pos
    if direction in (LEFT, RIGHT):
        return ("horizontal", y, direction)
    return ("vertical", x, direction)


def same_slot_conflict(pos_a, dir_a, pos_b, dir_b):
    if pos_a != pos_b:
        return False

    if pos_a == A:
        return False

    if is_intersection(pos_a):
        return True

    return lane_key(pos_a, dir_a) == lane_key(pos_b, dir_b)


def swap_conflict(old_a, new_a, dir_a, old_b, new_b, dir_b):
    if old_a == A or old_b == A:
        return False

    if old_a != new_b or old_b != new_a or old_a == new_a:
        return False

    if is_intersection(old_a) or is_intersection(old_b):
        return True

    return lane_key(old_a, dir_a) == lane_key(old_b, dir_b)


def main():
    history = load_history("vgroup_history.json")

    violations = {
        "bad_format": [],
        "illegal_positions": [],
        "same_slot_collisions": [],
        "swap_collisions": [],
        "illegal_steps": [],
        "direction_mismatch": [],
        "u_turns": [],
        "missing_BCD": [],
        "bad_finish": [],
    }

    if not history:
        violations["bad_format"].append("History is empty.")
        summary = {key: len(items) for key, items in violations.items()}
        summary["total_violations"] = sum(summary.values())
        print(json.dumps(summary, indent=2))
        return

    initial_ids = {v["vehicle_id"] for v in history[0]["vehicles"]}
    seen = {
        vid: {"B": False, "C": False, "D": False, "last": None, "present": False}
        for vid in initial_ids
    }

    for vehicle in history[0]["vehicles"]:
        if (vehicle["x"], vehicle["y"]) != A:
            violations["bad_format"].append(f"{vehicle['vehicle_id']} does not start at A")

    prev_positions = None
    prev_dirs = None
    all_seen_ids = set(initial_ids)

    for frame_idx, frame in enumerate(history):
        vehicles = frame["vehicles"]
        current_positions = {}
        current_dirs = {}

        for vehicle in vehicles:
            vid = vehicle["vehicle_id"]
            pos = (vehicle["x"], vehicle["y"])
            direction = vehicle["direction"]

            all_seen_ids.add(vid)
            current_positions[vid] = pos
            current_dirs[vid] = direction

            if vid not in seen:
                seen[vid] = {"B": False, "C": False, "D": False, "last": None, "present": False}

            seen[vid]["present"] = True
            seen[vid]["last"] = pos

            if pos == B:
                seen[vid]["B"] = True
            if pos == C:
                seen[vid]["C"] = True
            if pos == D:
                seen[vid]["D"] = True

            if not is_driveable(pos):
                violations["illegal_positions"].append(
                    f"frame {frame_idx}: {vid} at illegal position {pos}"
                )

        ids = sorted(current_positions)
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                v1 = ids[i]
                v2 = ids[j]
                if same_slot_conflict(
                    current_positions[v1],
                    current_dirs[v1],
                    current_positions[v2],
                    current_dirs[v2],
                ):
                    violations["same_slot_collisions"].append(
                        f"frame {frame_idx}: {v1} and {v2} conflict at {current_positions[v1]}"
                    )

        if prev_positions is not None:
            common_ids = set(prev_positions) & set(current_positions)

            for vid in common_ids:
                prev_pos = prev_positions[vid]
                curr_pos = current_positions[vid]
                prev_dir = prev_dirs[vid]
                curr_dir = current_dirs[vid]

                computed_dir = move_direction(prev_pos, curr_pos)
                if computed_dir is None:
                    violations["illegal_steps"].append(
                        f"frame {frame_idx}: {vid} made illegal jump from {prev_pos} to {curr_pos}"
                    )
                    continue

                if computed_dir != STOP and curr_dir != computed_dir:
                    violations["direction_mismatch"].append(
                        f"frame {frame_idx}: {vid} moved {computed_dir} but reported {curr_dir}"
                    )

                if computed_dir != STOP and is_uturn(prev_dir, computed_dir):
                    violations["u_turns"].append(
                        f"frame {frame_idx}: {vid} made U-turn from {prev_dir} to {computed_dir}"
                    )

            common_sorted = sorted(common_ids)
            for i in range(len(common_sorted)):
                for j in range(i + 1, len(common_sorted)):
                    v1 = common_sorted[i]
                    v2 = common_sorted[j]
                    if swap_conflict(
                        prev_positions[v1],
                        current_positions[v1],
                        prev_dirs[v1],
                        prev_positions[v2],
                        current_positions[v2],
                        prev_dirs[v2],
                    ):
                        violations["swap_collisions"].append(
                            f"frame {frame_idx}: {v1} and {v2} illegally swapped positions"
                        )

        prev_positions = current_positions
        prev_dirs = current_dirs

    final_ids = {v["vehicle_id"] for v in history[-1]["vehicles"]}

    for vid in sorted(all_seen_ids):
        if vid not in seen:
            continue

        if not (seen[vid]["B"] and seen[vid]["C"] and seen[vid]["D"]):
            violations["missing_BCD"].append(
                f"{vid} visited B={seen[vid]['B']} C={seen[vid]['C']} D={seen[vid]['D']}"
            )

        if vid in final_ids and seen[vid]["last"] != A:
            violations["bad_finish"].append(
                f"{vid} is still active at end and not at A"
            )

    summary = {key: len(items) for key, items in violations.items()}
    summary["vehicle_count"] = len(all_seen_ids)
    summary["total_violations"] = sum(summary[key] for key in violations.keys())

    print(json.dumps(summary, indent=2))

    print("\nDetailed violations:")
    for key, items in violations.items():
        if items:
            print(f"\n[{key}]")
            for item in items:
                print(item)


if __name__ == "__main__":
    main()