<template>
  <div class="donut">
    <svg viewBox="0 0 160 160" class="donut-svg">
      <circle class="track" cx="80" cy="80" r="54" />
      <circle
        v-for="(segment, index) in arcs"
        :key="segment.label"
        class="arc"
        cx="80"
        cy="80"
        r="54"
        :stroke="segment.color"
        :stroke-dasharray="segment.dash"
        :stroke-dashoffset="segment.offset"
      />
    </svg>
    <div class="donut-center">
      <strong>{{ formattedCenter }}</strong>
      <span>{{ centerLabel }}</span>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PiDonut',
  props: {
    segments: {
      type: Array,
      default: () => [],
    },
    centerValue: {
      type: Number,
      default: 0,
    },
    centerLabel: {
      type: String,
      default: 'Totalité',
    },
  },
  computed: {
    circumference() {
      return 2 * Math.PI * 54;
    },
    arcs() {
      const total = this.segments.reduce((sum, item) => sum + (Number(item.value) || 0), 0);
      if (!total) {
        return [];
      }
      let cursor = 0;
      return this.segments
        .filter((item) => Number(item.value) > 0)
        .map((item) => {
          const value = Number(item.value) || 0;
          const length = (value / total) * this.circumference;
          const offset = this.circumference - cursor;
          cursor += length;
          return {
            label: item.label,
            color: item.color,
            dash: `${length} ${this.circumference - length}`,
            offset,
          };
        });
    },
    formattedCenter() {
      return new Intl.NumberFormat('fr-FR').format(Number(this.centerValue) || 0);
    },
  },
};
</script>

<style scoped>
.donut {
  position: relative;
  width: 210px;
  height: 210px;
  flex-shrink: 0;
}

.donut-svg {
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.track,
.arc {
  fill: none;
  stroke-width: 18;
}

.track {
  stroke: #eef2f6;
}

.arc {
  stroke-linecap: butt;
}

.donut-center {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.donut-center strong {
  font-size: 22px;
}

.donut-center span {
  font-size: 12px;
  color: #64748b;
}
</style>
