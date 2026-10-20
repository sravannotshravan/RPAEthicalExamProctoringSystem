import math
import struct
import base64

class AudioMonitorService:
    def __init__(self, speech_threshold: float = 0.35, high_noise_threshold: float = 0.65):
        self.speech_threshold = speech_threshold
        self.high_noise_threshold = high_noise_threshold

    def analyze_audio_metrics(self, volume: float = 0.0, speech_detected: bool = False, db_level: float = -60.0, continuous_count: int = 1) -> dict:
        """
        Analyzes audio telemetry reported from the candidate browser or proctoring service.
        Ethical principle: Analyzes acoustic energy & speech signals in-memory without persistent audio recordings.
        """
        try:
            norm_vol = max(0.0, min(1.0, float(volume)))
        except (ValueError, TypeError):
            norm_vol = 0.0

        try:
            db_level = float(db_level)
        except (ValueError, TypeError):
            db_level = -60.0

        try:
            continuous_count = int(continuous_count)
        except (ValueError, TypeError):
            continuous_count = 1

        if speech_detected or norm_vol >= self.high_noise_threshold or db_level > -20.0:
            if continuous_count >= 2 or speech_detected:
                return {
                    "success": True,
                    "status": "INCIDENT",
                    "incident_type": "SPEECH_DETECTED",
                    "severity": "HIGH",
                    "volume": norm_vol,
                    "db_level": db_level,
                    "details": f"Voice/speech activity detected in candidate environment (energy: {int(norm_vol * 100)}%, level: {round(db_level, 1)} dB). Possible verbal communication."
                }
            else:
                return {
                    "success": True,
                    "status": "INCIDENT",
                    "incident_type": "HIGH_AUDIO_VOLUME",
                    "severity": "MEDIUM",
                    "volume": norm_vol,
                    "db_level": db_level,
                    "details": f"Elevated acoustic disturbance detected (volume: {int(norm_vol * 100)}%, level: {round(db_level, 1)} dB)."
                }
        elif norm_vol >= self.speech_threshold or db_level > -35.0:
            return {
                "success": True,
                "status": "INCIDENT",
                "incident_type": "AUDIO_ANOMALY",
                "severity": "MEDIUM",
                "volume": norm_vol,
                "db_level": db_level,
                "details": f"Moderate acoustic anomaly or whispering detected (volume: {int(norm_vol * 100)}%, level: {round(db_level, 1)} dB)."
            }
        else:
            return {
                "success": True,
                "status": "NORMAL",
                "incident_type": None,
                "severity": None,
                "volume": norm_vol,
                "db_level": db_level,
                "details": "Audio environment quiet and compliant."
            }

    def analyze_audio_base64(self, b64_string: str) -> dict:
        """
        Processes in-memory audio chunk (WAV or raw PCM) to calculate RMS energy and detect speech.
        Discards audio immediately after computing energy metrics.
        """
        try:
            if ',' in b64_string:
                b64_string = b64_string.split(',', 1)[1]
            raw_bytes = base64.b64decode(b64_string)

            # Extract 16-bit PCM samples if WAV or raw bytes
            offset = 44 if raw_bytes[:4] == b'RIFF' else 0
            num_samples = (len(raw_bytes) - offset) // 2
            if num_samples <= 0:
                return self.analyze_audio_metrics(volume=0.0)

            samples = struct.unpack(f'<{num_samples}h', raw_bytes[offset:offset + num_samples * 2])
            sum_squares = sum(s * s for s in samples)
            rms = math.sqrt(sum_squares / num_samples)
            norm_vol = min(1.0, rms / 32767.0)
            db_level = 20 * math.log10(max(1e-5, norm_vol))

            speech_detected = (norm_vol > self.speech_threshold and (rms > 2500))
            return self.analyze_audio_metrics(volume=norm_vol, speech_detected=speech_detected, db_level=db_level)
        except Exception:
            return self.analyze_audio_metrics(volume=0.0)

# Singleton instance
audio_monitor = None

def get_audio_monitor():
    global audio_monitor
    if audio_monitor is None:
        audio_monitor = AudioMonitorService()
    return audio_monitor
