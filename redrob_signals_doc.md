# Redrob Behavioral Signals — Reference

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


| #   | Signal                                                     | Range                         | What it measures                                                      |
| --- | ---------------------------------------------------------- | ----------------------------- | --------------------------------------------------------------------- |
| 1   | `profile_completeness_score`                               | 0-100                         | How much of the profile they've filled in                             |
| 2   | `signup_days_ago`                                          | 5-1500                        | Days since they signed up on Redrob                                   |
| 3   | `last_active_date`                                         | date string                   | When they last logged in                                              |
| 4   | `open_to_work_flag`                                        | bool                          | Have they marked themselves available                                 |
| 5   | `profile_views_30d`                                        | 0-400                         | How often their profile has been viewed by recruiters in last 30 days |
| 6   | `applications_30d`                                         | 0-25                          | How many roles they've applied to recently                            |
| 7   | `recruiter_response_rate`                                  | 0.0-1.0                       | What fraction of recruiter messages they reply to                     |
| 8   | `avg_response_time_hours`                                  | 1-280                         | Median time to respond to a recruiter message                         |
| 9   | `skill_assessment_score`                                   | 0-100                         | Average score across Redrob's skill assessments they've taken         |
| 10  | `skill_assessments_completed`                              | list[str]                     | Which assessments they completed                                      |
| 11  | `connections`                                              | 10-2000                       | Number of Redrob connections                                          |
| 12  | `total_endorsements`                                       | 0-250                         | Total skill endorsements received                                     |
| 13  | `notice_period_days`                                       | 0-180                         | Their stated notice period                                            |
| 14  | `expected_salary_lpa_min/max`                              | 3-75                          | Salary expectations in LPA                                            |
| 15  | `work_mode_preference`                                     | onsite/hybrid/remote/flexible | Their stated preference                                               |
| 16  | `willing_to_relocate`                                      | bool                          | Will they relocate if needed                                          |
| 17  | `github_activity_score`                                    | -1 to 100                     | GitHub commits/contributions score (-1 if no GitHub linked)           |
| 18  | `search_appearances_30d`                                   | 0-1500                        | How often they show up in recruiter searches                          |
| 19  | `saved_by_recruiters_30d`                                  | 0-80                          | How many recruiters bookmarked them in last 30 days                   |
| 20  | `interview_completion_rate`                                | 0.0-1.0                       | What fraction of interviews they've actually attended                 |
| 21  | `offer_acceptance_rate`                                    | -1 to 1.0                     | What fraction of offers they accepted (-1 if no prior offers)         |
| 22  | `verified_email` / `verified_phone` / `linkedin_connected` | bool                          | Identity verification flags                                           |
| 23  | `endorsements_per_skill`                                   | dict[str, int]                | Per-skill endorsement counts                                          |


