---
theme: "dataminded"
title: "AI Engineering Capstone"
info: "Why the capstone exists, what teams build during the day and how the final challenge works"
fonts: {"serif":"El Messiri","sans":"DM Sans"}
transition: "slide-left"
layout: "cover"
subtitle: "AI Engineering Capstone · Dataminded Academy"
---

# A <span class="dm-accent">dark factory</span> for data products

<!--
Open with the image: a factory that runs with the lights off because nobody is on the floor.
Today every team builds one where the product is a data product.
-->

---
layout: "default"
label: "The idea"
---

# A line of agents that builds data products

A stakeholder at Fernhill Outfitters files a GitHub issue. A line of agents turns it into tested dbt models and a dashboard, with no human in the loop.

<DmProcess class="line">
  <DmPhase label="Issue" />
  <DmPhase label="Intake" />
  <DmPhase label="Implement" />
  <DmPhase label="Review" />
  <DmPhase label="Governance" />
  <DmPhase label="BI" />
</DmProcess>

<p class="line-note">Review and governance can send work back to implement for one rework round.</p>

<DmColumns :gap="28">
  <DmColumn header="Contracts" tone="plain">
    Every hand-off is a file with a schema: <code>spec.yaml</code>, dbt models, <code>review.json</code>, a board. Stations change, the line still fits together.
  </DmColumn>
  <DmColumn header="Baseline agents" tone="plain" divider>
    Every station already works, but on purpose with short prompts, no skills and a small model. Most of the points are still on the table.
  </DmColumn>
  <DmColumn header="Benchmark" tone="plain" divider>
    Every station has graders and seed cases, so a change to an agent turns into a score, a cost and a number of turns.
  </DmColumn>
</DmColumns>

<style>
.line { margin: 24px 0 8px; }
.line-note { font-size: 15px; opacity: 0.7; margin: 0 0 28px; }
</style>

<!--
Walk the line from left to right. Intake writes an executable spec, implement writes dbt models,
review and governance check them, BI builds the dashboard.
The three columns are why one day is enough: the plumbing is done, teams spend their time on the agents.
-->

---
layout: "default"
label: "Your day"
---

# Your team builds up its own factory

Each team forks the repository and owns the whole line. Each person or pair takes one station; the stations nobody owns run on their baseline.

<DmProcess class="blocks">
  <DmPhase label="1 · Agno agent" />
  <DmPhase label="2 · Skills" />
  <DmPhase label="3 · MCP" />
  <DmPhase label="4 · Benchmark" />
  <DmPhase label="5 · Improve" />
</DmProcess>

<div class="block-notes">
  <p>Rebuild a station as your own Agno agent and read the trace of its first run.</p>
  <p>Write down what the traces taught you: Fernhill's business rules, dbt on DuckDB.</p>
  <p>Connect the dbt charts MCP server, or write your own tool.</p>
  <p>Add three cases of your own, from failures you saw that morning.</p>
  <p>Use your benchmark to find where the points are. Measure every change.</p>
</div>

<style>
.blocks { margin-top: 28px; }
.blocks .dm-phase { font-size: 16px; }
.block-notes { display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-top: 18px; }
.block-notes p { margin: 0; font-size: 15px; line-height: 1.4; }
</style>

<!--
One block per topic of the week, each with a checkpoint a facilitator ticks off.
Stress "one change at a time": without it nobody can say what actually helped.
Hand out interviews.md at the kick-off: it holds the company know-how no agent can find in the data.
-->

---
layout: "default"
label: "The final"
---

# The final: a request nobody has seen

<DmColumns :gap="44">
  <DmColumn>
    <p>At 16:00 the organisers open a new GitHub issue. Every team's factory builds it in the same CI pipeline, unattended, within 45 minutes.</p>
    <p>The request is about a part of the warehouse the public products hardly use. Only a factory that learned how Fernhill's data works will get the numbers right.</p>
    <p>An automated benchmark scores every product and picks the winner.</p>
  </DmColumn>
  <DmColumn header="How the product is scored" tone="plain">
    <div class="score">
      <span>Correctness</span><div><i style="width: 100%"></i></div><b>50</b>
      <span>Efficiency</span><div><i style="width: 30%"></i></div><b>15</b>
      <span>Governance</span><div><i style="width: 20%"></i></div><b>10</b>
      <span>Dashboard</span><div><i style="width: 20%"></i></div><b>10</b>
      <span>Own benchmark</span><div><i style="width: 20%"></i></div><b>10</b>
      <span>Interface</span><div><i style="width: 10%"></i></div><b>5</b>
    </div>
    <p class="score-note">A well-governed product with wrong numbers is still wrong.</p>
  </DmColumn>
</DmColumns>

<style>
.score { display: grid; grid-template-columns: 120px 1fr 28px; gap: 10px 12px; align-items: center; }
.score span { font-size: 15px; }
.score div { height: 14px; background: var(--dm-surface); border-radius: 3px; }
.score i { display: block; height: 100%; background: var(--dm-connecting); border-radius: 3px; }
.score b { font-size: 15px; text-align: right; color: var(--dm-premium); }
.score-note { margin-top: 18px !important; font-size: 14px; opacity: 0.7; }
</style>

<!--
This is the purpose of the day: not the best prompt for a known case, but a factory that generalises.
Correctness weighs half on purpose. Efficiency only counts as far as the product is correct.
After the final each team tells the change that mattered most, one thing that did not work,
and how well their own benchmark predicted their final score.
-->
