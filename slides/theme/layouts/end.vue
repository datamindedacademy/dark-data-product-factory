<script setup lang="ts">
// Closing slide, same look as a section divider.
</script>

<template>
  <div class="slidev-layout dm-section">
    <DmLogo light class="dm-section-logo" />
    <main class="dm-section-body">
      <slot />
      <div class="dm-section-bar" />
    </main>
    <div class="dm-section-page">{{ $slidev.nav.currentPage }}</div>
  </div>
</template>

<style scoped>
.dm-section { position: relative; background: var(--dm-gradient); color: #fff; padding: 1.6rem 3.2rem; overflow: hidden; }
.dm-section-logo { font-size: 0.95rem; }
.dm-section-body { height: 80%; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.dm-section-body :deep(h1) { color: #fff; font-weight: 500; font-size: 2.7rem; margin-bottom: 0.6rem; }
.dm-section-body :deep(p) { color: #e5e6ff; font-size: 1rem; max-width: 34rem; }
.dm-section-bar { width: 3.5rem; height: 4px; background: #fff; border-radius: 2px; margin-top: 1rem; }
.dm-section-page { position: absolute; right: 2rem; bottom: 0.9rem; font-size: 0.6rem; opacity: 0.7; }
</style>
