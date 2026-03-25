<template>
  <div class="client-section">
    <div class="section-header">
      <h2 class="section-title">Production en volume par Agence - {{ getPeriodTitle }}</h2>
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
      <span>Chargement des données en cours... Cette opération peut prendre jusqu'à 5 minutes.</span>
    </div>
    
    <!-- Message d'erreur -->
    <div v-if="error" class="error-message">
      ⚠️ {{ error }}
    </div>
    <div v-if="!loading && !error && (!hierarchicalData || Object.keys(hierarchicalData.TERRITOIRE || {}).length === 0)" class="info-message">
      ℹ️ Aucune donnée disponible. Vérifiez la connexion Oracle ou activez le mode fallback.
    </div>
    
    <!-- Tableau de production en volume -->
    <div class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Code Gestion</th>
              <th>Chargé d'affaire</th>
              <th>Objectif</th>
              <th>Volume de crédit décaissé <br>{{ tablePeriodLabels.previous }}</th>
              <th>Volume de crédit décaissé <br>{{ tablePeriodLabels.current }}</th>
              <th>Variation <br>(Volume)</th>
              <th>Variation <br>(%)</th>
              <th>TRO</th>
              <th>Contribution agence <br>sur la zone</th>
              <th>Frais de dossier <br>{{ tablePeriodLabels.previous }}</th>
              <th>Frais de dossier <br>{{ tablePeriodLabels.current }}</th>
              <th>Ecart</th>
              <th>Variation </th>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr v-if="filteredHierarchicalData && filteredHierarchicalData.TERRITOIRE && Object.keys(filteredHierarchicalData.TERRITOIRE).length > 0" class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">
                  {{ expandedSections.TERRITOIRE ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.objectif) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.volumeM1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.volumeM) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.variationVolume)">
                <strong>{{ formatVariationCurrency(territoireTotal.variationVolume) }}</strong>
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
              <td><strong>{{ formatCurrency(territoireTotal.fraisM1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.fraisM) }}</strong></td>
              <td :class="getVariationClass(territoireTotal.ecartFrais)">
                <strong>{{ formatVariationCurrency(territoireTotal.ecartFrais) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(territoireTotal.variationFrais) }}</strong></td>
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
                  <td><strong>{{ formatCurrency(territory.total.volumeM1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.total.volumeM) }}</strong></td>
                  <td :class="getVariationClass(territory.total.variationVolume)">
                    <strong>{{ formatVariationCurrency(territory.total.variationVolume) }}</strong>
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
                  <td><strong>{{ formatCurrency(territory.total.fraisM1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.total.fraisM) }}</strong></td>
                  <td :class="getVariationClass(territory.total.ecartFrais)">
                    <strong>{{ formatVariationCurrency(territory.total.ecartFrais) }}</strong>
                  </td>
                  <td><strong>{{ formatCurrency(territory.total.variationFrais) }}</strong></td>
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
                      <td>{{ getCodeGestionDisplay(agency) }}</td>
                      <td>{{ getChargeAffaireDisplay(agency) }}</td>
                      <td>{{ formatNumber(agency.OBJECTIF_PRODUCTION || agency.objectif || 0) }}</td>
                    <td>{{ formatCurrency(agency.VOLUME_CREDIT_DECAISSE_M_1 || agency.volumeM1 || 0) }}</td>
                    <td>{{ formatCurrency(agency.VOLUME_CREDIT_DECAISSE_M || agency.volumeM || 0) }}</td>
                    <td :class="getVariationClass(agency.VARIATION_VOLUME || agency.variationVolume || 0)">
                      {{ formatVariationCurrency(agency.VARIATION_VOLUME || agency.variationVolume || 0) }}
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
                    <td>{{ formatCurrency(agency.FRAIS_DOSSIER_M_1 || agency.fraisM1 || 0) }}</td>
                    <td>{{ formatCurrency(agency.FRAIS_DOSSIER_M || agency.fraisM || 0) }}</td>
                    <td :class="getVariationClass(agency.ECART_FRAIS || agency.ecartFrais || 0)">
                      {{ formatVariationCurrency(agency.ECART_FRAIS || agency.ecartFrais || 0) }}
                    </td>
                    <td>{{ formatCurrency(agency.VARIATION_FRAIS || agency.variationFrais || 0) }}</td>
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
                        <td>-</td>
                        <td>{{ formatCurrency(chargeDetail.volumeDebloqueM1 || chargeDetail.VOLUME_DEBLOQUE_M_1 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.volumeDebloqueM || chargeDetail.VOLUME_DEBLOQUE_M || 0) }}</td>
                        <td :class="getVariationClass(chargeDetail.variationVolume || chargeDetail.VARIATION_VOLUME || 0)">
                          {{ formatVariationCurrency(chargeDetail.variationVolume || chargeDetail.VARIATION_VOLUME || 0) }}
                        </td>
                        <td :class="getVariationClass(chargeDetail.variationPct || chargeDetail.VARIATION_PCT || 0)">
                          {{ formatVariationPercent(chargeDetail.variationPct || chargeDetail.VARIATION_PCT || 0) }}
                        </td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                      </tr>
                      <tr v-if="getChargeAffaireDetailsByBranchCode(agency.CODE_AGENCE || agency.BRANCH_CODE).length === 0" class="level-4-row">
                        <td colspan="14" style="text-align: center; padding: 10px; color: #666;">
                          Aucun chargé d'affaire trouvé pour cette agence
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </template>

            <!-- POINT SERVICES -->
            <tr v-if="Object.keys(filteredHierarchicalData['POINT SERVICES'] || {}).length > 0" class="level-1-row" @click="toggleExpand('POINT SERVICES')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('POINT SERVICES')">
                  {{ expandedSections['POINT SERVICES'] ? '−' : '+' }}
                </button>
                <strong>POINT SERVICES</strong>
              </td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(pointServicesTotal.objectif) }}</strong></td>
              <td><strong>{{ formatCurrency(pointServicesTotal.volumeM1) }}</strong></td>
              <td><strong>{{ formatCurrency(pointServicesTotal.volumeM) }}</strong></td>
              <td :class="getVariationClass(pointServicesTotal.variationVolume)">
                <strong>{{ formatVariationCurrency(pointServicesTotal.variationVolume) }}</strong>
              </td>
              <td :class="getVariationClass(pointServicesTotal.variationPourcent)">
                <strong>{{ formatVariationPercent(pointServicesTotal.variationPourcent) }}</strong>
              </td>
              <td :class="getAchievementClass(pointServicesTotal.atteinte)">
                <strong>{{ formatPercent(pointServicesTotal.atteinte) }}</strong>
              </td>
              <td :class="getContributionClass(pointServicesTotal.contribution)">
                <strong>{{ formatPercent(pointServicesTotal.contribution) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(pointServicesTotal.fraisM1) }}</strong></td>
              <td><strong>{{ formatCurrency(pointServicesTotal.fraisM) }}</strong></td>
              <td :class="getVariationClass(pointServicesTotal.ecartFrais)">
                <strong>{{ formatVariationCurrency(pointServicesTotal.ecartFrais) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(pointServicesTotal.variationFrais) }}</strong></td>
            </tr>
            
            <!-- Points de service individuels directement sous POINT SERVICES -->
            <template v-if="expandedSections['POINT SERVICES']">
              <template v-for="(servicePoint, servicePointKey) in filteredHierarchicalData['POINT SERVICES']" :key="servicePointKey">
                <!-- Afficher directement les points de service individuels (SCAT URBAM, NIARRY TALLY) -->
                <template v-if="servicePoint.data && servicePoint.data.length > 0">
                  <template v-for="(agency, agencyIndex) in servicePoint.data" :key="agency.CODE_AGENCE || agency.AGENCE || agency.name || agencyIndex">
                    <tr 
                      class="level-2-row service-point-row"
                      @click="toggleAgencyExpand(agency, `POINT_SERVICES_${getAgencyKey(agency, agencyIndex)}`)"
                    >
                      <td class="level-2 service-point-cell">
                        <button 
                          class="expand-btn" 
                          @click.stop="toggleAgencyExpand(agency, `POINT_SERVICES_${getAgencyKey(agency, agencyIndex)}`)"
                          v-if="hasChargeAffaireDetails(agency)"
                        >
                          {{ expandedSections[`POINT_SERVICES_${getAgencyKey(agency, agencyIndex)}`] ? '−' : '+' }}
                        </button>
                        {{ agency.AGENCE || agency.name }}
                      </td>
                      <td>{{ getCodeGestionDisplay(agency) }}</td>
                      <td>{{ getChargeAffaireDisplay(agency) }}</td>
                      <td>{{ formatNumber(agency.OBJECTIF_PRODUCTION || agency.objectif || 0) }}</td>
                    <td>{{ formatCurrency(agency.VOLUME_CREDIT_DECAISSE_M_1 || agency.volumeM1 || 0) }}</td>
                    <td>{{ formatCurrency(agency.VOLUME_CREDIT_DECAISSE_M || agency.volumeM || 0) }}</td>
                    <td :class="getVariationClass(agency.VARIATION_VOLUME || agency.variationVolume || 0)">
                      {{ formatVariationCurrency(agency.VARIATION_VOLUME || agency.variationVolume || 0) }}
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
                    <td>{{ formatCurrency(agency.FRAIS_DOSSIER_M_1 || agency.fraisM1 || 0) }}</td>
                    <td>{{ formatCurrency(agency.FRAIS_DOSSIER_M || agency.fraisM || 0) }}</td>
                    <td :class="getVariationClass(agency.ECART_FRAIS || agency.ecartFrais || 0)">
                      {{ formatVariationCurrency(agency.ECART_FRAIS || agency.ecartFrais || 0) }}
                    </td>
                    <td>{{ formatCurrency(agency.VARIATION_FRAIS || agency.variationFrais || 0) }}</td>
                    </tr>
                    <!-- Afficher tous les chargés d'affaire pour cette agence quand elle est expandée -->
                    <template v-if="expandedSections[`POINT_SERVICES_${getAgencyKey(agency, agencyIndex)}`]">
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
                        <td>-</td>
                        <td>{{ formatCurrency(chargeDetail.volumeDebloqueM1 || chargeDetail.VOLUME_DEBLOQUE_M_1 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.volumeDebloqueM || chargeDetail.VOLUME_DEBLOQUE_M || 0) }}</td>
                        <td :class="getVariationClass(chargeDetail.variationVolume || chargeDetail.VARIATION_VOLUME || 0)">
                          {{ formatVariationCurrency(chargeDetail.variationVolume || chargeDetail.VARIATION_VOLUME || 0) }}
                        </td>
                        <td :class="getVariationClass(chargeDetail.variationPct || chargeDetail.VARIATION_PCT || 0)">
                          {{ formatVariationPercent(chargeDetail.variationPct || chargeDetail.VARIATION_PCT || 0) }}
                        </td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                        <td>-</td>
                      </tr>
                      <tr v-if="getChargeAffaireDetailsByBranchCode(agency.CODE_AGENCE || agency.BRANCH_CODE).length === 0" class="level-4-row">
                        <td colspan="14" style="text-align: center; padding: 10px; color: #666;">
                          Aucun chargé d'affaire trouvé pour cette agence
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
              </template>
            </template>
            
            <!-- GRAND COMPTE -->
            <tr v-if="grandCompte && grandCompte.volumeM > 0" class="level-3-row">
              <td class="level-3">GRAND COMPTE</td>
              <td>-</td>
              <td>-</td>
              <td>{{ formatNumber(grandCompte.objectif) }}</td>
              <td>{{ formatCurrency(grandCompte.volumeM1) }}</td>
              <td>{{ formatCurrency(grandCompte.volumeM) }}</td>
              <td :class="getVariationClass(grandCompte.variationVolume)">
                {{ formatVariationCurrency(grandCompte.variationVolume) }}
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
              <td>{{ formatCurrency(grandCompte.fraisM1) }}</td>
              <td>{{ formatCurrency(grandCompte.fraisM) }}</td>
              <td :class="getVariationClass(grandCompte.ecartFrais)">
                {{ formatVariationCurrency(grandCompte.ecartFrais) }}
              </td>
              <td>{{ formatCurrency(grandCompte.variationFrais) }}</td>
            </tr>

            <!-- TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(total.objectif) }}</strong></td>
              <td><strong>{{ formatCurrency(total.volumeM1) }}</strong></td>
              <td><strong>{{ formatCurrency(total.volumeM) }}</strong></td>
              <td :class="getVariationClass(total.variationVolume)">
                <strong>{{ formatVariationCurrency(total.variationVolume) }}</strong>
              </td>
              <td :class="getVariationClass(total.variationPourcent)">
                <strong>{{ formatVariationPercent(total.variationPourcent) }}</strong>
              </td>
              <td :class="getAchievementClass(total.atteinte)">
                <strong>{{ formatPercent(total.atteinte) }}</strong>
              </td>
              <td></td>
              <td><strong>{{ formatCurrency(total.fraisM1) }}</strong></td>
              <td><strong>{{ formatCurrency(total.fraisM) }}</strong></td>
              <td :class="getVariationClass(total.ecartFrais)">
                <strong>{{ formatVariationCurrency(total.ecartFrais) }}</strong>
              </td>
              <td><strong>{{ formatCurrency(total.variationFrais) }}</strong></td>
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
  name: 'ProductionVolumeSection',
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
        'POINT SERVICES': false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false,
        'POINT SERVICES_service_points': false
      },
      hierarchicalDataFromBackend: null,
      servicePoints: [],
      chargeAffaireDetails: {}, // Détails par charge d'affaire
      chargeAffaireDetailsCache: new Map(), // Cache pour les détails par CAF
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      loading: false,
      error: null,
      grandCompteData: null,
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
      if (this.hierarchicalDataFromBackend && typeof this.hierarchicalDataFromBackend === 'object') {
        try {
          const data = JSON.parse(JSON.stringify(this.hierarchicalDataFromBackend));
          
          console.log('🔍 hierarchicalData - données brutes:', data);
          console.log('🔍 hierarchicalData - TERRITOIRE existe?', !!data.TERRITOIRE);
          console.log('🔍 hierarchicalData - clés TERRITOIRE:', data.TERRITOIRE ? Object.keys(data.TERRITOIRE) : []);
          
          if (data.TERRITOIRE && typeof data.TERRITOIRE === 'object' && data.TERRITOIRE !== null) {
            const territoireTotalM = Object.values(data.TERRITOIRE).reduce((sum, t) => {
              return sum + (t.total?.volumeM || t.total?.volume || 0);
            }, 0);
            
            Object.keys(data.TERRITOIRE).forEach(key => {
              const territory = data.TERRITOIRE[key];
              if (territory && !territory.total) {
                const agencies = territory.data || [];
                territory.total = this.calculateZoneTotalsFromData(agencies);
              }
              if (territory && territory.total && territoireTotalM > 0) {
                territory.total.contribution = ((territory.total.volumeM || territory.total.volume || 0) / territoireTotalM) * 100;
              }
            });
          }
          
          if (data['POINT SERVICES'] && typeof data['POINT SERVICES'] === 'object' && data['POINT SERVICES'] !== null) {
            Object.keys(data['POINT SERVICES']).forEach(key => {
              const servicePoint = data['POINT SERVICES'][key];
              if (servicePoint && !servicePoint.total) {
                const agencies = servicePoint.data || [];
                servicePoint.total = this.calculateZoneTotalsFromData(agencies);
              }
            });
          }
          
          console.log('🔍 hierarchicalData - retourne les données depuis hierarchicalDataFromBackend');
          return data;
        } catch (e) {
          console.warn('Erreur lors du traitement des données hiérarchiques:', e);
          console.error('Erreur détaillée:', e);
        }
      }
      
      console.log('⚠️ hierarchicalData - hierarchicalDataFromBackend est vide, construction depuis territories');
      console.log('⚠️ hierarchicalData - territories:', this.territories);
      
      if (!this.territories || typeof this.territories !== 'object') {
        console.warn('⚠️ hierarchicalData - territories est aussi vide');
        return {
          TERRITOIRE: {},
          'POINT SERVICES': {}
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
        },
        'POINT SERVICES': {
          service_points: {
            name: 'POINTS SERVICES',
            data: this.servicePoints || [],
            total: this.calculateZoneTotalsFromData(this.servicePoints || [])
          }
        }
      };
      
      const territoireTotalM = Object.values(data.TERRITOIRE).reduce((sum, t) => {
        return sum + (t.total?.volumeM || t.total?.volume || 0);
      }, 0);
      
      if (territoireTotalM > 0) {
        Object.keys(data.TERRITOIRE).forEach(key => {
          const territory = data.TERRITOIRE[key];
          if (territory && territory.total) {
            territory.total.contribution = ((territory.total.volumeM || territory.total.volume || 0) / territoireTotalM) * 100;
          }
        });
      }
      
      return data;
    },
    filteredHierarchicalData() {
      console.log('🔍 filteredHierarchicalData - hierarchicalData:', this.hierarchicalData);
      console.log('🔍 filteredHierarchicalData - TERRITOIRE existe?', !!this.hierarchicalData?.TERRITOIRE);
      console.log('🔍 filteredHierarchicalData - clés TERRITOIRE:', this.hierarchicalData?.TERRITOIRE ? Object.keys(this.hierarchicalData.TERRITOIRE) : []);
      
      if (!this.hierarchicalData || typeof this.hierarchicalData !== 'object' || this.hierarchicalData === null) {
        console.warn('⚠️ filteredHierarchicalData - hierarchicalData est vide ou invalide');
        return {
          TERRITOIRE: {},
          'POINT SERVICES': {}
        };
      }
      
      if (!this.selectedZoneProp) {
        console.log('🔍 filteredHierarchicalData - pas de zone sélectionnée, retour de hierarchicalData complet');
        return this.hierarchicalData;
      }
      
      const filtered = {
        TERRITOIRE: {},
        'POINT SERVICES': (this.hierarchicalData['POINT SERVICES'] && typeof this.hierarchicalData['POINT SERVICES'] === 'object' && this.hierarchicalData['POINT SERVICES'] !== null)
          ? this.hierarchicalData['POINT SERVICES']
          : {}
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
      if (!this.hierarchicalData || !this.hierarchicalData.TERRITOIRE) {
        return { objectif: 0, volumeM1: 0, volumeM: 0, variationVolume: 0, variationPourcent: 0, atteinte: 0, contribution: 0, fraisM1: 0, fraisM: 0, ecartFrais: 0, variationFrais: 0 };
      }
      
      let totalObjectif = 0;
      let totalVolumeM1 = 0;
      let totalVolumeM = 0;
      let totalFraisM1 = 0;
      let totalFraisM = 0;
      
      Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
        if (territory && territory.total) {
          console.log('🔍 territoireTotal - territoire:', territory.name, 'total:', territory.total);
          totalObjectif += territory.total.objectif || 0;
          totalVolumeM1 += territory.total.volumeM1 || 0;
          totalVolumeM += territory.total.volumeM || 0;
          totalFraisM1 += territory.total.fraisM1 || 0;
          totalFraisM += territory.total.fraisM || 0;
        }
      });
      
      console.log('🔍 territoireTotal - totaux calculés:', {
        totalObjectif,
        totalVolumeM1,
        totalVolumeM,
        totalFraisM1,
        totalFraisM
      });
      
      const variationVolume = totalVolumeM - totalVolumeM1;
      const variationPourcent = totalVolumeM1 > 0 ? ((totalVolumeM - totalVolumeM1) / totalVolumeM1) * 100 : 0;
      const atteinte = totalObjectif > 0 ? (totalVolumeM / totalObjectif) * 100 : 0;
      const ecartFrais = totalFraisM - totalFraisM1;
      const variationFrais = totalFraisM;
      
      let pointServicesM = 0;
      if (this.hierarchicalData && this.hierarchicalData['POINT SERVICES']) {
        Object.values(this.hierarchicalData['POINT SERVICES']).forEach(servicePoint => {
          if (servicePoint && servicePoint.total) {
            pointServicesM += servicePoint.total.volumeM || servicePoint.total.volume || 0;
          }
        });
      }
      const totalGlobalM = totalVolumeM + pointServicesM;
      const contribution = totalGlobalM > 0 ? (totalVolumeM / totalGlobalM) * 100 : 0;
      
      return {
        objectif: totalObjectif,
        volumeM1: totalVolumeM1,
        volumeM: totalVolumeM,
        variationVolume: variationVolume,
        variationPourcent: variationPourcent,
        atteinte: atteinte,
        contribution: contribution,
        fraisM1: totalFraisM1,
        fraisM: totalFraisM,
        ecartFrais: ecartFrais,
        variationFrais: variationFrais
      };
    },
    pointServicesTotal() {
      if (!this.hierarchicalData || !this.hierarchicalData['POINT SERVICES']) {
        return { objectif: 0, volumeM1: 0, volumeM: 0, variationVolume: 0, variationPourcent: 0, atteinte: 0, contribution: 0, fraisM1: 0, fraisM: 0, ecartFrais: 0, variationFrais: 0 };
      }
      
      let totalObjectif = 0;
      let totalVolumeM1 = 0;
      let totalVolumeM = 0;
      let totalFraisM1 = 0;
      let totalFraisM = 0;
      
      Object.values(this.hierarchicalData['POINT SERVICES']).forEach(servicePoint => {
        if (servicePoint && servicePoint.total) {
          totalObjectif += servicePoint.total.objectif || 0;
          totalVolumeM1 += servicePoint.total.volumeM1 || 0;
          totalVolumeM += servicePoint.total.volumeM || 0;
          totalFraisM1 += servicePoint.total.fraisM1 || 0;
          totalFraisM += servicePoint.total.fraisM || 0;
        }
      });
      
      const variationVolume = totalVolumeM - totalVolumeM1;
      const variationPourcent = totalVolumeM1 > 0 ? ((totalVolumeM - totalVolumeM1) / totalVolumeM1) * 100 : 0;
      const atteinte = totalObjectif > 0 ? (totalVolumeM / totalObjectif) * 100 : 0;
      const ecartFrais = totalFraisM - totalFraisM1;
      const variationFrais = totalFraisM;
      
      let territoireM = 0;
      if (this.hierarchicalData && this.hierarchicalData.TERRITOIRE) {
        Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory && territory.total) {
            territoireM += territory.total.volumeM || territory.total.volume || 0;
          }
        });
      }
      const totalGlobalM = totalVolumeM + territoireM;
      const contribution = totalGlobalM > 0 ? (totalVolumeM / totalGlobalM) * 100 : 0;
      
      return {
        objectif: totalObjectif,
        volumeM1: totalVolumeM1,
        volumeM: totalVolumeM,
        variationVolume: variationVolume,
        variationPourcent: variationPourcent,
        atteinte: atteinte,
        contribution: contribution,
        fraisM1: totalFraisM1,
        fraisM: totalFraisM,
        ecartFrais: ecartFrais,
        variationFrais: variationFrais
      };
    },
    grandCompte() {
      if (this.grandCompteData) {
        const data = this.grandCompteData;
        const grandCompteM = data.volumeM || 0;
        const variationVolume = grandCompteM - (data.volumeM1 || 0);
        const variationPourcent = (data.volumeM1 || 0) > 0 
          ? ((grandCompteM - data.volumeM1) / data.volumeM1) * 100 
          : 0;
        const ecartFrais = (data.fraisM || 0) - (data.fraisM1 || 0);
        
        let territoireM = 0;
        let pointServicesM = 0;
        
        if (this.hierarchicalData && this.hierarchicalData.TERRITOIRE) {
          Object.values(this.hierarchicalData.TERRITOIRE).forEach(territory => {
            if (territory && territory.total) {
              territoireM += territory.total.volumeM || territory.total.volume || 0;
            }
          });
        }
        
        if (this.hierarchicalData && this.hierarchicalData['POINT SERVICES']) {
          Object.values(this.hierarchicalData['POINT SERVICES']).forEach(servicePoint => {
            if (servicePoint && servicePoint.total) {
              pointServicesM += servicePoint.total.volumeM || servicePoint.total.volume || 0;
            }
          });
        }
        
        const totalGlobal = territoireM + pointServicesM + grandCompteM;
        const contribution = totalGlobal > 0 ? (grandCompteM / totalGlobal) * 100 : 0;
        
        return {
          objectif: data.objectif || 0,
          volumeM1: data.volumeM1 || 0,
          volumeM: grandCompteM,
          variationVolume: variationVolume,
          variationPourcent: variationPourcent,
          atteinte: (data.objectif || 0) > 0 ? (grandCompteM / data.objectif) * 100 : 0,
          contribution: contribution,
          fraisM1: data.fraisM1 || 0,
          fraisM: data.fraisM || 0,
          ecartFrais: ecartFrais,
          variationFrais: data.fraisM || 0
        };
      }
      
      return {
        objectif: 0,
        volumeM1: 0,
        volumeM: 0,
        variationVolume: 0,
        variationPourcent: 0,
        atteinte: 0,
        contribution: 0,
        fraisM1: 0,
        fraisM: 0,
        ecartFrais: 0,
        variationFrais: 0
      };
    },
    total() {
      const territoire = this.territoireTotal;
      const pointServices = this.pointServicesTotal;
      const grandCompte = this.grandCompte;
      
      const totalObjectif = territoire.objectif + pointServices.objectif + grandCompte.objectif;
      const totalVolumeM1 = territoire.volumeM1 + pointServices.volumeM1 + grandCompte.volumeM1;
      const totalVolumeM = territoire.volumeM + pointServices.volumeM + grandCompte.volumeM;
      const totalFraisM1 = territoire.fraisM1 + pointServices.fraisM1 + grandCompte.fraisM1;
      const totalFraisM = territoire.fraisM + pointServices.fraisM + grandCompte.fraisM;
      
      return {
        objectif: totalObjectif,
        volumeM1: totalVolumeM1,
        volumeM: totalVolumeM,
        variationVolume: totalVolumeM - totalVolumeM1,
        variationPourcent: totalVolumeM1 > 0 ? ((totalVolumeM - totalVolumeM1) / totalVolumeM1) * 100 : 0,
        atteinte: totalObjectif > 0 ? (totalVolumeM / totalObjectif) * 100 : 0,
        fraisM1: totalFraisM1,
        fraisM: totalFraisM,
        ecartFrais: totalFraisM - totalFraisM1,
        variationFrais: totalFraisM
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
    calculateZoneTotalsFromData(dataArray) {
      const totals = dataArray.reduce((acc, item) => {
        acc.objectif += item.OBJECTIF_PRODUCTION || item.objectif || 0;
        acc.volumeM1 += item.VOLUME_CREDIT_DECAISSE_M_1 || item.volumeM1 || 0;
        acc.volumeM += item.VOLUME_CREDIT_DECAISSE_M || item.volumeM || 0;
        acc.fraisM1 += item.FRAIS_DOSSIER_M_1 || item.fraisM1 || 0;
        acc.fraisM += item.FRAIS_DOSSIER_M || item.fraisM || 0;
        return acc;
      }, { objectif: 0, volumeM1: 0, volumeM: 0, fraisM1: 0, fraisM: 0 });
      
      totals.variationVolume = totals.volumeM - totals.volumeM1;
      totals.variation_pourcent = totals.volumeM1 > 0 ? ((totals.volumeM - totals.volumeM1) / totals.volumeM1) * 100 : 0;
      totals.atteinte = totals.objectif > 0 ? (totals.volumeM / totals.objectif) * 100 : 0;
      totals.ecartFrais = totals.fraisM - totals.fraisM1;
      totals.variationFrais = totals.fraisM;
      totals.contribution = 0;
      
      return totals;
    },
    formatNumber(num) {
      if (num === null || num === undefined) return '-';
      return new Intl.NumberFormat('fr-FR').format(num);
    },
    formatCurrency(num) {
      if (num === null || num === undefined || num === 0) return '-';
      return new Intl.NumberFormat('fr-FR', { 
        style: 'currency', 
        currency: 'XOF',
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      }).format(num).replace('XOF', '').trim();
    },
    formatVariationCurrency(num) {
      if (num === null || num === undefined || num === 0) return '-';
      const formatted = this.formatCurrency(Math.abs(num));
      return num > 0 ? `+${formatted}` : `-${formatted}`;
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
        const apiUrl = '/api/oracle/data/production-volume';
        
        const params = {};
        if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'week') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        }
        
        const response = await axios.get(apiUrl, { 
          params
        });
        const apiData = response.data;
        
        console.log('🔍 Réponse API production-volume complète:', apiData);
        console.log('🔍 Status:', response.status);
        console.log('🔍 Type de apiData:', typeof apiData);
        console.log('🔍 apiData.hierarchicalData existe?', !!apiData.hierarchicalData);
        
        if (apiData.error) {
          throw new Error(apiData.detail || apiData.error || 'Erreur lors de la récupération des données');
        }
        
        if (apiData.fallback) {
          this.error = null;
          console.warn(apiData.message || 'Mode fallback activé - Données de test');
        }
        
        // Les données sont directement dans apiData (pas dans apiData.data)
        const dataToUse = apiData;
        
        if (dataToUse.hierarchicalData) {
          console.log('📊 Données hiérarchiques reçues (production volume):', dataToUse.hierarchicalData);
          this.hierarchicalDataFromBackend = dataToUse.hierarchicalData;
          
          // Récupérer les détails par charge d'affaire
          if (dataToUse.chargeAffaireDetails) {
            this.chargeAffaireDetails = dataToUse.chargeAffaireDetails;
            console.log('📊 Détails par CAF reçus (production volume):', Object.keys(this.chargeAffaireDetails).length, 'agences');
            // Réinitialiser le cache
            this.chargeAffaireDetailsCache.clear();
          }
          
          if (dataToUse.hierarchicalData.TERRITOIRE) {
            this.territories = {
              territoire_dakar_ville: {
                name: dataToUse.hierarchicalData.TERRITOIRE.territoire_dakar_ville?.name || 'TERRITOIRE DAKAR VILLE',
                agencies: dataToUse.hierarchicalData.TERRITOIRE.territoire_dakar_ville?.data || []
              },
              territoire_dakar_banlieue: {
                name: dataToUse.hierarchicalData.TERRITOIRE.territoire_dakar_banlieue?.name || 'TERRITOIRE DAKAR BANLIEUE',
                agencies: dataToUse.hierarchicalData.TERRITOIRE.territoire_dakar_banlieue?.data || []
              },
              territoire_province_centre_sud: {
                name: dataToUse.hierarchicalData.TERRITOIRE.territoire_province_centre_sud?.name || 'TERRITOIRE PROVINCE CENTRE-SUD',
                agencies: dataToUse.hierarchicalData.TERRITOIRE.territoire_province_centre_sud?.data || []
              },
              territoire_province_nord: {
                name: dataToUse.hierarchicalData.TERRITOIRE.territoire_province_nord?.name || 'TERRITOIRE PROVINCE NORD',
                agencies: dataToUse.hierarchicalData.TERRITOIRE.territoire_province_nord?.data || []
              }
            };
          }
          
          if (dataToUse.hierarchicalData['POINT SERVICES'] && dataToUse.hierarchicalData['POINT SERVICES'].service_points) {
            this.servicePoints = dataToUse.hierarchicalData['POINT SERVICES'].service_points.data || [];
          }
          
          if (dataToUse.grandCompte) {
            this.grandCompteData = dataToUse.grandCompte;
          }
        } else {
          this.territories = {
            territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
            territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
            territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
            territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
          };
        }
        
      } catch (error) {
        console.error('Erreur lors de la récupération des données de production volume:', error);
        
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
          const errorData = error.response.data;
          const detail = errorData?.detail || errorData?.error || errorData?.message || '';
          
          if (detail.includes('Connection refused') || detail.includes('cannot connect to database')) {
            errorMessage = `⚠️ Erreur de connexion à la base de données Oracle`;
          } else {
            errorMessage = detail || `Erreur HTTP ${error.response.status}`;
          }
        } else if (error.request) {
          errorMessage = `⚠️ Impossible de se connecter au service Python`;
        } else {
          errorMessage = error.message || 'Erreur inconnue';
        }
        
        this.error = errorMessage;
        
        this.territories = {
          territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
          territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
          territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
          territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
        };
        this.grandCompteData = null;
      } finally {
        this.loading = false;
      }
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
    getCodeGestionDisplay(agency) {
      if (!agency) return '-';
      // Si l'agence a plusieurs codes gestion, afficher le premier ou un indicateur
      const codeGestion = agency.CODE_GESTION || agency.codeGestion || agency.CODE_GESTION_PRET || agency.codeGestionPret;
      return codeGestion || '-';
    },
    getChargeAffaireDisplay(agency) {
      if (!agency) return '-';
      // Si l'agence a plusieurs chargés d'affaire, afficher le premier ou un indicateur
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
  min-width: 1600px;
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
  background: #DC2626;
  font-weight: 600;
  color: white;
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
</style>
