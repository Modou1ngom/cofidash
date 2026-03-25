<template>
  <div class="cr-par-agence-section">
    <div class="section-header">
      <h2 class="section-title">CR par Agence</h2>
      <span v-if="loading || loadingData" class="loading-data-hint">Chargement des données...</span>
      <span v-else-if="crLoadErrors > 0" class="load-errors-hint">Certaines données n'ont pas pu être chargées (service Oracle indisponible ou erreur).</span>
    </div>

    <div class="table-wrapper" :class="{ 'table-loading': loading || loadingData }">
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
                row.type === 'total' && !isNeutralNegativeRow(row) ? 'row-total' : '',
                row.type === 'rubrique' ? 'row-rubrique' : '',
                row.type === 'sous-rubrique' ? 'row-sous-rubrique' : '',
                row.type === 'cle_repartition' || row.isCleRepartition ? 'row-cle-repartition' : '',
                hasSousRubriques(row) ? 'row-expandable' : ''
              ]"
              @click="hasSousRubriques(row) ? toggleExpand(row.blocIndex) : null"
            >
              <td
                class="col-poste sticky-col"
                :class="{
                  'cell-bold': row.type === 'total' || row.type === 'rubrique'
                }"
              >
                <span v-if="row.type === 'sous-rubrique'" class="indent-sous-rubrique"></span>
                <button
                  v-else-if="hasSousRubriques(row)"
                  type="button"
                  class="expand-btn"
                  @click.stop="toggleExpand(row.blocIndex)"
                  :aria-label="expandedSections[row.blocIndex] ? 'Replier' : 'Déplier'"
                >
                  {{ expandedSections[row.blocIndex] ? '−' : '+' }}
                </button>
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
  'Impôt sur le bénéfice (-)',
  'RESULTAT NET'
 
];

// Ordre d'affichage strict (alignement comme la capture officielle)
const CR_DISPLAY_ORDER = [
  'PRODUITS D\'INTÉRÊTS',
  'CHARGES D\'INTÉRÊTS',
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

function normalizeLibelle(s) {
  const t = (s || '').trim();
  return t.replace(/^[_\-]\s*/, '').trim();
}

/** Même ligne « clé répartition » que la sous-rubrique (ex. nom clé vs libellé avec « (-) »). */
function libelleCorrespondCleRepartition(nomCle, libelle) {
  if (!nomCle || !libelle) return false;
  const n = normalizeLibelle(nomCle).toLowerCase();
  const l = normalizeLibelle(libelle).toLowerCase();
  if (n === l) return true;
  const lSansParen = l.replace(/\s*\([^)]*\)\s*$/, '').trim();
  return n === lSansParen;
}

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
      expandedSections: {},
      crRowData: {},
      crLoadErrors: 0,
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
        const L = normalizeLibelle(libelle || '');
        let r = CR_DISPLAY_ORDER.indexOf(L);
        if (r === -1 && (L.includes('INTÉRÊTS') || L.includes('INTERÊTS'))) {
          const alt = L.includes('INTÉRÊTS') ? L.replace(/INTÉRÊTS/g, 'INTERÊTS') : L.replace(/INTERÊTS/g, 'INTÉRÊTS');
          r = CR_DISPLAY_ORDER.indexOf(alt);
        }
        if (r === -1 && /RESULTAT\s*BRUT/i.test(L) && L.includes('EXPLOITATION') && !/RESULTAT\s*NET\s*D/i.test(L)) return 7;
        if (r === -1 && L.includes('PROVISIONS') && L.includes('RISQUES')) return 8;
        if (r === -1 && /COÛT\s*NET\s*DU\s*RISQUE/i.test(L)) return 9;
        if (r === -1 && /RESULTAT\s*NET\s*D/i.test(L) && L.includes('EXPLOITATION')) return 10;
        if (r === -1 && /RESULTAT\s*EXCEPTIONNEL/i.test(L)) return 11;
        if (r === -1 && /RESULTAT\s*AVANT\s*IMPÔT/i.test(L)) return 12;
        if (r === -1 && /^Impôt sur le bénéfice/i.test(L)) return 13;
        if (r === -1 && (/^RESULTAT\s*NET$/i.test(L) || L.trim() === 'RESULTAT NET')) return 14;
        return r === -1 ? 9999 : r;
      };
      withIndex.sort((a, b) => getOrderRank(a.bloc.libelle) - getOrderRank(b.bloc.libelle));

      const rows = [];
      withIndex.forEach(({ bloc, originalIndex: blocIndex }) => {
        const rubriqueKey = `rubrique-${blocIndex}`;
        const isTotal = RUBRIQUES_TOTAL.includes(bloc.libelle) || RUBRIQUES_TOTAL.includes(normalizeLibelle(bloc.libelle));
        rows.push({
          uniqueKey: rubriqueKey,
          type: isTotal ? 'total' : 'rubrique',
          label: bloc.libelle || '—',
          blocIndex,
          data: this.crRowData[rubriqueKey] || {}
        });
        if (this.expandedSections[blocIndex] && (bloc.rubriques || []).length > 0) {
          (bloc.rubriques || []).forEach((sr, srIndex) => {
            const sousKey = `sous-${blocIndex}-${srIndex}`;
            const nomCle = (bloc.cle_repartition_nom || '').trim();
            const cr = bloc.cle_repartition && typeof bloc.cle_repartition === 'object' ? bloc.cle_repartition : {};
            const useCleForThisSousRubrique = nomCle && normalizeLibelle(sr.libelle || '') === normalizeLibelle(nomCle);
            const estLigneCle = nomCle && libelleCorrespondCleRepartition(nomCle, sr.libelle || '');
            const data = useCleForThisSousRubrique ? cr : (this.crRowData[sousKey] || {});
            rows.push({
              uniqueKey: sousKey,
              type: 'sous-rubrique',
              isCleRepartition: estLigneCle,
              label: sr.libelle || '—',
              blocIndex,
              sousRubriqueIndex: srIndex,
              data
            });
          });
        }
      });

      const rowMatchesLibelle = (row, libelle) => {
        const L = normalizeLibelle(libelle || '');
        const rowL = normalizeLibelle(row.label || '');
        if (rowL === L) return true;
        if ((L.includes('INTÉRÊTS') || L.includes('INTERÊTS')) && (rowL.includes('INTÉRÊTS') || rowL.includes('INTERÊTS'))) {
          const alt = L.includes('INTÉRÊTS') ? L.replace(/INTÉRÊTS/g, 'INTERÊTS') : L.replace(/INTERÊTS/g, 'INTÉRÊTS');
          return rowL === alt;
        }
        return false;
      };
      CR_DISPLAY_ORDER.forEach((libelle, rank) => {
        if (rows.some((r) => rowMatchesLibelle(r, libelle))) return;
        const isTotal = RUBRIQUES_TOTAL.includes(libelle);
        const synthetic = {
          uniqueKey: `synthetic-${rank}-${libelle.replace(/\s+/g, '-')}`,
          type: isTotal ? 'total' : 'rubrique',
          label: libelle,
          blocIndex: null,
          data: {}
        };
        const idx = rows.findIndex((r) => (r.type === 'rubrique' || r.type === 'total') && getOrderRank(r.label) > rank);
        if (idx === -1) rows.push(synthetic);
        else rows.splice(idx, 0, synthetic);
      });

      withIndex.forEach(({ bloc, originalIndex: blocIndex }) => {
        const nom = (bloc.cle_repartition_nom || '').trim();
        const cr = bloc.cle_repartition && typeof bloc.cle_repartition === 'object' ? bloc.cle_repartition : {};
        const hasValues = this.entityKeys.some((k) => cr[k] != null && Number(cr[k]) !== 0);
        const labelCle = nom || 'Clé répartition';
        const memeNomQuUneSousRubrique = (bloc.rubriques || []).some(
          (r) => normalizeLibelle(r.libelle || '') === normalizeLibelle(labelCle)
        );
        if ((nom || hasValues) && !memeNomQuUneSousRubrique) {
          rows.push({
            uniqueKey: `cle-repartition-${blocIndex}`,
            type: 'cle_repartition',
            label: labelCle,
            blocIndex,
            data: cr
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
      this._entityDataCache = {};
      try {
        const res = await window.axios.get('/api/reference-compte');
        const data = res.data != null && res.data.data != null ? res.data.data : null;
        this.referenceCompteBlocs = Array.isArray(data) ? data : [];
        // Afficher les sous-rubriques par défaut pour éviter l'impression de rubriques manquantes.
        const expanded = {};
        this.referenceCompteBlocs.forEach((bloc, idx) => {
          const hasChildren = Array.isArray(bloc?.rubriques) && bloc.rubriques.length > 0;
          const labelNorm = String(bloc?.libelle || '')
            .toUpperCase()
            .trim()
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .replace(/^[_\-]\s*/, '')
            .trim();
          const neutralToggleDefault = labelNorm === 'RESULTAT EXCEPTIONNEL' || labelNorm.includes('IMPOT SUR LE BENEFICE');
          // Garder ces lignes repliées pour qu'elles affichent bien le bouton `+`.
          expanded[idx] = hasChildren && !neutralToggleDefault;
        });
        this.expandedSections = expanded;
      } catch (err) {
        console.warn('CR par Agence: chargement référence compte', err);
        this.referenceCompteBlocs = [];
        this.expandedSections = {};
      } finally {
        this.loading = false;
      }
      try {
        await this.loadCrData();
      } catch (err) {
        console.warn('CR par Agence: chargement données CR', err);
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
      this.crLoadErrors = 0;
      this._entityDataCache = {};
      const newCrRowData = {};
      try {
        const blocs = this.referenceCompteBlocs || [];
        let errorCount = 0;
        for (let blocIndex = 0; blocIndex < blocs.length; blocIndex++) {
          const bloc = blocs[blocIndex];
          const rubriqueKey = `rubrique-${blocIndex}`;
          let rubriqueData = null;
          const nomCle = (bloc.cle_repartition_nom || '').trim();
          const cr = bloc.cle_repartition && typeof bloc.cle_repartition === 'object' ? bloc.cle_repartition : {};
          const sousRubriques = bloc.rubriques || [];
          for (let srIndex = 0; srIndex < sousRubriques.length; srIndex++) {
            const sr = sousRubriques[srIndex];
            const useCleForSousRubrique = nomCle && normalizeLibelle(sr.libelle || '') === normalizeLibelle(nomCle);
            const gls = sr.gls || [];
            const parentGlCodes = gls.map((g) => (g.numero_gl || '').trim()).filter(Boolean);
            const sousKey = `sous-${blocIndex}-${srIndex}`;
            let dataToStore = useCleForSousRubrique ? cr : null;
            if (!useCleForSousRubrique && parentGlCodes.length > 0) {
              try {
                const res = await window.axios.post('/api/oracle/data/cr-par-agence', {
                  date_from: this.dateFrom,
                  date_to: this.dateTo,
                  parent_gl_codes: parentGlCodes
                });
                const rows = this.extractCrRows(res.data);
                dataToStore = this.mapCrResponseToEntityData(rows);
              } catch (err) {
                errorCount += 1;
              }
            }
            if (dataToStore != null) {
              newCrRowData[sousKey] = dataToStore;
              if (!rubriqueData) rubriqueData = { ...dataToStore };
              else this.entityKeys.forEach((k) => { rubriqueData[k] = (rubriqueData[k] || 0) + (dataToStore[k] || 0); });
            }
          }
          if (rubriqueData) newCrRowData[rubriqueKey] = rubriqueData;
        }
        this.crRowData = newCrRowData;
        this.crLoadErrors = errorCount;
      } finally {
        this.loadingData = false;
      }
    },
    hasSousRubriques(row) {
      if (!row || (row.type !== 'rubrique' && row.type !== 'total') || row.blocIndex == null) return false;
      const bloc = this.referenceCompteBlocs[row.blocIndex];
      return bloc && (bloc.rubriques || []).length > 0;
    },
    toggleExpand(blocIndex) {
      this.expandedSections[blocIndex] = !this.expandedSections[blocIndex];
    },
    isNeutralNegativeRow(row) {
      const label = row && row.label ? String(row.label) : '';
      // Normaliser pour comparer sans accents/espaces parasites
      const norm = label
        .toUpperCase()
        .trim()
        .normalize('NFD')
        .replace(/[\u0300-\u036f]/g, '')
        .replace(/^[_\-]\s*/, '')
        .trim();

      return norm === 'RESULTAT EXCEPTIONNEL' || norm.includes('IMPOT SUR LE BENEFICE');
    },
    getEntityDataByBlocLibelle(libelle) {
      if (!this._entityDataCache) this._entityDataCache = {};
      const target = normalizeLibelle(libelle);
      if (this._entityDataCache[target] !== undefined) return this._entityDataCache[target];
      const blocs = this.referenceCompteBlocs || [];
      let idx = blocs.findIndex((b) => normalizeLibelle(b.libelle) === target);
      if (idx === -1 && (target.includes('INTÉRÊTS') || target.includes('INTERÊTS'))) {
        const alt = target.includes('INTÉRÊTS') ? target.replace(/INTÉRÊTS/g, 'INTERÊTS') : target.replace(/INTERÊTS/g, 'INTÉRÊTS');
        idx = blocs.findIndex((b) => normalizeLibelle(b.libelle) === alt);
      }
      if (idx === -1 && target === 'MARGE NETTE') {
        idx = blocs.findIndex((b) => normalizeLibelle(b.libelle || '').startsWith('MARGE NETTE'));
      }
      if (idx !== -1) {
        const bloc = blocs[idx];
        const rubriqueKey = `rubrique-${idx}`;
        const row = {
          label: bloc.libelle || '—',
          blocIndex: idx,
          data: this.crRowData[rubriqueKey] || {},
          type: (RUBRIQUES_TOTAL.includes(bloc.libelle) || RUBRIQUES_TOTAL.includes(normalizeLibelle(bloc.libelle))) ? 'total' : 'rubrique'
        };
        const out = {};
        this.entityKeys.forEach((k) => { out[k] = this.getValue(row, k); });
        this._entityDataCache[target] = out;
        return out;
      }
      // Ligne absente de la référence : si c'est une ligne calculée, calculer par formule
      for (const [formulaLabel, formula] of Object.entries(RUBRIQUE_FORMULAS)) {
        const normalizedFormula = normalizeLibelle(formulaLabel);
        if (normalizedFormula === target || normalizedFormula.startsWith(target)) {
          const out = {};
          this.entityKeys.forEach((k) => {
            let sum = 0;
            for (const term of formula) {
              const data = this.getEntityDataByBlocLibelle(term.libelle);
              const v = data[k];
              const num = v !== undefined && v !== null ? Number(v) : 0;
              sum += term.coef * (isNaN(num) ? 0 : num);
            }
            out[k] = sum;
          });
          this._entityDataCache[target] = out;
          return out;
        }
      }
      const out = {};
      this.entityKeys.forEach((k) => { out[k] = 0; });
      this._entityDataCache[target] = out;
      return out;
    },
    getFormulaForLabel(label) {
      if (!label) return null;
      const L = normalizeLibelle(label);
      return RUBRIQUE_FORMULAS[L] || RUBRIQUE_FORMULAS[label] || RUBRIQUE_FORMULAS[L.replace(/INTERÊTS/g, 'INTÉRÊTS')] || RUBRIQUE_FORMULAS[L.replace(/INTÉRÊTS/g, 'INTERÊTS')] || null;
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
  font-size: 0.9rem;
  color: #1A4D3A;
  margin-left: 12px;
  font-weight: 500;
}

.load-errors-hint {
  font-size: 0.85rem;
  color: #b45309;
  margin-left: 12px;
}

.section-title {
  font-size: 1.35rem;
  color: #1A4D3A;
  margin: 0;
  font-weight: 600;
}

.table-wrapper.table-loading {
  position: relative;
  opacity: 0.92;
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

.row-expandable .col-poste.sticky-col {
  display: flex;
  align-items: center;
  gap: 8px;
}

.expand-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(26, 77, 58, 0.35);
  background: rgba(26, 77, 58, 0.08);
  color: #1A4D3A;
  border-radius: 4px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
  transition: background 0.2s;
}

.expand-btn:hover {
  background: rgba(26, 77, 58, 0.15);
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

.row-cle-repartition .sticky-col,
.row-cle-repartition td {
  color: #b91c1c !important;
  font-weight: 600;
}

.indent-sous-rubrique {
  display: inline-block;
  width: 32px;
  margin-right: 8px;
  vertical-align: middle;
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
