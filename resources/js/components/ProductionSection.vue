<template>
  <div class="client-section">
    <div class="section-header">
      <h2 class="section-title">Production - {{ getPeriodTitle }}</h2>
      <div class="period-selector">
        <select v-model="selectedPeriod" class="period-select" @change="handlePeriodChange">
          <option value="week">Semaine</option>
          <option value="month">Mois</option>
          <option value="year">Année</option>
        </select>
        
        <!-- Sélecteur de date pour Semaine -->
        <template v-if="selectedPeriod === 'week'">
          <input 
            type="date" 
            v-model="selectedDate" 
            class="date-select"
            @change="updateWeekFromDate"
          />
        </template>
        
        <!-- Sélecteurs pour Mois -->
        <template v-if="selectedPeriod === 'month'">
          <select v-model="selectedMonth" class="month-select" @change="handleMonthChange">
            <option v-for="(month, index) in months" :key="index" :value="index + 1">
              {{ month }}
            </option>
          </select>
          <select v-model="selectedYear" class="year-select" @change="handleYearChange">
            <option v-for="year in years" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </template>
        
        <!-- Sélecteur pour Année -->
        <template v-if="selectedPeriod === 'year'">
          <select v-model="selectedYear" class="year-select" @change="handleYearChange">
            <option v-for="year in years" :key="year" :value="year">
              {{ year }}
            </option>
          </select>
        </template>
      </div>
    </div>
    
    <!-- Message de chargement en haut -->
    <div v-if="loading" class="loading-banner">
      <div class="loading-spinner-small"></div>
      <span>Chargement des données en cours... </span>
    </div>
    
    <!-- Message d'erreur -->
    <div v-if="error" class="error-message">
      ⚠️ {{ error }}
    </div>
    <div v-if="!loading && !error && (!hierarchicalData || Object.keys(hierarchicalData.TERRITOIRE || {}).length === 0)" class="info-message">
      ℹ️ Aucune donnée disponible. Vérifiez la connexion Oracle ou activez le mode fallback.
    </div>
    
    <!-- Tableau de production -->
    <div class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Code Gestion</th>
              <th>Chargé d'affaire</th>
              <th>Objectif</th>
              <th>Nombre de crédit décaissé <br>{{ tablePeriodLabels.previous }}</th>
              <th>Nombre de crédit décaissé <br>{{ tablePeriodLabels.current }}</th>
              <th>Variation <br>(nombre)</th>
              <th>Variation <br>(%)</th>
              <th>TRO</th>
              <th>Contribution agence <br>sur la zone</th>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr v-if="Object.keys(filteredHierarchicalData.TERRITOIRE || {}).length > 0" class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.objectif) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.m1) }}</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.m) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.variationNombre)">
                <strong>{{ formatVariation(territoireTotal.variationNombre) }}</strong>
              </td>
              <td :class="getVariationClass(territoireTotal.variationPourcent)">
                <strong>{{ formatVariationPercent(territoireTotal.variationPourcent) }}</strong>
              </td>
              <td :class="getAchievementClass(territoireTotal.atteinte)">
                <strong>{{ formatPercent(territoireTotal.atteinte) }}</strong>
              </td>
              <td :class="getContributionClass(territoireTotal.contribution)">
                <strong>{{ formatPercent(territoireTotal.contribution) }}</strong>
              </td>
            </tr>

            <!-- Territoires dans TERRITOIRE -->
            <template v-if="expandedSections.TERRITOIRE">
              <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
                <tr class="level-2-row" @click="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                  <td class="level-2">
                    <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                      {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                    </button>
                    {{ territory.name }}
                  </td>
                  <td><strong>-</strong></td>
                  <td><strong>-</strong></td>
                  <td><strong>{{ formatNumber(territory.total.objectif) }}</strong></td>
                  <td><strong>{{ formatNumber(territory.total.mois1) }}</strong></td>
                  <td><strong>{{ formatNumber(territory.total.mois) }}</strong></td>
                  <td :class="getVariationClass(territory.total.variation)">
                    <strong>{{ formatVariation(territory.total.variation) }}</strong>
                  </td>
                  <td :class="getVariationClass(territory.total.variation_pourcent)">
                    <strong>{{ formatVariationPercent(territory.total.variation_pourcent) }}</strong>
                  </td>
                  <td :class="getAchievementClass(territory.total.atteinte)">
                    <strong>{{ formatPercent(territory.total.atteinte) }}</strong>
                  </td>
                  <td :class="getContributionClass(territory.total.contribution || 0)">
                    <strong>{{ formatPercent(territory.total.contribution || 0) }}</strong>
                  </td>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                  <template v-for="(agency, agencyIndex) in territory.data" :key="agency.CODE_AGENCE || agency.AGENCE || agencyIndex">
                    <tr 
                      class="level-3-row"
                      @click="toggleAgencyExpand(agency, `TERRITOIRE_${territoryKey}_${getAgencyKey(agency, agencyIndex)}`)"
                    >
                      <td class="level-3">
                        <button 
                          class="expand-btn" 
                          @click.stop="toggleAgencyExpand(agency, `TERRITOIRE_${territoryKey}_${getAgencyKey(agency, agencyIndex)}`)"
                          v-if="hasChargeAffaireDetails(agency)"
                        >
                          {{ expandedSections[`TERRITOIRE_${territoryKey}_${getAgencyKey(agency, agencyIndex)}`] ? '−' : '+' }}
                        </button>
                        {{ agency.AGENCE || agency.name }}
                      </td>
                      <td :class="{ 'caf-all-label': isCafSummaryAll(agency) }">{{ getCodeGestionDisplay(agency) }}</td>
                      <td :class="{ 'caf-all-label': isCafSummaryAll(agency) }">{{ getChargeAffaireDisplay(agency) }}</td>
                      <td>{{ formatNumber(agency.OBJECTIF_PRODUCTION || agency.objectif || 0) }}</td>
                      <td>{{ formatNumber(agency.NOMBRE_DE_CREDITS_DECAISSES_M_1 || agency.m1 || 0) }}</td>
                      <td>{{ formatNumber(agency.NOMBRE_DE_CREDITS_DECAISSES_M || agency.m || 0) }}</td>
                      <td :class="getVariationClass(agency.VARIATION_NOMBRE || agency.variationNombre || 0)">
                        {{ formatVariation(agency.VARIATION_NOMBRE || agency.variationNombre || 0) }}
                      </td>
                      <td :class="getVariationClass(agency.VARIATION_POURCENT || agency.variationPourcent || 0)">
                        {{ formatVariationPercent(agency.VARIATION_POURCENT || agency.variationPourcent || 0) }}
                      </td>
                      <td :class="getAchievementClass(agency.TAUX_REALISATION || agency.atteinte || 0)">
                        {{ formatPercent(agency.TAUX_REALISATION || agency.atteinte || 0) }}
                      </td>
                      <td :class="getContributionClass(agency.contribution || 0)">
                        {{ formatPercent(agency.contribution || 0) }}
                      </td>
                    </tr>
                    <!-- Afficher tous les chargés d'affaire pour cette agence quand elle est expandée -->
                    <template v-if="expandedSections[`TERRITOIRE_${territoryKey}_${getAgencyKey(agency, agencyIndex)}`]">
                      <tr 
                        v-for="(chargeDetail, chargeIndex) in getChargeAffaireDetailsByBranchCode(agency.CODE_AGENCE || agency.BRANCH_CODE)" 
                        :key="`charge-${chargeIndex}`"
                        class="level-4-row charge-detail-row"
                      >
                        <td class="level-4">
                          {{ agency.CODE_AGENCE || agency.BRANCH_CODE || '-' }}
                        </td>
                        <td>{{ chargeDetail.codeGestion || chargeDetail.CODE_GESTION || '-' }}</td>
                        <td>{{ chargeDetail.chargeAffaire || chargeDetail.CHARGE_AFFAIRE || '-' }}</td>
                        <td>{{ formatNumber(chargeDetail.objectif ?? 0) }}</td>
                        <td>{{ formatNumber(chargeDetail.nombreDossiersM1 || chargeDetail.NOMBRE_DOSSIERS_M_1 || 0) }}</td>
                        <td>{{ formatNumber(chargeDetail.nombreDossiersM || chargeDetail.NOMBRE_DOSSIERS_M || 0) }}</td>
                        <td :class="getVariationClass(chargeDetail.variationNombre || chargeDetail.VARIATION_NOMBRE || 0)">
                          {{ formatVariation(chargeDetail.variationNombre || chargeDetail.VARIATION_NOMBRE || 0) }}
                        </td>
                        <td :class="getVariationClass(chargeDetail.variationPct || chargeDetail.VARIATION_PCT || 0)">
                          {{ formatVariationPercent(chargeDetail.variationPct || chargeDetail.VARIATION_PCT || 0) }}
                        </td>
                        <td>-</td>
                        <td>-</td>
                      </tr>
                      <tr v-if="getChargeAffaireDetailsByBranchCode(agency.CODE_AGENCE || agency.BRANCH_CODE).length === 0" class="level-4-row">
                        <td colspan="10" style="text-align: center; padding: 10px; color: #666;">
                          Aucun chargé d'affaire trouvé pour cette agence
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </template>

            <!-- GRAND COMPTE -->
            <tr v-if="grandCompte" class="level-3-row">
              <td class="level-3">GRAND COMPTE</td>
              <td>-</td>
              <td>-</td>
              <td>{{ formatNumber(grandCompte.objectif) }}</td>
              <td>{{ formatNumber(grandCompte.m1) }}</td>
              <td>{{ formatNumber(grandCompte.m) }}</td>
              <td :class="getVariationClass(grandCompte.variationNombre)">
                {{ formatVariation(grandCompte.variationNombre) }}
              </td>
              <td :class="getVariationClass(grandCompte.variationPourcent)">
                {{ formatVariationPercent(grandCompte.variationPourcent) }}
              </td>
              <td :class="getAchievementClass(grandCompte.atteinte)">
                {{ formatPercent(grandCompte.atteinte) }}
              </td>
              <td :class="getContributionClass(grandCompte.contribution)">
                {{ formatPercent(grandCompte.contribution) }}
              </td>
            </tr>

            <!-- TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(total.objectif) }}</strong></td>
              <td><strong>{{ formatNumber(total.m1) }}</strong></td>
              <td><strong>{{ formatNumber(total.m) }}</strong></td>
              <td :class="getVariationClass(total.variationNombre)">
                <strong>{{ formatVariation(total.variationNombre) }}</strong>
              </td>
              <td :class="getVariationClass(total.variationPourcent)">
                <strong>{{ formatVariationPercent(total.variationPourcent) }}</strong>
              </td>
              <td :class="getAchievementClass(total.atteinte)">
                <strong>{{ formatPercent(total.atteinte) }}</strong>
              </td>
              <td></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  name: 'ProductionSection',
  props: {
    selectedZoneProp: {
      type: String,
      default: null
    }
  },
  data() {
    const now = new Date();
    const getWeekNumber = (date) => {
      const d = new Date(Date.UTC(date.getFullYear(), date.getMonth(), date.getDate()));
      const dayNum = d.getUTCDay() || 7;
      d.setUTCDate(d.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
      return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
    };
    return {
      selectedPeriod: 'month',
      selectedDate: (() => {
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
      })(),
      selectedWeek: getWeekNumber(now),
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      expandedSections: {
        TERRITOIRE: false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      },
      hierarchicalDataFromBackend: null,
      chargeAffaireDetails: {}, // Détails par charge d'affaire
      chargeAffaireDetailsCache: new Map(), // Cache pour les détails par CAF
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      loading: false,
      error: null,
      grandCompteData: null, // Données du grand compte depuis l'API Oracle
      // Données de production - initialisées vides, seront remplies depuis l'API
      territories: {
        territoire_dakar_ville: {
          name: 'TERRITOIRE DAKAR VILLE',
          agencies: []
        },
        territoire_dakar_banlieue: {
          name: 'TERRITOIRE DAKAR BANLIEUE',
          agencies: []
        },
        territoire_province_centre_sud: {
          name: 'TERRITOIRE PROVINCE CENTRE-SUD',
          agencies: []
        },
        territoire_province_nord: {
          name: 'TERRITOIRE PROVINCE NORD',
          agencies: []
        }
      },
      productionData: {
        CORPORATE: {
          zone1: {
            name: 'TERRITOIRE DAKAR VILLE',
            agencies: []
          },
          zone2: {
            name: 'TERRITOIRE PROVINCE CENTRE-SUD',
            agencies: []
          }
        },
        RETAIL: {
          zone1: {
            name: 'TERRITOIRE DAKAR BANLIEUE',
            agencies: []
          },
          zone2: {
            name: 'TERRITOIRE PROVINCE NORD',
            agencies: []
          }
        }
      }
    };
  },
  computed: {
    years() {
      const currentYear = new Date().getFullYear();
      const years = [];
      for (let i = currentYear - 5; i <= currentYear + 2; i++) {
        years.push(i);
      }
      return years;
    },
    hierarchicalData() {
      // Utiliser les données hiérarchiques du backend si disponibles
      if (this.hierarchicalDataFromBackend && typeof this.hierarchicalDataFromBackend === 'object') {
        try {
          const data = JSON.parse(JSON.stringify(this.hierarchicalDataFromBackend));
          // Calculer les totaux et contributions si pas déjà calculés
          if (data.TERRITOIRE && typeof data.TERRITOIRE === 'object' && data.TERRITOIRE !== null) {
            // TOUJOURS recalculer les totaux à partir des données des agences pour s'assurer
            // que les objectifs fusionnés sont pris en compte
            Object.keys(data.TERRITOIRE).forEach(key => {
              const territory = data.TERRITOIRE[key];
              if (territory && territory.data) {
                // Recalculer les totaux à partir des données des agences (qui contiennent les objectifs fusionnés)
                const agencies = territory.data || [];
                const oldTotal = territory.total?.objectif || 0;
                territory.total = this.calculateZoneTotalsFromData(agencies);
                const newTotal = territory.total.objectif || 0;
                if (oldTotal !== newTotal) {
                  console.log(`🔄 Total recalculé pour ${territory.name || key}:`, {
                    ancien: oldTotal,
                    nouveau: newTotal,
                    agences: agencies.length,
                    objectifs_agences: agencies.map(a => ({
                      nom: a.AGENCE || a.name,
                      objectif: a.OBJECTIF_PRODUCTION || a.objectif || 0
                    }))
                  });
                }
              }
            });
            
            // Maintenant calculer les contributions après avoir recalculé tous les totaux
            const territoireTotalM = Object.values(data.TERRITOIRE).reduce((sum, t) => {
              return sum + (t.total?.mois || t.totals?.m || 0);
            }, 0);
            
            Object.keys(data.TERRITOIRE).forEach(key => {
              const territory = data.TERRITOIRE[key];
              if (territory && territory.total && territoireTotalM > 0) {
                territory.total.contribution = ((territory.total.mois || territory.total.m || 0) / territoireTotalM) * 100;
              }
            });
          }
          
          return data;
        } catch (e) {
          console.warn('Erreur lors du traitement des données hiérarchiques:', e);
        }
      }
      
      // Construire depuis les territories pour compatibilité
      if (!this.territories || typeof this.territories !== 'object') {
        return {
          TERRITOIRE: {
            territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', data: [], total: { objectif: 0, mois1: 0, mois: 0, m1: 0, m: 0, variation: 0, variation_pourcent: 0, atteinte: 0, contribution: 0 } },
            territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', data: [], total: { objectif: 0, mois1: 0, mois: 0, m1: 0, m: 0, variation: 0, variation_pourcent: 0, atteinte: 0, contribution: 0 } },
            territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', data: [], total: { objectif: 0, mois1: 0, mois: 0, m1: 0, m: 0, variation: 0, variation_pourcent: 0, atteinte: 0, contribution: 0 } },
            territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', data: [], total: { objectif: 0, mois1: 0, mois: 0, m1: 0, m: 0, variation: 0, variation_pourcent: 0, atteinte: 0, contribution: 0 } }
          }
        };
      }
      
      const data = {
        TERRITOIRE: {
          territoire_dakar_ville: {
            name: (this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.name) || 'TERRITOIRE DAKAR VILLE',
            data: (this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.agencies) || [],
            total: this.calculateZoneTotalsFromData((this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.agencies) || [])
          },
          territoire_dakar_banlieue: {
            name: (this.territories.territoire_dakar_banlieue && this.territories.territoire_dakar_banlieue.name) || 'TERRITOIRE DAKAR BANLIEUE',
            data: (this.territories.territoire_dakar_banlieue && this.territories.territoire_dakar_banlieue.agencies) || [],
            total: this.calculateZoneTotalsFromData((this.territories.territoire_dakar_banlieue && this.territories.territoire_dakar_banlieue.agencies) || [])
          },
          territoire_province_centre_sud: {
            name: (this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.name) || 'TERRITOIRE PROVINCE CENTRE-SUD',
            data: (this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.agencies) || [],
            total: this.calculateZoneTotalsFromData((this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.agencies) || [])
          },
          territoire_province_nord: {
            name: (this.territories.territoire_province_nord && this.territories.territoire_province_nord.name) || 'TERRITOIRE PROVINCE NORD',
            data: (this.territories.territoire_province_nord && this.territories.territoire_province_nord.agencies) || [],
            total: this.calculateZoneTotalsFromData((this.territories.territoire_province_nord && this.territories.territoire_province_nord.agencies) || [])
          }
        }
      };
      
      // Calculer la contribution des territoires
      const territoireTotalM = Object.values(data.TERRITOIRE).reduce((sum, t) => {
        return sum + (t.total?.mois || t.total?.m || 0);
      }, 0);
      
      if (territoireTotalM > 0) {
        Object.keys(data.TERRITOIRE).forEach(key => {
          const territory = data.TERRITOIRE[key];
          if (territory && territory.total) {
            territory.total.contribution = ((territory.total.mois || territory.total.m || 0) / territoireTotalM) * 100;
          }
        });
      }
      
      return data;
    },
    filteredHierarchicalData() {
      // S'assurer que hierarchicalData existe et est un objet
      if (!this.hierarchicalData || typeof this.hierarchicalData !== 'object' || this.hierarchicalData === null) {
        return {
          TERRITOIRE: {}
        };
      }
      
      if (!this.selectedZoneProp) {
        return this.hierarchicalData;
      }
      
      const filtered = {
        TERRITOIRE: {}
      };
      
      if (this.hierarchicalData.TERRITOIRE && 
          typeof this.hierarchicalData.TERRITOIRE === 'object' && 
          this.hierarchicalData.TERRITOIRE !== null &&
          !Array.isArray(this.hierarchicalData.TERRITOIRE) &&
          this.hierarchicalData.TERRITOIRE[this.selectedZoneProp]) {
        filtered.TERRITOIRE[this.selectedZoneProp] = this.hierarchicalData.TERRITOIRE[this.selectedZoneProp];
      }
      
      return filtered;
    },
    territoireTotal() {
      // Calculer le total de tous les territoires
      if (!this.hierarchicalData || !this.hierarchicalData.TERRITOIRE) {
        return { objectif: 0, m1: 0, m: 0, variationNombre: 0, variationPourcent: 0, atteinte: 0, contribution: 0 };
      }
      
      let totalObjectif = 0;
      let totalM1 = 0;
      let totalM = 0;
      
      Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
        if (territory && territory.total) {
          totalObjectif += territory.total.objectif || 0;
          totalM1 += territory.total.mois1 || territory.total.m1 || 0;
          totalM += territory.total.mois || territory.total.m || 0;
        }
      });
      
      const variationNombre = totalM - totalM1;
      const variationPourcent = totalM1 > 0 ? ((totalM - totalM1) / totalM1) * 100 : 0;
      const atteinte = totalObjectif > 0 ? (totalM / totalObjectif) * 100 : 0;
      
      const totalGlobalM = totalM;
      const contribution = totalGlobalM > 0 ? (totalM / totalGlobalM) * 100 : 0;
      
      return {
        objectif: totalObjectif,
        m1: totalM1,
        m: totalM,
        variationNombre: variationNombre,
        variationPourcent: variationPourcent,
        atteinte: atteinte,
        contribution: contribution
      };
    },
    // Compatibilité avec l'ancien code
    corporateTotal() {
      return this.territoireTotal;
    },
    retailTotal() {
      return {
        objectif: 0,
        m1: 0,
        m: 0,
        variationNombre: 0,
        variationPourcent: 0,
        atteinte: 0,
        contribution: 0
      };
    },
    grandCompte() {
      // Récupérer les données du grand compte depuis l'API ou retourner des valeurs vides
      if (this.grandCompteData) {
        const data = this.grandCompteData;
        const grandCompteM = data.m || 0;
        const variationNombre = grandCompteM - (data.m1 || 0);
        const variationPourcent = (data.m1 || 0) > 0 
          ? ((grandCompteM - data.m1) / data.m1) * 100 
          : 0;
        
        // Calculer la contribution du grand compte par rapport au total global
        // Utiliser les données brutes directement pour éviter les dépendances circulaires
        let corporateM = 0;
        let retailM = 0;
        
        // Calculer corporateM depuis les données brutes
        const corporateZone1 = this.productionData.CORPORATE.zone1.agencies.reduce((sum, a) => sum + (a.m || 0), 0);
        const corporateZone2 = this.productionData.CORPORATE.zone2.agencies.reduce((sum, a) => sum + (a.m || 0), 0);
        corporateM = corporateZone1 + corporateZone2;
        
        // Calculer retailM depuis les données brutes
        retailM = this.productionData.RETAIL.zone1.agencies.reduce((sum, a) => sum + (a.m || 0), 0);
        
        const totalGlobal = corporateM + retailM + grandCompteM;
        const contribution = totalGlobal > 0 ? (grandCompteM / totalGlobal) * 100 : 0;
        
        return {
          objectif: data.objectif || 0,
          m1: data.m1 || 0,
          m: grandCompteM,
          variationNombre: variationNombre,
          variationPourcent: variationPourcent,
          atteinte: (data.objectif || 0) > 0 ? (grandCompteM / data.objectif) * 100 : 0,
          contribution: contribution
        };
      }
      
      // Retourner des valeurs vides par défaut
      return {
        objectif: 0,
        m1: 0,
        m: 0,
        variationNombre: 0,
        variationPourcent: 0,
        atteinte: 0,
        contribution: 0
      };
    },
    total() {
      const territoire = this.territoireTotal;
      const grandCompte = this.grandCompte;
      
      const totalObjectif = territoire.objectif + grandCompte.objectif;
      const totalM1 = territoire.m1 + grandCompte.m1;
      const totalM = territoire.m + grandCompte.m;
      
      return {
        objectif: totalObjectif,
        m1: totalM1,
        m: totalM,
        variationNombre: totalM - totalM1,
        variationPourcent: totalM1 > 0 ? ((totalM - totalM1) / totalM1) * 100 : 0,
        atteinte: totalObjectif > 0 ? (totalM / totalObjectif) * 100 : 0
      };
    },
    getPeriodTitle() {
      if (this.selectedPeriod === 'week') {
        return `Semaine ${this.selectedWeek} ${this.selectedYear}`;
      } else if (this.selectedPeriod === 'month') {
        return `${this.months[this.selectedMonth - 1]} ${this.selectedYear}`;
      } else if (this.selectedPeriod === 'year') {
        return `Année ${this.selectedYear}`;
      }
      return `${this.months[this.selectedMonth - 1]} ${this.selectedYear}`;
    },
    tablePeriodLabels() {
      if (this.selectedPeriod === 'week') {
        return {
          current: 'S',
          previous: 'S-1'
        };
      } else if (this.selectedPeriod === 'month') {
        return {
          current: 'M',
          previous: 'M-1'
        };
      } else if (this.selectedPeriod === 'year') {
        return {
          current: 'A',
          previous: 'A-1'
        };
      }
      return {
        current: 'M',
        previous: 'M-1'
      };
    }
  },
  mounted() {
    // Charger les données au montage du composant
    this.fetchProductionData();
  },
  watch: {
    selectedMonth() {
      this.fetchProductionData();
    },
    selectedYear() {
      this.fetchProductionData();
    },
    selectedPeriod() {
      this.fetchProductionData();
    }
  },
  methods: {
    toggleExpand(section) {
      this.expandedSections[section] = !this.expandedSections[section];
    },
    calculateZoneTotals(agencies) {
      const totals = agencies.reduce((acc, agency) => {
        acc.objectif += agency.objectif || 0;
        acc.m1 += agency.m1 || 0;
        acc.m += agency.m || 0;
        return acc;
      }, { objectif: 0, m1: 0, m: 0 });
      
      totals.variationNombre = totals.m - totals.m1;
      totals.variationPourcent = totals.m1 > 0 ? ((totals.m - totals.m1) / totals.m1) * 100 : 0;
      totals.atteinte = totals.objectif > 0 ? (totals.m / totals.objectif) * 100 : 0;
      
      // Calculer la contribution de la zone par rapport au total CORPORATE/RETAIL
      // Cette valeur sera calculée dans corporateTotal/retailTotal
      totals.contribution = 0;
      
      // Calculer la contribution pour chaque agence par rapport à sa zone
      agencies.forEach(agency => {
        agency.contribution = totals.m > 0 ? (agency.m / totals.m) * 100 : 0;
      });
      
      return totals;
    },
    calculateZoneTotalsFromData(dataArray) {
      // Convertir les données brutes Oracle en format compatible
      const totals = dataArray.reduce((acc, item) => {
        // Support des deux formats : Oracle (NOMBRE_DE_CREDITS_DECAISSES_M) et format transformé (m)
        acc.objectif += item.OBJECTIF_PRODUCTION || item.objectif || 0;
        acc.mois1 += item.NOMBRE_DE_CREDITS_DECAISSES_M_1 || item.m1 || 0;
        acc.mois += item.NOMBRE_DE_CREDITS_DECAISSES_M || item.m || 0;
        return acc;
      }, { objectif: 0, mois1: 0, mois: 0 });
      
      // Calculer les variations
      totals.variation = totals.mois - totals.mois1;
      totals.variation_pourcent = totals.mois1 > 0 ? ((totals.mois - totals.mois1) / totals.mois1) * 100 : 0;
      totals.atteinte = totals.objectif > 0 ? (totals.mois / totals.objectif) * 100 : 0;
      totals.contribution = 0; // Sera calculé plus tard
      
      // Ajouter les alias pour compatibilité
      totals.m1 = totals.mois1;
      totals.m = totals.mois;
      totals.variationNombre = totals.variation;
      totals.variationPourcent = totals.variation_pourcent;
      
      return totals;
    },
    getCorporateTotalM() {
      // Utiliser la nouvelle structure
      if (this.hierarchicalData && this.hierarchicalData.TERRITOIRE) {
        let totalM = 0;
        Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory && territory.total) {
            totalM += territory.total.mois || territory.total.m || 0;
          }
        });
        return totalM;
      }
      
      // Fallback sur l'ancienne structure
      const territoire1 = this.calculateZoneTotals((this.territories.territoire_dakar_ville && this.territories.territoire_dakar_ville.agencies) || []);
      const territoire2 = this.calculateZoneTotals((this.territories.territoire_province_centre_sud && this.territories.territoire_province_centre_sud.agencies) || []);
      return territoire1.m + territoire2.m;
    },
    getRetailTotalM() {
      // Pour la production, RETAIL n'existe plus, retourner 0
      return 0;
    },
    formatNumber(num) {
      if (num === null || num === undefined) return '-';
      return new Intl.NumberFormat('fr-FR').format(num);
    },
    formatVariation(num) {
      if (num === null || num === undefined) return '-';
      if (num === 0) return '0';
      return num > 0 ? `+${this.formatNumber(num)}` : this.formatNumber(num);
    },
    formatVariationPercent(num) {
      if (num === null || num === undefined || isNaN(num)) return '-';
      return num > 0 ? `+${num.toFixed(0)}%` : `${num.toFixed(0)}%`;
    },
    formatPercent(num) {
      if (num === null || num === undefined) return '-';
      return `${num.toFixed(0)}%`;
    },
    getVariationClass(value) {
      if (value === null || value === undefined || value === 0) return '';
      return value > 0 ? 'positive' : 'negative';
    },
    getAchievementClass(value) {
      if (value === null || value === undefined) return '';
      if (value >= 100) return 'achievement-high';
      if (value >= 70) return 'achievement-medium';
      return 'achievement-low';
    },
    getContributionClass(value) {
      if (value === null || value === undefined) return '';
      if (value >= 20) return 'contribution-high';
      if (value >= 10) return 'contribution-medium';
      return 'contribution-low';
    },
    async fetchProductionData() {
      this.loading = true;
      this.error = null;
      
      try {
        // Utiliser l'API Laravel comme proxy vers l'API Python
        // Cela évite les problèmes CORS et centralise la gestion
        const apiUrl = '/api/oracle/data/production';
        
        const params = { period: this.selectedPeriod };
        if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'week') {
          if (this.selectedDate) {
            let dateToSend = this.selectedDate;
            if (dateToSend.includes('/')) {
              const parts = dateToSend.split('/');
              dateToSend = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            params.date = dateToSend;
          }
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        }
        
        const response = await axios.get(apiUrl, {
          params
        });
        const apiData = response.data;
        
        // Vérifier si c'est une erreur
        if (apiData.error) {
          throw new Error(apiData.detail || apiData.error || 'Erreur lors de la récupération des données');
        }
        
        // Vérifier si le mode fallback est activé
        if (apiData.fallback) {
          // Afficher un message d'information (pas une erreur)
          this.error = null; // Pas d'erreur, juste un avertissement
          console.warn(apiData.message || 'Mode fallback activé - Données de test');
        }
        
        // Priorité au nouveau format hiérarchique
        if (apiData.hierarchicalData) {
          console.log('📊 Données hiérarchiques reçues (production):', apiData.hierarchicalData);
          this.hierarchicalDataFromBackend = apiData.hierarchicalData;
          
          // Récupérer les détails par charge d'affaire
          if (apiData.chargeAffaireDetails) {
            this.chargeAffaireDetails = apiData.chargeAffaireDetails;
            console.log('📊 Détails par CAF reçus (production):', Object.keys(this.chargeAffaireDetails).length, 'agences');
            // Réinitialiser le cache
            this.chargeAffaireDetailsCache.clear();
          }
          
          // Extraire les territoires et points de service
          if (apiData.hierarchicalData.TERRITOIRE) {
            this.territories = {
              territoire_dakar_ville: {
                name: apiData.hierarchicalData.TERRITOIRE.territoire_dakar_ville?.name || 'TERRITOIRE DAKAR VILLE',
                agencies: apiData.hierarchicalData.TERRITOIRE.territoire_dakar_ville?.data || []
              },
              territoire_dakar_banlieue: {
                name: apiData.hierarchicalData.TERRITOIRE.territoire_dakar_banlieue?.name || 'TERRITOIRE DAKAR BANLIEUE',
                agencies: apiData.hierarchicalData.TERRITOIRE.territoire_dakar_banlieue?.data || []
              },
              territoire_province_centre_sud: {
                name: apiData.hierarchicalData.TERRITOIRE.territoire_province_centre_sud?.name || 'TERRITOIRE PROVINCE CENTRE-SUD',
                agencies: apiData.hierarchicalData.TERRITOIRE.territoire_province_centre_sud?.data || []
              },
              territoire_province_nord: {
                name: apiData.hierarchicalData.TERRITOIRE.territoire_province_nord?.name || 'TERRITOIRE PROVINCE NORD',
                agencies: apiData.hierarchicalData.TERRITOIRE.territoire_province_nord?.data || []
              }
            };
          }
          
          // Mettre à jour aussi productionData pour compatibilité
          this.productionData = {
            CORPORATE: {
              zone1: this.territories.territoire_dakar_ville,
              zone2: this.territories.territoire_province_centre_sud
            },
            RETAIL: {
              zone1: this.territories.territoire_dakar_banlieue,
              zone2: this.territories.territoire_province_nord
            }
          };
          this.grandCompteData = apiData.grandCompte || null;
        } else if (apiData.territories) {
          // Format territories (sans hierarchicalData)
          this.territories = {
            territoire_dakar_ville: {
              name: apiData.territories.territoire_dakar_ville?.name || 'TERRITOIRE DAKAR VILLE',
              agencies: apiData.territories.territoire_dakar_ville?.data || []
            },
            territoire_dakar_banlieue: {
              name: apiData.territories.territoire_dakar_banlieue?.name || 'TERRITOIRE DAKAR BANLIEUE',
              agencies: apiData.territories.territoire_dakar_banlieue?.data || []
            },
            territoire_province_centre_sud: {
              name: apiData.territories.territoire_province_centre_sud?.name || 'TERRITOIRE PROVINCE CENTRE-SUD',
              agencies: apiData.territories.territoire_province_centre_sud?.data || []
            },
            territoire_province_nord: {
              name: apiData.territories.territoire_province_nord?.name || 'TERRITOIRE PROVINCE NORD',
              agencies: apiData.territories.territoire_province_nord?.data || []
            }
          };
          
          this.productionData = {
            CORPORATE: {
              zone1: this.territories.territoire_dakar_ville,
              zone2: this.territories.territoire_province_centre_sud
            },
            RETAIL: {
              zone1: this.territories.territoire_dakar_banlieue,
              zone2: this.territories.territoire_province_nord
            }
          };
          this.grandCompteData = apiData.grandCompte || null;
        } else {
          // Format ancien - transformer les données
          const dataToTransform = apiData.data || [];
          this.transformApiData(dataToTransform);
        }
        
      } catch (error) {
        console.error('Erreur lors de la récupération des données de production:', error);
        
        // Afficher un message d'erreur détaillé
        let errorMessage = 'Erreur lors du chargement des données';
        
        // Détecter les erreurs de timeout
        const errorDetail = error.response?.data?.detail || error.response?.data?.error || '';
        const isTimeout = error.code === 'ECONNABORTED' || 
                         error.message?.includes('timeout') || 
                         error.message?.includes('timed out') ||
                         errorDetail.includes('timeout') ||
                         errorDetail.includes('cURL error 28') ||
                         errorDetail.includes('Operation timed out');
        
        if (isTimeout) {
          errorMessage = `⏱️ Le chargement prend plus de temps que prévu. Les calculs Oracle sont en cours, veuillez patienter. Vous pouvez rafraîchir la page dans quelques instants.`;
        } else if (error.response) {
          // Erreur HTTP (404, 500, etc.)
          const errorData = error.response.data;
          const detail = errorData?.detail || errorData?.error || errorData?.message || '';
          
          // Vérifier si c'est une erreur de connexion Oracle
          if (detail.includes('Connection refused') || detail.includes('cannot connect to database')) {
            errorMessage = `⚠️ Erreur de connexion à la base de données Oracle:\n\n` +
              `Le serveur Oracle n'est pas accessible.\n\n` +
              `Vérifiez que:\n` +
              `1. Le serveur Oracle est démarré et accessible\n` +
              `2. Le réseau/firewall permet la connexion\n` +
              `3. Les paramètres de connexion sont corrects\n\n` +
              `Pour tester la connexion, exécutez:\n` +
              `cd python-service && python test_oracle_connection.py`;
          } else {
            errorMessage = detail || `Erreur HTTP ${error.response.status}`;
          }
        } else if (error.request) {
          // Pas de réponse du serveur
          errorMessage = `⚠️ Impossible de se connecter au service Python.\n\n` +
            `Vérifiez que:\n` +
            `1. Le service Python est démarré (port 8001)\n` +
            `2. Exécutez: cd python-service && ./start.sh\n` +
            `3. Vérifiez que le port 8001 n'est pas bloqué`;
        } else {
          // Erreur de configuration
          errorMessage = error.message || 'Erreur inconnue';
        }
        
        this.error = errorMessage;
        
        // En cas d'erreur, utiliser des données vides
        this.territories = {
          territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
          territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
          territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
          territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
        };
        this.productionData = {
          CORPORATE: {
            zone1: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
            zone2: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] }
          },
          RETAIL: {
            zone1: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
            zone2: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
          }
        };
        this.grandCompteData = null;
      } finally {
        this.loading = false;
      }
    },
    transformApiData(apiData) {
      // Les données de l'API contiennent les agences avec leurs statistiques
      // Nous devons les mapper aux territoires selon le nouveau zonage
      
      const territoriesData = {
        territoire_dakar_ville: [],
        territoire_dakar_banlieue: [],
        territoire_province_centre_sud: [],
        territoire_province_nord: []
      };
      
      // Chercher d'abord le grand compte dans les données
      let grandCompteFound = null;
      
      // Mapping des agences aux territoires selon le nouveau zonage
      apiData.forEach(agence => {
        const agenceName = agence.AGENCE || agence.agence || 'Inconnu';
        
        // Vérifier si c'est le grand compte
        if (agenceName.toUpperCase().includes('GRAND COMPTE') || agenceName.toUpperCase().includes('GRAND_COMPTE')) {
          grandCompteFound = {
            name: agenceName,
            objectif: agence.OBJECTIF_PRODUCTION || 0,
            m1: agence.NOMBRE_DE_CREDITS_DECAISSES_M_1 || 0,
            m: agence.NOMBRE_DE_CREDITS_DECAISSES_M || 0,
            variationNombre: agence.VARIATION_NOMBRE || 0,
            variationPourcent: agence.VARIATION_POURCENT || 0,
            atteinte: agence.TAUX_REALISATION || 0
          };
          return; // Ne pas ajouter aux territoires
        }
        
        const agenceData = {
          name: agenceName,
          objectif: agence.OBJECTIF_PRODUCTION || 0,
          m1: agence.NOMBRE_DE_CREDITS_DECAISSES_M_1 || 0,
          m: agence.NOMBRE_DE_CREDITS_DECAISSES_M || 0,
          variationNombre: agence.VARIATION_NOMBRE || 0,
          variationPourcent: agence.VARIATION_POURCENT || 0,
          atteinte: agence.TAUX_REALISATION || 0,
          contribution: 0 // Sera calculé après
        };
        
        // Utiliser le mapping des territoires basé sur le nom de l'agence
        // Les territoires sont mappés dans le backend, mais on peut aussi le faire ici
        const territoryMap = {
          'CASTOR': 'territoire_dakar_ville',
          'MARISTES': 'territoire_dakar_ville',
          'VITRINE LAMINE': 'territoire_dakar_ville',
          'GUEYE': 'territoire_dakar_ville',
          'POINT E': 'territoire_dakar_ville',
          'LINGUERE': 'territoire_dakar_banlieue',
          'GUEDIAWAYE': 'territoire_dakar_banlieue',
          'RUFISQUE': 'territoire_dakar_banlieue',
          'PARCELLES': 'territoire_dakar_banlieue',
          'PIKINE': 'territoire_dakar_banlieue',
          'MBOUR': 'territoire_province_centre_sud',
          'TAMBACOUNDA': 'territoire_province_centre_sud',
          'ZIGUINCHOR': 'territoire_province_centre_sud',
          'THIES': 'territoire_province_centre_sud',
          'KAOLACK': 'territoire_province_centre_sud',
          'TOUBA': 'territoire_province_nord',
          'SAINT-LOUIS': 'territoire_province_nord',
          'LOUGA': 'territoire_province_nord',
          'DIOURBEL': 'territoire_province_nord',
          'OUROSSOGUI': 'territoire_province_nord'
        };
        
        // Trouver le territoire correspondant
        let territoryKey = null;
        const agenceNameUpper = agenceName.toUpperCase();
        for (const [key, territory] of Object.entries(territoryMap)) {
          if (agenceNameUpper.includes(key)) {
            territoryKey = territory;
            break;
          }
        }
        
        // Si aucun territoire trouvé, utiliser le mapping par défaut (DAKAR VILLE)
        if (!territoryKey) {
          territoryKey = 'territoire_dakar_ville';
        }
        
        territoriesData[territoryKey].push(agenceData);
      });
      
      // Stocker les données du grand compte
      this.grandCompteData = grandCompteFound;
      
      // Calculer les contributions pour chaque agence dans chaque territoire
      const calculateContributions = (agencies) => {
        const totalM = agencies.reduce((sum, a) => sum + a.m, 0);
        agencies.forEach(agency => {
          agency.contribution = totalM > 0 ? (agency.m / totalM) * 100 : 0;
        });
      };
      
      Object.values(territoriesData).forEach(agencies => {
        calculateContributions(agencies);
      });
      
      const agenciesByTerritory = {
        territoire_dakar_ville: [],
        territoire_dakar_banlieue: [],
        territoire_province_centre_sud: [],
        territoire_province_nord: []
      };
      
      for (const [territoryKey, agencies] of Object.entries(territoriesData)) {
        for (const agency of agencies) {
          const agencyNameUpper = (agency.name || agency.AGENCE || '').toUpperCase();
          const servicePointNames = ['SCAT URBAM', 'NIARRY TALLY', 'NIARRY TALLI', 'C-E NIARRY'];
          const isServicePoint = servicePointNames.some(sp => agencyNameUpper.includes(sp));
          
          if (isServicePoint) {
            agenciesByTerritory['territoire_dakar_ville'].push(agency);
          } else {
            agenciesByTerritory[territoryKey].push(agency);
          }
        }
      }
      
      // Mettre à jour les territoires
      this.territories = {
        territoire_dakar_ville: {
          name: 'TERRITOIRE DAKAR VILLE',
          agencies: agenciesByTerritory.territoire_dakar_ville
        },
        territoire_dakar_banlieue: {
          name: 'TERRITOIRE DAKAR BANLIEUE',
          agencies: agenciesByTerritory.territoire_dakar_banlieue
        },
        territoire_province_centre_sud: {
          name: 'TERRITOIRE PROVINCE CENTRE-SUD',
          agencies: agenciesByTerritory.territoire_province_centre_sud
        },
        territoire_province_nord: {
          name: 'TERRITOIRE PROVINCE NORD',
          agencies: agenciesByTerritory.territoire_province_nord
        }
      };
      
      // Construire la structure hiérarchique
      this.hierarchicalDataFromBackend = {
        TERRITOIRE: {
          territoire_dakar_ville: {
            name: 'TERRITOIRE DAKAR VILLE',
            data: agenciesByTerritory.territoire_dakar_ville.map(a => ({
              ...a,
              AGENCE: a.name || a.AGENCE,
              CODE_AGENCE: a.CODE_AGENCE || a.code_agence
            })),
            total: this.calculateZoneTotalsFromData(agenciesByTerritory.territoire_dakar_ville)
          },
          territoire_dakar_banlieue: {
            name: 'TERRITOIRE DAKAR BANLIEUE',
            data: agenciesByTerritory.territoire_dakar_banlieue.map(a => ({
              ...a,
              AGENCE: a.name || a.AGENCE,
              CODE_AGENCE: a.CODE_AGENCE || a.code_agence
            })),
            total: this.calculateZoneTotalsFromData(agenciesByTerritory.territoire_dakar_banlieue)
          },
          territoire_province_centre_sud: {
            name: 'TERRITOIRE PROVINCE CENTRE-SUD',
            data: agenciesByTerritory.territoire_province_centre_sud.map(a => ({
              ...a,
              AGENCE: a.name || a.AGENCE,
              CODE_AGENCE: a.CODE_AGENCE || a.code_agence
            })),
            total: this.calculateZoneTotalsFromData(agenciesByTerritory.territoire_province_centre_sud)
          },
          territoire_province_nord: {
            name: 'TERRITOIRE PROVINCE NORD',
            data: agenciesByTerritory.territoire_province_nord.map(a => ({
              ...a,
              AGENCE: a.name || a.AGENCE,
              CODE_AGENCE: a.CODE_AGENCE || a.code_agence
            })),
            total: this.calculateZoneTotalsFromData(agenciesByTerritory.territoire_province_nord)
          }
        }
      };
      
      // Mettre à jour aussi productionData pour compatibilité
      this.productionData = {
        CORPORATE: {
          zone1: this.territories.territoire_dakar_ville,
          zone2: this.territories.territoire_province_centre_sud
        },
        RETAIL: {
          zone1: this.territories.territoire_dakar_banlieue,
          zone2: this.territories.territoire_province_nord
        }
      };
    },
    handlePeriodChange() {
      this.fetchProductionData();
    },
    handleMonthChange() {
      this.fetchProductionData();
    },
    handleYearChange() {
      this.fetchProductionData();
    },
    updateWeekFromDate() {
      // Logique pour mettre à jour la semaine depuis la date
      this.fetchProductionData();
    },
    getAgencyKey(agency, index) {
      // Générer une clé unique pour chaque agence
      if (!agency) return `agency-${index}`;
      
      const name = agency.name || agency.AGENCE || agency.NOM_AGENCE || '';
      const code = agency.CODE_AGENCE || agency.code_agence || agency.BRANCH_CODE || agency.BRANCH_CODE_AC_NO || '';
      
      // Utiliser le premier identifiant disponible
      const identifier = name || code || `agency-${index}`;
      return `agency-${identifier}-${index}`;
    },
    getChargeAffaireDetailsByBranchCode(branchCode) {
      if (!branchCode) {
        return [];
      }
      
      if (!this.chargeAffaireDetails || Object.keys(this.chargeAffaireDetails).length === 0) {
        return [];
      }
      
      // Convertir branchCode en string pour la comparaison
      const branchCodeStr = String(branchCode).trim();
      
      // Vérifier le cache d'abord
      if (this.chargeAffaireDetailsCache.has(branchCodeStr)) {
        return this.chargeAffaireDetailsCache.get(branchCodeStr);
      }
      
      // Chercher directement par la clé (la clé est le branch_code dans le backend)
      if (this.chargeAffaireDetails[branchCodeStr]) {
        const directMatch = this.chargeAffaireDetails[branchCodeStr];
        if (Array.isArray(directMatch) && directMatch.length > 0) {
          // Mettre en cache le résultat
          this.chargeAffaireDetailsCache.set(branchCodeStr, directMatch);
          return directMatch;
        }
      }
      
      // Mettre en cache le résultat vide
      this.chargeAffaireDetailsCache.set(branchCodeStr, []);
      return [];
    },
    hasChargeAffaireDetails(agency) {
      if (!agency) return false;
      
      const branchCode = agency.CODE_AGENCE || agency.BRANCH_CODE || agency.branch_code;
      if (branchCode && this.getChargeAffaireDetailsByBranchCode(branchCode).length > 0) {
        return true;
      }
      
      return false;
    },
    isCafSummaryAll(agency) {
      if (!agency) return false;
      const bc = String(agency.CODE_AGENCE || agency.BRANCH_CODE || '').trim();
      const details = bc ? this.getChargeAffaireDetailsByBranchCode(bc) : [];
      return details.length > 1;
    },
    getCodeGestionDisplay(agency) {
      if (!agency) return '-';
      const bc = String(agency.CODE_AGENCE || agency.BRANCH_CODE || '').trim();
      const details = bc ? this.getChargeAffaireDetailsByBranchCode(bc) : [];
      if (details.length > 1) return 'Tous';
      if (details.length === 1) {
        const g = details[0].codeGestion || details[0].CODE_GESTION;
        return g || '-';
      }
      const codeGestion = agency.CODE_GESTION || agency.codeGestion || agency.CODE_GESTION_PRET || agency.codeGestionPret;
      return codeGestion || '-';
    },
    getChargeAffaireDisplay(agency) {
      if (!agency) return '-';
      const bc = String(agency.CODE_AGENCE || agency.BRANCH_CODE || '').trim();
      const details = bc ? this.getChargeAffaireDetailsByBranchCode(bc) : [];
      if (details.length > 1) return 'Tous';
      if (details.length === 1) {
        return details[0].chargeAffaire || details[0].CHARGE_AFFAIRE || '-';
      }
      const chargeAffaire = agency.CHARGE_AFFAIRE || agency.chargeAffaire;
      return chargeAffaire || '-';
    },
    toggleAgencyExpand(agency, sectionKey) {
      if (!this.hasChargeAffaireDetails(agency)) {
        return; // Ne rien faire si l'agence n'a pas de détails CAF
      }
      this.expandedSections[sectionKey] = !this.expandedSections[sectionKey];
    }
  }
}
</script>

<style scoped>
.client-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.section-title {
  font-size: 24px;
  font-weight: 600;
  margin: 0;
  color: #333;
}

.period-selector {
  display: flex;
  gap: 10px;
  align-items: center;
}

.period-select,
.month-select,
.week-select,
.year-select,
.date-select {
  padding: 8px 12px;
  border: 1px solid #DDD;
  border-radius: 4px;
  font-size: 14px;
  background: white;
  color: #333;
  cursor: pointer;
}

.period-select:hover,
.month-select:hover,
.week-select:hover,
.year-select:hover,
.date-select:hover {
  border-color: #1A4D3A;
}

.period-select:focus,
.month-select:focus,
.week-select:focus,
.year-select:focus,
.date-select:focus {
  outline: none;
  border-color: #1A4D3A;
  box-shadow: 0 0 0 2px rgba(26, 77, 58, 0.1);
}

.zone-agencies-section {
  margin-top: 30px;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.agencies-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  min-width: 1200px;
}

.agencies-table thead {
  background: #DC2626;
  color: white;
}

.agencies-table th {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
  border-right: 1px solid #444;
  white-space: nowrap;
}

.agencies-table th:first-child {
  text-align: left;
  padding-left: 16px;
}

.agencies-table td {
  padding: 10px 8px;
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid #EEE;
  border-right: 1px solid #F0F0F0;
}

.agencies-table td:first-child {
  text-align: left;
  padding-left: 16px;
}

.level-1-row {
  background: #2A2A2A;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.level-1 {
  font-size: 16px;
  padding-left: 16px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-2-row {
  background: #4A4A4A;
  color: white;
  font-weight: 600;
  cursor: pointer;
}

.service-point-row {
  background: white !important;
  color: #333 !important;
}

.service-point-cell {
  color: #333 !important;
}

.level-2 {
  font-size: 14px;
  padding-left: 32px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-3-row {
  background: white;
}

.level-3 {
  padding-left: 48px !important;
  color: #333;
  cursor: pointer;
}

.level-3-row:hover {
  background: #f5f5f5;
}

.agencies-table td.caf-all-label {
  color: #b0b8c4;
  font-weight: 500;
}

.level-4-row {
  background: #FAFAFA;
}

.level-4 {
  padding-left: 64px !important;
  color: #666;
  font-size: 12px;
}

.charge-detail-row {
  background: #FAFAFA !important;
}

.charge-detail-row:hover {
  background: #F0F0F0 !important;
}

.total-row {
  background: #F5F5F5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
}

.expand-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border-radius: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
  transition: background 0.2s;
}

.level-2 .expand-btn {
  border-color: rgba(255, 255, 255, 0.3);
}

.positive {
  color: #10B981;
  font-weight: 600;
}

.negative {
  color: #EF4444;
  font-weight: 600;
}

.achievement-high {
  color: #10B981;
  font-weight: 500;
}

.achievement-medium {
  color: #F59E0B;
  font-weight: 500;
}

.achievement-low {
  color: #EF4444;
  font-weight: 500;
}

.contribution-high {
  color: #10B981;
  font-weight: 500;
}

.contribution-medium {
  color: #F59E0B;
  font-weight: 500;
}

.contribution-low {
  color: #EF4444;
  font-weight: 500;
}

.loading-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 20px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #F0F9FF 0%, #E0F2FE 100%);
  border: 2px solid #0EA5E9;
  border-radius: 8px;
  color: #0369A1;
  font-size: 14px;
  font-weight: 500;
  box-shadow: 0 2px 8px rgba(14, 165, 233, 0.15);
}

.loading-spinner-small {
  width: 20px;
  height: 20px;
  border: 3px solid #BAE6FD;
  border-top: 3px solid #0EA5E9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  flex-shrink: 0;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.error-message {
  padding: 20px;
  text-align: left;
  background: #FEF2F2;
  border: 2px solid #EF4444;
  border-radius: 8px;
  color: #DC2626;
  font-weight: 500;
  margin: 20px 0;
  white-space: pre-line;
  font-family: monospace;
  font-size: 12px;
  line-height: 1.6;
  max-height: 400px;
  overflow-y: auto;
}

.info-message {
  padding: 15px;
  text-align: center;
  background: #EFF6FF;
  border: 1px solid #3B82F6;
  border-radius: 8px;
  color: #1E40AF;
  font-weight: 500;
  margin: 20px 0;
}

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .client-section {
    padding: 15px;
  }
  
  .section-header {
    flex-wrap: wrap;
    gap: 15px;
    padding: 15px;
  }
  
  .section-title {
    font-size: 22px;
  }
  
  .period-selector {
    gap: 8px;
  }
  
  .month-select,
  .year-select,
  .period-select,
  .date-select {
    padding: 8px 12px;
    font-size: 13px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .client-section {
    padding: 12px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 12px;
  }
  
  .section-title {
    font-size: 20px;
    width: 100%;
  }
  
  .period-selector {
    width: 100%;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .month-select,
  .year-select,
  .period-select,
  .date-select {
    flex: 1;
    min-width: 120px;
    padding: 8px 10px;
    font-size: 13px;
  }
  
  .loading-banner {
    padding: 10px 15px;
    font-size: 13px;
  }
  
  .error-message {
    padding: 15px;
    font-size: 11px;
    margin: 15px 0;
  }
  
  .info-message {
    padding: 12px;
    font-size: 13px;
    margin: 15px 0;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .client-section {
    padding: 10px;
  }
  
  .section-header {
    padding: 10px;
  }
  
  .section-title {
    font-size: 18px;
  }
  
  .period-selector {
    flex-direction: column;
    width: 100%;
  }
  
  .month-select,
  .year-select,
  .period-select,
  .date-select {
    width: 100%;
    min-width: 100%;
    padding: 8px 10px;
    font-size: 12px;
  }
  
  .loading-banner {
    padding: 8px 12px;
    font-size: 12px;
  }
  
  .loading-spinner-small {
    width: 18px;
    height: 18px;
  }
  
  .error-message {
    padding: 12px;
    font-size: 10px;
    margin: 12px 0;
  }
  
  .info-message {
    padding: 10px;
    font-size: 12px;
    margin: 12px 0;
  }
}
</style>

