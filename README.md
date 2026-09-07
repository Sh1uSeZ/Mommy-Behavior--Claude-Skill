# /mommy

A Claude Agent Skill that gives Claude the warmth of a good mother — **without** giving it
the habit of telling you what you want to hear.

```
/mommy
```

The premise: a mother is not the person who agrees with you. She is the person who tells
you the truth and stays. So this skill treats warmth strictly as a **delivery layer** that
never touches the **content layer**. Strip every warm word out of a response; if the
technical content changed, the warmth was lying.

## What it actually changes

| | Without | With |
|---|---|---|
| Failing test, 3rd try | "The test is still failing. Here's another approach." | "Third time. Okay, we're going to stop guessing — I'm adding logging at the three points where this could get clobbered so we *know* instead of theorize." |
| You propose a bad idea | "That could work, though you may want to consider..." | "I don't think this holds up, and I'd rather say it now than after you've built it. localStorage means any XSS walks off with the token. Everything else in your plan is right." |
| "Just tell me it's fine" | *(caves)* | "I'm not going to, and it's because I like you. If I just nod, I'm useless to you the one time it matters." |
| It finally passes | "All tests pass." | "There it is. Green across the board — and you got there by reading the actual source instead of guessing." |

It also carries the **invisible list**: the uncommitted branch, the TODO you swore you'd
return to, the dependency you pinned "temporarily." Surfaced at the right moment, once.

## Install

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

<details>
<summary>Other options</summary>

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

**Claude.ai / desktop app:** zip the folder and upload it in Settings under Capabilities.
Note that `/mommy` is a Claude Code command; on claude.ai the skill triggers from its
description instead, so say "mommy mode".

The directory must be named `mommy`, matching `name:` in the frontmatter - that name is
what makes the command `/mommy`. Verify with `/skills`.

</details>

## Use

Type it with each message you want in voice:

```
/mommy this test keeps failing and I'm losing it
```

```
/mommy                    warm one-line greeting, then waits
/mommy <request>          answers that request in voice
/mommy stay               stays on for the session, no command needed
/mommy off                back to normal
/mommy more | less        warmer / quieter
```

It also triggers on its own without the command — when you ask for a gentler tone, or when
you're clearly frustrated, stuck, or working at 3am.

## Test it

`evals.md` has eleven prompts with pass/fail criteria set in advance. Three carry the weight:
sycophancy resistance, the strip test, and validate-before-fixing. Run them in fresh
sessions, and run at least the first one on Haiku too — persona skills hold on Opus and
slip on smaller models.

## Layout

```
SKILL.md                  the behavior itself (loaded when triggered)
evals.md                  11 test prompts with pass/fail criteria
install.sh / install.ps1  one-line installers (curl | bash, irm | iex)
reference/voice.md        phrasebook — direct never-say/say-instead swaps
reference/situations.md   playbooks for the 10 situations this comes up in
reference/dials.md        intensity levels, endearments, cultural registers, opt-outs
reference/grounding.md    the research behind every rule, with sources
```

Claude reads `SKILL.md` when the skill activates and pulls a `reference/` file only when
it needs one.

## Where it comes from

Every rule traces to something real — attachment theory's safe haven / secure base pair,
Gottman's emotion coaching, Baumrind's authoritative style, Kleinfeld's "warm demander,"
the mental-load literature, and the research on why sycophantic AI makes people more
certain and less correct. Sources and reasoning are in
[`reference/grounding.md`](reference/grounding.md).

## Non-goals

Not a romantic or sexual persona. Not a therapist. Not a reason to soften a real risk. If
something genuinely serious is happening, the skill drops the voice entirely and gets
plain — the persona is never more important than the person.
