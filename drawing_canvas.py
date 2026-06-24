"""
AirSketch AI - Drawing Canvas & UI Module
Manages the virtual canvas, drawing actions, whiteboard states,
saving drawings, and rendering the high-fidelity UI/HUD.
"""

import cv2
import numpy as np
import os
from datetime import datetime

class DrawingCanvas:
    """
    Manages the drawing canvas, color/tool selections, 
    blending with backgrounds, and saving images.
    """
    def __init__(self, width=1280, height=720):
        """
        Initializes the canvas and default states.
        
        Args:
            width (int): Width of the canvas/video frame.
            height (int): Height of the canvas/video frame.
        """
        self.w = width
        self.h = height
        
        # Initialize a black canvas (drawings will be colored pixels, empty space is black)
        self.canvas = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        
        # UI Colors (BGR format)
        self.COLOR_PALETTE = {
            "RED": (0, 0, 255),
            "BLUE": (255, 0, 0),
            "GREEN": (0, 255, 0),
            "YELLOW": (0, 255, 255),
            "BLACK": (0, 0, 0),  # Act as eraser
            "WHITE": (255, 255, 255),
            "DARK_GRAY": (30, 30, 30),
            "LIGHT_GRAY": (220, 220, 220),
            "HUD_BG": (15, 15, 15),
            "TEXT_COLOR": (240, 240, 240)
        }

        # Button layout structures
        self.buttons = []
        self.setup_buttons()

        # Notification state
        self.notification_text = ""
        self.notification_timer = 0  # Number of frames to display notification

    def setup_buttons(self):
        """
        Calculates the positions and coordinates of the top menu buttons.
        This is called initially and can be recalculated if the screen size changes.
        """
        # Header bar height is 90px. Let's arrange buttons.
        # Format: {"name": str, "rect": (x1, y1, x2, y2), "color": BGR, "type": str, "value": any}
        
        # Colors (Red, Blue, Green, Yellow)
        self.buttons = [
            {"name": "RED", "rect": (280, 15, 360, 75), "color": self.COLOR_PALETTE["RED"], "type": "color", "value": self.COLOR_PALETTE["RED"]},
            {"name": "BLUE", "rect": (380, 15, 460, 75), "color": self.COLOR_PALETTE["BLUE"], "type": "color", "value": self.COLOR_PALETTE["BLUE"]},
            {"name": "GREEN", "rect": (480, 15, 560, 75), "color": self.COLOR_PALETTE["GREEN"], "type": "color", "value": self.COLOR_PALETTE["GREEN"]},
            {"name": "YELLOW", "rect": (580, 15, 660, 75), "color": self.COLOR_PALETTE["YELLOW"], "type": "color", "value": self.COLOR_PALETTE["YELLOW"]},
            
            # Eraser
            {"name": "ERASER", "rect": (680, 15, 780, 75), "color": self.COLOR_PALETTE["LIGHT_GRAY"], "type": "tool", "value": self.COLOR_PALETTE["BLACK"]},
            
            # Whiteboard Toggle
            {"name": "BOARD", "rect": (800, 15, 910, 75), "color": self.COLOR_PALETTE["DARK_GRAY"], "type": "action", "value": "toggle_board"},
            
            # Clear Canvas
            {"name": "CLEAR", "rect": (930, 15, 1030, 75), "color": (50, 50, 180), "type": "action", "value": "clear"},
            
            # Save Drawing
            {"name": "SAVE", "rect": (1050, 15, 1150, 75), "color": (50, 180, 50), "type": "action", "value": "save"}
        ]

    def update_dimensions(self, width, height):
        """
        Dynamically resizes the canvas if the webcam dimensions differ.
        
        Args:
            width (int): New frame width.
            height (int): New frame height.
        """
        if self.w != width or self.h != height:
            self.w = width
            self.h = height
            # Resize existing canvas or create new one
            self.canvas = cv2.resize(self.canvas, (self.w, self.h), interpolation=cv2.INTER_NEAREST)
            self.setup_buttons()

    def draw_line(self, pt1, pt2, color, thickness):
        """
        Draws a smooth line on the canvas between two points.
        
        Args:
            pt1 (tuple): Start point (x, y).
            pt2 (tuple): End point (x, y).
            color (tuple): BGR color tuple.
            thickness (int): Thickness of the line in pixels.
        """
        # If the start point is (0, 0) or out of bounds, skip to avoid drawing spikes
        if pt1 == (0, 0) or pt2 == (0, 0):
            return
            
        # Draw a circle at the endpoints and a line between them for continuous smooth drawing
        cv2.line(self.canvas, pt1, pt2, color, thickness)
        cv2.circle(self.canvas, pt2, thickness // 2, color, cv2.FILLED)

    def clear(self):
        """
        Clears the entire drawing canvas.
        """
        self.canvas.fill(0)
        self.show_notification("Canvas Cleared")

    def show_notification(self, text, duration=60):
        """
        Triggers a temporary status notification on screen.
        
        Args:
            text (str): Message to display.
            duration (int): Duration in frames.
        """
        self.notification_text = text
        self.notification_timer = duration

    def save_canvas(self, whiteboard_active, is_dark_bg=True):
        """
        Saves the drawing as a PNG image inside the 'saved_drawings' directory.
        If Whiteboard is OFF: Saves the drawing on a clean white background.
        If Whiteboard is ON: Saves the whiteboard image exactly as it appears.
        
        Args:
            whiteboard_active (bool): Whether whiteboard mode is currently active.
            is_dark_bg (bool): If whiteboard is active, is it dark or light background.
            
        Returns:
            str: Path to the saved image file, or None if failed.
        """
        # Create folder if it doesn't exist
        save_dir = "saved_drawings"
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
            except Exception as e:
                print(f"[ERROR] Failed to create folder '{save_dir}': {e}")
                self.show_notification("Save Failed: Dir Error")
                return None

        # Mask of where drawing exists
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)

        # Create the image to save
        if whiteboard_active:
            # Save exactly what is on the whiteboard
            bg_color = self.COLOR_PALETTE["DARK_GRAY"] if is_dark_bg else self.COLOR_PALETTE["WHITE"]
            save_img = np.full((self.h, self.w, 3), bg_color, dtype=np.uint8)
            img_bg = cv2.bitwise_and(save_img, save_img, mask=mask_inv)
            img_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
            save_img = cv2.add(img_bg, img_fg)
        else:
            # Whiteboard is off (camera overlay). Save the drawing on a clean white paper background.
            save_img = np.full((self.h, self.w, 3), (255, 255, 255), dtype=np.uint8)
            img_bg = cv2.bitwise_and(save_img, save_img, mask=mask_inv)
            img_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)
            save_img = cv2.add(img_bg, img_fg)

        # File name with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"airsketch_{timestamp}.png"
        filepath = os.path.join(save_dir, filename)

        try:
            cv2.imwrite(filepath, save_img)
            self.show_notification(f"Saved: {filename}")
            print(f"[INFO] Drawing saved successfully to: {filepath}")
            return filepath
        except Exception as e:
            print(f"[ERROR] Failed to write image: {e}")
            self.show_notification("Save Failed")
            return None

    def draw_ui(self, img, active_color, active_tool, brush_size, whiteboard_active, is_dark_bg):
        """
        Draws the header menu, buttons, indicators, and active notifications.
        
        Args:
            img (numpy.ndarray): The target image to draw the UI overlay onto.
            active_color (tuple): Currently selected drawing BGR color.
            active_tool (str): Active drawing tool ('pen' or 'eraser').
            brush_size (int): Active brush size in pixels.
            whiteboard_active (bool): Whether whiteboard mode is ON.
            is_dark_bg (bool): Whether whiteboard background is dark or light.
        """
        # 1. Glassmorphic Header Background
        # Draw a semi-transparent dark rectangle at the top
        overlay = img.copy()
        cv2.rectangle(overlay, (0, 0), (self.w, 90), self.COLOR_PALETTE["HUD_BG"], cv2.FILLED)
        # Apply transparency blend
        cv2.addWeighted(overlay, 0.85, img, 0.15, 0, img)

        # 2. Draw Title
        cv2.putText(img, "AirSketch AI", (20, 52), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 165, 255), 3, cv2.LINE_AA)
        
        # 3. Draw Buttons
        for btn in self.buttons:
            name = btn["name"]
            x1, y1, x2, y2 = btn["rect"]
            color = btn["color"]
            b_type = btn["type"]

            # Draw button shape
            if b_type == "color":
                # Circle for colors
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                radius = (x2 - x1) // 2
                
                # Check if this color is currently active and tool is pen
                is_active = (active_color == btn["value"]) and (active_tool == "pen")
                if is_active:
                    cv2.circle(img, (cx, cy), radius + 4, self.COLOR_PALETTE["TEXT_COLOR"], 3, cv2.LINE_AA)
                
                cv2.circle(img, (cx, cy), radius, color, cv2.FILLED)
            else:
                # Rounded or standard rectangle for tools/actions
                is_active = False
                label = name
                
                if name == "ERASER":
                    is_active = (active_tool == "eraser")
                    label = "ERASER"
                elif name == "BOARD":
                    is_active = whiteboard_active
                    label = "BOARD: " + ("DARK" if is_dark_bg else "LIGHT")
                    # Update board button color based on state
                    color = self.COLOR_PALETTE["DARK_GRAY"] if is_dark_bg else self.COLOR_PALETTE["WHITE"]
                
                # Draw border for active tools
                if is_active:
                    cv2.rectangle(img, (x1 - 3, y1 - 3), (x2 + 3, y2 + 3), (0, 165, 255), 3, cv2.LINE_AA)
                else:
                    cv2.rectangle(img, (x1, y1), (x2, y2), (80, 80, 80), 1, cv2.LINE_AA)

                cv2.rectangle(img, (x1, y1), (x2, y2), color, cv2.FILLED)
                
                # Button Text
                text_color = self.COLOR_PALETTE["TEXT_COLOR"] if name != "BOARD" or is_dark_bg else self.COLOR_PALETTE["DARK_GRAY"]
                text_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 2)[0]
                tx = x1 + (x2 - x1 - text_size[0]) // 2
                ty = y1 + (y2 - y1 + text_size[1]) // 2
                cv2.putText(img, label, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.45, text_color, 1, cv2.LINE_AA)

        # 4. Draw HUD Status Info (Bottom Panel)
        hud_y = self.h - 45
        # Draw bottom glassmorphic bar
        overlay_bottom = img.copy()
        cv2.rectangle(overlay_bottom, (0, self.h - 50), (self.w, self.h), self.COLOR_PALETTE["HUD_BG"], cv2.FILLED)
        cv2.addWeighted(overlay_bottom, 0.8, img, 0.2, 0, img)
        
        # Mode & brush state text
        mode_str = "ERASING" if active_tool == "eraser" else "DRAWING"
        state_text = f"Mode: {mode_str}  |  Size: {brush_size}px  |  BG: {'Whiteboard' if whiteboard_active else 'Webcam'}"
        cv2.putText(img, state_text, (20, self.h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, self.COLOR_PALETTE["TEXT_COLOR"], 1, cv2.LINE_AA)

        # 5. Draw Notification Banner
        if self.notification_timer > 0:
            self.notification_timer -= 1
            # Text size calculation
            n_size = cv2.getTextSize(self.notification_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            nx = (self.w - n_size[0]) // 2
            ny = 140
            
            # Notification background
            cv2.rectangle(img, (nx - 15, ny - 25), (nx + n_size[0] + 15, ny + 10), (20, 20, 20), cv2.FILLED)
            cv2.rectangle(img, (nx - 15, ny - 25), (nx + n_size[0] + 15, ny + 10), (0, 165, 255), 2)
            cv2.putText(img, self.notification_text, (nx, ny), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2, cv2.LINE_AA)

    def blend_canvas(self, bg_img, whiteboard_active, is_dark_bg=True):
        """
        Blends the drawing canvas with the background image (webcam frame or whiteboard).
        
        Args:
            bg_img (numpy.ndarray): The camera frame to blend with (if whiteboard is inactive).
            whiteboard_active (bool): Whether whiteboard mode is ON.
            is_dark_bg (bool): Whether whiteboard background is dark or light.
            
        Returns:
            numpy.ndarray: The final blended frame.
        """
        # Determine the base background image
        if whiteboard_active:
            # Create a solid color background
            bg_color = self.COLOR_PALETTE["DARK_GRAY"] if is_dark_bg else self.COLOR_PALETTE["WHITE"]
            base_bg = np.full((self.h, self.w, 3), bg_color, dtype=np.uint8)
        else:
            # Webcam frame is the background
            base_bg = bg_img.copy()

        # Mask of where drawing exists on the canvas (where canvas is NOT black)
        gray = cv2.cvtColor(self.canvas, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        mask_inv = cv2.bitwise_not(mask)

        # Clear the drawing area in the background frame
        img_bg = cv2.bitwise_and(base_bg, base_bg, mask=mask_inv)
        
        # Extract the drawing pixels from the canvas
        img_fg = cv2.bitwise_and(self.canvas, self.canvas, mask=mask)

        # Combine background and drawing canvas
        combined = cv2.add(img_bg, img_fg)
        return combined

    def check_button_click(self, x, y):
        """
        Checks if a given coordinate (finger tip) falls inside any UI buttons.
        
        Args:
            x (int): X coordinate.
            y (int): Y coordinate.
            
        Returns:
            dict: The button dictionary that was clicked, or None.
        """
        for btn in self.buttons:
            x1, y1, x2, y2 = btn["rect"]
            if x1 <= x <= x2 and y1 <= y <= y2:
                return btn
        return None
