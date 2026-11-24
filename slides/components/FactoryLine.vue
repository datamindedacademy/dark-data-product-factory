<script setup lang="ts">
/**
 * The factory line as an animated conveyor: a request travels from the GitHub issue
 * through the stations to the dashboard, and every station lights up as it passes.
 * The dashed arc above is the rework loop from review and governance back to implement.
 */
const stations = [
  { label: 'Issue', icon: 'i-mdi-github', edge: true },
  { label: 'Intake', icon: 'i-mdi-clipboard-text-search-outline' },
  { label: 'Implement', icon: 'i-mdi-database-cog-outline' },
  { label: 'Review', icon: 'i-mdi-magnify-scan' },
  { label: 'Governance', icon: 'i-mdi-shield-check-outline' },
  { label: 'BI', icon: 'i-mdi-chart-box-outline' },
  { label: 'Data product', icon: 'i-mdi-package-variant-closed-check', edge: true },
]
const cycle = 9
const delay = (i: number) => `${(i / (stations.length - 1)) * cycle}s`
</script>

<template>
  <div class="factory" :style="{ '--cycle': `${cycle}s`, '--n': stations.length }">
    <svg class="rework" viewBox="0 0 700 60" preserveAspectRatio="none">
      <defs>
        <marker id="rework-head" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">
          <path d="M0,0 L10,5 L0,10 z" fill="#b3a7f2" />
        </marker>
      </defs>
      <path d="M 450 58 C 450 4, 250 4, 250 58" class="rework-path" marker-end="url(#rework-head)" />
    </svg>
    <div class="rework-label">rework</div>

    <div class="belt"><div class="belt-flow" /></div>
    <div class="packet" />

    <div class="stations">
      <div v-for="(s, i) in stations" :key="s.label" class="station" :class="{ edge: s.edge }">
        <div class="node" :style="{ animationDelay: delay(i) }">
          <div :class="s.icon" class="node-icon" />
        </div>
        <div class="node-label">{{ s.label }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.factory { position: relative; padding-top: 58px; }
.rework { position: absolute; top: 0; left: 0; width: 100%; height: 64px; overflow: visible; }
.rework-path {
  fill: none; stroke: #b3a7f2; stroke-width: 1.6; stroke-dasharray: 6 6;
  vector-effect: non-scaling-stroke; animation: dash 1.2s linear infinite;
}
.rework-label {
  position: absolute; top: 2px; left: 50%; transform: translateX(-50%);
  font-size: 12px; letter-spacing: 0.12em; text-transform: uppercase; color: #b3a7f2;
}
.belt {
  position: absolute; left: calc(100% / var(--n) / 2); right: calc(100% / var(--n) / 2);
  top: calc(58px + 39px); height: 4px; border-radius: 2px; background: rgba(179, 167, 242, 0.18); overflow: hidden;
}
.belt-flow {
  position: absolute; inset: 0;
  background: repeating-linear-gradient(90deg, rgba(179, 167, 242, 0.7) 0 14px, transparent 14px 28px);
  animation: belt 0.9s linear infinite;
}
.packet {
  position: absolute; top: calc(58px + 33px); width: 16px; height: 16px; margin-left: -8px;
  border-radius: 4px; background: #fff;
  box-shadow: 0 0 14px 4px #8f7bff, 0 0 40px 10px rgba(143, 123, 255, 0.45);
  animation: travel var(--cycle) linear infinite; z-index: 3;
}
.stations { display: grid; grid-template-columns: repeat(var(--n), 1fr); position: relative; z-index: 2; }
.station { display: flex; flex-direction: column; align-items: center; gap: 12px; }
.node {
  width: 82px; height: 82px; border-radius: 22px; display: flex; align-items: center; justify-content: center;
  background: rgba(20, 16, 80, 0.9); border: 1.5px solid rgba(179, 167, 242, 0.55);
  animation: glow var(--cycle) linear infinite;
}
.edge .node { border-radius: 9999px; border-style: dashed; }
.node-icon { width: 38px; height: 38px; color: #cacdf9; }
.node-label { font-size: 15px; font-weight: 600; color: #fff; }
.edge .node-label { color: #b3a7f2; font-weight: 500; }

@keyframes travel {
  0% { left: calc(100% / var(--n) / 2); opacity: 0; }
  4% { opacity: 1; }
  92% { opacity: 1; }
  100% { left: calc(100% - 100% / var(--n) / 2); opacity: 0; }
}
@keyframes glow {
  0% { background: #543edc; border-color: #fff; box-shadow: 0 0 34px 6px rgba(143, 123, 255, 0.75); transform: scale(1.08); }
  12% { background: rgba(20, 16, 80, 0.9); border-color: rgba(179, 167, 242, 0.55); box-shadow: none; transform: scale(1); }
  100% { background: rgba(20, 16, 80, 0.9); border-color: rgba(179, 167, 242, 0.55); box-shadow: none; transform: scale(1); }
}
@keyframes belt { to { background-position: 28px 0; } }
@keyframes dash { to { stroke-dashoffset: -12; } }
</style>
