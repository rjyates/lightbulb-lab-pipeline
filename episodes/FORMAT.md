# Episode script format

One file per episode: `episodes/ep06-what-is-the-cloud.json`. Check it with `python3 -m lightbulb.check`.

```json
{
 "id": "ep06", "number": 6, "series": "Tech from Scratch", "title": "What Is the Cloud?",
 "status": "ready",
 "next": "Next: Passwords That Actually Work",
 "description": "One or two sentences for YouTube.",
 "tags": ["what is the cloud"],
 "thumbnail": {"line1": "WHAT IS", "line2": "THE CLOUD?", "sub1": "Tech from Scratch", "sub2": "Episode 6"},
 "scenes": [
  {"say": "A hook question.", "kip": "ask", "bub": "curious"},
  {"say": "Today on Tech from Scratch: what is the cloud?", "title": true},
  {"say": "Your photos, your email, your files...", "card": {"type": "grid", "title": "Things in the cloud",
     "items": [{"icon": "photo", "label": "Photos", "at": "photos"}, {"icon": "mail", "label": "Email", "at": "email"}]}},
  {"say": "More about the same card.", "card": "keep"},
  {"say": "Wrap-up and subscribe line.", "kip": "rest"}
 ],
 "shorts": [{"hook": "The cloud is just someone else's computer", "scenes": [2, 3]}]
}
```

**Scenes.** Each `say` is one beat (one to three sentences). Kip pauses between scenes.
Aim for 10–14 scenes and 1,300–1,900 characters total (about 2 minutes).

**`kip`** pose: `rest`, `point`, `open`, `shrug`, `ask`, `type`, `wave`. Default: `point` when a card is up, else `rest`.
**`bub`** mood: `happy`, `curious`, `aha`, `confused`, `sleepy`.
**`title: true`** shows the full-screen episode title during that scene (use once, scene 2).

**Cards** (the explainer board on the right):
| type | fields | good for |
|---|---|---|
| `grid` | `title`, up to 6 `items` {icon, label} | lists of examples |
| `tiles` | `title`, up to 4 `items` {icon, word, sub} | "4 jobs", big keywords |
| `callout` | `title`, 3 `items` {icon, label} | a heading plus three examples |
| `statement` | `icon`, `text`, `sub` | one key sentence |
| `compare` | `title`, `left`/`right` {icon, title, points[3]}, `at` [2 words] | X vs Y |
| `steps` | `title`, up to 5 `items` {icon, label, sub} | recaps, how-tos |
| `flow` | `title`, up to 4 `items` {icon, label, sub} | A → B → C |

`at` = a word from that scene's `say`. The item pops in the moment Kip says it.
Run the checker to see the full icon list.

**Shorts**: `scenes: [first, last]` (inclusive), keep under ~55 seconds. The `hook` is the big text at the top.
