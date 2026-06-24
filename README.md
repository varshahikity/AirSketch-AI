# AirSketch AI

AirSketch AI is a touchless, AI-powered virtual drawing system that allows users to paint in the air using simple hand gestures. By tracking hand movements in real-time through a standard webcam, it translates physical finger movements into beautiful digital strokes on screen.

---

## Why this project? (Interview Explanation)

> "I built AirSketch AI to explore computer vision and human-computer interaction. The goal was to create a touchless drawing experience using hand gestures. This project helped me understand real-time image processing, hand landmark detection, gesture recognition, and OpenCV-based application development. It also demonstrates how AI and computer vision can be used to build intuitive and accessible user interfaces."

---

## Features

### 1. Core Mechanics
* **Real-Time Webcam Feed:** Smooth camera mirroring provides a natural "mirror" drawing experience.
* **Robust Hand Detection:** Uses Google's MediaPipe framework to detect all 21 key points of a single hand.
* **Precise Index Finger Tracking:** Tracks the tip of the index finger continuously, serving as a highly responsive virtual pen.
* **Smooth Continuous Drawing:** Uses line-segment interpolation between frames to ensure seamless drawing without jagged gaps.

### 2. Rich User Interface & Interactive Controls
* **Top Header Menu:** Features colorful round palette buttons (Red, Blue, Green, Yellow), an Eraser, a Canvas Reset button, an Image Save button, and a Whiteboard Toggle.
* **Dynamic HUD Overlay:** Displays current status information at the bottom (selected tool, active brush size, background mode) and a real-time FPS counter in the top-right corner.
* **Interactive Status Banner:** Temporary overlays show feedback when actions are triggered (e.g., "Saved successfully!", "Canvas Cleared").
* **Multi-Mode Backgrounds:** Cycle between three interactive backgrounds:
  1. **Camera Mode:** Overlays the drawing directly on your mirrored webcam stream.
  2. **Chalkboard Mode:** Drawing on a clean dark slate background.
  3. **Whiteboard Mode:** Drawing on a clean white digital paper background.

### 3. Gesture Shortcuts & Controls
* **Selection Mode (2 Fingers UP):** Raise your index and middle fingers to move a cursor. **Pinch/bring them close together** to "click" and activate header buttons!
* **Drawing Mode (1 Finger UP):** Raise only your index finger (with middle finger down) to start drawing.
* **Brush Size Control (Thumb & Index UP):** Spread your thumb and index finger apart or pinch them together to dynamically scale the brush size (5px to 60px) in real-time, complete with an interactive preview circle.
* **Gesture Clear Canvas (5 Fingers UP - Hold):** Hold all 5 fingers spread open for 2 seconds. A circular progress indicator will load around your palm. Once complete, the canvas resets!

### 4. Image Saving
* **Export Drawing:** Press the **SAVE** button or tap the `s` key to save your creation.
* **Smart Backgrounds:** Saves drawings from Chalkboard or Whiteboard modes exactly as they appear, and saves camera-mode drawings on a clean white paper background, ideal for exporting sketches.
* **Storage:** Files are stored locally in the `saved_drawings/` folder with unique timestamps (e.g., `airsketch_20260624_214100.png`).

---

## Technologies Used

* **Python 3.8+** - Core programming language.
* **OpenCV** - Real-time image processing, camera capture, and GUI rendering.
* **MediaPipe** - State-of-the-art hand landmark detection and tracking.
* **NumPy** - Fast multi-dimensional array manipulation for canvas rendering.

---

## Folder Structure

```text
AirSketch-AI/
│
├── main.py               # Main application loop and controller
├── hand_tracker.py       # MediaPipe Hand detection & gesture helper class
├── drawing_canvas.py     # Drawing canvas rendering & HUD overlay class
├── requirements.txt      # Project dependencies
├── README.md             # Project documentation
│
├── assets/
│   ├── icons/            # Asset icons (optional)
│   └── screenshots/      # Application demo screenshots
│
└── saved_drawings/       # Saved drawings (automatically created)
```

---

## Installation Steps

1. **Clone or Download the Repository:**
   Ensure all files (`main.py`, `hand_tracker.py`, `drawing_canvas.py`, `requirements.txt`) are placed together in a directory named `AirSketch-AI`.

2. **Open Terminal & Navigate to the Project:**
   ```bash
   cd AirSketch-AI
   ```

3. **Install Dependencies:**
   Install the required libraries via `pip`:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage Guide

Run the application:
```bash
python main.py
```

### Gestures Guide
* **To Draw:** Hold up only your **index finger**. Moving your index fingertip draws lines of the active color.
* **To Erase:** Open the top menu using Selection Mode, hover over **ERASER**, and pinch your fingers to click. Now, drawing with your index finger will erase strokes.
* **To Change Color:** Open the top menu in Selection Mode, hover over a color button (Red, Blue, Green, Yellow), and pinch to select it.
* **To Adjust Brush Size:** Hold up only your **thumb and index finger**. Move them closer or further apart to shrink or enlarge the brush. Release to lock in the size.
* **To Reset Canvas:** Hold up **all 5 fingers** spread wide. A red timer will load on your hand. Keep it open for 2 seconds to clear the canvas. Alternatively, click the **CLEAR** button in the header.
* **To Save Drawing:** Hover over **SAVE** in the header and pinch to click, or press the `s` key. Your drawing will be exported to the `saved_drawings/` folder.

### Keyboard Shortcuts
* `q`: Quit the application.
* `c`: Clear the canvas.
* `s`: Save the drawing.
* `b`: Toggle whiteboard/webcam background modes.
* `e`: Activate Eraser tool.
* `p`: Activate Pen tool (resets to Red).
* `1` - `4`: Select colors (1: Red, 2: Blue, 3: Green, 4: Yellow).

---

## Future Improvements

* **Multi-Hand Support:** Enable simultaneous drawing with two hands or cooperative collaborative drawing.
* **Handwriting Recognition:** Add an AI model (like a CNN) that recognizes and digitizes text written in the air.
* **Shape Recognition:** Detect when a user draws rough shapes (circles, squares, triangles) and auto-correct them into clean geometric shapes.
* **3D Air Drawing:** Use depth estimation (using MediaPipe's landmark Z-axis coordinates) to allow drawing in virtual 3D space with 3D rotation.

---

## Screenshots

*(Screenshots can be added here to demonstrate the application in action)*
