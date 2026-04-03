import json
import matplotlib.pyplot as plt
import ipywidgets as widgets
from IPython.display import display, clear_output

A = (-2, 58)
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

DIR_LABEL = {
    0: "S",
    1: "U",
    2: "R",
    3: "D",
    4: "L",
}


def load_history(path="vgroup_history.json"):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, dict) and "history" in data:
        return data["history"]
    return data


def draw_frame(history, frame_idx):
    frame = history[frame_idx]

    plt.figure(figsize=(8, 8))

    for y in [0, 29, 58]:
        plt.plot([-2, 58], [y, y], color="gray", linewidth=2)

    for x in [0, 29, 58]:
        plt.plot([x, x], [0, 58], color="gray", linewidth=2)

    landmarks = {"A": A, "B": B, "C": C, "D": D}
    for label, (x, y) in landmarks.items():
        plt.scatter(x, y, s=140, color="gold", edgecolors="black", zorder=3)
        plt.text(x, y + 1.5, label, ha="center", fontsize=10, fontweight="bold")

    for iid, (x, y) in INTERSECTIONS.items():
        plt.scatter(x, y, s=30, color="black", zorder=2)
        plt.text(x + 0.7, y + 0.7, iid, fontsize=8)

    for vehicle in frame["vehicles"]:
        x = vehicle["x"]
        y = vehicle["y"]
        vid = vehicle["vehicle_id"]
        direction = vehicle["direction"]

        plt.scatter(x, y, s=90, color="red", edgecolors="black", zorder=4)
        plt.text(x, y - 1.5, f"{vid}:{DIR_LABEL.get(direction, '?')}", ha="center", fontsize=8)

    plt.xlim(-4, 62)
    plt.ylim(-4, 62)
    plt.gca().set_aspect("equal")
    plt.grid(True, linestyle="--", alpha=0.3)
    plt.xlabel("x")
    plt.ylabel("y")
    plt.title(f"Timestep {frame['timestep']} | Vehicles: {len(frame['vehicles'])}")
    plt.show()


def show_simulation_player(history, interval=250):
    play = widgets.Play(
        value=0,
        min=0,
        max=len(history) - 1,
        step=1,
        interval=interval,
        description="Play",
        disabled=False
    )

    slider = widgets.IntSlider(
        value=0,
        min=0,
        max=len(history) - 1,
        step=1,
        description="Frame",
        continuous_update=False,
        layout=widgets.Layout(width="700px")
    )

    widgets.jslink((play, "value"), (slider, "value"))

    output = widgets.Output()

    def on_value_change(change):
        with output:
            clear_output(wait=True)
            draw_frame(history, change["new"])

    slider.observe(on_value_change, names="value")

    controls = widgets.HBox([play, slider])
    display(controls, output)

    with output:
        draw_frame(history, 0)

history = load_history("vgroup_history.json")
show_simulation_player(history, interval=200)