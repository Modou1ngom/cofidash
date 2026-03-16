<template>
  <div class="cr-par-agence-section">
    <div class="section-header">
      <h2 class="section-title">CR par Agence</h2>
      <span v-if="loadingData" class="loading-data-hint">Chargement des montants...</span>
    </div>

    <div v-if="loading" class="loading-state">Chargement...</div>
    <div v-else class="table-wrapper">
      <table class="cr-table">
        <thead>
          <tr class="header-row territory-row">
            <th class="col-poste sticky-col"></th>
            <th class="col-value col-fixed" colspan="1">SIEGE</th>
            <th class="col-value col-fixed" colspan="1">GRAND COMPTE</th>
            <th class="col-value territory-dakar-ville" colspan="5">TERRITOIRE DAKAR VILLE</th>
            <th class="col-value territory-dakar-banlieue" colspan="5">TERRITOIRE DAKAR BANLIEUE</th>
            <th class="col-value territory-centre-sud" colspan="5">TERRITOIRE PROVINCE CENTRE SUD</th>
            <th class="col-value territory-nord" colspan="5">TERRITOIRE PROVINCE NORD</th>
          </tr>
          <tr class="header-row agency-row">
            <th class="col-poste sticky-col">Poste</th>
            <th class="col-value">SIEGE</th>
            <th class="col-value">GRAND COMPTE</th>
            <th class="col-value" v-for="ag in agenciesDakarVille" :key="ag">{{ ag }}</th>
            <th class="col-value" v-for="ag in agenciesDakarBanlieue" :key="ag">{{ ag }}</th>
            <th class="col-value" v-for="ag in agenciesCentreSud" :key="ag">{{ ag }}</th>
            <th class="col-value" v-for="ag in agenciesNord" :key="ag">{{ ag }}</th>
          </tr>
        </thead>
        <tbody>
          <template v-for="(row, rowIndex) in visibleRows" :key="row.uniqueKey">
            <tr
              :class="[
                'data-row',
                row.type === 'total' ? 'row-total' : '',
                row.type === 'rubrique' ? 'row-rubrique' : '',
                row.type === 'sous-rubrique' ? 'row-sous-rubrique' : '',
                row.type === 'rubrique' && hasSousRubriques(row) ? 'row-expandable' : ''
              ]"
              @click="row.type === 'rubrique' && hasSousRubriques(row) ? toggleExpand(row.blocIndex) : null"
            >
              <td
                class="col-poste sticky-col"
                :class="{
                  'cell-bold': row.type === 'total' || row.type === 'rubrique'
                }"
              >
                <span v-if="row.type === 'sous-rubrique'" class="indent-sous-rubrique"></span>
                <span v-else-if="row.type === 'rubrique' && hasSousRubriques(row)" class="expand-icon-btn">
                  {{ expandedBlocIndex === row.blocIndex ? '−' : '+' }}
                </span>
                {{ row.label }}
              </td>
              <td
                v-for="col in entityKeys"
                :key="col"
                class="col-value cell-numeric"
                :class="{ 'cell-negative': getValue(row, col) < 0, 'cell-bold': row.type === 'total' || row.type === 'rubrique' }"
              >
                {{ formatNumber(getValue(row, col)) }}
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script>
const RUBRIQUES_TOTAL = [
  'PRODUIT NET BANCAIRE',
  'RESULTAT BRUT D\'EXPLOITATION',
  'RESULTAT NET D\'EXPLOITATION',
  'RESULTAT EXCEPTIONNEL',
  'RESULTAT AVANT IMPÔT',
  'RESULTAT NET',
  'Impôt sur le bénéfice (-)'
];

// Ordre d'affichage des postes (PRODUIT NET BANCAIRE avant CHARGES D'EXPLOITATION)
const CR_DISPLAY_ORDER = [
  'CHARGES D\'INTÉRÊTS',
  'PRODUITS D\'INTÉRÊTS',
  'MARGE NETTE D\'INTÉRÊTS',
  'COMMISSIONS NETTES',
  'PRODUIT NET BANCAIRE',
  'CHARGES D\'EXPLOITATION',
  'PRODUITS D\'EXPLOITATION',
  'RESULTAT BRUT D\'EXPLOITATION',
  'PROVISIONS POUR RISQUES & CHARGES',
  'COÛT NET DU RISQUE',
  'RESULTAT NET D\'EXPLOITATION',
  'RESULTAT EXCEPTIONNEL',
  'RESULTAT AVANT IMPÔT',
  'Impôt sur le bénéfice (-)',
  'RESULTAT NET'
];

// Formules officielles du compte de résultat (tous les opérandes en + ; charges/impôts déjà négatifs en données)
const FORMULA_MARGE_NETTE = [
  { coef: 1, libelle: 'PRODUITS D\'INTÉRÊTS' },
  { coef: 1, libelle: 'CHARGES D\'INTÉRÊTS' }
];
const RUBRIQUE_FORMULAS = {
  'MARGE NETTE D\'INTÉRÊTS': FORMULA_MARGE_NETTE,
  'MARGE NETTE D\'INTERÊTS': FORMULA_MARGE_NETTE,
  'PRODUIT NET BANCAIRE': [
    { coef: 1, libelle: 'MARGE NETTE' },
    { coef: 1, libelle: 'COMMISSIONS NETTES' }
  ],
  'RESULTAT BRUT D\'EXPLOITATION': [
    { coef: 1, libelle: 'PRODUIT NET BANCAIRE' },
    { coef: 1, libelle: 'CHARGES D\'EXPLOITATION' },
    { coef: 1, libelle: 'PRODUITS D\'EXPLOITATION' }
  ],
  'RESULTAT NET D\'EXPLOITATION': [
    { coef: 1, libelle: 'RESULTAT BRUT D\'EXPLOITATION' },
    { coef: 1, libelle: 'PROVISIONS POUR RISQUES & CHARGES' },
    { coef: 1, libelle: 'COÛT NET DU RISQUE' }
  ],
  'RESULTAT AVANT IMPÔT': [
    { coef: 1, libelle: 'RESULTAT NET D\'EXPLOITATION' },
    { coef: 1, libelle: 'RESULTAT EXCEPTIONNEL' }
  ],
  'RESULTAT NET': [
    { coef: 1, libelle: 'RESULTAT AVANT IMPÔT' },
    { coef: 1, libelle: 'Impôt sur le bénéfice (-)' }
  ]
};

export default {
  name: 'CRParAgenceSection',
  data() {
    return {
      agenciesDakarVille: ['POINT E', 'CASTORS', 'LAMINE GUEYE', 'MARISTES', 'SCAT URBAM'],
      agenciesDakarBanlieue: ['NIARRY TALLI', 'LINGUERLA', 'PARCELLES', 'PIKINE', 'RUFISQUE'],
      agenciesCentreSud: ['THIES', 'KAOLACK', 'MBOUR', 'TAMBACOUNDA', 'ZIGUINCHOR'],
      agenciesNord: ['TOUBA', 'SAINT LOUIS', 'DIOURBEL', 'LOUGA', 'OUROSSOGUI'],
      entityKeys: [
        'siege', 'grand_compte',
        'point_e', 'castors', 'lamine_gueye', 'maristes', 'scat_urbam',
        'niarry_talli', 'linguerla', 'parcelles', 'pikine', 'rufisque',
        'thies', 'kaolack', 'mbour', 'tambacounda', 'ziguinchor',
        'touba', 'saint_louis', 'diourbel', 'louga', 'ourossogui'
      ],
      referenceCompteBlocs: [],
      loading: false,
      loadingData: false,
      expandedBlocIndex: null,
      crRowData: {},
      dateFrom: '',
      dateTo: '',
      branchCodeToEntityKey: {
        '501': 'siege',
        '503': 'touba',
        '504': 'pikine',
        '507': 'kaolack',
        '508': 'thies',
        '511': 'diourbel',
        '516': 'louga',
        '517': 'lamine_gueye',
        '518': 'maristes',
        '519': 'scat_urbam',
        '522': 'ourossogui',
        '524': 'saint_louis',
        '543': 'ziguinchor'
      }
    };
  },
  computed: {
    visibleRows() {
      const blocs = this.referenceCompteBlocs || [];
      const withIndex = blocs.map((bloc, originalIndex) => ({ bloc, originalIndex }));
      const getOrderRank = (libelle) => {
        const L = (libelle || '').trim();
        let r = CR_DISPLAY_ORDER.indexOf(L);
        if (r === -1 && (L.includes('INTÉRÊTS') || L.includes('INTERÊTS'))) {
          const alt = L.includes('INTÉRÊTS') ? L.replace(/INTÉRÊTS/g, 'INTERÊTS') : L.replace(/INTERÊTS/g, 'INTÉRÊTS');
          r = CR_DISPLAY_ORDER.indexOf(alt);
        }
        return r === -1 ? 9999 : r;
      };
      withIndex.sort((a, b) => getOrderRank(a.bloc.libelle) - getOrderRank(b.bloc.libelle));

      const rows = [];
      withIndex.forEach(({ bloc, originalIndex: blocIndex }) => {
        const rubriqueKey = `rubrique-${blocIndex}`;
        const isTotal = RUBRIQUES_TOTAL.includes(bloc.libelle);
        rows.push({
          uniqueKey: rubriqueKey,
          type: isTotal ? 'total' : 'rubrique',
          label: bloc.libelle || '—',
          blocIndex,
          data: this.crRowData[rubriqueKey] || {}
        });
        if (this.expandedBlocIndex === blocIndex && (bloc.rubriques || []).length > 0) {
          (bloc.rubriques || []).forEach((sr, srIndex) => {
            const sousKey = `sous-${blocIndex}-${srIndex}`;
            rows.push({
              uniqueKey: sousKey,
              type: 'sous-rubrique',
              label: sr.libelle || '—',
              blocIndex,
              sousRubriqueIndex: srIndex,
              data: this.crRowData[sousKey] || {}
            });
          });
        }
      });
      return rows;
    }
  },
  mounted() {
    this.setDefaultDates();
    this.loadReferenceCompte();
  },
  methods: {
    setDefaultDates() {
      const d = new Date();
      this.dateTo = String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0') + '/' + d.getFullYear();
      this.dateFrom = '01/01/' + d.getFullYear();
    },
    branchNameToEntityKey(name) {
      if (!name) return null;
      let s = String(name).toUpperCase().trim();
      s = s.replace(/^AGENCE\s+/i, '').replace(/^C-E\s+/i, '').trim();
      s = s.replace(/^PRINCIPALE\s+/i, '').trim();
      s = s.replace(/\s+/g, '_');
      if (s === 'OUROSSOGUT') s = 'OUROSSOGUI';
      const map = {
        SIEGE: 'siege',
        GRAND_COMPTE: 'grand_compte',
        'POINT_E': 'point_e',
        POINTE: 'point_e',
        PRINCIPALE_POINT_E: 'point_e',
        CASTORS: 'castors',
        LAMINE_GUEYE: 'lamine_gueye',
        LAMINE_GUEVE: 'lamine_gueye',
        MARISTES: 'maristes',
        SCAT_URBAM: 'scat_urbam',
        NIARRY_TALLI: 'niarry_talli',
        LINGUERLA: 'linguerla',
        PARCELLES: 'parcelles',
        PIKINE: 'pikine',
        RUFISQUE: 'rufisque',
        THIES: 'thies',
        KAOLACK: 'kaolack',
        MBOUR: 'mbour',
        TAMBACOUNDA: 'tambacounda',
        ZIGUINCHOR: 'ziguinchor',
        TOUBA: 'touba',
        SAINT_LOUIS: 'saint_louis',
        DIOURBEL: 'diourbel',
        LOUGA: 'louga',
        OUROSSOGUI: 'ourossogui'
      };
      return map[s] || null;
    },
    mapCrResponseToEntityData(apiRows) {
      const data = {};
      this.entityKeys.forEach((k) => { data[k] = 0; });
      (apiRows || []).forEach((r) => {
        const branchCode = String(r.AC_BRANCH ?? r.ac_branch ?? '').trim();
        const branchName = r.BRANCH_NAME ?? r.branch_name ?? '';
        const m = r.MONTANT ?? r.montant;
        const montant = typeof m === 'number' ? m : Number(m) || 0;
        let key = this.branchNameToEntityKey(branchName);
        if (!key && branchCode && this.branchCodeToEntityKey) {
          key = this.branchCodeToEntityKey[branchCode];
        }
        if (key) data[key] = (data[key] || 0) + montant;
      });
      return data;
    },
    async loadReferenceCompte() {
      this.loading = true;
      try {
        const res = await window.axios.get('/api/reference-compte');
        const data = res.data && res.data.data;
        this.referenceCompteBlocs = Array.isArray(data) ? data : [];
        await this.loadCrData();
      } catch (err) {
        console.warn('CR par Agence: chargement référence compte', err);
        this.referenceCompteBlocs = [];
      } finally {
        this.loading = false;
      }
    },
    extractCrRows(raw) {
      if (Array.isArray(raw)) return raw;
      if (!raw || typeof raw !== 'object') return [];
      if (Array.isArray(raw.data)) return raw.data;
      if (raw.data && typeof raw.data === 'object' && Array.isArray(raw.data.data)) return raw.data.data;
      return [];
    },
    async loadCrData() {
      if (!this.dateFrom || !this.dateTo) return;
      this.loadingData = true;
      const newCrRowData = {};
      try {
        const blocs = this.referenceCompteBlocs || [];
        for (let blocIndex = 0; blocIndex < blocs.length; blocIndex++) {
          const bloc = blocs[blocIndex];
          const rubriqueKey = `rubrique-${blocIndex}`;
          let rubriqueData = null;
          const sousRubriques = bloc.rubriques || [];
          for (let srIndex = 0; srIndex < sousRubriques.length; srIndex++) {
            const sr = sousRubriques[srIndex];
            const gls = sr.gls || [];
            const parentGlCodes = gls.map((g) => (g.numero_gl || '').trim()).filter(Boolean);
            if (parentGlCodes.length === 0) continue;
            try {
              const res = await window.axios.post('/api/oracle/data/cr-par-agence', {
                date_from: this.dateFrom,
                date_to: this.dateTo,
                parent_gl_codes: parentGlCodes
              });
              const rows = this.extractCrRows(res.data);
              const rowData = this.mapCrResponseToEntityData(rows);
              const sousKey = `sous-${blocIndex}-${srIndex}`;
              newCrRowData[sousKey] = rowData;
              if (!rubriqueData) rubriqueData = { ...rowData };
              else this.entityKeys.forEach((k) => { rubriqueData[k] = (rubriqueData[k] || 0) + (rowData[k] || 0); });
            } catch (err) {
              console.warn(`CR data sous-rubrique ${blocIndex}-${srIndex}:`, err);
            }
          }
          if (rubriqueData) newCrRowData[rubriqueKey] = rubriqueData;
        }
        this.crRowData = newCrRowData;
      } finally {
        this.loadingData = false;
      }
    },
    hasSousRubriques(row) {
      if (row.type !== 'rubrique' || row.blocIndex == null) return false;
      const bloc = this.referenceCompteBlocs[row.blocIndex];
      return bloc && (bloc.rubriques || []).length > 0;
    },
    toggleExpand(blocIndex) {
      this.expandedBlocIndex = this.expandedBlocIndex === blocIndex ? null : blocIndex;
    },
    getEntityDataByBlocLibelle(libelle) {
      const blocs = this.referenceCompteBlocs || [];
      const trim = (s) => (s || '').trim();
      const target = trim(libelle);
      let idx = blocs.findIndex((b) => trim(b.libelle) === target);
      if (idx === -1 && (target.includes('INTÉRÊTS') || target.includes('INTERÊTS'))) {
        const alt = target.includes('INTÉRÊTS') ? target.replace(/INTÉRÊTS/g, 'INTERÊTS') : target.replace(/INTERÊTS/g, 'INTÉRÊTS');
        idx = blocs.findIndex((b) => trim(b.libelle) === alt);
      }
      if (idx === -1 && target === 'MARGE NETTE') {
        idx = blocs.findIndex((b) => trim(b.libelle || '').startsWith('MARGE NETTE'));
      }
      if (idx === -1) return {};
      return this.crRowData[`rubrique-${idx}`] || {};
    },
    getFormulaForLabel(label) {
      if (!label) return null;
      return RUBRIQUE_FORMULAS[label] || RUBRIQUE_FORMULAS[label.replace(/INTERÊTS/g, 'INTÉRÊTS')] || RUBRIQUE_FORMULAS[label.replace(/INTÉRÊTS/g, 'INTERÊTS')] || null;
    },
    getValue(row, colKey) {
      const formula = this.getFormulaForLabel(row.label);
      if (formula) {
        let sum = 0;
        for (const term of formula) {
          const data = this.getEntityDataByBlocLibelle(term.libelle);
          const v = data[colKey];
          const num = v !== undefined && v !== null ? Number(v) : 0;
          sum += term.coef * (isNaN(num) ? 0 : num);
        }
        return sum;
      }
      const val = row.data && row.data[colKey];
      return val !== undefined && val !== null ? val : 0;
    },
    formatNumber(num) {
      if (num === 0) return '0';
      const n = Number(num);
      if (isNaN(n)) return '';
      return new Intl.NumberFormat('fr-FR', { minimumFractionDigits: 0, maximumFractionDigits: 0 }).format(n);
    }
  }
};
</script>

<style scoped>
.cr-par-agence-section {
  padding: 0;
  width: 100%;
}

.section-header {
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.loading-state {
  padding: 24px;
  text-align: center;
  background: #f9fafb;
  border-radius: 8px;
  color: #6b7280;
}

.loading-data-hint {
  font-size: 0.85rem;
  color: #6b7280;
  margin-left: 12px;
}

.section-title {
  font-size: 1.35rem;
  color: #1A4D3A;
  margin: 0;
  font-weight: 600;
}

.table-wrapper {
  overflow: auto;
  max-width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.cr-table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 0.8rem;
}

.cr-table th,
.cr-table td {
  border: 1px solid #e5e7eb;
  padding: 8px 12px;
  text-align: left;
  white-space: nowrap;
}

.cr-table th.col-value,
.cr-table td.col-value {
  text-align: right;
  min-width: 100px;
}

.cr-table .col-poste {
  min-width: 280px;
  max-width: 320px;
  text-align: left;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: #fff;
  z-index: 2;
  box-shadow: 2px 0 4px rgba(0, 0, 0, 0.04);
}

/* En-têtes */
.header-row th {
  background: #f3f4f6;
  font-weight: 600;
  color: #374151;
}

.territory-row th {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.02em;
  text-align: center;
  color: #fff;
  font-weight: 700;
}

.territory-row th.col-poste,
.territory-row th.col-fixed {
  background: #f3f4f6;
  color: #374151;
}

/* Couleurs des territoires (ligne d'en-tête) */
.territory-row th.territory-dakar-ville {
  background: #b91c1c !important;
  color: #fff !important;
}

.territory-row th.territory-dakar-banlieue {
  background: #1d4ed8 !important;
  color: #fff !important;
}

.territory-row th.territory-centre-sud {
  background: #15803d !important;
  color: #fff !important;
}

.territory-row th.territory-nord {
  background: #92400e !important;
  color: #fff !important;
}

.agency-row th {
  font-size: 0.78rem;
  background: #1f2937;
  color: #fff;
  font-weight: 600;
}

/* Couleurs des territoires sur la ligne agences (teinte par groupe) */
.agency-row th:nth-child(4),
.agency-row th:nth-child(5),
.agency-row th:nth-child(6),
.agency-row th:nth-child(7),
.agency-row th:nth-child(8) {
  background: #7f1d1d;
  color: #fff;
}
.agency-row th:nth-child(9),
.agency-row th:nth-child(10),
.agency-row th:nth-child(11),
.agency-row th:nth-child(12),
.agency-row th:nth-child(13) {
  background: #1e3a8a;
  color: #fff;
}
.agency-row th:nth-child(14),
.agency-row th:nth-child(15),
.agency-row th:nth-child(16),
.agency-row th:nth-child(17),
.agency-row th:nth-child(18) {
  background: #14532d;
  color: #fff;
}
.agency-row th:nth-child(19),
.agency-row th:nth-child(20),
.agency-row th:nth-child(21),
.agency-row th:nth-child(22),
.agency-row th:nth-child(23) {
  background: #78350f;
  color: #fff;
}

.agency-row th.sticky-col,
.agency-row th:nth-child(2),
.agency-row th:nth-child(3) {
  background: #1f2937 !important;
  color: #fff;
}

/* Lignes de données */
.data-row td {
  background: #fff;
  color: #374151;
}

/* Teinte territoire sur les colonnes de données */
.data-row td:nth-child(4),
.data-row td:nth-child(5),
.data-row td:nth-child(6),
.data-row td:nth-child(7),
.data-row td:nth-child(8) {
  background: #fef2f2;
}
.data-row td:nth-child(9),
.data-row td:nth-child(10),
.data-row td:nth-child(11),
.data-row td:nth-child(12),
.data-row td:nth-child(13) {
  background: #eff6ff;
}
.data-row td:nth-child(14),
.data-row td:nth-child(15),
.data-row td:nth-child(16),
.data-row td:nth-child(17),
.data-row td:nth-child(18) {
  background: #f0fdf4;
}
.data-row td:nth-child(19),
.data-row td:nth-child(20),
.data-row td:nth-child(21),
.data-row td:nth-child(22),
.data-row td:nth-child(23) {
  background: #fef3c7;
}

.row-rubrique .sticky-col,
.row-rubrique td {
  background: #f3f4f6;
  color: #374151;
}

.row-expandable {
  cursor: pointer;
}

.row-expandable:hover .sticky-col,
.row-expandable:hover td {
  background: #e5e7eb;
}

.expand-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  margin-right: 8px;
  background: #1f2937;
  color: #fff;
  font-size: 1rem;
  font-weight: 600;
  line-height: 1;
  border-radius: 2px;
  vertical-align: middle;
}

.row-sous-rubrique .sticky-col,
.row-sous-rubrique td {
  background: #f9fafb;
  color: #374151;
}

.indent-sous-rubrique {
  display: inline-block;
  width: 24px;
  margin-right: 4px;
}

.row-line .sticky-col,
.row-line td {
  background: #f3f4f6;
  color: #374151;
}

.row-line td:nth-child(4),
.row-line td:nth-child(5),
.row-line td:nth-child(6),
.row-line td:nth-child(7),
.row-line td:nth-child(8) {
  background: #fee2e2;
}
.row-line td:nth-child(9),
.row-line td:nth-child(10),
.row-line td:nth-child(11),
.row-line td:nth-child(12),
.row-line td:nth-child(13) {
  background: #dbeafe;
}
.row-line td:nth-child(14),
.row-line td:nth-child(15),
.row-line td:nth-child(16),
.row-line td:nth-child(17),
.row-line td:nth-child(18) {
  background: #dcfce7;
}
.row-line td:nth-child(19),
.row-line td:nth-child(20),
.row-line td:nth-child(21),
.row-line td:nth-child(22),
.row-line td:nth-child(23) {
  background: #fde68a;
}

.row-total .sticky-col,
.row-total td {
  background: #b91c1c !important;
  color: #fff !important;
  font-weight: 700;
}

.cell-numeric {
  font-variant-numeric: tabular-nums;
}

.cell-negative {
  color: #b91c1c;
  font-weight: 500;
}

.row-total .cell-negative {
  color: #fecaca;
}

.cell-bold {
  font-weight: 600;
}

@media (max-width: 768px) {
  .cr-table {
    font-size: 0.75rem;
  }

  .cr-table th,
  .cr-table td {
    padding: 6px 8px;
    min-width: 80px;
  }

  .cr-table .col-poste {
    min-width: 200px;
  }
}
</style>
