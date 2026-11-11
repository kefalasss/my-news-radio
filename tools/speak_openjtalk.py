#!/usr/bin/env python3
"""Render one myradio episode with offline Open JTalk and exact subtitle timing."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
from pathlib import Path
import subprocess
import tempfile
import wave

ROOT = Path(__file__).resolve().parents[1]
DICT = "/var/lib/mecab/dic/open-jtalk/naist-jdic"
VOICE = "/usr/share/hts-voice/nitech-jp-atr503-m001/nitech_jp_atr503_m001.htsvoice"
PAUSE_SECONDS = 0.25


def chunks(episode):
    yield 0, "opening", None, episode.get("opening", [])
    for index, item in enumerate(episode.get("news", [])):
        yield index + 1, "news", index, item.get("lines", [])
    yield len(episode.get("news", [])) + 1, "closing", None, episode.get("closing", [])


def synthesize(path: Path) -> Path:
    episode = json.loads(path.read_text(encoding="utf-8"))
    if episode.get("source") != "my-news-radio-auto":
        raise ValueError("Refusing to overwrite a non-automatic episode")
    target = ROOT / "audio" / f"{episode['date']}-ja.mp3"
    target.parent.mkdir(exist_ok=True)
    timed = []
    segments = []
    elapsed_frames = 0
    params = None
    with tempfile.TemporaryDirectory() as tmp:
        wav_out = Path(tmp) / "joined.wav"
        with wave.open(str(wav_out), "wb") as joined:
            for part, kind, index, lines in chunks(episode):
                seg_start = None
                for line in lines:
                    spoken = str(line.get("say", "")).strip()
                    if not spoken:
                        continue
                    out = Path(tmp) / f"{part}_{len(timed)}.wav"
                    subprocess.run(
                        ["open_jtalk", "-x", DICT, "-m", VOICE, "-r", "1.08",
                         "-ow", str(out)],
                        input=spoken.encode("utf-8"), check=True, timeout=60,
                        stdout=subprocess.DEVNULL,
                    )
                    with wave.open(str(out), "rb") as source:
                        got = source.getparams()
                        signature = (got.nchannels, got.sampwidth, got.framerate, got.comptype)
                        if params is None:
                            params = signature
                            joined.setnchannels(got.nchannels)
                            joined.setsampwidth(got.sampwidth)
                            joined.setframerate(got.framerate)
                        elif params != signature:
                            raise RuntimeError("Open JTalk unexpectedly changed WAV format")
                        frame_rate = got.framerate
                        start = elapsed_frames / frame_rate
                        if seg_start is None:
                            seg_start = start
                        frames = source.readframes(got.nframes)
                        joined.writeframes(frames)
                        elapsed_frames += got.nframes
                        end = elapsed_frames / frame_rate
                        timed.append({
                            "start": round(start, 3), "end": round(end, 3),
                            "show": line.get("show", spoken), "part": part,
                        })
                        pause_frames = round(frame_rate * PAUSE_SECONDS)
                        joined.writeframes(b"\0" * (pause_frames * got.nchannels * got.sampwidth))
                        elapsed_frames += pause_frames
                if seg_start is not None:
                    segments.append({"kind": kind, "index": index,
                                     "start": round(seg_start, 3), "end": 0.0})
        if not timed:
            raise RuntimeError("Episode has no speech")
        subprocess.run(
            ["ffmpeg", "-nostdin", "-hide_banner", "-loglevel", "error", "-y",
             "-i", str(wav_out), "-codec:a", "libmp3lame", "-qscale:a", "5",
             str(target)], check=True, timeout=120
        )
        probe = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(target)],
            check=True, capture_output=True, text=True, timeout=20,
        )
        duration = round(float(probe.stdout.strip()), 3)
    for i, segment in enumerate(segments):
        segment["end"] = segments[i + 1]["start"] if i + 1 < len(segments) else duration
    episode["seconds"] = duration
    episode["lines_timed"] = timed
    episode["segments"] = segments
    episode["made_at"] = dt.datetime.now(dt.timezone.utc).isoformat()
    path.write_text(json.dumps(episode, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    logging.info("Rendered %s, %.1f seconds, %s speech lines", target, duration, len(timed))
    return target


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("episode", type=Path)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    synthesize(args.episode)


if __name__ == "__main__":
    main()
