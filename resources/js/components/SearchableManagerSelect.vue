<template>
  <div class="sms" ref="root">
    <div class="sms-control" :class="{ open: isOpen, disabled }">
      <input
        :id="inputId"
        ref="input"
        type="text"
        class="sms-input"
        :value="isOpen ? query : displayLabel"
        :placeholder="placeholder"
        :disabled="disabled"
        :aria-expanded="isOpen"
        aria-autocomplete="list"
        autocomplete="off"
        role="combobox"
        @focus="openDropdown"
        @click="openDropdown"
        @input="onInput"
        @keydown.down.prevent="moveHighlight(1)"
        @keydown.up.prevent="moveHighlight(-1)"
        @keydown.enter.prevent="confirmHighlight"
        @keydown.escape.prevent="closeDropdown"
      />
      <button
        v-if="modelValue && !disabled"
        type="button"
        class="sms-clear"
        aria-label="Effacer"
        @click.stop="clear"
      >
        ×
      </button>
      <span class="sms-caret" aria-hidden="true">▾</span>
    </div>
    <input
      type="text"
      class="sms-required-mirror"
      tabindex="-1"
      aria-hidden="true"
      :value="modelValue || ''"
      :required="required"
      @focus="focusSearch"
    />
    <Teleport to="body">
      <ul
        v-if="isOpen"
        ref="menu"
        class="sms-menu"
        role="listbox"
        :style="menuStyle"
      >
        <li
          v-for="(option, index) in filteredOptions"
          :key="option.code_gestion_pret"
          class="sms-option"
          :class="{ active: index === highlightIndex, selected: option.code_gestion_pret === modelValue }"
          role="option"
          :aria-selected="option.code_gestion_pret === modelValue"
          @mousedown.prevent="selectOption(option)"
          @mouseenter="highlightIndex = index"
        >
          <span class="sms-code">{{ option.code_gestion_pret }}</span>
          <span v-if="option.charge_affaire" class="sms-name">{{ option.charge_affaire }}</span>
        </li>
        <li v-if="filteredOptions.length === 0" class="sms-empty">
          Aucun code GP trouvé
        </li>
      </ul>
    </Teleport>
  </div>
</template>

<script>
export default {
  name: 'SearchableManagerSelect',
  props: {
    modelValue: {
      type: String,
      default: ''
    },
    options: {
      type: Array,
      default: () => []
    },
    placeholder: {
      type: String,
      default: 'Rechercher un code GP…'
    },
    required: {
      type: Boolean,
      default: false
    },
    disabled: {
      type: Boolean,
      default: false
    },
    inputId: {
      type: String,
      default: undefined
    }
  },
  emits: ['update:modelValue'],
  data() {
    return {
      isOpen: false,
      query: '',
      highlightIndex: 0,
      menuStyle: {}
    };
  },
  computed: {
    normalizedOptions() {
      const list = Array.isArray(this.options) ? this.options : [];
      const byCode = new Map();
      for (const row of list) {
        const code = String(row?.code_gestion_pret || '').trim();
        if (!code || byCode.has(code)) continue;
        byCode.set(code, {
          code_gestion_pret: code,
          charge_affaire: String(row?.charge_affaire || '').trim()
        });
      }
      if (this.modelValue && !byCode.has(this.modelValue)) {
        byCode.set(this.modelValue, {
          code_gestion_pret: this.modelValue,
          charge_affaire: 'actuel'
        });
      }
      return [...byCode.values()];
    },
    filteredOptions() {
      const q = this.query.trim().toLowerCase();
      if (!q) return this.normalizedOptions;
      return this.normalizedOptions.filter((opt) => {
        const code = opt.code_gestion_pret.toLowerCase();
        const name = opt.charge_affaire.toLowerCase();
        return code.includes(q) || name.includes(q);
      });
    },
    displayLabel() {
      if (!this.modelValue) return '';
      const selected = this.normalizedOptions.find(
        (opt) => opt.code_gestion_pret === this.modelValue
      );
      if (!selected) return this.modelValue;
      return selected.charge_affaire
        ? `${selected.code_gestion_pret} — ${selected.charge_affaire}`
        : selected.code_gestion_pret;
    }
  },
  watch: {
    filteredOptions() {
      this.highlightIndex = 0;
    },
    isOpen(open) {
      if (open) {
        this.$nextTick(() => this.updateMenuPosition());
      }
    }
  },
  mounted() {
    document.addEventListener('mousedown', this.onClickOutside);
    window.addEventListener('resize', this.updateMenuPosition);
    window.addEventListener('scroll', this.updateMenuPosition, true);
  },
  beforeUnmount() {
    document.removeEventListener('mousedown', this.onClickOutside);
    window.removeEventListener('resize', this.updateMenuPosition);
    window.removeEventListener('scroll', this.updateMenuPosition, true);
  },
  methods: {
    openDropdown() {
      if (this.disabled) return;
      this.isOpen = true;
      this.query = '';
      this.highlightIndex = Math.max(
        0,
        this.filteredOptions.findIndex((opt) => opt.code_gestion_pret === this.modelValue)
      );
    },
    closeDropdown() {
      this.isOpen = false;
      this.query = '';
      this.highlightIndex = 0;
    },
    onInput(event) {
      this.isOpen = true;
      this.query = event.target.value;
      this.$nextTick(() => this.updateMenuPosition());
    },
    selectOption(option) {
      this.$emit('update:modelValue', option.code_gestion_pret);
      this.closeDropdown();
    },
    clear() {
      this.$emit('update:modelValue', '');
      this.query = '';
      this.$nextTick(() => this.$refs.input?.focus());
    },
    moveHighlight(step) {
      if (!this.isOpen || this.filteredOptions.length === 0) return;
      const len = this.filteredOptions.length;
      this.highlightIndex = (this.highlightIndex + step + len) % len;
      this.$nextTick(() => {
        const active = this.$refs.menu?.querySelector('.sms-option.active');
        active?.scrollIntoView({ block: 'nearest' });
      });
    },
    confirmHighlight() {
      const option = this.filteredOptions[this.highlightIndex];
      if (option) this.selectOption(option);
    },
    onClickOutside(event) {
      const inRoot = this.$refs.root?.contains(event.target);
      const inMenu = this.$refs.menu?.contains(event.target);
      if (!inRoot && !inMenu) {
        this.closeDropdown();
      }
    },
    focusSearch() {
      this.$refs.input?.focus();
    },
    updateMenuPosition() {
      if (!this.isOpen || !this.$refs.root) return;
      const rect = this.$refs.root.getBoundingClientRect();
      const maxHeight = 240;
      const spaceBelow = window.innerHeight - rect.bottom - 8;
      const openUp = spaceBelow < 160 && rect.top > spaceBelow;
      this.menuStyle = {
        position: 'fixed',
        left: `${Math.round(rect.left)}px`,
        width: `${Math.round(rect.width)}px`,
        maxHeight: `${Math.min(maxHeight, openUp ? rect.top - 8 : spaceBelow)}px`,
        top: openUp ? 'auto' : `${Math.round(rect.bottom + 4)}px`,
        bottom: openUp ? `${Math.round(window.innerHeight - rect.top + 4)}px` : 'auto',
        zIndex: 2000
      };
    }
  }
};
</script>

<style scoped>
.sms {
  position: relative;
  width: 100%;
}

.sms-control {
  position: relative;
  display: flex;
  align-items: center;
  border: 1px solid #ddd;
  border-radius: 4px;
  background: #fff;
}

.sms-control.open {
  border-color: #1a4d3a;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.12);
}

.sms-control.disabled {
  opacity: 0.65;
  background: #f5f5f5;
}

.sms-input {
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  padding: 10px 56px 10px 10px;
  font: inherit;
  color: #222;
  box-sizing: border-box;
}

.sms-clear,
.sms-caret {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  color: #666;
  line-height: 1;
}

.sms-clear {
  right: 28px;
  border: 0;
  background: transparent;
  cursor: pointer;
  font-size: 18px;
  padding: 0 4px;
}

.sms-caret {
  right: 10px;
  pointer-events: none;
  font-size: 12px;
}

.sms-required-mirror {
  position: absolute;
  opacity: 0;
  pointer-events: none;
  height: 0;
  width: 0;
  border: 0;
  padding: 0;
}
</style>

<style>
.sms-menu {
  margin: 0;
  padding: 4px;
  list-style: none;
  overflow-y: auto;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.sms-option {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 8px 10px;
  border-radius: 4px;
  cursor: pointer;
}

.sms-option.active,
.sms-option:hover {
  background: #eef6f1;
}

.sms-option.selected .sms-code {
  color: #1a4d3a;
}

.sms-code {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 13px;
  font-weight: 600;
  color: #222;
}

.sms-name {
  font-size: 12px;
  color: #666;
}

.sms-empty {
  padding: 12px 10px;
  color: #888;
  font-size: 13px;
  text-align: center;
}
</style>
