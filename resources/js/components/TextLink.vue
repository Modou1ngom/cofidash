<template>
  <a
    :href="href"
    :tabindex="tabindex"
    class="text-sm font-medium hover:underline"
    :class="className"
    @click.prevent="handleClick"
  >
    <slot />
  </a>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

const props = defineProps<{
  href: string;
  tabindex?: number | string;
  className?: string;
}>();

const router = useRouter();

const handleClick = () => {
  if (props.href.startsWith('/')) {
    router.push(props.href);
  } else {
    window.location.href = props.href;
  }
};
</script>
