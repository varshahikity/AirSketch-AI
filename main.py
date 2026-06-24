"""
AirSketch AI - Main Application Controller
Sets up webcam capture, coordinates hand tracking and gesture recognition,
manages drawing modes, and runs the central execution loop.
"""

import cv2
import numpy as np
import time
import os
import sys
import traceback

# Import custom modules
from hand_tracker import HandTracker
from drawing_canvas import DrawingCanvas

def main():
    """
    Main entry point for the AirSketch AI application.
    Initializes webcam, hand tracker, and canvas, and runs the frame loop.
    """
    print("[INFO] Initializing AirSketch AI...")
    
    # 1. Initialize Webcam Capture
    # Try index 0. If it fails, try 1 or 2.
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam at index 0. Trying alternative camera index 1...")
        cap = cv2.VideoCapture(1)
        if not cap.isOpened():
            print("[ERROR] Could not open webcam at index 1. Trying index 2...")
            cap = cv2.VideoCapture(2)
            if not cap.isOpened():
                print("\n[CRITICAL] No webcam detected.")
                print("Please ensure your webcam is connected, not being used by another app (like Zoom or Teams), and try again.")
                input("\nPress Enter to exit...")
                sys.exit(1)

    # Set camera resolution (1280x720 is ideal for drawing canvas)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    
    # Read a dummy frame to verify dimensions
    success, frame = cap.read()
    if not success or frame is None:
        print("\n[CRITICAL] Failed to read from webcam.")
        print("Your webcam was opened but did not return any image frames. It may be blocked by another application or permissions.")
        input("\nPress Enter to exit...")
        sys.exit(1)

    h, w, c = frame.shape
    print(f"[INFO] Webcam initialized successfully: {w}x{h}")

    # 2. Initialize Hand Tracker and Canvas
    # Configured with 1 hand max for optimized drawing performance.
    tracker = HandTracker(
        max_hands=1, 
        detection_confidence=0.75, 
        tracking_confidence=0.70
    )
    canvas_manager = DrawingCanvas(width=w, height=h)

    # 3. State Variables
    active_color = (0, 0, 255)  # Default: Red
    active_tool = "pen"         # 'pen' or 'eraser'
    brush_size = 10             # Default brush thickness
    
    whiteboard_active = False   # Start with webcam background
    is_dark_bg = True           # Whiteboard default is Dark Mode (Chalkboard)

    xp, yp = 0, 0               # Previous coordinate points for continuous lines
    click_cooldown = 0          # Prevent multiple rapid clicks in Selection Mode
    clear_gesture_timer = 0      # Hold 5 fingers for 2 seconds (60 frames at 30 fps) to clear
    frame_count = 0             # Frame counter to avoid race conditions with window property checks
    
    # FPS tracking variables
    prev_time = time.time()
    
    print("\n[INFO] AirSketch AI is running.")
    print("--------------------------------------------------")
    print("CONTROLS:")
    print("  - Index Finger UP: Draw")
    print("  - Index & Middle Fingers UP: Select colors/tools (Pinch fingers to Click)")
    print("  - Thumb & Index Fingers UP: Adjust Brush Size by spreading fingers")
    print("  - All 5 Fingers UP (Hold 2 seconds): Clear Canvas")
    print("  - Keyboard Shortcuts:")
    print("    'q': Quit | 'c': Clear | 's': Save | 'b': Toggle Whiteboard | 'e': Eraser")
    print("--------------------------------------------------")

    # Create window and set it to be resizable
    window_name = "AirSketch AI"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window_name, w, h)

    # Main Loop
    while cap.isOpened():
        success, img = cap.read()
        if not success or img is None:
            print("[WARNING] Empty frame received from webcam. Skipping frame.")
            time.sleep(0.01)
            continue

        # A. Mirror image for natural physical drawing experience
        img = cv2.flip(img, 1)
        
        # B. Ensure canvas dimensions match camera frame dynamically
        frame_h, frame_w, _ = img.shape
        canvas_manager.update_dimensions(frame_w, frame_h)

        # C. Detect hand landmarks
        img = tracker.find_hands(img, draw=True)
        lm_list = tracker.find_position(img, draw=False)
        
        # Decrement cooldown timers
        if click_cooldown > 0:
            click_cooldown -= 1

        # D. Process hand state and recognize gestures
        if lm_list and len(lm_list) >= 21:
            fingers = tracker.fingers_up()
            
            # Extract key landmarks for easy access
            # Index Tip (8), Middle Tip (12), Thumb Tip (4)
            x1, y1 = lm_list[8][1], lm_list[8][2]
            x2, y2 = lm_list[12][1], lm_list[12][2]
            
            # Reset clear gesture if fingers are not all up
            if sum(fingers) != 5:
                clear_gesture_timer = 0

            # --------------------------
            # GESTURE 1: SELECTION MODE
            # --------------------------
            # Trigger: Index and Middle fingers are UP, other fingers are DOWN
            if fingers[1] == 1 and fingers[2] == 1 and fingers[3] == 0 and fingers[4] == 0:
                # Reset previous drawing coordinate to avoid connecting lines
                xp, yp = 0, 0
                
                # Draw a selection cursor at the midpoint
                dist, cx, cy = tracker.get_distance(8, 12, img, draw=False)
                
                # Visual indicator for selection mode: Draw a crosshair or target
                cv2.circle(img, (cx, cy), 12, (0, 165, 255), 2, cv2.LINE_AA)
                cv2.circle(img, (cx, cy), 2, (0, 165, 255), cv2.FILLED)
                
                # Check for "Click" gesture: Pinching index and middle fingers together (distance < 35px)
                is_click = dist < 35
                
                # If hovering over the top menu bar (y < 90)
                if cy < 90:
                    btn = canvas_manager.check_button_click(cx, cy)
                    if btn:
                        # Highlight the hovered button with a glowing border
                        bx1, by1, bx2, by2 = btn["rect"]
                        cv2.rectangle(img, (bx1, by1), (bx2, by2), (0, 255, 0), 2, cv2.LINE_AA)
                        
                        # Process click action
                        if is_click and click_cooldown == 0:
                            click_cooldown = 15  # 0.5 second cooldown at 30fps
                            action_type = btn["type"]
                            
                            # Visual Click Feedback (Expand circle)
                            cv2.circle(img, (cx, cy), 25, (0, 255, 0), 4, cv2.LINE_AA)
                            
                            if action_type == "color":
                                active_color = btn["value"]
                                active_tool = "pen"
                                canvas_manager.show_notification(f"Color: {btn['name']}")
                            elif action_type == "tool":
                                active_tool = "eraser"
                                active_color = (0, 0, 0)
                                canvas_manager.show_notification("Tool: ERASER")
                            elif action_type == "action":
                                action_val = btn["value"]
                                if action_val == "clear":
                                    canvas_manager.clear()
                                elif action_val == "save":
                                    canvas_manager.save_canvas(whiteboard_active, is_dark_bg)
                                elif action_val == "toggle_board":
                                    # Cycle: Webcam -> Chalkboard (Dark) -> Whiteboard (Light)
                                    if not whiteboard_active:
                                        whiteboard_active = True
                                        is_dark_bg = True
                                        canvas_manager.show_notification("Board: Chalkboard Mode")
                                    elif whiteboard_active and is_dark_bg:
                                        is_dark_bg = False
                                        canvas_manager.show_notification("Board: Whiteboard Mode")
                                    else:
                                        whiteboard_active = False
                                        canvas_manager.show_notification("Camera Mode Enabled")

            # --------------------------
            # GESTURE 2: DRAWING MODE
            # --------------------------
            # Trigger: Only Index finger is UP, Middle finger is DOWN
            elif fingers[1] == 1 and fingers[2] == 0:
                # If this is the start of a line, anchor the coordinate
                if xp == 0 and yp == 0:
                    xp, yp = x1, y1
                
                # Draw on canvas
                draw_color = (0, 0, 0) if active_tool == "eraser" else active_color
                # Smooth drawing by connecting previous point (xp, yp) to current (x1, y1)
                canvas_manager.draw_line((xp, yp), (x1, y1), draw_color, brush_size)
                
                # Update previous position
                xp, yp = x1, y1
                
                # Draw glowing cursor at fingertip on camera view
                cv2.circle(img, (x1, y1), brush_size // 2 + 3, (0, 165, 255), 2, cv2.LINE_AA)
                cv2.circle(img, (x1, y1), 3, draw_color, cv2.FILLED)

            # --------------------------
            # GESTURE 3: BRUSH SIZE ADJUST
            # --------------------------
            # Trigger: Thumb and Index fingers UP, others DOWN
            elif fingers[0] == 1 and fingers[1] == 1 and fingers[2] == 0 and fingers[3] == 0 and fingers[4] == 0:
                xp, yp = 0, 0 # Reset drawing anchors
                
                # Draw a connection line and get distance between thumb and index
                dist, cx, cy = tracker.get_distance(4, 8, img, draw=True)
                
                # Interpolate distance (ranging roughly from 30px to 220px) to brush size (5px to 60px)
                brush_size = int(np.interp(dist, [30, 220], [5, 60]))
                
                # Draw a live preview circle representing the brush size at the midpoint
                preview_color = (120, 120, 120) if active_tool == "eraser" else active_color
                cv2.circle(img, (cx, cy), brush_size // 2, preview_color, cv2.FILLED)
                cv2.circle(img, (cx, cy), brush_size // 2 + 2, (255, 255, 255), 2, cv2.LINE_AA)
                
                # Draw text displaying size
                cv2.putText(img, f"Size: {brush_size}px", (cx - 40, cy - brush_size // 2 - 15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (240, 240, 240), 1, cv2.LINE_AA)

            # --------------------------
            # GESTURE 4: HAND GESTURE CLEAR CANVAS
            # --------------------------
            # Trigger: All 5 fingers UP (spread hand)
            elif sum(fingers) == 5:
                xp, yp = 0, 0 # Reset drawing anchors
                clear_gesture_timer += 1
                
                # Palm center (approximate using landmark 9)
                cx, cy = lm_list[9][1], lm_list[9][2]
                
                # Visual countdown: Draw a loading circle arc
                progress = min(clear_gesture_timer / 60.0, 1.0) # 2 seconds at ~30 FPS
                angle = int(progress * 360)
                
                # Circular progress background
                cv2.circle(img, (cx, cy), 45, (80, 80, 80), 2, cv2.LINE_AA)
                # Colored progress arc
                cv2.ellipse(img, (cx, cy), (45, 45), -90, 0, angle, (0, 0, 255), 4, cv2.LINE_AA)
                cv2.putText(img, "CLEARING", (cx - 35, cy + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 0, 255), 1, cv2.LINE_AA)
                
                if clear_gesture_timer >= 60:
                    canvas_manager.clear()
                    clear_gesture_timer = 0
            
            else:
                # If any other unhandled gesture is shown, reset drawing anchors
                xp, yp = 0, 0
        else:
            # If no hand is in frame, reset drawing anchors and clear timer
            xp, yp = 0, 0
            clear_gesture_timer = 0

        # E. Blend drawing canvas with background
        blended = canvas_manager.blend_canvas(img, whiteboard_active, is_dark_bg)
        
        # F. Draw Menu Overlay & HUD
        canvas_manager.draw_ui(blended, active_color, active_tool, brush_size, whiteboard_active, is_dark_bg)

        # G. Calculate and Display FPS
        curr_time = time.time()
        fps = 1.0 / (curr_time - prev_time)
        prev_time = curr_time
        cv2.putText(blended, f"FPS: {int(fps)}", (w - 100, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 0), 2, cv2.LINE_AA)

        # H. Render Frame Window
        cv2.imshow(window_name, blended)

        # I. Handle Keyboard Shortcuts
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('c'):
            canvas_manager.clear()
        elif key == ord('s'):
            canvas_manager.save_canvas(whiteboard_active, is_dark_bg)
        elif key == ord('b'):
            # Toggle whiteboard mode via keyboard
            whiteboard_active = not whiteboard_active
            canvas_manager.show_notification("Board Toggled" if whiteboard_active else "Camera Toggled")
        elif key == ord('e'):
            active_tool = "eraser"
            active_color = (0, 0, 0)
            canvas_manager.show_notification("Tool: ERASER")
        elif key == ord('p'):
            active_tool = "pen"
            active_color = (0, 0, 255) # Red default
            canvas_manager.show_notification("Tool: PEN (RED)")
        elif key == ord('1'):
            active_color = (0, 0, 255) # Red
            active_tool = "pen"
            canvas_manager.show_notification("Color: RED")
        elif key == ord('2'):
            active_color = (255, 0, 0) # Blue
            active_tool = "pen"
            canvas_manager.show_notification("Color: BLUE")
        elif key == ord('3'):
            active_color = (0, 255, 0) # Green
            active_tool = "pen"
            canvas_manager.show_notification("Color: GREEN")
        elif key == ord('4'):
            active_color = (0, 255, 255) # Yellow
            active_tool = "pen"
            canvas_manager.show_notification("Color: YELLOW")

        # J. Check if the window was closed via the OS [x] close button
        # To avoid race conditions, we only check this after a few frames are rendered.
        frame_count += 1
        if frame_count > 15:
            try:
                # getWindowProperty returns -1.0 or 0.0 if the window is closed
                if cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE) < 1:
                    break
            except Exception:
                # If an error is thrown, the window has likely been destroyed
                break

    # Clean up resources
    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] AirSketch AI shut down successfully.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Catch any unexpected runtime errors, print them, and prevent the terminal from auto-closing
        print("\n" + "="*50)
        print("[CRITICAL ERROR] The application encountered a crash:")
        print("="*50)
        traceback.print_exc()
        print("="*50)
        print("\nTroubleshooting tips:")
        print("1. Ensure you have installed all requirements: pip install -r requirements.txt")
        print("2. Ensure your webcam is connected and not in use by another program.")
        print("3. Check that your Python environment is configured correctly.")
        print("="*50)
        input("\nPress Enter to exit...")
