# 🎬 AI Video Creation Skill — Complete Reference Guide
> Built from real project experience creating demo/explainer videos for AI, automation,
> voice agents, SaaS tools, and developer portfolio projects.
> Covers every step: concept → thumbnail → script → prompts → generation → editing → publishing.

---

## 📌 TABLE OF CONTENTS
1. [Understanding What You Need Before Starting](#1-understanding-what-you-need-before-starting)
2. [Choosing the Right Tool](#2-choosing-the-right-tool)
3. [Color Schemes & Visual Style](#3-color-schemes--visual-style)
4. [Thumbnail Creation (Still Image)](#4-thumbnail-creation-still-image)
5. [Writing the Video Script](#5-writing-the-video-script)
6. [Writing AI Video Prompts](#6-writing-ai-video-prompts)
7. [Scene-by-Scene Structure](#7-scene-by-scene-structure)
8. [Characters & Dialogue (Avatar Videos)](#8-characters--dialogue-avatar-videos)
9. [Clip Generation — Common Mistakes & Fixes](#9-clip-generation--common-mistakes--fixes)
10. [Stitching & Editing in CapCut](#10-stitching--editing-in-capcut)
11. [Voiceover & Transcript Alignment](#11-voiceover--transcript-alignment)
12. [Animating a Still Image (Image-to-Video)](#12-animating-a-still-image-image-to-video)
13. [LinkedIn & Social Media Post](#13-linkedin--social-media-post)
14. [Full Workflow Checklist](#14-full-workflow-checklist)
15. [Prompt Templates Library](#15-prompt-templates-library)

---

## 1. Understanding What You Need Before Starting

Before writing a single prompt, answer these four questions:

| Question | Why it matters |
|---|---|
| What is the product/project? | Defines the story and what objects appear on screen |
| Who is the audience? | Business owners = simple; Developers = technical stack |
| What is the final platform? | YouTube = 16:9; Reels/TikTok = 9:16; LinkedIn = 16:9 or square |
| What is the call-to-action? | Book a call / visit portfolio / contact / buy |

### For AI/automation projects specifically, always map out:
```
Trigger → AI Action → Result → Confirmation
Example:
Phone call → AI agent answers → checks Google Calendar → books slot → sends WhatsApp
```
This is your video story. Every scene = one step in this flow.

---

## 2. Choosing the Right Tool

### For STILL IMAGES (thumbnails, hero frames)
| Tool | Best for | Cost |
|---|---|---|
| ChatGPT (GPT-4o image gen) | Photorealistic scenes + some readable text | ChatGPT Plus |
| Midjourney | Artistic, cinematic, highly stylized | Subscription |
| Adobe Firefly | Clean corporate/SaaS look | Adobe plan |
| DALL-E | Quick iterations | ChatGPT Plus |

**Winner for AI project thumbnails:** ChatGPT image generation — handles complex scenes (person + laptop + floating UI + workflow diagram) better than most.

### For VIDEO GENERATION (text-to-video / image-to-video)
| Tool | Best for | Plan needed |
|---|---|---|
| Google Veo 3 / Flow | Clean 3D motion, product reveals | Google AI Pro (Veo Fast) or Ultra (full Veo 3) |
| Runway Gen-3/4 | Cinematic motion, image-to-video | Paid |
| Kling AI | Good free credits, smooth motion | Free tier available |
| Pika | Quick iterations, decent motion | Free tier available |
| Sora (OpenAI) | High quality, realistic | ChatGPT Pro |

### For AVATAR / TALKING HEAD videos (person speaking dialogue)
| Tool | Best for |
|---|---|
| HeyGen | Most realistic avatar, good lip sync |
| Synthesia | Multiple avatars, enterprise look |
| Built-in avatar (Canva video, etc.) | Quick, integrated with editor |

### For STITCHING + EDITING
| Tool | Best for | Cost |
|---|---|---|
| CapCut | Easiest, free, text-to-speech built in | Free |
| DaVinci Resolve | Professional grade, full control | Free |
| Clipchamp | Simple, browser-based | Free (Windows) |
| Canva Video | Scene-based editor, avatars, voiceover | Free/Pro |

### KEY RULE
> **Image gen tools ≠ video gen tools ≠ editing tools.**
> Use each for what it does best. The best workflow:
> ChatGPT (thumbnail) → Veo/Kling (motion clips) → CapCut (stitch + text + voice)

---

## 3. Color Schemes & Visual Style

### Style options for tech/AI projects

**Option A — Bright SaaS / sky-blue (recommended for demos)**
- Background: bright azure → royal blue gradient
- Accents: white, green (WhatsApp/calendar), blue
- Mood: friendly, modern, accessible
- Reference: Spyne, Calendly, Google style
- Prompt keywords: `bright airy sky-blue and white background, glossy reflective surfaces, blue and green accents, premium SaaS tech aesthetic`

**Option B — Dark corporate / navy**
- Background: deep navy blue
- Accents: lime green, white
- Mood: enterprise, serious, premium
- Reference: Woodmark.de style
- Prompt keywords: `deep navy blue background, bright lime-green glowing accents, crisp white surfaces, clean minimal corporate design`

**Option C — Dark futuristic / neon**
- Background: near-black, dark charcoal
- Accents: cyan, purple, neon blue
- Mood: cutting-edge, dramatic, cyberpunk-lite
- Prompt keywords: `dark studio background, neon cyan and violet glowing accents, volumetric light rays, holographic UI elements`

### Rule: keep ONE style string and use it in EVERY clip
Copy this into every prompt so all your clips match:
```
[your chosen style string], glossy reflective surfaces, volumetric lighting,
bloom, cinematic color grade, shallow depth of field, ultra-detailed, 4k, 60fps.
```

---

## 4. Thumbnail Creation (Still Image)

### The proven thumbnail composition for AI agent/automation projects
Based on real results — this layout works:

```
COMPOSITION:
- Over-the-shoulder view of a woman at a desk (facing AWAY from camera)
- Her face is NOT visible (avoids face-garbling issues)
- Laptop OPEN with the workflow diagram on screen
- Phone on the desk RINGING (ripple rings + green call icon)
- Floating glassmorphism UI cards in the air (chat bubbles, "confirmed" badge)
- Bold text lower-left (add in editor, not AI)
```

### Thumbnail prompt template
```
Create a cinematic, premium 3D-rendered marketing thumbnail, 16:9 widescreen,
bright and airy color palette (soft sky blue, white, warm light — NOT dark).
Over-the-shoulder view from behind a young professional woman sitting at a
clean modern desk, facing away toward her open laptop. Her face is not visible.
She wears a light business-casual blouse.

On the glowing laptop screen, show a clean automation workflow diagram with
connected nodes and arrows: [YOUR STEPS HERE]. The diagram uses simple icons,
rounded boxes, and glowing connector lines in blue and green.

On the desk beside the laptop, a smartphone lies flat and is actively RINGING —
show glowing concentric sound-ripple rings and a green phone-call icon rising
above it. Floating UI cards hover in the air (chat bubble, checkmark, clock).

Soft cinematic studio lighting, gentle bokeh, shallow depth of field, glossy
reflections. Modern SaaS tech aesthetic, premium, high detail, 3D render look. 4k.
```

### Important: TEXT in AI-generated images
- AI tools garble text ~70% of the time (emails, phone numbers, labels)
- Let AI make the SCENE and SHAPES
- Add all real text (title, contact, workflow labels) yourself in Canva/CapCut

---

## 5. Writing the Video Script

### The connected story structure (most important rule)
**Wrong:** 7 separate unrelated scenes
**Right:** One continuous story split across scenes — each scene hands off to the next

```
SCENE 1: Setup the problem / introduce the product + "Here's how it works"
SCENE 2: Step 1 of workflow
SCENE 3: Step 2 ...
...
LAST SCENE: Result + call to action
```

### Connector words between scenes
Use these at the start of each voiceover line to make it feel like one story:
- "First..." / "Then..." / "Next..." / "From there..." / "Meanwhile..." / "And finally..."

### Word count per second (for timing)
- 1 second = ~2.5 words at a natural pace
- 5 second clip = max 12 words
- 8 second clip = max 20 words
- 10 second clip = max 25 words

---

## 6. Writing AI Video Prompts

### The 4 parts of a good video prompt
```
1. STYLE:     "Cinematic 3D animation, bright airy sky-blue and white background..."
2. SCENE:     "A glossy smartphone on a clean desk..."
3. ACTION:    "The phone lights up with an incoming call, glowing ripple rings pulse outward..."
4. QUALITY:   "...glossy reflections, volumetric lighting, bloom, ultra-detailed, 4k, 60fps."
```

### CRITICAL RULES for prompts
1. **One clip per prompt** — never paste a full multi-step script as one prompt. The tool compresses it into 5 seconds.
2. **Mention continuity** — start each new clip with: "continuing seamlessly from the previous shot with the same [phone/orb/background]"
3. **Never rely on text in the video** — AI garbles words inside cards/bubbles. Let it make shapes, add real text in the editor.
4. **No bell/ring after the call connects** — if a call was established in the previous clip, write "call still connected, green active indicator, NO ringing"
5. **Set max clip length** — always generate at the maximum your tool allows (8s Veo, 10s Kling/Runway)

### Global style string — prepend to every prompt
```
Cinematic 3D animation, bright airy sky-blue and white background, glossy
reflective surfaces, volumetric lighting, bloom, shallow depth of field,
premium SaaS tech aesthetic, blue and green accents, ultra-detailed, 4k, 60fps.
```

---

## 7. Scene-by-Scene Structure

### Standard structure for an AI/automation project demo video

| Clip | Name | Duration | Content |
|---|---|---|---|
| 0 | Intro / hook | 5s | Thumbnail animated OR problem hook scene |
| A | Trigger | 6s | The event that starts the flow (call comes in) |
| B | AI responds | 6s | Agent greets, conversation starts |
| C | Core action | 10s | The key automation (check calendar, book, etc.) |
| D | Result | 7s | Confirmation delivered (WhatsApp, email, calendar) |
| E | CTA close | 8s | Logo + contact details + call to action |

### Hook options for Clip 0 (opening)
- **Problem hook:** show the pain (missed calls, piling messages) then AI solves it
- **Hero product shot:** key objects orbiting around the product
- **Character intro:** friendly robot/avatar greeting the camera
- **Animate the thumbnail:** upload the still image and animate it (best if thumbnail already looks great)

---

## 8. Characters & Dialogue (Avatar Videos)

### Setup for two-character conversation
- **Agent character:** female voice (warm, friendly) — name: Finley / Aria / Riley
- **Client character:** male voice (natural) — name: Sebastian / David / James
- Attach two avatars in the tool BEFORE generating

### Dialogue structure for a booking conversation
```
Client:  "Hi, I want to book an appointment."
Agent:   "Sure! May I have your name, please?"
Client:  "My name is [Name]."
Agent:   "Thank you. What date and time would you prefer?"
Client:  "I'd like [day] morning."
Agent:   "Let me check [Calendar] for that time…"
Agent:   "[Time] is available. Shall I book it?"
Client:  "Yes, please book it."
Agent:   "Booking your appointment under the name [Name]."
[ON SCREEN: Booking Confirmed — Name · Day · Time]
```

### Dialogue split rule (10-second clip limit)
- Max ~5 dialogue lines per 10-second clip
- Split long conversations into two clips:
  - Clip A: greeting → name → preferred time (5–6 lines)
  - Clip B: checking calendar → offer slot → confirm booked (4–5 lines)
- Start Clip B with "continuing seamlessly from the previous shot" so they feel connected

### On-screen text for dialogue (always add manually)
- Let AI make the bubble shapes and motion
- Type the actual dialogue words yourself with the Text tool
- Alternate left/right: agent bubbles right, client bubbles left

---

## 9. Clip Generation — Common Mistakes & Fixes

| Problem | Cause | Fix |
|---|---|---|
| Video too short / rushed | Pasted full script as one prompt | One prompt per clip only |
| Colors flat / not vibrant | Missing quality boosters | Add: "hyper-saturated, glossy reflective surfaces, volumetric lighting, bloom, cinematic color grade" |
| Didn't show full workflow | Too many steps in one clip | Split into more clips |
| Bell keeps ringing | Didn't specify no ring | Add: "call still connected, green active indicator, NO ringing" |
| Scenes look inconsistent | Different style per clip | Copy-paste the same global style string into every prompt |
| Text garbled in bubbles | AI can't render text reliably | Add text with Text tool in editor after generation |
| Clip B looks different from Clip A | No continuity instruction | Start Clip B prompt with "continuing from the previous shot with the same [objects]" |
| Avatar says wrong thing | Voiceover and video prompts mixed up | Video prompt = visuals only; Voiceover panel = spoken words |
| Too many credits used | Generating the whole video in one go | Always preview/test one clip first |

---

## 10. Stitching & Editing in CapCut

### Assembly order
1. Import all clips in scene order
2. Trim each clip to its exact intended length
3. Add transitions: **subtle cross-dissolve** (0.3s) between scenes, or **none** for a seamless conversation
4. Add voiceover (CapCut text-to-speech or record)
5. Add on-screen text (dialogue bubbles, labels, captions)
6. Add background music (subtle, builds gently, resolves on CTA)
7. Export 1920×1080 for YouTube/LinkedIn, 1080×1920 for Reels

### Transitions by scene type
- Scene to scene (different step): soft cross-dissolve
- Continuation (same conversation): no transition / direct cut
- Big moment (booking confirmed): quick flash or zoom-in punch
- Closing CTA: fade to white or logo reveal

---

## 11. Voiceover & Transcript Alignment

### The alignment problem
AI video clips have a fixed generated length (often 5–10s).
Voiceover has a different length based on word count and speaking pace.
They drift apart = voiceover finishes before video or keeps talking over the next scene.

### The fix: let the video drive, not the script
1. Generate the AI video clip first — check its actual length
2. Set scene duration = clip length
3. Write a voiceover line that fits: 2.5 words × seconds = max word count
4. If the voice is still long, trim 1–2 words

### Two-voice conversation alignment
- Use two different avatar voices (male + female) — much clearer than one voice doing both
- Keep each line SHORT (5–8 words max per line)
- If only one voice is available: use it for agent lines, add client lines as animated text only

---

## 12. Animating a Still Image (Image-to-Video)

### When to use this
- You already have a perfect thumbnail and want to animate it
- You want exact control over the composition (AI text-to-video won't reproduce it exactly)
- You want the text in the image to stay readable (it won't regenerate garbled)

### Image-to-video prompt template
```
Animate this image into a cinematic [X]-second intro, keeping the composition
exactly as it is. Add life: [list specific elements to animate]. Slow gentle
camera push-in toward [focal point]. [Style string]. Clear, readable on-screen text.
```

### What to animate (from your real project thumbnail)
```
- The ringing phone: pulses with glowing concentric sound-ripple rings, green
  call icon gently bobs
- The floating UI cards: softly drift and glow
- The workflow diagram on screen: icons light up one after another left-to-right,
  glowing connector lines animate between them
- Background: subtle floating light particles
- Camera: slow gentle push-in toward the laptop
```

### Plan limitation note
- Image-to-video is often gated to higher tier plans (e.g., Google AI Ultra, not Pro)
- If unavailable: use Kling AI, Runway, or Pika — all allow image uploads on free/cheaper tiers

---

## 13. LinkedIn & Social Media Post

### Post structure (LinkedIn algorithm-optimized)
```
LINE 1-2:  Hook (the scroll-stopper — everything before "see more")
LINE 3:    Transition / "Here's the demo 👇"
LINE 4-10: Bullet-point breakdown of what it does
LINE 11:   The problem it solves (one sentence)
LINE 12:   Tech stack mention (brief — Vapi, AWS, etc.)
LINE 13:   Builder mention (built with Kiro, etc.)
LINE 14:   CTA line
LINE 15:   Contact details (website, email, phone)
LINE 16:   Hashtags
```

### Hook formulas that work
- **Demo hook:** "A customer called. The AI answered, checked the calendar, booked the slot, and confirmed — with zero human involvement."
- **Problem hook:** "Every missed call is a missed customer. So I built an AI that never misses one."
- **Bold claim:** "Your front desk doesn't need to be human anymore."
- **Relatable scenario:** "It's 9 PM. A customer calls. Your office is closed. With this, the AI picks up anyway."

### LinkedIn link tip
Putting a URL in the main post body slightly reduces reach.
Two options:
1. Put the link in the post (simpler, slightly less reach)
2. Write "portfolio link in the first comment 👇" and put the URL in a comment (more reach)

### Hashtag set for AI agent / automation projects
```
#AI #Automation #VoiceAI #Vapi #AIAgents #SmallBusiness
#BuildInPublic #LLM #Kiro #SaaS #MachineLearning
```

---

## 14. Full Workflow Checklist

### From zero to published video

**PLANNING**
- [ ] Map the full automation flow (trigger → steps → result)
- [ ] Decide final platform (YouTube / LinkedIn / Reels)
- [ ] Choose visual style (bright SaaS / dark corporate / neon)
- [ ] Pick color palette and write global style string

**THUMBNAIL**
- [ ] Write thumbnail prompt (woman + laptop + workflow diagram + ringing phone)
- [ ] Generate in ChatGPT image gen
- [ ] Add title text + contact manually in Canva/CapCut
- [ ] Save as PNG/JPG 16:9

**SCRIPT**
- [ ] Write connected voiceover (one story, not separate chunks)
- [ ] Match word count to clip length (2.5 words/sec)
- [ ] Assign lines per scene

**VIDEO PROMPTS**
- [ ] Write one prompt per clip
- [ ] Add global style string to every prompt
- [ ] Add continuity instruction to clips 2+
- [ ] Add "NO ringing" to clips after call connects
- [ ] Add dialogue to avatar/voiceover panel separately

**GENERATION**
- [ ] Generate clips one at a time
- [ ] Note actual length of each clip
- [ ] Regenerate any that look off (max 2 tries then adjust prompt)

**EDITING (CapCut)**
- [ ] Import all clips in order
- [ ] Add transitions
- [ ] Add voiceover (Nyla or record)
- [ ] Add on-screen text (dialogue, labels, captions)
- [ ] Add background music
- [ ] Add contact CTA on final frame
- [ ] Export 1920×1080

**PUBLISHING**
- [ ] Write LinkedIn post (hook + bullets + CTA + hashtags)
- [ ] Upload video + thumbnail
- [ ] Put portfolio link in first comment if needed

---

## 15. Prompt Templates Library

### Template 1 — Phone call comes in (opening scene)
```
Cinematic 3D animation, bright airy sky-blue and white background. A glossy
smartphone on a clean desk lights up with an incoming call, glowing concentric
sound-ripple rings pulsing outward from it and a green phone-call icon rising
above. Slow smooth camera push-in, glossy reflections, floating light particles,
shallow depth of field, premium SaaS tech aesthetic, blue and green accents,
ultra-detailed, 4k, 60fps.
```

### Template 2 — AI agent answers (continuing from call)
```
Cinematic 3D animation, bright airy sky-blue and white background, continuing
from the previous shot — same glossy smartphone, call now connected (green
active indicator, NO ringing). A friendly glowing blue AI assistant orb with a
flowing sound-wave inside appears beside the phone and pulses as it speaks. A
greeting chat bubble rises from the orb. Glossy reflections, floating light
particles, premium SaaS tech aesthetic, blue and green accents, ultra-detailed,
4k, 60fps.
```

### Template 3 — Calendar check
```
Cinematic 3D animation, bright airy sky-blue and white background, continuing
from the previous shot. A clean Google Calendar panel with a recognizable
calendar grid and "31" date icon slides in; the AI orb sends a glowing beam
into it and a scan animation sweeps across the dates, most slots appearing
greyed-out and booked, while a single slot glows bright green to show it is
available. Glossy reflections, floating light particles, premium SaaS tech
aesthetic, blue and green accents, ultra-detailed, 4k, 60fps.
```

### Template 4 — Booking confirmed
```
Cinematic 3D animation, bright airy sky-blue and white background. A single
highlighted appointment card lifts off and snaps satisfyingly into place, a
radiant green checkmark forms on top with a burst of glowing sparkles, and a
"Booking Confirmed" badge with a name and time fades into view. Punchy
micro-animation, glossy reflections, premium SaaS tech aesthetic, blue and
green accents, ultra-detailed, 4k, 60fps.
```

### Template 5 — WhatsApp + Calendar invite sent
```
Cinematic 3D animation, bright airy sky-blue and white background, split
composition: on the left a green WhatsApp-style chat bubble flying in with a
confirmation message and a highlighted link; on the right a Google Calendar
event card dropping into a calendar grid with a glowing bell notification icon.
Two luminous paper-plane send trails arc from a central glowing AI orb to each
side. Glossy reflections, floating particles, premium SaaS tech aesthetic, blue
and green accents, ultra-detailed, 4k, 60fps.
```

### Template 6 — CTA closing
```
Cinematic 3D animation, bright airy sky-blue and white background. All previous
elements gently drift inward and dissolve into glowing particles converging at
the center to form a clean logo lockup with open space for a brand name. Three
small glowing feature icons orbit gently around it. Premium product-reveal
lighting, elegant particle motion, the camera settling on a crisp static hero
frame. Leave clean lower-third space for contact details to be added in the
editor. Glossy reflections, blue and green accents, premium SaaS tech aesthetic,
ultra-detailed, 4k, 60fps.
```

### Template 7 — Animate a still image
```
Animate this image into a cinematic 5-second intro, keeping the composition
exactly as it is. Add life: the ringing phone pulses with glowing concentric
sound-ripple rings; the floating UI cards softly drift and glow; the workflow
diagram icons on the laptop screen light up one after another in sequence with
glowing connector lines animating left to right; subtle floating light particles
in the air; a slow gentle camera push-in toward the laptop. Bright airy
sky-blue cinematic look, glossy reflections, premium SaaS tech aesthetic,
ultra-detailed, 4k.
```

---

*Built from real experience creating demo videos for the Calling Agent Receptionist
AI voice agent project — FastAPI + AWS Lambda + Vapi + Amazon Nova + Google Calendar
+ WhatsApp Evolution API. Developed with Kiro.*
