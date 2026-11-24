<script setup lang="ts">
/** Dark content slide on a brand background, with the section label and page number. */
defineProps<{
  label?: string
  bg?: 'cover' | 'section' | 'stream-violet' | 'pills-violet' | 'stream-light'
}>()
</script>

<template>
  <div class="slidev-layout dm-dark dark-slide">
    <DmBg :variant="bg ?? 'section'" />
    <div class="dark-shade" />
    <div v-if="label" class="dm-section-label dark-label">{{ label }}</div>
    <div class="dark-body"><slot /></div>
    <DmFooter dark :page="true" />
  </div>
</template>

<style scoped>
.dark-slide { position: relative; height: 100%; padding: 44px 56px 48px; box-sizing: border-box; overflow: hidden; }
.dark-shade { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(8, 6, 53, 0.92) 0%, rgba(8, 6, 53, 0.7) 60%, rgba(8, 6, 53, 0.45) 100%); }
.dark-label { position: absolute; z-index: 2; color: #b3a7f2; }
.dark-body { position: relative; z-index: 1; height: 100%; }
.dark-body :deep(h1) { color: #fff; }
</style>
