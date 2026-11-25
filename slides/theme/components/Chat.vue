<script setup lang="ts">
// Container for a chat conversation. Put <ChatMsg> children inside, add v-click to reveal turns.
</script>

<template>
  <div class="dm-chat"><slot /></div>
</template>

<style scoped>
.dm-chat {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  background: var(--dm-card);
  border: 1px solid var(--dm-card-border);
  border-radius: 14px;
  padding: 0.8rem 1rem;
}
</style>
