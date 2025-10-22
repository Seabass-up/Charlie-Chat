"""
TTS worker process meant to run under a Python 3.10 virtual environment that has
Coqui TTS (XTTS) installed. This script synthesizes WAV audio to a given output path.

Usage (example):
  python tts_worker.py --text "Hello world" --out out.wav --language en --speaker "female" --model tts_models/multilingual/multi-dataset/xtts_v2
"""
from __future__ import annotations
import argparse
import sys
import numpy as np
import soundfile as sf


def synthesize(text: str, out_path: str, language: str, speaker: str | None, model_name: str, sample_rate: int) -> None:
    from TTS.api import TTS  # type: ignore
    tts = TTS(model_name)
    kwargs = {}
    if speaker:
        kwargs["speaker"] = speaker
    audio = tts.tts(text=text, language=language, **kwargs)
    data = np.asarray(audio, dtype=np.float32)
    sf.write(out_path, data, sample_rate, format="WAV")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--language", default="en")
    ap.add_argument("--speaker", default=None)
    ap.add_argument("--model", default="tts_models/multilingual/multi-dataset/xtts_v2")
    ap.add_argument("--sample_rate", type=int, default=22050)
    args = ap.parse_args(argv)

    synthesize(
        text=args.text,
        out_path=args.out,
        language=args.language,
        speaker=args.speaker,
        model_name=args.model,
        sample_rate=args.sample_rate,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
