<script setup lang="ts">
// Title on the right half with a purple bar and a short intro.
</script>

<template>
  <div class="slidev-layout dm-intro">
    <DmLogo class="dm-intro-logo" />
    <main class="dm-intro-body"><slot /></main>
    <div class="dm-intro-page">{{ $slidev.nav.currentPage }}</div>
  </div>
</template>

<style scoped>
.dm-intro { position: relative; padding: 1.6rem 3.2rem; overflow: hidden; }
.dm-intro-logo { font-size: 0.95rem; }
.dm-intro-body { position: absolute; left: 50%; right: 3rem; top: 30%; }
.dm-intro-body :deep(h1) { font-size: 2.4rem; margin-bottom: 0.8rem; }
.dm-intro-body :deep(h1)::after { content: ''; display: block; width: 3rem; height: 4px; background: var(--dm-purple); border-radius: 2px; margin-top: 1rem; }
.dm-intro-body :deep(p) { font-size: 0.9rem; }
.dm-intro-page { position: absolute; right: 2rem; bottom: 0.9rem; font-size: 0.6rem; color: var(--dm-muted); }
</style>
