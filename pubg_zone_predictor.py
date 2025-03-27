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
try:
    if os.path.exists("erangel_heatmap.jpg"):
        heatmap_img = Image.open("erangel_heatmap.jpg").convert("L")
        erangel_heatmap = np.array(heatmap_img) / 255.0
    if os.path.exists("miramar_heatmap.jpg"):
        heatmap_img = Image.open("miramar_heatmap.jpg").convert("L")
        miramar_heatmap = np.array(heatmap_img) / 255.0
except:
    pass

if 'zones' not in st.session_state:
    st.session_state.zones = []

st.sidebar.title("PUBG Zone Predictor")
map_name = st.sidebar.selectbox("Select Map", list(map_files.keys()))
x = st.sidebar.slider("X Coordinate (meters)", 0, WORLD_SIZE, 4000)
y = st.sidebar.slider("Y Coordinate (meters)", 0, WORLD_SIZE, 4000)
selected_phase = st.sidebar.selectbox("Which phase are you placing?", list(range(1, 10)))
avoid_red_zones = st.sidebar.checkbox("Avoid red heatmap zones (Erangel/Miramar)", value=True)

if st.sidebar.button("Set Zone"):
    radius = get_scaled_radius(map_name, selected_phase)
    img_x = world_to_image(x, map_name)
    img_y = world_to_image(y, map_name)
    while len(st.session_state.zones) < selected_phase:
        st.session_state.zones.append(None)
    st.session_state.zones[selected_phase - 1] = ((img_x, img_y), radius)

if st.sidebar.button("Reset Zones"):
    st.session_state.zones = []

# Remaining logic unchanged — prediction, land detection, heatmap scoring, and drawing
# all operate on image pixel coordinates now, but sliders use meters.
# Zones are placed using world meters, then converted to pixels for internal use.
