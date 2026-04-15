<template>
  <div class="reference-compte-form">
    <div class="section-header">
      <h2 class="section-title">Ajouter une référence compte</h2>
    </div>

    <div class="form-container">
      <div class="ref-form-layout">
        <nav class="rubrique-nav-form" aria-label="Rubriques à ajouter">
          <p class="rubrique-nav-title">Rubriques</p>
          <ul class="rubrique-nav-list">
            <li v-for="(bloc, blocIndex) in blocs" :key="'navf-' + blocIndex">
              <button
                type="button"
                class="rubrique-nav-item"
                :class="{ active: selectedBlocIndex === blocIndex }"
                @click="selectedBlocIndex = blocIndex"
              >
                <span class="nav-num">Rubrique {{ blocIndex + 1 }}</span>
                <span class="nav-libelle">{{ bloc.libelle || 'Sans libellé' }}</span>
              </button>
            </li>
          </ul>
          <button type="button" class="btn-add-bloc-nav" @click="addBlocFromNav">+ Ajouter une rubrique</button>
        </nav>
        <div v-if="blocs[selectedBlocIndex]" class="rubrique-detail-form">
      <div class="form-card bloc-card">
        <div class="bloc-header">
          <span class="bloc-label">Rubrique {{ selectedBlocIndex + 1 }}</span>
          <div class="form-group bloc-libelle-inline">
            <label>Libellé de la rubrique</label>
            <input
              v-model="blocs[selectedBlocIndex].libelle"
              type="text"
              class="form-input"
              placeholder="Ex: Actif, Passif, Produits..."
            />
          </div>
          <button
            type="button"
            class="btn-remove"
            @click="removeBloc(selectedBlocIndex)"
            title="Supprimer la rubrique"
          >
            ✕
          </button>
        </div>

        <div class="rubriques-in-bloc">
          <div v-for="(rubrique, rubriqueIndex) in blocs[selectedBlocIndex].rubriques" :key="rubriqueIndex" class="form-card rubrique-card">
            <div class="rubrique-header">
              <span class="rubrique-label">Sous-rubrique {{ rubriqueIndex + 1 }}</span>
              <button
                type="button"
                class="btn-remove"
                @click="removeRubrique(selectedBlocIndex, rubriqueIndex)"
                title="Supprimer la sous-rubrique"
              >
                ✕
              </button>
            </div>

            <div class="form-group">
              <label>Libellé</label>
              <input
                v-model="rubrique.libelle"
                type="text"
                class="form-input"
                placeholder="Libellé de la sous-rubrique"
              />
            </div>

            <div class="gl-section">
              <div class="gl-header">
                <label>Parent GL (un ou plusieurs)</label>
                <button type="button" class="btn-add-small" @click="addGl(selectedBlocIndex, rubriqueIndex)">+ Ajouter un parent GL</button>
              </div>

              <div v-for="(gl, glIndex) in rubrique.gls" :key="glIndex" class="gl-row">
                <div class="gl-fields">
                  <div class="form-group gl-numero gl-numero-only">
                    <label>Numéro parent GL</label>
                    <input
                      v-model="gl.numero_gl"
                      type="text"
                      class="form-input"
                      placeholder="Ex: 702930000000"
                    />
                  </div>
                </div>
                <button type="button" class="btn-remove-small" @click="removeGl(selectedBlocIndex, rubriqueIndex, glIndex)" title="Supprimer ce parent GL">✕</button>
              </div>
            </div>
          </div>

          <button type="button" class="btn-add-rubrique" @click="addRubrique(selectedBlocIndex)">+ Ajouter une sous-rubrique</button>

        <div v-if="!isCleRepartitionVisible(selectedBlocIndex)" class="cle-repartition-add-row">
          <button type="button" class="btn-add-cle-repartition" @click="showCleRepartition(selectedBlocIndex)">
            + Ajouter une clé de répartition
          </button>
        </div>
        <div v-else class="cle-repartition-in-bloc form-card rubrique-card">
          <h4 class="cle-repartition-title">Clé répartition (cette rubrique)</h4>
          <div class="form-group">
            <label>Nom de la clé</label>
            <input
              v-model="blocs[selectedBlocIndex].cle_repartition_nom"
              type="text"
              class="form-input"
              placeholder="Ex: Répartition commissions, Répartition PNB..."
            />
          </div>
          <p class="cle-repartition-desc">Valeurs par agence (affichées dans le tableau CR par Agence).</p>
          <div class="cle-repartition-grid">
            <div v-for="item in cleRepartitionItems" :key="item.key" class="cle-repartition-field">
              <label :for="'cle-' + selectedBlocIndex + '-' + item.key">{{ item.label }}</label>
              <input
                :id="'cle-' + selectedBlocIndex + '-' + item.key"
                v-model.number="blocs[selectedBlocIndex].cle_repartition[item.key]"
                type="number"
                step="any"
                class="form-input cle-repartition-input"
                placeholder="0"
              />
            </div>
          </div>
        </div>
        </div>
      </div>
        </div>
      </div>

      <button type="button" class="btn-add-bloc" @click="addBloc">+ Ajouter une rubrique</button>

      <div class="save-row">
        <button type="button" class="btn-save" :disabled="saving" @click="enregistrer">
          {{ saving ? 'Enregistrement...' : 'Enregistrer' }}
        </button>
        <p v-if="saveMessage" class="save-message" :class="{ error: saveError }">{{ saveMessage }}</p>
      </div>
    </div>
  </div>
</template>

<script>
const CLE_REPARTITION_ENTITIES = [
  { key: 'siege', label: 'SIEGE' },
  { key: 'grand_compte', label: 'GRAND COMPTE' },
  { key: 'point_e', label: 'POINT E' },
  { key: 'castors', label: 'CASTORS' },
  { key: 'lamine_gueye', label: 'LAMINE GUEYE' },
  { key: 'maristes', label: 'MARISTES' },
  { key: 'scat_urbam', label: 'SCAT URBAM' },
  { key: 'niarry_talli', label: 'NIARRY TALLI' },
  { key: 'linguerla', label: 'LINGUERLA' },
  { key: 'parcelles', label: 'PARCELLES' },
  { key: 'pikine', label: 'PIKINE' },
  { key: 'rufisque', label: 'RUFISQUE' },
  { key: 'thies', label: 'THIES' },
  { key: 'kaolack', label: 'KAOLACK' },
  { key: 'mbour', label: 'MBOUR' },
  { key: 'tambacounda', label: 'TAMBACOUNDA' },
  { key: 'ziguinchor', label: 'ZIGUINCHOR' },
  { key: 'touba', label: 'TOUBA' },
  { key: 'saint_louis', label: 'SAINT LOUIS' },
  { key: 'diourbel', label: 'DIOURBEL' },
  { key: 'louga', label: 'LOUGA' },
  { key: 'ourossogui', label: 'OUROSSOGUI' }
];

function defaultCleRepartition() {
  const o = {};
  CLE_REPARTITION_ENTITIES.forEach(({ key }) => { o[key] = 0; });
  return o;
}

export default {
  name: 'ReferenceCompteForm',
  data() {
    return {
      blocs: [
        {
          libelle: '',
          cle_repartition_nom: '',
          cle_repartition: defaultCleRepartition(),
          rubriques: [
            { libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }
          ]
        }
      ],
      saving: false,
      saveMessage: '',
      saveError: false,
      showCleRepartitionByIndex: [false],
      selectedBlocIndex: 0
    };
  },
  computed: {
    cleRepartitionItems() {
      return CLE_REPARTITION_ENTITIES;
    },
    /** Map blocIndex -> true si la section clé répartition est visible (pour réactivité fiable). */
    cleRepartitionVisibleMap() {
      const map = {};
      this.showCleRepartitionByIndex.forEach((val, i) => {
        map[i] = !!val;
      });
      return map;
    }
  },
  methods: {
    defaultCleRepartition,
    isCleRepartitionVisible(blocIndex) {
      return !!this.cleRepartitionVisibleMap[blocIndex];
    },
    addBloc() {
      this.blocs.push({
        libelle: '',
        cle_repartition_nom: '',
        cle_repartition: defaultCleRepartition(),
        rubriques: [{ libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }]
      });
      this.showCleRepartitionByIndex.push(false);
      this.selectedBlocIndex = this.blocs.length - 1;
    },
    addBlocFromNav() {
      this.addBloc();
    },
    showCleRepartition(blocIndex) {
      const next = [...this.showCleRepartitionByIndex];
      next[blocIndex] = true;
      this.showCleRepartitionByIndex = next;
    },
    removeBloc(index) {
      this.blocs.splice(index, 1);
      this.showCleRepartitionByIndex.splice(index, 1);
      if (this.blocs.length === 0) {
        this.blocs.push({
          libelle: '',
          cle_repartition_nom: '',
          cle_repartition: defaultCleRepartition(),
          rubriques: [{ libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }]
        });
        this.showCleRepartitionByIndex = [false];
        this.selectedBlocIndex = 0;
      } else {
        this.selectedBlocIndex = Math.min(index, this.blocs.length - 1);
      }
    },
    addRubrique(blocIndex) {
      this.blocs[blocIndex].rubriques.push({
        libelle: '',
        gls: [{ numero_gl: '', nom_gl: '', error: null }]
      });
    },
    removeRubrique(blocIndex, rubriqueIndex) {
      this.blocs[blocIndex].rubriques.splice(rubriqueIndex, 1);
    },
    addGl(blocIndex, rubriqueIndex) {
      this.blocs[blocIndex].rubriques[rubriqueIndex].gls.push({
        numero_gl: '',
        nom_gl: '',
        error: null
      });
    },
    removeGl(blocIndex, rubriqueIndex, glIndex) {
      this.blocs[blocIndex].rubriques[rubriqueIndex].gls.splice(glIndex, 1);
    },
    async enregistrer() {
      const nouvelles = this.blocs
        .filter((b) => b.libelle && b.libelle.trim())
        .map((b) => {
          const rubriques = (b.rubriques || [])
            .filter((r) => r.libelle && r.libelle.trim())
            .map((r) => ({
              libelle: r.libelle.trim(),
              gls: (r.gls || [])
                .filter((g) => g.numero_gl && g.numero_gl.trim())
                .map((g) => ({
                  numero_gl: g.numero_gl.trim(),
                  nom_gl: (g.nom_gl && g.nom_gl.trim()) || null
                }))
            }))
            .filter((r) => r.gls.length > 0);
          const cr = {};
          CLE_REPARTITION_ENTITIES.forEach(({ key }) => {
            cr[key] = (b.cle_repartition && b.cle_repartition[key] != null) ? Number(b.cle_repartition[key]) : 0;
          });
          return {
            libelle: b.libelle.trim(),
            cle_repartition_nom: (b.cle_repartition_nom || '').trim() || null,
            cle_repartition: cr,
            rubriques
          };
        })
        .filter((b) => b.rubriques.length > 0);

      const hasValid = nouvelles.some((b) => b.rubriques.length > 0);
      if (!hasValid) {
        this.saveMessage = 'Ajoutez au moins une rubrique avec un libellé et une sous-rubrique (avec libellé et parent GL).';
        this.saveError = true;
        return;
      }

      this.saving = true;
      this.saveMessage = '';
      this.saveError = false;

      try {
        let existing = [];
        let getExistingFailed = false;
        try {
          const res = await window.axios.get('/api/reference-compte');
          const data = res.data && res.data.data;
          if (data && Array.isArray(data)) {
            existing = data.map((b) => {
              const cr = {};
              CLE_REPARTITION_ENTITIES.forEach(({ key }) => {
                cr[key] = (b.cle_repartition && b.cle_repartition[key] != null) ? Number(b.cle_repartition[key]) : 0;
              });
              return {
                libelle: b.libelle,
                cle_repartition_nom: b.cle_repartition_nom || null,
                cle_repartition: cr,
                rubriques: (b.rubriques || []).map((r) => ({
                  libelle: r.libelle,
                  gls: (r.gls || []).map((g) => ({
                    numero_gl: g.numero_gl,
                    nom_gl: g.nom_gl || null
                  }))
                }))
              };
            });
          }
        } catch (e) {
          getExistingFailed = true;
        }
        if (getExistingFailed && existing.length === 0 && nouvelles.length > 0) {
          this.saveMessage = 'Impossible de récupérer les références existantes. Enregistrement annulé — réessayez ou rafraîchissez la page.';
          this.saveError = true;
          this.saving = false;
          return;
        }
        const payload = [...existing, ...nouvelles];
        await window.axios.post('/api/reference-compte', { blocs: payload });
        this.saveMessage = 'Référence compte enregistrée avec succès.';
        this.saveError = false;
        this.blocs = [
          {
            libelle: '',
            cle_repartition_nom: '',
            cle_repartition: defaultCleRepartition(),
            rubriques: [{ libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }]
          }
        ];
        this.showCleRepartitionByIndex = [false];
        this.selectedBlocIndex = 0;
        this.$emit('saved');
      } catch (err) {
        this.saveMessage = err.response?.data?.message || err.message || "Erreur lors de l'enregistrement.";
        this.saveError = true;
      } finally {
        this.saving = false;
      }
    },
  }
};
</script>

<style scoped>
.reference-compte-form {
  padding: 0;
  width: 100%;
}

.section-header {
  margin-bottom: 24px;
}

.section-title {
  font-size: 1.35rem;
  color: #1A4D3A;
  margin: 0;
  font-weight: 600;
}

.form-container {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.ref-form-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.rubrique-nav-form {
  flex: 0 0 260px;
  max-width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  padding: 12px;
  max-height: 70vh;
  overflow-y: auto;
}

.rubrique-nav-form .rubrique-nav-title {
  margin: 0 0 10px 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.rubrique-nav-form .rubrique-nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rubrique-nav-form .rubrique-nav-item {
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #fff;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  gap: 4px;
  transition: background 0.15s, border-color 0.15s;
}

.rubrique-nav-form .rubrique-nav-item:hover {
  background: #f3f4f6;
  border-color: #1A4D3A;
}

.rubrique-nav-form .rubrique-nav-item.active {
  background: #1A4D3A;
  border-color: #1A4D3A;
  color: #fff;
}

.rubrique-nav-form .rubrique-nav-item.active .nav-num,
.rubrique-nav-form .rubrique-nav-item.active .nav-libelle {
  color: #fff;
}

.rubrique-nav-form .nav-num {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
}

.rubrique-nav-form .nav-libelle {
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  word-break: break-word;
}

.btn-add-bloc-nav {
  width: 100%;
  margin-top: 12px;
  padding: 10px 12px;
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-add-bloc-nav:hover {
  background: #153d2a;
}

.rubrique-detail-form {
  flex: 1;
  min-width: 280px;
}

.form-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.bloc-card {
  background: #fff;
  border-color: #1f2937;
  border-width: 1px 1px 1px 4px;
  border-left-color: #1f2937;
}

.bloc-header {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.bloc-label {
  font-weight: 700;
  color: #111827;
  font-size: 1.1rem;
}

.bloc-libelle-inline {
  flex: 1;
  margin-bottom: 0;
}

.rubriques-in-bloc {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.rubrique-card {
  margin-left: 12px;
  border-left: 3px solid #1A4D3A;
}

.rubrique-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.rubrique-label {
  font-weight: 600;
  color: #374151;
  font-size: 1rem;
}

.btn-remove {
  background: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-remove:hover {
  background: #fecaca;
}

.form-group {
  margin-bottom: 16px;
}

.form-group:last-child {
  margin-bottom: 0;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}

.form-input {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.2);
}

.form-input-readonly {
  background: #f9fafb;
  color: #6b7280;
  cursor: default;
}

.gl-section {
  margin-top: 20px;
}

.gl-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.gl-header label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.btn-add-small {
  background: #ecfdf5;
  color: #1A4D3A;
  border: 1px solid #a7f3d0;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.85rem;
  cursor: pointer;
  font-weight: 500;
}

.btn-add-small:hover {
  background: #d1fae5;
}

.gl-row {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.gl-fields {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 12px;
}

.gl-numero,
.gl-nom {
  margin-bottom: 0;
}

.loading-text {
  font-size: 0.8rem;
  color: #6b7280;
  margin-top: 4px;
}

.error-text {
  font-size: 0.8rem;
  color: #b91c1c;
  margin-top: 4px;
}

.btn-remove-small {
  background: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fecaca;
  border-radius: 6px;
  width: 32px;
  height: 32px;
  cursor: pointer;
  font-size: 12px;
  flex-shrink: 0;
  margin-top: 24px;
}

.btn-remove-small:hover {
  background: #fecaca;
}

.btn-add-rubrique {
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 16px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-add-rubrique:hover {
  background: #153d2a;
}

.btn-add-bloc {
  background: #166534;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 12px 20px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-add-bloc:hover {
  background: #14532d;
}

.save-row {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 16px;
}

.btn-save {
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 12px 24px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-save:hover:not(:disabled) {
  background: #153d2a;
}

.btn-save:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.save-message {
  margin: 0;
  font-size: 0.9rem;
  color: #15803d;
}

.save-message.error {
  color: #b91c1c;
}

.cle-repartition-add-row {
  margin-top: 16px;
}

.btn-add-cle-repartition {
  background: #ecfdf5;
  color: #1A4D3A;
  border: 1px solid #a7f3d0;
  border-radius: 6px;
  padding: 8px 14px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-add-cle-repartition:hover {
  background: #d1fae5;
}

.cle-repartition-in-bloc {
  margin-top: 20px;
  border-left: 3px solid #1A4D3A;
}

.cle-repartition-in-bloc .cle-repartition-title {
  font-size: 1rem;
  margin-bottom: 12px;
}

.cle-repartition-header {
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.cle-repartition-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: #1A4D3A;
  margin: 0 0 4px 0;
}

.cle-repartition-desc {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

.cle-repartition-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 12px 20px;
}

.cle-repartition-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.cle-repartition-field label {
  font-size: 0.8rem;
  font-weight: 500;
  color: #374151;
}

.cle-repartition-input {
  width: 100%;
  max-width: 140px;
}

@media (max-width: 768px) {
  .gl-fields {
    grid-template-columns: 1fr;
  }
  .cle-repartition-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
