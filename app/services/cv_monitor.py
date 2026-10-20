import base64
import os
import cv2
import numpy as np

class CVMonitorService:
    def __init__(self):
        # Load OpenCV's built-in Haar Cascade for frontal face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(f"Haar cascade file not found at {cascade_path}")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Load eye cascade for gaze / orientation analysis
        eye_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_path) if os.path.exists(eye_path) else None

    def analyze_frame_bytes(self, image_bytes: bytes) -> dict:
        """
        Analyze a raw image byte buffer and inspect for:
        - Face count (0 -> NO_FACE, 1 -> check gaze/phone, 2 -> MULTIPLE_FACES [MED], 3+ -> MULTIPLE_FACES [HIGH])
        - Gaze shift (head or eye orientation turned away)
        - Mobile phone in frame (rectangular handheld device contour)
        Returns ethical monitoring status and detected anomalies without storing footage.
        """
        try:
            nparr = np.frombuffer(image_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                return {
                    "success": False,
                    "error": "Invalid image data received",
                    "face_count": 0,
                    "status": "ERROR"
                }

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_h, img_w = gray.shape[:2]

            # 1. Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=4,
                minSize=(30, 30)
            )

            face_count = len(faces)

            # If 0 faces, check if a phone is present in frame before defaulting to NO_FACE
            if face_count == 0:
                if self._detect_phone_in_frame(gray, (0, 0, 0, 0)):
                    return {
                        "success": True,
                        "face_count": 0,
                        "status": "INCIDENT",
                        "incident_type": "PHONE_DETECTED",
                        "severity": "HIGH",
                        "details": "Mobile phone or electronic device detected in candidate webcam frame."
                    }
                return self._classify_face_count(0)
            elif face_count > 1:
                return self._classify_face_count(face_count)

            # 2. When 1 face is present, inspect for phone or gaze shift
            (fx, fy, fw, fh) = faces[0]

            # Check for phone in frame (rectangular handheld contour in lower/side area)
            phone_detected = self._detect_phone_in_frame(gray, faces[0])
            if phone_detected:
                return {
                    "success": True,
                    "face_count": 1,
                    "status": "INCIDENT",
                    "incident_type": "PHONE_DETECTED",
                    "severity": "HIGH",
                    "details": "Mobile phone or electronic device detected in candidate webcam frame."
                }

            # Check for gaze shift (face shifted to extreme margins or eyes turned away)
            face_center_x = (fx + fw / 2) / img_w
            if face_center_x < 0.18 or face_center_x > 0.82:
                return {
                    "success": True,
                    "face_count": 1,
                    "status": "INCIDENT",
                    "incident_type": "GAZE_SHIFT",
                    "severity": "LOW",
                    "details": "Candidate head orientation or gaze shifted away from exam screen."
                }

            # Eye tracking within upper region of face
            if self.eye_cascade and fw >= 50 and fh >= 50:
                roi_gray = gray[fy : fy + int(fh * 0.65), fx : fx + fw]
                eyes = self.eye_cascade.detectMultiScale(roi_gray, scaleFactor=1.1, minNeighbors=3, minSize=(12, 12))
                # If eyes not visible and face is oriented downwards/sideways
                if len(eyes) == 0 and fh > 80:
                    return {
                        "success": True,
                        "face_count": 1,
                        "status": "INCIDENT",
                        "incident_type": "GAZE_SHIFT",
                        "severity": "LOW",
                        "details": "Candidate gaze shifted away from exam screen (eyes looking away/down)."
                    }

            return self._classify_face_count(1)

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "face_count": 0,
                "status": "ERROR"
            }

    def _detect_phone_in_frame(self, gray: np.ndarray, face_rect) -> bool:
        """
        Heuristic detection for mobile phones in frame:
        Detects high-contrast rectangular contours with smartphone aspect ratio (approx 1.6 - 2.5).
        """
        try:
            (fx, fy, fw, fh) = face_rect
            img_h, img_w = gray.shape[:2]
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edges = cv2.Canny(blurred, 60, 150)

            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            for cnt in contours:
                area = cv2.contourArea(cnt)
                # Check for reasonable phone-sized area (1% to 15% of frame)
                if area < (img_w * img_h * 0.015) or area > (img_w * img_h * 0.20):
                    continue

                peri = cv2.arcLength(cnt, True)
                approx = cv2.approxPolyDP(cnt, 0.04 * peri, True)
                if len(approx) == 4:
                    x, y, w, h = cv2.boundingRect(approx)
                    # Exclude contour if it largely overlaps with face box
                    if (x < fx + fw and x + w > fx and y < fy + fh and y + h > fy):
                        continue
                    aspect_ratio = float(h) / w if w > 0 else 0
                    if 1.5 <= aspect_ratio <= 2.6 or 0.38 <= aspect_ratio <= 0.67:
                        return True
            return False
        except Exception:
            return False

    def analyze_frame_base64(self, b64_string: str) -> dict:
        """
        Analyze a base64 encoded data URI or raw base64 string from browser webcam.
        """
        try:
            if ',' in b64_string:
                # Remove data:image/...;base64, prefix
                b64_string = b64_string.split(',', 1)[1]

            image_bytes = base64.b64decode(b64_string)
            return self.analyze_frame_bytes(image_bytes)
        except Exception as e:
            return {
                "success": False,
                "error": f"Base64 decoding failed: {str(e)}",
                "face_count": 0,
                "status": "ERROR"
            }

    def classify_face_count(self, face_count: int) -> dict:
        """Public API: classify a face count into a NORMAL/INCIDENT result."""
        return self._classify_face_count(face_count)

    def _classify_face_count(self, face_count: int) -> dict:
        """
        Ethical classification rules:
        - 0 faces: NO_FACE (Low severity anomaly)
        - 1 face: NORMAL (Expected state)
        - 2 faces: MULTIPLE_FACES (Medium severity anomaly)
        - 3+ faces: MULTIPLE_FACES (High severity anomaly)
        Never marks student as 'cheating' - strictly logs visual anomalies for human faculty review.
        """
        if face_count == 0:
            return {
                "success": True,
                "face_count": 0,
                "status": "INCIDENT",
                "incident_type": "NO_FACE",
                "severity": "LOW",
                "details": "No face detected in webcam view. Candidate may have moved out of frame."
            }
        elif face_count == 1:
            return {
                "success": True,
                "face_count": 1,
                "status": "NORMAL",
                "incident_type": None,
                "severity": None,
                "details": "Single face present and centered."
            }
        elif face_count == 2:
            return {
                "success": True,
                "face_count": 2,
                "status": "INCIDENT",
                "incident_type": "MULTIPLE_FACES",
                "severity": "MEDIUM",
                "details": "Multiple faces (2) detected in frame. Additional person may be present."
            }
        else:
            return {
                "success": True,
                "face_count": face_count,
                "status": "INCIDENT",
                "incident_type": "MULTIPLE_FACES",
                "severity": "HIGH",
                "details": f"Critical visual anomaly: {face_count} faces detected in frame. Multiple unauthorized individuals present."
            }

# Singleton instance
cv_monitor = None

def get_cv_monitor():
    global cv_monitor
    if cv_monitor is None:
        cv_monitor = CVMonitorService()
    return cv_monitor
