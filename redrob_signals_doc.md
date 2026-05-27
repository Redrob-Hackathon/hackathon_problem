# Redrob Behavioral Signals — Reference (v2)

This document explains the 23 behavioral signals embedded in each candidate's `redrob_signals` object, how they relate to candidate quality, and how they're constructed in the synthetic dataset.

---

## What are Redrob signals?

In a real recruiting platform, candidates generate observable behavior beyond what they list in their profile:
- Do they actually respond to recruiter messages?
- Have they logged in recently?
- Did they complete the assessments they started?
- Are recruiters saving their profile?
- Have they completed previous interview cycles?

These behavioral signals are often **more predictive** of whether a candidate can actually be hired than their static profile. A perfect-on-paper candidate who hasn't logged in for 6 months and has a 5% response rate is, for hiring purposes, not actually available.

This dataset includes these signals so that ranking systems can incorporate them as a multiplier or modifier on top of skill-match scoring.

---

## The 23 signals

| # | Signal | Range | What it measures |
|---|---|---|---|
| 1 | `profile_completeness_score` | 0-100 | How much of the profile they've filled in |
| 2 | `signup_days_ago` | 5-1500 | Days since they signed up on Redrob |
| 3 | `last_active_date` | date string | When they last logged in |
| 4 | `open_to_work_flag` | bool | Have they marked themselves available |
| 5 | `profile_views_30d` | 0-400 | How often their profile has been viewed by recruiters in last 30 days |
| 6 | `applications_30d` | 0-25 | How many roles they've applied to recently |
| 7 | `recruiter_response_rate` | 0.0-1.0 | What fraction of recruiter messages they reply to |
| 8 | `avg_response_time_hours` | 1-280 | Median time to respond to a recruiter message |
| 9 | `skill_assessment_score` | 0-100 | Average score across Redrob's skill assessments they've taken |
| 10 | `skill_assessments_completed` | list[str] | Which assessments they completed |
| 11 | `connections` | 10-2000 | Number of Redrob connections |
| 12 | `total_endorsements` | 0-250 | Total skill endorsements received |
| 13 | `notice_period_days` | 0-180 | Their stated notice period |
| 14 | `expected_salary_lpa_min/max` | 3-75 | Salary expectations in LPA |
| 15 | `work_mode_preference` | onsite/hybrid/remote/flexible | Their stated preference |
| 16 | `willing_to_relocate` | bool | Will they relocate if needed |
| 17 | `github_activity_score` | -1 to 100 | GitHub commits/contributions score (-1 if no GitHub linked) |
| 18 | `search_appearances_30d` | 0-1500 | How often they show up in recruiter searches |
| 19 | `saved_by_recruiters_30d` | 0-80 | How many recruiters bookmarked them in last 30 days |
| 20 | `interview_completion_rate` | 0.0-1.0 | What fraction of interviews they've actually attended |
| 21 | `offer_acceptance_rate` | -1 to 1.0 | What fraction of offers they accepted (-1 if no prior offers) |
| 22 | `verified_email` / `verified_phone` / `linkedin_connected` | bool | Identity verification flags |
| 23 | `endorsements_per_skill` | dict[str, int] | Per-skill endorsement counts |

---

## How signals relate to candidate tier (v2)

The dataset assigns each candidate a hidden "relevance tier" (0-5) for the **public JD** (Senior AI Engineer). Tier 5 is a perfect fit; tier 0 is completely irrelevant.

For each tier, the generator picks a "signal envelope" — a range of typical values for each signal. The candidate's actual signal values are sampled randomly from within their tier's envelope.

### Important v2 change: envelopes overlap heavily

In v1, signal envelopes had only narrow overlap between adjacent tiers (e.g. Tier 5 response rate was 0.70-0.98; Tier 1 was 0.10-0.60 — almost no overlap on this signal).

**In v2, envelopes overlap substantially:**

| Signal | Tier 5 range | Tier 1 range | Overlap |
|---|---|---|---|
| `recruiter_response_rate` | 0.55-0.98 | 0.10-0.85 | 0.55-0.85 (heavy) |
| `profile_completeness_score` | 55-100 | 30-88 | 55-88 (heavy) |
| `last_active_days_ago` | 0-60 | 0-180 | 0-60 (heavy) |
| `saved_by_recruiters_30d` | 5-80 | 0-20 | 5-20 (medium) |
| `total_endorsements` | 15-250 | 0-75 | 15-75 (medium) |
| `github_activity_score` | 30-100 | 0-65 | 30-65 (medium) |

**Why we changed this:** in v1, a single high-value signal (like a high response rate) was a strong proxy for tier. A naive system that simply sorted by response rate could score reasonably well. In v2, no single signal cleanly separates tiers — you need to combine multiple signals **with profile content** to get good ranking quality.

A system that only uses signals (without reading the profile) will perform near-random.
A system that combines profile content + signals contextually will perform well.

---

## Edge cases that signals are designed to expose (v2 traps)

The v2 dataset deliberately includes "trap" candidates whose profile content disagrees with their behavioral signals — or vice versa. A well-designed ranking system handles these cases correctly.

### Trap A — Stealth high-performer

A Tier 5 candidate with **perfect AI engineering skills and experience**, but:
- `last_active_date` is 75-220 days ago
- `recruiter_response_rate` is 0.03-0.20
- `open_to_work_flag` = false
- `saved_by_recruiters_30d` ≤ 5

**The trap:** a system that filters by engagement signals will drop them. A system that *only* uses profile content will rank them perfectly. The correct behavior depends on the JD's hiring urgency, but for a hackathon, a moderate down-weighting is appropriate (they're great but probably not reachable).

**Frequency:** ~25% of Tier 5 candidates.

### Trap B — Plain-language Tier 5

A Tier 5 candidate whose actual experience is described in **plain English** ("built systems that surface relevant content") with no jargon. Their skill list uses generic terms like "Information Retrieval", "Search Backend", "Search & Discovery" instead of "RAG", "Pinecone", "Weaviate".

**The trap:** a keyword matcher misses them entirely. Only a semantic ranker (or a system that reads the career history) will catch them.

**Frequency:** ~25% of Tier 5 candidates.

### Trap C — Keyword stuffer

A Tier 0 candidate (e.g., Marketing Manager, Customer Support, Mechanical Engineer) whose skill list contains **dense AI keywords**: LangChain, RAG, LLMs, Vector Search, FAISS, Pinecone, Embeddings, etc. They've added these because Twitter said it would help their profile.

**The trap:** their headline mentions AI/GenAI; their summary says they're "exploring" AI applications. But their job title and career history clearly show they don't do AI engineering. Their `endorsements` per skill is suspiciously low (0-4 typical) — a real expert has dozens.

A keyword matcher ranks them top-10. A system that reads the title or checks endorsement quality rejects them.

**Frequency:** ~8% of Tier 0 candidates (which is a lot — ~5,500 in a 100K dataset).

### Trap D — Behavioral twin pairs

For ~10% of Tier 3 candidates, the generator creates a corresponding Tier 1 candidate with **nearly identical skills**. The only difference is behavioral signals:
- The Tier 3 has high engagement (0.78-0.95 response rate, recently active, high completeness).
- The Tier 1 has low engagement (0.02-0.18 response rate, 120-240 days inactive, low completeness).

**The trap:** a system that only looks at skills can't distinguish them. A system that incorporates engagement signals correctly puts the Tier 3 above the Tier 1.

**Frequency:** ~1% of Tier 3 candidates + ~0.5% of Tier 1 candidates (paired).

### Honeypots

A small number (~80 in a 100K dataset, 0.08%) of candidates have **subtly impossible profiles**:
- 8 years of experience at a company that didn't exist 8 years ago
- "Expert" proficiency in 5 skills with `years_used = 0`
- Career stint duration exceeding total years of experience
- Certifications dated 2030

Honeypots are **forced to relevance tier 0 across all 5 JDs**. A system that genuinely reads profiles will reject them. A system that just embeds-and-ranks will rank them high.

At Stage 3, organizers flag submissions where honeypot rate in top-100 exceeds 10%.

---

## How to think about using signals

For a Senior AI Engineer JD (the public JD in this hackathon), a reasonable signal-aware scoring approach might look like:

```python
def signal_modifier(candidate):
    s = candidate["redrob_signals"]

    # Base modifier from response rate (continuous)
    base = 0.4 + 0.6 * s["recruiter_response_rate"]

    # Active in the last 60 days
    last_active = days_since(s["last_active_date"])
    if last_active <= 14:
        base *= 1.1
    elif last_active <= 60:
        base *= 1.0
    elif last_active <= 120:
        base *= 0.8
    else:
        base *= 0.5  # very inactive

    # Open to work
    if not s["open_to_work_flag"]:
        base *= 0.6

    # Recruiter interest signal
    if s["saved_by_recruiters_30d"] >= 10:
        base *= 1.05

    return base

final_score = profile_match_score(candidate, jd) * signal_modifier(candidate)
```

This is illustrative, not prescriptive — the actual best combination is something you should determine.

---

## What NOT to do

**Don't rank purely by signals.** Signals overlap heavily across tiers; a high response rate could be a Tier 5, Tier 3, or Tier 1 candidate.

**Don't rank purely by skills.** The trap candidates are designed to defeat this.

**Don't ignore signal-profile contradictions.** A candidate with great skills but a 0.04 response rate is probably not actually available — and a candidate with mediocre skills but perfect engagement could be a hidden gem.

**Don't trust `total_endorsements` blindly.** Keyword stuffers have many "advanced" AI skills with very low per-skill endorsements. The ratio of endorsements to claimed skills is more informative than the total.

---

## What honeypots tell you about real-world skepticism

In production, the equivalent of honeypots includes:
- Candidates who lie about their experience (claiming 10 years when LinkedIn shows 4)
- Candidates whose career timelines don't add up
- Candidates with "expert" claims on technologies that didn't exist yet
- Skills bought from third-party endorsement services

A good recruiting system should detect these inconsistencies. The hackathon's honeypot mechanism is a synthetic version of this real-world need.
