<template>
  <div v-if="message" class="text-sm text-red-600 mt-1">
    {{ message }}
  </div>
</template>

<script setup lang="ts">
defineProps<{
  message?: string;
}>();
</script>
