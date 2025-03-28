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

# Regular map image pixel dimensions (all maps are 3072x3072)
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

# Radii per phase in in‑game meters (from official PUBG specs)
radius_by_phase = {
    "8x8": [1997.05, 1198.25, 659.05, 362.45, 181.25, 90.6, 45.3, 22.65, 0],
    "6x6": [1502.3, 901.4, 495.75, 272.65, 136.35, 68.15, 34.1, 17.05, 0],
    "4x4": [999.3, 599.55, 329.75, 181.35, 90.7, 45.35, 22.65, 11.35, 0]
}

def get_map_meter_size(map_name):
    return 8000 if map_name in maps_8x8 else 6000 if map_name in maps_6x6 else 4000

def get_radius(map_name, phase):
    key = "8x8" if map_name in maps_8x8 else "6x6" if map_name in maps_6x6 else "4x4"
    return radius_by_phase[key][min(phase - 1, 8)]

def get_scaled_radius(map_name, phase):
    base_radius = get_radius(map_name, phase)
    map_meter_size = get_map_meter_size(map_name)
    pixel_width = map_dimensions[map_name][0]
    scale_factor = pixel_width / map_meter_size
    return base_radius * scale_factor

def world_to_image(x, map_name):
    map_meter_size = get_map_meter_size(map_name)
    pixel_width = map_dimensions[map_name][0]
    return x * (pixel_width / map_meter_size)

def image_to_world(x, map_name):
    map_meter_size = get_map_meter_size(map_name)
    pixel_width = map_dimensions[map_name][0]
    return x * (map_meter_size / pixel_width)

# Load heatmaps as color images (now 3072x3072, matching regular maps)
erangel_heatmap = None
miramar_heatmap = None
vikendi_heatmap = None
taego_heatmap = None
try:
    if os.path.exists("erangel_heatmap.jpg"):
        heatmap_img = Image.open("erangel_heatmap.jpg").convert("RGB")
        erangel_heatmap = np.array(heatmap_img)
    if os.path.exists("miramar_heatmap.jpg"):
        heatmap_img = Image.open("miramar_heatmap.jpg").convert("RGB")
        miramar_heatmap = np.array(heatmap_img)
    if os.path.exists("vikendi_heatmap.jpg"):
        heatmap_img = Image.open("vikendi_heatmap.jpg").convert("RGB")
        vikendi_heatmap = np.array(heatmap_img)
    if os.path.exists("taego_heatmap.jpg"):
        heatmap_img = Image.open("taego_heatmap.jpg").convert("RGB")
        taego_heatmap = np.array(heatmap_img)
except Exception as e:
    pass

def is_zone_on_land(center, radius, img_array):
    cx, cy = int(center[0]), int(center[1])
    rr = int(radius)
    count = 0
    water_count = 0
    for dx in range(-rr, rr + 1, 10):
        for dy in range(-rr, rr + 1, 10):
            if dx*dx + dy*dy <= rr*rr:
                px = cx + dx
                py = cy + dy
                if 0 <= px < img_array.shape[1] and 0 <= py < img_array.shape[0]:
                    r, g, b = img_array[py, px, :3]
                    count += 1
                    if b > 130 and b > r + 20 and b > g + 20:
                        water_count += 1
    return water_count / max(count, 1) < 0.15

def compute_unsafe_ratio(center, radius, map_name, map_width, map_height):
    """
    Samples the candidate zone at a 5-pixel resolution and returns the fraction of unsafe pixels.
    Here, we compute a danger (or "redness") score per pixel as:
      danger = max(R - (G+B)/2, 0) / 255
    A pixel is considered unsafe if its danger score exceeds THRESHOLD_DANGER.
    Since both the regular map and the heatmap are 3072x3072, the conversion ratio is 1.
    """
    THRESHOLD_DANGER = 0.5  # Adjust this value as needed (0-1 scale)
    if map_name == "Erangel":
        heatmap = erangel_heatmap
    elif map_name == "Miramar":
        heatmap = miramar_heatmap
    elif map_name == "Taego":
        heatmap = taego_heatmap
    elif map_name == "Vikendi":
        heatmap = vikendi_heatmap
    else:
        return 0.0

    if heatmap is None:
        return 0.0

    # Heatmap and map have the same resolution, so ratio is 1.
    hm_height, hm_width, _ = heatmap.shape

    cx, cy = int(center[0]), int(center[1])
    rr = int(radius)
    total_count = 0
    unsafe_count = 0

    for dx in range(-rr, rr + 1, 5):
        for dy in range(-rr, rr + 1, 5):
            if dx*dx + dy*dy <= rr*rr:
                px = cx + dx
                py = cy + dy
                if 0 <= px < map_width and 0 <= py < map_height:
                    # Direct 1:1 indexing into the heatmap color image.
                    pixel = heatmap[py, px]  # (R, G, B)
                    # Compute danger score.
                    danger = pixel[0] - (pixel[1] + pixel[2]) / 2.0
                    danger = max(danger, 0) / 255.0  # Normalize to 0-1
                    total_count += 1
                    if danger > THRESHOLD_DANGER:
                        unsafe_count += 1

    if total_count == 0:
        return 1.0
    return unsafe_count / total_count

# Initialize session state for zones if not already set
if 'zones' not in st.session_state:
    st.session_state.zones = []

# Sidebar controls
with st.sidebar:
    st.title("PUBG Zone Predictor")
    map_name = st.selectbox("Select Map", list(map_files.keys()))
    map_meter_size = get_map_meter_size(map_name)
    x = st.slider("X Coordinate (meters)", 0, map_meter_size, map_meter_size // 2)
    y = st.slider("Y Coordinate (meters)", 0, map_meter_size, map_meter_size // 2)
    selected_phase = st.selectbox("Which phase are you placing?", list(range(1, 10)))
    avoid_red_zones = st.checkbox("Avoid red heatmap zones (All maps supported)", value=True)

    if st.button("Set Zone"):
        radius = get_scaled_radius(map_name, selected_phase)
        img_x = world_to_image(x, map_name)
        img_y = world_to_image(y, map_name)
        while len(st.session_state.zones) < selected_phase:
            st.session_state.zones.append(None)
        st.session_state.zones[selected_phase - 1] = ((img_x, img_y), radius)

    if st.button("Reset Zones"):
        st.session_state.zones = []

    if st.button("Predict Next Zone"):
        if any(st.session_state.zones):
            map_img = Image.open(map_files[map_name]).convert('RGB')
            img_array = np.array(map_img)
            width, height = map_dimensions[map_name]  # 3072x3072

            last_idx = max(i for i, z in enumerate(st.session_state.zones) if z is not None)
            last_center, last_radius = st.session_state.zones[last_idx]
            current_phase = last_idx + 2  # Next phase number
            new_radius = get_scaled_radius(map_name, current_phase)

            best_candidate = None
            if current_phase < 4:
                # For phases before Z4, accept the first candidate that passes the land test.
                for attempt in range(30):
                    center_bias_x = width/2 - last_center[0]
                    center_bias_y = height/2 - last_center[1]
                    bias_strength = 0.25 if current_phase <= 3 else 0.0
                    shift_bias = (random.uniform(-1, 1) + bias_strength*center_bias_x/width,
                                  random.uniform(-1, 1) + bias_strength*center_bias_y/height)
                    norm = math.hypot(*shift_bias)
                    shift_dir = (shift_bias[0]/norm, shift_bias[1]/norm)
                    max_shift = last_radius * (0.4 if current_phase <= 4 else 0.6)
                    shift_dist = random.uniform(0.3, 1.0)*max_shift

                    shift_x = shift_dist * shift_dir[0]
                    shift_y = shift_dist * shift_dir[1]

                    new_x = max(0, min(width, last_center[0] + shift_x))
                    new_y = max(0, min(height, last_center[1] + shift_y))
                    new_center = (new_x, new_y)

                    if not is_zone_on_land(new_center, new_radius, img_array):
                        continue
                    best_candidate = (new_center, new_radius)
                    break
            else:
                # For Z4 and later, sample 100 candidates and choose the one with the lowest unsafe (red) ratio.
                best_ratio = float('inf')
                for attempt in range(100):
                    center_bias_x = width/2 - last_center[0]
                    center_bias_y = height/2 - last_center[1]
                    bias_strength = 0.25 if current_phase <= 3 else 0.0
                    shift_bias = (random.uniform(-1, 1) + bias_strength*center_bias_x/width,
                                  random.uniform(-1, 1) + bias_strength*center_bias_y/height)
                    norm = math.hypot(*shift_bias)
                    shift_dir = (shift_bias[0]/norm, shift_bias[1]/norm)
                    max_shift = last_radius * (0.4 if current_phase <= 4 else 0.6)
                    shift_dist = random.uniform(0.3, 1.0)*max_shift

                    shift_x = shift_dist * shift_dir[0]
                    shift_y = shift_dist * shift_dir[1]

                    new_x = max(0, min(width, last_center[0] + shift_x))
                    new_y = max(0, min(height, last_center[1] + shift_y))
                    new_center = (new_x, new_y)

                    if not is_zone_on_land(new_center, new_radius, img_array):
                        continue

                    unsafe_ratio = compute_unsafe_ratio(new_center, new_radius, map_name, width, height)
                    if unsafe_ratio < best_ratio:
                        best_ratio = unsafe_ratio
                        best_candidate = (new_center, new_radius)

            if best_candidate is not None:
                while len(st.session_state.zones) < current_phase:
                    st.session_state.zones.append(None)
                st.session_state.zones[current_phase - 1] = best_candidate

# Display Map and Circles
fig, ax = plt.subplots(figsize=(8, 8))
map_path = map_files[map_name]
map_meter_size = get_map_meter_size(map_name)

if os.path.exists(map_path):
    map_img = Image.open(map_path)
    # Display the map with axes in in‑game meters.
    ax.imshow(map_img, extent=[0, map_meter_size, map_meter_size, 0])
    ax.set_xlim(0, map_meter_size)
    ax.set_ylim(map_meter_size, 0)

    colors = ['blue', 'green', 'orange', 'red', 'purple', 'black', 'cyan', 'magenta']
    for i, zone in enumerate(st.session_state.zones):
        if zone is None:
            continue
        center_px, radius_px = zone
        cx = image_to_world(center_px[0], map_name)
        cy = image_to_world(center_px[1], map_name)
        radius_m = image_to_world(radius_px, map_name)
        circle = patches.Circle((cx, cy), radius_m, fill=False, linewidth=2, edgecolor=colors[i % len(colors)])
        ax.add_patch(circle)
        ax.text(cx, cy, f'Z{i+1}', color=colors[i % len(colors)],
                fontsize=10, ha='center', va='center', weight='bold')

    ax.set_title(f"{map_name} - Zones")
    st.pyplot(fig)
else:
    st.error(f"Map image not found: {map_path}")
