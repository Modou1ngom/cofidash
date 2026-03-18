<template>
  <label
    :for="forAttr"
    :class="labelClasses"
  >
    <slot />
  </label>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = defineProps<{
  for?: string;
  className?: string;
}>();

const forAttr = computed(() => props.for);

const labelClasses = computed(() => {
  const base = 'text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70';
  return `${base} ${props.className || ''}`;
});
</script>
