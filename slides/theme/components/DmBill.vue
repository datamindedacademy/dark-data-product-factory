<script setup lang="ts">
// The four-term bill strip: QUESTIONS × TURNS × TOKENS PER TURN × PRICE PER TOKEN, each with its gloss.
// lit: term keys to highlight ('questions' | 'turns' | 'tokens' | 'price'); none = all neutral. size: 'strip' (thin, slides 49 to 56) or 'full' (slide 57).
// Levers (size="full"): one named slot per term, same keys. Wrap each lever as <div v-click class="dmb-lever-item">text</div> so it appears on its own click.
withDefaults(defineProps<{ lit?: string[], size?: 'strip' | 'full' }>(), { lit: () => [], size: 'strip' })

const terms = [
  { k: 'questions', t: 'QUESTIONS', g: 'users × questions, scripts' },
  { k: 'turns', t: 'TURNS', g: 'model calls per question' },
  { k: 'tokens', t: 'TOKENS PER TURN', g: 'input + output' },
  { k: 'price', t: 'PRICE PER TOKEN', g: 'input · cached · output' },
]
</script>

<template>
  <div class="dmb" :class="'dmb-' + size">
    <template v-for="(t, i) in terms" :key="t.k">
      <div v-if="i" class="dmb-x">×</div>
      <div class="dmb-col">
        <div class="dmb-term" :class="{ 'dmb-lit': lit.includes(t.k) }">
          <div class="dmb-label">{{ t.t }}</div>
          <div class="dmb-gloss">{{ t.g }}</div>
        </div>
        <div v-if="size === 'full'" class="dmb-lever"><slot :name="t.k" /></div>
      </div>
    </template>
  </div>
</template>

<style>
.dmb { display: flex; align-items: flex-start; gap: 0.5rem; font-family: 'DM Sans', Arial, sans-serif; }
.dmb-col { flex: 1; min-width: 0; }
.dmb-x { font-size: 1.4rem; font-weight: 700; color: var(--dm-muted); line-height: 3.2rem; }
.dmb-term { background: var(--dm-surface); color: var(--dm-navy); border-radius: 8px; padding: 0.35rem 0.6rem; min-height: 3.2rem; box-sizing: border-box; display: flex; flex-direction: column; justify-content: center; text-align: center; transition: background 0.3s, color 0.3s; }
.dmb-label { font-family: ui-monospace, Menlo, monospace; font-size: 0.8rem; font-weight: 700; letter-spacing: 0.1em; }
.dmb-gloss { font-size: 0.8rem; line-height: 1.25; margin-top: 0.15rem; color: var(--dm-muted); }
.dmb-lit { background: var(--dm-purple); color: #fff; }
.dmb-lit .dmb-gloss { color: var(--dm-authentic); }
.dmb-full .dmb-x { font-size: 2.2rem; line-height: 8rem; }
.dmb-full .dmb-term { padding: 1.1rem 0.8rem; min-height: 8rem; }
.dmb-full .dmb-label { font-size: 0.95rem; letter-spacing: 0.04em; }
.dmb-full .dmb-gloss { font-size: 1rem; margin-top: 0.4rem; }
.dmb-lever { margin-top: 0.6rem; min-height: 4rem; }
.dmb-lever-item { position: relative; margin-top: 1.4rem; text-align: center; font-size: 1.25rem; font-weight: 700; color: var(--dm-purple); line-height: 1.25; }
.dmb-lever-item::before { content: ''; position: absolute; left: 50%; top: -1.2rem; height: 1rem; border-left: 2px solid var(--dm-purple); }
</style>
