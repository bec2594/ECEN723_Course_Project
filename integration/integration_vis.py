import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from IPython.display import HTML
import numpy as np
import matplotlib as mpl

mpl.rcParams['animation.embed_limit'] = 200


V_GROUP_FILE = Path("traffic_sim_output/v_group_messages.json")
I_GROUP_FILE = Path("traffic_sim_output/i_group_messages.json")

with open(V_GROUP_FILE, "r", encoding="utf-8") as f:
    v_group_data = json.load(f)

with open(I_GROUP_FILE, "r", encoding="utf-8") as f:
    i_group_data = json.load(f)

v_messages = v_group_data["messages"]
i_messages = i_group_data["messages"]

v_by_timestep = {msg["timestep"]: msg for msg in v_messages}
i_by_timestep = {msg["timestep"]: msg for msg in i_messages}
timesteps = sorted(set(v_by_timestep.keys()) & set(i_by_timestep.keys()))
frames = [(t, v_by_timestep[t], i_by_timestep[t]) for t in timesteps]

LIGHT_COLORS = {
    0: "limegreen",
    1: "red",
}

VEHICLE_COLORS = {
    0: "gray",
    1: "royalblue",
    2: "darkorange",
    3: "seagreen",
    4: "crimson",
}

MARKERS = {
    0: "o",
    1: "^",
    2: ">",
    3: "v",
    4: "<",
}

INTERSECTION_POSITIONS = {
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

ROAD_OFFSET = 0.28


def empty_offsets():
    return np.empty((0, 2))


def lane_offset(x, y, direction):
    if direction == 2:
        return x, y - ROAD_OFFSET
    if direction == 4:
        return x, y + ROAD_OFFSET
    if direction == 1:
        return x - ROAD_OFFSET, y
    if direction == 3:
        return x + ROAD_OFFSET, y
    return x, y


fig, ax = plt.subplots(figsize=(8, 8))

for y in [0, 29, 58]:
    ax.plot([0, 58], [y, y], color="black", linewidth=8, alpha=0.15, solid_capstyle="round", zorder=0)
    ax.plot([0, 58], [y + ROAD_OFFSET, y + ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35, zorder=0)
    ax.plot([0, 58], [y - ROAD_OFFSET, y - ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35, zorder=0)

for x in [0, 29, 58]:
    ax.plot([x, x], [0, 58], color="black", linewidth=8, alpha=0.15, solid_capstyle="round", zorder=0)
    ax.plot([x + ROAD_OFFSET, x + ROAD_OFFSET], [0, 58], color="gray", linewidth=1, alpha=0.35, zorder=0)
    ax.plot([x - ROAD_OFFSET, x - ROAD_OFFSET], [0, 58], color="gray", linewidth=1, alpha=0.35, zorder=0)

ax.plot([-2, 0], [58, 58], color="black", linewidth=8, alpha=0.15, solid_capstyle="round", zorder=0)
ax.plot([-2, 0], [58 + ROAD_OFFSET, 58 + ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35, zorder=0)
ax.plot([-2, 0], [58 - ROAD_OFFSET, 58 - ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35, zorder=0)

ax.scatter([-2], [58], s=150, c="gold", edgecolors="black", zorder=2)
ax.text(-2, 59.6, "A", ha="center", fontsize=11, weight="bold")
ax.text(0, -2.8, "B", ha="center", fontsize=11, weight="bold")
ax.text(58, -2.8, "C", ha="center", fontsize=11, weight="bold")
ax.text(58, 60.2, "D", ha="center", fontsize=11, weight="bold")

ax.set_xlim(-4, 62)
ax.set_ylim(-4, 62)
ax.set_aspect("equal")
ax.grid(True, alpha=0.12)
ax.set_xlabel("x")
ax.set_ylabel("y")
title = ax.set_title("Traffic Simulation", fontsize=14, weight="bold")

light_artists = {}
for intersection_id, (x, y) in INTERSECTION_POSITIONS.items():
    light_artists[intersection_id] = {
        "light_top": ax.scatter([x], [y + 1.4], s=55, c="red", edgecolors="black", zorder=3),
        "light_right": ax.scatter([x + 1.4], [y], s=55, c="red", edgecolors="black", zorder=3),
        "light_down": ax.scatter([x], [y - 1.4], s=55, c="red", edgecolors="black", zorder=3),
        "light_left": ax.scatter([x - 1.4], [y], s=55, c="red", edgecolors="black", zorder=3),
    }

vehicle_scatters = {
    0: ax.scatter([], [], s=110, c=VEHICLE_COLORS[0], marker=MARKERS[0], edgecolors="black", zorder=4),
    1: ax.scatter([], [], s=110, c=VEHICLE_COLORS[1], marker=MARKERS[1], edgecolors="black", zorder=4),
    2: ax.scatter([], [], s=110, c=VEHICLE_COLORS[2], marker=MARKERS[2], edgecolors="black", zorder=4),
    3: ax.scatter([], [], s=110, c=VEHICLE_COLORS[3], marker=MARKERS[3], edgecolors="black", zorder=4),
    4: ax.scatter([], [], s=110, c=VEHICLE_COLORS[4], marker=MARKERS[4], edgecolors="black", zorder=4),
}

max_vehicles = max(len(v_msg["vehicles"]) for _, v_msg, _ in frames) if frames else 0
vehicle_labels = [ax.text(0, 0, "", fontsize=8, zorder=5) for _ in range(max_vehicles)]


def update(frame_index):
    timestep, v_msg, i_msg = frames[frame_index]
    title.set_text(f"Traffic Simulation | Timestep {timestep}")

    intersections = {item["intersection_id"]: item for item in i_msg["intersections"]}

    for intersection_id, payload in intersections.items():
        for light_name, artist in light_artists[intersection_id].items():
            if light_name in payload:
                artist.set_color(LIGHT_COLORS[payload[light_name]])
                artist.set_visible(True)
            else:
                artist.set_visible(False)

    grouped_positions = {0: [], 1: [], 2: [], 3: [], 4: []}
    vehicles = v_msg["vehicles"]

    for vehicle in vehicles:
        px, py = lane_offset(vehicle["x"], vehicle["y"], vehicle["direction"])
        grouped_positions[vehicle["direction"]].append([px, py])

    for direction, scatter in vehicle_scatters.items():
        if grouped_positions[direction]:
            scatter.set_offsets(np.array(grouped_positions[direction], dtype=float))
            scatter.set_visible(True)
        else:
            scatter.set_offsets(empty_offsets())
            scatter.set_visible(False)

    for i, vehicle in enumerate(vehicles):
        px, py = lane_offset(vehicle["x"], vehicle["y"], vehicle["direction"])
        vehicle_labels[i].set_position((px + 0.45, py + 0.45))
        vehicle_labels[i].set_text(vehicle["vehicle_id"])
        vehicle_labels[i].set_visible(True)

    for i in range(len(vehicles), len(vehicle_labels)):
        vehicle_labels[i].set_visible(False)

    artists = [title]
    for light_dict in light_artists.values():
        artists.extend(light_dict.values())
    artists.extend(vehicle_scatters.values())
    artists.extend(vehicle_labels)
    return artists


ani = FuncAnimation(
    fig,
    update,
    frames=len(frames),
    interval=250,
    blit=False,
    repeat=False,
)

plt.close(fig)
HTML(ani.to_jshtml())
