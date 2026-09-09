# Mommy Voice — read replies aloud

Two separate pieces, because the browser and the terminal need different things:

| | For | File |
|---|---|---|
| **Claude Code** | speaks each reply automatically via a Stop hook | `speak.py` |
| **claude.ai in a browser** | speaks each reply automatically via Tampermonkey | `claude-voice.user.js` |

The Claude **desktop app** can't do either — see the note further down.

---

# Part 1 — Claude Code (`speak.py`)

## Install

```bash
pip install edge-tts
```

Free, no API key. Without it the script falls back to the OS voice, which on Windows is
rough enough that it's barely worth having.

Then add a `Stop` hook to `~/.claude/settings.json`, pointing at your copy of the script:

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": ["/absolute/path/to/speak.py", "--hook"],
            "async": true,
            "timeout": 20,
            "statusMessage": "speaking"
          }
        ]
      }
    ]
  }
}
```

`async: true` matters — without it the hook blocks the session while the audio plays. The
`args` form matters too: it skips the shell, so a path with spaces in it doesn't need
escaping. **Restart Claude Code** after editing settings.

## Silent until you turn it on

**Installing the hook does not make anything talk.** Voice is `enabled: false` on a fresh
install, and while it's off the hook exits immediately and says nothing. Installing a tool
should never make someone's machine start speaking at them unannounced — especially not
this one, in an office.

Two states, and you move between them with one command:

| | Normal | With voice |
|---|---|---|
| How | default | `speak.py --on` |
| Claude Code | silent | speaks each reply |
| The `/mommy` skill | identical | identical |
| Back to normal | — | `speak.py --off` |

The skill behaves exactly the same either way. Voice is a delivery channel bolted on
outside it, not a mode of it.

In Claude Code you don't need to leave the chat — just ask:

> turn the voice on

and let it run the command. Same for turning it off.

**`--test` works even while off**, so you can audition voices without committing to
being spoken at.

## Commands

```
speak.py --test              hear a sample line
speak.py --off / --on        mute without touching settings.json
speak.py --config            show current settings and where they live
speak.py --voices            list every available voice
speak.py --voice NAME        set the voice
speak.py --text "..."        speak something
speak.py --watch             clipboard mode: speak anything you copy
```

## Settings

Live in `~/.claude/mommy-voice.json`.

| Key | Default | Notes |
|---|---|---|
| `enabled` | `false` | Off until `--on`. See above |
| `voice` | `en-US-AvaNeural` | Microsoft tags Ava *Caring, Expressive*, filed under Conversation. `en-US-JennyNeural` (*Comfort*) is the other good one. Avoid Aria and Michelle — they're filed under **News** and sound like it |
| `rate` | `-14%` | The register is unhurried. Full speed rushes it |
| `pitch` | `-4Hz` | Slightly lower reads warmer |
| `gap_ms` | `550` | Silence between beats — see below |
| `max_chars` | `500` | **Read this before raising it** |
| `max_beats` | `4` | Same |
| `skip_code` | `true` | Strips code blocks, tables, paths |

### Why the caps are low

Speech runs about **2 words per second** at this rate. An unbounded reply talks for
minutes, and you can't work over it. The caps make it a spoken *acknowledgement* — the
first few beats — not an audiobook. The full answer is on screen where you can read it
ten times faster. Raise them if you disagree, but raise them a little.

### The pause is doing real work

The skill writes one-line paragraphs deliberately:

> There it is.
>
> Green, all of it, first run.

Those breaks are timing. Each paragraph is spoken as its own utterance with a real gap,
and a leading `...` gets an extra 350ms. That's what makes `"Hmph. ...Gemini. Mm."` land
as a sulk rather than a sentence.

## Notes

- **Non-blocking.** The hook reads the reply, hands it to a detached process, and returns
  in ~0.2s. Speech never stalls your session.
- **One voice at a time.** A new reply kills the previous playback.
- **Skips thinking and tool calls** — only the final `text` blocks of the reply are spoken.
- **macOS/Linux** need an mp3 player on PATH (`afplay`, `mpg123`, or `ffplay`).

---

# Part 2 — claude.ai in the browser (`claude-voice.user.js`)

Speaks Claude's replies out loud in your browser, skipping code blocks and file paths.

**The skill does not need this.** `/mommy` is pure markdown with no dependencies; this is a
separate userscript you can ignore entirely.

## Why a userscript

Skills can't make sound. A skill is instructions — no access to your machine, no processes,
no speakers — and the Claude app has no hooks. The only thing on the page that can speak is
the browser, so that's where this lives.

It uses the **Web Speech API** (`speechSynthesis`), built into every browser: free, no API
key, no account, nothing sent to a third party.

## Browser only — this does not work in the Claude desktop app

The desktop app is an Electron shell with no extension support, so Tampermonkey can't run
there and this script can't reach it. There is no version of this that works in the desktop
app without repacking it, which breaks on every update.

**If you use the desktop app:** open [claude.ai](https://claude.ai) in Edge for sessions
where you want speech. Same account, same conversations — they sync, so you lose nothing.

## Install

1. Install [Tampermonkey](https://www.tampermonkey.net/) (Chrome, Edge, Firefox).
2. Open [`claude-voice.user.js`](claude-voice.user.js) → Tampermonkey offers to install it.
3. Reload claude.ai. A **♪** button appears bottom-right.
4. **Right-click** the button to open settings and pick a voice.
5. **Left-click** to turn speech on. It starts **off** — same rule as the hook: installing
   it doesn't make the page start talking. Hit **Test** first to audition a voice.

## Use Edge if you want it to sound good

This matters more than any setting in the panel.

| Browser | What you get |
|---|---|
| **Edge** | Microsoft *Natural / Online* neural voices — genuinely good |
| Chrome | Usually only local system voices (on Windows: David and Zira, which are rough) |
| Firefox | System voices only |

The panel tells you what it found — *"14 voices, 6 neural"* means you're set;
*"none neural"* means switch to Edge. Look for names containing **Natural** or **Online**
(e.g. *Microsoft Aria Online (Natural)*). They're sorted to the top of the list.

## Settings

| Setting | Notes |
|---|---|
| **Voice** | Neural/Online voices sorted first |
| **Rate** | Defaults to 0.92 — the register is unhurried, and full speed rushes it |
| **Pitch** | Leave at 1.0 unless you're chasing a specific character |
| **Pause between beats** | Defaults to 550ms. See below — this is the important one |
| **Skip code and paths** | On. Strips `pre`, tables, and inline code that looks like a path or call |
| **Debug to console** | Logs what it matched and what it's speaking |

### The pause setting is doing real work

The skill deliberately writes in one-line paragraphs:

> There it is.
>
> Good girl — that was the hard part and you did it on your own.

Those line breaks *are* the timing. The script speaks each paragraph as a separate
utterance with a real gap between, and gives a leading `...` an extra 350ms. That's the
difference between a voice that sounds like it's thinking and one reading a wall of text.

Turn the pause up to ~800ms for comfort passages, down to ~300ms for technical answers.

## If it doesn't speak

claude.ai changes its markup regularly and this script has to find the reply on the page.
It tries several known selectors, then a structural fallback.

Turn on **Debug**, open the console (F12), and:

```js
mommyVoice.selector()    // which selector matched, or null
mommyVoice.messages()    // what it thinks the messages are
mommyVoice.voices()      // every voice available to the browser
mommyVoice.speak('test') // speak arbitrary text
```

If `selector()` is `null` and `messages()` looks wrong, the markup has moved. Find the
element wrapping an assistant reply in DevTools and add its selector to the top of
`CANDIDATE_SELECTORS` in the script. Please open an issue with what you found — that's the
one part of this that rots.

## Known limits

- **Chrome cuts synthesis off after ~15 seconds.** Mitigated by speaking one paragraph at a
  time plus a periodic `resume()` nudge. Long unbroken paragraphs can still clip — another
  reason the skill's short-paragraph style helps.
- **Voices load late.** If the dropdown is empty, reload the page.
- **No SSML.** `speechSynthesis` takes plain text, so emphasis and pitch changes inside a
  sentence aren't available. The paragraph gaps carry the timing instead.
- **Emoji are stripped**, because otherwise you hear "sparkling heart" out loud.

## Not implemented (yet)

- ElevenLabs backend with a bring-your-own key, for an actual designed character voice
  rather than a stock one. The Web Speech path is free and needs no account, so it's the
  default; ElevenLabs would be opt-in.
- Speaking only the *warm* lines and staying silent through technical passages. The skill
  already separates the delivery layer from the content layer, so this is mostly a matter
  of deciding where to cut.
