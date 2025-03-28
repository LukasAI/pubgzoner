import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import random
import math
import os
import numpy as np

# Constants
WORLD_SIZE = 8000  # in-game meters for 8x8 maps

# Map metadata and file paths
map_files = {
    "Erangel": "Erangel_Main_High_Res.png",
    "Miramar": "Miramar_Main_High_Res.png",
    "Sanhok": "Sanhok_Main_High_Res.png",
    "Vikendi": "Vikendi_Main_High_Res.png",
    "Deston": "Deston_Main_High_Res.png",
    "Taego": "Taego_Main_High_Res.png",
    "Rondo": "Rondo_Main_High_Res.png"
}

map_dimensions = {
    "Erangel": (3072, 3072),
    "Miramar": (3072, 3072),
    "Sanhok": (3072, 3072),
    "Vikendi": (3072, 3072),
    "Deston": (3072, 3072),
    "Taego": (3072, 3072),
    "Rondo": (3072, 3072)
}

maps_8x8 = ["Erangel", "Miramar", "Deston", "Taego", "Rondo"]
maps_6x6 = ["Vikendi"]
maps_4x4 = ["Sanhok"]

radius_by_phase = {
    "8x8": [1997.05, 1198.25, 659.05, 362.45, 181.25, 90.6, 45.3, 22.65, 0],
    "6x6": [1502.3, 901.4, 495.75, 272.65, 136.35, 68.15, 34.1, 17.05, 0],
    "4x4": [999.3, 599.55, 329.75, 181.35, 90.7, 45.35, 22.65, 11.35, 0]
}

def get_radius(map_name, phase):
    key = "8x8" if map_name in maps_8x8 else "6x6" if map_name in maps_6x6 else "4x4"
    return radius_by_phase[key][min(phase - 1, 8)]

def get_scaled_radius(map_name, phase):
    base_radius = get_radius(map_name, phase)
    map_width = map_dimensions[map_name][0]
    scale_factor = map_width / WORLD_SIZE
    return base_radius * scale_factor

def world_to_image(x, map_name):
    scale = map_dimensions[map_name][0] / WORLD_SIZE
    return x * scale

def image_to_world(x, map_name):
    scale = map_dimensions[map_name][0] / WORLD_SIZE
    return x / scale

# Load heatmaps if available
erangel_heatmap = None
miramar_heatmap = None
vikendi_heatmap = None
taego_heatmap = None
try:
    if os.path.exists("erangel_heatmap.jpg"):
        heatmap_img = Image.open("erangel_heatmap.jpg").convert("L")
        erangel_heatmap = np.array(heatmap_img) / 255.0
    if os.path.exists("miramar_heatmap.jpg"):
        heatmap_img = Image.open("miramar_heatmap.jpg").convert("L")
        miramar_heatmap = np.array(heatmap_img) / 255.0
    if os.path.exists("vikendi_heatmap.jpg"):
        heatmap_img = Image.open("vikendi_heatmap.jpg").convert("L")
        vikendi_heatmap = np.array(heatmap_img) / 255.0
    if os.path.exists("taego_heatmap.jpg"):
        heatmap_img = Image.open("taego_heatmap.jpg").convert("L")
        taego_heatmap = np.array(heatmap_img) / 255.0
except:
    pass

if 'zones' not in st.session_state:
    st.session_state.zones = []

st.sidebar.title("PUBG Zone Predictor")
map_name = st.sidebar.selectbox("Select Map", list(map_files.keys()))
x = st.sidebar.slider("X Coordinate (meters)", 0, WORLD_SIZE, 4000)
y = st.sidebar.slider("Y Coordinate (meters)", 0, WORLD_SIZE, 4000)
selected_phase = st.sidebar.selectbox("Which phase are you placing?", list(range(1, 10)))
avoid_red_zones = st.sidebar.checkbox("Avoid red heatmap zones (All maps supported)", value=True)

if st.sidebar.button("Set Zone"):
    radius = get_scaled_radius(map_name, selected_phase)
    img_x = world_to_image(x, map_name)
    img_y = world_to_image(y, map_name)
    while len(st.session_state.zones) < selected_phase:
        st.session_state.zones.append(None)
    st.session_state.zones[selected_phase - 1] = ((img_x, img_y), radius)

if st.sidebar.button("Reset Zones"):
    st.session_state.zones = []

def is_zone_heatmap_acceptable(center, radius, map_name, map_width, map_height):
    if map_name == "Erangel":
        heatmap = erangel_heatmap
    elif map_name == "Miramar":
        heatmap = miramar_heatmap
    elif map_name == "Vikendi":
        heatmap = vikendi_heatmap
    elif map_name == "Taego":
        heatmap = taego_heatmap
    else:
        return True

    if heatmap is None:
        return True

    cx, cy = int(center[0]), int(center[1])
    rr = int(radius)
    heatmap_h, heatmap_w = heatmap.shape
    score_sum = 0
    count = 0
    for dx in range(-rr, rr + 1, 10):
        for dy in range(-rr, rr + 1, 10):
            if dx**2 + dy**2 <= rr**2:
                px = cx + dx
                py = cy + dy
                if 0 <= px < map_width and 0 <= py < map_height:
                    hx = int((px / map_width) * heatmap_w)
                    hy = int((py / map_height) * heatmap_h)
                    if 0 <= hx < heatmap_w and 0 <= hy < heatmap_h:
                        heatmap_score = 1.0 - heatmap[hy, hx]
                        score_sum += heatmap_score
                        count += 1
    avg_score = score_sum / max(count, 1)
    return avg_score > 0.3

# Display Map and Circles
fig, ax = plt.subplots(figsize=(8, 8))
map_path = map_files[map_name]

if os.path.exists(map_path):
    map_img = Image.open(map_path)
    width, height = map_dimensions[map_name]
    ax.imshow(map_img, extent=[0, width, height, 0])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)

    colors = ['blue', 'green', 'orange', 'red', 'purple', 'black', 'cyan', 'magenta']
    for i, zone in enumerate(st.session_state.zones):
        if zone is None:
            continue
        center, radius = zone
        circle = patches.Circle(center, radius, fill=False, linewidth=2, edgecolor=colors[i % len(colors)])
        ax.add_patch(circle)
        ax.text(center[0], center[1], f'Z{i+1}', color=colors[i % len(colors)],
                fontsize=10, ha='center', va='center', weight='bold')

    ax.set_title(f"{map_name} - Zones")
    st.pyplot(fig)
else:
    st.error(f"Map image not found: {map_path}")
