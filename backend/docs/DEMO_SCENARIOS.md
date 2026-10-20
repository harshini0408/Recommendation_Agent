# Demonstration and local evaluation

Start both services and use a fresh conversation for each scenario. Live interpretation can vary; expected numerical catalogue outcomes below are deterministic once the requirements are extracted correctly. Verify the requirements panel before interpreting recommendations.

| Scenario | Customer messages | Expected application result |
|---|---|---|
| Vague college request | `I need a laptop for college.` then `Programming under 80000, 16 GB RAM. I carry it daily.` | Ask use case, then show two eligible products and portability preference |
| Complete request | `Laptop for programming under 80000 with 16 GB RAM` | Direct recommendations without another question |
| Budget change | Complete the above, then `Actually my budget is 60000` | Preserve programming/RAM, enforce new ceiling |
| One match | `General coursework under 28000` | Exactly CC-001 at INR 28000 |
| No match | `Programming under 20000 with 16 GB RAM` | Zero compliant recommendations; budget proposal based on catalogue |
| Explicit acceptance | After no-match proposal, `yes` | Apply the proposed ceiling; rerun filters |
| Proposal rejection | After proposal, `no thanks` | Original ceiling remains; no automatic relaxation |
| Unknown weight | `Programming under 90000, maximum weight 2 kg` | CC-016 (missing weight) excluded |
| Local ML clarification | `Machine learning under 100000` then `Mostly local experiments` | Clarify local/cloud, then rank using local-ML heuristic |
| Remove a requirement | `Programming under 100000; must have dedicated graphics` then `I no longer need dedicated graphics` | CLEAR the mandatory GPU condition, not set false |
| Conflicting budget | `My maximum is 60000 and 80000, I am not sure which` | Live model identifies ambiguity; asks for resolution |
| Product reference | After recommendations, `Tell me about the second one` | Facts for the previous second product |
| Reload | Refresh after a completed conversation | History, state and latest results restored |
| Unsupported category | `I want a phone` | Honest laptop-only scope explanation |

The demo parser supports only simple English patterns; contradiction resolution and arbitrary phrasing must be tested with the live model. Do not use demo-mode success as evidence of LLM quality.

## Evaluation record

For each live run, record input, resulting extracted state, response type, selected IDs, whether every hard constraint passed, unsupported factual claims (if any), unnecessary questions, and measured latency. Save actual results in a new local record. Do not invent measurements. Keep customer data and keys out of any screenshots.

## Browser checklist

- New conversation, pending indicator, Enter/Shift+Enter, keyboard focus.
- Failed requests leave text available for retry; no indefinite spinner.
- Budget change updates panel and product cards together.
- No-match clears old cards and preserves hard constraints.
- Product detail uses real GET endpoint; unknown values remain visible.
- Refresh restores the correct conversation.
- At 390 px and 1440 px widths, no horizontal overflow or clipped controls.
- If API is stopped, show a useful connection error.
- Live mode without key displays setup guidance; demo mode is visibly labelled.

## Meeting flow

Show a vague request, clarify it, demonstrate requirements updating, review two factual cards, change the budget, then trigger and recover from no match. Finish with `/docs`, a catalogue record, tests, and the state/filters/ranking code. Exact meeting time is supplied separately by the organizer.
