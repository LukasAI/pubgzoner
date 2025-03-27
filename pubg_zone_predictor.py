import streamlit as st
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from PIL import Image
import random
import math
import os

# Map metadata and file paths
map_files = {
    "Erangel": "Erangel_Main_High_Res.png",
}

map_dimensions = {
    "Erangel": (8160, 8160),
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
map_name = "Erangel"
zone_number = st.sidebar.selectbox("Zone Number (for radius only)", list(zone_radii.keys()), index=0)
radius = zone_radii[zone_number]

if st.sidebar.button("Reset Zones"):
    st.session_state.zones = []

if st.sidebar.button("Predict Next Zone"):
    if st.session_state.zones:
        last_center, last_radius = st.session_state.zones[-1]
        current_phase = len(st.session_state.zones) + 1
        max_shift = last_radius * (0.4 if current_phase <= 4 else 0.6)
        bias_angle = random.uniform(0, 2 * math.pi)
        bias_distance = random.uniform(0.3, 1.0) * max_shift
        shift_x = bias_distance * math.cos(bias_angle)
        shift_y = bias_distance * math.sin(bias_angle)
        new_center = (last_center[0] + shift_x, last_center[1] + shift_y)
        new_radius = last_radius * 0.6
        new_center = (
            max(0, min(map_dimensions[map_name][0], new_center[0])),
            max(0, min(map_dimensions[map_name][1], new_center[1]))
        )
        st.session_state.zones.append((new_center, new_radius))

# Main UI - Map interaction
st.title("📍 Click to Set Zone Center")
click_info = st.empty()

fig, ax = plt.subplots(figsize=(8, 8))
map_path = map_files[map_name]
width, height = map_dimensions[map_name]

if os.path.exists(map_path):
    map_img = Image.open(map_path)
    ax.imshow(map_img, extent=[0, width, height, 0])
    ax.set_xlim(0, width)
    ax.set_ylim(height, 0)
    ax.set_title(f"{map_name} - Zones")

    colors = ['blue', 'green', 'orange', 'red', 'purple', 'black', 'cyan', 'magenta']
    for i, (center, rad) in enumerate(st.session_state.zones):
        circle = patches.Circle(center, rad, fill=False, linewidth=2, edgecolor=colors[i % len(colors)])
        ax.add_patch(circle)
        ax.text(center[0], center[1], f'Z{i+1}', color=colors[i % len(colors)],
                fontsize=10, ha='center', va='center', weight='bold')

    st.pyplot(fig, use_container_width=True)

    # Coordinate click input (simulated click until real interactivity added)
    with st.expander("Manual Zone Placement"):
        col1, col2 = st.columns(2)
        with col1:
            manual_x = st.slider("X Coordinate", 0, width, width // 2)
        with col2:
            manual_y = st.slider("Y Coordinate", 0, height, height // 2)
        if st.button("Place Zone Here"):
            st.session_state.zones.append(((manual_x, manual_y), radius))
            st.experimental_rerun()
else:
    st.error(f"Map image not found: {map_path}")
