<script setup lang="ts">
// The icon of one of the three questions, drawn around 0,0 in about 18x18 units, in currentColor: a padlock (is it safe?), a gauge (will it scale?), a coin (what does it cost?). Place it with a transform.
defineProps<{ q: 'safe' | 'scale' | 'cost' }>()
</script>

<template>
  <g class="dmqi">
    <template v-if="q === 'safe'">
      <rect x="-7" y="-1.5" width="14" height="10" rx="2" style="fill: currentColor; stroke: none" />
      <path d="M-4 -1.5 V-4.5 a4 4 0 0 1 8 0 V-1.5" style="fill: none; stroke: currentColor; stroke-width: 2" />
    </template>
    <template v-else-if="q === 'scale'">
      <path d="M-8.5 5 A8.5 8.5 0 0 1 8.5 5" style="fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round" />
      <path d="M0 5 L5 -3" style="fill: none; stroke: currentColor; stroke-width: 2.2; stroke-linecap: round" />
      <circle cx="0" cy="5" r="2" style="fill: currentColor; stroke: none" />
    </template>
    <template v-else>
      <circle cx="0" cy="0" r="8" style="fill: none; stroke: currentColor; stroke-width: 2" />
      <text x="0" y="4.5" text-anchor="middle" style="fill: currentColor; font-size: 12px; font-weight: 700">€</text>
    </template>
  </g>
</template>
