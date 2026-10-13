<template>
  <footer class="app-foot">
    <div class="foot-brand">
      <img src="/logo.png" alt="Cofina" />
      <div>
        <strong>Cofina</strong>
        <span>Usage interne</span>
      </div>
    </div>
    <p class="foot-copy">© {{ year }} Cofina Sénégal</p>
    <p class="foot-meta">
      <span>Données au {{ dataDate }}</span>
      <span class="foot-sep" aria-hidden="true"></span>
      <span>Version {{ version }}</span>
    </p>
  </footer>
</template>

<script>
import { version } from '../../../package.json';

export default {
  name: 'AppFooter',
  data() {
    const now = new Date();
    return {
      year: now.getFullYear(),
      dataDate: now.toLocaleDateString('fr-FR'),
      version,
    };
  },
};
</script>

<style scoped>
.app-foot {
  position: relative;
  flex-shrink: 0;
  z-index: 0;
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  gap: 16px;
  padding: 10px 18px;
  background: #1a4d3a;
  color: #fff;
  box-shadow: 0 -6px 18px rgba(16, 48, 36, 0.18);
}

.foot-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.foot-brand img {
  width: 36px;
  height: 36px;
  padding: 4px;
  object-fit: contain;
  background: #fff;
  border-radius: 8px;
}

.foot-brand strong {
  display: block;
  font-size: 14px;
  font-weight: 700;
  line-height: 1.2;
}

.foot-brand span {
  display: block;
  margin-top: 1px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.78);
}

.foot-copy {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
}

.foot-meta {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
  white-space: nowrap;
}

.foot-sep {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.55);
}

@media (max-width: 900px) {
  .app-foot {
    grid-template-columns: 1fr;
    justify-items: center;
    text-align: center;
  }

  .foot-meta {
    justify-content: center;
  }
}
</style>
