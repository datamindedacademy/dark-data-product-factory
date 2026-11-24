<script setup lang="ts">
/** A clock ring that runs down the 45 minutes of the final, looping. */
</script>

<template>
  <div class="clock">
    <svg viewBox="0 0 120 120">
      <circle cx="60" cy="60" r="52" class="track" />
      <circle cx="60" cy="60" r="52" class="run" />
    </svg>
    <div class="clock-text">
      <div class="clock-time">16:00</div>
      <div class="clock-sub">45 minutes</div>
    </div>
  </div>
</template>

<style scoped>
.clock { position: relative; width: 190px; height: 190px; }
.clock svg { width: 100%; height: 100%; transform: rotate(-90deg); }
.track { fill: none; stroke: rgba(179, 167, 242, 0.18); stroke-width: 7; }
.run {
  fill: none; stroke: #8f7bff; stroke-width: 7; stroke-linecap: round;
  stroke-dasharray: 327; animation: run 8s linear infinite;
  filter: drop-shadow(0 0 6px rgba(143, 123, 255, 0.8));
}
.clock-text { position: absolute; inset: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; }
.clock-time { font-family: 'El Messiri', serif; font-size: 44px; font-weight: 700; color: #fff; line-height: 1; }
.clock-sub { font-size: 14px; color: #b3a7f2; margin-top: 6px; letter-spacing: 0.06em; }
@keyframes run { from { stroke-dashoffset: 0; } to { stroke-dashoffset: 327; } }
</style>
