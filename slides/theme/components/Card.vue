<script setup lang="ts">
// Lavender card with a purple icon badge. Pass a literal UnoCSS icon class, e.g. icon="i-ph-database-bold".
defineProps<{ title?: string, icon?: string, number?: string | number }>()
</script>

<template>
  <div class="dm-card">
    <div v-if="icon || number" class="dm-card-badge">
      <div v-if="icon" :class="icon" />
      <span v-else>{{ number }}</span>
    </div>
    <h3 v-if="title" class="dm-card-title">{{ title }}</h3>
    <div class="dm-card-body"><slot /></div>
  </div>
</template>

<style scoped>
.dm-card {
  background: var(--dm-card);
  border: 1px solid var(--dm-card-border);
  border-radius: 12px;
  padding: 1rem 1.1rem;
  height: 100%;
}
.dm-card-badge {
  width: 2rem;
  height: 2rem;
  border-radius: 999px;
  background: var(--dm-purple);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.95rem;
  margin-bottom: 0.6rem;
}
.dm-card-title { margin: 0 0 0.3rem; font-size: 0.95rem; }
.dm-card-body { font-size: 0.8rem; color: var(--dm-muted); line-height: 1.45; }
.dm-card-body :deep(p) { margin: 0.25rem 0; }
.dm-card-body :deep(ul li) { margin: 0.2rem 0; }
</style>
