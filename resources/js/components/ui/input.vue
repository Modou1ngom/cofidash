<template>
  <input
    :id="id"
    :type="type"
    :name="name"
    :required="required"
    :autofocus="autofocus"
    :tabindex="tabindex"
    :autocomplete="autocomplete"
    :placeholder="placeholder"
    :value="modelValue"
    :class="inputClasses"
    @input="$emit('update:modelValue', ($event.target as HTMLInputElement).value)"
    @blur="$emit('blur', $event)"
    @focus="$emit('focus', $event)"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(defineProps<{
  id?: string;
  type?: string;
  name?: string;
  required?: boolean;
  autofocus?: boolean;
  tabindex?: number | string;
  autocomplete?: string;
  placeholder?: string;
  modelValue?: string | number;
  className?: string;
}>(), {
  type: 'text'
});

defineEmits<{
  'update:modelValue': [value: string | number];
  blur: [event: FocusEvent];
  focus: [event: FocusEvent];
}>();

const inputClasses = computed(() => {
  const base = 'flex w-full rounded-md border bg-transparent px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50';
  return `${base} ${props.className || ''}`;
});
</script>
