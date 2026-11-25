<script setup lang="ts">
// The map of an enterprise agent (slide 3, and in grey on slide 9). One inline SVG, geometry never changes.
// step: 0 is the laptop (orchestration, LLM, tools), 1 adds the entrypoint, 2 knowledge, memory and monitoring, 3 outside systems; undefined shows all.
// Props are plain values, so a page can bind them to $clicks. Nothing is stored in the component.
//
// Centre of every box in the viewBox (for content passed in the default slot, which is drawn on top inside the <svg>):
//   Entrypoint 120,175 · Orchestration 410,175 (frame 220..600 x 70..280) · LLM 770,175
//   Internal knowledge 305,31 · Tools and actions 515,31 · Outside systems 765,31 · Memory 305,317 · Monitoring 515,317
//   Arrows: Entrypoint-Orchestration x 190..298 at y 160 and 190 · Orchestration-LLM x 520..698 at y 160 and 190
// Marker ids: arr-<uid> (navy), arrp-<uid> (violet), arrc-<uid> (coral), for use in the slot.
const props = defineProps<{
  uid: string
  step?: number
  dim?: boolean
}>()

const vis = (n: number) => props.step === undefined || props.step >= n
const op = () => ({ opacity: props.dim ? 0.5 : 1 })

const nodes = [
  { k: 'entry', x: 50, y: 148, w: 140, h: 54, t: 'Entrypoint', step: 1 },
  { k: 'orch', x: 300, y: 148, w: 220, h: 54, t: 'Orchestration', step: 0, solid: true },
  { k: 'llm', x: 700, y: 148, w: 140, h: 54, t: 'LLM', step: 0 },
  { k: 'know', x: 220, y: 4, w: 170, h: 54, t: 'Internal knowledge', step: 2 },
  { k: 'mem', x: 220, y: 290, w: 170, h: 54, t: 'Memory', step: 2 },
  { k: 'mon', x: 430, y: 290, w: 170, h: 54, t: 'Monitoring', step: 2 },
  { k: 'tools', x: 430, y: 4, w: 170, h: 54, t: 'Tools and actions', step: 0 },
]
const arrows = [
  { step: 1, d: 'M190 160 H298' }, { step: 1, d: 'M298 190 H192' },
  { step: 0, d: 'M520 160 H698' }, { step: 0, d: 'M698 190 H522' },
  { step: 2, d: 'M330 148 V60' }, { step: 2, d: 'M370 60 V146' },
  { step: 2, d: 'M330 288 V204' }, { step: 2, d: 'M370 204 V288' },
  { step: 2, d: 'M470 204 V288' },
  { step: 0, d: 'M450 148 V60' }, { step: 0, d: 'M490 60 V146' },
  { step: 3, d: 'M600 31 H688' },
]
</script>

<template>
  <svg class="dg dmm" viewBox="0 -22 860 372">
    <defs>
      <marker :id="`arr-${uid}`" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#080635"/></marker>
      <marker :id="`arrp-${uid}`" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#543edc"/></marker>
      <marker :id="`arrc-${uid}`" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#fc6b51"/></marker>
    </defs>

    <!-- the agent's frame around the loop -->
    <g v-show="vis(0)" class="dg-group"><rect x="220" y="70" width="380" height="210" rx="70"/></g>

    <path v-for="(a, i) in arrows" :key="'a' + i" v-show="vis(a.step)" :d="a.d" class="dg-line" :style="op()" :marker-end="`url(#arr-${uid})`"/>

    <g v-for="n in nodes" :key="n.k" v-show="vis(n.step)" :class="n.solid ? 'dg-solid' : 'dg-node'" :style="op()">
      <rect :x="n.x" :y="n.y" :width="n.w" :height="n.h" rx="3"/>
      <text :x="n.x + n.w / 2" :y="n.y + n.h / 2 + 6" text-anchor="middle" class="dmm-label">{{ n.t }}</text>
    </g>
    <g v-show="vis(3)" class="dg-ghost" :style="op()">
      <rect x="690" y="4" width="150" height="54" rx="3"/>
      <text x="765" y="37" text-anchor="middle" class="dmm-label">Outside systems</text>
    </g>

    <slot />
  </svg>
</template>

<style>
.dg.dmm .dmm-label { font-size: 17px; font-weight: 700; }
.dg.dmm .dg-ghost rect { fill: #fff; }
</style>
