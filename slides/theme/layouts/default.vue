<script setup lang="ts">
// Content slide as in the Dataminded template: optional section tag and pill top-right (practice: true, or whatif: acts | code), optional source line, page number and brandmark bottom-right.
defineProps<{ tag?: string, source?: string, practice?: boolean, whatif?: 'acts' | 'code' }>()
</script>

<template>
  <div class="slidev-layout dm-default">
    <header class="dm-default-header">
      <div v-if="practice" class="dm-practice-tag">IN PRACTICE</div>
      <div v-else-if="whatif" class="dm-agent-tag">WHAT IF · {{ whatif === 'acts' ? 'IT ACTS' : 'IT RUNS CODE' }}</div>
      <div v-if="tag" class="dm-default-tag">{{ tag }}</div>
    </header>
    <main class="dm-default-body"><slot /></main>
    <footer class="dm-default-footer">
      <div class="dm-default-source" v-if="source" v-html="'Source: ' + source" />
    </footer>
    <DmFooter page />
  </div>
</template>

<style scoped>
.dm-default { position: relative; padding: 1.6rem 3.2rem 2.4rem; overflow: hidden; }
.dm-default-header { display: flex; justify-content: flex-end; align-items: center; gap: 0.8rem; min-height: 1.4rem; margin-bottom: 1.4rem; font-size: 0.95rem; }
.dm-default-tag { font-size: 0.65rem; color: var(--dm-muted); text-transform: uppercase; letter-spacing: 0.08em; }
.dm-default-body { position: relative; z-index: 1; }
.dm-default-footer {
  position: absolute; left: 3.2rem; right: 7rem; bottom: 0.9rem;
  display: flex; justify-content: space-between; align-items: flex-end;
  font-size: 0.6rem; color: var(--dm-muted);
}
.dm-default-source { max-width: 85%; }
</style>
