<template>
  <div class="section-async-loading" role="status" aria-live="polite">
    Chargement de la section…
  </div>
</template>

<script>
export default {
  name: 'SectionAsyncLoading'
};
</script>

<style scoped>
.section-async-loading {
  padding: 1.5rem;
  color: #6b7280;
  font-size: 14px;
}
</style>
