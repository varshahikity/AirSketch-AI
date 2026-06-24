"""
AirSketch AI - Hand Tracking Module
Uses MediaPipe to detect and track hand landmarks in real-time.
Provides utility methods to determine finger states and gestures.
"""

import cv2
import numpy as np
import math
import mediapipe as mp

mp_hands = mp.solutions.hands
mp_draw = mp.solutions.drawing_utils
mp_draw_styles = mp.solutions.drawing_styles

# Import MediaPipe and explicitly import its submodules
# This prevents 'AttributeError: module mediapipe has no attribute solutions' on some platforms

mp_hands = mp.solutions.hands


class HandTracker:
    """
    Class to detect and track hand landmarks using MediaPipe.
    Provides utility methods to recognize gestures for drawing, selecting, and editing.
    """

    def __init__(self, mode=False, max_hands=1, model_complexity=1,
                 detection_confidence=0.75, tracking_confidence=0.65):
        """
        Initializes the MediaPipe Hands detector.

        Args:
            mode (bool): Treat input images as static images (True) or video frames (False).
            max_hands (int): Maximum number of hands to detect.
            model_complexity (int): Complexity of the hand landmark model (0 or 1).
            detection_confidence (float): Minimum confidence value ([0.0, 1.0]) for detection.
            tracking_confidence (float): Minimum confidence value ([0.0, 1.0]) for tracking.
        """
        self.mode = mode
        self.max_hands = max_hands
        self.model_complexity = model_complexity
        self.detection_confidence = detection_confidence
        self.tracking_confidence = tracking_confidence

        # Use the explicitly imported submodules to avoid attribute errors
        self.mp_hands = mp_hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=self.mode,
            max_num_hands=self.max_hands,
            model_complexity=self.model_complexity,
            min_detection_confidence=self.detection_confidence,
            min_tracking_confidence=self.tracking_confidence
        )
        self.mp_draw = mp_draw
        self.mp_draw_styles = mp_draw_styles
        self.results = None
        self.lm_list = []  # List of landmarks for the active hand

    def find_hands(self, img, draw=True):
        """
        Processes the BGR frame to detect hands and optionally draws landmarks.

        Args:
            img (numpy.ndarray): The BGR frame from the webcam.
            draw (bool): Whether to draw landmark connections on the image.

        Returns:
            numpy.ndarray: The frame with optional drawings.
        """
        # Convert BGR to RGB for MediaPipe
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        try:
            self.results = self.hands.process(img_rgb)
        except Exception as e:
            # Handle processing exceptions gracefully
            print(f"[ERROR] MediaPipe processing failed: {e}")
            return img

        if self.results.multi_hand_landmarks:
            for hand_lms in self.results.multi_hand_landmarks:
                if draw:
                    # Draw elegant stylized landmarks and connections
                    self.mp_draw.draw_landmarks(
                        img,
                        hand_lms,
                        self.mp_hands.HAND_CONNECTIONS,
                        self.mp_draw_styles.get_default_hand_landmarks_style(),
                        self.mp_draw_styles.get_default_hand_connections_style()
                    )
        return img

    def find_position(self, img, hand_no=0, draw=False):
        """
        Extracts landmark coordinates for a specific hand.

        Args:
            img (numpy.ndarray): The BGR frame.
            hand_no (int): The index of the hand to track.
            draw (bool): Whether to draw a circle on the tracked landmarks.

        Returns:
            list: A list of landmarks, where each item is [id, x, y, z].
        """
        self.lm_list = []
        if self.results and self.results.multi_hand_landmarks:
            # Verify the requested hand index is within range
            if hand_no < len(self.results.multi_hand_landmarks):
                my_hand = self.results.multi_hand_landmarks[hand_no]
                h, w, c = img.shape
                for id, lm in enumerate(my_hand.landmark):
                    # Convert normalized coordinates to pixel coordinates
                    cx, cy = int(lm.x * w), int(lm.y * h)
                    self.lm_list.append([id, cx, cy, lm.z])
                    if draw:
                        cv2.circle(img, (cx, cy), 5, (255, 0, 255), cv2.FILLED)
        return self.lm_list

    def get_handedness(self, hand_no=0):
        """
        Determines whether the tracked hand is Left or Right.

        Args:
            hand_no (int): The index of the hand.

        Returns:
            str: 'Left', 'Right', or 'Unknown'.
        """
        if self.results and self.results.multi_handedness:
            if hand_no < len(self.results.multi_handedness):
                return self.results.multi_handedness[hand_no].classification[0].label
        return "Unknown"

    def fingers_up(self, hand_no=0):
        """
        Determines which fingers are open/extended.

        Args:
            hand_no (int): The index of the hand.

        Returns:
            list: A list of 5 binary values [thumb, index, middle, ring, pinky] 
                  where 1 is open and 0 is closed.
        """
        if not self.lm_list or len(self.lm_list) < 21:
            return [0, 0, 0, 0, 0]

        fingers = []

        # 1. Thumb Check
        # The thumb state depends on whether the hand is Left or Right.
        # Since the image is mirrored, we check the classification of the hand.
        hand_type = self.get_handedness(hand_no)

        # Tip of thumb (4) compared to the joint (3 or 2)
        # Note: If hand is upright, checking horizontal expansion works well.
        # For a right hand (mirrored to appear on the right): extended if tip is to the right of joint 3.
        # For a left hand: extended if tip is to the left of joint 3.
        if hand_type == "Right":
            if self.lm_list[4][1] > self.lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)
        else:
            if self.lm_list[4][1] < self.lm_list[3][1]:
                fingers.append(1)
            else:
                fingers.append(0)

        # 2. Four Fingers Check (Index, Middle, Ring, Pinky)
        # Tip landmarks: Index (8), Middle (12), Ring (16), Pinky (20)
        # Pip landmarks: Index (6), Middle (10), Ring (14), Pinky (18)
        # If tip Y is less than PIP Y (since Y-axis goes down), the finger is open.
        tips = [8, 12, 16, 20]
        pips = [6, 10, 14, 18]
        for tip, pip in zip(tips, pips):
            if self.lm_list[tip][2] < self.lm_list[pip][2]:
                fingers.append(1)
            else:
                fingers.append(0)

        return fingers

    def get_distance(self, p1, p2, img=None, draw=False):
        """
        Calculates the pixel distance between two landmarks.

        Args:
            p1 (int): Landmark index of point 1.
            p2 (int): Landmark index of point 2.
            img (numpy.ndarray): Optional frame to draw a visual line on.
            draw (bool): Whether to draw a line and circles connecting the points.

        Returns:
            tuple: (distance, midpoint_x, midpoint_y)
        """
        if not self.lm_list or len(self.lm_list) < max(p1, p2):
            return 0, 0, 0

        x1, y1 = self.lm_list[p1][1], self.lm_list[p1][2]
        x2, y2 = self.lm_list[p2][1], self.lm_list[p2][2]
        cx, cy = (x1 + x2) // 2, (y1 + y2) // 2

        distance = math.hypot(x2 - x1, y2 - y1)

        if draw and img is not None:
            cv2.line(img, (x1, y1), (x2, y2), (255, 0, 255), 3)
            cv2.circle(img, (x1, y1), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (x2, y2), 8, (255, 0, 255), cv2.FILLED)
            cv2.circle(img, (cx, cy), 10, (0, 0, 255), cv2.FILLED)

        return distance, cx, cy
