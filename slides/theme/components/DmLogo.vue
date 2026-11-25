<script setup lang="ts">
// Official Dataminded wordmark.
import logoDark from '../assets/wordlogo-dark.png'
import logoLight from '../assets/wordlogo-light.png'
defineProps<{ light?: boolean }>()
</script>

<template>
  <img :src="light ? logoLight : logoDark" class="dm-logo" alt="dataminded" />
</template>

<style scoped>
.dm-logo { height: 1.2em; width: auto; display: block; }
</style>
