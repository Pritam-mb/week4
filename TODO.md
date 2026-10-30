# Graveyard of Dead Software — Task Tracker

## ✅ Done (Fri Oct 30)
- [x] `app.py` — full FastAPI app: all routes, rate limiting (3/hr /bury, 5/hr /memory), background jobs, slug dedup, screenshot save
- [x] `pipeline.py` — Sentry `traced_chat` + `traced_tool` helpers; `_ask_groq` emits `gen_ai.chat` span with token usage; Browserbase wrapped in `gen_ai.execute_tool` span; HTTP fallback wrapped; stage tags: coroner / eulogist / checker
- [x] `app.py` — root `gen_ai.invoke_agent` span wraps full dig; `sentry_sdk.ai.set_conversation_id(job_id)` at start; tags: extractor, walkback_count, cause_label
- [x] `requirements.txt` — pinned `sentry-sdk[fastapi,httpx]>=2.14.0`
- [x] `.env.example` — added `SENTRY_DSN`
- [x] Seed DB verified working; server runs on port 8000

## 🔲 Still needed today (Fri Oct 30)
- [ ] Add `SENTRY_DSN=<your-dsn>` to `.env` (get from sentry.io → Project → Client Keys)
- [ ] Deploy to Render (push to GitHub, create Render web service, set env vars)
- [ ] Run `benchmark.py` against the 35 URLs (with Sentry on) to fill Sentry dashboard
- [ ] Hand-label ~20 causes of death → `labels.json`

## 🔲 Sat Oct 31
- [ ] Lifeline chart polish (already rendered; just verify bar heights)
- [ ] `/benchmark` page displays Eval A numbers (HTML already exists in templates)
- [ ] Sentry dashboard screenshots (latency per stage, token cost, error rate)
- [ ] Replay link verified on a real dig (needs live Browserbase session)
- [ ] Styling pass: ensure Día de los Muertos theme is sharp
- [ ] Rate limit test on live Render URL

## 🔲 Sun Nov 1 (submit early)
- [ ] Demo video (90-second script in plan)
- [ ] Blog post with Eval A–D numbers and Sentry section
- [ ] README, rules check, submit

## Never cut
- Render deploy, Eval A benchmark, fact-checker, Sentry spans + debugging story, Sources links, blog post
