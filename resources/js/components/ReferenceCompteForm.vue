<template>
  <div class="reference-compte-form">
    <div class="section-header">
      <h2 class="section-title">Ajouter une référence compte</h2>
    </div>

    <div class="form-container">
      <div v-for="(bloc, blocIndex) in blocs" :key="blocIndex" class="form-card bloc-card">
        <div class="bloc-header">
          <span class="bloc-label">Rubrique {{ blocIndex + 1 }}</span>
          <div class="form-group bloc-libelle-inline">
            <label>Libellé de la rubrique</label>
            <input
              v-model="bloc.libelle"
              type="text"
              class="form-input"
              placeholder="Ex: Actif, Passif, Produits..."
            />
          </div>
          <button
            type="button"
            class="btn-remove"
            @click="removeBloc(blocIndex)"
            title="Supprimer la rubrique"
          >
            ✕
          </button>
        </div>

        <div class="rubriques-in-bloc">
          <div v-for="(rubrique, rubriqueIndex) in bloc.rubriques" :key="rubriqueIndex" class="form-card rubrique-card">
            <div class="rubrique-header">
              <span class="rubrique-label">Sous-rubrique {{ rubriqueIndex + 1 }}</span>
              <button
                type="button"
                class="btn-remove"
                @click="removeRubrique(blocIndex, rubriqueIndex)"
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
                <button type="button" class="btn-add-small" @click="addGl(blocIndex, rubriqueIndex)">+ Ajouter un parent GL</button>
              </div>

              <div v-for="(gl, glIndex) in rubrique.gls" :key="glIndex" class="gl-row">
                <div class="gl-fields">
                  <div class="form-group gl-numero">
                    <label>Numéro parent GL</label>
                    <input
                      v-model="gl.numero_gl"
                      type="text"
                      class="form-input"
                      placeholder="Ex: 702930000000"
                      @blur="fetchGlNom(blocIndex, rubriqueIndex, glIndex)"
                    />
                  </div>
                  <div class="form-group gl-nom">
                    <label>Nom parent GL</label>
                    <input
                      :value="gl.nom_gl"
                      type="text"
                      class="form-input form-input-readonly"
                      placeholder="Récupéré depuis le SI"
                      readonly
                    />
                    <span v-if="glLoading[glKey(blocIndex, rubriqueIndex, glIndex)]" class="loading-text">Chargement...</span>
                    <span v-else-if="gl.error" class="error-text">{{ gl.error }}</span>
                  </div>
                </div>
                <button type="button" class="btn-remove-small" @click="removeGl(blocIndex, rubriqueIndex, glIndex)" title="Supprimer ce parent GL">✕</button>
              </div>
            </div>
          </div>

          <button type="button" class="btn-add-rubrique" @click="addRubrique(blocIndex)">+ Ajouter une sous-rubrique</button>
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
export default {
  name: 'ReferenceCompteForm',
  data() {
    return {
      blocs: [
        {
          libelle: '',
          rubriques: [
            { libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }
          ]
        }
      ],
      glLoading: {},
      saving: false,
      saveMessage: '',
      saveError: false
    };
  },
  methods: {
    glKey(blocIndex, rubriqueIndex, glIndex) {
      return `${blocIndex}-${rubriqueIndex}-${glIndex}`;
    },
    addBloc() {
      this.blocs.push({
        libelle: '',
        rubriques: [{ libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }]
      });
    },
    removeBloc(index) {
      this.blocs.splice(index, 1);
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
          return { libelle: b.libelle.trim(), rubriques };
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
        try {
          const res = await window.axios.get('/api/reference-compte');
          const data = res.data && res.data.data;
          if (data && Array.isArray(data)) {
            existing = data.map((b) => ({
              libelle: b.libelle,
              rubriques: (b.rubriques || []).map((r) => ({
                libelle: r.libelle,
                gls: (r.gls || []).map((g) => ({
                  numero_gl: g.numero_gl,
                  nom_gl: g.nom_gl || null
                }))
              }))
            }));
          }
        } catch (_) {}
        const payload = [...existing, ...nouvelles];
        await window.axios.post('/api/reference-compte', { blocs: payload });
        this.saveMessage = 'Référence compte enregistrée avec succès.';
        this.saveError = false;
        this.blocs = [
          {
            libelle: '',
            rubriques: [{ libelle: '', gls: [{ numero_gl: '', nom_gl: '', error: null }] }]
          }
        ];
        this.$emit('saved');
      } catch (err) {
        this.saveMessage = err.response?.data?.message || err.message || "Erreur lors de l'enregistrement.";
        this.saveError = true;
      } finally {
        this.saving = false;
      }
    },
    async fetchGlNom(blocIndex, rubriqueIndex, glIndex) {
      const gl = this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex];
      if (!gl || !gl.numero_gl || !gl.numero_gl.trim()) {
        if (gl) gl.nom_gl = '';
        if (gl) gl.error = null;
        return;
      }

      const key = this.glKey(blocIndex, rubriqueIndex, glIndex);
      this.$set(this.glLoading, key, true);
      gl.error = null;

      try {
        const response = await window.axios.get('/api/oracle/data/gl-lookup', {
          params: { gl_code: gl.numero_gl.trim() }
        });
        const data = response.data;
        const glData = data && (data.data != null ? data.data : data);
        if (glData && (glData.nom_gl != null || glData.GL_DESC_E != null || glData.gl_desc_e != null)) {
          const nom = glData.nom_gl || glData.GL_DESC_E || glData.gl_desc_e || '';
          this.$set(this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex], 'nom_gl', nom);
          this.$set(this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex], 'error', null);
        } else {
          this.$set(this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex], 'nom_gl', '');
          this.$set(this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex], 'error', (data && data.message) || 'GL non trouvé');
        }
      } catch (err) {
        this.$set(this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex], 'nom_gl', '');
        this.$set(this.blocs[blocIndex].rubriques[rubriqueIndex].gls[glIndex], 'error', err.response?.data?.message || err.message || 'Erreur lors de la récupération');
      } finally {
        this.$set(this.glLoading, key, false);
      }
    }
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

@media (max-width: 768px) {
  .gl-fields {
    grid-template-columns: 1fr;
  }
}
</style>
