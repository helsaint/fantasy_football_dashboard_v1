from config.text import TEXT_FONT
from config.position_config import POSITION_COORDINATES
from PIL import Image, ImageDraw,ImageFont
import requests
import streamlit as st


def player_text_display(pitch_image, pos_key, position,
                 df, draw, font_name,
                 font_value, index):
    pitch_image = pitch_image
    position = position
    pos_key = pos_key
    df = df
    draw = draw
    font_name = font_name
    font_value = font_value
    i = index
    
    # Player Name
    text = df[df['position_y']==position]['player_name'].values[i]
    pos_key_name = f"{pos_key}_NAME_{i+1}"
    x, y, w, h = POSITION_COORDINATES[pos_key_name]
    text_bbox = draw.textbbox((0, 0), text, font=font_name)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw_x = x + (w - text_width) / 2
    draw_y = y + (h - text_height) / 2
    draw.text((draw_x, draw_y), text, font=font_name, 
              fill=TEXT_FONT["font_color_names"])
    
    # Player Value
    pos_key_value = f"{pos_key}_VALUE_{i+1}"
    x, y, w, h = POSITION_COORDINATES[pos_key_value]
    text = df[df['position_y']==position]['now_cost'].values[i]
    draw.text((x, y), f"£{text/10}m", fill=TEXT_FONT["font_color_values"], font=font_value)
    # Player GW Points
    pos_key_points = f"{pos_key}_POINTS_{i+1}"
    x, y, w, h = POSITION_COORDINATES[pos_key_points]
    text = df[df['position_y']==position]['total_points'].values[i]
    draw.text((x, y), f"Pts: {text}", fill=TEXT_FONT["font_color_values"], font=font_value)
    # Player Photo
    pos_key_coord = f"{pos_key}_{i+1}"
    x, y, w, h = POSITION_COORDINATES[pos_key_coord]
    text = df[df['position_y']==position]['photo'].values[i]
    text = text.replace('.jpg','').replace('.png','')
    try:
        photo_url = f"https://resources.premierleague.com/premierleague/photos/players/110x140/p{text}.png"
        player_image = Image.open(requests.get(photo_url, stream=True).raw).resize((w, h))
        pitch_image.paste(player_image, (x, y))
    except Exception as e:
        print(f"Error loading image for player {text}: {e}")


def text_heading_display(pos_key, text, draw, font_team_value):
    pos_key = pos_key
    text = text
    draw = draw
    x, y, w, h = POSITION_COORDINATES[pos_key]
    text_bbox = draw.textbbox((0, 0), text, font=font_team_value)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    draw_x = x + (w - text_width) / 2
    draw_y = y + (h - text_height) / 2
    draw.text((draw_x, draw_y), text, font=font_team_value, 
              fill=TEXT_FONT["font_color_values"])