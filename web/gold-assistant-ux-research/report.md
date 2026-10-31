# Gold Assistant UX Deep Research Report

Topic: UX needs of real users for Gold Assistant (Thai retail gold investor AI dashboard)  
Generated: 2026-10-28 | Items: 8 | Sources: web research agents (per-item JSON in results/)

## Table of Contents

1. [Benchmark: Global fintech dashboards with AI (Revolut gold/commodities, Robinhood, Wealthsimple, Cleo, Copilot Money, Empower/Personal Capital)](#1-benchmark-global-fintech-dashboards-with-ai-revolut-gold-commodities-robinhood-wealthsimple-cleo-copilot-money-empower-personal-capital) - confidence: medium — findings are triangulated from one primary usabilit | A cross-product study of consumer fintech apps known for easy dashboards and AI assistants
2. [Benchmark: Thai gold apps (YLindo, Kaiy/Gahtong, GT Goldtrend, GOLD NOW by Hua Seng Heng, V-GO Online by MTS, KKP Dime gold)](#2-benchmark-thai-gold-apps-ylindo-kaiy-gahtong-gt-goldtrend-gold-now-by-hua-seng-heng-v-go-online-by-mts-kkp-dime-gold) - confidence: low-medium — ratings, feature claims and market positioning  | A six-app benchmark of how Thai retail gold apps serve price-watching, online gold trading
3. [Pattern: AI assistant transparency and trust UX](#3-pattern-ai-assistant-transparency-and-trust-ux) - confidence: medium - converging support from experimental research (Stan | How consumer AI analysis products earn CALIBRATED (not blind) trust: show each agent's rea
4. [Pattern: Portfolio dashboard UX best practices](#4-pattern-portfolio-dashboard-ux-best-practices) - confidence: medium - the first-screen hierarchy, progressive disclosure, | Proven dashboard patterns for retail investors: answer the four first-screen questions (wh
5. [Segment: Active short-term gold traders (Thai online gold-trading app users)](#5-segment-active-short-term-gold-traders-thai-online-gold-trading-app-users) - confidence: medium — the trust/scam/withdrawal findings and the real-tim | Thai retail traders who buy and sell gold frequently on intraday-to-days horizons via onli
6. [Segment: DCA long-term accumulators](#6-segment-dca-long-term-accumulators) - confidence: medium - the segment's market context, product norms, and ex | Thai gold investors who buy a fixed amount on a regular schedule (monthly baht-cost averag
7. [Segment: First-time gold savers (Thai retail users new to gold, buying small bars or saving via gold-savings apps)](#7-segment-first-time-gold-savers-thai-retail-users-new-to-gold-buying-small-bars-or-saving-via-gold-savings-apps) - confidence: medium - app landscape, minimums, lock-ups, redemption rules | Thai users new to gold - largely younger salaried/first-job and Gen Z savers - who treat g
8. [Segment: Traditional older shop customers (Thai walk-in gold-shop seniors)](#8-segment-traditional-older-shop-customers-thai-walk-in-gold-shop-seniors) - confidence: medium - scam-pattern and price-board mechanics are directly | Thai users roughly 55-75+ whose entire gold habit was built at the physical counter - read

## 1. Benchmark: Global fintech dashboards with AI (Revolut gold/commodities, Robinhood, Wealthsimple, Cleo, Copilot Money, Empower/Personal Capital)

*Fields marked uncertain: top_pains, confusion_points, workflow_preferences*

### basic_info

**item_name**: Benchmark: Global fintech dashboards with AI (Revolut gold/commodities, Robinhood, Wealthsimple, Cleo, Copilot Money, Empower/Personal Capital)

**one_liner**: A cross-product study of consumer fintech apps known for easy dashboards and AI assistants, extracting the concrete patterns they use to make numbers feel simple and AI insights feel trustworthy, and mapping them onto the Gold Assistant Thai gold-portfolio redesign.

### needs

**jobs_to_be_done**: Users of these products are fundamentally trying to: (1) get an answer in under 5 seconds — 'how much do I have, is it up or down today, and vs what I paid in' (Robinhood's home screen is a single portfolio graph for exactly this glance; a survey in a UX case study found 95.2% of users interact with it primarily on their phone for quick checks); (2) understand WHY the number moved without doing their own research — Wealthsimple's whole product research program targets users' goals, motivations, habits and emotions, and financial-dashboard best practice (Eleken) says a dashboard must answer 'what is happening, why is it happening, what needs attention'; (3) decide a next action with confidence — buy/hold/sell, set an alert, or consciously do nothing — without feeling manipulated; (4) feel safe: balances stay private in public, funds are secure, nothing looks like a scam; (5) build a low-effort habit — automated savings challenges and chatty check-ins (Cleo), recurring commodity buys at live prices (Revolut's Commodities section), and daily net-worth refreshes (Empower users revolted on Reddit when daily updates were removed, proving the habit mattered).

**top_questions**: In user language: 'How much is my portfolio worth right now, and did it go up or down today?'; 'Why did it drop — is it me or the market?' (a one-sentence cause, news or macro, not a lecture); 'Am I actually in profit or loss overall compared to what I put in?'; 'Should I buy more, hold, or sell?' (framed as scenarios with trade-offs, not commands); 'Is now a good time to buy?'; 'What fees or spread am I actually paying?' (e.g., r/Revolut threads debate whether buying gold through the app is 'a good idea' — cost transparency is the underlying question); 'Can I trust this AI/app with my money and my data?'; 'What changed since I last opened the app?'

**decision_drivers**: What actually drives continued use and buy/hold/sell decisions: clear total-return-vs-cost numbers rather than a bare today price; trust in data provenance — live market prices, named sources, timestamps (Revolut positions its commodities trading as 'based on live market performance'); perceived control (undo/override, no forced action); fee and spread transparency before committing money; speed and number of taps to act; emotional tone — encouraging and never shaming (Cleo's humor works because users opted into the personality); habit hooks such as price alerts, thresholds and recurring buys; and credibility signals (App Store Editor's Choice / Apple Design Award finalist for Copilot Money, licenses, media coverage) that reduce adoption anxiety for first-time investors.

### pains

**trust_barriers**: Black-box AI is the biggest one: only 46% of people globally say they trust AI systems, dropping to 39% in high-income countries, and about three quarters of companies believe lack of transparency drives churn (Parallel, citing the AI Index and a Zendesk survey); unexplained or unverifiable predictions; fear of scams — especially for older or less digitally confident users; hidden fees and spreads; gamified nudges that create over-trading pressure (the confetti episode is the canonical cautionary tale); no ability to undo, override, or challenge an automated recommendation; and missing data lineage — trust research consistently says users want 'why this recommendation' links and cited sources so outputs feel grounded (Parallel; ScreamingBox: connect inputs, reasoning and outcomes into a transparent narrative).

### ux

**must_have_first_screen**: A single dominant 'answer card', with drill-down below the fold. The benchmark pattern: Robinhood leads with one portfolio value + graph; Empower leads with net worth; Copilot Money leads with an elegant cash-flow chart ('elegant graphs, a crystal-clear interface'); Cleo leads with a short conversational summary instead of a chart. For Gold Assistant the first screen must show, within one glance and no scrolling: portfolio value in THB, today's change and total P/L vs average cost with a color-blind-safe +/- indicator, a sparkline for trend context, ONE plain-Thai sentence from the agent team on why the portfolio is losing ('ลงเพราะดอลลาร์แข็ง ไม่ใช่ความผิดพอร์ตคุณ' style), a visible entry point to ask the cat agents, and a privacy/blur toggle. Keep it to ~5 KPI cards maximum before progressive disclosure (Eleken best practice).

**language_and_tone**: Plain language over jargon, and translation of statistics into familiar concepts — ScreamingBox's example: explain a forecast with 'seasonal trends or historical patterns rather than statistical terminology'. Use verdict-first sentences ('Your gold is down 3% this week because...') followed by expandable 'why this recommendation' links or tooltips (Parallel). Numbers must be consistently formatted with explicit currency, +/- signs and dates (Eleken). Personality builds engagement — Cleo's humor and even 'roast mode' attract younger users — but in a losing-portfolio context the tone must be supportive coach, never mocking; self-deprecating banter about overspending does not transfer to 'your savings are shrinking'. Keep one idea per line; short paragraphs; UI labels in everyday Thai, not finance English loanwords where a simpler Thai term exists. (The example Thai string in must_have_first_screen is illustrative; all analytical values here are English.)

**accessibility_notes**: Touch targets of at least 44x44pt (Apple HIG standard, used as the explicit fix in the Robinhood case study); never encode gain/loss in red/green alone — pair color with up/down arrows and explicit +/- signs for color-blind users; large default body text (16-18pt+) and generous line-height for older users; one-hand reachability for primary actions at the bottom of the screen; a blur/privacy mode for balances in public; icons always paired with text labels so meaning is never color- or icon-only.

### design

**implications_for_gold_assistant**: 1) First screen = answer card: ฿ portfolio value, today's change, total P/L vs average cost, sparkline, and one plain-Thai 'why' sentence attributed to the agent consensus — users should get the Robinhood-style glance answer without scrolling. 2) Give each of the 5 cat agents exactly one <=15-word takeaway chip on the first screen (News: 'Fed พูดแข็ง กดทอง'; Macro: 'ดอกเบี้ยสูง ทองไม่มีดอกเบี้ย'; Quant: 'แนวรับที่ X'; Risk: 'พอร์ตรวมทองเกิน 30%'; Lead: สรุปปิดท้าย), each with a tiny cited-source icon (headline name, indicator, timestamp); tapping a cat opens its full reasoning trail — the knowledge-graph made progressive, matching Parallel's 'make AI visible + why-this-recommendation links' and ScreamingBox's 'inputs, reasoning, outcomes narrative'. 3) Adopt a Cleo-style Thai chat entry ('ถามแมว') that accepts casual Thai phrasing, answers in <=3 sentences, and always appends source chips; keep the personality warm but drop any roast-style mockery — the user is already losing money. 4) Apply Eleken's rules: max ~5 KPI cards, show trends not static numbers, visually flag anomalies (sudden drops) with icon+color+label, and keep บาท/%/date formats identical everywhere. 5) Always surface a 'what changed since yesterday' feed so users build habits on stable anchors — and never silently remove or rename existing metrics in updates (Empower backlash). 6) Every AI diagnosis must carry data provenance: price source and timestamp (e.g., 96.5% gold bar board price, FX rate), a confidence level, and an honest limitation line ('AI อาจผิดพลาด — ตรวจสอบก่อนตัดสินใจ'); transparency research shows honesty about limitations increases credibility. 7) Give users control: allow dismissing/flagging an agent's conclusion as unhelpful, adjusting the risk profile, and re-running the diagnosis; track override rates internally to monitor trust calibration (Parallel). 8) Accessibility baseline: 44pt+ tap targets for time-frame chips and cat cards, arrows+signs alongside color for P/L, 16-18pt+ Thai body text, bottom-sheet one-hand flows, and a balance-blur privacy toggle. 9) Explain one jargon term at a time, inline and contextual: the first time 'กำไร/ขาดทุนที่ยังไม่ขาย (unrealized)' appears, attach a one-tap plain-Thai definition. 10) Before any buy/sell suggestion, show the gold-specific cost truth — buy/sell spread, premium over spot, and fees — so the 'is it a good idea' question (the exact r/Revolut debate) is answered inside the product.

**antipatterns_to_avoid**: 1) Gamified celebration of trades (confetti and similar) — removed by Robinhood under regulatory scrutiny; in a loss-context app it reads as mocking. 2) Dark patterns: hiding fees/spread, pre-checked recurring buys, artificial urgency. 3) Wall-of-metrics dashboards with no hierarchy — 'too many metrics, unclear structure' is the #1 dashboard failure (Eleken). 4) Black-box AI verdicts with no sources, confidence, or reasoning trail. 5) Shaming or alarmist tone about losses (roast-mode humor applied to a shrinking portfolio). 6) Silently removing or renaming familiar numbers/updates in redesigns (Empower's 'new UI is awful' backlash). 7) Tiny tap targets on high-frequency controls like time-frame switchers. 8) Red/green as the only gain/loss signal. 9) Static numbers with no trend or comparison context. 10) Generic advice not tied to the user's actual holdings and costs ('gold is volatile' without 'your average cost is X, you need Y to break even').

### evidence

**sources**: 1) '4 ways to improve Robinhood — a UX case study' (Dan Wall, UX Collective) — https://uxdesign.cc/4-ways-to-improve-robinhood-ux-case-study-38c21774238e [fetched; guerrilla test n=7 + survey n=22: tap targets, privacy, portfolio detail, 95.2% mobile]. 2) 'Cleo Budgeting App Review: Features, Costs & Alternatives' (Kudos, 2025) — https://www.joinkudos.com/blog/cleo-budgeting-app-review-your-ai-financial-assistant-in-2025 [fetched: AI chatbot personality, roast mode, pros/cons, limited investment integration]. 3) '12 Financial Dashboard Examples, Templates + Best Practices' (Eleken, updated 2026) — https://www.eleken.co/blog-posts/financial-dashboard-examples [fetched: KPI hierarchy, trends-not-numbers, limit metrics, anomalies, consistent formatting, design-for-decisions, simplicity-with-drill-down]. 4) 'Explainable AI and the UX of Trust' (ScreamingBox, May 2026) — https://screamingdev.com/blog/explainable-ai-and-the-ux-of-trust-designing-transparency-that-drives-adoption [fetched: mental models, layered explanations, dashboard storytelling]. 5) 'Designing for AI Trust: 2026 Transparency Best Practices' (Parallel, Robin Dhanwani) — https://www.parallelhq.com/blog/designing-ai-transparency-trust [fetched: trust stats 46%/39%, why-this-recommendation links, make AI visible, limitations honesty, cite sources, override/undo, auditability, dark-pattern avoidance]. 6) 'Wealthsimple Case Study' (Brazen) — https://www.brazen.io/our-work/wealthsimple [fetched: persona research into goals/motivations/habits/emotions; simple-affordable-accessible-personalized mission]. 7) 'How Copilot Money developed an interest in Swift Charts' (Apple Developer Stories) — https://developer.apple.com/articles/copilot-money [fetched: elegant graphs, crystal-clear interface, accurate ML categorization, Cash Flow feature, Apple Design Award finalist]. 8) 'Revolut lets you purchase gold on Premium and Metal' (FF News, Mar 2020) — https://ffnews.com/newsarticle/revolut-lets-you-purchase-gold-on-premium-and-metal [fetched: Commodities section, live market performance, tier-gated]. 9) 'Robinhood gets rid of confetti feature amid scrutiny over gamification' (CNBC, Mar 31 2021) — https://www.cnbc.com/2021/03/31/robinhood-gets-rid-of-confetti-feature-amid-scrutiny-over-gamification.html [headline-level; corroborated by WSJ/Reuters/AP headlines in search results]. 10) "Robinhood's UI led to a suicide and a $70M fine" (UX Woman, Substack) — https://uxdesigncourses.substack.com/p/ux-challenge-15-robinhoods-ui-led [headline-level evidence of UI-harm criticism]. 11) 'On Confetti Regulation: The Wrong Way to Regulate Gamified Investing' (Yale Law Journal) — https://yalelawjournal.org/essay/on-confetti-regulation-the-wrong-way-to-regulate-gamified-investing [search-result-level]. 12) 'New UI is awful - no more daily updates' (r/PersonalCapital) — https://www.reddit.com/r/PersonalCapital/comments/1ohwv4d/new_ui_is_awful_no_more_daily_updates [headline-level community evidence; thread body not fetchable]. 13) 'Buying gold with rev app a good idea?' (r/Revolut) — https://www.reddit.com/r/Revolut/comments/1bh4bf5/buying_gold_with_rev_app_a_good_idea [headline-level; cost-trust question]. 14) 'Robinhood | Product design case study' (MetaLab) — https://www.metalab.com/work/robinhood [search-result-level, not fetched].

**confidence**: medium — findings are triangulated from one primary usability study (Robinhood case study with n=7+n=22), three design-practice guides, four product reviews/press articles, and headline-level community complaints; latest-version in-app teardowns and Thai-user validation were not possible in this pass.

---

## 2. Benchmark: Thai gold apps (YLindo, Kaiy/Gahtong, GT Goldtrend, GOLD NOW by Hua Seng Heng, V-GO Online by MTS, KKP Dime gold)

*Fields marked uncertain: top_questions, top_pains, confusion_points, trust_barriers, workflow_preferences, implications_for_gold_assistant, antipatterns_to_avoid*

### basic_info

**item_name**: Benchmark: Thai gold apps (YLindo, Kaiy/Gahtong, GT Goldtrend, GOLD NOW by Hua Seng Heng, V-GO Online by MTS, KKP Dime gold)

**one_liner**: A six-app benchmark of how Thai retail gold apps serve price-watching, online gold trading and micro gold saving, extracting what users praise and complain about (verified ratings + feature sets, plus review-level signals) to define the UX bar for the Gold Assistant Thai-language AI dashboard.

### needs

**jobs_to_be_done**: Thai gold app users are fundamentally trying to: (1) know the live 96.5% gold board price (ราคาทองคำแท่ง รับซื้อ/ขายออก) in THB per บาททองคำ at a glance, since that number is the national reference every gold buyer anchors to; (2) buy and sell gold online in real time without traveling to a gold shop — GOLD NOW advertises 'ซื้อขายทองคำแบบไม่วางหลักประกา สะดวก รวดเร็ว ทุกที่ ทุกเวลา' (verified App Store description) and supports automatic target-price orders so users 'ไม่ต้องเฝ้ากราฟ' (don't have to watch the chart); (3) accumulate gold in small amounts as savings — Dime! markets 'Finance for All' with no-minimum accounts and gold alongside savings/stocks (verified), GOLD NOW has a 'Gold Saving' feature (verified); (4) profit from intraday and overnight volatility (Thai gold reacts to US session moves at night, a core reason for real-time apps); (5) understand why gold moved — USD strength, Fed/rates, FX; HSH even launched a separate USD-denominated product (USD Gold Trade, verified: 'ลดความเสี่ยงจากแรงกดดันความผันผวนของค่าเงินบาท') proving users care about the baht-FX drag on gold returns; (6) eventually convert digital gold to physical baht bars/coins — GOLD NOW allows redemption at any Hua Seng Heng branch and USD Gold Trade allows withdrawal as 99.99% coins (verified); (7) for signal/analysis app users (GT Goldtrend-type), get direction and entry/exit levels without doing their own technical analysis [uncertain for Goldtrend specifics].

**decision_drivers**: What drives adoption and buy/hold/sell: (1) trust in the brand behind the app — Hua Seng Heng is a decades-old household gold shop and KKP is a licensed bank, which explains GOLD NOW's exceptional 4.83/5 average across 72,004 THB App Store ratings (verified) versus Dime!'s far weaker 3.94/5 across 4,022 (verified); (2) price accuracy and speed vs the shop board — the app must match the 96.5% board price users see elsewhere; (3) ability to redeem physical gold at a real branch (GOLD NOW's explicit selling point, verified); (4) low entry amounts and no minimums (Dime!, verified: 'No minimum', US stocks from 50 THB); (5) spread/fee transparency and total P/L vs own cost; (6) execution reliability exactly during volatile windows — users decide to stay with the app that does not freeze when the market moves; (7) automation convenience — GOLD NOW's automatic target-price buy/sell orders (verified) remove the need to watch charts all day; (8) funding friction — linking bank accounts/mobile banking (GOLD NOW, USD Gold Trade via FCD account, both verified) instead of document-heavy onboarding ('สมัครง่าย ไม่ใช้เอกสาร', verified); (9) for analysis apps, perceived signal accuracy and analyst credibility [uncertain — Goldtrend subscription value could not be verified].

### pains

### ux

**must_have_first_screen**: A Thai-gold-native answer card, in one glance, no scrolling: (a) the live 96.5% baht-gold board price with รับซื้อ/ขายออก (buy/sell) clearly labeled and a timestamp + named source (e.g., Hua Seng Heng board / FX rate) — the GOLD NOW pattern that earned 4.83/5 (verified); (b) user's portfolio value in THB with today's change and total P/L vs average cost, color + arrow + sign (not color alone); (c) a one-line plain-Thai 'why it moved' from the agent team, including the FX explanation when baht drag is the cause ('ทองโลกขึ้น แต่ค่าเงินบาทแข็ง กดพอร์ตทองไทย'); (d) the 5 cat agents' one-line consensus chips with tap-through reasoning; (e) a fast entry to buy/sell/hold scenarios and to price alerts. Everything else (charts, news, community, settings) sits below the fold. A 'what changed since I last opened the app' strip covers the overnight US-session gap that no benchmark app currently summarizes well.

**language_and_tone**: Everyday Thai that mirrors how gold shops and Facebook gold communities actually talk: ทองคำแท่ง, รับซื้อ/ขายออก, บาททองคำ, ทอง 96.5 — not translated finance jargon like 'commodities' or 'spot price' without a Thai gloss; short verdict-first sentences ('ทองลง 50 บาท เพราะดอลลาร์แข็งหลังประกาศ FOMC') followed by an expandable why; numbers always with unit and direction (฿, บาททองคำ, +/-, arrows); a supportive coach tone — users checking gold apps are often anxious about money, so no hype, no get-rich promises, no shame; disclose AI limits honestly ('AI วิเคราะห์จากข้อมูล ไม่ใช่คำแนะนำการลงทุน — ตรวจสอบก่อนตัดสินใจ'); keep text minimal per screen since the benchmark's best-rated app communicates through numbers and features, not paragraphs.

**accessibility_notes**: Older users (40–60+) are a large share of Thai gold buyers, so: large, high-contrast numerals for the price board; gain/loss encoded with color + arrow + sign (never red/green alone); 16–18pt+ Thai body text with generous line-height; 44pt+ tap targets for time-frame chips and buy/sell buttons; bottom-of-screen placement for primary actions for one-hand use; biometric login (fingerprint) as the reassurance pattern GOLD NOW advertises (verified); a balance-blur privacy toggle for checking gold in public; icons always paired with Thai text labels.

### design

### evidence

**sources**: 1) iTunes/App Store Search API, TH storefront, term 'ทอง' — https://itunes.apple.com/search?term=%E0%B8%97%E0%B8%AD%E0%B8%87&country=th&entity=software&limit=60 [fetched; yielded app records used below]. 2) iTunes/App Store Search API, TH storefront, term 'gold' — https://itunes.apple.com/search?term=gold&country=th&entity=software&limit=60 [fetched]. 3) 'GOLD NOW by HUA SENG HENG' App Store record — https://apps.apple.com/th/app/gold-now-by-hua-seng-heng/id1577898799 [fetched via API: 4.83/5 avg, 72,004 ratings; features verified: real-time trading, automatic target-price orders, no-document signup, fingerprint login, bank linking, Gold Saving, physical redemption at HSH branches]. 4) 'Dime! เงินฝาก หุ้น กองทุน ทอง' App Store record — https://apps.apple.com/th/app/id1612798502 [fetched via API: 3.94/5 avg, 4,022 ratings; verified: KKP-backed, no-minimum savings, US stocks from 50 THB, gold in title/positioning]. 5) 'USD Gold Trade by HuaSengHeng' App Store record — https://apps.apple.com/th/app/usd-gold-trade-by-huasengheng/id6470643040 [fetched via API: 4.79/5 avg, 1,809 ratings; verified: 99.99% gold in USD, FCD account requirement, 0.1 troy oz start, baht-volatility hedging positioning, physical coin withdrawal]. 6) Domain knowledge of Thai gold app landscape (YLindo, Kaiy/Gahtong, GT Goldtrend, V-GO Online/MTS) — NOT verifiable this session: web search engines (DuckDuckGo HTML/lite, Bing) returned no usable results (blocked/empty responses), and these apps did not surface in the two iTunes API result sets; all app-specific claims for them are marked [uncertain].

**confidence**: low-medium — ratings, feature claims and market positioning for Hua Seng Heng (GOLD NOW, USD Gold Trade) and KKP Dime! are verified from the App Store API (strong, current data), but review-content evidence (what users actually praise/complain in text) and anything about YLindo, Kaiy/Gahtong, GT Goldtrend or V-GO Online could not be fetched because search engines were blocked this session; those portions rest on domain knowledge and are explicitly flagged [uncertain].

---

## 3. Pattern: AI assistant transparency and trust UX

*Fields marked uncertain: ux.language_and_tone*

### basic_info

**item_name**: Pattern: AI assistant transparency and trust UX

**one_liner**: How consumer AI analysis products earn CALIBRATED (not blind) trust: show each agent's reasoning, tool calls and cited evidence visibly, answer first and evidence second, label uncertainty honestly, and tie displayed trust to measured per-domain track records instead of usage-based scores.

### needs

**jobs_to_be_done**: When an AI system analyzes their money, users' core jobs are: (1) UNDERSTAND - get a plain-language diagnosis of why the portfolio is losing, not just a verdict; (2) VERIFY - check AI claims against real, inspectable evidence (news items, prices, calculations) without redoing the whole analysis themselves; (3) CALIBRATE - learn where the AI is reliable vs. weak, per domain and over time, so they know when to rely and when to double-check (research shows people engage with an explanation only when scrutinizing it is EASIER than doing the task alone - Stanford HAI maze experiments); (4) STAY IN CONTROL - see what agents are doing, and be able to approve, correct, dismiss or defer; (5) DECIDE - convert the analysis into an actionable, risk-labeled next step (hold / trim / hedge / do nothing) they can defend to themselves.

**top_questions**: 'Why exactly is my portfolio losing money right now - in one sentence?' 'Which agent said this, and what evidence did it use?' 'Can I see the original news / price / source myself?' 'How confident are you, and what would change your conclusion?' 'What did you just do while I was waiting?' 'Have calls like this been right before?' 'What are the risks of the suggested action, and what alternatives did you consider?' 'What happens if I do nothing?' 'Who is talking now, and why did another agent take over?'

**decision_drivers**: Continued use is driven by: verified accuracy of past calls (a track record users can check); perceived evidence quality (cited, clickable sources vs. vague claims); cost of verification (hover-preview of the exact quote beats digging through documents); honest uncertainty handling (admits unknowns, scopes low-confidence claims); sense of control (can approve / modify / reject); and stakes-aware presentation - with money on the line, users pick verifiability over persuasiveness. Trust builds slowly and breaks quickly: one unexplained wrong 'confident' call or one fabricated-looking source costs more trust than ten good calls build.

### pains

**top_pains**: (1) OVER-TRUST: AI overreliance - people accept AI recommendations even when wrong; classic XAI explanations often FAIL to reduce overreliance when the explanation is as complex as the task itself (Stanford HAI). (2) UNDER-TRUST: when transparency is absent or past errors were hidden, users micromanage every step or abandon the product. (3) Walls of unverifiable text and jargon that users skim, then blindly accept - worse than no explanation. (4) Theatrics: fake progress bars, fabricated confidence numbers, 'vanity trust levels' that rise with usage instead of accuracy (aiuxdesign.guide calls this a calibration lie). (5) Sycophancy: AI advice that overly affirms what the user already hopes (Stanford News, 2026) - especially damaging in a loss situation where users want reassurance. (6) Black-box multi-agent graphs: pretty node-and-edge visuals with no narrative of who concluded what from what.

**confusion_points**: Finance jargon (DXY, drawdown, volatility, realized vs. unrealized P/L); unexplained handoffs between 5 agents ('who is analyzing now and why?'); bare confidence percentages with no referent ('70% of what?'); engineer-grade tool-call logs; knowledge-graph visualizations with too many nodes/edges and no summary sentence; multiple agents disagreeing with no visible synthesis or tie-breaking rule; Thai users additionally face English finance terms and English-only UI copy.

**trust_barriers**: Black-box feel (no visible reasoning path from data to conclusion); missing, vague or dead citations, or hidden 'source unavailable' gaps; hallucinated or unverifiable sources; no track record of the AI's past advice; a wrong confident prediction with no follow-up or repair; fear of scams - strong among Thai retail users - amplified by marketing language, urgency tricks or anything that smells like a pump; unclear data provenance (which news outlet, which exchange, how fresh the data is).

### ux

**must_have_first_screen**: Answer-first, evidence-second. In the first 5 seconds: (1) a plain-Thai one-sentence diagnosis of why the portfolio is losing (main driver + direction + rough magnitude); (2) the 2-3 key drivers as concrete numbers with a visible uncertainty label; (3) one-line 'what would change this conclusion'; (4) evidence chips on each claim (one tap to the source); (5) a quiet, non-theatrical agent status line (which cat agent is doing what, real steps). NOT first: a large agent graph, agent avatars animating, a wall of logs, or a verdict without reasons.

**workflow_preferences**: Progressive disclosure in 3 layers: L1 conclusion (one screen, no jargon) -> L2 key evidence per claim (citation chips with hover/press preview quoting the exact passage) -> L3 full per-agent reasoning trace and tool-call log for power users. Multi-agent activity rendered as an inspectable timeline/ledger ('News Analyst fetched 12 items -> Risk Analyst flagged 2 conflicts') rather than a modal users must watch. High-stakes suggestions arrive as a decision card: What / Why / Risk / Alternatives + Approve / Modify / Reject / Defer. Group minor updates, interrupt only for genuinely high-stakes items ('never cry wolf'). Single page with anchored sections, mobile-first, deep links from every claim to its evidence.

**language_and_tone**: Plain Thai at roughly an 8th-grade reading level (Microsoft HAX explicitly targets 8th-grade clarity); short sentences; consistent cat-agent names and fixed roles; numbers formatted with sign, baht and comparison ('+3.2% vs last week', '-8% vs your average cost'); every technical term glossed in one line on first use; confidence expressed as words + reason ('low confidence: the news contradicts itself') rather than bare percentages; the system must be allowed to say 'I don't know / the data is not enough'. No hedging walls, no marketing adjectives, no blame-the-user phrasing. [uncertain - Thai-specific reading-grade norms and preferred Thai finance vocabulary were not directly verified in this item; confirm with Thai user interviews]

**accessibility_notes**: Body text >=16-18px for older shop customers; color-blind-safe gain/loss: pair green/red with arrows or +/- signs and position so color is never the only signal (Thai convention: green = up, red = down); text alternatives for agent states (screen-reader label: 'Risk Analyst: finished, 2 warnings'); touch targets >=44px and one-hand mobile use; a reduce-motion option for agent animations; visible keyboard focus on evidence chips and graph nodes.

### design

**implications_for_gold_assistant**: Ten concrete recommendations for showing the 5 cat agents with calibrated trust: 1) ANSWER FIRST: open the page with the Lead Researcher's plain-Thai conclusion (why losing: driver + magnitude); evidence and agents below - never a graph or agent theater first. 2) PER-CLAIM CITATION CHIPS from each agent (headline+date, price series point, Fed/DXY data) with hover/press preview quoting the exact passage; deep-link to source; show broken/missing sources explicitly instead of hiding the gap (Shape of AI citations pattern). 3) MAKE EXPLANATIONS SIMPLER THAN THE TASK (Stanford HAI): instead of turn-by-turn reasoning text, highlight ON THE USER'S OWN CHART the moments that drove the diagnosis (buy date vs. price peak, the news-event marker) - verification by looking, not by reading logic. 4) UNCERTAINTY LABELS on every agent output: word + reason + 'what would change this'; low-confidence claims use scoped language and quieter visual weight; never show a bare 0-100% score without meaning. 5) PER-AGENT, PER-DOMAIN TRACK RECORD card: each cat keeps a small visible scorecard ('News-based calls: 6/10 right in the last 90 days') so trust tracks measured competence, not usage; update it after outcomes; show misses as well as hits (trust-calibration pattern). 6) VISIBLE HANDOFFS in the knowledge graph: tapping an edge shows 'News Analyst passed these 3 items to Risk Analyst because...'; the graph must be explorable FROM a narrative summary, not instead of one (multi-agent coordination UX). 7) AUTONOMY TIERS per action (Silent / Notify / Confirm / Escalate) published in an 'Agent Permissions' panel; portfolio-affecting suggestions default to Confirm/Escalate with a decision card (What/Why/Risk/Alternatives + Approve/Modify/Reject/Defer); irreversible actions are never silent (multi-agent autonomy-tier pattern). 8) HONEST PROGRESS: replace fake progress theatrics with a short real activity ledger of tool calls ('fetching SET news... 12 items... done') that can be collapsed; never invent steps, delays or confidence numbers. 9) SHOW DISAGREEMENT: let the Risk Analyst visibly dissent from Quant/Lead with a one-line 'dissent' chip - visible disagreement signals honesty and guards against sycophantic single-voice advice. 10) TRUST REPAIR FLOW: when a past AI call turns out wrong, surface it proactively in context ('our Oct 3 call was wrong because...'), explain what changed, and temporarily raise oversight prompts (trust builds slowly and breaks fast - repair must be proactive).

**antipatterns_to_avoid**: Fake progress bars or staged 'thinking' animations unrelated to real work; vanity trust/confidence scores that rise with usage instead of measured accuracy; one confident omniscient voice that never disagrees (sycophancy); a black-box agent graph with no narrative summary; wall-of-text explanations as complex as the underlying task; citation spam linking broad documents instead of exact passages; hiding broken sources or empty states behind filler; hiding all reasoning behind a chat bubble ('chat is not a transparency strategy'); jargon without gloss; urgency or social-pressure tricks ('experts are selling now!') that mimic the scam patterns Thai users fear.

### evidence

**sources**: Fully fetched & read: (1) 'AI Overreliance Is a Problem. Are Explanations a Solution?' - Stanford HAI - https://hai.stanford.edu/news/ai-overreliance-problem-are-explanations-solution ; (2) 'Guidelines for Human-AI Interaction' (18 guidelines, 4 phases: initially / during / when wrong / over time) - Microsoft Research - https://www.microsoft.com/en-us/research/project/guidelines-for-human-ai-interaction/ and HAX Toolkit https://www.microsoft.com/en-us/haxtoolkit/ai-guidelines/ ; (3) HAX guidelines summary 'Microsoft HAI guidelines (HAX)' - AI Nerd Network - https://www.ainerdnetwork.com/learn/microsoft-hai-guidelines ; (4) 'UI/UX & Human-AI Interaction patterns' (multi-agent coordination, progressive disclosure, trust & transparency) - Agentic Design Guide - https://agentic-design.ai/patterns/ui-ux-patterns ; (5) 'Trust Calibration in AI - Meaning + UX Patterns for Appropriate Trust' - AI Design Patterns (aiuxdesign.guide) - https://www.aiuxdesign.guide/patterns/trust-calibration ; (6) 'AI UX Patterns | Citations' - Shape of AI - https://www.shapeof.ai/patterns/citations ; (7) 'Agentic AI and Multi-Agent UX Design Patterns' (autonomy tiers, decision cards, escalation design) - https://github.com/phazurlabs/ux-ui-mastery/blob/main/skills/agentic-ai-generative-ux/references/agentic-multi-agent-patterns.md . Consulted via search results only (titles/snippets, not fully read): CFI 'Explainable AI: Meaning and Why It Matters in Finance'; JIDMIS 'Explainable AI and Consumer Trust in Financial Services'; ScienceDirect (Computers in Human Behavior) 'Trust and reliance on AI - An experimental study on the extent and nature of overreliance'; Stanford News 'AI overly affirms users asking for personal advice' (2026); arXiv 'The Trust Calibration Maturity Model'; UXperiment 'Explainable AI UX: Design Patterns for Trust'; SAP Design System 'Explainable AI (XAI) - Building Explanations'. 10+ web searches run across: explainable AI in finance, agent transparency patterns, trust calibration / overreliance, multi-agent UI patterns, citation & evidence UI, progressive disclosure, Microsoft HAX.

**confidence**: medium - converging support from experimental research (Stanford overreliance experiments), validated industry guideline sets (Microsoft HAX, CHI 2019) and current agentic-UX pattern libraries (2024-2026); weaker on Thai-language specifics and on directly observed Thai gold-investor behavior, which this pattern item did not test with real users.

---

## 4. Pattern: Portfolio dashboard UX best practices

*Fields marked uncertain: sources, language_and_tone*

### basic_info

**item_name**: Pattern: Portfolio dashboard UX best practices

**one_liner**: Proven dashboard patterns for retail investors: answer the four first-screen questions (what is it worth, am I up or down, what changed, what should I do) in under 5 seconds, then progressively disclose detail; plain language with tap-to-explain jargon, color-blind-safe gain/loss encoding, mobile-first card layouts, and honest empty/loading/error states.

### needs

**jobs_to_be_done**: (1) CHECK STATUS in seconds: 'how much is my gold portfolio worth right now, and am I up or down overall?'; (2) EXPLAIN CHANGE: 'what moved since my last visit - market price, news, or my own transactions?'; (3) DECIDE: convert status into a risk-labeled next step (buy / hold / sell / DCA / do nothing) they can act on or ignore; (4) MONITOR passively with low cognitive load - a glance, not a work session; (5) VERIFY & CONTROL: confirm numbers match what their gold shop / broker / exchange shows, and check their own history; (6) LEARN: gradually understand why gold moves so the dashboard makes them smarter, not dependent.

**top_questions**: 'How much is my portfolio worth today?' 'Am I up or down - overall and on each position - in baht and in percent?' 'Why did it change since yesterday? What happened in the market?' 'Should I buy more, hold, or sell now?' 'How does today compare with my average cost and with last week?' 'What fees/spread am I actually paying?' 'Is this today's price - how fresh is the data?' 'What do the AI analysts say I should do, in one line?'

**decision_drivers**: Glanceability (answer visible without scrolling or tapping); price accuracy and freshness (timestamped, matching the shop/broker number they can cross-check); comparison anchors (change vs. yesterday, vs. average cost, vs. last week); clarity of the recommended next step including permission to do nothing; perceived effort (how long until I understand today's situation); fee/spread transparency; sense of control (I can drill down or dismiss); emotional framing (calm, not panic-inducing on red days).

### pains

**top_pains**: (1) Information overload: widget soup of charts and KPIs where the answer to 'am I up or down?' takes hunting; (2) key numbers below the fold or behind taps - value and P/L must be top-left and big; (3) P/L shown only as percent OR only as baht (retail users want both); (4) numbers without a comparison ('2,340' - compared to what?); (5) stale prices with no visible timestamp; (6) jargon-dense labels and legends; (7) desktop-first dense tables that are unusable on a phone (where most retail users check); (8) anxiety framing: solid red screens and loss-only emphasis with no context ('gold is long-term volatile'); (9) empty or error screens that look like the app is broken; (10) dashboards that answer marketing questions ('features!') instead of the user's four first-screen questions.

**confusion_points**: Realized vs. unrealized P/L; bid/ask spread and shop buy-back vs. sell price (Thai: รับซื้อ/ขายออก, ค่าแรง); spot price vs. Thai retail gold-bar/ornament price (they differ - users think one of them is 'wrong'); USD/gold linkage (DXY, Fed) without explanation; volatility and drawdown; chart timeframes and candlesticks; percentage vs. baht sign conventions; basis points; why the AI recommendation changed since morning.

**trust_barriers**: Numbers that do not match what the gold shop counter or broker app shows (top credibility killer); prices without a visible timestamp or source; black-box AI advice with no one-line 'why'; hidden fees/spreads discovered later; marketing hype or urgency banners; no track record of past AI calls; data that looks fabricated or demo-like; app errors during market hours.

### ux

**must_have_first_screen**: Visible in the first 5 seconds, no scroll: (1) total portfolio value in large type (largest number on screen); (2) day change directly adjacent as signed pair: '+฿1,240 (+2.1%) today' with color + arrow + sign (never color alone); (3) top 2-3 movers / what changed since last visit as one-line chips; (4) one clear suggested next action card - or explicitly 'no action needed today'; (5) price freshness timestamp ('ราคา ณ 14:05 น.'); (6) navigation to detail tabs (Holdings, AI Analysts, History). NOT first: marketing banner, dense chart grid, agent avatars, login walls, news feed.

**workflow_preferences**: Mobile-first portrait cards, one question per card; tab/bottom-nav grouping (Overview / My holdings / AI advice / History) so depth is a tap away but the overview stays clean; progressive disclosure L1 summary -> L2 per-position or per-analyst detail -> L3 raw data and logs; tap a chart point to get an inline explanation, not a separate page; pull-to-refresh with visible last-updated; push notifications only for big moves or completed AI analyses; skeletons during load; most sessions are 30-90 seconds on a phone, so state must persist and the answer must survive an interruption.

**accessibility_notes**: WCAG 1.4.1 Use of Color (verified): color must never be the only signal for gain/loss - always pair with +/- sign, ▲▼ arrow, or text label; keep >=4.5:1 contrast for text; color-blind-safe default: use the Thai/global convention green=up / red=down but choose deuteranopia/protanopia-distinguishable shades (darker green / deeper red with blue tint) and add arrows so it degrades gracefully; body text >=16sp with Thai-friendly line height (Thai diacritics need taller lines); touch targets >=44-48px; primary actions in one-hand thumb reach (bottom of screen); support OS font scaling; reduce-motion option; charts need text summaries for screen readers.

### design

**implications_for_gold_assistant**: Ten concrete recommendations: 1) FIRST-SCREEN CONTENT ORDER: (a) total portfolio value, biggest type on screen; (b) day change as signed pair '+฿1,240 (+2.1%)' with green/red + arrow; (c) 2-3 'what changed' one-line chips from the cat analysts; (d) one suggested-action card or 'no action needed today'; (e) price timestamp; (f) bottom tab bar - nothing else above the fold. 2) DUAL P/L: always show baht AND percent, always next to average cost ('กำไร +฿3,200 (+8.4%) จากต้นทุนเฉลี่ย ฿31,500'); never one without the other. 3) TAP-TO-EXPLAIN JARGON: dotted-underline Thai terms (spot price, spread, DXY, realized/unrealized) open a 1-2 line plain-Thai gloss sheet on tap, with a link to a 60-second explainer; glosses written once, reused everywhere. 4) COLOR-BLIND-SAFE GAIN/LOSS: green=up/red=down PLUS mandatory ▲/▼ arrows and +/- signs on every number and chart; pick darker/deeper shades distinguishable under deuteranopia and protanopia; add pattern or label text on chart segments; verify with a CVD simulator before ship. 5) TAB GROUPING: bottom nav หน้าแรก (Overview) / พอร์ตของฉัน (Holdings) / นักวิเคราะห์ AI (5 cats) / ประวัติ (History) / ตั้งค่า; overview answers the 4 questions, everything else is drill-down. 6) MOBILE PATTERNS: one question per card, 48px targets, thumb-zone primary actions, pull-to-refresh, skeleton loaders shaped like the real layout, sticky timestamp on price widgets; desktop is the secondary layout that mirrors the same order. 7) PROGRESSIVE DISCLOSURE: L1 first-screen summary -> L2 per-position detail + per-cat analyst one-liners -> L3 full agent reasoning and raw data; each L1 number deep-links to its L2 card. 8) EMPTY STATES: new user sees a worked sample portfolio clearly labeled 'ตัวอย่าง' plus a 3-step onboarding ('เพิ่มไม้ทองแรกของคุณ'); never a blank screen; every empty state says what will appear here and offers the next action. 9) LOADING/ERROR: skeleton screens (never bare spinners) with 'อัปเดตล่าสุด ...' timestamp; on price-feed failure show last known price grayed out with 'ราคาล่าช้า - อาจไม่ตรงกับร้าน' + retry button; never hide errors behind old data. 10) NUMBER FORMATTING: Thai locale ฿ symbol, thousands separators, 2 decimals for baht / 1 for percent, explicit +/− signs on all changes, no scientific notation, consistent across every screen; freshness line on every price ('ราคา ณ 14:05 น.'). BONUS 11) FRESHNESS + MATCH CHECK: show the exact source price (e.g., ทองคำแท่ง 96.5% ราคากลาง) so users can reconcile with their gold shop and trust the app. BONUS 12) 5-SECOND TEST in QA: before release, a first-time user must answer value / up-down / what changed / what to do within 5 seconds of opening the app.

**antipatterns_to_avoid**: Widget soup (more than ~6 first-screen elements competing for attention); marketing/upsell banner above the portfolio numbers; color-only gain/loss encoding (fails 1.4.1 and ~8% of male users); P/L in only one unit; numbers with no comparison anchor; jargon tooltips that define terms with more jargon; desktop-first dense tables squeezed onto mobile; fake or unlabeled demo data in empty states; bare spinner-only loading; burying the day change below the fold or behind a tap; login wall before any value is shown; notification spam (every move = crying wolf); charts without numeric labels; red-wall loss screens without long-term context; hiding the price timestamp.

### evidence

**confidence**: medium - the first-screen hierarchy, progressive disclosure, dual-unit P/L, color-blind-safe encoding and state-design patterns are long-established and consistent across NN/g, WCAG and mainstream fintech practice (2 key sources verified live), but this session's web searches all failed, so fintech-specific claims and Thai-language/number-format conventions rest on prior knowledge rather than fresh citations.

---

## 5. Segment: Active short-term gold traders (Thai online gold-trading app users)

*Fields marked uncertain: MTS Gold V-GO feature set and user reviews — dedicated search returned zero results; any V-GO-specific claim is [uncertain] (segment description sourced from project context, not verified)., App-store review sentiment (ratings, top complaints) for Thai gold apps — store pages were not directly read [uncertain]., Per-app latency, spread and fee figures — no benchmark numbers found in retrieved sources [uncertain]., Relative share of Thai short-term traders using futures/margin vs physical 96.5% online bars [uncertain]., Push-notification open rates or gold-specific alert-UX studies — no dedicated study found; alert preferences are inferred from general active-trader tooling trends [uncertain]., Specific baht-price levels and resistance values used in example user questions are illustrative, not verified market data [uncertain].*

### basic_info

**item_name**: Segment: Active short-term gold traders (Thai online gold-trading app users)

**one_liner**: Thai retail traders who buy and sell gold frequently on intraday-to-days horizons via online apps (real-time Gold Spot trading like YLG Get Gold, baht-based 96.5% online gold and gold futures/margin platforms, USD 99.99% spot apps), who follow DXY, US10Y and Fed news closely and need fast charts, reliable alerts and clear timing context rather than beginner education.

### needs

**jobs_to_be_done**: - Time entries and exits around volatile sessions (Asia open, London/NY overlap, US data drops: FOMC, CPI, NFP) with 24-hour real-time Gold Spot access from the phone — YLG explicitly markets 24h real-time spot trading from 100 THB up to 80 kg/day (thestandard.co).
- Set a daily directional bias from macro drivers: DXY (inverse), US10Y/real yields, Fed rate path, geopolitics — using them as context for buy/hold/sell, not as predictions.
- Manage risk on leveraged positions: know distance to margin call / liquidation, size positions, place stops; MTS Gold's own chairman example (10% margin + 2% price drop = 20% loss) shows how brutal leverage is when misjudged.
- Act on alerts within minutes: see the trigger, verify on a fast chart, execute, and know profit can be withdrawn same-day (YLG legitimacy checkpoint #1: withdrawal must be immediate with no extra transfer).
- Track realized/unrealized P&L per trade and per position, including fees/spread/swap — the market trend toward dedicated P&L dashboards (e.g., Groww's F&O P&L dashboard) reflects this job.
- Diagnose losing trades afterwards: what news or macro move caused the drawdown, and what to change — this is the 'review' job active traders do nightly.
- Screen platforms for legitimacy before funding them: run the 5-point check (withdrawal terms, Gold Traders Association membership, official app-store origin, company-name transfer account, no guaranteed returns) — a recurring job whenever the hot market spawns new apps.
- Stay inside spread/fee/overnight-swap costs so intraday profits are not eaten by friction.

**top_questions**: - "ทองวันนี้เข้าหรือรอ?" — Buy now or wait? (the single most-asked question before a session)
- "DXY ขึ้น ทองโดนแรงไหม?" — If the dollar index jumps, how hard does gold get hit today?
- "เฟดประชุมคืนนี้ (ตี 2 ไทย) ควรลดพอร์ตไหม?" — Fed decides tonight at 2am Thai time; should I cut my position?
- "ราคาทอง (บาททอง) รับซื้อ-ขายเท่าไร สปอตเท่าไร?" — What is the baht-gold bid/ask vs world spot right now?
- "ผมเหลือระยะ margin call กี่จุด?" — How many baht/points until my margin call?
- "ทำไมทองร่วงทั้งที่ข่าวดี?" — Why did gold drop even on good news? (they see moves they cannot explain)
- "จุดตัดขาดทุน (cut loss) ควรวางตรงไหน?" — Where should my stop sit so it is not in the noise zone?
- "เป้า 52,700 ผ่านแล้ว เดินหน้าไหม?" — Price broke my target level; do I hold for continuation?
- "ถอนเงินกี่โมงถึงเข้าบัญชี?" — Until what time can I withdraw and get money today?
- "แอปนี้ของแท้ไหม? ทำไมให้โอนเข้าชื่อคน?" — Is this app real? Why is the transfer account a person's name?

**decision_drivers**: - Real-time 24h Gold Spot feed with tight spread and low fees — they compare apps on feed speed and cost, and trade only where spot tracks the world market (YLG: legit apps 'อิงตามราคาทองโลก Gold Spot').
- Withdrawal speed and terms: same-day withdrawal with no additional transfer, no advance 'tax/fee' — the #1 legitimacy and platform-choice signal in YLG's 5-point checklist.
- Execution stability during volatility: the gold market just had its most volatile week since 1980 (Nation Thailand) — app freezes or rejected orders cost real money, so reliability drives platform loyalty.
- Clear margin and liquidation rules for futures/margin accounts (initial margin %, liquidation price shown in advance).
- Macro context they already trust: DXY, US10Y, Fed calendar and geopolitics — an app that surfaces these with correct direction (not vague predictions) becomes the daily home screen.
- Technical levels and order-book context: support/resistance, previous high/low, depth-of-market (TradingView's DOM explainer shows active traders expect this).
- Legitimacy credentials: membership in the Gold Traders Association, official App Store/Play Store distribution with substantial non-bot reviews, transfers going to a registered company name (YLG 5 points).
- Regulatory environment signals: Thailand currently lacks a dedicated gold-trading regulator and rules are tightening (Policy Watch) — they watch for platforms that self-police.

### pains

**top_pains**: - Scam/fake gold-trading apps exploded during the hot market: LINE-forwarded links, sideloaded .APK files, lookalike stores, personal-name ('mule') accounts — YLG, Spring News and the Central Investigation Bureau all issued warnings (thestandard.co; springnews.co.th).
- Withdrawal traps: fake apps demand an extra 10–20% 'tax/fee' before release; active traders live in fear of profits they cannot pull out.
- Volatility blowouts and stop hunts in the most volatile week since 1980 (Nation Thailand) — margin calls, liquidations and emotional overtrading.
- News beats them to the trade: Fed/DXY/CPI headlines move price in seconds; by the time they interpret Thai-language news, the move is gone — they lose money to lag, not to lack of effort.
- Fragmented workflow: one app for baht-gold, one for world spot, MT4/TradingView for charts, Line groups and YouTube for analysis, a notes app for journaling — nothing joins them.
- Consumer apps hide intraday tools (1m/5m granularity, depth, indicators) because they are designed for beginners; pro platforms don't show baht-denominated positions or 96.5% bar pricing.
- Opaque costs: spreads, overnight swaps and fee schedules that make intraday P&L differ from the raw spot move, without explanation.
- Regulatory grey zone: no single Thai regulator oversees gold trading and supervision is being tightened (Policy Watch), so dispute recourse is unclear.

**confusion_points**: - Why baht gold (96.5% purity, per-baht-weight shop price) and world spot (99.99%, USD/oz) do not move 1:1 — local premium/discount and exchange rate are invisible to them.
- Fed/DXY/US10Y causality and lag: jargon like 'real yields', 'hawkish/dovish', 'CME FedWatch' gets repeated by influencers without a direction or time-horizon attached.
- Margin/liquidation arithmetic: many cannot compute their own liquidation price or how a 10% margin account turns a 2% drop into a 20% loss (MTS chairman's example).
- Chart artifacts: session gaps, overnight swap charges, and why their realized P&L differs from the spot move (spread + fees).
- Real vs fake app signals: high download counts and 5-star reviews can be bot-farmed; they do not know the transfer-account-name and association-membership tells.
- Units and conversions: baht weight vs troy ounce, 96.5% vs 99.99% purity, baht-yen terminology — easy to compare the wrong numbers across apps.

**trust_barriers**: - Any request to transfer additional money to withdraw is treated as a 100% scam (YLG checkpoint: fees must be deducted from the withdrawal, never added).
- Guaranteed-return marketing ('กำไรวันละ 10–20%') instantly disqualifies a platform — legit apps do not guarantee returns.
- Black-box AI calls destroy trust fast with this segment because they can immediately verify against the chart: one wrong, unexplained 'BUY' signal and the assistant is muted.
- Data provenance doubts: whose spot price is it, which market, delayed or real-time, baht-converted at what rate?
- Non-official distribution (APK via LINE) and transfer destinations that are personal accounts or names that do not match the app.
- Fear that the app itself holds their money with no regulator behind it (Thailand has no dedicated gold-trading supervisor — Policy Watch).

### ux

**must_have_first_screen**: - Big live tickers: world Gold Spot (USD/oz) AND Thai baht-gold price, with change-since-open and +/− ▲▼ coloring, updating in seconds.
- Their open position(s) card: entry price, live P&L in THB, distance to stop and to margin call/liquidation.
- Alert status strip: which alerts fired today, with one-line reason.
- Macro mini-strip: DXY, US10Y, and a countdown to the next Fed/CPI event tagged with expected impact.
- One-tap Buy/Sell entry buttons and a chart that goes full-screen instantly.
- Visible legitimacy badge: registered company name + Gold Traders Association membership, so the scam-detection job is answered at a glance.

**workflow_preferences**: - Mobile-first, one-handed, glance-and-go: they check the price dozens of times per day in seconds — dashboard must be readable in 5 seconds.
- Notification-driven loop: price alert or economic-calendar push → open app → glance cockpit → execute; total under ~30 seconds, with deep links straight to the chart.
- Fast multi-timeframe charts: 1m/5m/15m/H1/D toggle with no reload, drawings preserved; landscape mode and second-screen/desktop for active sessions.
- Bottom-nav or tab structure: Chart, Positions/Portfolio, News/Macro, Alerts, History — not a single endless page.
- Session bookends: quick pre-market macro briefing (what to watch tonight) and after-close recap/diagnosis (what happened to my trades).
- Alerts need priority tiers and distinct sounds (price level vs margin call vs news) so they never mute the channel; withdrawal/bank-cutoff status visible inline.

**language_and_tone**: - Terse Thai trading slang is native to them ('เข้า', 'ตัด', 'cut loss', 'ทำกำไร', 'เหนียว', 'รูปเสา') — use it, but put icon + number first and words second.
- Numbers must be unambiguous: thousands separators, explicit unit labels (บาททอง/96.5% vs spot USD/oz 99.99%), ±% change, Thai baht and USD shown together.
- Macro lines must be one sentence with a plain-Thai direction gloss ('สั้น ๆ: เหรียญแข็ง กดทอง'), not paragraph explainers; link out for depth.
- Neutral, factual tone only: no hype, no guaranteed-return copy, no exclamation-mark marketing — for this segment hype is a scam tell (YLG checkpoint #5).

**accessibility_notes**: - Color-blind-safe gain/loss: red/green must always be paired with ▲▼ glyphs and +/− signs; check contrast for the most common deuteranopia patterns.
- Prices in large type (≥16sp equivalent) with high contrast; dark mode essential because US data drops land 8pm–3am Thai time.
- One-hand reachability: Buy/Sell and stop controls in thumb zone; confirmations must not require two-handed typing.
- Distinct alert sounds + haptics per alert type so a margin call is never confused with a routine price ping.
- Thai-first labels with small English subtitles for standard terms (DXY, Fed) so jargon is learnable but never a blocker.

### design

**implications_for_gold_assistant**: - 1. Make the default first screen a trader cockpit, not a portfolio gallery: live baht-gold + world-spot tickers with second-level updates, an open-positions card (entry, live P&L in THB, distance to liquidation), today's alert strip, and a countdown to the next Fed/CPI event — all readable in a 5-second glance.
- 2. Macro density with progressive disclosure: DXY, US10Y and Fed as compact always-visible tiles (one number + one arrow each), tap-to-expand into a single plain-Thai line ('ดอลลาร์แข็ง → กดทอง') — never default to long macro essays on the main screen.
- 3. News-to-price correlation layer: when a macro headline (FOMC, CPI, DXY spike) moves gold more than a threshold within minutes, overlay the news timestamp directly on the 1m/5m chart and pin a one-line Thai explanation ('ข่าว Fed เหยียดดอกเบี้ย 21:14 → ทองร่วง 120 จุด') — this converts loss diagnosis from guessing into a visible cause.
- 4. Context-carrying alerts: push notifications should include trigger level + the macro reason + a deep link to the chart with the alert line pre-drawn; use distinct sounds/tiers for price alerts vs margin-call alerts vs news so users never mute the channel.
- 5. Intraday granularity for traders: offer 1m/5m/15m charts with session markers (Asia/London/NY), previous-close line, today's high/low, and optional depth-of-market for futures users; timeframe switching must be instant with drawings preserved, and a 'trader mode' toggle should hide beginner education cards to maximize chart space.
- 6. Loss-diagnosis mode: for each closed trade show entry/exit, spread+fees paid, what DXY/US10Y/Fed did during the holding window, and a plain-Thai 'what happened' summary — this segment reviews losses nightly; an assistant that explains rather than predicts earns the right to be consulted before the next trade.
- 7. Design the trust surface deliberately: show registered company name, Gold Traders Association membership, official-store-only install path, and company-name transfer destinations directly on money screens; implement YLG's 5-point checklist as an in-app 'verify before you fund' aid; never use guaranteed-return copy anywhere.
- 8. Surface withdrawal mechanics inline (bank cutoff times, withdrawal status, fee-deducted-not-added rule) — withdrawal certainty is the #1 legitimacy signal from the research.

**antipatterns_to_avoid**: - Guaranteed-return or 'daily profit' marketing copy anywhere in the product — for active traders it is indistinguishable from the scam apps being warned about (YLG checkpoint #5).
- Any flow asking users to transfer extra money or 'tax/fees' to unlock withdrawals, or showing personal-name bank accounts on payment screens.
- App distribution outside official stores (LINE-forwarded APKs, sideloading) — an automatic trust killer.
- Burying price and open positions under educational cards, mascot animations or long AI essays; requiring more than one tap to reach a 5-minute chart.
- Heavy, graphics-first dashboards that cost seconds of latency — during 1980-level volatility weeks, a slow app is a financial loss.
- Unexplained AI predictions ('AI says BUY') without timestamped reasoning, data provenance or a verifiable track record.
- English jargon walls (DXY, US10Y, real yields) with no Thai gloss, and mixing baht-gold (96.5%) and spot (99.99%) numbers without unit labels.
- Untiered notification spam — it gets muted, and then a real margin call is missed.

### evidence

**sources**: - THE STANDARD WEALTH — 'YLG เปิด 5 จุดสังเกต แอปฯเทรดทอง ของแท้ vs. มิจฉาชีพ ชี้ทองร้อนแรง' (full article read: 5-point real-vs-fake app checklist, YLG Get Gold 24h spot from 100 THB, gold forecast 5,100–5,136→5,400 USD/oz) — https://thestandard.co/ylg-gold-app-scam-price-forecast/
- Spring News — 'จุดสังเกต แอปฯเทรดทองคำ ของแท้ เทียบ แอปฯมิจฉาชีพ หลอกเทรดทองคำออนไลน์' (headline/summary via Google News RSS; page body not retrievable) — https://www.springnews.co.th/news/hot-issue/861954
- Daily News — 'เปิด 5 จุดสังเกต แอปเทรดทอง ของแท้ Vs มิจฉาชีพ รู้ทันก่อนไม่ตกเป็นเหยื่อ' (search-result corroboration of YLG checklist) — https://www.dailynews.co.th/news/5590037/
- Marketeer Online — 'เจาะลึกแอปฯ GOLD NOW แพลตฟอร์มเทรดทองคำออนไลน์ รับเงินเข้าแบบ Real-Time ซื้อ ขาย ออม ได้ทุกที่ ไม่ต้องวางหลักประกัน' (headline via Google News RSS: real-time deposits, no-collateral trading) — via https://news.google.com/rss/search?q=เทรดทองออนไลน์+รีวิว+แอป&hl=th
- Hua Seng Heng — 'วิธีเทรดทองออนไลน์ฉบับมือใหม่ รวมทุกเรื่องที่ควรรู้' (headline via RSS: beginner onboarding flow for online gold trading) — via Google News RSS (query: เทรดทองออนไลน์ รีวิว แอป)
- Nation Thailand — 'Gold Market Plummets in Most Volatile Week Since 1980 as Speculative Blowouts Spark Alarm' (headline via RSS: volatility context) — via Google News RSS (query: gold price alert app traders UX)
- Policy Watch — 'ไทยไร้หน่วยงานดูแลซื้อขายทอง จ่อคุมเข้มร้านทอง ส่งรายงานธุรกรรม' (headline via RSS: Thai regulatory gap) — via Google News RSS
- Robinhood Newsroom — 'Robinhood Unveils Powerful New Tools for Active Traders at HOOD Summit 2025' (headline via RSS: direction of active-trader tooling) — via Google News RSS (query: gold trader dashboard features)
- Groww — 'Track, Analyse & Improve Your Trades with Groww's F&O P&L Dashboard' (headline via RSS: per-trade P&L analytics trend) — via Google News RSS
- TradingView — 'Depth of market (DOM): what it is and how traders can use it' (headline via RSS: active-trader chart tooling expectations) — via Google News RSS
- Yahoo Finance — '8 best stock market apps for trading in 2025' (headline via RSS: dashboard feature baselines) — via Google News RSS
- Mitrade — 'ซื้อทองร้านไหนดีสำหรับปี 2569? 10 อันดับร้านทองที่เหมาะกับการลงทุน' (headline via RSS: platform comparison behavior) — via Google News RSS
- SCB — 'ซื้อทองยุคนี้ ไม่ได้เลือกแค่ว่า ซื้อที่ไหน แต่เลือกได้ว่าจะ ลงทุนทองแบบไหน' (headline via RSS: form-factor choice, online vs physical) — via Google News RSS

**confidence**: medium — the trust/scam/withdrawal findings and the real-time spot trading model are anchored in one fully-read Thai industry article (YLG via THE STANDARD) and corroborated by multiple independent Thai headlines (Spring News, Daily News, CIB warning) and English market headlines, but no direct user interviews, app-store review mining, or MTS Gold V-GO-specific reviews could be retrieved, so behavioral details (latency sensitivity, notification habits) rest on segment plausibility rather than primary evidence.

---

## 6. Segment: DCA long-term accumulators

*Fields marked uncertain: ux.accessibility_notes, ux.workflow_preferences, needs.decision_drivers, pains.top_pains*

### basic_info

**item_name**: Segment: DCA long-term accumulators

**one_liner**: Thai gold investors who buy a fixed amount on a regular schedule (monthly baht-cost averaging into 96.5% gold bars or digital gold savings/funds), hold for years, and measure success by average cost, total return versus cash savings, and the discipline to keep buying through corrections.

### needs

**jobs_to_be_done**: Accumulate wealth in gold in small, disciplined steps without needing to time the market; protect savings from inflation and the feeling that cash 'won't stay saved' (a common Thai motivation: if you can't save cash, save gold). They need to always know where they stand versus their own average cost and versus simply keeping the money in a bank deposit; to get steady, calm guidance on whether to keep buying or pause when price corrects; to convert digital savings into physical bars/coins when ready (gold as a trusted, tangible asset and a way to pass wealth to family - Thai demand is #1 in ASEAN, top-10 globally per YLG); and to avoid the leverage/futures traps that cause most gold-investor losses (per MTS Gold's chairman: a 10% margin + 2% price drop = 20% loss).

**top_questions**: 1) 'Am I in profit or loss right now versus my average cost - in baht, not just percent?' 2) 'Gold keeps falling - should I keep buying every month or pause first?' (the classic saver's dilemma 'should I buy the dip or wait?', echoed across Thai gold media during the 2026 correction) 3) 'If I save 1,000-3,000 baht every month, how many grams / how many bars will I have in 5 years?' 4) 'Why did the gold price drop today - should I worry?' 5) 'Can I withdraw my app savings as real gold bars, and what are the fees/spreads?' 6) 'If I sell today, how much cash do I actually get after the shop spread?' 7) 'What share of my portfolio should be gold?' (common guidance: cap around 10%) 8) 'App gold savings vs gold mutual fund vs physical bars at the shop - which is better for me and what do they cost?'

**decision_drivers**: Distance of current price from their own average cost; belief in the long-term uptrend narrative (central-bank buying streaks, '$4,000 is the new base' story from big Thai gold houses); comparison of gold's total return versus fixed deposits and cash savings; visible fees, spreads and conversion costs; whether the platform lets them take physical gold (trust anchor for Thai savers); liquidity for emergencies; regulatory news (Bank of Thailand curbs on online gold trading cut volumes ~60% in 2026, possible trading tax); and explicit warnings that leveraged products (futures/margin) are the real loss-maker, so they stay with physical/DCA products.

### pains

**top_pains**: Holding losses after buying near the peak ('stuck on the mountain' / dtid doi): in 2026 Thai gold funds returned about -30% in H1 and baht gold fell from over 70,000 to ~64,000 baht/baht-weight, so many regular buyers are under water. The agonizing keep-buying-or-pause decision during corrections with no tool showing the math on THEIR plan. Opaque real returns: shop buy/sell spreads, premiums, fund fees and conversion fees are scattered and rarely netted out. Price whiplash anxiety - local prices are revised up to 15 times a day. Conflicting guru forecasts (70,000 is the new base / 100,000-baht gold someday vs asset managers telling people to cut gold after a -30% half) leave them whipsawed. Fear of scam or unlicensed platforms, and uncertainty about Bank of Thailand rules and possible taxes.

**confusion_points**: Units: baht-weight (15.16g) vs gram vs troy ounce. Purity: 96.5% local bars vs 99.99% app/fund gold - average costs cannot be compared naively. Local price vs world price (baht exchange rate makes Thai gold move differently). Buy/sell spread and why selling back gives less than the board price. Difference between gold savings in an app, gold mutual funds, and physical bars (fees, tax, redemption), and especially 'gold fund' vs 'gold mining equity fund' (in 2025 they returned +61.95% vs +141.23% - completely different risk). Why gold falls when everything looks bad (Fed rate HIKES on oil-driven inflation in 2026, opportunity cost). Jargon: DCA, support/resistance, realized vs unrealized loss.

**trust_barriers**: Scam fear and doubts about whether 'digital gold' is really vaulted gold - the single strongest trust move in the Thai market in 2026 was apps adding physical withdrawal (KKP Dime partnered MTS/YLG so 100-baht savers can convert to real bars/coins from 0.05 troy oz). Black-box AI advice ('sell now' with no reason) - users distrust predictions without cited evidence, especially when famous analysts contradict each other. Unfamiliar platforms versus century-old gold shops (MTS, YLG, Hua Seng Heng carry inherited trust). Concerns about where analysis data comes from, and about regulatory standing (BOT measures, potential tax) - people fear platforms that could be shut down or taxed.

### ux

**must_have_first_screen**: Within 5 seconds: (1) current portfolio value in THB and total P/L versus average cost in BOTH baht and percent; (2) today's buy/sell prices (with the shop spread visible, e.g. bar sell-out price); (3) the user's average cost per baht-weight next to today's price; (4) next scheduled DCA buy (date + amount) with a pause/skip affordance; (5) one plain-Thai line: why gold moved today, with source chips; (6) a price chart with the user's average-cost line drawn on it. Agent activity should be visible but secondary - a compact 'analysts are reviewing your plan' indicator, not a wall of text.

**workflow_preferences**: Mobile-first single page (the growth of Thai gold accumulation is happening on phones: KKP Dime 267k users, +95% volume in a year; apps let savers start at 100 baht, pick the day and amount, and adjust anytime). Rhythm matters more than features: a quick daily glance at P/L; the real session is monthly around payday/auto-buy day (review plan, confirm or adjust the next buy); a yearly review of total return vs cash. Push notifications only on meaningful events: price crossing their average cost, a >3-5% daily move, monthly buy reminder, physical-gold threshold reached. Progressive disclosure: one-tap expansion from any number into the agents' reasoning with citations. Must support manually logging offline purchases from gold shops, since many accumulators mix shop bars with app savings.

**language_and_tone**: Plain everyday Thai, warm and reassuring (gold is a 'comfort asset' - the KKP Dime product team explicitly says UX must make buy > check savings > withdraw physical feel seamless, clear and uncomplicated). Prefer Thai terms over English jargon: say 'buy steadily every month / monthly gold saving' for DCA, explain anything technical in tap-to-explain chips. Numbers in Thai formats: '64,000 baht per baht-weight', Buddhist calendar years (B.E. 2569), every percentage paired with its baht amount ('-12% (-9,400 baht)'). Short sentences; details expand on demand; never moralize about losses.

**accessibility_notes**: [uncertain - inferred, not directly verified by sources] Adjustable font size (16sp+ body, large-number mode for key figures), WCAG AA contrast, color-blind-safe gain/loss encoding (green/red PLUS up/down arrows and +/- signs - never color alone), one-hand-reach bottom action bar, reduce-motion option, and high-contrast large numerals for the 40+ cohort that also accumulates gold.

### design

**implications_for_gold_assistant**: 1) AVERAGE-COST LINE ON THE CHART: overlay a dashed horizontal line at the user's weighted average cost with a floating label ('average cost 62,400 / today 64,000 = +2.6% (+8,200 THB)'); shade the gap between price and cost line; default ranges 1Y/5Y/MAX with intraday collapsed behind an explicit 'daily' toggle so long-horizon framing wins. 2) 'AM I WINNING?' HEADER CARD: total value, P/L vs average cost in baht AND %, average cost per baht-weight and per gram, today's sell-back price net of spread ('if you sold all today you'd get X baht'); recompute on price change but throttle refreshes to avoid 15x/day anxiety. 3) DCA PLAN CARD: next auto-buy (date, amount), 12-month progress bar and accumulation streak, total grams accumulated, goal marker (e.g. '1 baht-weight bar'), with actions: change amount / skip this month / pause for 1-3 months (pause, never hard-cancel) - mirrors what Thai gold apps ship (choose day, choose amount, adjust anytime, withdraw real gold). 4) 'KEEP BUYING OR PAUSE?' DECISION SUPPORT: when spot < average cost or price fell >=5% in 30 days, surface a card with three options (continue / reduce amount / pause) and compute - on the user's own plan - the resulting new average cost and total grams for each under a 12-month scenario, plus the Quant agent's evidence chips (e.g. how DCA buyers fared through past deep corrections, citing published deep-correction statistics from YLG) and a Risk agent note; frame as options with reasons, never as a command, and never push stop-loss selling at this segment. 5) 'VS CASH' COMPARISON STRIP: total return of their actual monthly contributions versus (a) the same contributions in a fixed deposit and (b) one lump sum on their first purchase date - accumulators judge gold against cash savings, so show 'if this had been a deposit: ~X baht'. 6) UNIFIED MULTI-PRODUCT LEDGER: consolidate shop bars (96.5%), app gold savings (99.99%) and gold funds into one list with per-product average cost, all normalized to grams and THB, purity badge on every row, and a per-row 'fees + spread paid so far' figure; allow manual entry for offline shop purchases. 7) PHYSICAL CONVERSION TRACKER: show progress toward the physical-withdrawal minimum (e.g. 0.05 troy oz), a transparent conversion calculator (spread + casting/withdrawal fee + delivery insurance) BEFORE confirmation, and partner-shop trust badges with pickup or insured-mail options. 8) AGENTS' DIVISION OF LABOR FOR THIS SEGMENT: News/Macro agents answer 'why did gold fall today' in 2-3 plain-Thai sentences with linked sources; Quant agent runs the DCA scenario math; Risk agent explicitly separates gold-price risk from leverage risk and the app must never show futures/margin promotions or CTAs to these users (leverage is where Thai gold investors actually lose money per MTS Gold); Lead Researcher delivers a monthly plain-Thai summary push: 'this month you bought X g at avg Y; your average cost moved from A to B'. 9) TRUST SURFACES: every agent claim carries citation chips into the knowledge graph; show regulatory/licence status and physical-gold proof; tone guidelines ban guaranteed-return language.

**antipatterns_to_avoid**: Intraday-first ticker dashboards and flashing red/green tiles (prices revise up to 15 times a day; it manufactures anxiety for people who buy monthly). Push notifications urging timing moves, 'hot tips', or leveraged products. Showing only percentages without baht amounts. Black-box 'AI says: sell' verdicts without reasons, sources, or confidence - this kills trust fastest. One-sided bullish hype (Thai users see contradictory guru forecasts daily; overconfidence reads as scam). Hiding spreads/fees/redemption costs until checkout. Separate product silos with incompatible units (96.5% bars vs 99.99% app gold) and no normalization. Confusing 'gold fund' with 'gold mining fund' labels. Gamified streak guilt-tripping when a user must pause a month. Any aesthetic that resembles known Thai investment scams: guaranteed returns, countdown pressure, unsolicited DMs.

### evidence

**sources**: FULL TEXT READ: (1) 'MTS Gold recommends gold investing in a volatile world, champions DCA long-term accumulation, warns margin trading carries high loss risk' (Thai, Share2Trade reprinting InfoQuest, Jul 2026) https://www.share2trade.com/news/57354/mts ; (2) 'Gold's price is down by more than 25%. Here's what investors should do next.' (CBS News, Jul 9 2026) https://www.cbsnews.com/news/golds-price-down-25-percent-what-investors-should-do-next/ ; (3) 'Gold is hot on Dime! Trading volume passes 500 billion baht, +95% in one year; MTS-YLG partnership enables real-gold withdrawal' (Forbes Thailand, Sep 2026) https://forbesthailand.com/news/finance-and-investment/gold-heats-up-on-dime-trading-volume-surges-past-500-billion-baht-a-95-increase . SEARCH-SNIPPET EVIDENCE (Google News RSS + Bing News RSS, Thai & English): (4) East Spring AM: fund houses advise cutting gold allocation after H1 2026 return of -30% (via Bing News RSS) ; (5) Thairath (Jan 2026): gold past 70,000 baht, gurus recommend long-term DCA (via Google News RSS) ; (6) TrueID (Jul 2026): the gold-saver's view - buy the dip or wait? (via Google News RSS) ; (7) Bangkok Biznews (Oct 10 2026): take profit or buy more? https://www.bangkokbiznews.com/news/news-update/1255805 (Cloudflare-blocked on direct fetch; headline via Bing News RSS) ; (8) Post Today: MTS Gold - 70,000 baht is the new base https://www.posttoday.com/business/740289 (via Bing News RSS) ; (9) SCMP (Sep 2026): Shanghai Gold Exchange pushes banks to end retail leverage trading https://www.scmp.com/economy/china-economy/article/3368681/shanghai-gold-exchange-pushes-more-chinese-banks-end-retail-leverage-trading ; (10) BigGo Finance (Oct 2026): China's banks escalate gold accumulation plan fee war - auto-invest fees cut to zero (via Bing News RSS) ; (11) GoldSilver (May 2026): Dollar-cost averaging into gold and silver - the investor's practical guide (via Google News RSS) ; (12) Money.com (Jun 2026): Why a $100-a-month gold plan could make sense right now (via Google News RSS) ; (13) Khaosod (Aug 2026): YLG - Gen Z worldwide accumulates gold via mobile in small amounts (via Google News RSS) ; (14) Hua Seng Heng (May 2026): GOLD NOW app - monthly gold saving, pick day/amount, adjust anytime, withdraw real bars (via Google News RSS) ; (15) Krungsri (Jan 2026): 2026 gold outlook + how to avoid buying at the peak (via Google News RSS) ; (16) Wealthy Thai (Dec 2025): gold funds +61.95% vs gold-mining funds +141.23% - different assets, different risk (via Google News RSS) ; (17) Spacebar.th (Jun 2026): YLG deep-correction statistics (via Google News RSS) ; (18) MSN-syndicated Thai personal finance (Nov 2025): how to invest in gold without getting stuck at the peak - 3 checklists (via Bing News RSS) ; (19) CNBC (Sep 2026): Gold drops more than 1% on U.S. rate-hike bets https://www.cnbc.com/2026/09/28/gold-drops-more-than-1percent-on-us-rate-hike-bets.html ; (20) InterGold weekly (Jul-Oct 2026): $4,000 base, gold below 65,000 baht - moment to accumulate? (via Google/Bing News RSS). SEARCH LIMITS: Thai web queries on Bing returned poisoned results and Pantip/Thairath blocked scraping from this sandbox, so first-hand forum complaints could not be read directly; user-voice pains are inferred from mainstream Thai financial media framing instead.

**confidence**: medium - the segment's market context, product norms, and expert guidance are directly evidenced by three full-text articles plus many corroborating headlines, but direct first-hand user-voice evidence (forums, app reviews) was unreachable from this environment, so several UX inferences rest on expert commentary rather than observed user behavior.

---

## 7. Segment: First-time gold savers (Thai retail users new to gold, buying small bars or saving via gold-savings apps)

*Fields marked uncertain: [uncertain] Segment size and demographics (share of Gen Z/first-jobbers in Thai gold demand) - no national survey read this session., [uncertain] 'ทองหมีเนย' product details (issuer, exact denomination, fees, whether it is a bar or sheet) - evidence is headline-level only., [uncertain] SCB Gold Marketplace specifics beyond the headline (which 3 shops, minimums, delivery fees) - not fetched., [uncertain] Whether เป๋าตัง Gold Wallet terms are still current (the 0.1 บาททอง / 6,000+ baht minimum comes from a Dec 2025 article; may have changed)., [uncertain] Exact current ค่ากำเหน็จ / fee schedule for 1 สลึง and ครึ่งสลึง small bars at major shops - not verified this session., [uncertain] Practical redemption experience details per app (wait times, branch availability) - no user reviews read, only article summaries of pros/cons.*

### basic_info

**item_name**: Segment: First-time gold savers (Thai retail users new to gold, buying small bars or saving via gold-savings apps)

**one_liner**: Thai users new to gold - largely younger salaried/first-job and Gen Z savers - who treat gold as SAVINGS, not trading: a full 1 บาททอง bar (~66,000-80,000 baht in 2026) is out of reach, so they enter via tiny denominations (999-baht ทองแผ่น like the viral 'ทองหมีเนย' and Aurora x Disney sheets, 20,000 pieces sold in 2 months) or savings apps starting at 10-1,000 baht (Dime 100, MTS แม่ทองสุก 100, TrueMoney SafeGold 100, GOLD NOW ออมNow 1,000, เป๋าตัง ~6,000+, Bitkub XAUt 10), deciding from the shop price board, parents'/friends' word of mouth, and influencer marketing, with almost no finance vocabulary.

### needs

**jobs_to_be_done**: - Turn small spare cash into something that grows: 'เงินเก็บไม่ค่อยอยู่ เอาไปออมทองดีกว่า' - put 10-1,000 baht daily/weekly/monthly into gold instead of leaving it in a deposit.
- Reach a milestone of REAL physical gold: accumulate up to 1 สลึง or the first small bar to hold, gift, or keep as the family safety asset ('ทองมีไว้ยึดเหนี่ยว', wedding-gold habit inherited from parents).
- Know today's price the way shops announce it: check the board price (สมาคมค้าทองคำ morning announcement, repeated intraday) before deciding to put today's slice in - and buy more when 'ทองลง' (ช้อนซื้อ / dip-saving).
- Check 'did my savings grow?' in baht: how much is my accumulated gold worth TODAY, how much is gained/lost, and how much more until the next สลึง.
- Understand the way out before the way in: when can I sell/redeem, what will I actually receive (ราคารับซื้อ, fees, minimum weight, lock-up) if I need the money back.
- Choose a place to save WITHOUT financial knowledge: a real gold-shop brand or bank app that someone they trust already uses - verifiable by walking into a branch.
- Get simple, honest guidance on 'ตอนนี้ควรออม/ถือ/ขายดี?' (the exact beginner question on TrueID) - a plain answer with reasons, not a trading signal.

**top_questions**: - วันนี้ทองขึ้นหรือลง - เอาเงินมาออมวันนี้ดีไหม? (Up or down today - good day to save?)
- เริ่มต้นขั้นต่ำเท่าไหร่ - มีแค่ 100 บาท/1,000 บาทพอไหม? (What's the minimum - I only have 100/1,000 baht)
- ป้ายราคา ขายออก/รับซื้อ ต่างกันยังไง - ถ้าฉันซื้อต้องดูตัวไหน? (Sell-out vs buyback - which one applies when I buy?)
- ออมไปแล้วถ้าต้องการเงินคืน ทำได้ไหม - ได้เท่าที่ใส่ไหม? (Can I get my money back - the same amount?)
- ออมยังไงให้กลายเป็นทองแท่งได้จริง - ต้องครบ 1 สลึงเหรอ ต้องไปรับที่ห้างไหม? (How does saving become a real bar - do I need 1 สลึง and which branch?)
- ทอง 96.5% กับ 99.99% ต่างกันยังไง - ร้านรับซื้ออันไหนดีกว่า? (96.5% vs 99.99% - which does the shop prefer to buy back?)
- ทำไมขายคืนได้น้อยกว่าที่ซื้อ - ค่ากำเหน็จ/ค่าธรรมเนียมคืออะไร? (Why is sell-back less than what I paid - what are craftsmanship fees?)
- แอปนี้ปลอดภัยไหม - ทองเก็บอยู่ที่ไหน - เอาออกมาเป็นทองจริงได้จริงไหม? (Is this app safe - where is the gold - can I really get physical gold out?)

**decision_drivers**: - Ticket size first: can they start with the cash they actually have today - minimum purchase is the first filter (apps: Dime/MTS/SafeGold from 100 baht, ออมNow from 1,000, เป๋าตัง 0.1 บาททอง = 6,000+, XAUt from 10; micro-gold sheets from 999 baht).
- The shop board number they already see on news feeds and family LINE groups: 'gold is down today = good day to save', decided from baht deltas, not charts or percentages.
- Word of mouth is the deciding channel: parents/relatives who keep gold, friends' recommendations, and influencer-branded micro-gold ('ทองหมีเนย' 20,000 pieces in 2 months 'ลงทุนทองด้วยค่าข้าว 1 มื้อ'; Aurora x Disney Mickey & Friends sheets from 999 baht aimed at Young Gen).
- Brand familiarity = trust shortcut: ฮั่วเซ่งเฮง, แม่ทองสุก, TrueMoney, เป๋าตัง/banks, SCB EASY Gold Marketplace (3 big gold shops in one bank app, no fee, home delivery) - things already in their pocket read safe.
- 'ถอนออกมาเป็นทองได้จริง' is the core trust test: redeemable as real bars at a shop branch (Gold Now, MTS strengths); delivery-only (SafeGold) or value-only (XAUt) weakens it.
- Flexibility: can save 24h or long hours (Dime 07:00-03:00), sell early without penalty, no lock-up - lock-ups are discovered too late and cause anger.
- Everything in baht: USD-only purchase flows (Dime, เป๋าตัง) and oz units feel foreign and risky to a Thai saver.

### pains

**top_pains**: - The entry ticket is too big offline: one บาททอง costs ~66,000-80,000 baht in 2026 plus travel to a shop - exactly why online 'ออมทอง' services exist (Siam Blockchain framing).
- Sell-back shock: getting less than the headline price - 'ขายทองแต่งงานหวัง 4.6 แสน ร้านให้แค่ 4.4 แสน ชาวเน็ตบอกปกติ' (Sanook, Mar 2026); spread + non-refunded ค่ากำเหน็จ are never explained at purchase time.
- Withdrawal minimums and fees bite at the end: can withdraw as a bar only at >=1 สลึง (Gold Now); MTS has a withdrawal minimum AND a withdrawal fee; XAUt cannot be redeemed physically at all.
- Lock-ups feel like a trap: TrueMoney SafeGold cannot be sold before the saving term completes - only redeemed as the gold that was saved; the money feels stuck.
- Unit and currency confusion in-app: USD-only payments with auto-conversion, oz vs บาททอง vs gram, 0.05 oz meaning nothing to them.
- Product-type confusion: crypto-form gold (XAUt/Tether Gold) looks like gold savings but 'ไม่ใช่การออมทองแบบ 100%' - no physical redemption, thin local liquidity, slight price deviation.
- 96.5% vs 99.99% purity and which one any shop will happily buy back - unknown and unexplained.
- Choice overload with no plain-Thai comparison: 6+ apps with different minimums, hours, redemption rules, fees - currently only comparable via a crypto-news article.
- Scam fear absorbed from news (fake trading platforms, mule accounts, 'fee before withdrawal') without knowing HOW to verify a legitimate platform.

**confusion_points**: - The board's columns: ราคาขายออก vs ราคารับซื้อ (vs ราคากลาง) - which number applies when THEY buy vs when THEY sell, and why the app shows yet another number.
- Units: 1 บาททอง = 15.244 g (96.5%), vs grams vs troy ounces; '0.05 oz' or '0.0152 บาททอง' from a 1,000-baht saving is meaningless without a visual.
- Purity: ทองคำแท่ง 96.5% (Thai standard) vs 99.99% 'ทองคำมาตรฐานโลก' - which is 'real gold', why prices/fees differ, and resale implications.
- Why the app price differs from the shop board or the สมาคม announcement (timing, global spot, THB/USD, platform fees).
- Finance vocabulary they do not hold: DCA, volatility, spread, spot, portfolio, oz - they think in 'ออม', 'ก้อน', 'สลึง', 'ค่าข้าว 1 มื้อ'.
- Where the gold 'is' inside an app (digital gold as a concept) and whether redemption is real or just a number.
- What an AI forecast/probability/confidence even means, and who is responsible if it is wrong.
- Fine print surfacing only at sell/redeem time: lock-up, withdrawal minimum, withdrawal fee, delivery-only redemption.

**trust_barriers**: - No known real-shop or bank brand behind the app: 'มีความน่าเชื่อถือสูง' is granted to shop-direct apps (Gold Now, MTS) and bank products (เป๋าตัง, SCB) - unknown platforms inherit scam suspicion.
- The physical-redemption test: if they cannot picture walking out with a real bar (delivery-only like SafeGold, or value-only like XAUt), trust drops.
- Anything echoing documented scam patterns: guaranteed returns, urgency/countdowns, 'pay a fee before withdrawal', personal-name accounts (Thai PBS Verify red flags; 'ไม่เชื่อ ไม่รีบ ไม่โอน').
- USD-denominated payment/price screens read as 'foreign and shady' to a Thai saver.
- Crypto-adjacent products (XAUt on Bitkub) read as gambling to them and to the family whose approval they need.
- Black-box AI advice with no visible reasons, no reference board price, and no 'not a guarantee' label.
- App distribution outside official stores (forwarded LINE links, APKs).
- One bad experience - number not matching the board, surprise fee at redemption - deletes the app; they revert to the physical shop.

### ux

**must_have_first_screen**: - Today's shop-format board as the hero: ทองแท่ง (and ทองรูปพรรณ) ขายออก/รับซื้อ in baht per บาททอง, with up/down arrow + baht delta, and provenance line 'อ้างอิงประกาศสมาคมค้าทองคำ เวลา 9:04 น.' - no login wall before this.
- 'ออมทองของฉัน' card right under the board: total saved, current value in baht, gain/loss in baht, and a progress bar to the next milestone ('อีก 2,300 บาท ครบ 1 สลึง') - progress bar, not a chart.
- A plain 'เริ่มออม' action with the minimum stated upfront: 'เริ่มเพียง 100 บาท' and what that buys in gold TODAY ('1,000 บาท = ทอง ~0.015 บาททอง').
- One tappable line that says which price is for whom: 'ขายออก = ราคาที่คุณซื้อ / รับซื้อ = ราคาที่ร้านซื้อคืนจากคุณ'.
- A reassurance strip: real-shop/bank partner badge, 'ถอนเป็นทองแท่งได้จริง', official-store badge - and absolutely no urgency/FOMO mechanics.

**workflow_preferences**: - Mobile-first inside apps they already have (TrueMoney, เป๋าตัง, banking apps) or as few steps as possible from cash to 'I own gold'; browse the board before any registration.
- Small, repeatable saving loops: set a fixed amount ('ออมเดือนละ 1,000'), optional dip-alert ('ทองลง 200 บาท - ออมวันนี้ได้ทองมากกว่าเมื่อวาน'), and milestone celebrations ('ครบ 1 สลึง').
- Full journey preview BEFORE committing: 'จ่าย 1,000 บาท -> ได้ทอง 0.015 บาททอง -> ถอนเป็นทองแท่งได้เมื่อครบ 1 สลึง ที่สาขา... เอกสาร... ค่าธรรมเนียม...' - redemption rules shown at purchase time, not at the end.
- Answers as 3-5 plain bullets, not charts or graphs; a 'ถามผู้ช่วย' entry point for beginner questions.
- LINE-shareable price cards and progress cards - word of mouth is their channel, so make sharing one tap.
- Notifications in savings language (baht deltas, milestone progress), not alert-style percentage spam.

**language_and_tone**: - Core verb is 'ออมทอง', never 'ลงทุน/DCA/เทรด'; vocabulary of the jar and the shop: 'เก็บทอง', 'ก้อนแรก', 'ครบ 1 สลึง', 'ทองแท่ง', 'ค่ากำเหน็จ' - zero jargon (no spread, spot, oz, portfolio, CFD) on primary screens.
- Baht-first and unit-always: '1,000 บาท = ทอง ~0.015 บาททอง (~0.23 กรัม)'; baht deltas before percentages; every number carries its unit.
- Short sentences, one idea per line, friendly big-sister/brother tone; inline one-time glosses ('รับซื้อ = ราคาที่ร้านซื้อคืนจากคุณ').
- Costs stated upfront in baht: show spread, fees, and non-refunded ค่าเหน็จ BEFORE purchase - honesty is the tone differentiator vs scammy platforms.
- AI framed as 'ความเห็นผู้ช่วย ไม่ใช่คำรับประกัน', always beside the official board number; encourage the fixed-amount habit rather than timing calls.
- Micro-gold framing works: 'เริ่มได้ด้วยค่าข้าว 1 มื้อ' resonates (ทองหมีเนย), but keep it dignified - no pushy gamification.

**accessibility_notes**: - Body text 16px+ with large numbers for board/values (24-32px); high-contrast; up/down always arrow + word ('ขึ้น/ลง') plus color - color never the only cue.
- Tap targets ~44-48px, bottom-anchored primary buttons for one-hand use; must work well on cheap Android phones and slow connections.
- No icon-only navigation; every icon paired with Thai text; avoid stylized fonts for numbers.
- Plain-Thai throughout - English terms (Gold Wallet, SafeGold, XAUt) need Thai labels/glosses.
- Stable layouts, no autoplaying motion; LINE-shareable cards with readable text for family consultation.
- First-run glossary available but skippable - don't force a tutorial before the first price view.

### design

**implications_for_gold_assistant**: - 1) Home screen = board + savings jar, not a portfolio dashboard: 4-number shop board (ทองแท่ง/ทองรูปพรรณ ขายออก-รับซื้อ, baht per บาททอง, baht deltas, provenance line) directly above an 'ออมทองของฉัน' card (baht value, baht gain/loss, progress bar to next สลึง); board visible pre-login.
- 2) Add a 'เริ่มออมง่าย ๆ' first-run path with the minimum stated plainly ('เริ่มเพียง 100 บาท') and a plain-Thai side-by-side of saving options (minimum, hours, how to get physical gold out, fees, lock-up) - rebuild the Siam Blockchain 6-app comparison inside the app in savings vocabulary.
- 3) Every buy/sell shows BOTH sides of the spread in baht before confirming: 'ซื้อวันนี้: จ่าย X ได้ทอง Y บาททอง (ขายออก) | ขายวันนี้: รับ Z (รับซื้อ) ต่ำกว่าที่จ่าย W เพราะส่วนต่างร้าน + ค่าเหน็จไม่คืน' - prevents the 4.6-vs-4.4-แสน wedding-gold shock documented by Sanook.
- 4) Milestone tracker with a concrete redemption checklist: when 'ครบ 1 สลึง' show 'เอาทองออกเป็นแท่งได้' with branch, documents, weight options, and any withdrawal fee/minimum - celebration yes, countdowns/urgency never.
- 5) Ship 'ทอง 101' explainer cards, one screen each, in shop analogies: บาททอง vs กรัม vs ออนซ์ (1 บาททอง = 15.244 กรัม), 96.5% vs 99.99%, ค่ากำเหน็จ, why sell-back < purchase; link every jargon term on any screen to its card.
- 6) AI cats act as a savings coach, not a trading desk: answer 'วันนี้ควรออม/ถือ/ขายดีไหม' with the board number + 3 plain reasons + 'ความเห็น ไม่ใช่คำรับประกัน'; recommend fixed-amount recurring saving over timing calls; never suggest leverage/CFD/tokenized gold to this segment.
- 7) Product-transparency card per instrument: 'ขายก่อนกำหนดได้ไหม', 'ค่าธรรมเนียมถอน', 'ขั้นต่ำถอนเป็นแท่ง', 'แลกทองจริงได้ที่ไหน'; for anything not physically redeemable show a plain warning ('ผลิตภัณฑ์นี้แลกทองจริงไม่ได้ ได้แต่มูลค่า') - protects XAUt-style products from being mistaken for savings.
- 8) Trust strip on every money screen: real-shop/bank partner badge, SEC license-check link (market.sec.or.th/LicenseCheck/Search), 'โอนเข้าบัญชีบริษัทเท่านั้น', official-store badge, and 'ไม่เชื่อ ไม่รีบ ไม่โอน' guidance; state explicitly the app never asks for OTP/recovery codes.
- 9) Replace the knowledge-graph as the default explainer with 'ทำไมราคาขยับ' (3-5 plain bullets: ค่าเงินบาท, ดอกเบี้ยสหรัฐ, ตะวันออกกลาง) and add a one-tap LINE-shareable price/progress card - word of mouth is this segment's decision channel.

**antipatterns_to_avoid**: - Trading-dashboard-first home (candlesticks, %, order book) for a segment that thinks in 'ออม' and 'สลึง'.
- Jargon on primary screens: spread, spot, oz, portfolio, DCA, leverage - and USD-denominated or unit-less numbers ('0.05' of what?).
- Hiding spread, fees, withdrawal minimums, or lock-ups until the sell/redeem moment (SafeGold-style 'cannot sell before term' discovered too late).
- Urgency/FOMO mechanics: countdown timers, 'ราคาจะขึ้น!', streaks, bonus-for-deposit - they mirror documented scam red flags and destroy this segment's trust.
- Promoting products that cannot become physical gold (tokenized/crypto gold) without a plain-Thai warning; presenting them as equivalent to 'ออมทอง'.
- Registration walls before any price is visible; multi-step onboarding before first value.
- Knowledge-graph visualization as the default explanation surface; AI predictions without the reference board price beside them.
- Percentage-only change indicators without baht deltas and units; icon-only navigation; tiny gray text; layout shifts on load.
- Pressuring family-vetted decisions: no 'act now' language that bypasses the parent/friend consultation this segment relies on.

### evidence

**sources**: - Siam Blockchain - '6 แอปออมทอง 2026 ฉบับมนุษย์เงินเดือนงบน้อยก็รวยได้ สะสมง่าย เริ่มต้นเพียงแค่ 10 บาท' (read in full: gold +70% in 2025 attracting มือใหม่; Dime min 100 baht/no fee/07:00-03:00/USD auto-convert/clumsy physical redemption; GOLD NOW ออมNow shop-direct, min 1,000, bar withdrawal only at >=1 สลึง; แม่ทองสุก MTS blockchain MGB, min 100, 24h, withdrawal minimum + fee; TrueMoney SafeGold min 100, delivery-only, no early sell; เป๋าตัง Gold Wallet bank-direct, order at -5%, min 0.1 บาททอง ~6,000+ for 96.5%, USD-only; Bitkub XAUt min 10, no physical redemption, thin liquidity) - https://siamblockchain.com/2025/12/23/6-app-for-gold-saving-in-2026/
- Google News RSS search 'ซื้อทอง มือใหม่ ครั้งแรก' (headlines consulted): TrueID 'ราคาทองพุ่งแรง ปีนี้ยังน่าลงทุนไหม มือใหม่ควรถือหรือขายดี' (22 Aug 2026); Techsauce/Workpoint/Thairath 'SCB Gold Marketplace ผนึก 3 ร้านทองยักษ์ใหญ่ ในแอปเดียว เทรดทันที ไม่มีค่าธรรมเนียม จัดส่งทองถึงบ้าน' (17 Aug 2026); Sanook 'สาวช็อก! ขายทองแต่งงาน หวังเงิน 4.6 แสน แต่ร้านให้แค่ 4.4 แสน ชาวเน็ตบอก ปกติ' (22 Mar 2026); Mitrade 'ซื้อทองร้านไหนดีสำหรับปี 2569' (13 Aug 2026) - https://news.google.com/rss/search?q=%E0%B8%8B%E0%B8%B7%E0%B9%89%E0%B8%AD%E0%B8%97%E0%B8%AD%E0%B8%87+%E0%B8%A1%E0%B8%B7%E0%B9%89%E0%B8%AD%E0%B9%83%E0%B8%AB%E0%B8%A1%E0%B9%88+%E0%B8%84%E0%B8%A3%E0%B8%B1%E0%B9%89%E0%B8%87%E0%B9%81%E0%B8%A3%E0%B8%81&hl=th&gl=TH&ceid=TH:th
- Google News RSS search 'ออมทอง แอป ทองคำออมทรัพย์' (headlines consulted): LINE TODAY 'ทองหมีเนย ยอดขายแตก 2 เดือน 2 หมื่นชิ้น ตก มัมหมี-Gen Z ลงทุนทองด้วยค่าข้าว 1 มื้อ' (25 May 2026); TrueID 'รีวิว SafeGold ใน TrueMoney เงินไม่เยอะก็เริ่มออมทองได้' (10 Jan 2026); LINE TODAY '3 แอปฯ ตัวช่วยออมทองคำ ซื้อง่ายด้วยเงินไม่ถึง 100 บาท ออมได้ทั้งวันทั้งคืน แลกเป็นทองคำแท่งก็ได้' (24 May 2025); Marketeer 'เจาะลึกแอป GOLD NOW' (6 Jun 2025); ThaiPublica 'KKP Dime x ร้านทองชื่อดัง เริ่มต้น 100 บาท ฟรีค่าธรรมเนียม' (9 Feb 2024); krungsri.com 'กรุงศรี ฮั่วเซ่งเฮง เพิ่มการลงทุนและออมทองผ่านแอป GOLD NOW' - https://news.google.com/rss/search?q=%E0%B8%AD%E0%B8%AD%E0%B8%A1%E0%B8%97%E0%B8%AD%E0%B8%87+%E0%B9%81%E0%B8%AD%E0%B8%9B+%E0%B8%97%E0%B8%AD%E0%B8%87%E0%B8%84%E0%B8%B3%E0%B8%AD%E0%B8%AD%E0%B8%A1%E0%B8%97%E0%B8%A3%E0%B8%B1%E0%B8%9E%E0%B8%A2%E0%B9%8C&hl=th&gl=TH&ceid=TH:th
- Google News RSS search 'ทองแท่ง 1 สลึง ค่ากำเหน็จ ซื้อทุกเดือน' (headlines consulted): Thansettakij daily board reports (e.g., 4 Oct 2026 ทองรูปพรรณขาย 66,950; 3 Mar 2026 แท่ง 79,450/79,650 รับซื้อ-ขายออก, intraday -600); Positioningmag/Marketeer 'Aurora x Disney ทองแผ่น Mickey & Friends เริ่ม 999 บาท เจาะคนรุ่นใหม่' (Mar 2026) - https://news.google.com/rss/search?q=%E0%B8%97%E0%B8%AD%E0%B8%87%E0%B9%81%E0%B8%97%E0%B9%88%E0%B8%87+1+%E0%B8%AA%E0%B8%A5%E0%B8%B6%E0%B8%87+%E0%B8%84%E0%B9%88%E0%B8%B2%E0%B8%81%E0%B8%B3%E0%B9%80%E0%B8%99%E0%B8%87%E0%B8%8D&hl=th&gl=TH&ceid=TH:th
- Reused verified mechanics from this project's prior research file segment_traditional_seniors.json (board reading ขายออก/รับซื้อ/ราคากลาง, 1 บาททอง = 15.244 g, ค่ากำเหน็จ non-refund, scam red flags via Thai PBS Verify https://www.thaipbs.or.th/verify/article/content/17664 and Thansettakij board explainer https://www.thansettakij.com/social-biz/670431, both read in full in that task)

**confidence**: medium - app landscape, minimums, lock-ups, redemption rules, and the sell-back spread shock are directly evidenced by one full article (Siam Blockchain) plus corroborating headlines (SCB Gold Marketplace, ทองหมีเนย micro-gold, Sanook spread story); but no dedicated study of first-time Thai gold savers was found, several corroborating items are headline-level only, and segment size/demographics remain unverified.

---

## 8. Segment: Traditional older shop customers (Thai walk-in gold-shop seniors)

*Fields marked uncertain: [uncertain] Exact prevalence/age profile of walk-in gold-shop customers with low digital literacy - no national survey on this specific segment was read this session., [uncertain] Specific font-size and tap-target recommendations (16px/18px, 44-48px) - based on general WCAG/NNg guidance, primary guideline pages not fetched this session., [uncertain] Whether leading Thai bank apps' 'elder mode' accessibility modes exist and what they include - search returned only tangential results., [uncertain] 'Yiwarat' board wording conventions beyond ขายออก/รับซื้อ/ราคากลาง (e.g., exact column labels used at Yaowarat shops) - inferred from Thansettakij's board explainer, not from a Yaowarat shop photo/source., [uncertain] Degree to which seniors (vs their children) currently use gold-price apps - only indirect evidence from family-assist news items., [uncertain] Full content of the Springnews article (Cloudflare-blocked) - relied on the identical YLG release via LINE TODAY.*

### basic_info

**item_name**: Segment: Traditional older shop customers (Thai walk-in gold-shop seniors)

**one_liner**: Thai users roughly 55-75+ whose entire gold habit was built at the physical counter - reading the Yiwarat/Chinatown-style shop price board (ป้ายราคาทอง: ราคาขายออก / ราคารับซื้อ / ราคากลาง), buying jewelry and 96.5% bars over the counter - now facing a digital dashboard with lower digital literacy, larger-font and simpler-flow needs, and strong distrust of anything that looks like the scams they read about daily.

### needs

**jobs_to_be_done**: - Know TODAY's shop price before going to the store: the Gold Traders Association (สมาคมค้าทองคำ) board they already trust - announced around 9:00 AM and re-announced many times a day (in 2026 some days saw 20-30 revisions - Thansettakij).
- Check whether the gold they bought years ago (bars, or jewelry with a craftsmanship fee / ค่ากำเหน็จ) is now worth more or less, answered in baht, in shop language: 'if I sell today, how much baht do I actually get back at the รับซื้อ price?'
- Understand a recent 'loss' without jargon: why selling back yields less than the headline price (buyback vs sell-out spread, non-refunded ค่ากำเหน็จ), i.e., a diagnosis they can verify against the shop board.
- Keep gold as family savings and inheritance (gold as a tangible, 'real' asset you hand to children), so they need to know holdings' value and where papers/receipts stand.
- Avoid being cheated: verify that any app, price number, or payment instruction is legitimate (company account, official store, licensed trader) before trusting it.
- Get calm guidance on buy/hold/sell without pressure tactics - the opposite of the countdown-timer, guaranteed-profit scams they fear.
- Do it themselves where possible, or show one clear screen to a child/grandchild who helps them (family-assisted use).

**top_questions**: - วันนี้ทองขึ้นหรือลง - ขึ้นกี่บาท? (Did gold go up or down today, and by how many baht?)
- ราคารับซื้อวันนี้กี่บาท - ถ้าขายทองที่มีอยู่วันนี้ ได้เงินเท่าไหร่เข้ามือ? (What is today's buyback price - how much cash do I actually get if I sell?)
- ทองรูปพรรณที่ซื้อไว้ขายคืนได้เท่าไหร่ - ค่ากำเหน็จได้คืนไหม? (Jewelry sell-back value - is the craftsmanship fee refunded?)
- ตัวเลขในแอปตรงกับป้ายหน้าร้าน/สมาคมค้าทองคำไหม? (Do the app's numbers match the shop board / the Association announcement?)
- ราคากลาง, ราคาขายออก, ราคารับซื้อ - อันไหนคือราคาที่ฉันจะได้จริง? (Mid price, sell-out, buyback - which one is what I actually get?)
- แอปนี้ปลอดภัยไหม - ไม่ใช่มิจฉาชีพใช่ไหม - โอนเงินเข้าบัญชีใคร? (Is this app safe - not a scam - whose account would I transfer to?)
- AI บอกให้ขายตอนนี้ - เชื่อได้แค่ไหน ใครรับผิดชอบถ้าผิด? (The AI says sell now - how much can I trust it, and who is responsible if it's wrong?)

**decision_drivers**: - The official Gold Traders Association board price (ขายออก/รับซื้อ per บาททอง) - the single reference number they cross-check everything against; they decide 'gold is up/down' from it, not from charts or percentages.
- Realized cash outcome: buyback price minus what they originally paid, including the painful fact that jewelry sells back below purchase (spread + non-refunded ค่ากำเหน็จ).
- Trust in a known physical shop and the clerk relationship - digital substitutes must visibly carry institutional backing (registered company, Association membership, SEC license).
- Scam exposure: news of fake gold-trading platforms, phishing ('หนวดกระจาย'), mule accounts, and romance-into-gold-trading scams makes them default to 'don't believe, don't rush, don't transfer' (ไม่เชื่อ ไม่รีบ ไม่โอน).
- Family opinion: children/grandchildren often act as gatekeepers who install, vet, or veto apps for them.
- Preservation instinct over returns: they buy/hold gold to keep money 'safe and real', so calm, verifiable information beats aggressive growth pitches.
- Simplicity of the moment: if doing it in the app feels risky or confusing, they fall back to walking into the shop - the app must beat 'just go to the shop' to be used at all.

### pains

**top_pains**: - Text and numbers too small; dense tables and tiny gray labels are unreadable without glasses; no text-size option in most apps.
- Too many steps and screens between opening the app and the one number they came for (logins, PINs, OTPs, menus, ads).
- Fear of pressing the wrong button and losing money - no clear confirmation, no obvious undo, unfamiliar icons without labels.
- Numbers that don't match the shop board or the Association announcement, or prices shown only in percent/dollars without baht-per-บาททอง.
- Jargon they never used at the counter: spread, spot, CFD, leverage, ounce, USD/oz, portfolio, XIRR - none of these words appear on a shop price board.
- Scam anxiety from real news: victims lured via chat into fake platforms showing portfolios 'worth hundreds of thousands' that cannot be withdrawn, then asked to pay a 50,000-baht 'bonus recovery fee' (Thai PBS Verify); fake apps demanding an extra 10-20% 'tax/fee before withdrawal' (YLG).
- Having to rely on children for registration, password resets, and interpreting English-heavy screens - feels dependent and embarrassing.
- Timid interaction budget: one mistake (or one perceived mistake) and trust in the whole app collapses; they cannot afford to experiment.

**confusion_points**: - The three board columns: ราคาขายออก (shop sells out), ราคารับซื้อ (shop buys back), ราคากลาง (mid) - which one applies to THEM depends on whether they buy or sell, and apps rarely say so in those words.
- Why the money received is less than the headline: spread between ขายออก/รับซื้อ (e.g., 22 Sep 2026 opening: bars 68,500 sold out / 68,300 bought back) plus ค่ากำเหน็จ on jewelry that is not refunded.
- Units: 1 บาททอง = 15.244 grams (bars, 96.5%), versus gram gold vs troy ounce; world price in USD/oz only maps to Thai baht per บาททอง after the THB/USD exchange rate - a double conversion nobody at the counter ever asked them to do.
- 'Gold went up today' vs 'my portfolio shows red': apps mark holdings at buyback value while shop conversation anchors on the sell-out/ราคากลาง headline, so the screen can show a loss on a day gold 'went up'.
- Charts: candlesticks, moving averages, % change badges - they know direction and baht deltas, not chart grammar.
- AI-language predictions: probability, forecast ranges, confidence - concepts with no counter equivalent; also who is 'the AI' and why its advice should be trusted.
- Security rituals: OTP, recovery codes, 'never share screenshots' - rules they half-know from scam warnings but can't map to app screens.
- Knowledge-graph style visualizations: nodes and links read as decoration or confusion, not information.

**trust_barriers**: - Anything resembling documented scam patterns: guaranteed returns ('profit 10-20% per day'), countdown pressure ('within 15 minutes', 'within 24 hours'), bonuses that must be repaid/deposited more to unlock (Thai PBS Verify red flags 2-4).
- Payment to personal-name accounts (บัญชีม้า/mule accounts) or odd company names instead of a clearly registered company (YLG check #4).
- App distribution outside official stores - forwarded LINE links, .APK files, lookalike web pages (YLG check #3) - triggers immediate suspicion.
- Withdrawal friction: 'must transfer extra 10-20% as tax/fee before you can withdraw' is read as 100% scammer (YLG check #1); any prepayment-to-withdraw language is the strongest red flag.
- Lack of verifiable identity: no visible company registration, no Gold Traders Association membership, no SEC license check (market.sec.or.th/LicenseCheck/Search) - unverifiable platforms should be presumed scam (YLG check #2).
- Black-box AI: advice without reasons, no source numbers, no way to verify against the board; predictions that cannot be held accountable feel like the 'guaranteed profit' hook.
- Language mismatch: English menus and finance jargon read as 'made by outsiders', increasing scam feel and error risk.
- Requesting OTPs, recovery codes, or full ID photos without clear explanation - exactly the behaviors scam warnings tell them to refuse.

### ux

**must_have_first_screen**: - A shop-format price board as the hero: four big numbers in shop vocabulary - ทองแท่ง (bars): ขายออก / รับซื้อ, ทองรูปพรรณ (jewelry): ขายออก / รับซื้อ - in baht per บาททอง, with up/down arrows and the baht delta, not just percentages.
- A visible provenance line: 'ราคา 9:30 น. - อ้างอิงประกาศสมาคมค้าทองคำ' (price at 9:30 AM per the Gold Traders Association announcement) with refresh time - the same provenance they trust at the shop.
- 'ทองของฉัน' (My gold) summary right under the board: current buyback value of their holdings, up/down since purchase IN BAHT, split bars vs jewelry.
- One prominent, clearly worded safe-harbor strip: 'ไม่มีค่าธรรมเนียมก่อนถอน - โอนเข้าบัญชีบริษัทเท่านั้น' (no pre-withdrawal fees; transfers only to the registered company account).
- Large 'ใหญ่ตัวอักษร' text-size control and a labeled ผู้ช่วย (assistant) entry point - no login wall before the board is visible.

**workflow_preferences**: - Browse first, register never/last: the price board and portfolio estimate must be visible without an account; if registration is unavoidable, walk through it one screen at a time with plain-Thai labels.
- One task per screen, forward-only flows with big 'ยืนยัน / ยกเลิก' buttons; no nested menus, no hidden swipe actions, no icon-only navigation.
- Phone-first, single-hand, portrait; few huge tap targets; minimal typing (no mandatory complex passwords; support biometrics/PIN once set up).
- Family-assisted mode: screens that are self-explanatory enough to hand to a child - clear 'what will happen next' preview before every irreversible action.
- Plain-Thai push notifications they can trust: 'ทองขึ้น 50 บาท - ราคารับซื้อตอนนี้ 68,300' rather than alert-style percentage spam.
- Search or a short list beats a graph: if they want 'why did the price move', give 3-5 plain bullets, not a node diagram.
- Any sell/transfer journey must show the destination (shop price, account name, fee) BEFORE confirming - mirroring the counter habit of asking the clerk 'ถ้าขายวันนี้ได้เท่าไหร่' first.

**language_and_tone**: - Plain everyday Thai exactly as spoken in gold shops: ทองขึ้น/ทองลง, ขายออก, รับซื้อ, บาททอง, ค่ากำเหน็จ - reuse the counter vocabulary; it IS the correct design language for this segment.
- Avoid or gloss all loanword finance jargon: no 'spread', 'spot', 'CFD', 'leverage', 'portfolio' on primary screens; if needed once, explain with a counter analogy in parentheses.
- Baht-first numbers: '68,300 บาท ต่อ บาททอง' with commas; baht deltas ('ขึ้น 50 บาท') before or instead of percentages; always state the unit (บาททอง vs กรัม vs ออนซ์).
- Short sentences, one idea per line, generous line spacing; polite, respectful, calm tone (neutral polite particles) - never playful urgency, never FOMO phrasing.
- Frame AI output as a humble opinion tied to visible numbers: 'ความเห็นผู้ช่วย ไม่ใช่คำรับประกัน' (assistant's opinion, not a guarantee), always shown next to the official board number so it can be checked.
- Buttons in verb form and consequence-bearing: 'ดูราคารับซื้อวันนี้', 'ขายทอง - ตรวจสอบก่อนยืนยัน'.

**accessibility_notes**: - Font floor: body/labels ~16px minimum with a user-facing text-size control up to roughly 200% (WCAG 1.4.4 resize-text); for this segment prefer 18px+ for body and 24-32px for board numbers. [uncertain: exact px recommendations are from general WCAG/NNg guidance, not re-verified from primary pages this session]
- High contrast pairs (dark text on light ground), no meaning by color alone: up/down shown with arrows + words ('ขึ้น/ลง') in color-blind-safe green/red - supports WCAG 1.4.1 use-of-color. [uncertain: WCAG clause numbers not re-verified this session]
- Tap targets large (~44-48px) and separated; no hover-only interactions; one-hand reachable primary buttons at bottom of screen.
- Icons always paired with Thai text labels; no icon-only navigation; avoid tiny date tables - prefer 3-5 bullet summary.
- Reduce motion, no auto-playing carousels; stable layouts (nothing shifts after load) - sudden movement reads as 'something is wrong/scam'.
- Consider read-aloud or simplified mode for weakest users; Thai fonts must render clearly at large sizes (avoid stylized display fonts for numbers).

### design

**implications_for_gold_assistant**: - 1) Home screen = shop price board, not a dashboard: replicate the 4-number board layout (ทองแท่ง ขายออก/รับซื้อ, ทองรูปพรรณ ขายออก/รับซื้อ) in baht per บาททอง with arrows + baht deltas, plus a provenance line 'อ้างอิงสมาคมค้าทองคำ เวลา ...' and a big refresh button.
- 2) 'ทองของฉัน' card directly under the board: current รับซื้อ-based value in baht, gain/loss since purchase in baht (and since when), bars vs jewelry split; percentages secondary and always paired with baht.
- 3) Font floor + text-size control: 18px+ body, 24-32px board numbers, persistent 'ตัวหนังสือใหญ่' toggle (A / A+ / A++) on every screen; 44-48px tap targets; icons always with Thai labels.
- 4) Plain-Thai label system: sub-label every board term once ('รับซื้อ = ราคาที่ร้านซื้อจากคุณ'; 'ขายออก = ราคาที่ร้านขายให้คุณ'); globally ban spread/spot/CFD/leverage from primary screens - the loss-explainer uses them only after plain-Thai summary.
- 5) Loss diagnosis in counter language: 'ถ้าขายวันนี้ รับเงิน X บาท ต่ำกว่าที่ซื้อ Y บาท เพราะ: (1) ราคารับซื้อต่ำกว่าราคาขายออก Z บาท (2) ทองรูปพรรณ ค่ากำเหน็จไม่ได้คืน' - one reason per line, each mapped to the board numbers, replacing any knowledge-graph or jargon explanation on this segment's path.
- 6) Scam-safety signals built in: a permanent trust strip ('โอนเข้าบัญชีบริษัทเท่านั้น', 'ไม่มีค่าธรรมเนียมก่อนถอน', official App Store/Play Store badge), a 'ตรวจสอบก่อนเชื่อ' page linking the SEC license check (market.sec.or.th/LicenseCheck/Search) and Gold Traders Association membership, and the 'ไม่เชื่อ ไม่รีบ ไม่โอน' motto; never ask OTP/recovery codes in-app, and say so explicitly.
- 7) Fewer steps: no login wall before the board; max ~3 taps to any core answer (price, my value, sell estimate); every irreversible action gets a full-screen plain-Thai confirmation with big ยืนยัน/ยกเลิก and a 'what happens next' preview; support family-assist (hand the phone to a child) with self-explanatory screens.
- 8) Tone-guard the AI cats: keep cats as warm optional guides, but cap persona chattiness; every AI claim sits beside the official board number and is labeled 'ความเห็น ไม่ใช่คำรับประกัน'; no countdown timers, no bonus/reward language anywhere near this segment's flows.
- 9) Replace the knowledge graph with 'ทำไมราคาขยับ' - 3-5 plain bullets (ค่าเงินบาทแข็งขึ้น / ดอกเบี้ยสหรัฐ / ตะวันออกกลาง) per Thansettakij's framing; keep the graph behind an 'advanced' entry for other segments.

**antipatterns_to_avoid**: - Dashboard-first design: charts, candles, or % badges as the hero instead of the shop-board numbers.
- English/jargon labels on primary screens (Spot, CFD, Spread, Leverage, Portfolio) or unexplained 'ราคากลาง' without saying which price applies when YOU buy vs sell.
- Percentage-only change indicators without baht deltas and units.
- Urgency mechanics of any kind: countdown timers, 'limited offer', bonus-for-deposit, streaks - they mirror documented scam red flags (Thai PBS Verify, YLG).
- Payment/transfer flows to personal-name accounts, or any prepayment-to-unlock/withdraw step - instant, justified distrust.
- APK/sideload prompts, LINE-forwarded install links, or app-store bypass - reads as scam distribution (YLG check #3).
- Asking for OTP, recovery codes, or ID photos without an explicit reason screen.
- Login/registration walls hiding the price board; multi-step onboarding before first value.
- Icon-only navigation, tiny gray text, dense multi-column tables, hover-dependent UI, layout shifts.
- Knowledge-graph visualization as the default explanation surface for this segment; AI predictions shown without the reference price beside them.

### evidence

**sources**: - Thai PBS Verify - '5 ธงเเดง สัญญาณหลอกลวงจากแพลตฟอร์มเทรดทองปลอม' (5 red flags of fake gold-trading platforms; victim story, red-flag list, SEC license check, 'ไม่เชื่อ ไม่รีบ ไม่โอน') - https://www.thaipbs.or.th/verify/article/content/17664 (read in full)
- Thansettakij / ฐานเศษตรกิจ - 'ราคาทองวันนี้ขยับเพราะอะไร เปิดที่มาป้ายราคาทอง ก่อนตัดสินใจซื้อ-ขาย' (Gold Association ~9AM announcements, 20-30 revisions/day in 2026, board reading: ขายออก/รับซื้อ/ค่ากำเหน็จ, 1 บาททอง = 15.244g, example 68,500/68,300, THB/USD + US rates drivers) - https://www.thansettakij.com/social-biz/670431 (read in full)
- LINE TODAY (YLG via การเงินธนาคาร) - 'YLG เปิด 5 จุดสังเกต แอปฯเทรดทองของแท้ VS มิจฉาชีพ' (withdrawal-conditions test, Gold Traders Association membership check, official-store-only installs, company-name accounts, no guaranteed returns) - https://today.line.me/th/v3/article/2D7WQZe (read in full)
- Springnews - 'จุดสังเกต แอปฯเทรดทองคำ ของแท้ เทียบ แอปฯมิจฉาชีพ' - https://www.springnews.co.th/news/hot-issue/861954 (URL/title consulted; page Cloudflare-blocked, content taken from LINE TODAY version of same YLG release)
- Google News RSS searches consulted (titles/heads only): 'ผู้สูงอายุ แอปธนาคาร ปัญหา ใช้ยาก' (Thai PBS พม.CARE online-registration walk-through; Facebook 'เช็กเบี้ยคนชรา แอปทางรัฐ' family-assist pattern; Thairath bank mule-account warnings) and 'ออกแบบแอปพลิเคชัน สำหรับผู้สูงอายุ UX' (ThaiPublica 'วิจัยกรุงศรี: สังคมสูงวัย Silver Economy'; VNurse native app for elderly care) - https://news.google.com/rss/search?q=%E0%B8%9C%E0%B8%B9%E0%B9%89%E0%B8%AA%E0%B8%B9%E0%B8%87%E0%B8%AD%E0%B8%B2%E0%B8%A2%E0%B8%B8+%E0%B9%81%E0%B8%AD%E0%B8%9B%E0%B8%98%E0%B8%99%E0%B8%B2%E0%B8%84%E0%B8%B2%E0%B8%A3+%E0%B8%9B%E0%B8%B1%E0%B8%8D%E0%B8%AB%E0%B8%B2+%E0%B9%83%E0%B8%8A%E0%B9%89%E0%B8%A2%E0%B8%B2%E0%B8%81&hl=th&gl=TH&ceid=TH:th
- Google News RSS search 'อ่านป้ายราคาทอง ราคากลาง ราคาขายออก ราคารับซื้อ' and 'แชร์ทองคำ หลอกลวง มิจฉาชีพ' (Thai PBS fake-platform red flags; CH3Plus 1.5M-baht gold-savings fraud report; MOE 'รักออนไลน์ ชวนเทรดทอง' romance-scam explainer; ฮั่วเซ่งเฮง scam-warning page) - https://news.google.com/rss/search?q=%E0%B9%81%E0%B8%8A%E0%B8%A3%E0%B9%8C%E0%B8%97%E0%B8%AD%E0%B8%87%E0%B8%84%E0%B8%B3+%E0%B8%AB%E0%B8%A5%E0%B8%AD%E0%B8%81%E0%B8%A5%E0%B8%A7%E0%B8%87&hl=th&gl=TH&ceid=TH:th

**confidence**: medium - scam-pattern and price-board mechanics are directly evidenced by three full Thai articles read this session (Thai PBS Verify, Thansettakij, LINE TODAY/YLG); the senior-UX specifics (font floors, tap sizes) rest on general WCAG/NNg guidance not re-verified from primary pages this session, and segment behaviors (family-assist, counter habits) are triangulated from news and standard practice rather than a dedicated senior-gold-customer study.

---
