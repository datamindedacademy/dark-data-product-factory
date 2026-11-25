---
theme: ./theme
title: Dark data product factory
layout: cover
tag: 'Kick-off'
date: AI Academy
---

# Dark data product factory

Capstone · AI Engineering Bootcamp

<p style="margin-top: 2.2rem; max-width: 30rem; font-size: 1.35rem; line-height: 1.45; color: #fff">A line of agents that builds data products, with nobody in the loop</p>

<!--
A dark factory runs with the lights off, because nobody is on the floor. Today every team builds one, and the product is a data product.
-->

---
layout: default
tag: 'The idea'
clicks: 3
---

# A line of agents builds the product

<svg class="dg" viewBox="0 0 860 340" style="margin-top: 0.2rem">
  <defs>
    <marker id="arr-02" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#080635"/></marker>
    <marker id="arr-02s" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#543edc"/></marker>
  </defs>
  <!-- the request -->
    <g class="dg-node">
      <rect x="0" y="122" width="112" height="56" rx="3"/>
      <text x="12" y="143" class="dg-cap">REQUEST</text>
      <text x="12" y="164" style="font-size: 15px; font-weight: 700">GitHub issue</text>
    </g>
  <!-- the stations: review and governance run side by side -->
  <g v-click="1">
    <g class="dg-line" style="fill: none">
      <path d="M112 150 H140" marker-end="url(#arr-02)"/>
      <path d="M256 150 H284" marker-end="url(#arr-02)"/>
      <path d="M400 150 C 416 150, 414 114, 428 114" marker-end="url(#arr-02)"/>
      <path d="M400 150 C 416 150, 414 186, 428 186" marker-end="url(#arr-02)"/>
      <path d="M544 114 C 560 114, 558 150, 572 150" marker-end="url(#arr-02)"/>
      <path d="M544 186 C 560 186, 558 150, 572 150"/>
      <path d="M688 150 H716" marker-end="url(#arr-02)"/>
    </g>
    <g class="dg-solid">
      <rect x="144" y="122" width="112" height="56" rx="3"/>
      <text x="156" y="143" class="dg-cap">INTAKE</text>
      <text x="156" y="164" style="font-size: 13px">spec.yaml</text>
    </g>
    <foreignObject x="230" y="150" width="22" height="22"><span class="i-ph-clipboard-text-bold" style="display: block; font-size: 20px; color: #b3a7f2" /></foreignObject>
    <g class="dg-solid">
      <rect x="288" y="122" width="112" height="56" rx="3"/>
      <text x="300" y="143" class="dg-cap">IMPLEMENT</text>
      <text x="300" y="164" style="font-size: 13px">dbt models</text>
    </g>
    <foreignObject x="374" y="150" width="22" height="22"><span class="i-ph-database-bold" style="display: block; font-size: 20px; color: #b3a7f2" /></foreignObject>
    <g class="dg-solid">
      <rect x="432" y="86" width="112" height="56" rx="3"/>
      <text x="444" y="107" class="dg-cap">REVIEW</text>
      <text x="444" y="128" style="font-size: 13px">findings</text>
    </g>
    <foreignObject x="518" y="114" width="22" height="22"><span class="i-ph-magnifying-glass-bold" style="display: block; font-size: 20px; color: #b3a7f2" /></foreignObject>
    <g class="dg-solid">
      <rect x="432" y="158" width="112" height="56" rx="3"/>
      <text x="444" y="179" class="dg-cap">GOVERNANCE</text>
      <text x="444" y="200" style="font-size: 13px">checkup</text>
    </g>
    <foreignObject x="518" y="186" width="22" height="22"><span class="i-ph-shield-check-bold" style="display: block; font-size: 20px; color: #b3a7f2" /></foreignObject>
    <g class="dg-solid">
      <rect x="576" y="122" width="112" height="56" rx="3"/>
      <text x="588" y="143" class="dg-cap">BI</text>
      <text x="588" y="164" style="font-size: 13px">dashboard</text>
    </g>
    <foreignObject x="662" y="150" width="22" height="22"><span class="i-ph-chart-bar-bold" style="display: block; font-size: 20px; color: #b3a7f2" /></foreignObject>
    <g class="dg-node">
      <rect x="720" y="122" width="140" height="56" rx="3"/>
      <text x="732" y="143" class="dg-cap">DELIVERED</text>
      <text x="732" y="164" style="font-size: 15px; font-weight: 700">data product</text>
    </g>
  </g>
  <!-- the rework loop -->
  <g v-click="2">
    <path d="M488 86 C 488 40, 344 40, 344 116" class="dg-line-soft" marker-end="url(#arr-02s)"/>
    <path d="M488 214 C 488 260, 344 260, 344 184" class="dg-line-soft" marker-end="url(#arr-02s)"/>
    <text x="416" y="34" text-anchor="middle" class="dg-cap">REWORK, ONCE</text>
  </g>
  <!-- what makes the time enough -->
  <g v-click="3">
    <g v-for="(c, i) in [['CONTRACTS', 'every hand-off is a file with a schema'], ['BASELINES', 'every station already works, plainly'], ['BENCHMARK', 'every change becomes a score']]" :key="c[0]">
      <rect :x="i * 292" y="276" width="276" height="62" rx="3" style="fill: #f2f2f4"/>
      <text :x="16 + i * 292" y="299" class="dg-cap">{{ c[0] }}</text>
      <text :x="16 + i * 292" y="321" style="font-size: 14px">{{ c[1] }}</text>
    </g>
  </g>
</svg>

<!--
A stakeholder at Fernhill Outfitters, our invented outdoor-gear retailer, files a GitHub issue.

[click] Five agents turn it into a data product. Intake writes an executable spec and implement writes the dbt models. Review and governance check them at the same time, then BI builds the dashboard.

[click] Review and governance can send the work back to implement once.

[click] Three things make a day and a half enough. Every hand-off is a file with a schema, so the stations fit together. Every station has a working baseline agent, plain on purpose. And a benchmark turns every change to an agent into a score, a cost and a number of turns.
-->

---
layout: default
tag: 'Your day'
clicks: 5
---

# Your team builds up its own factory

<svg class="dg" viewBox="0 0 860 330" style="margin-top: 0.6rem">
  <!-- two half days, the night in between -->
  <path d="M0 90 H328" class="dg-line"/>
  <path d="M344 90 H860" class="dg-line"/>
  <text x="0" y="64" class="dg-cap">THURSDAY AFTERNOON</text>
  <text x="344" y="64" class="dg-cap">FRIDAY</text>
  <circle cx="0" cy="90" r="5" style="fill: #080635"/>
  <circle cx="344" cy="90" r="5" style="fill: #080635"/>
  <circle cx="852" cy="90" r="7" :style="{ fill: $clicks >= 5 ? '#543edc' : '#b4b2c6', transition: 'fill 0.3s' }"/>
  <text x="860" y="64" text-anchor="end" :style="{ fontSize: '15px', fontWeight: 700, fill: $clicks >= 5 ? '#543edc' : '#8a88a3', transition: 'fill 0.3s' }">final, done by 14:00</text>
  <!-- the five blocks -->
  <g v-for="(b, i) in [['An Agno agent', 'Rebuild a station', 'as your own agent.'], ['Skills', 'Teach it Fernhill’s', 'business rules.'], ['MCP', 'Connect a server,', 'or write your own.'], ['A benchmark', 'Three cases from', 'the failures you saw.'], ['Improve', 'Measure every change,', 'revert what fails.']]" :key="b[0]" v-click="i + 1">
    <circle :cx="78 + i * 172" cy="90" r="5" style="fill: #543edc"/>
    <path :d="`M${78 + i * 172} 96 V128`" class="dg-line-soft"/>
    <g class="dg-node">
      <rect :x="0 + i * 172" y="132" width="156" height="122" rx="3"/>
    </g>
    <text :x="12 + i * 172" y="156" class="dg-cap">BLOCK {{ i + 1 }}</text>
    <text :x="12 + i * 172" y="182" style="font-size: 16px; font-weight: 700">{{ b[0] }}</text>
    <text :x="12 + i * 172" y="212" class="dg-note" style="font-size: 13px">{{ b[1] }}</text>
    <text :x="12 + i * 172" y="230" class="dg-note" style="font-size: 13px">{{ b[2] }}</text>
  </g>
  <text x="0" y="300" class="dg-note" style="font-size: 14px">One station per person or pair. The rest of the line runs on its baseline.</text>
</svg>

<!--
The capstone runs from Thursday afternoon to Friday, 14:00. Fork the repository: your team owns the whole line. Split the stations, one per person or pair; the rest runs on its baseline. Start with intake, implement, governance and BI. One block per topic of the week, each with a checkpoint a facilitator ticks off.

[click] Rebuild a station as your own Agno agent, and read the trace of its first run.

[click] Give it a skill: what the traces showed you, Fernhill's business rules.

[click] Connect the dbt charts MCP server, or write your own tool.

[click] Add three benchmark cases for your station, taken from the failures you saw on Thursday.

[click] Then improve the factory: go where the practice score says the points are, measure every change and revert what fails. Then you freeze your fork and the final runs; everything is done by 14:00 on Friday. Hand out interviews.md now: it holds the company know-how no agent can find in the data.
-->

---
layout: default
tag: 'The final'
clicks: 4
---

# The final: a request nobody has seen

<div style="display: grid; grid-template-columns: 0.8fr 1.2fr; gap: 2.4rem; margin-top: 1.2rem">
<div style="display: flex; flex-direction: column; gap: 1.1rem; font-size: 1.05rem">
  <div v-click="1" style="display: flex; gap: 0.7rem; align-items: center"><span class="i-ph-github-logo-bold" style="color: #543edc; flex: none" /> A new issue, opened on Friday</div>
  <div v-click="2" style="display: flex; gap: 0.7rem; align-items: center"><span class="i-ph-factory-bold" style="color: #543edc; flex: none" /> Every factory, the same CI pipeline</div>
  <div v-click="3" style="display: flex; gap: 0.7rem; align-items: center"><span class="i-ph-timer-bold" style="color: #543edc; flex: none" /> One run, 45 minutes, no reruns</div>
</div>
<svg v-click="4" class="dg" viewBox="0 0 500 250">
  <text x="0" y="12" class="dg-cap">POINTS, OUT OF 100</text>
  <g v-for="(r, i) in [['Correctness', 50], ['Efficiency', 15], ['Governance', 10], ['Dashboard', 10], ['Own benchmark', 10], ['Interface', 5]]" :key="r[0]">
    <text x="0" :y="50 + i * 34" style="font-size: 15px">{{ r[0] }}</text>
    <rect x="130" :y="36 + i * 34" :width="r[1] * 6.6" height="18" rx="2" :class="i === 0 ? 'dg-block' : 'dg-block-soft'"/>
    <text :x="140 + r[1] * 6.6" :y="50 + i * 34" style="font-size: 15px; font-weight: 700">{{ r[1] }}</text>
  </g>
</svg>
</div>

<p v-click="4" style="margin-top: 1.4rem; font-size: 1.05rem">Only a factory that learned how Fernhill’s data works gets the numbers right.</p>

<!--
This is the point of the capstone: not the best prompt for a known case, but a factory that generalises.

[click] On Friday the organisers open an issue nobody has seen.

[click] Every team's factory builds it in the same CI pipeline, one the team cannot change.

[click] One run, 45 minutes, unattended. No reruns for bad luck.

[click] Correctness weighs half, on purpose: a well-governed product with wrong numbers is wrong. Efficiency only counts as far as the product is correct. The request uses a part of the warehouse the public products hardly touch. After the final each team tells the change that mattered most, one thing that did not work, and how well their own benchmark predicted their final score.
-->
