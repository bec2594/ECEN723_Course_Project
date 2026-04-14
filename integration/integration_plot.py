import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from ipywidgets import interact, IntSlider

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

LIGHT_COLORS = {0: "limegreen", 1: "red"}
VEHICLE_COLORS = {0: "gray", 1: "royalblue", 2: "darkorange", 3: "seagreen", 4: "crimson"}
MARKERS = {0: "o", 1: "^", 2: ">", 3: "v", 4: "<"}

INTERSECTION_POSITIONS = {
    "I1": (0, 0), "I2": (29, 0), "I3": (58, 0),
    "I4": (0, 29), "I5": (29, 29), "I6": (58, 29),
    "I7": (0, 58), "I8": (29, 58), "I9": (58, 58),
}

ROAD_OFFSET = 0.28

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

def draw_frame(frame_idx):
    t = timesteps[frame_idx]
    v_msg = v_by_timestep[t]
    i_msg = i_by_timestep[t]

    fig, ax = plt.subplots(figsize=(8, 8))

    for y in [0, 29, 58]:
        ax.plot([0, 58], [y, y], color="black", linewidth=8, alpha=0.15, solid_capstyle="round")
        ax.plot([0, 58], [y + ROAD_OFFSET, y + ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35)
        ax.plot([0, 58], [y - ROAD_OFFSET, y - ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35)

    for x in [0, 29, 58]:
        ax.plot([x, x], [0, 58], color="black", linewidth=8, alpha=0.15, solid_capstyle="round")
        ax.plot([x + ROAD_OFFSET, x + ROAD_OFFSET], [0, 58], color="gray", linewidth=1, alpha=0.35)
        ax.plot([x - ROAD_OFFSET, x - ROAD_OFFSET], [0, 58], color="gray", linewidth=1, alpha=0.35)

    ax.plot([-2, 0], [58, 58], color="black", linewidth=8, alpha=0.15, solid_capstyle="round")
    ax.plot([-2, 0], [58 + ROAD_OFFSET, 58 + ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35)
    ax.plot([-2, 0], [58 - ROAD_OFFSET, 58 - ROAD_OFFSET], color="gray", linewidth=1, alpha=0.35)

    ax.scatter([-2], [58], s=150, c="gold", edgecolors="black")
    ax.text(-2, 59.6, "A", ha="center", fontsize=11, weight="bold")
    ax.text(0, -2.8, "B", ha="center", fontsize=11, weight="bold")
    ax.text(58, -2.8, "C", ha="center", fontsize=11, weight="bold")
    ax.text(58, 60.2, "D", ha="center", fontsize=11, weight="bold")

    for item in i_msg["intersections"]:
        x, y = item["x"], item["y"]
        if "light_top" in item:
            ax.scatter([x], [y + 1.4], s=55, c=LIGHT_COLORS[item["light_top"]], edgecolors="black")
        if "light_right" in item:
            ax.scatter([x + 1.4], [y], s=55, c=LIGHT_COLORS[item["light_right"]], edgecolors="black")
        if "light_down" in item:
            ax.scatter([x], [y - 1.4], s=55, c=LIGHT_COLORS[item["light_down"]], edgecolors="black")
        if "light_left" in item:
            ax.scatter([x - 1.4], [y], s=55, c=LIGHT_COLORS[item["light_left"]], edgecolors="black")

    for vehicle in v_msg["vehicles"]:
        px, py = lane_offset(vehicle["x"], vehicle["y"], vehicle["direction"])
        ax.scatter(
            [px], [py],
            s=110,
            c=VEHICLE_COLORS.get(vehicle["direction"], "gray"),
            marker=MARKERS.get(vehicle["direction"], "o"),
            edgecolors="black",
        )
        ax.text(px + 0.4, py + 0.4, vehicle["vehicle_id"], fontsize=8)

    ax.set_xlim(-4, 62)
    ax.set_ylim(-4, 62)
    ax.set_aspect("equal")
    ax.grid(True, alpha=0.12)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"Traffic Simulation | Timestep {t}")

    plt.show()

interact(
    draw_frame,
    frame_idx=IntSlider(min=0, max=len(timesteps) - 1, step=1, value=0, description="Frame")
)
