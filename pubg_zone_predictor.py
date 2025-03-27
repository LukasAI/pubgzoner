
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

if st.sidebar.button("Predict Next Zone"):
    if st.session_state.zones:
        last_center, last_radius = st.session_state.zones[-1]
        max_shift = last_radius * 0.4
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0, max_shift)
        shift_x = distance * math.cos(angle)
        shift_y = distance * math.sin(angle)
        new_center = (last_center[0] + shift_x, last_center[1] + shift_y)
        new_radius = last_radius * 0.6
        st.session_state.zones.append((new_center, new_radius))

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
