<template>
  <div class="reference-compte-list">
    <div class="section-header">
      <h2 class="section-title">Liste des références compte</h2>
    </div>

    <div v-if="loading" class="loading-state">Chargement...</div>
    <div v-else-if="loadError" class="empty-state error-state">
      <p>Erreur lors du chargement des références.</p>
      <p class="empty-hint">{{ loadError }}</p>
      <button type="button" class="btn-refresh-list" @click="load">Rafraîchir la liste</button>
    </div>
    <div v-else-if="!savedBlocs || !savedBlocs.length" class="empty-state">
      <p>Aucune référence compte enregistrée.</p>
      <p class="empty-hint">Utilisez le bouton « Ajouter » pour créer des références.</p>
      <button type="button" class="btn-refresh-list" @click="load">Rafraîchir la liste</button>
    </div>
    <div v-else class="saved-section">
      <div class="ref-list-layout">
        <nav class="rubrique-nav" aria-label="Liste des rubriques">
          <p class="rubrique-nav-title">Rubriques</p>
          <ul class="rubrique-nav-list">
            <li v-for="(bloc, blocIndex) in savedBlocs" :key="'nav-' + blocIndex">
              <button
                type="button"
                class="rubrique-nav-item"
                :class="{ active: selectedBlocIndex === blocIndex }"
                @click="selectBloc(blocIndex)"
              >
                <span class="nav-num">Rubrique {{ blocIndex + 1 }}</span>
                <span class="nav-libelle">{{ bloc.libelle || 'Sans libellé' }}</span>
              </button>
            </li>
          </ul>
        </nav>
        <div
          v-if="selectedBlocIndex !== null && savedBlocs[selectedBlocIndex]"
          class="rubrique-detail"
        >
        <div class="saved-bloc">
        <div class="saved-bloc-header">
          <strong class="saved-bloc-libelle">Rubrique {{ selectedBlocIndex + 1 }}</strong>
          <input
            v-model="savedBlocs[selectedBlocIndex].libelle"
            type="text"
            class="saved-bloc-libelle-input"
            placeholder="Libellé de la rubrique"
          />
          <button
            type="button"
            class="btn-add-sous-rubrique"
            @click="toggleAddSousRubrique(selectedBlocIndex)"
            :disabled="(addingSousRubriqueToBloc !== null && addingSousRubriqueToBloc !== selectedBlocIndex) || (addingToBloc !== null)"
          >
            {{ addingSousRubriqueToBloc === selectedBlocIndex ? 'Annuler' : '+ Ajouter une sous-rubrique' }}
          </button>
        </div>
        <div v-if="addingSousRubriqueToBloc === selectedBlocIndex" class="add-sous-rubrique-row">
          <input
            ref="newSousRubriqueInput"
            v-model="newSousRubriqueLibelle"
            type="text"
            class="form-input-sous-rubrique"
            placeholder="Libellé de la sous-rubrique"
          />
          <div class="add-gl-actions">
            <button type="button" class="btn-validate" :disabled="savingSousRubrique" @click="saveNewSousRubrique(selectedBlocIndex)">
              {{ savingSousRubrique ? 'Enregistrement...' : 'Valider' }}
            </button>
            <button type="button" class="btn-cancel" @click="cancelAddSousRubrique">Annuler</button>
          </div>
        </div>
        <div class="saved-rubriques">
          <div
            v-for="(rubrique, rubriqueIndex) in savedBlocs[selectedBlocIndex].rubriques"
            :key="rubriqueIndex"
            class="saved-card"
          >
            <div class="saved-card-header">
              <span class="saved-rubrique-num">Sous-rubrique {{ rubriqueIndex + 1 }}</span>
              <input
                v-model="rubrique.libelle"
                type="text"
                class="saved-rubrique-libelle-input"
                placeholder="Libellé de la sous-rubrique"
              />
              <button
                type="button"
                class="btn-add-gl"
                @click="toggleAddGl(selectedBlocIndex, rubriqueIndex)"
                :disabled="(addingToBloc !== null || addingToRubrique !== null) && (addingToBloc !== selectedBlocIndex || addingToRubrique !== rubriqueIndex) || addingSousRubriqueToBloc !== null"
              >
                {{ addingToBloc === selectedBlocIndex && addingToRubrique === rubriqueIndex ? 'Annuler' : '+ Ajouter un parent GL' }}
              </button>
            </div>
            <div class="saved-gl-table-wrap">
              <table class="saved-gl-table">
                <thead>
                <tr>
                    <th>Numéro parent GL</th>
                    <th>Nom parent GL</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(gl, glIdx) in rubrique.gls" :key="glIdx">
                    <td>
                      <input
                        v-model="gl.numero_gl"
                        type="text"
                        class="form-input-inline"
                        placeholder="Numéro parent GL"
                        @blur="updateExistingGlNom(selectedBlocIndex, rubriqueIndex, glIdx)"
                      />
                    </td>
                    <td>{{ gl.nom_gl || '—' }}</td>
                  </tr>
                  <tr v-if="addingToBloc === selectedBlocIndex && addingToRubrique === rubriqueIndex" class="add-gl-row">
                    <td>
                      <input
                        ref="newGlInput"
                        v-model="newGl.numero_gl"
                        type="text"
                        class="form-input-inline"
                        placeholder="Ex: 702930000000"
                        @blur="fetchNewGlNom"
                      />
                    </td>
                    <td>
                      <span v-if="newGlLoading" class="loading-text">Chargement...</span>
                      <span v-else-if="newGl.error" class="error-text">{{ newGl.error }}</span>
                      <span v-else class="form-input-readonly-inline">{{ newGl.nom_gl || '—' }}</span>
                      <div class="add-gl-actions">
                        <button type="button" class="btn-validate" :disabled="savingNewGl" @click="saveNewGl(selectedBlocIndex, rubriqueIndex)">
                          {{ savingNewGl ? 'Enregistrement...' : 'Valider' }}
                        </button>
                        <button type="button" class="btn-cancel" @click="cancelAddGl">Annuler</button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
        <div v-if="!cleRepartitionVisibleMap[selectedBlocIndex]" class="cle-repartition-add-row">
          <button type="button" class="btn-add-cle-repartition" @click="showCleRepartition(selectedBlocIndex)">
            + Ajouter une clé de répartition
          </button>
        </div>
        <div v-else class="cle-repartition-in-bloc form-card saved-card">
          <h4 class="cle-repartition-title">Clé répartition (cette rubrique)</h4>
          <div class="form-group-inline">
            <label>Nom de la clé</label>
            <input
              v-model="savedBlocs[selectedBlocIndex].cle_repartition_nom"
              type="text"
              class="form-input-inline"
              placeholder="Ex: Répartition commissions..."
            />
          </div>
          <p class="cle-repartition-desc">Valeurs par agence (affichées dans le tableau CR par Agence).</p>
          <div class="cle-repartition-grid">
            <div v-for="item in cleRepartitionItems" :key="item.key" class="cle-repartition-field">
              <label :for="'list-cle-' + selectedBlocIndex + '-' + item.key">{{ item.label }}</label>
              <input
                :id="'list-cle-' + selectedBlocIndex + '-' + item.key"
                v-model.number="savedBlocs[selectedBlocIndex].cle_repartition[item.key]"
                type="number"
                step="any"
                class="form-input-inline cle-repartition-input"
                placeholder="0"
              />
            </div>
          </div>
        </div>
        </div>
        </div>
      </div>
      <div class="save-all-row">
        <button type="button" class="btn-save-all" :disabled="savingAll" @click="saveAll">
          {{ savingAll ? 'Enregistrement...' : 'Enregistrer les modifications' }}
        </button>
        <p v-if="saveMessage" class="save-all-message" :class="{ error: saveError }">
          {{ saveMessage }}
        </p>
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

export default {
  name: 'ReferenceCompteList',
  data() {
    return {
      loading: false,
      loadError: null,
      savedBlocs: [],
      showCleRepartitionByIndex: {},
      addingToBloc: null,
      addingToRubrique: null,
      newGl: { numero_gl: '', nom_gl: '', error: null },
      newGlLoading: false,
      savingNewGl: false,
      addingSousRubriqueToBloc: null,
      newSousRubriqueLibelle: '',
      savingSousRubrique: false,
      savingAll: false,
      saveMessage: '',
      saveError: false,
      selectedBlocIndex: null
    };
  },
  computed: {
    cleRepartitionItems() {
      return CLE_REPARTITION_ENTITIES;
    },
    cleRepartitionVisibleMap() {
      return { ...this.showCleRepartitionByIndex };
    }
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      this.loadError = null;
      try {
        const response = await window.axios.get('/api/reference-compte');
        const data = response.data && response.data.data;
        if (data && Array.isArray(data) && data.length > 0) {
          this.savedBlocs = data.map((b) => {
            const cr = {};
            CLE_REPARTITION_ENTITIES.forEach(({ key }) => {
              cr[key] = (b.cle_repartition && b.cle_repartition[key] != null) ? Number(b.cle_repartition[key]) : 0;
            });
            const hasCleRepartition = (b.cle_repartition_nom && (b.cle_repartition_nom || '').trim()) || CLE_REPARTITION_ENTITIES.some(({ key }) => cr[key] != null && Number(cr[key]) !== 0);
            return {
              libelle: b.libelle || '',
              cle_repartition_nom: b.cle_repartition_nom || '',
              cle_repartition: cr,
              rubriques: (b.rubriques || []).map((r) => ({
              libelle: r.libelle || '',
              gls: (r.gls || []).map((g) => ({
                numero_gl: g.numero_gl || '',
                nom_gl: g.nom_gl || ''
              }))
            }))
            };
          });
          this.showCleRepartitionByIndex = {};
          this.savedBlocs.forEach((b, i) => {
            const hasVal = (b.cle_repartition_nom && (b.cle_repartition_nom || '').trim()) || CLE_REPARTITION_ENTITIES.some(({ key }) => (b.cle_repartition && b.cle_repartition[key] != null && Number(b.cle_repartition[key]) !== 0));
            this.showCleRepartitionByIndex[i] = !!hasVal;
          });
          this.loading = false;
          this.hydrateNomsEnregistres();
        } else {
          this.savedBlocs = [];
          this.showCleRepartitionByIndex = {};
          this.selectedBlocIndex = null;
        }
        if (this.savedBlocs.length > 0) {
          if (this.selectedBlocIndex == null || this.selectedBlocIndex >= this.savedBlocs.length) {
            this.selectedBlocIndex = 0;
          }
        } else {
          this.selectedBlocIndex = null;
        }
        this.loading = false;
      } catch (err) {
        console.warn('Chargement référence compte:', err.response?.status === 404 ? 'aucune donnée' : err.message);
        this.savedBlocs = [];
        this.selectedBlocIndex = null;
        this.loadError = err.response?.data?.message || err.message || 'Erreur réseau ou serveur.';
      } finally {
        this.loading = false;
      }
    },
    buildPayloadFromState() {
      return this.savedBlocs
        .map((b) => {
          const libelleBloc = (b.libelle || '').trim();
          const rubriques = (b.rubriques || [])
            .filter((r) => (r.libelle || '').trim())
            .map((r) => {
              const libelleRub = (r.libelle || '').trim();
              const gls = (r.gls || [])
                .filter((gl) => (gl.numero_gl || '').trim())
                .map((gl) => ({
                  numero_gl: (gl.numero_gl || '').trim(),
                  nom_gl: ((gl.nom_gl || '').trim()) || null
                }));
              return { libelle: libelleRub, gls };
            })
            .filter((r) => r.gls.length > 0);
          const cr = {};
          CLE_REPARTITION_ENTITIES.forEach(({ key }) => {
            cr[key] = (b.cle_repartition && b.cle_repartition[key] != null) ? Number(b.cle_repartition[key]) : 0;
          });
          return {
            libelle: libelleBloc,
            cle_repartition_nom: (b.cle_repartition_nom || '').trim() || null,
            cle_repartition: cr,
            rubriques
          };
        })
        .filter((b) => b.libelle && b.rubriques.length > 0);
    },
    async hydrateNomsEnregistres() {
      const toFetch = [];
      this.savedBlocs.forEach((bloc, bi) => {
        (bloc.rubriques || []).forEach((rubrique, ri) => {
          (rubrique.gls || []).forEach((g, gi) => {
            if ((g.numero_gl || '').trim() && !(g.nom_gl || '').trim()) {
              toFetch.push({ bi, ri, gi, numero: (g.numero_gl || '').trim() });
            }
          });
        });
      });
      if (!toFetch.length) return;
      const results = await Promise.all(
        toFetch.map(async ({ bi, ri, gi, numero }) => {
          try {
            const response = await window.axios.get('/api/oracle/data/gl-lookup', {
              params: { gl_code: numero }
            });
            const data = response.data;
            const glData = data && (data.data != null ? data.data : data);
            const nom = (glData && (glData.nom_gl || glData.GL_DESC_E || glData.gl_desc_e)) || '';
            return { bi, ri, gi, nom };
          } catch (_) {
            return { bi, ri, gi, nom: '' };
          }
        })
      );
      const updated = this.savedBlocs.map((b) => ({
        libelle: b.libelle,
        rubriques: (b.rubriques || []).map((r) => ({
          libelle: r.libelle,
          gls: (r.gls || []).map((g) => ({ ...g, nom_gl: g.nom_gl || '' }))
        }))
      }));
      results.forEach(({ bi, ri, gi, nom }) => {
        if (updated[bi] && updated[bi].rubriques[ri] && updated[bi].rubriques[ri].gls[gi]) {
          updated[bi].rubriques[ri].gls[gi].nom_gl = nom;
        }
      });
      this.savedBlocs = updated;
    },
    toggleAddGl(blocIndex, rubriqueIndex) {
      if (this.addingToBloc === blocIndex && this.addingToRubrique === rubriqueIndex) {
        this.cancelAddGl();
        return;
      }
      this.addingToBloc = blocIndex;
      this.addingToRubrique = rubriqueIndex;
      this.newGl = { numero_gl: '', nom_gl: '', error: null };
      this.$nextTick(() => {
        const input = this.$refs.newGlInput;
        if (input && (Array.isArray(input) ? input[0] : input)) {
          (Array.isArray(input) ? input[0] : input).focus();
        }
      });
    },
    cancelAddGl() {
      this.addingToBloc = null;
      this.addingToRubrique = null;
      this.newGl = { numero_gl: '', nom_gl: '', error: null };
    },
    toggleAddSousRubrique(blocIndex) {
      if (this.addingSousRubriqueToBloc === blocIndex) {
        this.cancelAddSousRubrique();
        return;
      }
      this.addingSousRubriqueToBloc = blocIndex;
      this.newSousRubriqueLibelle = '';
      this.$nextTick(() => {
        const input = this.$refs.newSousRubriqueInput;
        if (input && (Array.isArray(input) ? input[0] : input)) {
          (Array.isArray(input) ? input[0] : input).focus();
        }
      });
    },
    cancelAddSousRubrique() {
      this.addingSousRubriqueToBloc = null;
      this.newSousRubriqueLibelle = '';
    },
    showCleRepartition(blocIndex) {
      this.showCleRepartitionByIndex = { ...this.showCleRepartitionByIndex, [blocIndex]: true };
    },
    selectBloc(index) {
      if (this.addingToBloc !== null && this.addingToBloc !== index) this.cancelAddGl();
      if (this.addingSousRubriqueToBloc !== null && this.addingSousRubriqueToBloc !== index) this.cancelAddSousRubrique();
      this.selectedBlocIndex = index;
    },
    async saveNewSousRubrique(blocIndex) {
      const libelle = (this.newSousRubriqueLibelle || '').trim();
      if (!libelle) return;
      this.savingSousRubrique = true;
      try {
        const payload = this.buildPayloadFromState();
        payload[blocIndex].rubriques.push({ libelle, gls: [] });
        await window.axios.post('/api/reference-compte', { blocs: payload });
        this.cancelAddSousRubrique();
        await this.load();
      } catch (err) {
        console.warn('Erreur enregistrement sous-rubrique:', err);
      } finally {
        this.savingSousRubrique = false;
      }
    },
    async fetchNewGlNom() {
      const g = this.newGl;
      if (!g.numero_gl || !g.numero_gl.trim()) {
        g.nom_gl = '';
        g.error = null;
        return;
      }
      this.newGlLoading = true;
      g.error = null;
      try {
        const response = await window.axios.get('/api/oracle/data/gl-lookup', {
          params: { gl_code: g.numero_gl.trim() }
        });
        const data = response.data;
        const glData = data && (data.data != null ? data.data : data);
        if (glData && (glData.nom_gl || glData.GL_DESC_E || glData.gl_desc_e)) {
          g.nom_gl = glData.nom_gl || glData.GL_DESC_E || glData.gl_desc_e || '';
        } else {
          g.nom_gl = '';
          g.error = (data && data.message) || 'GL non trouvé';
        }
      } catch (err) {
        g.nom_gl = '';
        g.error = err.response?.data?.message || err.message || 'Erreur lors de la récupération';
      } finally {
        this.newGlLoading = false;
      }
    },
    async saveNewGl(blocIndex, rubriqueIndex) {
      const g = this.newGl;
      if (!g.numero_gl || !g.numero_gl.trim()) return;
      this.savingNewGl = true;
      try {
        const payload = this.buildPayloadFromState();
        const newGl = {
          numero_gl: g.numero_gl.trim(),
          nom_gl: (g.nom_gl && g.nom_gl.trim()) || null
        };
        payload[blocIndex].rubriques[rubriqueIndex].gls.push(newGl);
        await window.axios.post('/api/reference-compte', { blocs: payload });
        this.cancelAddGl();
        await this.load();
      } catch (err) {
        g.error = err.response?.data?.message || err.message || 'Erreur lors de l\'enregistrement';
      } finally {
        this.savingNewGl = false;
      }
    },
    async updateExistingGlNom(blocIndex, rubriqueIndex, glIndex) {
      const bloc = this.savedBlocs[blocIndex];
      const rubrique = bloc && bloc.rubriques && bloc.rubriques[rubriqueIndex];
      const gl = rubrique && rubrique.gls && rubrique.gls[glIndex];
      if (!gl || !gl.numero_gl || !gl.numero_gl.trim()) {
        if (gl) gl.nom_gl = '';
        return;
      }
      try {
        const response = await window.axios.get('/api/oracle/data/gl-lookup', {
          params: { gl_code: gl.numero_gl.trim() }
        });
        const data = response.data;
        const glData = data && (data.data != null ? data.data : data);
        if (glData && (glData.nom_gl || glData.GL_DESC_E || glData.gl_desc_e)) {
          gl.nom_gl = glData.nom_gl || glData.GL_DESC_E || glData.gl_desc_e || '';
        }
      } catch (_) {
        // on laisse l'ancien nom en cas d'erreur
      }
    },
    async saveAll() {
      this.savingAll = true;
      this.saveMessage = '';
      this.saveError = false;
      try {
        const payload = this.buildPayloadFromState();
        await window.axios.post('/api/reference-compte', { blocs: payload });
        this.saveMessage = 'Référence compte mise à jour.';
        this.saveError = false;
        await this.load();
      } catch (err) {
        this.saveMessage = err.response?.data?.message || err.message || 'Erreur lors de la mise à jour.';
        this.saveError = true;
      } finally {
        this.savingAll = false;
      }
    }
  }
};
</script>

<style scoped>
.reference-compte-list {
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

.loading-state,
.empty-state {
  padding: 40px 20px;
  text-align: center;
  background: #f9fafb;
  border-radius: 8px;
  color: #6b7280;
}

.empty-hint {
  margin-top: 8px;
  font-size: 0.9rem;
  color: #9ca3af;
}

.error-state .empty-hint {
  color: #b91c1c;
}

.btn-refresh-list {
  margin-top: 16px;
  padding: 8px 16px;
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-refresh-list:hover {
  background: #153d2a;
}

.saved-section {
  margin-top: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.ref-list-layout {
  display: flex;
  gap: 24px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.rubrique-nav {
  flex: 0 0 260px;
  max-width: 100%;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f9fafb;
  padding: 12px;
  max-height: 70vh;
  overflow-y: auto;
}

.rubrique-nav-title {
  margin: 0 0 10px 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.rubrique-nav-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.rubrique-nav-item {
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

.rubrique-nav-item:hover {
  background: #f3f4f6;
  border-color: #1A4D3A;
}

.rubrique-nav-item.active {
  background: #1A4D3A;
  border-color: #1A4D3A;
  color: #fff;
}

.rubrique-nav-item.active .nav-num,
.rubrique-nav-item.active .nav-libelle {
  color: #fff;
}

.nav-num {
  font-size: 0.75rem;
  font-weight: 600;
  color: #6b7280;
}

.nav-libelle {
  font-size: 0.875rem;
  font-weight: 500;
  color: #111827;
  word-break: break-word;
}

.rubrique-detail {
  flex: 1;
  min-width: 280px;
}

.saved-bloc {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-left: 4px solid #1f2937;
  border-radius: 8px;
  overflow: hidden;
}

.saved-bloc-header {
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-add-sous-rubrique {
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-add-sous-rubrique:hover:not(:disabled) {
  background: #153d2a;
}

.btn-add-sous-rubrique:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.add-sous-rubrique-row {
  padding: 12px 16px;
  background: #f0fdf4;
  border-bottom: 1px solid #bbf7d0;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.form-input-sous-rubrique {
  flex: 1;
  min-width: 200px;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input-sous-rubrique:focus {
  outline: none;
  border-color: #1A4D3A;
}

.saved-bloc-libelle {
  font-size: 1rem;
  font-weight: 700;
  color: #111827;
}

.saved-rubriques {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.saved-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.saved-card-header {
  padding: 12px 16px;
  background: #ecfdf5;
  border-bottom: 1px solid #d1fae5;
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.btn-add-gl {
  margin-left: auto;
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-add-gl:hover:not(:disabled) {
  background: #153d2a;
}

.btn-add-gl:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.saved-rubrique-num {
  font-size: 0.8rem;
  color: #047857;
  font-weight: 600;
}

.saved-rubrique-libelle {
  font-size: 1rem;
  color: #065f46;
}

.saved-rubrique-libelle-input {
  flex: 1;
  min-width: 200px;
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.saved-gl-table-wrap {
  overflow-x: auto;
}

.saved-gl-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.9rem;
}

.saved-gl-table th,
.saved-gl-table td {
  padding: 10px 16px;
  text-align: left;
  border-bottom: 1px solid #e5e7eb;
}

.saved-gl-table th {
  background: #f3f4f6;
  font-weight: 600;
  color: #374151;
}

.saved-gl-table tbody tr:last-child td {
  border-bottom: none;
}

.saved-gl-table td {
  color: #374151;
}

.add-gl-row {
  background: #f0fdf4;
}

.add-gl-row td {
  padding: 12px 16px;
  vertical-align: top;
}

.form-input-inline {
  width: 100%;
  max-width: 200px;
  padding: 8px 10px;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.9rem;
}

.form-input-inline:focus {
  outline: none;
  border-color: #1A4D3A;
}

.form-input-readonly-inline {
  color: #6b7280;
  font-size: 0.9rem;
}

.loading-text {
  font-size: 0.8rem;
  color: #6b7280;
  margin-right: 8px;
}

.error-text {
  font-size: 0.8rem;
  color: #b91c1c;
  margin-right: 8px;
}

.add-gl-actions {
  margin-top: 8px;
  display: flex;
  gap: 8px;
}

.btn-validate {
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
}

.btn-validate:hover:not(:disabled) {
  background: #153d2a;
}

.btn-validate:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-cancel {
  background: #f3f4f6;
  color: #374151;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  padding: 6px 14px;
  font-size: 0.85rem;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #e5e7eb;
}

.save-all-row {
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 12px;
}

.btn-save-all {
  background: #1A4D3A;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 10px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
}

.btn-save-all:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.save-all-message {
  font-size: 0.9rem;
  color: #15803d;
}

.save-all-message.error {
  color: #b91c1c;
}

.form-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
}

.cle-repartition-card {
  border-left: 4px solid #1A4D3A;
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
  margin: 0 0 16px 0;
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
  max-width: 140px;
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
  margin-top: 16px;
  border-left: 4px solid #1A4D3A;
}

.cle-repartition-in-bloc .cle-repartition-title {
  font-size: 1rem;
  margin-bottom: 8px;
}

.form-group-inline {
  margin-bottom: 12px;
}

.form-group-inline label {
  display: block;
  font-size: 0.8rem;
  font-weight: 500;
  color: #374151;
  margin-bottom: 4px;
}
</style>
