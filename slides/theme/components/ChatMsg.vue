<script setup lang="ts">
// One chat turn. from="user" shows its avatar on the right, from="bot" on the left.
// The bot avatar sits on a white circle; without an avatar it falls back to a robot icon.
// `badge` sets the background of the bot badge, to tell two different bots apart.
defineProps<{ from: 'user' | 'bot', avatar?: string, name?: string, badge?: string }>()
</script>

<template>
  <div class="dm-msg" :class="from">
    <div v-if="from === 'bot'" class="dm-msg-bot" :style="badge ? { background: badge } : undefined" aria-label="assistant">
      <img v-if="avatar" :src="avatar" alt="">
      <!-- Phosphor robot-bold -->
      <svg v-else viewBox="0 0 256 256" width="1.15rem" height="1.15rem" aria-hidden="true">
        <path style="fill: #080635" d="M72 104a16 16 0 1 1 16 16a16 16 0 0 1-16-16m96 16a16 16 0 1 0-16-16a16 16 0 0 0 16 16m68-40v112a36 36 0 0 1-36 36H56a36 36 0 0 1-36-36V80a36 36 0 0 1 36-36h60V16a12 12 0 0 1 24 0v28h60a36 36 0 0 1 36 36m-24 0a12 12 0 0 0-12-12H56a12 12 0 0 0-12 12v112a12 12 0 0 0 12 12h144a12 12 0 0 0 12-12Zm-12 82a30 30 0 0 1-30 30H86a30 30 0 0 1 0-60h84a30 30 0 0 1 30 30m-80-6v12h16v-12Zm-34 12h10v-12H86a6 6 0 0 0 0 12m90-6a6 6 0 0 0-6-6h-10v12h10a6 6 0 0 0 6-6" />
      </svg>
    </div>
    <div class="dm-msg-bubble">
      <div v-if="name" class="dm-msg-name">{{ name }}</div>
      <slot />
    </div>
    <img v-if="from === 'user' && avatar" :src="avatar" class="dm-msg-avatar" alt="">
  </div>
</template>

<style scoped>
.dm-msg { display: flex; align-items: flex-end; gap: 0.6rem; }
.dm-msg.user { justify-content: flex-end; }
.dm-msg-bubble {
  max-width: 84%;
  padding: 0.4rem 0.75rem;
  border-radius: 14px;
  font-size: 0.74rem;
  line-height: 1.4;
}
.dm-msg.user .dm-msg-bubble { background: var(--dm-purple); color: #fff; border-bottom-right-radius: 4px; }
.dm-msg.bot .dm-msg-bubble { background: #fff; color: var(--dm-navy); border: 1px solid var(--dm-card-border); border-bottom-left-radius: 4px; }
.dm-msg-name { font-size: 0.58rem; font-weight: 700; opacity: 0.75; margin-bottom: 0.15rem; }
.dm-msg-bubble :deep(p) { margin: 0; }
.dm-msg-bubble :deep(strong) { color: inherit; }
.dm-msg-avatar { width: 2rem; height: 2rem; border-radius: 999px; flex-shrink: 0; }
.dm-msg-bot {
  width: 2rem; height: 2rem; border-radius: 999px; flex-shrink: 0;
  background: #fff; border: 1px solid var(--dm-card-border);
  display: flex; align-items: center; justify-content: center;
}
.dm-msg-bot img { width: 72%; height: auto; }
</style>
