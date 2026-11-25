<script setup lang="ts">
// Large number with a short label, for slides built around one figure.
defineProps<{ value: string, label?: string }>()
</script>

<template>
  <div class="dm-stat">
    <div class="dm-stat-value">{{ value }}</div>
    <div class="dm-bar" />
    <div v-if="label" class="dm-stat-label">{{ label }}</div>
    <div class="dm-stat-body"><slot /></div>
  </div>
</template>

<style scoped>
.dm-stat-value {
  font-family: 'El Messiri', Arial, serif;
  font-weight: 700;
  font-size: 3.6rem;
  line-height: 1;
  color: var(--dm-purple);
  margin-bottom: 0.6rem;
}
.dm-stat-label { margin-top: 0.7rem; font-weight: 700; }
.dm-stat-body { font-size: 0.85rem; color: var(--dm-muted); }
</style>
