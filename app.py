import cv2
import numpy as np
import time
import gradio as gr

from hand_tracker import HandTracker
from drawing_canvas import DrawingCanvas


# -----------------------------
# Create tracker once
# -----------------------------
tracker = HandTracker(
    max_hands=1,
    detection_confidence=0.75,
    tracking_confidence=0.70
)


# -----------------------------
# Initial application state
# -----------------------------
def initial_state():
    return {
        "canvas": None,
        "xp": 0,
        "yp": 0,
        "active_color": (0, 0, 255),  # Red
        "active_tool": "pen",
        "brush_size": 10,
        "whiteboard_active": False,
        "is_dark_bg": True,
        "click_cooldown": 0,
        "clear_gesture_timer": 0,
        "last_time": time.time()
    }


# -----------------------------
# Main frame processing
# -----------------------------
def process_frame(img, state):
    if img is None:
        return None, state

    # Gradio gives RGB image
    frame = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)

    # Mirror image
    frame = cv2.flip(frame, 1)

    h, w, _ = frame.shape

    # Create canvas for this session
    if state["canvas"] is None:
        state["canvas"] = DrawingCanvas(width=w, height=h)

    else:
        state["canvas"].update_dimensions(w, h)

    canvas_manager = state["canvas"]

    # Reduce click cooldown
    if state["click_cooldown"] > 0:
        state["click_cooldown"] -= 1

    # -----------------------------
    # Hand detection
    # -----------------------------
    frame = tracker.find_hands(frame, draw=True)
    lm_list = tracker.find_position(frame, draw=False)

    if lm_list and len(lm_list) >= 21:

        fingers = tracker.fingers_up()

        # Index finger
        x1, y1 = lm_list[8][1], lm_list[8][2]

        # Middle finger
        x2, y2 = lm_list[12][1], lm_list[12][2]

        # -----------------------------
        # Selection Mode
        # Index + Middle UP
        # -----------------------------
        if (
            fingers[1] == 1
            and fingers[2] == 1
            and fingers[3] == 0
            and fingers[4] == 0
        ):

            state["xp"] = 0
            state["yp"] = 0

            dist, cx, cy = tracker.get_distance(
                8, 12, frame, draw=False
            )

            cv2.circle(
                frame,
                (cx, cy),
                12,
                (0, 165, 255),
                2
            )

            cv2.circle(
                frame,
                (cx, cy),
                2,
                (0, 165, 255),
                cv2.FILLED
            )

            is_click = dist < 35

            # Check top menu
            if cy < 90:

                btn = canvas_manager.check_button_click(cx, cy)

                if btn:

                    bx1, by1, bx2, by2 = btn["rect"]

                    cv2.rectangle(
                        frame,
                        (bx1, by1),
                        (bx2, by2),
                        (0, 255, 0),
                        2
                    )

                    if (
                        is_click
                        and state["click_cooldown"] == 0
                    ):

                        state["click_cooldown"] = 15

                        action_type = btn["type"]

                        if action_type == "color":

                            state["active_color"] = btn["value"]
                            state["active_tool"] = "pen"

                            canvas_manager.show_notification(
                                f"Color: {btn['name']}"
                            )

                        elif action_type == "tool":

                            state["active_tool"] = "eraser"
                            state["active_color"] = (0, 0, 0)

                            canvas_manager.show_notification(
                                "Tool: ERASER"
                            )

                        elif action_type == "action":

                            action = btn["value"]

                            if action == "clear":

                                canvas_manager.clear()

                            elif action == "toggle_board":

                                if not state["whiteboard_active"]:

                                    state["whiteboard_active"] = True
                                    state["is_dark_bg"] = True

                                    canvas_manager.show_notification(
                                        "Board: Chalkboard Mode"
                                    )

                                elif state["is_dark_bg"]:

                                    state["is_dark_bg"] = False

                                    canvas_manager.show_notification(
                                        "Board: Whiteboard Mode"
                                    )

                                else:

                                    state["whiteboard_active"] = False

                                    canvas_manager.show_notification(
                                        "Camera Mode Enabled"
                                    )

        # -----------------------------
        # Drawing Mode
        # Index UP, Middle DOWN
        # -----------------------------
        elif fingers[1] == 1 and fingers[2] == 0:

            if state["xp"] == 0 and state["yp"] == 0:

                state["xp"] = x1
                state["yp"] = y1

            draw_color = (
                (0, 0, 0)
                if state["active_tool"] == "eraser"
                else state["active_color"]
            )

            canvas_manager.draw_line(
                (state["xp"], state["yp"]),
                (x1, y1),
                draw_color,
                state["brush_size"]
            )

            state["xp"] = x1
            state["yp"] = y1

            cv2.circle(
                frame,
                (x1, y1),
                state["brush_size"] // 2 + 3,
                (0, 165, 255),
                2
            )

            cv2.circle(
                frame,
                (x1, y1),
                3,
                draw_color,
                cv2.FILLED
            )

        # -----------------------------
        # Brush Size Mode
        # Thumb + Index UP
        # -----------------------------
        elif (
            fingers[0] == 1
            and fingers[1] == 1
            and fingers[2] == 0
            and fingers[3] == 0
            and fingers[4] == 0
        ):

            state["xp"] = 0
            state["yp"] = 0

            dist, cx, cy = tracker.get_distance(
                4, 8, frame, draw=True
            )

            state["brush_size"] = int(
                np.interp(
                    dist,
                    [30, 220],
                    [5, 60]
                )
            )

            preview_color = (
                (120, 120, 120)
                if state["active_tool"] == "eraser"
                else state["active_color"]
            )

            cv2.circle(
                frame,
                (cx, cy),
                state["brush_size"] // 2,
                preview_color,
                cv2.FILLED
            )

            cv2.circle(
                frame,
                (cx, cy),
                state["brush_size"] // 2 + 2,
                (255, 255, 255),
                2
            )

            cv2.putText(
                frame,
                f"Size: {state['brush_size']}px",
                (
                    cx - 40,
                    cy - state["brush_size"] // 2 - 15
                ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (240, 240, 240),
                1
            )

        # -----------------------------
        # Clear Gesture
        # All 5 fingers UP
        # -----------------------------
        elif sum(fingers) == 5:

            state["xp"] = 0
            state["yp"] = 0

            state["clear_gesture_timer"] += 1

            cx = lm_list[9][1]
            cy = lm_list[9][2]

            progress = min(
                state["clear_gesture_timer"] / 60.0,
                1.0
            )

            angle = int(progress * 360)

            cv2.circle(
                frame,
                (cx, cy),
                45,
                (80, 80, 80),
                2
            )

            cv2.ellipse(
                frame,
                (cx, cy),
                (45, 45),
                -90,
                0,
                angle,
                (0, 0, 255),
                4
            )

            cv2.putText(
                frame,
                "CLEARING",
                (cx - 35, cy + 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.4,
                (0, 0, 255),
                1
            )

            if state["clear_gesture_timer"] >= 60:

                canvas_manager.clear()

                state["clear_gesture_timer"] = 0

        else:

            state["xp"] = 0
            state["yp"] = 0

    else:

        state["xp"] = 0
        state["yp"] = 0
        state["clear_gesture_timer"] = 0

    # -----------------------------
    # Blend drawing with background
    # -----------------------------
    blended = canvas_manager.blend_canvas(
        frame,
        state["whiteboard_active"],
        state["is_dark_bg"]
    )

    # -----------------------------
    # Draw UI
    # -----------------------------
    canvas_manager.draw_ui(
        blended,
        state["active_color"],
        state["active_tool"],
        state["brush_size"],
        state["whiteboard_active"],
        state["is_dark_bg"]
    )

    # -----------------------------
    # FPS
    # -----------------------------
    current_time = time.time()

    fps = 1 / max(
        current_time - state["last_time"],
        0.001
    )

    state["last_time"] = current_time

    cv2.putText(
        blended,
        f"FPS: {int(fps)}",
        (w - 100, 52),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        (0, 255, 0),
        2
    )

    # Convert BGR -> RGB for Gradio
    output = cv2.cvtColor(
        blended,
        cv2.COLOR_BGR2RGB
    )

    return output, state


# -----------------------------
# Reset function
# -----------------------------
def reset_app():
    return initial_state()


# -----------------------------
# Gradio Interface
# -----------------------------
with gr.Blocks(
    title="AirSketch AI"
) as demo:

    gr.Markdown(
        """
        # ✋ AirSketch AI

        **Draw in the air using your hand gestures!**

        ### Gestures

        🖐️ **Index finger** → Draw

        ✌️ **Index + Middle fingers** → Select

        🤏 **Thumb + Index fingers** → Change brush size

        🖐️ **All 5 fingers for 2 seconds** → Clear canvas
        """
    )

    state = gr.State(initial_state())

    camera = gr.Image(
        sources=["webcam"],
        type="numpy",
        label="Webcam"
    )

    output = gr.Image(
        type="numpy",
        label="AirSketch AI Output"
    )

    reset_button = gr.Button("🔄 Reset")

    reset_button.click(
        fn=reset_app,
        inputs=None,
        outputs=state
    )

    camera.stream(
        fn=process_frame,
        inputs=[camera, state],
        outputs=[output, state],
        time_limit=30,
        stream_every=0.05
    )


# -----------------------------
# Start application
# -----------------------------
if __name__ == "__main__":
    import os

    demo.launch(
        server_name="0.0.0.0",
        server_port=int(os.environ.get("PORT", 10000)),
        share=False
    )
