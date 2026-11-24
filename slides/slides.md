---
theme: "dataminded"
title: "AI Engineering Capstone"
info: "Why the capstone exists, what teams build during the day and how the final challenge works"
fonts: {"serif":"El Messiri","sans":"DM Sans"}
transition: "fade-out"
layout: "cover"
subtitle: "AI Engineering Capstone · Dataminded Academy"
---

<div v-motion :initial="{ y: 30, opacity: 0 }" :enter="{ y: 0, opacity: 1, transition: { duration: 900 } }">
  <div class="eyebrow"><span class="i-mdi-lightbulb-off-outline" /> Lights out, nobody on the floor</div>
</div>

<h1 v-motion :initial="{ y: 40, opacity: 0 }" :enter="{ y: 0, opacity: 1, transition: { delay: 250, duration: 900 } }">A <span class="dm-accent">dark factory</span> for data products</h1>

<style>
.eyebrow { display: inline-flex; align-items: center; gap: 10px; font-size: 15px; letter-spacing: 0.14em; text-transform: uppercase; color: #b3a7f2; margin-bottom: 22px; }
.eyebrow span { width: 20px; height: 20px; }
</style>

<!--
Open with the image: a factory that runs with the lights off because nobody is on the floor.
Today every team builds one where the product is a data product.
-->

---
layout: "dark"
label: "The idea"
bg: "stream-violet"
---

# A line of agents that builds data products

<p class="lead">A stakeholder at Fernhill Outfitters files a GitHub issue. Agents turn it into tested dbt models and a dashboard. No human in the loop.</p>

<FactoryLine class="line" />

<div class="pillars">
  <div v-click class="pillar">
    <span class="i-mdi-file-document-check-outline" />
    <div><b>Contracts</b><p>Every hand-off is a file with a schema, so the stations fit together.</p></div>
  </div>
  <div v-click class="pillar">
    <span class="i-mdi-robot-outline" />
    <div><b>Plain baselines</b><p>Every station works, on purpose with short prompts and a small model.</p></div>
  </div>
  <div v-click class="pillar">
    <span class="i-mdi-target-arrow" />
    <div><b>A benchmark</b><p>Every change to an agent becomes a score, a cost and a number of turns.</p></div>
  </div>
</div>

<style>
.lead { color: #e9edff; font-size: 18px; max-width: 760px; margin: 14px 0 18px; }
.line { margin: 6px 0 34px; }
.pillars { display: grid; grid-template-columns: repeat(3, 1fr); gap: 18px; }
.pillar { display: flex; gap: 14px; align-items: flex-start; padding: 14px 16px; border-radius: 14px; background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(179, 167, 242, 0.25); backdrop-filter: blur(4px); }
.pillar > span { flex: none; width: 30px; height: 30px; color: #8f7bff; }
.pillar b { color: #fff; font-size: 16px; }
.pillar p { margin: 4px 0 0; font-size: 13.5px; line-height: 1.4; color: #cacdf9; }
.slidev-vclick-target { transition: opacity 0.5s ease, transform 0.5s ease; }
.slidev-vclick-hidden { transform: translateY(16px); }
</style>

<!--
Let the animation run for a moment: the request travels through the line and each station lights up.
Intake writes an executable spec, implement writes dbt models, review and governance check them
and can send work back once, BI builds the dashboard.
Then click in the three pillars: they are why one day is enough. The plumbing is done.
-->

---
layout: "default"
label: "Your day"
---

# Your team builds up its own factory

<p class="intro">Fork the repository, own the whole line. One station per person or pair; the rest runs on its baseline.</p>

<div class="blocks">
  <div v-click="1" class="block">
    <div class="tile"><span class="i-mdi-robot-happy-outline" /></div>
    <div class="time">09:30</div>
    <b>Agno agent</b>
    <p>Rebuild a station as your own agent and read its first trace.</p>
  </div>
  <div v-click="2" class="block">
    <div class="tile"><span class="i-mdi-book-open-page-variant-outline" /></div>
    <div class="time">10:45</div>
    <b>Skills</b>
    <p>Teach it what the traces showed: Fernhill's business rules.</p>
  </div>
  <div v-click="3" class="block">
    <div class="tile"><span class="i-mdi-power-plug-outline" /></div>
    <div class="time">11:30</div>
    <b>MCP</b>
    <p>Connect the dbt charts MCP server, or write your own tool.</p>
  </div>
  <div v-click="4" class="block">
    <div class="tile"><span class="i-mdi-flask-outline" /></div>
    <div class="time">13:15</div>
    <b>Benchmark</b>
    <p>Add three cases of your own, from the failures you saw.</p>
  </div>
  <div v-click="5" class="block">
    <div class="tile"><span class="i-mdi-chart-line-variant" /></div>
    <div class="time">14:15</div>
    <b>Improve</b>
    <p>Follow the points. Measure every change, revert what fails.</p>
  </div>
</div>

<div class="day">
  <div class="day-bar"><div class="day-fill" :style="{ width: `${Math.min($clicks, 5) * 17.6}%` }" /></div>
  <div class="day-end" :class="{ on: $clicks >= 5 }"><span class="i-mdi-trophy-outline" /> 16:00 final</div>
</div>

<style>
.intro { font-size: 17px; margin: -4px 0 34px; }
.blocks { display: grid; grid-template-columns: repeat(5, 1fr); gap: 16px; }
.block { position: relative; background: var(--dm-surface); border-radius: 16px; padding: 18px 16px 16px; }
.block b { display: block; font-size: 17px; color: var(--dm-premium); margin-top: 4px; }
.block p { font-size: 13.5px; line-height: 1.4; margin: 6px 0 0; color: #3a3a44; }
.tile { width: 54px; height: 54px; border-radius: 14px; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #543edc, #ba3ddb); box-shadow: 0 10px 22px rgba(84, 62, 220, 0.35); margin-bottom: 12px; }
.tile span { width: 30px; height: 30px; color: #fff; }
.time { position: absolute; top: 18px; right: 16px; font-size: 13px; font-weight: 600; color: var(--dm-connecting); }
.day { display: flex; align-items: center; gap: 16px; margin-top: 44px; }
.day-bar { flex: 1; height: 8px; border-radius: 4px; background: var(--dm-surface); overflow: hidden; }
.day-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #543edc, #ba3ddb); transition: width 0.7s ease; }
.day-end { display: flex; align-items: center; gap: 6px; font-weight: 700; font-size: 15px; color: #b6b6c2; transition: color 0.4s; }
.day-end span { width: 22px; height: 22px; }
.day-end.on { color: var(--dm-connecting); }
.slidev-vclick-target { transition: opacity 0.5s ease, transform 0.5s ease; }
.slidev-vclick-hidden { transform: translateY(24px); }
</style>

<!--
Click through the five blocks: one per topic of the week, each with a checkpoint a facilitator ticks off.
The bar fills up towards the final at 16:00.
Hand out interviews.md at the kick-off: it holds the company know-how no agent can find in the data.
-->

---
layout: "dark"
label: "The final"
bg: "section"
---

# The final: a request nobody has seen

<div class="final">
  <div class="final-left">
    <ScoreClock />
    <div class="facts">
      <div v-click="1"><span class="i-mdi-github" /> A new issue, opened at 16:00</div>
      <div v-click="2"><span class="i-mdi-factory" /> Every team's factory, the same CI pipeline</div>
      <div v-click="3"><span class="i-mdi-account-off-outline" /> One run, unattended, no reruns</div>
    </div>
  </div>
  <div v-click="4" class="final-right">
    <div class="score-title">How the product is scored</div>
    <div class="score">
      <span>Correctness</span><div><i style="--w: 100%" class="hot" /></div><b>50</b>
      <span>Efficiency</span><div><i style="--w: 30%" /></div><b>15</b>
      <span>Governance</span><div><i style="--w: 20%" /></div><b>10</b>
      <span>Dashboard</span><div><i style="--w: 20%" /></div><b>10</b>
      <span>Own benchmark</span><div><i style="--w: 20%" /></div><b>10</b>
      <span>Interface</span><div><i style="--w: 10%" /></div><b>5</b>
    </div>
    <p class="score-note">The request uses data the public products hardly touch. Only a factory that learned how Fernhill's data works gets the numbers right.</p>
  </div>
</div>

<style>
.final { display: grid; grid-template-columns: 0.9fr 1.1fr; gap: 48px; margin-top: 8px; }
.final-left { display: flex; flex-direction: column; gap: 22px; }
.facts { display: flex; flex-direction: column; gap: 12px; }
.facts div { display: flex; align-items: center; gap: 12px; font-size: 16px; color: #e9edff; }
.facts span { flex: none; width: 24px; height: 24px; color: #8f7bff; }
.final-right { background: rgba(255, 255, 255, 0.06); border: 1px solid rgba(179, 167, 242, 0.25); border-radius: 18px; padding: 22px 24px; backdrop-filter: blur(4px); }
.score-title { font-size: 13px; letter-spacing: 0.14em; text-transform: uppercase; color: #b3a7f2; margin-bottom: 16px; }
.score { display: grid; grid-template-columns: 118px 1fr 28px; gap: 12px 12px; align-items: center; }
.score span { font-size: 15px; color: #fff; }
.score div { height: 12px; background: rgba(179, 167, 242, 0.15); border-radius: 6px; overflow: hidden; }
.score i { display: block; height: 100%; width: var(--w); border-radius: 6px; background: linear-gradient(90deg, #543edc, #8f7bff); transition: width 1.1s cubic-bezier(0.2, 0.8, 0.2, 1); }
.score i.hot { background: linear-gradient(90deg, #543edc, #ba3ddb, #fc6b51); box-shadow: 0 0 16px rgba(186, 61, 219, 0.6); }
.final-right.slidev-vclick-hidden .score i { width: 0; }
.score b { font-size: 15px; text-align: right; color: #fff; }
.score-note { margin: 18px 0 0; font-size: 13.5px; line-height: 1.45; color: #cacdf9; }
</style>

<!--
This is the purpose of the day: not the best prompt for a known case, but a factory that generalises.
Click in the facts, then the scoring: the bars grow in. Correctness weighs half on purpose,
and efficiency only counts as far as the product is correct.
After the final each team tells the change that mattered most, one thing that did not work,
and how well their own benchmark predicted their final score.
-->
