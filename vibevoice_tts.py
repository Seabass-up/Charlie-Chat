"""
Unified TTS integration for Charlie with preference order:
1) Coqui XTTS (local, high quality)
2) Microsoft VibeVoice (placeholder until repo provides API)
3) pyttsx3 (system voices fallback)

Synthesize returns WAV bytes.
"""
from __future__ import annotations
import io
import os
import tempfile
from typing import Optional
import subprocess

# Fallback engine
import pyttsx3
import soundfile as sf
import numpy as np


class VibeVoiceTTS:
    def __init__(self, model_name: Optional[str] = None, device: Optional[str] = None) -> None:
        self.model_name = model_name or os.getenv("VIBEVOICE_MODEL", "vibe-tts-base")
        self.device = device or os.getenv("VIBEVOICE_DEVICE", "cpu")
        self._engine = None  # pyttsx3 fallback
        self._vibe = None    # placeholder
        self._coqui = None   # Coqui TTS API instance
        self._coqui_model_name = os.getenv("COQUI_TTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2")
        self._init_backends()

    def _init_backends(self) -> None:
        # Try preparing Coqui XTTS lazily at first call to avoid heavy startup cost.
        # We keep _coqui as None until synthesize.
        try:
            import TTS  # noqa: F401
        except Exception:
            pass

        try:
            # Lazy import; if not installed we use fallback
            import vibevoice  # type: ignore
            self._vibe = vibevoice
        except Exception:
            self._vibe = None

        if self._vibe is None:
            # Init fallback TTS so endpoint remains usable
            try:
                self._engine = pyttsx3.init()
            except Exception:
                self._engine = None

    def synthesize(self, text: str, speaker: Optional[str] = None, sample_rate: int = 22050, language: Optional[str] = None) -> bytes:
        """Synthesize speech; prefer Coqui XTTS, then VibeVoice (placeholder), else pyttsx3.
        Returns WAV bytes.
        """
        text = (text or "").strip()
        if not text:
            return self._silence_wav(duration_sec=0.2, sample_rate=sample_rate)

        # Preferred backend #1: Coqui XTTS (in-process)
        wav = self._try_coqui_xtts(text, speaker=speaker, language=language, sample_rate=sample_rate)
        if wav is not None:
            return wav

        # Preferred backend #1b: Coqui XTTS via external worker (Python 3.10 venv)
        wav = self._try_coqui_xtts_external(text, speaker=speaker, language=language, sample_rate=sample_rate)
        if wav is not None:
            return wav

        # Preferred backend #2: VibeVoice (placeholder tone until official API available)
        if self._vibe is not None:
            try:
                return self._tone_wav(frequency=440.0, duration_sec=min(3.0, max(0.5, len(text) / 20.0)), sample_rate=sample_rate)
            except Exception:
                pass

        # Fallback: pyttsx3 to WAV
        if self._engine is not None:
            try:
                with tempfile.TemporaryDirectory() as td:
                    out_wav = os.path.join(td, "out.wav")
                    self._engine.save_to_file(text, out_wav)
                    self._engine.runAndWait()
                    with open(out_wav, "rb") as f:
                        return f.read()
            except Exception:
                pass

        # Last resort: small silence wav
        return self._silence_wav(duration_sec=0.5, sample_rate=sample_rate)

    def _try_coqui_xtts(self, text: str, speaker: Optional[str], language: Optional[str], sample_rate: int) -> Optional[bytes]:
        """Attempt to synthesize with Coqui XTTS. Returns WAV bytes or None on failure."""
        try:
            if self._coqui is None:
                from TTS.api import TTS  # type: ignore
                # This will download the model on first use if not present
                self._coqui = TTS(self._coqui_model_name)
            # Coqui may return numpy array; let’s request desired language
            lang = language or os.getenv("COQUI_TTS_LANGUAGE", "en")
            kwargs = {}
            if speaker:
                # XTTS supports speaker as a string identifier; also supports cloning using speaker_wav
                kwargs["speaker"] = speaker
            audio = self._coqui.tts(text=text, language=lang, **kwargs)
            # Normalize to float32 numpy array
            data = np.asarray(audio, dtype=np.float32)
            # Some models return 22050/24000; resample only if needed
            return self._wav_bytes(data, sample_rate)
        except Exception:
            return None

    def _try_coqui_xtts_external(self, text: str, speaker: Optional[str], language: Optional[str], sample_rate: int) -> Optional[bytes]:
        """Run XTTS using an external Python 3.10 venv and tts_worker.py.
        Expects a virtual environment at ./venv310 (or CHARLIE_TTS_VENV).
        """
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            venv_path = os.getenv("CHARLIE_TTS_VENV", os.path.join(base_dir, "venv310"))
            python_exe = os.path.join(venv_path, "Scripts", "python.exe") if os.name == 'nt' else os.path.join(venv_path, "bin", "python")
            worker = os.path.join(base_dir, "tts_worker.py")
            if not os.path.exists(python_exe) or not os.path.exists(worker):
                return None

            with tempfile.TemporaryDirectory() as td:
                out_wav = os.path.join(td, "out.wav")
                cmd = [
                    python_exe,
                    worker,
                    "--text", text,
                    "--out", out_wav,
                    "--language", (language or os.getenv("COQUI_TTS_LANGUAGE", "en")),
                    "--model", self._coqui_model_name,
                    "--sample_rate", str(sample_rate),
                ]
                if speaker:
                    cmd.extend(["--speaker", speaker])

                subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                with open(out_wav, "rb") as f:
                    return f.read()
        except Exception:
            return None

    def _silence_wav(self, duration_sec: float, sample_rate: int) -> bytes:
        samples = int(duration_sec * sample_rate)
        data = np.zeros(samples, dtype=np.float32)
        buf = io.BytesIO()
        sf.write(buf, data, sample_rate, format="WAV")
        return buf.getvalue()

    def _tone_wav(self, frequency: float, duration_sec: float, sample_rate: int) -> bytes:
        t = np.linspace(0, duration_sec, int(sample_rate * duration_sec), endpoint=False)
        data = 0.1 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
        buf = io.BytesIO()
        sf.write(buf, data, sample_rate, format="WAV")
        return buf.getvalue()

    def _wav_bytes(self, data: np.ndarray, sample_rate: int) -> bytes:
        buf = io.BytesIO()
        sf.write(buf, data, sample_rate, format="WAV")
        return buf.getvalue()
