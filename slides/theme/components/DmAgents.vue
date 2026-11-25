<script setup lang="ts">
// One agent, three stages on one scale (reads today; what if it acts; what if it runs code), built up over three slides: rows="1" (slide 12, the tiles and the scale), rows="2" (slide 14, adds WORST CASE), rows="3" (slide 38, adds CONTAINED BY).
// Rows already seen stay visible, muted; the newest row is the emphasised one. All texts live here so the slides cannot drift.
// Clicks are registered by the component itself: rows 1 = 4 clicks (tile, tile, tile, scale) · rows 2 = 3 clicks (one worst case per stage) · rows 3 = 4 clicks (rows 1 and 2 return, then one containment per stage).
defineProps<{ rows: 1 | 2 | 3 }>()

const stages = [
  { icon: 'i-ph-magnifying-glass-bold', verb: 'READS', text: 'Searches documents and queries data', tag: 'Today', mine: true, note: 'Also writes SQL, read-only', change: 'Nothing', worst: 'The wrong person sees a document', safe: 'Permissions checked per user, outside the agent', ref: 'Slides 21, 22, 34' },
  { icon: 'i-ph-share-network-bold', verb: 'ACTS', text: 'Shares a document for you', tag: 'What if', change: 'What its tools allow', worst: 'Shared with the wrong people, can\'t be unshared', safe: 'Limits in the API, a human approves the risky ones', ref: 'Slides 24, 25, 26' },
  { icon: 'i-ph-terminal-window-bold', verb: 'RUNS CODE', text: 'Writes a Python report and runs it', tag: 'What if', change: 'Whatever its code can reach', worst: 'Its code reads any file, calls any address', safe: 'The sandbox: no credentials inside, approved hosts only', ref: 'Slide 35' },
]
</script>

<template>
  <div class="dma">
    <div class="dma-agent" :class="{ 'dg-dim': rows > 1 }"><div class="i-ph-books-bold dma-icon" /><div class="dma-name">Knowledge agent</div></div>
    <!-- rows="1": the tiles appear one per click, then the scale -->
    <template v-if="rows === 1">
      <div class="dma-grid">
        <div v-for="a in stages" :key="a.verb" v-click class="dma-tile">
          <div class="dma-head"><div :class="a.icon" class="dma-icon" /><div class="dma-name">{{ a.verb }}</div></div>
          <div class="dma-text">{{ a.text }}</div>
          <div class="dma-tag" :class="{ 'dma-tag-mine': a.mine }">{{ a.tag }}</div>
          <div v-if="a.note" class="dma-note">{{ a.note }}</div>
        </div>
      </div>
      <div v-click class="dma-scale">
        <div class="dma-cap">WHAT IT CAN CHANGE</div>
        <div class="dma-line"><div class="dma-line-bar" /><div class="dma-line-head" /></div>
        <div class="dma-grid dma-stops">
          <div v-for="(a, i) in stages" :key="a.verb" class="dma-stop"><div class="dma-dotbox"><div class="dma-dot" :class="'dma-dot-' + i" /></div><div class="dma-change">{{ a.change }}</div></div>
        </div>
      </div>
    </template>

    <!-- rows="2": the tiles return muted, WORST CASE appears one per click -->
    <template v-else-if="rows === 2">
      <div class="dma-grid dg-dim">
        <div v-for="a in stages" :key="a.verb" class="dma-tile">
          <div class="dma-head"><div :class="a.icon" class="dma-icon" /><div class="dma-name">{{ a.verb }}</div></div>
          <div class="dma-text">{{ a.text }}</div>
          <div class="dma-tag" :class="{ 'dma-tag-mine': a.mine }">{{ a.tag }}</div>
          <div v-if="a.note" class="dma-note">{{ a.note }}</div>
        </div>
      </div>
      <div class="dma-cap dma-cap-coral">WORST CASE</div>
      <div class="dma-grid">
        <div v-for="a in stages" :key="a.verb" v-click class="dma-cell dma-worst">{{ a.worst }}</div>
      </div>
    </template>

    <!-- rows="3": rows 1 and 2 return muted on the first click (compact), CONTAINED BY appears one per click -->
    <template v-else>
      <div v-click class="dg-dim">
        <div class="dma-grid">
          <div v-for="a in stages" :key="a.verb" class="dma-tile dma-tile-compact">
            <div class="dma-head"><div :class="a.icon" class="dma-icon" /><div class="dma-name">{{ a.verb }}</div></div>
          </div>
        </div>
        <div class="dma-grid" style="margin-top:0.5rem">
          <div v-for="a in stages" :key="a.verb" class="dma-cell dma-worst dma-cell-small">{{ a.worst }}</div>
        </div>
      </div>
      <div class="dma-cap">CONTAINED BY</div>
      <div class="dma-grid">
        <div v-for="a in stages" :key="a.verb" v-click class="dma-cell dma-safe">{{ a.safe }}<div class="dma-ref">{{ a.ref }}</div></div>
      </div>
    </template>
  </div>
</template>

<style>
.dma { font-family: 'DM Sans', Arial, sans-serif; color: var(--dm-navy); }
.dma-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; }
.dma-tile { background: var(--dm-surface); border-radius: 8px; padding: 0.9rem 1rem; }
.dma-agent { display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.7rem; }
.dma-agent .dma-icon { font-size: 1.5rem; }
.dma-agent .dma-name { font-size: 1.05rem; }
.dma-head { display: flex; align-items: center; gap: 0.6rem; }
.dma-icon { font-size: 2rem; color: var(--dm-purple); flex: none; }
.dma-name { font-size: 1.25rem; font-weight: 700; line-height: 1.15; letter-spacing: 0.04em; }
.dma-verb { font-family: ui-monospace, Menlo, monospace; font-size: 0.8rem; letter-spacing: 0.14em; color: var(--dm-purple); margin: 0.5rem 0 0.3rem; }
.dma-text { font-size: 1.05rem; line-height: 1.3; margin-top: 0.5rem; min-height: 2.6em; text-wrap: balance; }
.dma-tag { display: inline-block; margin-top: 0.6rem; font-size: 0.7rem; padding: 0.15rem 0.6rem; border-radius: 999px; background: #fff; color: var(--dm-muted); }
.dma-tag-mine { background: var(--dm-purple); color: #fff; }
.dma-note { margin-top: 0.5rem; font-size: 0.8rem; color: var(--dm-muted); }
.dma-tile-compact { padding: 0.5rem 0.9rem; display: flex; align-items: center; justify-content: space-between; }
.dma-tile-compact .dma-icon { font-size: 1.5rem; }
.dma-tile-compact .dma-name { font-size: 1rem; }
.dma-tile-compact .dma-verb { margin: 0; }
.dma-cap { font-family: ui-monospace, Menlo, monospace; font-size: 0.75rem; letter-spacing: 0.14em; color: var(--dm-purple); margin: 1rem 0 0.4rem; }
.dma-cap-coral { color: var(--dm-coral); }
/* the cap of a row appears with its first cell, never alone */
.dma-cap:has(+ .dma-grid > .dma-cell.slidev-vclick-hidden:first-child) { visibility: hidden; }
.dma-cell { border-radius: 8px; padding: 0.8rem 1rem; font-size: 1.1rem; line-height: 1.3; }
.dma-cell-small { padding: 0.4rem 0.8rem; font-size: 0.85rem; }
.dma-worst { background: #fff1ee; border-left: 4px solid var(--dm-coral); }
.dma-safe { background: var(--dm-navy); color: #fff; font-weight: 700; }
.dma-ref { margin-top: 0.4rem; font-size: 0.7rem; font-weight: 400; color: var(--dm-lavender); }
.dma-scale { margin-top: 1rem; }
.dma-line { position: relative; height: 14px; margin: 0.2rem 0 0; }
.dma-line-bar { position: absolute; left: 0; right: 8px; top: 6px; height: 3px; background: var(--dm-navy); transform-origin: left; transform: scaleX(1); transition: transform 0.9s ease; }
.dma-line-head { position: absolute; right: 0; top: 0; border-left: 12px solid var(--dm-navy); border-top: 7px solid transparent; border-bottom: 7px solid transparent; transition: opacity 0.3s 0.8s; }
.slidev-vclick-hidden.dma-scale .dma-line-bar { transform: scaleX(0); }
.slidev-vclick-hidden.dma-scale .dma-line-head { opacity: 0; }
.dma-stops { margin-top: -21px; }
.dma-stop { text-align: center; }
.dma-dotbox { height: 28px; display: flex; align-items: center; justify-content: center; }
.dma-dot { display: inline-block; border-radius: 50%; background: var(--dm-purple); }
.dma-dot-0 { width: 14px; height: 14px; } .dma-dot-1 { width: 20px; height: 20px; } .dma-dot-2 { width: 28px; height: 28px; }
.dma-change { font-size: 1.05rem; font-weight: 700; margin-top: 0.2rem; }
</style>
