import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import random
import math
import os
import numpy as np

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
    "Erangel": (8160, 8160),
    "Miramar": (8160, 8160),
    "Sanhok": (4096, 4096),
    "Vikendi": (6144, 6144),
    "Deston": (8160, 8160),
    "Taego": (8192, 8192),
    "Rondo": (8000, 8000)
}

zone_radii = {
    1: 1500,
    2: 1000,
    3: 650,
    4: 400,
    5: 250,
    6: 150,
    7: 100,
    8: 50
}

# App state
if 'zones' not in st.session_state:
    st.session_state.zones = []

# Sidebar controls
st.sidebar.title("PUBG Zone Predictor")
map_name = st.sidebar.selectbox("Select Map", list(map_files.keys()))
zone_number = st.sidebar.selectbox("Zone Number", list(zone_radii.keys()))
x = st.sidebar.slider("X Coordinate", 0, map_dimensions[map_name][0], 4000)
y = st.sidebar.slider("Y Coordinate", 0, map_dimensions[map_name][1], 4000)

if st.sidebar.button("Set Zone"):
    radius = zone_radii[zone_number]
    st.session_state.zones.append(((x, y), radius))

if st.sidebar.button("Reset Zones"):
    st.session_state.zones = []


def is_zone_on_land(center, radius, img_array):
    cx, cy = int(center[0]), int(center[1])
    rr = int(radius)
    h, w, _ = img_array.shape
    count = 0
    water_count = 0
    for dx in range(-rr, rr + 1, 10):
        for dy in range(-rr, rr + 1, 10):
            if dx**2 + dy**2 <= rr**2:
                px = cx + dx
                py = cy + dy
                if 0 <= px < w and 0 <= py < h:
                    pixel = img_array[py, px]  # Y,X
                    r, g, b = pixel[:3]
                    count += 1
                    if b > 130 and b > r + 20 and b > g + 20:
                        water_count += 1
    return water_count / count < 0.15  # Must be mostly land

if st.sidebar.button("Predict Next Zone"):
    if st.session_state.zones:
        map_img = Image.open(map_files[map_name]).convert('RGB')
        img_array = np.array(map_img)
        width, height = map_dimensions[map_name]

        last_center, last_radius = st.session_state.zones[-1]
        current_phase = len(st.session_state.zones) + 1
        new_radius = last_radius * 0.6

        for attempt in range(30):
            center_bias_x = width / 2 - last_center[0]
            center_bias_y = height / 2 - last_center[1]
            bias_strength = 0.25 if current_phase <= 3 else 0.0
            shift_bias = (random.uniform(-1, 1) + bias_strength * center_bias_x / width,
                          random.uniform(-1, 1) + bias_strength * center_bias_y / height)
            norm = math.hypot(*shift_bias)
            shift_dir = (shift_bias[0] / norm, shift_bias[1] / norm)

            max_shift = last_radius * (0.4 if current_phase <= 4 else 0.6)
            shift_dist = random.uniform(0.3, 1.0) * max_shift

            shift_x = shift_dist * shift_dir[0]
            shift_y = shift_dist * shift_dir[1]

            new_x = max(0, min(width, last_center[0] + shift_x))
            new_y = max(0, min(height, last_center[1] + shift_y))
            new_center = (new_x, new_y)

            if is_zone_on_land(new_center, new_radius, img_array):
                st.session_state.zones.append((new_center, new_radius))
                break

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
    for i, (center, radius) in enumerate(st.session_state.zones):
        circle = patches.Circle(center, radius, fill=False, linewidth=2, edgecolor=colors[i % len(colors)])
        ax.add_patch(circle)
        ax.text(center[0], center[1], f'Z{i+1}', color=colors[i % len(colors)],
                fontsize=10, ha='center', va='center', weight='bold')

    ax.set_title(f"{map_name} - Zones")
    st.pyplot(fig)
else:
    st.error(f"Map image not found: {map_path}")
