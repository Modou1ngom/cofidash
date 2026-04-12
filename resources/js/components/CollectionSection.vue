<template>
  <div class="collection-section">
    <div class="section-header">
      <h2 class="section-title">Collecte- {{ getPeriodTitle() }}</h2>
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
            @change="handleDateChange"
            @input="handleDateChange"
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
    
    <!-- Résultat Global -->
    <div class="global-result-section">
      <div v-if="loading" class="loading-message">
        <p>🔄 Chargement des données ...</p>
       
      </div>
      <div v-if="errorMessage" class="error-message">
        <p>⚠️ {{ errorMessage }}</p>
      </div>
    </div>

    <!-- Tableaux hiérarchiques par niveaux - Scindés en Collecte et Solde -->
    
    <!-- Menu d'onglets pour basculer entre Collecte, Solde et Epargne -->
    <div class="tabs-menu">
      <button 
        :class="['tab-button', { active: activeTab === 'collecte' }]"
        @click="setActiveTab('collecte')"
      >
        📊 DOMICILIATION DE FLUX
      </button>
    <!-- 
    <button 
        :class="['tab-button', { active: activeTab === 'solde' }]"
        @click="setActiveTab('solde')"
      >
        💰 SOLDE
      </button>
    -->
      
     
    </div>
    
    <!-- Tableau COLLECTE -->
    <div v-if="activeTab === 'collecte'" class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>Agence</th>
              <th>code gestionnaire</th>
              <th>chargé d'affaire</th>
              <th>Exigible M-1</th>
              <th>MT Echeanche</th>
              <th>Objectif</th>
              <th>Collecte M</th>
              <th>TRO</th>
              <th>Collecte S1</th>
              <th>Collecte S2</th>
              <th>Collecte S3</th>
              <th>Collecte S4</th>
            </tr>
          </thead>
          <tbody>
            <!-- Message si aucune donnée -->
            <tr v-if="!loading && !errorMessage && Object.keys(filteredHierarchicalData.TERRITOIRE || {}).length === 0" class="no-data-row">
              <td colspan="12" style="text-align: center; padding: 40px; color: #666;">
                <p>Aucune donnée de collection disponible pour la période sélectionnée.</p>
                <p style="font-size: 12px; margin-top: 10px;">Vérifiez que l'API /api/oracle/data/collection retourne des données.</p>
              </td>
            </tr>
            
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
              <td><strong>{{ formatNumber(territoireTotal.exigibleM1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.mtEcheance) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.objectif) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.collecteM) }}</strong></td>
              <td><strong>{{ formatTroPercent(territoireTotal.tro) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.collecteS1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.collecteS2) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.collecteS3) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.collecteS4) }}</strong></td>
            </tr>

            <!-- Territoires dans TERRITOIRE -->
            <template v-if="expandedSections.TERRITOIRE">
              <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
                <!-- Exclure grand_compte de la boucle car il est affiché séparément -->
                <template v-if="territoryKey !== 'grand_compte'">
                <tr class="level-2-row" @click="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                  <td class="level-2">
                    <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_${territoryKey}`)">
                      {{ expandedSections[`TERRITOIRE_${territoryKey}`] ? '−' : '+' }}
                    </button>
                    {{ territory.name }}
                  </td>
                  <td><strong>-</strong></td>
                  <td><strong>-</strong></td>
                  <td><strong>{{ formatNumber(territory.totals.exigibleM1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.mtEcheance) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.objectif) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.collecteM) }}</strong></td>
                  <td><strong>{{ formatTroPercent(territory.totals.tro) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.collecteS1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.collecteS2) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.collecteS3) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.collecteS4) }}</strong></td>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_${territoryKey}`]">
                  <template v-for="(agency, index) in (territory.agencies || [])" :key="getAgencyKey(agency, index)">
                    <!-- Ligne principale de l'agence avec bouton d'expansion -->
                    <tr 
                      class="level-3-row"
                      @click="toggleAgencyExpand(agency, `TERRITOIRE_${territoryKey}_${getAgencyKey(agency, index)}`)"
                    >
                      <td class="level-3">
                        <button 
                          class="expand-btn" 
                          @click.stop="toggleAgencyExpand(agency, `TERRITOIRE_${territoryKey}_${getAgencyKey(agency, index)}`)"
                          v-if="hasChargeAffaireDetails(agency)"
                        >
                          {{ expandedSections[`TERRITOIRE_${territoryKey}_${getAgencyKey(agency, index)}`] ? '−' : '+' }}
                        </button>
                        {{ agency.name || agency.AGENCE || getAgencyName(agency) }}
                      </td>
                      <td>{{ getCodeGestionDisplay(agency) }}</td>
                      <td>{{ getChargeAffaireDisplay(agency) }}</td>
                      <td>{{ formatNumber(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'exigibleM1')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'mtEcheance')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'objectif')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'collecteM')) }}</td>
                      <td>{{ formatTroPercent(getCollecteTroForAgencyName(agency.name || agency.AGENCE || getAgencyName(agency))) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'collecteS1')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'collecteS2')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'collecteS3')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'collecteS4')) }}</td>
                    </tr>
                    <!-- Afficher tous les chargés d'affaire pour cette agence quand elle est expandée -->
                    <template v-if="expandedSections[`TERRITOIRE_${territoryKey}_${getAgencyKey(agency, index)}`]">
                      <tr 
                        v-for="(chargeDetail, chargeIndex) in getCachedChargeAffaireLines(`TERRITOIRE_${territoryKey}_${getAgencyKey(agency, index)}`)" 
                        :key="`charge-${chargeIndex}`"
                        class="level-4-row charge-detail-row"
                      >
                        <td class="level-4">
                          {{ agency.BRANCH_CODE || agency.branch_code || '-' }}
                        </td>
                        <td>{{ chargeDetail.codeGestion || chargeDetail.CODE_GESTION || '-' }}</td>
                        <td>{{ chargeDetail.chargeAffaire || chargeDetail.CHARGE_AFFAIRE || '-' }}</td>
                        <td>{{ formatNumber(chargeDetail.exigibleM1 || chargeDetail.EXIGIBLE_M1 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.mtEcheance || chargeDetail.MT_ECHEANCE || 0) }}</td>
                        <td>-</td>
                        <td>{{ formatCurrency(chargeDetail.collecteM || chargeDetail.COLLECTE_M || 0) }}</td>
                        <td>-</td>
                        <td>{{ formatCurrency(chargeDetail.collecteS1 || chargeDetail.COLLECTE_S1 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.collecteS2 || chargeDetail.COLLECTE_S2 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.collecteS3 || chargeDetail.COLLECTE_S3 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.collecteS4 || chargeDetail.COLLECTE_S4 || 0) }}</td>
                      </tr>
                      <tr v-if="getCachedChargeAffaireLines(`TERRITOIRE_${territoryKey}_${getAgencyKey(agency, index)}`).length === 0" class="level-4-row">
                        <td colspan="12" style="text-align: center; padding: 10px; color: #666;">
                          Aucun chargé d'affaire trouvé pour cette agence
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
                </template>
              </template>
            </template>

            <!-- GRAND COMPTE -->
            <tr v-if="grandCompte" class="grand-compte-row">
              <td>{{ grandCompte.BRANCH_CODE || grandCompte.branch_code || '526' }}</td>
              <td>{{ getCodeGestionDisplay(grandCompte) }}</td>
              <td>{{ getChargeAffaireDisplay(grandCompte) }}</td>
              <td>{{ formatNumber(grandCompte.exigibleM1 || grandCompte.EXIGIBLE_M1 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.mtEcheance || grandCompte.MT_ECHEANCE || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.objectif || grandCompte.OBJECTIF || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.collecteM || grandCompte.COLLECTE_M || 0) }}</td>
              <td>{{ formatTroPercent(getCollecteTroFromValues(grandCompte.collecteM || grandCompte.COLLECTE_M, grandCompte.objectif || grandCompte.OBJECTIF)) }}</td>
              <td>{{ formatCurrency(grandCompte.collecteS1 || grandCompte.COLLECTE_S1 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.collecteS2 || grandCompte.COLLECTE_S2 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.collecteS3 || grandCompte.COLLECTE_S3 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.collecteS4 || grandCompte.COLLECTE_S4 || 0) }}</td>
            </tr>

            <!-- Ligne TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(getGrandTotal('exigibleM1')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('mtEcheance')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('objectif')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('collecteM')) }}</strong></td>
              <td><strong>{{ formatTroPercent(getGrandTotalCollecteTro()) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('collecteS1')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('collecteS2')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('collecteS3')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('collecteS4')) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Tableau SOLDE -->
    <div v-if="activeTab === 'solde'" class="zone-agencies-section">
      <div class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th>Agence</th>
              <th>code gestionnaire</th>
              <th>chargé d'affaire</th>
              <th>Exigible M-1</th>
              <th>MT Echeanche</th>
              <th>SLD M</th>
              <th>SLD S1</th>
              <th>SLD S2</th>
              <th>SLD S3</th>
              <th>SLD S4</th>
            </tr>
          </thead>
          <tbody>
            <!-- Message si aucune donnée -->
            <tr v-if="!loading && !errorMessage && Object.keys(filteredHierarchicalData.TERRITOIRE || {}).length === 0" class="no-data-row">
              <td colspan="10" style="text-align: center; padding: 40px; color: #666;">
                <p>Aucune donnée de solde disponible pour la période sélectionnée.</p>
              </td>
            </tr>
            
            <!-- TERRITOIRE -->
            <tr v-if="Object.keys(filteredHierarchicalData.TERRITOIRE || {}).length > 0" class="level-1-row" @click="toggleExpand('TERRITOIRE_SOLDE')">
              <td class="level-1">
                <button class="expand-btn" @click.stop="toggleExpand('TERRITOIRE_SOLDE')">
                  {{ expandedSections['TERRITOIRE_SOLDE'] ? '−' : '+' }}
                </button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(territoireTotal.exigibleM1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.mtEcheance) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.sldM) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.sldS1) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.sldS2) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.sldS3) }}</strong></td>
              <td><strong>{{ formatCurrency(territoireTotal.sldS4) }}</strong></td>
            </tr>

            <!-- Territoires dans TERRITOIRE -->
            <template v-if="expandedSections['TERRITOIRE_SOLDE']">
              <template v-for="(territory, territoryKey) in filteredHierarchicalData.TERRITOIRE" :key="territoryKey">
                <template v-if="territoryKey !== 'grand_compte'">
                <tr class="level-2-row" @click="toggleExpand(`TERRITOIRE_SOLDE_${territoryKey}`)">
                  <td class="level-2">
                    <button class="expand-btn" @click.stop="toggleExpand(`TERRITOIRE_SOLDE_${territoryKey}`)">
                      {{ expandedSections[`TERRITOIRE_SOLDE_${territoryKey}`] ? '−' : '+' }}
                    </button>
                    {{ territory.name }}
                  </td>
                  <td><strong>-</strong></td>
                  <td><strong>-</strong></td>
                  <td><strong>{{ formatNumber(territory.totals.exigibleM1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.mtEcheance) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.sldM) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.sldS1) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.sldS2) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.sldS3) }}</strong></td>
                  <td><strong>{{ formatCurrency(territory.totals.sldS4) }}</strong></td>
                </tr>
                <!-- Agences dans chaque territoire -->
                <template v-if="expandedSections[`TERRITOIRE_SOLDE_${territoryKey}`]">
                  <template v-for="(agency, index) in (territory.agencies || [])" :key="getAgencyKey(agency, index)">
                    <!-- Ligne principale de l'agence avec bouton d'expansion -->
                    <tr 
                      class="level-3-row"
                      @click="toggleAgencyExpand(agency, `TERRITOIRE_SOLDE_${territoryKey}_${getAgencyKey(agency, index)}`)"
                    >
                      <td class="level-3">
                        <button 
                          class="expand-btn" 
                          @click.stop="toggleAgencyExpand(agency, `TERRITOIRE_SOLDE_${territoryKey}_${getAgencyKey(agency, index)}`)"
                          v-if="hasChargeAffaireDetails(agency)"
                        >
                          {{ expandedSections[`TERRITOIRE_SOLDE_${territoryKey}_${getAgencyKey(agency, index)}`] ? '−' : '+' }}
                        </button>
                        {{ agency.name || agency.AGENCE || getAgencyName(agency) }}
                      </td>
                      <td>{{ getCodeGestionDisplay(agency) }}</td>
                      <td>{{ getChargeAffaireDisplay(agency) }}</td>
                      <td>{{ formatNumber(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'exigibleM1')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'mtEcheance')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'sldM')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'sldS1')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'sldS2')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'sldS3')) }}</td>
                      <td>{{ formatCurrency(getAgencyTotalByName(agency.name || agency.AGENCE || getAgencyName(agency), 'sldS4')) }}</td>
                    </tr>
                    <!-- Afficher tous les chargés d'affaire pour cette agence quand elle est expandée -->
                    <template v-if="expandedSections[`TERRITOIRE_SOLDE_${territoryKey}_${getAgencyKey(agency, index)}`]">
                      <tr 
                        v-for="(chargeDetail, chargeIndex) in getChargeAffaireDetailsByBranchCode(agency.BRANCH_CODE || agency.branch_code)" 
                        :key="`charge-${chargeIndex}`"
                        class="level-4-row charge-detail-row"
                      >
                        <td class="level-4">
                          {{ agency.BRANCH_CODE || agency.branch_code || '-' }}
                        </td>
                        <td>{{ chargeDetail.codeGestion || chargeDetail.CODE_GESTION || '-' }}</td>
                        <td>{{ chargeDetail.chargeAffaire || chargeDetail.CHARGE_AFFAIRE || '-' }}</td>
                        <td>{{ formatNumber(chargeDetail.exigibleM1 || chargeDetail.EXIGIBLE_M1 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.mtEcheance || chargeDetail.MT_ECHEANCE || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.sldM || chargeDetail.SLD_M || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.sldS1 || chargeDetail.SLD_S1 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.sldS2 || chargeDetail.SLD_S2 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.sldS3 || chargeDetail.SLD_S3 || 0) }}</td>
                        <td>{{ formatCurrency(chargeDetail.sldS4 || chargeDetail.SLD_S4 || 0) }}</td>
                      </tr>
                      <tr v-if="getChargeAffaireDetailsByBranchCode(agency.BRANCH_CODE || agency.branch_code).length === 0" class="level-4-row">
                        <td colspan="10" style="text-align: center; padding: 10px; color: #666;">
                          Aucun chargé d'affaire trouvé pour cette agence
                        </td>
                      </tr>
                    </template>
                  </template>
                </template>
                </template>
              </template>
            </template>

            <!-- GRAND COMPTE -->
            <tr v-if="grandCompte" class="grand-compte-row">
              <td>{{ grandCompte.BRANCH_CODE || grandCompte.branch_code || '526' }}</td>
              <td>{{ getCodeGestionDisplay(grandCompte) }}</td>
              <td>{{ getChargeAffaireDisplay(grandCompte) }}</td>
              <td>{{ formatNumber(grandCompte.exigibleM1 || grandCompte.EXIGIBLE_M1 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.mtEcheance || grandCompte.MT_ECHEANCE || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.sldM || grandCompte.SLD_M || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.sldS1 || grandCompte.SLD_S1 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.sldS2 || grandCompte.SLD_S2 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.sldS3 || grandCompte.SLD_S3 || 0) }}</td>
              <td>{{ formatCurrency(grandCompte.sldS4 || grandCompte.SLD_S4 || 0) }}</td>
            </tr>

            <!-- Ligne TOTAL -->
            <tr class="total-row">
              <td><strong>TOTAL</strong></td>
              <td><strong>-</strong></td>
              <td><strong>-</strong></td>
              <td><strong>{{ formatNumber(getGrandTotal('exigibleM1')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('mtEcheance')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('sldM')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('sldS1')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('sldS2')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('sldS3')) }}</strong></td>
              <td><strong>{{ formatCurrency(getGrandTotal('sldS4')) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>


    <!-- Tableau EPARGNE -->
    <div v-if="activeTab === 'epargne'" class="zone-agencies-section">
      <div class="table-container">
        <div style="text-align: center; padding: 40px; color: #666;">
          <p>💵 Page Epargne en cours de développement</p>
          <p style="font-size: 12px; margin-top: 10px;">Cette fonctionnalité sera bientôt disponible.</p>
        </div>
      </div>
    </div>

    <!-- Section Graphique d'évolution -->
    <div class="chart-evolution-section" v-if="hasChartData">
      <div class="chart-header">
        <div class="chart-title-section">
          <h3 class="chart-section-title">{{ chartTitle }}</h3>
          <div class="breadcrumb" v-if="activeLevel.type !== 'total'">
            <span class="breadcrumb-item" @click="resetToTotal()">Total</span>
            <span class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item" v-if="activeLevel.type === 'category' || activeLevel.type === 'zone' || activeLevel.type === 'agency'">
              {{ activeLevel.category }}
            </span>
            <span v-if="activeLevel.type === 'zone' || activeLevel.type === 'agency'" class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item" v-if="activeLevel.type === 'zone' || activeLevel.type === 'agency'">
              {{ getTerritoryName(activeLevel.zone) }}
            </span>
            <span v-if="activeLevel.type === 'agency'" class="breadcrumb-separator">›</span>
            <span class="breadcrumb-item active" v-if="activeLevel.type === 'agency'">
              {{ activeLevel.name }}
            </span>
          </div>
        </div>
        <div class="chart-actions">
          <button @click="exportChart('png')" class="export-btn" title="Exporter en PNG">
            📷 PNG
          </button>
          <button @click="exportChart('pdf')" class="export-btn" title="Exporter en PDF">
            📄 PDF
          </button>
          <button @click="exportChart('csv')" class="export-btn" title="Exporter les données en CSV">
            📊 CSV
          </button>
        </div>
      </div>
      
      <!-- Menu pour basculer entre Graphique et Performance -->
      <div class="chart-view-tabs">
        <button 
          :class="['chart-view-tab', { active: chartViewMode === 'graph' }]"
          @click="chartViewMode = 'graph'"
        >
          📈 Graphique
        </button>
        <button 
          :class="['chart-view-tab', { active: chartViewMode === 'performance' }]"
          @click="chartViewMode = 'performance'"
        >
          🏆 Performance
        </button>
      </div>
      
      <!-- Vue Graphique -->
      <div v-if="chartViewMode === 'graph'">
      <div class="chart-tabs">
        <button 
          :class="['chart-tab', { active: selectedChartType === 'line' }]"
          @click="selectedChartType = 'line'"
          title="Graphique en ligne"
        >
          📈 Ligne
        </button>
        <button 
          :class="['chart-tab', { active: selectedChartType === 'bar' }]"
          @click="selectedChartType = 'bar'"
          title="Graphique en barres"
        >
          📊 Barres
        </button>
        <button 
          :class="['chart-tab', { active: selectedChartType === 'area' }]"
          @click="selectedChartType = 'area'"
          title="Graphique en aires"
        >
          📉 Aires
        </button>
        <button 
          :class="['chart-tab', { active: selectedChartType === 'pie' }]"
          @click="selectedChartType = 'pie'"
          title="Graphique circulaire"
        >
          🥧 Circulaire
        </button>
      </div>
      
      <!-- Sélecteur de données -->
      <div class="data-type-selector">
        <label>
          <input 
            type="radio" 
            value="collection" 
            v-model="selectedDataType"
            @change="updateChart"
          />
          Collecte S
        </label>
      </div>
      
      <div class="chart-wrapper-container">
        <PythonChart
          :key="`chart-${selectedChartType}-${selectedDataType}-${activeLevel.type}-${activeLevel.category || ''}-${activeLevel.zone || ''}-${activeLevel.name || ''}`"
          :chartType="selectedChartType"
          :chartData="currentChartData"
          :height="600"
          ref="chartComponent"
        />
      </div>
      </div>
      
      <!-- Vue Performance -->
      <div v-if="chartViewMode === 'performance'">
        <AgencyPerformanceSection 
          :dataType="'collection'" 
          :tableData="performanceTableData"
        />
      </div>
    </div>
    <div v-else class="chart-evolution-section">
      <h3 class="chart-section-title">Évolution de la Collection</h3>
      <div class="chart-wrapper-container" style="display: flex; align-items: center; justify-content: center; color: #999;">
        <p>Chargement des données...</p>
      </div>
    </div>
  </div>
</template>

<script>
import KPICard from './KPICard.vue';
import PythonChart from './charts/PythonChart.vue';
import AgencyPerformanceSection from './AgencyPerformanceSection.vue';
import { ProfileManager, PERMISSIONS } from '../utils/profiles.js';

export default {
  name: 'CollectionSection',
  emits: ['tab-changed'],
  components: {
    KPICard,
    PythonChart,
    AgencyPerformanceSection
  },
  provide() {
    return {
      collectionTab: () => this.activeTab,
      updateCollectionTab: (tab) => {
        this.setActiveTab(tab);
      }
    };
  },
  computed: {
    performanceTableData() {
      // Propriété calculée pour éviter de recréer l'objet à chaque rendu
      if (this.hierarchicalDataFromBackend) {
        return {
          hierarchicalData: this.hierarchicalDataFromBackend,
          chargeAffaireDetails: this.chargeAffaireDetails
        };
      }
      return null;
    },
    canEditObjectives() {
      return ProfileManager.canEditObjectives();
    },
    canManageFinancial() {
      return ProfileManager.canManageFinancial();
    },
    isAdmin() {
      return ProfileManager.isAdmin();
    },
    canViewOnly() {
      return ProfileManager.getCurrentProfile() === 'EXPLOITATIONS';
    },
    kpiLabels() {
      if (this.selectedPeriod === 'week') {
        return {
          current: 'Résultat Global (Semaine)',
          previous: 'Résultat Global (Semaine-1)',
          difference: 'Différence'
        };
      } else if (this.selectedPeriod === 'month') {
        return {
          current: 'Résultat Global (Mois)',
          previous: 'Résultat Global (Mois-1)',
          difference: 'Différence'
        };
      } else if (this.selectedPeriod === 'year') {
        return {
          current: 'Résultat Global (Année)',
          previous: 'Résultat Global (Année-1)',
          difference: 'Différence'
        };
      }
      return {
        current: 'Résultat Global (Mois)',
        previous: 'Résultat Global (Mois-1)',
        difference: 'Différence'
      };
    },
    computedDifference() {
      return this.globalResult.mois - this.globalResult.mois1;
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
    },
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
          if (data.TERRITOIRE && typeof data.TERRITOIRE === 'object' && data.TERRITOIRE !== null) {
            Object.keys(data.TERRITOIRE).forEach(key => {
              if (data.TERRITOIRE[key]) {
                const agencies = data.TERRITOIRE[key].agencies || data.TERRITOIRE[key].data || [];
                
                // Obtenir les agences par défaut pour ce territoire
                const defaultAgencies = this.getDefaultAgenciesForTerritory(key);
                
                // Filtrer les agences du backend
                const filtered = this.filterAgencies(agencies);
                
                // Fusionner avec les agences par défaut
                const merged = this.mergeAgenciesWithDefaults(filtered, defaultAgencies);
                
                // Vérifier que toutes les agences par défaut sont présentes
                const mergedNames = merged.map(a => this.getAgencyName(a).toUpperCase());
                const missingAgencies = defaultAgencies.filter(defaultAgency => {
                  const defaultName = this.getAgencyName(defaultAgency).toUpperCase();
                  return !mergedNames.some(name => name.includes(defaultName) || defaultName.includes(name));
                });
                // Agences par défaut manquantes ignorées silencieusement
                
                data.TERRITOIRE[key].agencies = merged;
                if (!data.TERRITOIRE[key].totals) {
                  data.TERRITOIRE[key].totals = this.calculateZoneTotals(data.TERRITOIRE[key].agencies);
                }
              }
            });
          }
          return data;
        } catch (e) {
          // Erreur silencieuse lors du traitement des données hiérarchiques
        }
      }
      
      if (!this.territories || typeof this.territories !== 'object') {
        return {
          TERRITOIRE: {}
        };
      }
      
      // Support des anciennes et nouvelles clés pour compatibilité
      const dakarVilleData = this.territories.dakar_centre_ville || this.territories.territoire_dakar_ville || {};
      const dakarBanlieueData = this.territories.dakar_banlieue || this.territories.territoire_dakar_banlieue || {};
      const provinceCentreSudData = this.territories.province_centre_sud || this.territories.territoire_province_centre_sud || {};
      const provinceNordData = this.territories.province_nord || this.territories.territoire_province_nord || {};
      
      // Filtrer les agences du backend
      const filteredDakarVille = this.filterAgencies(dakarVilleData.agencies || []);
      const filteredDakarBanlieue = this.filterAgencies(dakarBanlieueData.agencies || []);
      const filteredProvinceCentreSud = this.filterAgencies(provinceCentreSudData.agencies || []);
      const filteredProvinceNord = this.filterAgencies(provinceNordData.agencies || []);
      const filteredGrandCompte = this.filterAgencies((this.territories.grand_compte && this.territories.grand_compte.agencies) || []);
      const filteredServicePoints = this.filterAgencies([]);
      
      let mergedDakarVille = this.mergeAgenciesWithDefaults(filteredDakarVille, this.getDefaultAgenciesForTerritory('dakar_centre_ville'));
      const mergedServicePoints = this.mergeAgenciesWithDefaults(filteredServicePoints, this.getDefaultServicePoints());
      mergedDakarVille = this.mergeAgenciesWithDefaults(mergedDakarVille, mergedServicePoints);
      const mergedDakarBanlieue = this.mergeAgenciesWithDefaults(filteredDakarBanlieue, this.getDefaultAgenciesForTerritory('dakar_banlieue'));
      const mergedProvinceCentreSud = this.mergeAgenciesWithDefaults(filteredProvinceCentreSud, this.getDefaultAgenciesForTerritory('province_centre_sud'));
      const mergedProvinceNord = this.mergeAgenciesWithDefaults(filteredProvinceNord, this.getDefaultAgenciesForTerritory('province_nord'));
      
      const data = {
        TERRITOIRE: {
          dakar_centre_ville: {
            name: dakarVilleData.name || 'DAKAR CENTRE VILLE',
            agencies: mergedDakarVille,
            totals: this.calculateZoneTotals(mergedDakarVille)
          },
          dakar_banlieue: {
            name: dakarBanlieueData.name || 'DAKAR BANLIEUE',
            agencies: mergedDakarBanlieue,
            totals: this.calculateZoneTotals(mergedDakarBanlieue)
          },
          province_centre_sud: {
            name: provinceCentreSudData.name || 'PROVINCE CENTRE SUD',
            agencies: mergedProvinceCentreSud,
            totals: this.calculateZoneTotals(mergedProvinceCentreSud)
          },
          province_nord: {
            name: provinceNordData.name || 'PROVINCE NORD',
            agencies: mergedProvinceNord,
            totals: this.calculateZoneTotals(mergedProvinceNord)
          },
          grand_compte: {
            name: (this.territories.grand_compte && this.territories.grand_compte.name) || 'GRAND COMPTE',
            agencies: filteredGrandCompte,
            totals: this.calculateZoneTotals(filteredGrandCompte)
          }
        }
      };
      
      return data;
    },
    filteredHierarchicalData() {
      if (!this.hierarchicalData || typeof this.hierarchicalData !== 'object' || this.hierarchicalData === null) {
        return {
          TERRITOIRE: {}
        };
      }
      
      if (!this.selectedZone) {
        return this.hierarchicalData;
      }
      
      const filtered = {
        TERRITOIRE: {}
      };
      
      if (this.hierarchicalData.TERRITOIRE && 
          typeof this.hierarchicalData.TERRITOIRE === 'object' && 
          this.hierarchicalData.TERRITOIRE !== null &&
          !Array.isArray(this.hierarchicalData.TERRITOIRE) &&
          this.hierarchicalData.TERRITOIRE[this.selectedZone]) {
        filtered.TERRITOIRE[this.selectedZone] = this.hierarchicalData.TERRITOIRE[this.selectedZone];
      }
      
      return filtered;
    },
    territoireTotal() {
      // Support des anciennes et nouvelles clés pour compatibilité
      const dakarVilleData = this.territories.dakar_centre_ville || this.territories.territoire_dakar_ville || {};
      const dakarBanlieueData = this.territories.dakar_banlieue || this.territories.territoire_dakar_banlieue || {};
      const provinceCentreSudData = this.territories.province_centre_sud || this.territories.territoire_province_centre_sud || {};
      const provinceNordData = this.territories.province_nord || this.territories.territoire_province_nord || {};
      
      const t1 = this.calculateZoneTotals(dakarVilleData.agencies || []);
      const t2 = this.calculateZoneTotals(dakarBanlieueData.agencies || []);
      const t3 = this.calculateZoneTotals(provinceCentreSudData.agencies || []);
      const t4 = this.calculateZoneTotals(provinceNordData.agencies || []);
      
      const sumObjectif = t1.objectif + t2.objectif + t3.objectif + t4.objectif;
      const sumCollecteM = t1.collecteM + t2.collecteM + t3.collecteM + t4.collecteM;
      
      return {
        exigibleM1: t1.exigibleM1 + t2.exigibleM1 + t3.exigibleM1 + t4.exigibleM1,
        mtEcheance: t1.mtEcheance + t2.mtEcheance + t3.mtEcheance + t4.mtEcheance,
        m: t1.m + t2.m + t3.m + t4.m,
        sldM: t1.sldM + t2.sldM + t3.sldM + t4.sldM,
        collecteM: sumCollecteM,
        objectif: sumObjectif,
        tro: sumObjectif > 0 ? (sumCollecteM / sumObjectif) * 100 : null,
        exigibleS1: t1.exigibleS1 + t2.exigibleS1 + t3.exigibleS1 + t4.exigibleS1,
        mtEcheanceS1: t1.mtEcheanceS1 + t2.mtEcheanceS1 + t3.mtEcheanceS1 + t4.mtEcheanceS1,
        mS1: t1.mS1 + t2.mS1 + t3.mS1 + t4.mS1,
        sldS1: t1.sldS1 + t2.sldS1 + t3.sldS1 + t4.sldS1,
        collecteS1: t1.collecteS1 + t2.collecteS1 + t3.collecteS1 + t4.collecteS1,
        collecteS2: t1.collecteS2 + t2.collecteS2 + t3.collecteS2 + t4.collecteS2,
        sldS2: t1.sldS2 + t2.sldS2 + t3.sldS2 + t4.sldS2,
        collecteS3: t1.collecteS3 + t2.collecteS3 + t3.collecteS3 + t4.collecteS3,
        sldS3: t1.sldS3 + t2.sldS3 + t3.sldS3 + t4.sldS3,
        collecteS4: t1.collecteS4 + t2.collecteS4 + t3.collecteS4 + t4.collecteS4,
        sldS4: t1.sldS4 + t2.sldS4 + t3.sldS4 + t4.sldS4
      };
    },
    grandCompte() {
      // Récupérer le grand compte depuis territories ou hierarchicalData
      const grandCompteData = this.territories?.grand_compte || 
                              this.hierarchicalData?.TERRITOIRE?.grand_compte;
      
      if (!grandCompteData) {
        return null;
      }
      
      // Si le grand compte a des agences, prendre la première
      if (grandCompteData.agencies && grandCompteData.agencies.length > 0) {
        return grandCompteData.agencies[0];
      }
      
      // Sinon, utiliser les totaux du grand compte
      if (grandCompteData.totals) {
        return {
          AGENCE: 'GRAND COMPTE',
          name: 'GRAND COMPTE',
          BRANCH_CODE: '526',
          branch_code: '526',
          CODE_GESTION: '-',
          CHARGE_AFFAIRE: '-',
          EXIGIBLE_M1: grandCompteData.totals.exigibleM1 || 0,
          MT_ECHEANCE: grandCompteData.totals.mtEcheance || 0,
          M: grandCompteData.totals.m || 0,
          SLD_M: grandCompteData.totals.sldM || 0,
          COLLECTE_M: grandCompteData.totals.collecteM || 0,
          EXIGIBLE_S1: grandCompteData.totals.exigibleS1 || 0,
          MT_ECHEANCE_S1: grandCompteData.totals.mtEcheanceS1 || 0,
          M_S1: grandCompteData.totals.mS1 || 0,
          SLD_S1: grandCompteData.totals.sldS1 || 0,
          COLLECTE_S1: grandCompteData.totals.collecteS1 || 0
        };
      }
      
      return null;
    },
    chartLabels() {
      // Afficher les labels S1, S2, S3, S4 pour les volumes collectés
      return ['S1', 'S2', 'S3', 'S4'];
    },
    hasChartData() {
      // Vérifier qu'on a des labels et des données, et qu'ils correspondent (4 valeurs: S1, S2, S3, S4)
      return this.chartLabels.length > 0 && 
             this.chartCurrentData.length > 0 && 
             this.chartCurrentData.length === this.chartLabels.length &&
             this.chartCurrentData.length === 4;
    },
    activeLevel() {
      if (this.selectedAgency) {
        return {
          type: 'agency',
          category: this.selectedAgency.category,
          zone: this.selectedAgency.zone,
          name: this.selectedAgency.name
        };
      }
      
      for (const key in this.expandedSections) {
        if (key.startsWith('TERRITOIRE_') && this.expandedSections[key]) {
          const zoneKey = key.replace('TERRITOIRE_', '');
          return {
            type: 'zone',
            category: 'TERRITOIRE',
            zone: zoneKey,
            name: this.hierarchicalData.TERRITOIRE[zoneKey]?.name || `Zone ${zoneKey}`
          };
        }
      }
      
      if (this.expandedSections.TERRITOIRE) {
        return {
          type: 'category',
          category: 'TERRITOIRE',
          name: 'TERRITOIRE'
        };
      }
      
      return {
        type: 'total',
        name: 'Total'
      };
    },
    chartTitle() {
      const level = this.activeLevel;
      return `Évolution - ${level.name}`;
    },
    getValueByDataType(data, totals = null) {
      // Helper pour obtenir la valeur selon le type de données sélectionné
      switch (this.selectedDataType) {
        case 'recouvrement':
          return data?.collecteM || data?.COLLECTE_M || totals?.collecteM || 0;
        case 'collection':
          return data?.collecteS1 || data?.COLLECTE_S1 || totals?.collecteS1 || 0;
        case 'epargne':
          return data?.epargne || data?.EPARGNE || totals?.epargne || totals?.EPARGNE || 0;
        default:
          return 0;
      }
    },
    chartCurrentData() {
      const level = this.activeLevel;
      let data = [];
      
      // Fonction helper pour normaliser une valeur en nombre
      const normalizeValue = (value) => {
        const num = parseFloat(value);
        return isNaN(num) || num === null || num === undefined ? 0 : num;
      };
      
      // Récupérer les vraies valeurs S1, S2, S3, S4 du tableau (sans M)
      if (level.type === 'agency') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        const agency = zoneData?.agencies?.find(a => a.name === level.name);
        if (agency) {
          data = [
            normalizeValue(agency.collecteS1 || agency.COLLECTE_S1),
            normalizeValue(agency.collecteS2 || agency.COLLECTE_S2),
            normalizeValue(agency.collecteS3 || agency.COLLECTE_S3),
            normalizeValue(agency.collecteS4 || agency.COLLECTE_S4)
          ];
        }
      } else if (level.type === 'zone') {
        const zoneData = this.hierarchicalData[level.category][level.zone];
        if (zoneData?.totals) {
          data = [
            normalizeValue(zoneData.totals.collecteS1),
            normalizeValue(zoneData.totals.collecteS2),
            normalizeValue(zoneData.totals.collecteS3),
            normalizeValue(zoneData.totals.collecteS4)
          ];
        }
      } else if (level.type === 'category') {
        if (level.category === 'TERRITOIRE') {
          data = [
            normalizeValue(this.territoireTotal.collecteS1),
            normalizeValue(this.territoireTotal.collecteS2),
            normalizeValue(this.territoireTotal.collecteS3),
            normalizeValue(this.territoireTotal.collecteS4)
          ];
        } else {
          data = [
            normalizeValue(this.getGrandTotal('collecteS1')),
            normalizeValue(this.getGrandTotal('collecteS2')),
            normalizeValue(this.getGrandTotal('collecteS3')),
            normalizeValue(this.getGrandTotal('collecteS4'))
          ];
        }
      } else {
        // Total général
        data = [
          normalizeValue(this.getGrandTotal('collecteS1')),
          normalizeValue(this.getGrandTotal('collecteS2')),
          normalizeValue(this.getGrandTotal('collecteS3')),
          normalizeValue(this.getGrandTotal('collecteS4'))
        ];
      }
      
      // Normaliser toutes les valeurs pour s'assurer qu'elles sont des nombres
      return data.map(v => normalizeValue(v));
    },
    currentChartData() {
      const labels = this.chartLabels;
      const current = this.chartCurrentData;
      const title = `${this.chartTitle} - Volume Collecté`;
      const ylabel = 'Volume Collecté (FCFA)';
      
      // S'assurer que current est un tableau de nombres valides
      const normalizedCurrent = current.map(v => {
        const num = parseFloat(v);
        return isNaN(num) || num === null || num === undefined ? 0 : num;
      });
      
      if (this.selectedChartType === 'bar') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title,
          xlabel: 'Période',
          ylabel: ylabel
        };
      } else if (this.selectedChartType === 'area') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title,
          ylabel: ylabel
        };
      } else if (this.selectedChartType === 'pie') {
        return {
          labels: labels,
          values: normalizedCurrent,
          title: title
        };
      } else {
        // Pour les graphiques en ligne, on affiche seulement les valeurs actuelles
        // Pas besoin de previous car on affiche M, S1, S2, S3, S4
        return {
          labels: labels,
          current: normalizedCurrent,
          previous: normalizedCurrent, // Même valeur pour éviter les erreurs
          title: title,
          ylabel: ylabel
        };
      }
    },
    updateChart() {
      this.$nextTick(() => {});
    },
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
      loading: false,
      errorMessage: null,
      selectedZone: null,
      selectedPeriod: 'month',
      activeTab: 'collecte', // 'collecte' ou 'solde'
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
        'TERRITOIRE_territoire_province_nord': false,
        'TERRITOIRE_SOLDE': false
      },
      hierarchicalDataFromBackend: null,
      chargeAffaireDetails: {},  // Détails par chargé d'affaire pour chaque agence
      chargeAffaireDetailsCache: new Map(),  // Cache pour les résultats par branchCode
      expandedAgencyLines: {},  // Cache pour les lignes calculées par sectionKey
      tabDataCache: {
        collecte: null,
        solde: null
      },  // Cache des données par onglet
      cacheKey: null,  // Clé de cache basée sur les paramètres de filtrage
      selectedAgency: null,
      selectedChartType: 'line',
      selectedDataType: 'collection',
      chartViewMode: 'graph', // 'graph' ou 'performance'
      months: [
        'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
        'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
      ],
      globalResult: {
        mois: 0,
        mois1: 0,
        evolution: 0
      },
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
    }
  },
  props: {
    selectedZoneProp: {
      type: String,
      default: null
    }
  },
  mounted() {
    this.fetchDataFromOracle();
  },
  watch: {
    activeTab(newVal) {
      // Émettre l'événement quand l'onglet change
      this.$emit('tab-changed', newVal);
      // Utiliser le cache si disponible, sinon charger les données
      if (newVal === 'collecte' || newVal === 'solde') {
        const currentCacheKey = this.generateCacheKey();
        const cachedData = this.tabDataCache[newVal];
        
        // Si les données sont en cache avec la même clé, les utiliser
        if (cachedData && cachedData.cacheKey === currentCacheKey) {
          this.hierarchicalDataFromBackend = cachedData.hierarchicalData;
          this.chargeAffaireDetails = cachedData.chargeAffaireDetails || {};
          this.territories = cachedData.territories || {};
        } else {
          // Sinon, charger les données
          this.loadDataForPeriod();
        }
      }
    },
    selectedZoneProp(newVal) {
      this.selectedZone = newVal;
      this.fetchDataFromOracle();
    },
    selectedPeriod(newVal) {
      if (newVal === 'week' && !this.selectedDate) {
        const now = new Date();
        const year = now.getFullYear();
        const month = String(now.getMonth() + 1).padStart(2, '0');
        const day = String(now.getDate()).padStart(2, '0');
        this.selectedDate = `${year}-${month}-${day}`;
        this.updateWeekFromDate();
      }
      this.loadDataForPeriod();
    },
    selectedDate(newVal, oldVal) {
      this.updateWeekFromDate();
      this.loadDataForPeriod();
    },
    selectedWeek() {
      this.loadDataForPeriod();
    },
    selectedMonth(newVal, oldVal) {
      if (newVal !== oldVal && oldVal !== undefined) {
        this.loadDataForPeriod();
      }
    },
    selectedYear(newVal, oldVal) {
      if (newVal !== oldVal && oldVal !== undefined) {
        this.loadDataForPeriod();
      }
    }
  },
  methods: {
    setActiveTab(tab) {
      this.activeTab = tab;
      this.$emit('tab-changed', tab);
    },
    getTerritoryName(zone) {
      const territoryMap = {
        'territoire_dakar_ville': 'TERRITOIRE DAKAR VILLE',
        'territoire_dakar_banlieue': 'TERRITOIRE DAKAR BANLIEUE',
        'territoire_province_centre_sud': 'TERRITOIRE PROVINCE CENTRE-SUD',
        'territoire_province_nord': 'TERRITOIRE PROVINCE NORD'
      };
      return territoryMap[zone] || zone || '';
    },
    formatNumber(num) {
      return new Intl.NumberFormat('fr-FR').format(num);
    },
    formatCurrency(num) {
      return new Intl.NumberFormat('fr-FR', { 
        minimumFractionDigits: 2, 
        maximumFractionDigits: 2 
      }).format(num);
    },
    formatPercent(num) {
      if (num === null || num === undefined || isNaN(num)) return '-';
      return `${num.toFixed(0)}%`;
    },
    formatTroPercent(num) {
      if (num === null || num === undefined || isNaN(num)) return '-';
      return `${num.toFixed(0)}%`;
    },
    getCollecteTroFromValues(collecteM, objectif) {
      const c = parseFloat(collecteM) || 0;
      const o = parseFloat(objectif) || 0;
      if (o <= 0) return null;
      return (c / o) * 100;
    },
    getCollecteTroForAgencyName(agencyName) {
      const c = this.getAgencyTotalByName(agencyName, 'collecteM');
      const o = this.getAgencyTotalByName(agencyName, 'objectif');
      return this.getCollecteTroFromValues(c, o);
    },
    getGrandTotalCollecteTro() {
      return this.getCollecteTroFromValues(this.getGrandTotal('collecteM'), this.getGrandTotal('objectif'));
    },
    getAgencyName(agency) {
      if (!agency) return 'Agence non identifiée';
      
      // Chercher le nom de l'agence dans plusieurs champs possibles, par ordre de priorité
      const name = agency.name || 
                   agency.AGENCE || 
                   agency.NOM_AGENCE || 
                   agency.agence ||
                   agency.BRANCH_NAME ||
                   agency.branch_name || '';
      
      // Si on a un nom valide, le retourner
      if (name && name.trim() !== '' && name.toUpperCase() !== 'INCONNU' && name.toUpperCase() !== 'UNKNOWN') {
        return name.trim();
      }
      
      // Essayer avec le code d'agence
      const code = agency.CODE_AGENCE || 
                   agency.code_agence || 
                   agency.CODE || 
                   agency.code ||
                   agency.BRANCH_CODE_AC_NO || 
                   agency.branch_code_ac_no ||
                   agency.BRANCH_CODE ||
                   agency.branch_code || '';
      
      if (code && code.trim() !== '') {
        return `Agence ${code}`;
      }
      
      // Essayer avec CODE_GESTION
      const codeGestion = agency.CODE_GESTION || agency.codeGestion || agency.CODE_GESTION_PRET || '';
      if (codeGestion && codeGestion.trim() !== '') {
        return `Agence ${codeGestion}`;
      }
      
      // Dernier recours : utiliser un identifiant unique
      const uniqueId = agency.AC_NO || agency.ac_no || agency.ACCOUNT_NUMBER || agency.account_number || '';
      if (uniqueId && uniqueId.trim() !== '') {
        return `Agence ${uniqueId}`;
      }
      
      return 'Agence non identifiée';
    },
    filterAgencies(agencies) {
      // Filtrer les agences - être moins restrictif pour accepter plus d'agences
      if (!agencies || !Array.isArray(agencies)) {
        return [];
      }
      
      const filtered = agencies.filter(agency => {
        if (!agency || typeof agency !== 'object') {
          return false;
        }
        
        // Exclure le grand compte (BRANCH_CODE 526) des zones territoriales
        const branchCode = agency.BRANCH_CODE || agency.branch_code || '';
        const agencyName = (agency.name || agency.AGENCE || '').toUpperCase();
        if (branchCode === '526' || 
            agencyName.includes('GRAND COMPTE') || 
            agencyName.includes('GRAND COMPTES')) {
          return false;
        }
        
        // Exclure spécifiquement "AGENCE LINGUERE'LA GUEDIAWAYE"
        if (agencyName.includes('LINGUERE') && agencyName.includes('GUEDIAWAYE')) {
          return false;
        }
        
        // Exclure spécifiquement "COFINA EXPRESS TAMBA"
        if (agencyName.includes('COFINA EXPRESS') && agencyName.includes('TAMBA')) {
          return false;
        }
        
        // Accepter l'agence si elle a au moins un identifiant valide
        const hasName = agency.name || agency.AGENCE || agency.NOM_AGENCE || agency.agence || agency.BRANCH_NAME;
        const hasCode = agency.CODE_AGENCE || agency.code_agence || agency.CODE || agency.BRANCH_CODE || agency.BRANCH_CODE_AC_NO;
        const hasCodeGestion = agency.CODE_GESTION || agency.codeGestion || agency.CODE_GESTION_PRET;
        const hasAccountNumber = agency.AC_NO || agency.ac_no || agency.ACCOUNT_NUMBER;
        
        // Vérifier si toutes les valeurs de collecte sont à 0
        const collecteM = parseFloat(agency.collecteM || agency.COLLECTE_M || 0);
        const collecteS1 = parseFloat(agency.collecteS1 || agency.COLLECTE_S1 || 0);
        const collecteS2 = parseFloat(agency.collecteS2 || agency.COLLECTE_S2 || 0);
        const collecteS3 = parseFloat(agency.collecteS3 || agency.COLLECTE_S3 || 0);
        const collecteS4 = parseFloat(agency.collecteS4 || agency.COLLECTE_S4 || 0);
        const exigibleM1 = parseFloat(agency.exigibleM1 || agency.EXIGIBLE_M1 || 0);
        const mtEcheance = parseFloat(agency.mtEcheance || agency.MT_ECHEANCE || 0);
        const sldM = parseFloat(agency.sldM || agency.SLD_M || 0);
        const sldS1 = parseFloat(agency.sldS1 || agency.SLD_S1 || 0);
        const sldS2 = parseFloat(agency.sldS2 || agency.SLD_S2 || 0);
        const sldS3 = parseFloat(agency.sldS3 || agency.SLD_S3 || 0);
        const sldS4 = parseFloat(agency.sldS4 || agency.SLD_S4 || 0);
        
        // Vérifier si toutes les valeurs sont à 0
        const allZero = collecteM === 0 && collecteS1 === 0 && collecteS2 === 0 && collecteS3 === 0 && collecteS4 === 0 &&
                        exigibleM1 === 0 && mtEcheance === 0 && sldM === 0 && sldS1 === 0 && sldS2 === 0 && sldS3 === 0 && sldS4 === 0;
        
        // Exclure les agences avec toutes les valeurs à 0
        if (allZero) {
          return false;
        }
        
        // Accepter si on a au moins un identifiant
        if (hasName || hasCode || hasCodeGestion || hasAccountNumber) {
          // Vérifier que le nom n'est pas explicitement "INCONNU" ou vide
          const name = hasName || '';
          const nameUpper = (name || '').toUpperCase().trim();
          
          // Exclure seulement si le nom est explicitement "INCONNU" ou "UNKNOWN"
          // Mais accepter même si le nom est vide, tant qu'on a un autre identifiant
          if (nameUpper === 'INCONNU' || nameUpper === 'UNKNOWN') {
            // Si on a un autre identifiant, on accepte quand même
            if (hasCode || hasCodeGestion || hasAccountNumber) {
              return true;
            }
            return false;
          }
          
          return true;
        }
        
        // Accepter même si aucun identifiant n'est trouvé (pour les agences par défaut créées)
        // Mais seulement si elles ont des valeurs non nulles
        return !allZero;
      });
      
      // Trier les agences par nom pour un affichage cohérent
      return filtered.sort((a, b) => {
        const nameA = this.getAgencyName(a).toUpperCase();
        const nameB = this.getAgencyName(b).toUpperCase();
        return nameA.localeCompare(nameB, 'fr', { numeric: true, sensitivity: 'base' });
      });
    },
    getDefaultAgenciesForTerritory(territoryKey) {
      // Liste des agences par défaut pour chaque territoire
      const defaultAgenciesMap = {
        'dakar_centre_ville': [
          { name: 'AGENCE PRINCIPALE POINT E', AGENCE: 'AGENCE PRINCIPALE POINT E' },
          { name: 'AGENCE CASTORS', AGENCE: 'AGENCE CASTORS' },
          { name: 'C-E NGUELAW', AGENCE: 'C-E NGUELAW' },
          { name: 'AGENCE LAMINE GUEYE', AGENCE: 'AGENCE LAMINE GUEYE' },
          { name: 'C-E MARISTES', AGENCE: 'C-E MARISTES' },
          { name: 'AGENCE KEUR MASSAR', AGENCE: 'AGENCE KEUR MASSAR' }
        ],
        'dakar_banlieue': [
          { name: 'AGENCE PIKINE', AGENCE: 'AGENCE PIKINE' },
          { name: 'AGENCE PARCELLES', AGENCE: 'AGENCE PARCELLES' },
          { name: 'COFINA EXPRESS RUFISQUE', AGENCE: 'COFINA EXPRESS RUFISQUE' }
        ],
        'province_centre_sud': [
          { name: 'KAOLACK', AGENCE: 'KAOLACK' },
          { name: 'MBOUR', AGENCE: 'MBOUR' },
          { name: 'THIES', AGENCE: 'THIES' },
          { name: 'COFINA C. E. ZIGUINCHOR', AGENCE: 'COFINA C. E. ZIGUINCHOR' }
        ],
        'province_nord': [
          { name: 'TOUBA', AGENCE: 'TOUBA' },
          { name: 'SAINT LOUIS', AGENCE: 'SAINT LOUIS' },
          { name: 'COFINA EXPRESS DIOURBEL', AGENCE: 'COFINA EXPRESS DIOURBEL' },
          { name: 'COFINA EXPRESS LOUGA', AGENCE: 'COFINA EXPRESS LOUGA' },
          { name: 'COFINA EXPRESS OUROSSOGUI', AGENCE: 'COFINA EXPRESS OUROSSOGUI' }
        ],
        'territoire_dakar_ville': [
          { name: 'AGENCE PRINCIPALE POINT E', AGENCE: 'AGENCE PRINCIPALE POINT E' },
          { name: 'AGENCE CASTORS', AGENCE: 'AGENCE CASTORS' },
          { name: 'C-E NGUELAW', AGENCE: 'C-E NGUELAW' },
          { name: 'AGENCE LAMINE GUEYE', AGENCE: 'AGENCE LAMINE GUEYE' },
          { name: 'C-E MARISTES', AGENCE: 'C-E MARISTES' },
          { name: 'AGENCE KEUR MASSAR', AGENCE: 'AGENCE KEUR MASSAR' }
        ],
        'territoire_dakar_banlieue': [
          { name: 'AGENCE PIKINE', AGENCE: 'AGENCE PIKINE' },
          { name: 'AGENCE PARCELLES', AGENCE: 'AGENCE PARCELLES' },
          { name: 'COFINA EXPRESS RUFISQUE', AGENCE: 'COFINA EXPRESS RUFISQUE' }
        ],
        'territoire_province_centre_sud': [
          { name: 'KAOLACK', AGENCE: 'KAOLACK' },
          { name: 'MBOUR', AGENCE: 'MBOUR' },
          { name: 'THIES', AGENCE: 'THIES' },
          { name: 'COFINA C. E. ZIGUINCHOR', AGENCE: 'COFINA C. E. ZIGUINCHOR' }
        ],
        'territoire_province_nord': [
          { name: 'TOUBA', AGENCE: 'TOUBA' },
          { name: 'SAINT LOUIS', AGENCE: 'SAINT LOUIS' },
          { name: 'COFINA EXPRESS DIOURBEL', AGENCE: 'COFINA EXPRESS DIOURBEL' },
          { name: 'COFINA EXPRESS LOUGA', AGENCE: 'COFINA EXPRESS LOUGA' },
          { name: 'COFINA EXPRESS OUROSSOGUI', AGENCE: 'COFINA EXPRESS OUROSSOGUI' }
        ]
      };
      
      return defaultAgenciesMap[territoryKey] || [];
    },
    getDefaultServicePoints() {
      // Liste des points de service par défaut
      return [
        { name: 'C-E NIARRY TALLI', AGENCE: 'C-E NIARRY TALLI' },
        { name: 'C-E SCAT URBAM', AGENCE: 'C-E SCAT URBAM' }
      ];
    },
    mergeAgenciesWithDefaults(backendAgencies, defaultAgencies) {
      // Normaliser un nom d'agence pour la comparaison (supprimer accents, espaces multiples, etc.)
      const normalizeName = (name) => {
        if (!name) return '';
        return name.toUpperCase()
          .normalize('NFD')
          .replace(/[\u0300-\u036f]/g, '') // Supprimer les accents
          .replace(/\s+/g, ' ') // Remplacer espaces multiples par un seul
          .trim()
          .replace(/[^\w\s]/g, '') // Supprimer caractères spéciaux sauf espaces
          .replace(/\s+/g, ''); // Supprimer tous les espaces
      };
      
      // Créer un map des agences du backend par nom normalisé
      const backendMap = new Map();
      backendAgencies.forEach(agency => {
        const agencyName = this.getAgencyName(agency);
        const normalizedName = normalizeName(agencyName);
        // Stocker avec plusieurs clés possibles pour plus de flexibilité
        backendMap.set(normalizedName, agency);
        // Aussi stocker avec le nom original
        backendMap.set(agencyName.toUpperCase().trim(), agency);
        // Et avec les variantes possibles
        if (agency.AGENCE) {
          backendMap.set(normalizeName(agency.AGENCE), agency);
        }
        if (agency.name) {
          backendMap.set(normalizeName(agency.name), agency);
        }
      });
      
      // Fusionner : utiliser les données du backend si disponibles, sinon utiliser les agences par défaut
      const merged = defaultAgencies.map(defaultAgency => {
        const defaultName = this.getAgencyName(defaultAgency);
        const normalizedDefaultName = normalizeName(defaultName);
        
        // Chercher une correspondance dans le backend
        let backendAgency = backendMap.get(normalizedDefaultName) || 
                           backendMap.get(defaultName.toUpperCase().trim()) ||
                           backendMap.get(normalizeName(defaultAgency.AGENCE || '')) ||
                           backendMap.get(normalizeName(defaultAgency.name || ''));
        
        // Si pas de correspondance exacte, chercher une correspondance partielle
        if (!backendAgency) {
          for (const [key, agency] of backendMap.entries()) {
            const backendNormalized = normalizeName(key);
            // Vérifier si le nom normalisé contient le nom par défaut ou vice versa
            if (normalizedDefaultName.includes(backendNormalized) || 
                backendNormalized.includes(normalizedDefaultName) ||
                normalizedDefaultName.replace(/AGENCE|COFINA|EXPRESS|CE|C\.E\./g, '').trim() === 
                backendNormalized.replace(/AGENCE|COFINA|EXPRESS|CE|C\.E\./g, '').trim()) {
              backendAgency = agency;
              break;
            }
          }
        }
        
        if (backendAgency) {
          // Utiliser les données du backend
          return backendAgency;
        } else {
          // Créer une agence vide avec les données par défaut
          const emptyAgency = {
            ...defaultAgency,
            name: defaultAgency.name || defaultAgency.AGENCE || 'Agence non identifiée',
            AGENCE: defaultAgency.AGENCE || defaultAgency.name || 'Agence non identifiée',
            EXIGIBLE_M_1: 0,
            EXIGIBLE_M1: 0,
            exigibleM1: 0,
            MT_ECHEANCE: 0,
            mtEcheance: 0,
            COLLECTE_M: 0,
            collecteM: 0,
            SLD_M: 0,
            sldM: 0,
            COLLECTE_S1: 0,
            collecteS1: 0,
            SLD_S1: 0,
            sldS1: 0,
            COLLECTE_S2: 0,
            collecteS2: 0,
            SLD_S2: 0,
            sldS2: 0,
            COLLECTE_S3: 0,
            collecteS3: 0,
            SLD_S3: 0,
            sldS3: 0,
            COLLECTE_S4: 0,
            collecteS4: 0,
            SLD_S4: 0,
            sldS4: 0,
            CODE_GESTION: '-',
            codeGestion: '-',
            CHARGE_AFFAIRE: '-',
            chargeAffaire: '-'
          };
          return emptyAgency;
        }
      });
      
      // Ajouter les agences du backend qui ne sont pas dans les agences par défaut
      backendAgencies.forEach(agency => {
        const agencyName = this.getAgencyName(agency);
        const normalizedAgencyName = normalizeName(agencyName);
        const exists = merged.some(m => {
          const mergedName = this.getAgencyName(m);
          const normalizedMergedName = normalizeName(mergedName);
          return normalizedMergedName === normalizedAgencyName || 
                 normalizedMergedName.includes(normalizedAgencyName) ||
                 normalizedAgencyName.includes(normalizedMergedName);
        });
        if (!exists) {
          merged.push(agency);
        }
      });
      
      // Trier les agences par nom pour un affichage cohérent
      return merged.sort((a, b) => {
        const nameA = this.getAgencyName(a).toUpperCase();
        const nameB = this.getAgencyName(b).toUpperCase();
        return nameA.localeCompare(nameB, 'fr', { numeric: true, sensitivity: 'base' });
      });
    },
    calculateZoneTotals(agencies) {
      const totals = {
        exigibleM1: 0,
        mtEcheance: 0,
        m: 0,
        sldM: 0,
        collecteM: 0,
        objectif: 0,
        tro: null,
        exigibleS1: 0,
        mtEcheanceS1: 0,
        mS1: 0,
        sldS1: 0,
        collecteS1: 0,
        collecteS2: 0,
        sldS2: 0,
        collecteS3: 0,
        sldS3: 0,
        collecteS4: 0,
        sldS4: 0
      };

      agencies.forEach(agency => {
        totals.exigibleM1 += agency.exigibleM1 || agency.EXIGIBLE_M1 || 0;
        totals.mtEcheance += agency.mtEcheance || agency.MT_ECHEANCE || 0;
        totals.m += agency.m || agency.M || 0;
        totals.sldM += agency.sldM || agency.SLD_M || 0;
        totals.collecteM += agency.collecteM || agency.COLLECTE_M || 0;
        totals.objectif += parseFloat(agency.objectif || agency.OBJECTIF || 0) || 0;
        totals.exigibleS1 += agency.exigibleS1 || agency.EXIGIBLE_S1 || 0;
        totals.mtEcheanceS1 += agency.mtEcheanceS1 || agency.MT_ECHEANCE_S1 || 0;
        totals.mS1 += agency.mS1 || agency.M_S1 || 0;
        totals.sldS1 += agency.sldS1 || agency.SLD_S1 || 0;
        totals.collecteS1 += agency.collecteS1 || agency.COLLECTE_S1 || 0;
        totals.collecteS2 += agency.collecteS2 || agency.COLLECTE_S2 || 0;
        totals.sldS2 += agency.sldS2 || agency.SLD_S2 || 0;
        totals.collecteS3 += agency.collecteS3 || agency.COLLECTE_S3 || 0;
        totals.sldS3 += agency.sldS3 || agency.SLD_S3 || 0;
        totals.collecteS4 += agency.collecteS4 || agency.COLLECTE_S4 || 0;
        totals.sldS4 += agency.sldS4 || agency.SLD_S4 || 0;
      });

      totals.tro = totals.objectif > 0 ? (totals.collecteM / totals.objectif) * 100 : null;
      return totals;
    },
    getAgencyKey(agency, index) {
      // Générer une clé unique pour chaque agence
      if (!agency) return `agency-${index}`;
      
      const name = agency.name || agency.AGENCE || agency.NOM_AGENCE || '';
      const code = agency.CODE_AGENCE || agency.code_agence || agency.BRANCH_CODE || agency.BRANCH_CODE_AC_NO || '';
      const codeGestion = agency.CODE_GESTION || agency.codeGestion || '';
      const accountNumber = agency.AC_NO || agency.ac_no || agency.ACCOUNT_NUMBER || '';
      
      // Utiliser le premier identifiant disponible
      const identifier = name || code || codeGestion || accountNumber || `agency-${index}`;
      return `agency-${identifier}-${index}`;
    },
    getChargeAffaireDetails(agency) {
      // Récupérer les détails des chargés d'affaire pour cette agence
      if (!agency) {
        return [];
      }
      
      if (!this.chargeAffaireDetails || Object.keys(this.chargeAffaireDetails).length === 0) {
        return [];
      }
      
      // Construire la clé de l'agence (même format que dans le backend: agency_name_branch_code)
      // Utiliser getAgencyName pour obtenir le nom de l'agence (comme dans le backend)
      const agencyName = this.getAgencyName(agency);
      const branchCode = agency.BRANCH_CODE || agency.branch_code || agency.BRANCH_CODE_AC_NO || agency.AC_NO || '';
      
      // Essayer différentes combinaisons de clés (comme dans le backend: f"{agency_name}_{branch_code}")
      const possibleKeys = [
        `${agencyName}_${branchCode}`,
        `${agencyName}_`,
        `${agencyName}`,
        agency.name || '',
        agency.AGENCE || '',
        agency.agence || '',
        agency.NOM_AGENCE || '',
        agency.BRANCH_NAME || ''
      ].filter(key => key && key !== '_' && key.trim() !== '');
      
      // Chercher la clé correspondante
      let details = [];
      for (const key of possibleKeys) {
        if (this.chargeAffaireDetails[key]) {
          details = this.chargeAffaireDetails[key];
          break;
        }
      }
      
      // Si aucune clé exacte n'est trouvée, chercher une correspondance partielle
      if (details.length === 0 && agencyName) {
        const matchingKey = Object.keys(this.chargeAffaireDetails).find(key => 
          key.includes(agencyName) || agencyName.includes(key.split('_')[0])
        );
        if (matchingKey) {
          details = this.chargeAffaireDetails[matchingKey];
        }
      }
      
      return Array.isArray(details) ? details : [];
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
      
      // D'abord, chercher directement par la clé (la clé est le branch_code dans le backend)
      if (this.chargeAffaireDetails[branchCodeStr]) {
        const directMatch = this.chargeAffaireDetails[branchCodeStr];
        if (Array.isArray(directMatch) && directMatch.length > 0) {
          // Filtrer les lignes sans code gestionnaire valide (une seule passe)
          const filteredDetails = directMatch.filter(charge => {
            const codeGestion = charge.codeGestion || charge.CODE_GESTION || '';
            return codeGestion && codeGestion.trim() !== '' && codeGestion.trim() !== '-';
          });
          
          // Mettre en cache le résultat
          this.chargeAffaireDetailsCache.set(branchCodeStr, filteredDetails);
          return filteredDetails;
        }
      }
      
      // Si pas trouvé directement, chercher dans toutes les clés (mais seulement si nécessaire)
      const matchingDetails = [];
      
      // Parcourir toutes les clés dans chargeAffaireDetails
      Object.keys(this.chargeAffaireDetails).forEach(key => {
        const chargeList = this.chargeAffaireDetails[key];
        if (Array.isArray(chargeList)) {
          chargeList.forEach(charge => {
            const chargeBranchCode = String(charge.BRANCH_CODE || charge.branch_code || '').trim();
            if (chargeBranchCode === branchCodeStr) {
              // Filtrer les lignes sans code gestionnaire valide
              const codeGestion = charge.codeGestion || charge.CODE_GESTION || '';
              if (!codeGestion || codeGestion.trim() === '' || codeGestion.trim() === '-') {
                return; // Ignorer cette ligne
              }
              
              // Vérifier si ce chargé d'affaire n'existe pas déjà
              const exists = matchingDetails.some(existing => 
                (existing.codeGestion || existing.CODE_GESTION) === (charge.codeGestion || charge.CODE_GESTION) &&
                (existing.chargeAffaire || existing.CHARGE_AFFAIRE) === (charge.chargeAffaire || charge.CHARGE_AFFAIRE)
              );
              if (!exists) {
                matchingDetails.push(charge);
              }
            }
          });
        }
      });
      
      // Mettre en cache le résultat (même si vide)
      this.chargeAffaireDetailsCache.set(branchCodeStr, matchingDetails);
      
      return matchingDetails;
    },
    hasChargeAffaireDetails(agency) {
      if (!agency) return false;
      
      // Vérifier d'abord si l'agence a une liste de chargés d'affaire (plus rapide)
      const chargeAffaireList = agency.chargeAffaireList || agency.CHARGE_AFFAIRE_LIST || [];
      if (chargeAffaireList && chargeAffaireList.length > 1) {
        return true;
      }
      
      // Vérifier aussi si l'agence a plusieurs codes gestionnaires
      const codeGestionList = agency.codeGestionList || agency.CODE_GESTION_LIST || [];
      if (codeGestionList && codeGestionList.length > 1) {
        return true;
      }
      
      // En dernier, vérifier dans chargeAffaireDetails (plus lent)
      const branchCode = agency.BRANCH_CODE || agency.branch_code;
      if (branchCode && this.getChargeAffaireDetailsByBranchCode(branchCode).length > 0) {
        return true;
      }
      
      return false;
    },
    getChargeAffaireLinesForAgency(agency) {
      if (!agency) return [];
      
      const branchCode = agency.BRANCH_CODE || agency.branch_code;
      
      // D'abord, essayer de récupérer depuis chargeAffaireDetails (déjà filtré et mis en cache)
      const detailsFromDetails = this.getChargeAffaireDetailsByBranchCode(branchCode);
      if (detailsFromDetails && detailsFromDetails.length > 0) {
        return detailsFromDetails;
      }
      
      // Sinon, créer des lignes à partir des listes
      const chargeAffaireList = agency.chargeAffaireList || agency.CHARGE_AFFAIRE_LIST || [];
      const codeGestionList = agency.codeGestionList || agency.CODE_GESTION_LIST || [];
      
      if (chargeAffaireList.length === 0 && codeGestionList.length === 0) {
        return [];
      }
      
      // Créer une ligne pour chaque combinaison unique de code gestionnaire et chargé d'affaire
      const lines = [];
      const maxLength = Math.max(chargeAffaireList.length, codeGestionList.length);
      
      for (let i = 0; i < maxLength; i++) {
        const codeGestion = codeGestionList[i] || codeGestionList[0] || agency.codeGestion || agency.CODE_GESTION || '-';
        const chargeAffaire = chargeAffaireList[i] || chargeAffaireList[0] || agency.chargeAffaire || agency.CHARGE_AFFAIRE || '-';
        
        // Exclure les lignes sans code gestionnaire valide
        if (!codeGestion || codeGestion.trim() === '' || codeGestion.trim() === '-') {
          continue;
        }
        
        // Vérifier si cette combinaison existe déjà
        const exists = lines.some(line => 
          line.codeGestion === codeGestion && line.chargeAffaire === chargeAffaire
        );
        
        if (!exists) {
          lines.push({
            BRANCH_CODE: branchCode,
            branch_code: branchCode,
            codeGestion: codeGestion,
            CODE_GESTION: codeGestion,
            chargeAffaire: chargeAffaire,
            CHARGE_AFFAIRE: chargeAffaire,
            // Utiliser les valeurs de l'agence pour les montants (seront partagés entre les lignes)
            exigibleM1: agency.exigibleM1 || agency.EXIGIBLE_M1 || 0,
            EXIGIBLE_M1: agency.EXIGIBLE_M1 || agency.exigibleM1 || 0,
            mtEcheance: agency.mtEcheance || agency.MT_ECHEANCE || 0,
            MT_ECHEANCE: agency.MT_ECHEANCE || agency.mtEcheance || 0,
            collecteM: agency.collecteM || agency.COLLECTE_M || 0,
            COLLECTE_M: agency.COLLECTE_M || agency.collecteM || 0,
            collecteS1: agency.collecteS1 || agency.COLLECTE_S1 || 0,
            COLLECTE_S1: agency.COLLECTE_S1 || agency.collecteS1 || 0,
            collecteS2: agency.collecteS2 || agency.COLLECTE_S2 || 0,
            COLLECTE_S2: agency.COLLECTE_S2 || agency.collecteS2 || 0,
            collecteS3: agency.collecteS3 || agency.COLLECTE_S3 || 0,
            COLLECTE_S3: agency.COLLECTE_S3 || agency.collecteS3 || 0,
            collecteS4: agency.collecteS4 || agency.COLLECTE_S4 || 0,
            COLLECTE_S4: agency.COLLECTE_S4 || agency.collecteS4 || 0,
            sldM: agency.sldM || agency.SLD_M || 0,
            SLD_M: agency.SLD_M || agency.sldM || 0,
            sldS1: agency.sldS1 || agency.SLD_S1 || 0,
            SLD_S1: agency.SLD_S1 || agency.sldS1 || 0,
            sldS2: agency.sldS2 || agency.SLD_S2 || 0,
            SLD_S2: agency.SLD_S2 || agency.sldS2 || 0,
            sldS3: agency.sldS3 || agency.SLD_S3 || 0,
            SLD_S3: agency.SLD_S3 || agency.sldS3 || 0,
            sldS4: agency.sldS4 || agency.SLD_S4 || 0,
            SLD_S4: agency.SLD_S4 || agency.sldS4 || 0
          });
        }
      }
      
      return lines;
    },
    getCodeGestionDisplay(agency) {
      if (!agency) return '-';
      
      // Si l'agence a une liste de codes gestionnaires avec plus d'un élément, afficher "ALL"
      const codeGestionList = agency.codeGestionList || agency.CODE_GESTION_LIST || [];
      if (codeGestionList && codeGestionList.length > 1) {
        return 'ALL';
      }
      
      // Si un seul code gestionnaire, l'afficher
      if (codeGestionList && codeGestionList.length === 1) {
        return codeGestionList[0];
      }
      
      // Sinon, afficher le code gestionnaire principal
      return agency.codeGestion || agency.CODE_GESTION || '-';
    },
    getChargeAffaireDisplay(agency) {
      if (!agency) return '-';
      
      // Si l'agence a une liste de chargés d'affaire avec plus d'un élément, afficher "ALL"
      const chargeAffaireList = agency.chargeAffaireList || agency.CHARGE_AFFAIRE_LIST || [];
      if (chargeAffaireList && chargeAffaireList.length > 1) {
        return 'ALL';
      }
      
      // Si un seul chargé d'affaire, l'afficher
      if (chargeAffaireList && chargeAffaireList.length === 1) {
        return chargeAffaireList[0];
      }
      
      // Sinon, afficher le chargé d'affaire principal
      return agency.chargeAffaire || agency.CHARGE_AFFAIRE || '-';
    },
    getGrandTotal(field) {
      let total = 0;
      const hierarchicalData = this.filteredHierarchicalData || {};
      
      if (hierarchicalData.TERRITOIRE && 
          typeof hierarchicalData.TERRITOIRE === 'object' && 
          hierarchicalData.TERRITOIRE !== null &&
          !Array.isArray(hierarchicalData.TERRITOIRE)) {
        try {
          Object.values(hierarchicalData.TERRITOIRE).forEach(territory => {
            if (territory && territory.totals && territory.totals[field] !== undefined) {
              total += territory.totals[field] || 0;
            }
          });
        } catch (e) {
          // Erreur silencieuse lors du calcul du total des territoires
        }
      }
      
      return total;
    },
    toggleExpand(section) {
      this.expandedSections[section] = !this.expandedSections[section];
      if (this.selectedAgency) {
        const agencyZone = `${this.selectedAgency.category}_${this.selectedAgency.zone}`;
        if (section === agencyZone && !this.expandedSections[section]) {
          this.selectedAgency = null;
        }
      }
      if (this.selectedAgency && (section === this.selectedAgency.category)) {
        if (!this.expandedSections[section]) {
          this.selectedAgency = null;
        }
      }
    },
    toggleAgencyExpand(agency, sectionKey) {
      const wasExpanded = this.expandedSections[sectionKey];
      this.expandedSections[sectionKey] = !wasExpanded;
      
      // Si on vient d'expand, calculer et mettre en cache les lignes
      if (!wasExpanded && !this.expandedAgencyLines[sectionKey]) {
        // En Vue 3, on peut directement assigner (la réactivité est automatique)
        this.expandedAgencyLines[sectionKey] = this.getChargeAffaireLinesForAgency(agency);
      }
    },
    getCachedChargeAffaireLines(sectionKey) {
      // Retourner les lignes mises en cache, ou un tableau vide si pas encore calculé
      return this.expandedAgencyLines[sectionKey] || [];
    },
    getAgenciesByBranchCode(branchCode) {
      if (!branchCode) return [];
      
      // Récupérer toutes les agences avec le même BRANCH_CODE depuis toutes les zones
      const allAgencies = [];
      const hierarchicalData = this.filteredHierarchicalData || {};
      
      // Parcourir tous les territoires
      if (hierarchicalData.TERRITOIRE) {
        Object.values(hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory && territory.agencies && Array.isArray(territory.agencies)) {
            territory.agencies.forEach(agency => {
              const agencyBranchCode = agency.BRANCH_CODE || agency.branch_code;
              if (agencyBranchCode === branchCode) {
                allAgencies.push(agency);
              }
            });
          }
        });
      }
      
      // Si on a des détails de chargés d'affaire, les utiliser aussi
      if (this.chargeAffaireDetails && Object.keys(this.chargeAffaireDetails).length > 0) {
        Object.values(this.chargeAffaireDetails).forEach(chargeList => {
          if (Array.isArray(chargeList)) {
            chargeList.forEach(charge => {
              const chargeBranchCode = charge.BRANCH_CODE || charge.branch_code;
              if (chargeBranchCode === branchCode) {
                // Vérifier si cette ligne n'existe pas déjà
                const exists = allAgencies.some(ag => 
                  (ag.codeGestion || ag.CODE_GESTION) === (charge.codeGestion || charge.CODE_GESTION) &&
                  (ag.chargeAffaire || ag.CHARGE_AFFAIRE) === (charge.chargeAffaire || charge.CHARGE_AFFAIRE)
                );
                if (!exists) {
                  allAgencies.push(charge);
                }
              }
            });
          }
        });
      }
      
      return allAgencies;
    },
    getAgenciesByName(agencyName) {
      if (!agencyName) return [];
      
      // Récupérer toutes les agences avec le même nom depuis toutes les zones
      const allAgencies = [];
      const hierarchicalData = this.filteredHierarchicalData || {};
      
      // Parcourir tous les territoires
      if (hierarchicalData.TERRITOIRE) {
        Object.values(hierarchicalData.TERRITOIRE).forEach(territory => {
          if (territory && territory.agencies && Array.isArray(territory.agencies)) {
            territory.agencies.forEach(agency => {
              const currentAgencyName = agency.name || agency.AGENCE || this.getAgencyName(agency);
              if (currentAgencyName === agencyName) {
                allAgencies.push(agency);
              }
            });
          }
        });
      }
      
      // Si on a des détails de chargés d'affaire, les utiliser aussi
      if (this.chargeAffaireDetails && Object.keys(this.chargeAffaireDetails).length > 0) {
        Object.values(this.chargeAffaireDetails).forEach(chargeList => {
          if (Array.isArray(chargeList)) {
            chargeList.forEach(charge => {
              const chargeAgencyName = charge.name || charge.AGENCE || this.getAgencyName(charge);
              if (chargeAgencyName === agencyName) {
                // Vérifier si cette ligne n'existe pas déjà (par BRANCH_CODE)
                const exists = allAgencies.some(ag => 
                  (ag.BRANCH_CODE || ag.branch_code) === (charge.BRANCH_CODE || charge.branch_code)
                );
                if (!exists) {
                  allAgencies.push(charge);
                }
              }
            });
          }
        });
      }
      
      return allAgencies;
    },
    getAgencyTotalByName(agencyName, field) {
      if (!agencyName) return 0;
      
      const agencies = this.getAgenciesByName(agencyName);
      let total = 0;
      
      agencies.forEach(agency => {
        const value = agency[field] || agency[field.toUpperCase()] || 0;
        total += parseFloat(value) || 0;
      });
      
      return total;
    },
    selectAgency(agency) {
      if (this.selectedAgency && 
          this.selectedAgency.name === agency.name && 
          this.selectedAgency.category === agency.category && 
          this.selectedAgency.zone === agency.zone) {
        this.selectedAgency = null;
      } else {
        this.selectedAgency = agency;
      }
    },
    resetToTotal() {
      this.selectedAgency = null;
      this.expandedSections.TERRITOIRE = false;
      Object.keys(this.expandedSections).forEach(key => {
        if (key.startsWith('TERRITOIRE_')) {
          this.expandedSections[key] = false;
        }
      });
    },
    async exportChart(format) {
      try {
        await this.$nextTick();
        
        if (format === 'csv') {
          const labels = this.chartLabels;
          const current = this.chartCurrentData;
          const typeLabels = {
            'recouvrement': 'Collecte M',
            'collection': 'Collecte S1',
            'epargne': 'Epargne'
          };
          const typeLabel = typeLabels[this.selectedDataType] || 'Collecte M';
          let csv = 'Période,' + typeLabel + '\n';
          
          for (let i = 0; i < labels.length; i++) {
            const value = current[i] || 0;
            csv += `"${labels[i]}",${value}\n`;
          }
          
          const BOM = '\uFEFF';
          const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
          const link = document.createElement('a');
          const fileName = `donnees-collection-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${this.selectedDataType}-${new Date().toISOString().split('T')[0]}.csv`;
          link.download = fileName;
          link.href = URL.createObjectURL(blob);
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          setTimeout(() => URL.revokeObjectURL(link.href), 100);
          return;
        }
        
        const chartRef = this.$refs.chartComponent;
        if (!chartRef || !chartRef.chartContainer) {
          alert('Le graphique n\'est pas encore chargé. Veuillez attendre quelques instants.');
          return;
        }

        if (format === 'png' || format === 'pdf') {
          const Plotly = (await import('plotly.js-dist')).default;
          const container = chartRef.chartContainer;
          
          if (!container) {
            alert('Le graphique n\'est pas encore chargé. Veuillez attendre quelques instants.');
            return;
          }
          
          const img = await Plotly.toImage(container, {
            format: 'png',
            width: 1200,
            height: 600
          });
          
          const link = document.createElement('a');
          const extension = format === 'pdf' ? 'png' : 'png';
          const fileName = `graphique-collection-${(this.activeLevel.name || 'total').replace(/\s+/g, '-')}-${this.selectedChartType}-${this.selectedDataType}-${new Date().toISOString().split('T')[0]}.${extension}`;
          link.download = fileName;
          link.href = img;
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          
          if (format === 'pdf') {
            alert('Graphique exporté en PNG. Pour PDF, ouvrez l\'image et utilisez "Imprimer en PDF" de votre navigateur.');
          }
        }
      } catch (error) {
        alert('Erreur lors de l\'export du graphique : ' + error.message);
      }
    },
    getSelectedMonthName() {
      return this.months[this.selectedMonth - 1];
    },
    getPeriodTitle() {
      if (this.selectedPeriod === 'week') {
        return 'Résultat de la semaine';
      } else if (this.selectedPeriod === 'month') {
        return `Résultat Global du Mois (${this.getSelectedMonthName()} ${this.selectedYear})`;
      } else if (this.selectedPeriod === 'year') {
        return `Résultat Global de l'Année (${this.selectedYear})`;
      }
      return 'Résultat Global';
    },
    updateWeekFromDate() {
      if (this.selectedDate) {
        const date = new Date(this.selectedDate);
        this.selectedYear = date.getFullYear();
        this.selectedWeek = this.getWeekNumber(date);
      }
    },
    getWeekNumber(date) {
      const d = date instanceof Date ? date : new Date(date);
      const dateObj = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
      const dayNum = dateObj.getUTCDay() || 7;
      dateObj.setUTCDate(dateObj.getUTCDate() + 4 - dayNum);
      const yearStart = new Date(Date.UTC(dateObj.getUTCFullYear(), 0, 1));
      return Math.ceil((((dateObj - yearStart) / 86400000) + 1) / 7);
    },
    async fetchDataFromOracle() {
      this.loading = true;
      try {
        const params = {
          period: this.selectedPeriod,
          zone: this.selectedZone || null
        };
        
        if (this.selectedPeriod === 'week') {
          if (this.selectedDate) {
            let dateToSend = this.selectedDate;
            if (dateToSend.includes('/')) {
              const parts = dateToSend.split('/');
              dateToSend = `${parts[2]}-${parts[1]}-${parts[0]}`;
            }
            params.date = dateToSend;
          }
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'month') {
          params.month = this.selectedMonth;
          params.year = this.selectedYear;
        } else if (this.selectedPeriod === 'year') {
          params.year = this.selectedYear;
        }
        
        this.errorMessage = null;
        
        const endpoint = '/api/oracle/data/collection';

        const response = await window.axios.get(endpoint, { params });
        
        let data = null;
        let chargeAffaireDetailsFromResponse = null;
        
        if (response.data && response.data.data) {
          data = response.data.data;
          // Récupérer chargeAffaireDetails depuis response.data si disponible
          chargeAffaireDetailsFromResponse = response.data.chargeAffaireDetails || response.data.data?.chargeAffaireDetails;
        } else if (response.data) {
          data = response.data;
          // Si data est un array, chargeAffaireDetails peut être dans response.data directement
          if (Array.isArray(data)) {
            chargeAffaireDetailsFromResponse = response.data.chargeAffaireDetails;
          } else {
            chargeAffaireDetailsFromResponse = data.chargeAffaireDetails;
          }
        }
        
        // Assigner chargeAffaireDetails dès qu'on le trouve
        if (chargeAffaireDetailsFromResponse) {
          this.chargeAffaireDetails = chargeAffaireDetailsFromResponse;
          // Vider le cache quand les données changent
          this.chargeAffaireDetailsCache.clear();
        }
        
        if (data) {
          // Si les données sont dans un format plat (array direct)
          if (Array.isArray(data) && data.length > 0) {
            // Grouper par territoire ou agence
            const grouped = {};
            data.forEach(item => {
              const territoryKey = item.TERRITOIRE || item.territoire || 'autre';
              if (!grouped[territoryKey]) {
                grouped[territoryKey] = [];
              }
              grouped[territoryKey].push(item);
            });
            
            // Convertir en format hiérarchique
            const hierarchical = {
              TERRITOIRE: {}
            };
            
            Object.keys(grouped).forEach(key => {
              const agencies = this.filterAgencies(grouped[key]);
              if (agencies.length > 0) {
                hierarchical.TERRITOIRE[key] = {
                  name: key,
                  agencies: agencies,
                  totals: this.calculateZoneTotals(agencies)
                };
              }
            });
            
            this.hierarchicalDataFromBackend = hierarchical;
          } else if (data.hierarchicalData) {
            this.hierarchicalDataFromBackend = data.hierarchicalData;
            
            if (data.hierarchicalData.TERRITOIRE) {
              if (data.hierarchicalData.TERRITOIRE) {
              // Support des nouvelles clés de zones
              const dakar_centre_ville = data.hierarchicalData.TERRITOIRE.dakar_centre_ville || data.hierarchicalData.TERRITOIRE.territoire_dakar_ville || { name: 'DAKAR CENTRE VILLE', agencies: [] };
              const dakar_banlieue = data.hierarchicalData.TERRITOIRE.dakar_banlieue || data.hierarchicalData.TERRITOIRE.territoire_dakar_banlieue || { name: 'DAKAR BANLIEUE', agencies: [] };
              const province_centre_sud = data.hierarchicalData.TERRITOIRE.province_centre_sud || data.hierarchicalData.TERRITOIRE.territoire_province_centre_sud || { name: 'PROVINCE CENTRE SUD', agencies: [] };
              const province_nord = data.hierarchicalData.TERRITOIRE.province_nord || data.hierarchicalData.TERRITOIRE.territoire_province_nord || { name: 'PROVINCE NORD', agencies: [] };
              const grand_compte = data.hierarchicalData.TERRITOIRE.grand_compte || { name: 'GRAND COMPTE', agencies: [] };
              
              const rawAgenciesDakarCentreVille = dakar_centre_ville.agencies || dakar_centre_ville.data || [];
              const rawAgenciesDakarBanlieue = dakar_banlieue.agencies || dakar_banlieue.data || [];
              const rawAgenciesProvinceCentreSud = province_centre_sud.agencies || province_centre_sud.data || [];
              const rawAgenciesProvinceNord = province_nord.agencies || province_nord.data || [];
              const rawAgenciesGrandCompte = grand_compte.agencies || grand_compte.data || [];
              
              const filteredDakarCentreVille = this.filterAgencies(rawAgenciesDakarCentreVille);
              const filteredDakarBanlieue = this.filterAgencies(rawAgenciesDakarBanlieue);
              const filteredProvinceCentreSud = this.filterAgencies(rawAgenciesProvinceCentreSud);
              const filteredProvinceNord = this.filterAgencies(rawAgenciesProvinceNord);
              const filteredGrandCompte = this.filterAgencies(rawAgenciesGrandCompte);
              
              this.territories = {
                territoire_dakar_ville: {
                  ...dakar_centre_ville,
                  name: dakar_centre_ville.name || 'DAKAR CENTRE VILLE',
                  agencies: filteredDakarCentreVille
                },
                territoire_dakar_banlieue: {
                  ...dakar_banlieue,
                  name: dakar_banlieue.name || 'DAKAR BANLIEUE',
                  agencies: filteredDakarBanlieue
                },
                territoire_province_centre_sud: {
                  ...province_centre_sud,
                  name: province_centre_sud.name || 'PROVINCE CENTRE SUD',
                  agencies: filteredProvinceCentreSud
                },
                territoire_province_nord: {
                  ...province_nord,
                  name: province_nord.name || 'PROVINCE NORD',
                  agencies: filteredProvinceNord
                },
                grand_compte: {
                  ...grand_compte,
                  name: grand_compte.name || 'GRAND COMPTE',
                  agencies: filteredGrandCompte
                }
              };
              }
              
              if (data.globalResult) {
                this.globalResult = {
                  mois: data.globalResult.mois || 0,
                  mois1: data.globalResult.mois1 || 0,
                  evolution: data.globalResult.evolution || 0
                };
              }
            }
          } else if (data.territories) {
            // Support des anciennes et nouvelles clés pour compatibilité
            const dakarVille = data.territories.dakar_centre_ville || data.territories.territoire_dakar_ville || { name: 'DAKAR CENTRE VILLE', agencies: [] };
            const dakarBanlieue = data.territories.dakar_banlieue || data.territories.territoire_dakar_banlieue || { name: 'DAKAR BANLIEUE', agencies: [] };
            const provinceCentreSud = data.territories.province_centre_sud || data.territories.territoire_province_centre_sud || { name: 'PROVINCE CENTRE SUD', agencies: [] };
            const provinceNord = data.territories.province_nord || data.territories.territoire_province_nord || { name: 'PROVINCE NORD', agencies: [] };
            
            this.territories = {
              dakar_centre_ville: {
                ...dakarVille,
                name: dakarVille.name || 'DAKAR CENTRE VILLE',
                agencies: this.filterAgencies(dakarVille.agencies || dakarVille.data || [])
              },
              dakar_banlieue: {
                ...dakarBanlieue,
                name: dakarBanlieue.name || 'DAKAR BANLIEUE',
                agencies: this.filterAgencies(dakarBanlieue.agencies || dakarBanlieue.data || [])
              },
              province_centre_sud: {
                ...provinceCentreSud,
                name: provinceCentreSud.name || 'PROVINCE CENTRE SUD',
                agencies: this.filterAgencies(provinceCentreSud.agencies || provinceCentreSud.data || [])
              },
              province_nord: {
                ...provinceNord,
                name: provinceNord.name || 'PROVINCE NORD',
                agencies: this.filterAgencies(provinceNord.agencies || provinceNord.data || [])
              },
              // Garder les anciennes clés pour compatibilité
              territoire_dakar_ville: {
                ...dakarVille,
                name: dakarVille.name || 'DAKAR CENTRE VILLE',
                agencies: this.filterAgencies(dakarVille.agencies || dakarVille.data || [])
              },
              territoire_dakar_banlieue: {
                ...dakarBanlieue,
                name: dakarBanlieue.name || 'DAKAR BANLIEUE',
                agencies: this.filterAgencies(dakarBanlieue.agencies || dakarBanlieue.data || [])
              },
              territoire_province_centre_sud: {
                ...provinceCentreSud,
                name: provinceCentreSud.name || 'PROVINCE CENTRE SUD',
                agencies: this.filterAgencies(provinceCentreSud.agencies || provinceCentreSud.data || [])
              },
              territoire_province_nord: {
                ...provinceNord,
                name: provinceNord.name || 'PROVINCE NORD',
                agencies: this.filterAgencies(provinceNord.agencies || provinceNord.data || [])
              }
            };
            
            if (data.globalResult) {
              this.globalResult = {
                mois: data.globalResult.mois || 0,
                mois1: data.globalResult.mois1 || 0,
                evolution: data.globalResult.evolution || 0
              };
            }
          } else {
            this.territories = {
              territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
              territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
              territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
              territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
            };
            this.globalResult = { mois: 0, mois1: 0, evolution: 0 };
          }
        } else {
          this.territories = {
            territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
            territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
            territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
            territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
          };
          this.globalResult = { mois: 0, mois1: 0, evolution: 0 };
        }

        if (this.hierarchicalDataFromBackend) {
          await this.loadObjectives();
        }
      } catch (error) {
        this.territories = {
          territoire_dakar_ville: { name: 'TERRITOIRE DAKAR VILLE', agencies: [] },
          territoire_dakar_banlieue: { name: 'TERRITOIRE DAKAR BANLIEUE', agencies: [] },
          territoire_province_centre_sud: { name: 'TERRITOIRE PROVINCE CENTRE-SUD', agencies: [] },
          territoire_province_nord: { name: 'TERRITOIRE PROVINCE NORD', agencies: [] }
        };
        this.globalResult = { mois: 0, mois1: 0, evolution: 0 };
        
        const status = error.response?.status;
        const raw = error.response?.data;
        const fromJson = raw && typeof raw === 'object'
          ? (raw.message || raw.detail || raw.error || '')
          : (typeof raw === 'string' ? raw : '');
        if (status) {
          const hint = (status === 502 || status === 504)
            ? ' (souvent : timeout proxy/nginx ou PHP — la requête collection est longue)'
            : '';
          this.errorMessage = `Erreur HTTP ${status}${hint}. ${fromJson || error.message || 'Échec de /api/oracle/data/collection'}`;
        } else if (error.code === 'ECONNABORTED' || (error.message && String(error.message).toLowerCase().includes('timeout'))) {
          this.errorMessage = 'La requête a pris trop de temps (timeout). La collecte est lourde : augmentez les timeouts côté serveur (nginx, PHP-FPM) ou Python.';
        } else if (error.message === 'Network Error' || !error.response) {
          this.errorMessage = `Erreur réseau ou pas de réponse du serveur : ${error.message || 'inconnue'}. Vérifiez PYTHON_SERVICE_URL, le firewall et les logs Laravel/Python.`;
        } else {
          this.errorMessage = fromJson || error.message || 'Erreur lors du chargement des données depuis Oracle.';
        }
      } finally {
        // Mettre en cache les données pour l'onglet actif
        if (this.activeTab === 'collecte' || this.activeTab === 'solde') {
          const cacheKey = this.generateCacheKey();
          this.tabDataCache[this.activeTab] = {
            cacheKey: cacheKey,
            hierarchicalData: this.hierarchicalDataFromBackend,
            chargeAffaireDetails: this.chargeAffaireDetails,
            territories: this.territories
          };
        }
        this.loading = false;
      }
    },
    generateCacheKey() {
      // Générer une clé de cache basée sur les paramètres de filtrage
      const parts = [
        this.selectedPeriod,
        this.selectedZone || 'all',
        this.selectedYear,
        this.selectedMonth,
        this.selectedWeek,
        this.selectedDate
      ];
      return parts.join('|');
    },
    loadDataForPeriod() {
      // Réinitialiser les données pour forcer la mise à jour
      this.hierarchicalDataFromBackend = null;
      this.territories = {};
      this.chargeAffaireDetails = {};
      this.chargeAffaireDetailsCache.clear(); // Vider le cache
      this.expandedAgencyLines = {}; // Vider le cache des lignes expandées
      // Réinitialiser les sections expandées
      this.expandedSections = {
        TERRITOIRE: false,
        'TERRITOIRE_territoire_dakar_ville': false,
        'TERRITOIRE_territoire_dakar_banlieue': false,
        'TERRITOIRE_territoire_province_centre_sud': false,
        'TERRITOIRE_territoire_province_nord': false
      };
      this.fetchDataFromOracle();
    },
    handlePeriodChange() {
      this.loadDataForPeriod();
    },
    handleMonthChange() {
      this.loadDataForPeriod();
    },
    handleYearChange() {
      this.loadDataForPeriod();
    },
    handleDateChange() {
      this.updateWeekFromDate();
      this.$nextTick(() => {
        this.loadDataForPeriod();
      });
    },
    async loadObjectives() {
      try {
        const token = localStorage.getItem('token');
        if (!token) {
          return;
        }

        const params = {
          type: 'COLLECT',
          year: this.selectedYear
        };

        if (this.selectedPeriod === 'month') {
          params.period = 'month';
          params.month = this.selectedMonth;
        } else if (this.selectedPeriod === 'year') {
          params.period = 'year';
        } else if (this.selectedPeriod === 'week') {
          params.period = 'month';
          if (this.selectedDate) {
            const date = new Date(this.selectedDate);
            params.month = date.getMonth() + 1;
          }
        }

        const response = await window.axios.get('/api/objectives', {
          params: params,
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });

        if (response.data && response.data.success && response.data.data) {
          const objectives = Array.isArray(response.data.data) ? response.data.data : [response.data.data];
          const objectivesMapByCode = {};
          const objectivesMapByName = {};
          objectives.forEach(obj => {
            const agencyCode = (obj.agency_code || '').toString().trim();
            const agencyName = (obj.agency_name || '').toString().trim();
            const value = obj.value || 0;
            if (agencyCode) {
              objectivesMapByCode[agencyCode] = value;
            }
            if (agencyName) {
              objectivesMapByName[agencyName.toUpperCase().trim()] = value;
            }
          });

          this.mergeObjectivesWithOracleData(objectivesMapByCode, objectivesMapByName);
        }
      } catch (error) {
        console.warn('Erreur lors du chargement des objectifs collecte:', error);
      }
    },
    mergeObjectivesWithOracleData(objectivesMapByCode, objectivesMapByName) {
      const applyToAgency = (agency) => {
        const agencyCode = (agency.CODE_AGENCE || agency.code_agence || agency.code || agency.CODE || '').toString().trim();
        const agencyName = (agency.name || agency.AGENCE || agency.NOM_AGENCE || '').toString().trim();
        let objectiveValue = null;
        if (agencyCode && objectivesMapByCode[agencyCode]) {
          objectiveValue = objectivesMapByCode[agencyCode];
        } else if (agencyName) {
          const normalizedName = agencyName.toUpperCase().trim();
          if (objectivesMapByName[normalizedName]) {
            objectiveValue = objectivesMapByName[normalizedName];
          }
        }
        if (objectiveValue !== null) {
          agency.objectif = objectiveValue;
          agency.OBJECTIF = objectiveValue;
        }
      };

      const h = this.hierarchicalDataFromBackend;
      if (!h) return;

      if (h.TERRITOIRE) {
        Object.keys(h.TERRITOIRE).forEach(territoryKey => {
          const territory = h.TERRITOIRE[territoryKey];
          if (territory && territory.agencies && Array.isArray(territory.agencies)) {
            territory.agencies.forEach(applyToAgency);
          }
        });
      }

      this.refreshZoneTotalsAfterObjectives();
      this.$nextTick(() => {
        this.$forceUpdate();
      });
    },
    refreshZoneTotalsAfterObjectives() {
      const h = this.hierarchicalDataFromBackend;
      if (!h) return;

      if (h.TERRITOIRE) {
        Object.keys(h.TERRITOIRE).forEach(k => {
          const zone = h.TERRITOIRE[k];
          if (zone && zone.agencies && Array.isArray(zone.agencies)) {
            zone.totals = this.calculateZoneTotals(zone.agencies);
          }
        });
      }
    }
  }
}
</script>

<style scoped>
.collection-section {
  margin-bottom: 30px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.table-section-title {
  font-size: 20px;
  font-weight: 600;
  margin: 30px 0 15px 0;
  color: #10B981;
  padding-bottom: 10px;
  border-bottom: 2px solid #10B981;
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

.global-result-section {
  margin-bottom: 40px;
}

.loading-message {
  background: #E3F2FD;
  border: 1px solid #2196F3;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  text-align: center;
  color: #1976D2;
  font-weight: 500;
}

.error-message {
  background: #FFEBEE;
  border: 1px solid #F44336;
  border-radius: 4px;
  padding: 15px;
  margin-bottom: 20px;
  text-align: center;
  color: #C62828;
  font-weight: 500;
}

.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.tabs-menu {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid #e5e7eb;
}

.tab-button {
  padding: 12px 24px;
  font-size: 16px;
  font-weight: 600;
  background: transparent;
  border: none;
  border-bottom: 3px solid transparent;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.3s ease;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #10B981;
  background: #f0fdf4;
}

.tab-button.active {
  color: #10B981;
  border-bottom-color: #10B981;
  background: #f0fdf4;
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

.total-row {
  background: #F5F5F5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
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
  background: #E3F2FD;
  font-weight: 600;
  border-left: 4px solid #2196F3;
}

.level-3 {
  padding-left: 48px !important;
  color: #333;
  cursor: pointer;
  font-weight: normal;
  display: flex;
  align-items: center;
  gap: 8px;
}

.level-3-row:hover {
  background: #BBDEFB;
}

.level-4-row {
  background-color: #fafafa;
  font-size: 0.9em;
}

.level-4-row:hover {
  background-color: #f0f0f0;
}

.charge-detail-row {
  background-color: #f9f9f9;
  border-left: 3px solid #1A4D3A;
}

.charge-detail-row:hover {
  background-color: #f0f0f0;
}

.level-4 {
  padding-left: 60px !important;
  font-style: italic;
  color: #666;
}

.grand-compte-row {
  background: white;
  font-weight: normal;
}

.grand-compte-row td {
  color: #333;
  font-weight: normal;
}

.selected-agency {
  background: #e3f2fd !important;
  border-left: 4px solid #1A4D3A;
}

.expand-btn {
  width: 24px;
  height: 24px;
  border: 1px solid #1A4D3A;
  background: #1A4D3A;
  color: white;
  border-radius: 3px;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 16px;
  flex-shrink: 0;
  transition: background 0.2s;
  margin-right: 8px;
  vertical-align: middle;
}

.expand-btn:hover {
  background: #0d3320;
  border-color: #0d3320;
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

.chart-evolution-section {
  margin-top: 30px;
  background: white;
  border: 1px solid #DDD;
  border-radius: 4px;
  padding: 20px;
  width: 100%;
  max-width: 100%;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.chart-title-section {
  flex: 1;
}

.chart-section-title {
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #333;
}

.breadcrumb {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #666;
  flex-wrap: wrap;
}

.breadcrumb-item {
  cursor: pointer;
  color: #1A4D3A;
  transition: color 0.2s;
}

.breadcrumb-item:hover {
  color: #0d3320;
  text-decoration: underline;
}

.breadcrumb-item.active {
  color: #333;
  font-weight: 600;
  cursor: default;
}

.breadcrumb-item.active:hover {
  text-decoration: none;
}

.breadcrumb-separator {
  color: #999;
}

.chart-actions {
  display: flex;
  gap: 8px;
}

.export-btn {
  padding: 6px 12px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: background 0.2s;
}

.export-btn:hover {
  background: #153d2a;
}

.chart-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #DDD;
  margin-bottom: 20px;
}

.chart-tab {
  padding: 10px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.2s;
}

.chart-tab:hover {
  color: #1A4D3A;
  background: #f5f5f5;
}

.chart-tab.active {
  color: #1A4D3A;
  font-weight: 600;
  border-bottom-color: #1A4D3A;
  background: transparent;
}

.chart-view-tabs {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  padding: 0;
  border-bottom: 2px solid #DDD;
}

.chart-view-tab {
  padding: 12px 24px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: #666;
  border-bottom: 3px solid transparent;
  transition: all 0.3s ease;
  position: relative;
}

.chart-view-tab:hover {
  color: #1A4D3A;
  background: #f5f5f5;
}

.chart-view-tab.active {
  color: #1A4D3A;
  font-weight: 600;
  border-bottom-color: #1A4D3A;
  background: transparent;
}

.data-type-selector {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
  padding: 10px;
  background: #f9f9f9;
  border-radius: 4px;
}

.data-type-selector label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
}

.data-type-selector input[type="radio"] {
  cursor: pointer;
  accent-color: #1A4D3A;
}

.chart-wrapper-container {
  width: 100% !important;
  min-height: 500px;
  height: 600px;
  max-height: 800px;
  position: relative;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  overflow: hidden;
}

/* Media Queries pour le responsive */

/* Tablettes */
@media (max-width: 1200px) {
  .kpi-row {
    grid-template-columns: repeat(3, 1fr);
    gap: 15px;
  }
  
  .section-header {
    flex-wrap: wrap;
    gap: 15px;
  }
  
  .chart-wrapper-container {
    min-height: 450px;
    height: 550px;
    max-height: 700px;
  }
}

/* Tablettes en mode portrait et petits écrans */
@media (max-width: 768px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }
  
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    padding: 15px;
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
  
  .table-container {
    overflow-x: scroll;
  }
  
  .chart-wrapper-container {
    min-height: 400px;
    max-height: 500px;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .chart-actions {
    width: 100%;
    justify-content: flex-end;
  }
  
  .chart-tabs {
    flex-wrap: wrap;
  }
  
  .chart-tab {
    padding: 8px 16px;
    font-size: 13px;
  }
}

/* Petits mobiles */
@media (max-width: 480px) {
  .kpi-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }
  
  .section-header {
    padding: 12px;
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
  }
  
  .chart-tabs {
    flex-direction: column;
  }
  
  .chart-tab {
    width: 100%;
    text-align: left;
  }
  
  .chart-wrapper-container {
    min-height: 350px;
    max-height: 450px;
  }
}
</style>
