import os
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(CURRENT_DIR)
font_path = os.path.join(BASE_DIR, "ui", "fonts", "ARIAL.TTF")

TEXT_FONT = {
    "font_family": font_path,
    "font_size_names": 20,
    "font_color_names": "white",
    "font_color_values": "black",
    "font_size_values": 16,
    "font_size_team_value": 24,
}