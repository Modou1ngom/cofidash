<template>
  <div class="reference-compte-list">
    <div class="section-header">
      <h2 class="section-title">Liste des références compte</h2>
    </div>

    <div v-if="loading" class="loading-state">Chargement...</div>
    <div v-else-if="!savedBlocs || !savedBlocs.length" class="empty-state">
      <p>Aucune référence compte enregistrée.</p>
      <p class="empty-hint">Utilisez le bouton « Ajouter » pour créer des références.</p>
    </div>
    <div v-else class="saved-section">
      <div v-for="(bloc, blocIndex) in savedBlocs" :key="blocIndex" class="saved-bloc">
        <div class="saved-bloc-header">
          <strong class="saved-bloc-libelle">Rubrique {{ blocIndex + 1 }} — {{ bloc.libelle || '—' }}</strong>
          <button
            type="button"
            class="btn-add-sous-rubrique"
            @click="toggleAddSousRubrique(blocIndex)"
            :disabled="(addingSousRubriqueToBloc !== null && addingSousRubriqueToBloc !== blocIndex) || (addingToBloc !== null)"
          >
            {{ addingSousRubriqueToBloc === blocIndex ? 'Annuler' : '+ Ajouter une sous-rubrique' }}
          </button>
        </div>
        <div v-if="addingSousRubriqueToBloc === blocIndex" class="add-sous-rubrique-row">
          <input
            ref="newSousRubriqueInput"
            v-model="newSousRubriqueLibelle"
            type="text"
            class="form-input-sous-rubrique"
            placeholder="Libellé de la sous-rubrique"
          />
          <div class="add-gl-actions">
            <button type="button" class="btn-validate" :disabled="savingSousRubrique" @click="saveNewSousRubrique(blocIndex)">
              {{ savingSousRubrique ? 'Enregistrement...' : 'Valider' }}
            </button>
            <button type="button" class="btn-cancel" @click="cancelAddSousRubrique">Annuler</button>
          </div>
        </div>
        <div class="saved-rubriques">
          <div
            v-for="(rubrique, rubriqueIndex) in bloc.rubriques"
            :key="rubriqueIndex"
            class="saved-card"
          >
            <div class="saved-card-header">
              <span class="saved-rubrique-num">Sous-rubrique {{ rubriqueIndex + 1 }}</span>
              <strong class="saved-rubrique-libelle">{{ rubrique.libelle || '—' }}</strong>
              <button
                type="button"
                class="btn-add-gl"
                @click="toggleAddGl(blocIndex, rubriqueIndex)"
                :disabled="(addingToBloc !== null || addingToRubrique !== null) && (addingToBloc !== blocIndex || addingToRubrique !== rubriqueIndex) || addingSousRubriqueToBloc !== null"
              >
                {{ addingToBloc === blocIndex && addingToRubrique === rubriqueIndex ? 'Annuler' : '+ Ajouter un parent GL' }}
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
                    <td>{{ gl.numero_gl }}</td>
                    <td>{{ gl.nom_gl || '—' }}</td>
                  </tr>
                  <tr v-if="addingToBloc === blocIndex && addingToRubrique === rubriqueIndex" class="add-gl-row">
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
                        <button type="button" class="btn-validate" :disabled="savingNewGl" @click="saveNewGl(blocIndex, rubriqueIndex)">
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
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ReferenceCompteList',
  data() {
    return {
      loading: false,
      savedBlocs: [],
      addingToBloc: null,
      addingToRubrique: null,
      newGl: { numero_gl: '', nom_gl: '', error: null },
      newGlLoading: false,
      savingNewGl: false,
      addingSousRubriqueToBloc: null,
      newSousRubriqueLibelle: '',
      savingSousRubrique: false
    };
  },
  mounted() {
    this.load();
  },
  methods: {
    async load() {
      this.loading = true;
      try {
        const response = await window.axios.get('/api/reference-compte');
        const data = response.data && response.data.data;
        if (data && Array.isArray(data) && data.length > 0) {
          this.savedBlocs = data.map((b) => ({
            libelle: b.libelle || '',
            rubriques: (b.rubriques || []).map((r) => ({
              libelle: r.libelle || '',
              gls: (r.gls || []).map((g) => ({
                numero_gl: g.numero_gl || '',
                nom_gl: g.nom_gl || ''
              }))
            }))
          }));
          this.loading = false;
          this.hydrateNomsEnregistres();
        } else {
          this.savedBlocs = [];
          this.loading = false;
        }
      } catch (err) {
        console.warn('Chargement référence compte:', err.response?.status === 404 ? 'aucune donnée' : err.message);
        this.savedBlocs = [];
      } finally {
        this.loading = false;
      }
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
    async saveNewSousRubrique(blocIndex) {
      const libelle = (this.newSousRubriqueLibelle || '').trim();
      if (!libelle) return;
      this.savingSousRubrique = true;
      try {
        const payload = this.savedBlocs.map((b) => ({
          libelle: b.libelle,
          rubriques: (b.rubriques || []).map((r) => ({
            libelle: r.libelle,
            gls: (r.gls || []).map((gl) => ({
              numero_gl: gl.numero_gl,
              nom_gl: gl.nom_gl || null
            }))
          }))
        }));
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
        const payload = this.savedBlocs.map((b) => ({
          libelle: b.libelle,
          rubriques: (b.rubriques || []).map((r) => ({
            libelle: r.libelle,
            gls: (r.gls || []).map((gl) => ({
              numero_gl: gl.numero_gl,
              nom_gl: gl.nom_gl || null
            }))
          }))
        }));
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

.saved-section {
  margin-top: 0;
  display: flex;
  flex-direction: column;
  gap: 24px;
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
</style>
