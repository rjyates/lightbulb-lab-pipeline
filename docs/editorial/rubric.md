# Editorial review rubric

[Proposal 5.2](../autonomy/proposal.md#52-editorial-independent-review-separate-cloud-task-about-1200) · [Script gates 6.1](../autonomy/proposal.md#61-script-and-editorial-gates-ci-and-worker) · [Episode format](../../episodes/FORMAT.md)

- **Status:** Draft v0.1, 2026-10-28. Calibration set: fif06–fif11 ([first pass](calibration/2026-10-28-fif06-fif11.md)). Thresholds change only with the owner's agreement.

The reviewer is a separate session that did not write the script. It reads the script as a viewer would hear it: a non-technical adult, often older, possibly anxious about technology.

## 1. Scores

Score each dimension 1–5. Write one line of evidence for every score below 5.

### Accuracy

| Score | Meaning |
| :- | :- |
| 5 | Every factual claim is checked against a current official or primary source; dates, steps and menu names are right for the current software versions. |
| 4 | One minor issue: a menu name that varies by version, or wording that will date soon. Nothing that would mislead a viewer. |
| 3 | A claim that is out of date, unsourced, or true only for some viewers without saying so. |
| 1–2 | A wrong instruction, a wrong date or number, or advice that could cost the viewer money or security. |

Checks:
- Phone numbers, websites and dates are copied from the official source, not from news coverage.
- Menu paths are checked against the vendor's current help page. When names differ by brand or version, the script says so.
- Relative time words (*today*, *this month*, *just announced*, *next week*) are not allowed unless the claim has a `valid_until` date. Prefer absolute dates or *recently*.
- A date that has already passed is described in the past tense.

### Clarity

| Score | Meaning |
| :- | :- |
| 5 | One idea per scene; each step is something a beginner can do without pausing the video; jargon is explained the first time. |
| 4 | One scene packs in too much or uses one unexplained term. |
| 3 | A beginner would get lost or need to rewatch. |
| 1–2 | The main instruction is unclear or missing. |

Checks:
- No more than three instructions in one scene.
- Vague actions are made concrete ("run your security scan" → "open Windows Security and run a quick scan").
- The recap scene matches what the episode taught.

### Mission fit

| Score | Meaning |
| :- | :- |
| 5 | Directly helps a non-technical adult stay safe or get something done; reassuring; tells them what to do next. |
| 4 | Useful, but the "what to do" is weaker than the "what is". |
| 3 | Interesting rather than useful, or aimed at confident users. |
| 1–2 | Off-mission, alarming without a fix, or promotional. |

### Brand voice

| Score | Meaning |
| :- | :- |
| 5 | Calm, warm, plain; Kip explains and Bub reacts; no fear-mongering, no talking down. |
| 4 | One phrase that is too dramatic, too casual or slightly condescending. |
| 3 | Several such phrases, or the tone fights the content. |
| 1–2 | Hype, clickbait, or blaming the viewer. |

Banned: "hack" as a tip, "you won't believe", "insane", "scary truth", "everyone is doing it wrong", "even grandma can", any wording that makes fun of the viewer's age or skill.

## 2. Hard rules (any failure means *changes requested*)

1. **Scam content** tells the viewer to contact the organization using a number or website they look up themselves (on the card, the statement, the official site).
2. **Never** tells the viewer to disable a security feature.
3. **No medical, legal or investment advice** beyond pointing to official, free help.
4. **Already-acted guidance.** Scam episodes include what to do if the viewer already clicked, called or paid.
5. **Length and structure** follow [FORMAT.md](../../episodes/FORMAT.md): 1,300–1,900 characters, 10–14 scenes, Shorts under about 55 seconds, and `python -m lightbulb.check` passes.
6. **Reading level:** Flesch–Kincaid grade 8 or below.
7. **Titles and thumbnails** promise only what the script delivers.
8. **`next` line** names an episode that exists. It is set when the episode is scheduled, not when it is drafted.

## 3. Sensitive topics

Mark `sensitive: true` (and wait for the owner) when the episode is about health or Medicare, money or investments beyond "call your bank", legal matters, or government benefits. Scam-awareness episodes that only say "hang up and call your bank" are not sensitive by themselves.

## 4. Verdict

- **approve:** accuracy 5, no other score below 4, no hard-rule failure.
- **changes requested:** anything else that can be fixed in the script. List each change as *scene number: problem → suggested fix*.
- **reject:** off-mission, unfixable, or duplicates an existing episode.

Record the verdict, the scores, every source checked (URL, publisher, date accessed) and each `valid_until` date. Until schema v2 lands, the record goes in the calibration or review notes under `docs/editorial/`.

## 5. Calibration

The owner scores the same scripts independently. When the owner's verdict and the reviewer's differ, the rubric is fixed, not just the score. The goal for M3 is agreement on at least 5 of every 6 verdicts.
