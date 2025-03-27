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
    "Miramar": (3072, 3072),
    "Sanhok": (4096, 4096),
    "Vikendi": (6144, 6144),
    "Deston": (8160, 8160),
    "Taego": (8192, 8192),
    "Rondo": (8000, 8000)
}

maps_8x8 = ["Erangel", "Miramar", "Deston", "Taego", "Rondo"]
maps_6x6 = ["Vikendi"]
maps_4x4 = ["Sanhok"]

# Radii per phase by map size (from official PUBG specs)
radius_by_phase = {
    "8x8": [1997.05, 1198.25, 659.05, 362.45, 181.25, 90.6, 45.3, 22.65, 0],
    "6x6": [1502.3, 901.4, 495.75, 272.65, 136.35, 68.15, 34.1, 17.05, 0],
    "4x4": [999.3, 599.55, 329.75, 181.35, 90.7, 45.35, 22.65, 11.35, 0]
}

def get_radius(map_name, phase):
    key = "8x8" if map_name in maps_8x8 else "6x6" if map_name in maps_6x6 else "4x4"
    return radius_by_phase[key][min(phase - 1, 8)]

def get_scaled_radius(map_name, phase):
    base_radius = get_scaled_radius(map_name, phase)  # in meters
    scale_factor = 3072 / 8000  # assuming 3072px = 8km
    return base_radius * scale_factor

# Load heatmaps if available
erangel_heatmap = None
miramar_heatmap = None
try:
    if os.path.exists("erangel_heatmap.jpg"):
        heatmap_img = Image.open("erangel_heatmap.jpg").convert("L")
        erangel_heatmap = np.array(heatmap_img) / 255.0
    if os.path.exists("miramar_heatmap.jpg"):
        heatmap_img = Image.open("miramar_heatmap.jpg").convert("L")
        miramar_heatmap = np.array(heatmap_img) / 255.0
except:
    pass

# App state
if 'zones' not in st.session_state:
    st.session_state.zones = []

# Sidebar controls
st.sidebar.title("PUBG Zone Predictor")
map_name = st.sidebar.selectbox("Select Map", list(map_files.keys()))
x = st.sidebar.slider("X Coordinate", 0, map_dimensions[map_name][0], 4000)
y = st.sidebar.slider("Y Coordinate", 0, map_dimensions[map_name][1], 4000)
phase = len(st.session_state.zones) + 1
avoid_red_zones = st.sidebar.checkbox("Avoid red heatmap zones (Erangel only)", value=True)

if st.sidebar.button("Set Zone"):
    radius = get_radius(map_name, phase)
    st.session_state.zones.append(((x, y), radius))

if st.sidebar.button("Reset Zones"):
    st.session_state.zones = []

def is_zone_on_land(center, radius, img_array):
    cx, cy = int(center[0]), int(center[1])
    rr = int(radius)
    count = 0
    water_count = 0
    for dx in range(-rr, rr + 1, 10):
        for dy in range(-rr, rr + 1, 10):
            if dx**2 + dy**2 <= rr**2:
                px = cx + dx
                py = cy + dy
                if 0 <= px < img_array.shape[1] and 0 <= py < img_array.shape[0]:
                    r, g, b = img_array[py, px, :3]
                    count += 1
                    if b > 130 and b > r + 20 and b > g + 20:
                        water_count += 1
    return water_count / max(count, 1) < 0.15

def is_zone_heatmap_acceptable(center, radius, map_name, map_width, map_height):
    if map_name == "Erangel":
        heatmap = erangel_heatmap
    elif map_name == "Miramar":
        heatmap = miramar_heatmap
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

if st.sidebar.button("Predict Next Zone"):
    if st.session_state.zones:
        map_img = Image.open(map_files[map_name]).convert('RGB')
        img_array = np.array(map_img)
        width, height = map_dimensions[map_name]

        last_center, last_radius = st.session_state.zones[-1]
        current_phase = len(st.session_state.zones) + 1
        new_radius = get_scaled_radius(map_name, current_phase)

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

            land_ok = is_zone_on_land(new_center, new_radius, img_array)
            heatmap_ok = True
            if map_name == "Erangel" and avoid_red_zones and current_phase >= 4:
                heatmap_ok = is_zone_heatmap_acceptable(new_center, new_radius, map_name, width, height)

            if land_ok and (not avoid_red_zones or heatmap_ok):
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
