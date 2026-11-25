<script setup lang="ts">
// Section tag top-right and page number, as on the default layout.
defineProps<{ tag?: string }>()
</script>

<template>
  <div class="slidev-layout dm-cards">
    <div v-if="tag" class="dm-layout-tag">{{ tag }}</div>
    <div class="dm-cards-head"><slot /></div>
    <div class="dm-cards-grid">
      <slot name="cards" />
    </div>
    <DmFooter page />
  </div>
</template>

<style scoped>
.dm-cards {
  background: #ffffff;
  height: 100%;
  padding: 48px 56px;
  box-sizing: border-box;
  position: relative;
}
.dm-layout-tag { position: absolute; top: 1.6rem; right: 3.2rem; line-height: 1.4rem; font-size: 0.65rem; color: var(--dm-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.dm-cards-head :deep(h1) { font-size: 40px; }
.dm-cards-grid {
  margin-top: 32px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}
</style>
