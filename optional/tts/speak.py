#!/usr/bin/env python3
"""
Mommy Voice - speaks Claude's replies out loud.

Modes:
  speak.py --hook              read a Claude Code Stop-hook payload on stdin and speak the reply
  speak.py --text "..."        speak some text
  speak.py --watch             watch the clipboard; speak anything newly copied
  speak.py --test              say a sample line
  speak.py --voices            list available voices
  speak.py --on / --off        enable or disable speaking
  speak.py --config            show where settings live and what they are

Voice comes from edge-tts (free, no API key, Microsoft neural voices). If edge-tts
isn't installed it falls back to the OS voice, which on Windows is rough.

    pip install edge-tts
"""

import argparse
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG_PATH = Path.home() / ".claude" / "mommy-voice.json"

DEFAULTS = {
    # Off until explicitly turned on. Installing the hook should never make a
    # machine start talking on its own - `speak.py --on` is the opt-in, and
    # --test works regardless so a voice can be auditioned first.
    "enabled": False,
    # Microsoft tags Ava as Caring/Expressive and files her under Conversation
    # rather than News, which is why she beats Aria and Michelle here.
    # Jenny (Friendly, Considerate, Comfort) is the other good one.
    "voice": "en-US-AvaNeural",
    "rate": "-14%",     # the register is unhurried; full speed rushes it
    "pitch": "-4Hz",    # slightly lower reads warmer and older
    "volume": "+0%",
    # "auto" picks fish if a key is set, else edge-tts, else the OS voice.
    # Force one with "edge", "fish" or "os".
    "backend": "auto",
    # Fish Audio (fish-speech). Needs a key from fish.audio; the free edge path
    # needs nothing. Default model is "English Female Audiobook" - warm, gentle,
    # middle-aged, empathetic.
    "fish_api_key": "",
    "fish_model_id": "23c1b755b9994a68a1d21d6a67562445",
    "fish_speed": 0.88,   # same intent as edge's -14% rate
    "gap_ms": 550,      # silence between beats - this is what makes pauses land
    # Speech runs ~2 words/second at this rate, so an unbounded reply talks for
    # minutes. These caps keep it to a spoken acknowledgement, not an audiobook.
    "max_chars": 500,
    "max_beats": 4,
    "skip_code": True,
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def load_config():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except Exception:
        pass
    return cfg


def save_config(cfg):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cfg, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# Turning a reply into speakable text
# ---------------------------------------------------------------------------

EMOJI = re.compile(
    "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0000FE0F\U0001F900-\U0001F9FF]+"
)


def clean(text, skip_code=True):
    if skip_code:
        text = re.sub(r"```.*?```", " ", text, flags=re.S)     # fenced blocks
        text = re.sub(r"^\s{4,}\S.*$", " ", text, flags=re.M)  # indented blocks
        # Inline code: keep short identifiers, drop paths/calls/flags.
        def _inline(m):
            body = m.group(1)
            return " " if (len(body) > 24 or re.search(r"[/\\().]|^-{1,2}\w", body)) else body
        text = re.sub(r"`([^`]*)`", _inline, text)

    text = EMOJI.sub(" ", text)
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.M)          # headings
    text = re.sub(r"^\s*\|.*\|\s*$", " ", text, flags=re.M)     # table rows
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)      # links/images
    text = re.sub(r"\*\*|__", "", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\w*])", r"\1", text)
    text = re.sub(r"^\s*[-*+]\s+", "", text, flags=re.M)        # bullets
    text = re.sub(r"^\s*>\s?", "", text, flags=re.M)            # quotes
    text = re.sub(r"^\s*[-=]{3,}\s*$", " ", text, flags=re.M)   # rules
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def to_beats(text, max_chars, max_beats=0):
    """One beat per line. The skill writes one-line paragraphs as pauses, so the
    timing is already in the text - this just keeps it from being flattened."""
    if len(text) > max_chars:
        head = text[:max_chars]
        cut = max(head.rfind("."), head.rfind("\n"))
        text = head[: cut + 1] if cut > 40 else head

    beats = []
    for raw in re.split(r"\n+", text):
        s = raw.strip()
        if len(s) < 2:
            continue
        lead = bool(re.match(r"^(\.{2,}|…)", s))
        s = re.sub(r"^(\.{2,}|…)\s*", "", s)
        if len(s) >= 2:
            beats.append((s, lead))

    if max_beats and len(beats) > max_beats:
        beats = beats[:max_beats]
    return beats


# ---------------------------------------------------------------------------
# Reading the Claude Code transcript
# ---------------------------------------------------------------------------

def last_assistant_text(transcript_path):
    """Walk back through the JSONL and collect the final assistant turn's text
    blocks, skipping thinking and tool_use."""
    try:
        lines = Path(transcript_path).read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return ""

    chunks = []
    for line in reversed(lines):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except Exception:
            continue

        msg = obj.get("message") or {}
        role = msg.get("role")

        if role == "user":
            if chunks:
                break        # reached the prompt that started this turn
            continue
        if role != "assistant":
            continue

        content = msg.get("content")
        if isinstance(content, str):
            chunks.append(content)
            continue
        if not isinstance(content, list):
            continue
        for block in reversed(content):
            if isinstance(block, dict) and block.get("type") == "text":
                chunks.append(block.get("text", ""))

    return "\n".join(reversed(chunks)).strip()


# ---------------------------------------------------------------------------
# Speaking
# ---------------------------------------------------------------------------

def have_edge_tts():
    try:
        import edge_tts  # noqa: F401
        return True
    except Exception:
        return False


def pick_backend(cfg):
    want = (cfg.get("backend") or "auto").lower()
    if want == "auto":
        if cfg.get("fish_api_key"):
            return "fish"
        return "edge" if have_edge_tts() else "os"
    if want == "fish" and not cfg.get("fish_api_key"):
        print("backend=fish but fish_api_key is empty; falling back", file=sys.stderr)
        return "edge" if have_edge_tts() else "os"
    if want == "edge" and not have_edge_tts():
        print("backend=edge but edge-tts isn't installed; falling back", file=sys.stderr)
        return "os"
    return want


def synth_beats_fish(beats, cfg, outdir):
    """Render each beat via the Fish Audio API. Needs fish_api_key."""
    import urllib.request

    paths = []
    for i, (text, _) in enumerate(beats):
        body = json.dumps({
            "text": text,
            "reference_id": cfg["fish_model_id"],
            "format": "mp3",
            "prosody": {"speed": cfg.get("fish_speed", 1.0)},
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.fish.audio/v1/tts",
            data=body,
            headers={
                "Authorization": "Bearer " + cfg["fish_api_key"],
                "Content-Type": "application/json",
                "model": "speech-1.5",
            },
        )
        path = os.path.join(outdir, f"b{i:03d}.mp3")
        with urllib.request.urlopen(req, timeout=45) as r:
            data = r.read()
        if not data:
            raise RuntimeError("fish returned empty audio")
        with open(path, "wb") as fh:
            fh.write(data)
        paths.append(path)
    return paths


def synth_beats(beats, cfg, outdir):
    """Render each beat to its own mp3, concurrently."""
    import asyncio
    import edge_tts

    async def one(idx, text):
        path = os.path.join(outdir, f"b{idx:03d}.mp3")
        c = edge_tts.Communicate(
            text, cfg["voice"],
            rate=cfg["rate"], pitch=cfg["pitch"], volume=cfg["volume"],
        )
        await c.save(path)
        return path

    async def all_of_them():
        return await asyncio.gather(*(one(i, t) for i, (t, _) in enumerate(beats)))

    return asyncio.run(all_of_them())


def play_sequence(paths, gaps_ms):
    """Play files in order with a gap after each. One subprocess for the lot."""
    system = platform.system()

    if system == "Windows":
        items = ",".join(
            "@{p='%s';g=%d}" % (p.replace("'", "''"), g) for p, g in zip(paths, gaps_ms)
        )
        # Open() is async, so wait for the duration to land before playing,
        # then sleep exactly that long. Polling Position instead burns a
        # multi-second timeout on every file.
        ps = (
            "Add-Type -AssemblyName presentationCore;"
            "$pl=New-Object System.Windows.Media.MediaPlayer;"
            f"foreach($i in @({items})){{"
            "$pl.Open([uri]$i.p);"
            "$w=0;while(-not $pl.NaturalDuration.HasTimeSpan -and $w -lt 50){Start-Sleep -Milliseconds 40;$w++};"
            "$pl.Play();"
            "if($pl.NaturalDuration.HasTimeSpan){"
            "Start-Sleep -Milliseconds ([int]$pl.NaturalDuration.TimeSpan.TotalMilliseconds + 80)"
            "}else{Start-Sleep -Milliseconds 1500};"
            "$pl.Stop();Start-Sleep -Milliseconds $i.g};"
            "$pl.Close()"
        )
        subprocess.run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return

    player = None
    for cand in (["afplay"], ["mpg123", "-q"], ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet"]):
        if shutil.which(cand[0]):
            player = cand
            break
    if not player:
        print("no audio player found (install mpg123 or ffmpeg)", file=sys.stderr)
        return

    import time
    for p, g in zip(paths, gaps_ms):
        subprocess.run(player + [p], check=False)
        time.sleep(g / 1000.0)


def fallback_speak(text, cfg):
    """OS voice. Rough, but better than silence."""
    system = platform.system()
    if system == "Windows":
        safe = text.replace("'", "''")
        ps = (
            "Add-Type -AssemblyName System.Speech;"
            "$s=New-Object System.Speech.Synthesis.SpeechSynthesizer;"
            "$s.Rate=-2;"
            f"$s.Speak('{safe}')"
        )
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       check=False,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    elif system == "Darwin":
        subprocess.run(["say", "-r", "170", text], check=False)
    else:
        if shutil.which("espeak-ng"):
            subprocess.run(["espeak-ng", "-s", "150", text], check=False)


def say(text, cfg):
    text = clean(text, cfg["skip_code"])
    beats = to_beats(text, cfg["max_chars"], cfg.get("max_beats", 0))
    if not beats:
        return

    backend = pick_backend(cfg)
    if backend == "os":
        fallback_speak(" ".join(t for t, _ in beats), cfg)
        return

    with tempfile.TemporaryDirectory(prefix="mommyvoice-") as tmp:
        try:
            if backend == "fish":
                paths = synth_beats_fish(beats, cfg, tmp)
            else:
                paths = synth_beats(beats, cfg, tmp)
        except Exception as e:
            print(f"{backend} synthesis failed ({e}); falling back", file=sys.stderr)
            fallback_speak(" ".join(t for t, _ in beats), cfg)
            return
        gaps = [cfg["gap_ms"] + (350 if lead else 0) for _, lead in beats]
        play_sequence(paths, gaps)


# ---------------------------------------------------------------------------
# Entry points
# ---------------------------------------------------------------------------

SAMPLE = (
    "There it is.\n"
    "Green, all of it, first run.\n"
    "...And you got there by reading the actual source instead of guessing. Good girl."
)


def mode_hook(cfg):
    """Stop hook: payload arrives on stdin with the transcript path.

    Speaking takes tens of seconds, and a hook that blocks stalls the session
    for that whole time. So this reads the reply, hands it to a detached child
    and returns immediately.
    """
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    path = payload.get("transcript_path")
    if not path:
        return 0
    text = last_assistant_text(path)
    if not text:
        return 0

    flags = 0
    kwargs = {}
    if platform.system() == "Windows":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0) | getattr(subprocess, "DETACHED_PROCESS", 0)
    else:
        kwargs["start_new_session"] = True

    try:
        subprocess.Popen(
            [sys.executable, os.path.abspath(__file__), "--speak-now"],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            creationflags=flags, **kwargs,
        ).stdin.write(text.encode("utf-8", "replace"))
    except Exception:
        pass
    return 0


def kill_previous():
    """One voice at a time. A new reply cuts off the last one."""
    pid_file = Path(tempfile.gettempdir()) / "mommy-voice.pid"
    try:
        old = int(pid_file.read_text())
        if platform.system() == "Windows":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(old)],
                           check=False, capture_output=True)
        else:
            os.kill(old, 9)
    except Exception:
        pass
    try:
        pid_file.write_text(str(os.getpid()))
    except Exception:
        pass


def mode_watch(cfg):
    try:
        import tkinter
    except Exception:
        print("clipboard watch needs tkinter", file=sys.stderr)
        return 1
    import time
    root = tkinter.Tk()
    root.withdraw()
    last = None
    print("watching clipboard - copy a reply to hear it. ctrl-c to stop.")
    try:
        while True:
            try:
                cur = root.clipboard_get()
            except Exception:
                cur = None
            if cur and cur != last and len(cur.strip()) > 12:
                last = cur
                say(cur, cfg)
            time.sleep(0.6)
    except KeyboardInterrupt:
        pass
    return 0


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--hook", action="store_true")
    ap.add_argument("--speak-now", action="store_true",
                    help="internal: detached child that does the talking")
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--voices", action="store_true")
    ap.add_argument("--config", action="store_true")
    ap.add_argument("--on", action="store_true")
    ap.add_argument("--off", action="store_true")
    ap.add_argument("--voice")
    ap.add_argument("--backend", choices=["auto", "edge", "fish", "os"])
    ap.add_argument("--fish-key", help="Fish Audio API key (stored in the config file)")
    ap.add_argument("--fish-model", help="Fish Audio voice/model id")
    ap.add_argument("--text", nargs="*")
    args = ap.parse_args()

    cfg = load_config()

    if args.on or args.off:
        cfg["enabled"] = bool(args.on)
        save_config(cfg)
        if args.on:
            print(f"voice ON - {cfg['voice']} @ rate {cfg['rate']}, pitch {cfg['pitch']}")
            print("turn it off again with:  speak.py --off")
        else:
            print("voice OFF")
        return 0

    changed = []
    if args.voice:
        cfg["voice"] = args.voice
        changed.append(f"voice={args.voice}")
    if args.backend:
        cfg["backend"] = args.backend
        changed.append(f"backend={args.backend}")
    if args.fish_key:
        cfg["fish_api_key"] = args.fish_key
        changed.append("fish_api_key=***stored***")
    if args.fish_model:
        cfg["fish_model_id"] = args.fish_model
        changed.append(f"fish_model_id={args.fish_model}")
    if changed:
        save_config(cfg)
        print("set " + ", ".join(changed))
        return 0

    if args.config:
        shown = dict(cfg)
        if shown.get("fish_api_key"):
            shown["fish_api_key"] = "***set***"
        print(f"config: {CONFIG_PATH}")
        print(json.dumps(shown, indent=2))
        print(f"edge-tts installed: {have_edge_tts()}")
        print(f"backend in use: {pick_backend(cfg)}")
        return 0

    if args.voices:
        subprocess.run([sys.executable, "-m", "edge_tts", "--list-voices"], check=False)
        return 0

    # Everything below actually makes noise, so respect the switch.
    if not cfg["enabled"] and not args.test:
        return 0

    if args.speak_now:
        kill_previous()
        say(sys.stdin.read(), cfg)
        return 0
    if args.hook:
        return mode_hook(cfg)
    if args.watch:
        return mode_watch(cfg)
    if args.test:
        say(SAMPLE, cfg)
        return 0
    if args.text:
        say(" ".join(args.text), cfg)
        return 0

    text = sys.stdin.read() if not sys.stdin.isatty() else ""
    if text.strip():
        say(text, cfg)
    else:
        ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
