<template>
  <input
    :id="id"
    :name="name"
    :tabindex="tabindex"
    type="checkbox"
    :checked="modelValue"
    :value="value"
    class="h-4 w-4 rounded border-gray-300 text-red-600 focus:ring-red-500"
    @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
  />
</template>

<script setup lang="ts">
defineProps<{
  id?: string;
  name?: string;
  tabindex?: number | string;
  modelValue?: boolean;
  value?: string | number;
}>();

defineEmits<{
  'update:modelValue': [value: boolean];
}>();
</script>
