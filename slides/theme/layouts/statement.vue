<script setup lang="ts">
// One sentence, centred, on white. For a single strong message.
</script>

<template>
  <div class="slidev-layout dm-statement">
    <DmLogo class="dm-statement-logo" />
    <main class="dm-statement-body"><slot /></main>
    <div class="dm-statement-page">{{ $slidev.nav.currentPage }}</div>
  </div>
</template>

<style scoped>
.dm-statement { position: relative; padding: 1.6rem 3.2rem; overflow: hidden; }
.dm-statement-logo { font-size: 0.95rem; }
.dm-statement-body { height: 82%; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; padding: 0 4rem; }
.dm-statement-body :deep(h1) { font-weight: 500; font-size: 1.9rem; line-height: 1.3; }
.dm-statement-body :deep(p) { color: var(--dm-muted); }
.dm-statement-page { position: absolute; right: 2rem; bottom: 0.9rem; font-size: 0.6rem; color: var(--dm-muted); }
</style>
