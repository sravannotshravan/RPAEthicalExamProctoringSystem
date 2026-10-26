import base64
import logging
import os
import threading
import cv2
import numpy as np

logger = logging.getLogger(__name__)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
YOLO_MODEL_PATH = os.environ.get('YOLO_MODEL', os.path.join(BASE_DIR, 'models', 'yolov8n.pt'))
YOLO_CONFIDENCE = float(os.environ.get('YOLO_CONFIDENCE', '0.35'))
# Set YOLO_ENABLED=0 to force the lightweight Haar/contour fallback (no torch needed).
YOLO_ENABLED = os.environ.get('YOLO_ENABLED', '1').strip().lower() not in ('0', 'false', 'no', 'off')

# COCO class name -> (incident_type, severity, description). Anything not listed is ignored,
# so a candidate's own keyboard, mouse, cup, etc. never raises an anomaly.
PROHIBITED_OBJECTS = {
    'cell phone': ('PHONE_DETECTED', 'HIGH', 'Mobile phone'),
    'laptop': ('PROHIBITED_DEVICE_DETECTED', 'HIGH', 'Laptop or tablet'),
    'tv': ('PROHIBITED_DEVICE_DETECTED', 'HIGH', 'Secondary display'),
    'remote': ('PROHIBITED_DEVICE_DETECTED', 'MEDIUM', 'Handheld remote/electronic device'),
    'book': ('PROHIBITED_MATERIAL_DETECTED', 'MEDIUM', 'Book or printed material'),
}
SEVERITY_RANK = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}


class CVMonitorService:
    def __init__(self):
        self._yolo = None
        self._yolo_failed = False
        self._yolo_lock = threading.Lock()

        # Load OpenCV's built-in Haar Cascade for frontal face detection
        cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        if not os.path.exists(cascade_path):
            raise FileNotFoundError(f"Haar cascade file not found at {cascade_path}")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)

        # Load eye cascade for gaze / orientation analysis
        eye_path = cv2.data.haarcascades + 'haarcascade_eye.xml'
        self.eye_cascade = cv2.CascadeClassifier(eye_path) if os.path.exists(eye_path) else None

    # ------------------------------------------------------------------ YOLO (COCO)
    def _get_yolo(self):
        """Lazily loads the COCO-pretrained YOLO model; returns None if unavailable."""
        if not YOLO_ENABLED or self._yolo_failed:
            return None
        if self._yolo is not None:
            return self._yolo
        with self._yolo_lock:
            if self._yolo is None and not self._yolo_failed:
                try:
                    from ultralytics import YOLO
                    if not os.path.exists(YOLO_MODEL_PATH):
                        os.makedirs(os.path.dirname(YOLO_MODEL_PATH), exist_ok=True)
                        from ultralytics.utils.downloads import attempt_download_asset
                        attempt_download_asset(YOLO_MODEL_PATH)
                    self._yolo = YOLO(YOLO_MODEL_PATH)
                except Exception as e:  # missing package, no network for weights, etc.
                    logger.warning("YOLO unavailable, using Haar fallback: %s", e)
                    self._yolo_failed = True
        return self._yolo

    def detect_objects(self, detector, img) -> list:
        """Runs YOLO on an in-memory BGR frame; returns [(coco_label, confidence)]. Nothing is saved."""
        with self._yolo_lock:
            results = detector.predict(img, conf=YOLO_CONFIDENCE, imgsz=640, verbose=False)
        found = []
        for r in results:
            for cls_id, conf in zip(r.boxes.cls.tolist(), r.boxes.conf.tolist()):
                found.append((r.names[int(cls_id)], float(conf)))
        return found

    def _analyze_with_yolo(self, detector, img) -> dict:
        objects = self.detect_objects(detector, img)
        person_count = sum(1 for label, _ in objects if label == 'person')
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
        if person_count == 0 and len(faces) == 1:
            person_count = 1  # tight face crop that YOLO did not box as a full person
        gaze = None
        if person_count == 1 and len(faces) == 1:
            gaze = self._gaze_violation(gray, faces[0])
        return self.evaluate_detections(person_count, objects, gaze)

    def evaluate_detections(self, person_count: int, objects: list, gaze: dict = None) -> dict:
        """
        Pure rule engine: turns a person count and detected COCO objects into ALL applicable violations.
        Exactly one person must be in frame; each prohibited object type is reported, so a frame with
        two people and a phone yields two violations. `objects` is [(coco_label, confidence)].
        """
        violations = []
        if person_count != 1:
            base = self._classify_face_count(person_count)
            violation = {k: base[k] for k in ('incident_type', 'severity', 'details')}
            if person_count > 1:
                violation['details'] = f"{person_count} people detected in frame; only the candidate should be present."
            violations.append(violation)

        best = {}
        for label, conf in objects:
            if label in PROHIBITED_OBJECTS and conf > best.get(label, 0):
                best[label] = conf
        for label, conf in best.items():
            incident_type, severity, desc = PROHIBITED_OBJECTS[label]
            violations.append({
                'incident_type': incident_type,
                'severity': severity,
                'details': f"{desc} ('{label}') detected in webcam frame (confidence {conf:.0%}). Requires human review.",
            })
        if gaze:
            violations.append(gaze)

        # One violation per incident type (e.g. laptop + tv are both PROHIBITED_DEVICE_DETECTED)
        merged = {}
        for v in violations:
            cur = merged.get(v['incident_type'])
            if cur is None:
                merged[v['incident_type']] = dict(v)
            else:
                cur['details'] += ' ' + v['details']
                if SEVERITY_RANK[v['severity']] > SEVERITY_RANK[cur['severity']]:
                    cur['severity'] = v['severity']
        violations = sorted(merged.values(), key=lambda v: -SEVERITY_RANK[v['severity']])

        result = {
            'success': True,
            'face_count': person_count,
            'person_count': person_count,
            'detected_objects': sorted({label for label, _ in objects if label != 'person'}),
            'violations': violations,
        }
        if violations:
            top = violations[0]
            result.update(status='INCIDENT', incident_type=top['incident_type'],
                          severity=top['severity'], details=top['details'])
        else:
            result.update(status='NORMAL', incident_type=None, severity=None,
                          details='Single person present; no prohibited objects detected.')
        return result

    def _gaze_violation(self, gray, face):
        """Returns a GAZE_SHIFT violation dict for a single face, or None."""
        img_w = gray.shape[1]
        fx, fy, fw, fh = face
        center_x = (fx + fw / 2) / img_w
        if center_x < 0.18 or center_x > 0.82:
            return {'incident_type': 'GAZE_SHIFT', 'severity': 'LOW',
                    'details': 'Candidate head orientation or gaze shifted away from exam screen.'}
        if self.eye_cascade and fw >= 50 and fh >= 50:
            roi = gray[fy: fy + int(fh * 0.65), fx: fx + fw]
            eyes = self.eye_cascade.detectMultiScale(roi, scaleFactor=1.1, minNeighbors=3, minSize=(12, 12))
            if len(eyes) == 0 and fh > 80:
                return {'incident_type': 'GAZE_SHIFT', 'severity': 'LOW',
                        'details': 'Candidate gaze shifted away from exam screen (eyes looking away/down).'}
        return None

    def analyze_frame_bytes(self, image_bytes: bytes) -> dict:
        """
        Analyze a raw image byte buffer and inspect for:
        - Person count (exactly one allowed): NO_FACE / MULTIPLE_FACES [MED for 2, HIGH for 3+]
        - Prohibited objects (YOLO + COCO): phone, laptop, tv, remote, book
        - Gaze shift (head or eye orientation turned away)
        Returns every violation found (`violations`) plus a primary incident for back-compat.
        Falls back to Haar cascades + a contour phone heuristic when YOLO is unavailable.
        The frame is analyzed in memory and never stored.
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

            detector = self._get_yolo()
            if detector is not None:
                return self._analyze_with_yolo(detector, img)

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img_h, img_w = gray.shape[:2]

            # Fallback (YOLO unavailable) - 1. Detect faces
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

            gaze = self._gaze_violation(gray, faces[0])
            if gaze:
                return {"success": True, "face_count": 1, "status": "INCIDENT", **gaze}

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
