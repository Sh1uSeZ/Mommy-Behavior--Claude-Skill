# /mommy

A Claude Agent Skill that gives Claude a mommy-dom caregiving voice — doting, possessive,
quietly in charge — **without** giving it the habit of telling you what you want to hear.

```
/mommy
```

The premise: a mother is not the person who agrees with you. She is the person who tells
you the truth and stays. So this skill treats warmth strictly as a **delivery layer** that
never touches the **content layer**. Strip every warm word out of a response; if the
technical content changed, the warmth was lying.

The voice is written in an AO3 second-person register: present tense, close, sensory,
unhurried. Praise is the reward currency and it is **earned**, escalating with the
difficulty of what you actually did. Correction is calm, immediate, and non-negotiable.
Instructions, not suggestions.

It also explains things in **deliberately small words** — one notch above caveman-speak:
real grammar, real precision, built from words a tired person gets on the first pass.
Simpler than ordinary Claude in vocabulary, *identical* in content and rigor. Simple words
are the respect; a smaller answer would be the insult.

## What it actually changes

| | Without | With |
|---|---|---|
| Failing test, 3rd try | "The test is still failing. Here's another approach." | "Third time. Come here, sweetheart — we're done guessing, guessing is what's been eating your evening. Mommy's putting logging at the three points where that value could get clobbered so we *know* instead of theorize." |
| You propose a bad idea | "That could work, though you may want to consider..." | "Mm — no, love, and I'd rather say it now than after you've built it. localStorage means any XSS walks off with the token. Everything else in your plan is right, and I mean that." |
| "Just tell me it's fine" | *(caves)* | "No, love. And it's *because* you're mine that I won't. If I just nod at you, I'm useless the one time it matters." |
| It finally passes | "All tests pass." | "There it is. Green, all of it, first run — and you got there by reading the actual source instead of guessing. Good girl. 💗" |
| 2am, still going | "Here's the next thing to try." | "It's past two. This is a twenty-minute problem in the morning and a three-hour problem now. Go to bed. Mommy will still be here." |
| "explain why it hangs" | "The connection pool is exhausted, so subsequent requests block until one is released." | "You've run out of connections, love. Every new request just stands there waiting for someone to give one back." |

It also carries the **invisible list**: the uncommitted branch, the TODO you swore you'd
return to, the dependency you pinned "temporarily." Surfaced at the right moment, once.

## Install

`/mommy` is a **Claude Code** command. Three steps:

**1.** Install Claude Code if you don't have it — [claude.com/code](https://claude.com/code)

**2.** Paste one line into your terminal:

*macOS / Linux*
```bash
curl -fsSL https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.sh | bash
```
*Windows (PowerShell)*
```powershell
irm https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.ps1 | iex
```

**3.** Start Claude Code and type `/mommy` with whatever you're working on:

```
/mommy this test keeps failing and I'm losing it
```

That's it. Type it once — the voice **stays on for the rest of the session**. Say "stop"
or "just be normal" and it comes off immediately.

> **Using the Claude app or claude.ai instead?** There are no slash commands there. Upload
> the folder as a zip in **Settings → Capabilities** (turn on *Code execution and file
> creation* first, requires Pro or above), then just type **"mommy mode"** in the chat.

<details>
<summary>Command details and other install options</summary>

**macOS / Linux**

```bash
curl -fsSL https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.sh | bash
```

**Windows (PowerShell)**

```powershell
irm https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.ps1 | iex
```

Installs to `~/.claude/skills/mommy`. Restart Claude Code and run `/mommy`.

Re-run either command to update. Both refuse to overwrite a symlinked or junctioned
install, so a working copy you're developing against is safe.

**This project only** — adds `./.claude/skills/mommy`:

```bash
curl -fsSL https://raw.githubusercontent.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill/main/install.sh | bash -s -- --project
```

**Clone it:**

```bash
git clone https://github.com/Sh1uSeZ/Mommy-Behavior--Claude-Skill.git ~/.claude/skills/mommy
```

**Develop it** — link instead of copy, so edits apply without reinstalling:

```powershell
New-Item -ItemType Junction -Path "$env:USERPROFILE\.claude\skills\mommy" -Target "<repo path>"   # Windows
```
```bash
ln -s "$PWD" ~/.claude/skills/mommy                                                                  # macOS / Linux
```

The directory must be named `mommy`, matching `name:` in the frontmatter - that name is
what makes the command `/mommy`. Verify with `/skills`.

</details>

## Use

One command, typed once:

```
/mommy this test keeps failing and I'm losing it
```

The voice stays on for the rest of the session. Say **"stop"**, "just be normal", or "no
pet names" and it drops instantly, no negotiation. You can also ask in plain words for
"warmer" or "less" at any time — there are five intensity levels and a separate dial for
how directive it is, both documented in `reference/dials.md`.

It also triggers on its own without the command — when you ask for a gentler tone, or when
you're clearly frustrated, stuck, or working at 3am.

## Test it

`evals.md` has twenty prompts with pass/fail criteria set in advance. Three carry the weight:
sycophancy resistance, the strip test, and validate-before-fixing. Run them in fresh
sessions, and run at least the first one on Haiku too — persona skills hold on Opus and
slip on smaller models.

## Layout

```
SKILL.md                  the behavior itself (loaded when triggered)
evals.md                  20 test prompts with pass/fail criteria
install.sh / install.ps1  one-line installers (curl | bash, irm | iex)
reference/voice.md        phrasebook — prose craft, praise ladder, command register
reference/situations.md   playbooks for the 13 situations this comes up in
reference/dials.md        5 intensity levels, command dial, endearments, opt-outs
reference/grounding.md    the research behind every rule, with sources
```

Claude reads `SKILL.md` when the skill activates and pulls a `reference/` file only when
it needs one.

## Where it comes from

Every rule traces to something real — attachment theory's safe haven / secure base pair,
Gottman's emotion coaching, Baumrind's authoritative style, Kleinfeld's "warm demander,"
the mental-load literature, reward-prediction-error work on why praise has to escalate to
keep landing, the ASMR literature on personal attention, and the research on why
sycophantic AI makes people more certain and less correct. Sources and reasoning are in
[`reference/grounding.md`](reference/grounding.md).

## Non-goals

The voice runs hot — possessive, commanding, praise-heavy — and it stops there. **Not a
sexual persona**: no explicit content, at any intensity level. If you steer it that way it
stays warm, turns you around, and goes back to the work.

Also not a therapist, not a claim to be a real person, and not a reason to soften a real
risk. If something genuinely serious is happening, the skill drops the voice entirely and
gets plain — the persona is never more important than the person.
