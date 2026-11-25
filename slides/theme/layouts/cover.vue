<script setup lang="ts">
// Title slide on the brand gradient. Frontmatter: date (top-right), disclaimer (small text bottom-right).
defineProps<{ date?: string, disclaimer?: string }>()
</script>

<template>
  <div class="slidev-layout dm-cover">
    <header class="dm-cover-header">
      <DmLogo light class="dm-cover-logo" />
      <div v-if="date" class="dm-cover-date">{{ date }}</div>
    </header>
    <main class="dm-cover-body"><slot /></main>
    <footer class="dm-cover-footer">
      <span class="dm-cover-play">▶</span> www.dataminded.com
    </footer>
    <div v-if="disclaimer" class="dm-cover-disclaimer">{{ disclaimer }}</div>
  </div>
</template>

<style scoped>
.dm-cover { position: relative; background: var(--dm-gradient); color: #fff; padding: 2.2rem 3rem; overflow: hidden; }
.dm-cover-header { display: flex; justify-content: space-between; align-items: center; }
.dm-cover-logo { font-size: 1.45rem; }
.dm-cover-date { font-size: 0.6rem; opacity: 0.85; }
.dm-cover-body { margin-top: 4.2rem; max-width: 70%; }
.dm-cover-body :deep(h1) { color: #fff; font-size: 2.9rem; line-height: 1.15; margin-bottom: 1rem; }
.dm-cover-body :deep(p) { color: #e5e6ff; font-size: 1.05rem; }
.dm-cover-footer {
  position: absolute; left: 3rem; bottom: 2.1rem; width: 45%;
  font-size: 0.65rem; padding-bottom: 0.6rem; border-bottom: 1px solid #7b6cf0;
}
.dm-cover-play { margin-right: 0.4rem; }
.dm-cover-disclaimer { position: absolute; right: 6rem; bottom: 2.1rem; max-width: 40%; text-align: right; font-size: 0.6rem; opacity: 0.8; }
</style>
