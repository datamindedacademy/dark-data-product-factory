<script setup lang="ts">
// A real incident as evidence: a screenshot from public/incidents/ cropped to its headline, slightly tilted. Used on slides 13, 23, 28, 30, 32, 35.
withDefaults(defineProps<{ src: string, tilt?: number, height?: string }>(), { tilt: -1.2, height: '19rem' })
</script>

<template>
  <figure class="dme" :style="{ transform: `rotate(${tilt}deg)` }">
    <div class="dme-crop" :style="{ maxHeight: height }"><img :src="src" alt="" /></div>
  </figure>
</template>

<style>
.dme { margin: 0 auto; width: 72%; background: #fff; border-radius: 8px; box-shadow: 0 10px 30px rgba(8, 6, 53, 0.18); overflow: hidden; }
.dme-crop { overflow: hidden; }
.dme img { display: block; width: 100%; }
</style>
