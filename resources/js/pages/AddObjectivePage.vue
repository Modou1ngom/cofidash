<template>
  <div class="add-objective-page page-adapt">
    <div class="page-container">
      <div class="page-header">
        <h1>Ajouter un Objectif</h1>
        <button @click="goBack" class="btn-back">← Retour</button>
      </div>

      <div class="form-container">
        <form @submit.prevent="submitObjective" class="objective-form">
          <div class="form-group">
            <label for="type">Type d'objectif *</label>
            <select 
              id="type" 
              v-model="form.type" 
              required 
              class="form-select"
              @change="onTypeChange"
            >
              <option value="">Sélectionner un type</option>
              <option value="CLIENT">Objectif Client</option>
              <option value="PRODUCTION">Objectif Production</option>
            </select>
          </div>

          <div class="form-group">
            <label for="category">Catégorie *</label>
            <select 
              id="category" 
              v-model="form.category" 
              required 
              class="form-select"
              @change="onCategoryChange"
            >
              <option value="">Sélectionner une catégorie</option>
              <option value="TERRITOIRE">Territoire (inclut les agences ex-point service sous Dakar Ville)</option>
              <option value="GRAND COMPTE">Grand Compte</option>
            </select>
          </div>

          <div class="form-group" v-if="form.category === 'TERRITOIRE'">
            <label for="territory">Territoire *</label>
            <select 
              id="territory" 
              v-model="form.territory" 
              required 
              class="form-select"
              @change="loadAgencies"
            >
              <option value="">Sélectionner un territoire</option>
              <option value="DAKAR_VILLE">Dakar Ville</option>
              <option value="DAKAR_BANLIEUE">Dakar Banlieue</option>
              <option value="PROVINCE_CENTRE_SUD">Province Centre-Sud</option>
              <option value="PROVINCE_NORD">Province Nord</option>
            </select>
          </div>

          <div class="form-group" v-if="form.category === 'GRAND COMPTE' || (form.category === 'TERRITOIRE' && form.territory)">
            <label for="agency">Agence *</label>
            <select 
              id="agency" 
              v-model="form.agency" 
              required 
              class="form-select"
            >
              <option value="">Sélectionner une agence</option>
              <option v-for="agency in agencies" :key="agency.code" :value="agency.code">
                {{ agency.name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label for="value">Valeur de l'objectif *</label>
            <input 
              id="value" 
              type="number" 
              v-model.number="form.value" 
              required 
              min="0"
              step="0.01"
              class="form-input"
              placeholder="Entrez la valeur de l'objectif"
            />
          </div>

          <div class="form-group">
            <label for="period">Période *</label>
            <select 
              id="period" 
              v-model="form.period" 
              required 
              class="form-select"
            >
              <option value="">Sélectionner une période</option>
              <option value="month">Mensuel</option>
              <option value="quarter">Trimestriel</option>
              <option value="year">Annuel</option>
            </select>
          </div>

          <div class="form-group" v-if="form.period === 'month'">
            <label for="month">Mois *</label>
            <select 
              id="month" 
              v-model="form.month" 
              required 
              class="form-select"
            >
              <option value="">Sélectionner un mois</option>
              <option v-for="(month, index) in months" :key="index" :value="index + 1">
                {{ month }}
              </option>
            </select>
          </div>

          <div class="form-group" v-if="form.period === 'month' || form.period === 'quarter' || form.period === 'year'">
            <label for="year">Année *</label>
            <select 
              id="year" 
              v-model="form.year" 
              required 
              class="form-select"
            >
              <option value="">Sélectionner une année</option>
              <option v-for="year in years" :key="year" :value="year">
                {{ year }}
              </option>
            </select>
          </div>

          <div class="form-group" v-if="form.period === 'quarter'">
            <label for="quarter">Trimestre *</label>
            <select 
              id="quarter" 
              v-model="form.quarter" 
              required 
              class="form-select"
            >
              <option value="">Sélectionner un trimestre</option>
              <option value="1">T1 (Janvier - Mars)</option>
              <option value="2">T2 (Avril - Juin)</option>
              <option value="3">T3 (Juillet - Septembre)</option>
              <option value="4">T4 (Octobre - Décembre)</option>
            </select>
          </div>

          <div class="form-group">
            <label for="description">Description (optionnel)</label>
            <textarea 
              id="description" 
              v-model="form.description" 
              rows="3"
              class="form-textarea"
              placeholder="Ajoutez une description pour cet objectif"
            ></textarea>
          </div>

          <div v-if="errorMessage" class="error-message">
            {{ errorMessage }}
          </div>

          <div v-if="successMessage" class="success-message">
            {{ successMessage }}
          </div>

          <div class="form-actions">
            <button type="button" @click="resetForm" class="btn-reset">Réinitialiser</button>
            <button type="submit" :disabled="loading" class="btn-submit">
              {{ loading ? 'Enregistrement...' : 'Enregistrer l\'objectif' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script>
import { useRouter } from 'vue-router';
import axios from 'axios';

export default {
  name: 'AddObjectivePage',
  setup() {
    const router = useRouter();
    return { router };
  },
  data() {
    return {
      loading: false,
      errorMessage: '',
      successMessage: '',
      agencies: [],
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      years: [],
      form: {
        type: '',
        category: '',
        territory: '',
        agency: '',
        value: null,
        period: '',
        month: '',
        quarter: '',
        year: '',
        description: ''
      }
    }
  },
  mounted() {
    this.generateYears();
    this.loadAgencies();
  },
  methods: {
    generateYears() {
      const currentYear = new Date().getFullYear();
      for (let i = currentYear - 2; i <= currentYear + 2; i++) {
        this.years.push(i);
      }
    },
    async loadAgencies() {
      try {
        // Charger les agences depuis l'API
        // Pour l'instant, on utilise une liste statique basée sur les territoires
        if (this.form.category === 'TERRITOIRE' && this.form.territory) {
          // Vous pouvez appeler une API pour charger les agences du territoire
          const response = await axios.get(`/api/oracle/data/clients`, {
            params: {
              period: 'month',
              zone: this.form.territory
            }
          });
          
          // Extraire les agences uniques depuis les données
          const agenciesSet = new Set();
          if (response.data && response.data.agencies) {
            response.data.agencies.forEach(agency => {
              if (agency.name) {
                agenciesSet.add(JSON.stringify({ code: agency.code || agency.name, name: agency.name }));
              }
            });
          }
          
          this.agencies = Array.from(agenciesSet).map(item => JSON.parse(item));
        } else if (this.form.category === 'GRAND COMPTE') {
          // Pour les grands comptes, on peut avoir une liste spécifique
          this.agencies = [
            { code: 'GC001', name: 'Grand Compte 1' },
            { code: 'GC002', name: 'Grand Compte 2' }
          ];
        }
      } catch (error) {
        console.error('Erreur lors du chargement des agences:', error);
        // En cas d'erreur, on utilise une liste vide
        this.agencies = [];
      }
    },
    onTypeChange() {
      // Réinitialiser les champs dépendants
      this.form.category = '';
      this.form.territory = '';
      this.form.agency = '';
      this.agencies = [];
    },
    onCategoryChange() {
      // Réinitialiser les champs dépendants
      this.form.territory = '';
      this.form.agency = '';
      this.agencies = [];
      if (this.form.category !== 'TERRITOIRE') {
        this.loadAgencies();
      }
    },
    async submitObjective() {
      this.loading = true;
      this.errorMessage = '';
      this.successMessage = '';

      try {
        const payload = {
          type: this.form.type,
          category: this.form.category,
          territory: this.form.territory || null,
          agency_code: this.form.agency,
          value: this.form.value,
          period: this.form.period,
          month: this.form.month || null,
          quarter: this.form.quarter || null,
          year: this.form.year,
          description: this.form.description || null
        };

        const response = await axios.post('/api/objectives', payload);

        this.successMessage = 'Objectif ajouté avec succès !';
        
        // Réinitialiser le formulaire après 2 secondes
        setTimeout(() => {
          this.resetForm();
          this.successMessage = '';
        }, 2000);

      } catch (error) {
        console.error('Erreur lors de l\'ajout de l\'objectif:', error);
        this.errorMessage = error.response?.data?.message || 'Une erreur est survenue lors de l\'ajout de l\'objectif.';
      } finally {
        this.loading = false;
      }
    },
    resetForm() {
      this.form = {
        type: '',
        category: '',
        territory: '',
        agency: '',
        value: null,
        period: '',
        month: '',
        quarter: '',
        year: '',
        description: ''
      };
      this.agencies = [];
      this.errorMessage = '';
      this.successMessage = '';
    },
    goBack() {
      this.router.push('/dashboard');
    }
  }
}
</script>

<style scoped>
.add-objective-page {
  width: 100%;
  min-height: 100vh;
  background: #f5f5f5;
  padding: 16px;
  box-sizing: border-box;
}

.page-container {
  width: 100%;
  max-width: 800px;
  margin: 0 auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.page-header h1 {
  margin: 0;
  font-size: 28px;
  color: #333;
}

.btn-back {
  padding: 10px 20px;
  background: #6c757d;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-back:hover {
  background: #5a6268;
}

.form-container {
  padding: 20px;
}

.objective-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  margin-bottom: 8px;
  font-weight: 500;
  color: #333;
  font-size: 14px;
}

.form-select,
.form-input,
.form-textarea {
  padding: 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s;
}

.form-select:focus,
.form-input:focus,
.form-textarea:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.form-textarea {
  resize: vertical;
  font-family: inherit;
}

.error-message {
  padding: 12px;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 6px;
  border: 1px solid #fecaca;
}

.success-message {
  padding: 12px;
  background: #d1fae5;
  color: #065f46;
  border-radius: 6px;
  border: 1px solid #a7f3d0;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e0e0e0;
}

.btn-reset,
.btn-submit {
  padding: 12px 24px;
  border: none;
  border-radius: 6px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset {
  background: #f3f4f6;
  color: #333;
}

.btn-reset:hover {
  background: #e5e7eb;
}

.btn-submit {
  background: #1A4D3A;
  color: white;
}

.btn-submit:hover:not(:disabled) {
  background: #153d2e;
}

.btn-submit:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .add-objective-page {
    padding: 12px;
  }

  .page-header {
    flex-direction: column;
    align-items: stretch;
    padding: 16px;
  }

  .page-header h1 {
    font-size: 22px;
  }

  .form-container {
    padding: 16px;
  }
}

@media (max-width: 480px) {
  .page-header h1 {
    font-size: 20px;
  }

  .form-container {
    padding: 12px;
  }
}
</style>
