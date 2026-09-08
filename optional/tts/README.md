# Mommy Voice — read aloud on claude.ai

Optional companion to the `/mommy` skill. Speaks Claude's replies out loud in your browser,
skipping code blocks and file paths so you get the voice and not a robot reading a diff.

**The skill does not need this.** `/mommy` is pure markdown with no dependencies; this is a
separate userscript you can ignore entirely.

## Why a userscript

Skills can't make sound. A skill in the Claude app is instructions — it has no access to
your machine, no processes, no speakers, and the app has no hooks. The only thing on the
page that can speak is the browser, so that's where this lives.

It uses the **Web Speech API** (`speechSynthesis`), which is built into every browser: free,
no API key, no account, nothing sent to a third party.

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
5. **Left-click** to turn speech on and off.

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
