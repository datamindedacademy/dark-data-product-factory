<script setup lang="ts">
// The anchor of the deck, "the circuit": a closed track with the three questions as stations and the live agent in the middle (slides 4, 11, 16, 27, 40, 48, 58).
import { computed } from 'vue'

const props = defineProps<{
  uid: string
  step?: number // slide 4 build, 0-4 (5, safety lit, is the state slide 11 opens in)
  current?: 'safe' | 'scale' | 'cost' // compact: the lit question; earlier ones are ticked
  done?: number // stations ticked in order (slide 58)
  again?: boolean // slide 58: the on-ramp and Safe are asked again
  live?: boolean // the hub shows the agent in production
  compact?: boolean // the track only, cropped, for the corner
  harm?: number // slides 16, 27: misuse cards shown (0-2)
  insidersDone?: boolean
  grey?: boolean // the callback: labels and hub in grey
}>()

type St = 'neutral' | 'lit' | 'ticked' | 'muted'
const keys = ['safe', 'scale', 'cost'] as const
const s = computed(() => props.step)
const ci = computed(() => keys.indexOf(props.current as any))
const nDone = computed(() => props.done ?? (ci.value > 0 ? ci.value : 0))

const stations = [
  { k: 'safe', x: 350, y: 120, t: 'Is it safe?', ty: 62 },
  { k: 'scale', x: 650, y: 120, t: 'Will it scale?', ty: 62 },
  { k: 'cost', x: 500, y: 340, t: 'What does it cost?', ty: 454 },
] as const

const open = computed(() => s.value !== undefined && s.value >= 3 && s.value !== 5)
const st = computed<St[]>(() => {
  if (s.value !== undefined) {
    if (s.value === 3) return ['ticked', 'neutral', 'neutral']
    if (s.value === 5) return ['lit', 'muted', 'muted']
    return ['neutral', 'neutral', 'neutral']
  }
  return keys.map((_, i) => {
    if (props.again && i === 0) return 'lit'
    if (i < nDone.value) return 'ticked'
    if (ci.value >= 0) return i === ci.value ? 'lit' : 'muted'
    return 'neutral'
  }) as St[]
})
// the segment after a ticked station is walked (navy); the closing one (Cost to Safe) is never walked
// slide 4, step 3: safety is ticked but the track after it stays light, so it does not read as progress towards scale
const navy = computed(() => s.value === 3 ? [false, false, false] : [st.value[0] === 'ticked' || (props.again && nDone.value > 0), st.value[1] === 'ticked', false])

const showTop = computed(() => s.value === undefined || s.value >= 1)
const showRest = computed(() => s.value === undefined || s.value >= 2)
const hub = computed<'work' | 'live' | 'grey' | 'dim'>(() => {
  if (s.value !== undefined) return s.value >= 4 ? 'grey' : s.value === 3 ? 'live' : 'work'
  return props.grey ? 'grey' : props.live ? 'live' : 'work'
})
const ramp = computed<'' | 'violet' | 'grey'>(() => {
  if (s.value !== undefined) return s.value === 4 ? 'violet' : s.value === 5 ? 'grey' : ''
  return props.again ? 'violet' : ''
})
const lit = computed(() => stations.find((_, i) => st.value[i] === 'lit'))
const centre = computed(() => lit.value?.k === 'cost' ? 'MAKE IT EFFICIENT' : 'MAKE IT GOOD')

const cards = [
  { k: 'ins', t: 'INSIDERS', g: 'See or do more than they should', to: '→ access controls', c: 'var(--dm-purple)' },
  { k: 'out', t: 'OUTSIDERS × POWER', g: 'Trick an agent that can do too much', to: '→ attackers and agent power', c: 'var(--dm-coral)' },
]
const cstate = (i: number): St => i === 0 && props.insidersDone ? 'ticked' : i === (props.harm ?? 0) - 1 ? 'lit' : 'muted'
const hasHarm = computed(() => props.harm !== undefined)
const viewBox = computed(() => hasHarm.value ? '150 0 1670 460' : props.compact ? '150 60 700 340' : '10 0 960 466')
const calm = computed(() => s.value === 5 || !!props.again) // phase captions go quiet once the question is asked again
const chev = [['M488 108 L502 120 L488 132', 'top', 0], ['M838 218 L850 232 L862 218', 'rest', 1], ['M512 328 L498 340 L512 352', 'rest', 2], ['M138 242 L150 228 L162 242', 'rest', 2]] as const
// a chevron on a walked segment would sit half off the navy line, so it hides there (not once asked again)
const showChev = (c: typeof chev[number]) => (c[1] === 'top' ? showTop.value : showRest.value) && !(hasHarm.value && c[2] === 1) && !(navy.value[c[2]] && !props.again)
</script>

<template>
  <svg class="dg dab" :class="{ 'dab-grey': grey, 'dab-again': again }" :viewBox="viewBox">
    <defs>
      <marker :id="`ra-${uid}`" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="3" markerHeight="3" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#543edc"/></marker>
      <marker :id="`rg-${uid}`" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="3" markerHeight="3" orient="auto"><path d="M0 0 L10 5 L0 10 z" fill="#cacdf9"/></marker>
    </defs>

    <!-- the track: clockwise, closed, no finish line -->
    <path v-show="showTop" d="M260 120 H740" class="dab-track"/>
    <path v-show="showRest" d="M740 120 A110 110 0 0 1 740 340 H260 A110 110 0 0 1 260 120" class="dab-track"/>
    <path v-show="navy[0]" d="M350 120 H650" class="dab-track dab-walked"/>
    <path v-show="navy[1]" d="M650 120 H740 A110 110 0 0 1 740 340 H500" class="dab-track dab-walked"/>
    <path v-show="navy[2]" d="M500 340 H260 A110 110 0 0 1 260 120 H350" class="dab-track dab-walked"/>

    <path v-for="c in chev" :key="c[0]" v-show="showChev(c)" :d="c[0]" class="dab-chev"/>

    <!-- the on-ramp: something changes, join the track again before safety -->
    <g v-if="!compact && ramp" :class="{ 'dab-rg': ramp === 'grey' }">
      <path d="M20 90 H110 C190 90 205 120 276 120" class="dab-ramp" :marker-end="`url(#${ramp === 'grey' ? 'rg' : 'ra'}-${uid})`"/>
      <text x="20" y="28" class="dab-rtext">Something</text><text x="20" y="58" class="dab-rtext">changes</text>
    </g>

    <!-- the agent, live or not yet -->
    <g v-if="!compact" :class="`dab-hub dab-hub-${hub}`">
      <rect x="320" y="196" width="360" height="96" rx="20"/>
      <foreignObject x="338" y="219" width="52" height="52"><div class="dab-fo"><i :class="hub === 'work' ? 'i-ph-laptop-bold' : 'i-ph-users-three-bold'"/></div></foreignObject>
      <template v-if="hub === 'work'">
        <text x="408" y="240" class="dab-htitle">Make it work</text>
        <text x="408" y="270" class="dab-hsub">Earlier modules</text>
        <circle cx="648" cy="244" r="17" class="dab-hcheck"/>
        <path d="M640 244 L646 250 L657 238" class="dab-tick" style="stroke-width:3.5"/>
      </template>
      <template v-else>
        <text x="408" y="240" class="dab-htitle">In production</text>
        <text x="408" y="270" class="dab-hsub">with real users</text>
      </template>
    </g>

    <!-- compact: the lit question in the middle of the loop -->
    <g v-if="compact && lit" class="dab-mid">
      <text x="500" :y="lit.k === 'cost' ? 200 : 206" class="dab-cap dab-cap-c" :style="lit.k === 'cost' ? 'font-size:26px' : ''">{{ centre }}</text>
      <text x="500" :y="lit.k === 'cost' ? 256 : 262" class="dab-mq" :style="lit.k === 'cost' ? 'font-size:42px' : ''">{{ lit.t }}</text>
    </g>

    <!-- the stations -->
    <g v-for="(g, i) in stations" :key="g.k" v-show="g.k === 'cost' ? showRest : showTop" :transform="`translate(${g.x} ${g.y})`">
     <circle r="40" fill="#fff"/>
     <g :class="[`dab-st dab-${st[i]}`, { 'dab-open': open && st[i] === 'neutral' }]">
      <circle v-if="st[i] === 'lit'" r="54" class="dab-halo"/>
      <circle :r="st[i] === 'lit' ? 46 : 40" class="dab-disc"/>
      <path v-if="st[i] === 'ticked'" d="M-13 0 L-4 10 L14 -10" class="dab-tick"/>
      <g v-else transform="scale(1.8)" class="dab-ic"><DmQIcon :q="g.k"/></g>
      <text v-if="!compact" :y="g.ty - g.y" class="dab-label">{{ g.t }}</text>
     </g>
    </g>

    <!-- the two phases -->
    <text v-if="!compact && showTop" x="500" y="100" class="dab-cap" :class="{ 'dab-quiet': calm }">MAKE IT GOOD</text>
    <text v-if="!compact && showRest" x="500" y="410" class="dab-cap" :class="{ 'dab-quiet': calm }">MAKE IT EFFICIENT</text>

    <!-- slides 16 and 27: the two sources of misuse, one card each, tied to the question in the middle of the loop -->
    <g v-if="hasHarm && harm">
      <defs><clipPath :id="`cc-${uid}`"><rect width="800" height="190" rx="20"/></clipPath></defs>
      <path d="M640 230 H930" class="dab-conn" style="stroke-linecap:butt"/>
      <circle cx="640" cy="230" r="8" class="dab-dot"/>
      <path :d="harm > 1 ? 'M930 120 V340 M930 120 H1000 M930 340 H1000' : 'M930 230 V120 H1000'" class="dab-conn"/>
      <g v-for="(c, i) in cards" v-show="harm > i" :key="c.k" :class="`dab-card dab-card-${cstate(i)}`" :transform="`translate(1000 ${25 + i * 220})`">
        <rect width="800" height="190" rx="20" class="dab-cardbox"/>
        <rect width="16" height="190" :style="{ fill: c.c }" :clip-path="`url(#cc-${uid})`"/>
        <text x="48" y="54" class="dab-cap" :style="{ fontSize: '28px', textAnchor: 'start', fill: 'var(--dm-navy)' }">{{ c.t }}</text>
        <text x="48" y="112" class="dab-cg">{{ c.g }}</text>
        <text x="48" y="164" class="dab-cto">{{ c.to }}</text>
        <g v-if="i === 0" transform="translate(730 56) scale(2)" fill="#080635"><circle cx="0" cy="-9" r="6"/><path d="M-12 11 C-12 2 -6 -2 0 -2 C6 -2 12 2 12 11 Z"/></g>
        <g v-if="cstate(i) === 'ticked'" transform="translate(740 150)"><circle r="20" fill="#080635"/><path d="M-9 0 L-2 7 L10 -7" class="dab-tick" style="stroke-width:4"/></g>
        <g v-if="i === 1 && insidersDone" transform="translate(660 22)"><rect width="110" height="40" rx="20" style="fill:var(--dm-purple)"/><text x="55" y="27" class="dab-next">NEXT</text></g>
      </g>
    </g>
  </svg>
</template>

<style>
.dg.dab text { text-anchor: middle; }
.dg.dab .dab-track { fill: none; stroke: var(--dm-lilac); stroke-width: 10; stroke-linecap: round; }
.dg.dab .dab-walked { stroke: var(--dm-navy); }
.dg.dab .dab-ramp { fill: none; stroke: var(--dm-purple); stroke-width: 8; stroke-linecap: round; }
.dg.dab .dab-rtext { font-size: 26px; font-weight: 700; fill: var(--dm-purple); text-anchor: start; }
.dg.dab .dab-rg .dab-ramp { stroke: var(--dm-lilac); }
.dg.dab .dab-rg .dab-rtext { fill: var(--dm-muted); }
.dg.dab .dab-disc { fill: #fff; stroke: var(--dm-navy); stroke-width: 3; }
.dg.dab .dab-ic { color: var(--dm-navy); }
.dg.dab .dab-label { font-size: 30px; font-weight: 700; }
.dg.dab .dab-grey .dab-label, .dg.dab.dab-grey .dab-label { fill: var(--dm-muted); }
.dg.dab .dab-halo { fill: var(--dm-authentic); }
.dg.dab .dab-lit .dab-disc { fill: var(--dm-purple); stroke: var(--dm-purple); }
.dg.dab .dab-lit .dab-ic { color: #fff; }
.dg.dab .dab-lit .dab-label { fill: var(--dm-purple); }
.dg.dab .dab-ticked .dab-disc { fill: var(--dm-navy); }
.dg.dab .dab-ticked .dab-label { fill: var(--dm-muted); }
.dg.dab .dab-tick { fill: none; stroke: #fff; stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; }
.dg.dab .dab-muted { opacity: 0.4; }
.dg.dab .dab-cap { font-family: ui-monospace, Menlo, monospace; font-size: 20px; letter-spacing: 0.14em; fill: var(--dm-purple); }
.dg.dab.dab-grey .dab-cap { fill: var(--dm-muted); }
.dg.dab .dab-cap-c { font-size: 28px; }
.dg.dab .dab-quiet { fill: var(--dm-muted); }
.dg.dab .dab-chev { fill: none; stroke: var(--dm-purple); stroke-width: 5; stroke-linecap: round; stroke-linejoin: round; }
.dg.dab .dab-open .dab-disc { stroke-dasharray: 9 7; }
.dg.dab .dab-open .dab-ic { color: var(--dm-muted); }
.dg.dab.dab-grey .dab-neutral .dab-disc { stroke: var(--dm-lilac); }
.dg.dab.dab-grey .dab-neutral .dab-ic { color: var(--dm-muted); }
.dg.dab .dab-mq { font-size: 46px; font-weight: 700; fill: var(--dm-purple); }
.dg.dab .dab-hub rect { fill: var(--dm-purple); }
.dg.dab .dab-fo { display: flex; align-items: center; justify-content: center; width: 52px; height: 52px; font-size: 46px; color: #fff; }
.dg.dab .dab-htitle { font-size: 28px; font-weight: 700; fill: #fff; text-anchor: start; }
.dg.dab .dab-hsub { font-size: 21px; fill: var(--dm-lilac); text-anchor: start; }
.dg.dab .dab-hub-work rect, .dg.dab .dab-hub-grey rect { fill: var(--dm-surface); }
.dg.dab .dab-hub-work .dab-fo, .dg.dab .dab-hub-grey .dab-fo { color: var(--dm-muted); }
.dg.dab .dab-hub-work .dab-htitle { fill: var(--dm-navy); }
.dg.dab .dab-hub-grey .dab-htitle { fill: var(--dm-muted); }
.dg.dab .dab-hub-work .dab-hsub, .dg.dab .dab-hub-grey .dab-hsub { fill: var(--dm-muted); }
.dg.dab .dab-hcheck { fill: var(--dm-muted); }
.dg.dab .dab-conn { fill: none; stroke: var(--dm-purple); stroke-width: 4; stroke-linecap: round; stroke-linejoin: round; }
.dg.dab .dab-cardbox { fill: #fff; stroke: var(--dm-navy); stroke-width: 3; }
.dg.dab .dab-card-lit .dab-cardbox { fill: var(--dm-authentic); stroke: var(--dm-purple); stroke-width: 4; }
.dg.dab .dab-card-ticked, .dg.dab .dab-card-muted { opacity: 0.6; }
.dg.dab .dab-card-ticked { opacity: 0.6; }
.dg.dab .dab-dot { fill: var(--dm-purple); }
.dg.dab.dab-again .dab-walked { stroke: var(--dm-lilac); }
.dg.dab.dab-again .dab-ticked .dab-disc { fill: var(--dm-authentic); stroke: var(--dm-lilac); }
.dg.dab.dab-again .dab-ticked .dab-tick { stroke: var(--dm-muted); }
.dg.dab .dab-cg { font-size: 38px; font-weight: 700; text-anchor: start; }
.dg.dab .dab-cto { font-size: 30px; font-weight: 700; fill: var(--dm-purple); text-anchor: start; }
.dg.dab .dab-next { font-size: 24px; font-weight: 700; fill: #fff; letter-spacing: 0.1em; }
.dg.dab .dab-hub-dim rect { fill: var(--dm-authentic); }
.dg.dab .dab-hub-dim .dab-fo { color: var(--dm-purple); }
.dg.dab .dab-hub-dim .dab-htitle { fill: var(--dm-navy); }
.dg.dab .dab-hub-dim .dab-hsub { fill: var(--dm-muted); }
</style>
