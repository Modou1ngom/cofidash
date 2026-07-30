<template>
  <div class="caf-overview-page">
    <header class="page-header">
      <div class="header-text">
        <div class="hero-badge">Portefeuille crédit</div>
        <h1>Vue d'ensemble CAF</h1>
        <p v-if="chargeAffaireLabel" class="subtitle">{{ chargeAffaireLabel }}</p>
        <p v-else-if="selectedCafCode" class="subtitle">Code gestionnaire : {{ selectedCafCode }}</p>
      </div>

      <div class="filters">
        <label class="filter-field">
          <span>Mois</span>
          <select v-model.number="selectedMonth" @change="onFilterChange">
            <option v-for="m in monthOptions" :key="m.value" :value="m.value">{{ m.label }}</option>
          </select>
        </label>
        <label class="filter-field">
          <span>Année</span>
          <select v-model.number="selectedYear" @change="onFilterChange">
            <option v-for="y in yearOptions" :key="y" :value="y">{{ y }}</option>
          </select>
        </label>
        <label v-if="showCafSelector" class="filter-field filter-field--wide">
          <span>Chargé d'affaires</span>
          <select v-model="selectedCafCode" @change="onFilterChange" :disabled="managersLoading">
            <option value="">Sélectionner un CAF…</option>
            <option
              v-for="mgr in managers"
              :key="mgr.code_gestion_pret"
              :value="mgr.code_gestion_pret"
            >
              {{ mgr.charge_affaire }} ({{ mgr.code_gestion_pret }})
            </option>
          </select>
        </label>
        <button type="button" class="refresh-btn" :disabled="loading || refreshing" @click="loadOverview({ force: true })">
          <span v-if="loading && !overview" class="btn-spinner" />
          <span v-else-if="refreshing" class="btn-spinner btn-spinner--subtle" />
          {{ loading && !overview ? 'Chargement…' : refreshing ? 'Mise à jour…' : 'Actualiser' }}
        </button>
      </div>
    </header>

    <p v-if="error" class="error-banner">{{ error }}</p>
    <p v-else-if="!selectedCafCode && !loading" class="info-banner">
      Sélectionnez un chargé d'affaires pour afficher la vue d'ensemble.
    </p>

    <div v-if="loading && !overview" class="loading-state">
      <div v-for="n in 4" :key="n" class="skeleton-card" />
    </div>

    <template v-else-if="overview">
      <section class="kpi-grid">
        <article v-for="card in kpiCards" :key="card.id" class="kpi-card">
          <span class="kpi-label">{{ card.label }}</span>
          <strong class="kpi-value">{{ card.value }}</strong>
          <span class="kpi-meta">{{ card.meta }}</span>
          <button type="button" class="kpi-detail-btn" @click="openDetail(card.id)">
            Voir détails
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
              <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
        </article>
      </section>

      <Teleport to="body">
        <div v-if="activeDetail" class="detail-overlay" @click.self="closeDetail">
          <div class="detail-modal" role="dialog" aria-modal="true" :aria-labelledby="`detail-title-${activeDetail}`">
            <header class="detail-modal-head">
              <button
                v-if="loanDetailReturn && activeDetail === 'loan'"
                type="button"
                class="detail-back"
                aria-label="Retour"
                @click="closeLoanDetail"
              >
                ←
              </button>
              <h2 :id="`detail-title-${activeDetail}`">{{ detailTitle }}</h2>
              <button type="button" class="detail-close" aria-label="Fermer" @click="closeDetail">×</button>
            </header>
            <div class="detail-modal-body">
              <!-- Détail prêt -->
              <template v-if="activeDetail === 'loan'">
                <div v-if="loanDetailLoading" class="empty-state compact">Chargement du prêt…</div>
                <p v-else-if="loanDetailError" class="loan-detail-error">{{ loanDetailError }}</p>
                <template v-else-if="loanDetail">
                  <div class="loan-panel">
                    <header class="loan-panel-head">
                      <div class="loan-panel-identity">
                        <h3 class="loan-panel-name">{{ loanDetail.client_name || 'Client' }}</h3>
                        <span class="loan-panel-ref">{{ loanDetail.loan_number }}</span>
                      </div>
                      <div class="loan-panel-badges">
                        <span class="loan-badge loan-badge--status">{{ loanStatusLabel(loanDetail) }}</span>
                        <span
                          class="loan-badge"
                          :class="`loan-badge--${loanDetail.health_status || 'sain'}`"
                        >
                          {{ healthLabel(loanDetail.health_status) }}
                        </span>
                        <span v-if="loanDetail.par_days != null" class="loan-badge loan-badge--par">
                          {{ loanDetail.par_days }} j. PAR
                        </span>
                      </div>
                    </header>

                    <div class="loan-kpis">
                      <div class="loan-kpi loan-kpi--primary">
                        <span class="loan-kpi-label">Encours total</span>
                        <strong class="loan-kpi-value">{{ formatMoney(loanDetail.total_outstanding || loanDetail.outstanding) }}</strong>
                      </div>
                      <div
                        class="loan-kpi"
                        :class="{ 'loan-kpi--danger': (loanDetail.unpaid_amount || 0) > 0 }"
                      >
                        <span class="loan-kpi-label">Impayé</span>
                        <strong class="loan-kpi-value">{{ formatMoney(loanDetail.unpaid_amount) }}</strong>
                      </div>
                      <div class="loan-kpi">
                        <span class="loan-kpi-label">Montant financé</span>
                        <strong class="loan-kpi-value">{{ formatMoney(loanDetail.financed_amount) }}</strong>
                      </div>
                    </div>

                    <div class="loan-repayment">
                      <div class="loan-repayment-head">
                        <span>Taux de remboursement</span>
                        <strong>{{ loanDetail.repayment_percent ?? 0 }} %</strong>
                      </div>
                      <div class="loan-repayment-bar" role="presentation">
                        <div
                          class="loan-repayment-fill"
                          :style="{ width: `${Math.min(100, loanDetail.repayment_percent || 0)}%` }"
                        />
                      </div>
                    </div>

                    <div class="loan-sections">
                      <section class="loan-section">
                        <h4 class="loan-section-title">Produit & suivi</h4>
                        <dl class="loan-info-grid">
                          <div class="loan-info-item loan-info-item--wide">
                            <dt>Type de prêt</dt>
                            <dd>{{ creditProductLabel(loanDetail) }}</dd>
                          </div>
                          <div class="loan-info-item">
                            <dt>Agence</dt>
                            <dd>{{ loanDetail.agency || '—' }}</dd>
                          </div>
                          <div class="loan-info-item">
                            <dt>Chargé d'affaires</dt>
                            <dd>{{ loanDetail.manager || '—' }}</dd>
                          </div>
                        </dl>
                      </section>

                      <section class="loan-section">
                        <h4 class="loan-section-title">Échéances & compte</h4>
                        <dl class="loan-info-grid">
                          <div class="loan-info-item">
                            <dt>Décaissement</dt>
                            <dd>{{ formatDate(loanDetail.disbursement_date) }}</dd>
                          </div>
                          <div class="loan-info-item">
                            <dt>Échéance</dt>
                            <dd>{{ formatDate(loanDetail.maturity_date) }}</dd>
                          </div>
                          <div class="loan-info-item">
                            <dt>Prochaine échéance</dt>
                            <dd>{{ formatDate(loanDetail.next_due_date) }}</dd>
                          </div>
                          <div class="loan-info-item">
                            <dt>Compte lié</dt>
                            <dd class="loan-info-mono">{{ loanDetail.linked_account || '—' }}</dd>
                          </div>
                          <div class="loan-info-item">
                            <dt>Solde compte</dt>
                            <dd>{{ formatMoney(loanDetail.account_balance) }}</dd>
                          </div>
                        </dl>
                      </section>
                    </div>

                    <footer v-if="loanDetail.client_id" class="loan-panel-foot">
                      <button type="button" class="btn-client-link" @click="goToClientFiche">
                        Voir fiche client →
                      </button>
                    </footer>
                  </div>
                </template>
              </template>

              <template v-else>
              <!-- Encours total -->
              <template v-if="activeDetail === 'encours'">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Période</span>
                    <strong>{{ periodLabel }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Encours M-1</span>
                    <strong>{{ formatMoney(portefeuillePrev.encours_total) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Variation</span>
                    <strong :class="trendClass(comparison.encours_mom_pct)">
                      {{ formatTrend(comparison.encours_mom_pct) }}
                    </strong>
                  </div>
                </div>
                <h3 class="detail-section-title">Évolution sur 12 mois</h3>
                <div v-if="encoursEvolutionChart.length" class="evo-chart">
                  <div
                    v-for="point in encoursEvolutionChart"
                    :key="point.label"
                    class="evo-bar-wrap"
                    :title="`${point.label} : ${formatMoney(point.value)}`"
                  >
                    <div class="evo-bar" :style="{ height: `${point.percent}%` }" />
                    <span class="evo-label">{{ point.shortLabel }}</span>
                  </div>
                </div>
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Encours impayé</span>
                    <strong>{{ formatMoney(portefeuille.encours_impaye) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Ratio impayé</span>
                    <strong>{{ formatPercent(portefeuille.ratio_encours_impaye) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Agence</span>
                    <strong>{{ portefeuille.branch_name || '—' }}</strong>
                  </div>
                </div>
              </template>

              <!-- PAR global -->
              <template v-else-if="activeDetail === 'par'">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>PAR global</span>
                    <strong>{{ formatPercent(parGlobalRate) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>PAR M-1</span>
                    <strong>{{ formatPercent(parGlobalRatePrev) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Évolution</span>
                    <strong :class="trendClass(-comparison.par_mom_pct)">
                      {{ formatParTrend(comparison.par_mom_pct) }} pts
                    </strong>
                  </div>
                </div>
                <h3 class="detail-section-title">Répartition par palier</h3>
                <div class="par-bar detail-par-bar">
                  <div
                    v-for="bucket in parBuckets"
                    :key="bucket.key"
                    class="par-segment"
                    :style="{ width: `${bucket.share}%`, background: bucket.color }"
                  />
                </div>
                <div class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Palier</th>
                        <th class="num">Taux</th>
                        <th class="num">Encours</th>
                        <th class="num">Dossiers</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="bucket in parBuckets" :key="bucket.key">
                        <td>
                          <span class="par-dot inline" :style="{ background: bucket.color }" />
                          {{ bucket.label }}
                        </td>
                        <td class="num">{{ formatPercent(bucket.rate) }}</td>
                        <td class="num">{{ formatMoney(bucket.encours) }}</td>
                        <td class="num">{{ formatCount(bucket.dossiers) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>

              <!-- Détail palier PAR -->
              <template v-else-if="activeDetail === 'par_bucket' && selectedParBucket">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Palier</span>
                    <strong>
                      <span class="par-dot inline" :style="{ background: selectedParBucket.color }" />
                      {{ selectedParBucket.label }}
                    </strong>
                  </div>
                  <div class="detail-stat">
                    <span>Taux PAR</span>
                    <strong>{{ formatPercent(selectedParBucket.rate) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Encours</span>
                    <strong>{{ formatMoney(selectedParBucket.encours) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Dossiers</span>
                    <strong>{{ formatCount(selectedParBucket.dossiers) }}</strong>
                  </div>
                </div>

                <h3 class="detail-section-title">Top encours — {{ selectedParBucket.label }}</h3>
                <div v-if="!selectedParTopEncours.length" class="empty-state compact">Aucun dossier.</div>
                <div v-else class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Client</th>
                        <th>N° dossier</th>
                        <th class="num">Encours</th>
                        <th class="num">Exigible</th>
                        <th class="num">Jours</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="row in selectedParTopEncours"
                        :key="`${selectedParBucket.key}-${row.rank}`"
                        class="loan-row"
                        tabindex="0"
                        role="button"
                        @click="openLoanDetail(row.loan_number)"
                        @keydown.enter="openLoanDetail(row.loan_number)"
                      >
                        <td>{{ row.rank }}</td>
                        <td>{{ row.client_name }}</td>
                        <td>{{ row.loan_number }}</td>
                        <td class="num">{{ formatMoney(row.outstanding) }}</td>
                        <td class="num">{{ formatMoney(row.exigible) }}</td>
                        <td class="num">{{ row.par_days }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                <h3 class="detail-section-title">Entrées en PAR — {{ selectedParBucket.label }}</h3>
                <div v-if="!selectedParEntrees.length" class="empty-state compact">Aucune entrée sur ce palier.</div>
                <div v-else class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>N° dossier</th>
                        <th>Client</th>
                        <th class="num">Montant</th>
                        <th class="num">Jours</th>
                        <th>Statut</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="row in selectedParEntrees"
                        :key="row.loan_number"
                        class="loan-row"
                        tabindex="0"
                        role="button"
                        @click="openLoanDetail(row.loan_number)"
                        @keydown.enter="openLoanDetail(row.loan_number)"
                      >
                        <td>{{ row.loan_number }}</td>
                        <td>{{ row.client_name }}</td>
                        <td class="num">{{ formatMoney(row.outstanding) }}</td>
                        <td class="num">{{ row.par_days }}</td>
                        <td>
                          <span v-if="row.declassement_status" class="status-pill">{{ row.declassement_status }}</span>
                          <span v-else>—</span>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>

              <!-- Production -->
              <template v-else-if="activeDetail === 'production'">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Volume mois</span>
                    <strong>{{ formatMoney(production.monthly_volume) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Volume M-1</span>
                    <strong>{{ formatMoney(production.monthly_volume_prev) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Nombre prêts</span>
                    <strong>{{ formatCount(production.loan_count) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Prêts M-1</span>
                    <strong>{{ formatCount(production.loan_count_prev) }}</strong>
                  </div>
                </div>
                <h3 class="detail-section-title">Décaissements du mois</h3>
                <div v-if="!productionLoans.length" class="empty-state compact">Aucun décaissement.</div>
                <div v-else class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>N° dossier</th>
                        <th>Client</th>
                        <th>Date</th>
                        <th class="num">Montant</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="loan in productionLoans"
                        :key="loan.loan_number"
                        class="loan-row"
                        tabindex="0"
                        role="button"
                        @click="openLoanDetail(loan.loan_number)"
                        @keydown.enter="openLoanDetail(loan.loan_number)"
                      >
                        <td>{{ loan.loan_number }}</td>
                        <td>{{ loan.client_name }}</td>
                        <td>{{ formatDate(loan.disbursement_date) }}</td>
                        <td class="num">{{ formatMoney(loan.outstanding) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>

              <!-- New Deal -->
              <template v-else-if="activeDetail === 'new_deal'">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Nombre New Deal</span>
                    <strong>{{ formatCount(newDeal.loan_count) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Volume financé</span>
                    <strong>{{ formatMoney(newDeal.monthly_volume) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Objectif</span>
                    <strong>{{ formatCount(newDeal.loan_count_objective) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Réalisation</span>
                    <strong>{{ formatPercent(newDeal.loan_count_realization_pct) }}</strong>
                  </div>
                </div>
                <h3 class="detail-section-title">New Deal du mois</h3>
                <div v-if="!newDealLoans.length" class="empty-state compact">Aucun New Deal sur la période.</div>
                <div v-else class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>N° dossier</th>
                        <th>Client</th>
                        <th>Date</th>
                        <th class="num">Montant</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="loan in newDealLoans"
                        :key="loan.loan_number"
                        class="loan-row"
                        tabindex="0"
                        role="button"
                        @click="openLoanDetail(loan.loan_number)"
                        @keydown.enter="openLoanDetail(loan.loan_number)"
                      >
                        <td>{{ loan.loan_number }}</td>
                        <td>{{ loan.client_name }}</td>
                        <td>{{ formatDate(loan.disbursement_date) }}</td>
                        <td class="num">{{ formatMoney(loan.outstanding) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>

              <!-- Dossiers portefeuille -->
              <template v-else-if="activeDetail === 'dossiers'">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Total dossiers</span>
                    <strong>{{ formatCount(portefeuille.nombre_dossier) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Dossiers impayés (%)</span>
                    <strong>{{ formatPercent(portefeuille.ratio_nombre_impaye) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Encours impayé</span>
                    <strong>{{ formatMoney(portefeuille.encours_impaye) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Encours sain</span>
                    <strong>{{ formatMoney(encoursSain) }}</strong>
                  </div>
                </div>
                <h3 class="detail-section-title">Top encours (tous paliers)</h3>
                <div v-if="!allTopEncours.length" class="empty-state compact">Aucun dossier.</div>
                <div v-else class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>Palier</th>
                        <th>Client</th>
                        <th>N° dossier</th>
                        <th class="num">Encours</th>
                        <th class="num">Jours</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="row in allTopEncours"
                        :key="`${row.parKey}-${row.loan_number}`"
                        class="loan-row"
                        tabindex="0"
                        role="button"
                        @click="openLoanDetail(row.loan_number)"
                        @keydown.enter="openLoanDetail(row.loan_number)"
                      >
                        <td>{{ row.parLabel }}</td>
                        <td>{{ row.client_name }}</td>
                        <td>{{ row.loan_number }}</td>
                        <td class="num">{{ formatMoney(row.outstanding) }}</td>
                        <td class="num">{{ row.par_days }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>

              <!-- Provisions -->
              <template v-else-if="activeDetail === 'provisions'">
                <div class="detail-kpi-row">
                  <div class="detail-stat">
                    <span>Total provisions</span>
                    <strong>{{ formatMoney(portefeuille.provision_total) }}</strong>
                  </div>
                  <div class="detail-stat">
                    <span>Dossiers listés</span>
                    <strong>{{ formatCount(topProvisions.length) }}</strong>
                  </div>
                </div>
                <h3 class="detail-section-title">Top montants à provisionner</h3>
                <div v-if="!topProvisions.length" class="empty-state compact">Aucune provision.</div>
                <div v-else class="detail-table-wrap">
                  <table>
                    <thead>
                      <tr>
                        <th>#</th>
                        <th>Client</th>
                        <th>N° dossier</th>
                        <th class="num">Provision</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="row in topProvisions"
                        :key="`${row.rank}-${row.loan_number}`"
                        class="loan-row"
                        tabindex="0"
                        role="button"
                        @click="openLoanDetail(row.loan_number)"
                        @keydown.enter="openLoanDetail(row.loan_number)"
                      >
                        <td>{{ row.rank }}</td>
                        <td>{{ row.client_name }}</td>
                        <td>{{ row.loan_number }}</td>
                        <td class="num">{{ formatMoney(row.provision_total) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </template>
              </template>
            </div>
          </div>
        </div>
      </Teleport>

      <section ref="sectionPar" class="panel">
        <div class="panel-head">
          <h2>Répartition des PAR</h2>
          <span class="panel-sub">{{ periodLabel }}</span>
        </div>
        <div v-if="parBuckets.length" class="par-bar" role="presentation">
          <button
            v-for="bucket in parBuckets"
            :key="bucket.key"
            type="button"
            class="par-segment"
            :style="{ width: `${bucket.share}%`, background: bucket.color }"
            :title="`${bucket.label} : ${formatPercent(bucket.rate)} — voir détails`"
            @click="openParDetail(bucket.key)"
          />
        </div>
        <div class="par-grid">
          <button
            v-for="bucket in parBuckets"
            :key="bucket.key"
            type="button"
            class="par-item par-item--clickable"
            @click="openParDetail(bucket.key)"
          >
            <span class="par-dot" :style="{ background: bucket.color }" />
            <div class="par-info">
              <strong>{{ bucket.label }}</strong>
            </div>
            <div class="par-stats">
              <span>{{ formatPercent(bucket.rate) }}</span>
              <span>{{ formatMoney(bucket.encours) }}</span>
              <span class="par-count">{{ formatCount(bucket.dossiers) }} doss.</span>
              <span class="par-item-action" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </div>
          </button>
        </div>
      </section>

      <section class="panel">
        <div class="panel-head">
          <h2>Entrées en PAR</h2>
          <span class="panel-sub">Nouveaux dossiers par palier</span>
        </div>
        <div class="tabs" role="tablist">
          <button
            v-for="bucket in parBucketDefs"
            :key="bucket.key"
            type="button"
            class="tab"
            :class="{ active: activeEntreeTab === bucket.key }"
            @click="activeEntreeTab = bucket.key"
          >
            {{ bucket.label }}
            <span class="tab-badge">{{ entreesCount(bucket.key) }}</span>
          </button>
        </div>
        <div v-if="!activeEntrees.length" class="empty-state">Aucune entrée PAR sur ce palier.</div>
        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>N° dossier</th>
                <th>Client</th>
                <th class="num">Montant</th>
                <th class="num">Jours</th>
                <th>Statut</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="row in activeEntrees"
                :key="row.loan_number"
                class="loan-row"
                tabindex="0"
                role="button"
                @click="openLoanDetail(row.loan_number)"
                @keydown.enter="openLoanDetail(row.loan_number)"
              >
                <td>{{ row.loan_number }}</td>
                <td>{{ row.client_name }}</td>
                <td class="num">{{ formatMoney(row.outstanding) }}</td>
                <td class="num">{{ row.par_days }}</td>
                <td>
                  <span v-if="row.declassement_status" class="status-pill">{{ row.declassement_status }}</span>
                  <span v-else>—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </template>
  </div>
</template>

<script>
import {
  getCachedManagers,
  getCachedOverview,
  isOverviewCacheFresh,
  setCachedManagers,
  setCachedOverview,
} from '../utils/cafOverviewCache.js';

const PAR_BUCKET_DEFS = [
  { key: 'par_0', label: 'PAR 0', daysLabel: '> 0 jour', color: '#16a34a' },
  { key: 'par_30', label: 'PAR 30', daysLabel: '> 30 jours', color: '#ca8a04' },
  { key: 'par_90', label: 'PAR 90', daysLabel: '> 90 jours', color: '#ea580c' },
  { key: 'par_180', label: 'PAR 180', daysLabel: '> 180 jours', color: '#dc2626' },
  { key: 'par_360', label: 'PAR 360', daysLabel: '> 360 jours', color: '#7f1d1d' },
];

const MONTH_LABELS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
];

function readStoredUser() {
  try {
    const raw = localStorage.getItem('user');
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export default {
  name: 'CafVueEnsemblePage',
  data() {
    const now = new Date();
    return {
      loading: false,
      refreshing: false,
      managersLoading: false,
      error: '',
      overview: null,
      managers: [],
      selectedMonth: now.getMonth() + 1,
      selectedYear: now.getFullYear(),
      selectedCafCode: '',
      activeEntreeTab: 'par_0',
      activeDetail: null,
      activeParBucket: null,
      loanDetailReturn: null,
      loanDetail: null,
      loanDetailLoading: false,
      loanDetailError: '',
      parBucketDefs: PAR_BUCKET_DEFS,
      user: readStoredUser(),
    };
  },
  computed: {
    isCaf() {
      return (this.user?.profile?.code || '').toUpperCase() === 'CAF';
    },
    userManagerCode() {
      return String(this.user?.manager_code || '').trim();
    },
    showCafSelector() {
      return !this.isCaf || !this.userManagerCode;
    },
    monthOptions() {
      return MONTH_LABELS.map((label, index) => ({
        value: index + 1,
        label,
      }));
    },
    yearOptions() {
      const current = new Date().getFullYear();
      return [current - 2, current - 1, current, current + 1];
    },
    periodLabel() {
      const month = MONTH_LABELS[(this.selectedMonth || 1) - 1] || '';
      return `${month} ${this.selectedYear}`;
    },
    portefeuille() {
      return this.overview?.portefeuille || {};
    },
    portefeuillePrev() {
      return this.overview?.portefeuille_prev || {};
    },
    production() {
      return this.overview?.production || {};
    },
    comparison() {
      return this.overview?.comparison || {};
    },
    productionLoans() {
      return this.overview?.production_loans || [];
    },
    newDeal() {
      return this.overview?.new_deal || {};
    },
    newDealLoans() {
      return this.overview?.new_deal_loans || [];
    },
    topProvisions() {
      return this.overview?.top_provisions || [];
    },
    chargeAffaireLabel() {
      return this.overview?.charge_affaire || this.portefeuille?.charge_affaire || '';
    },
    parGlobalRate() {
      return this.computeParGlobalRate(this.portefeuille);
    },
    parGlobalRatePrev() {
      return this.computeParGlobalRate(this.portefeuillePrev);
    },
    encoursSain() {
      const total = Number(this.portefeuille.encours_total) || 0;
      const impaye = Number(this.portefeuille.encours_impaye) || 0;
      return Math.max(total - impaye, 0);
    },
    kpiCards() {
      const nd = this.newDeal;
      const ndCount = Number(nd.loan_count) || 0;
      const ndObj = Number(nd.loan_count_objective) || 0;
      let newDealMeta = `${this.formatMoney(nd.monthly_volume)} financés`;
      if (ndObj > 0) {
        const vsObj = Math.round(((ndCount / ndObj) - 1) * 100);
        const sign = vsObj > 0 ? '+' : '';
        newDealMeta = `${sign}${vsObj}% vs obj · ${this.formatMoney(nd.monthly_volume)}`;
      }
      return [
        {
          id: 'encours',
          label: 'Encours total',
          value: this.formatMoney(this.portefeuille.encours_total),
        },
        {
          id: 'par',
          label: 'PAR global',
          value: this.formatPercent(this.parGlobalRate),
        },
        {
          id: 'production',
          label: 'Production du mois',
          value: this.formatMoney(this.production.monthly_volume),
          meta: `${this.formatCount(this.production.loan_count)} dossier(s)`,
        },
        {
          id: 'new_deal',
          label: 'Nombre New Deal',
          value: this.formatCount(ndCount),
          meta: newDealMeta,
        },
        {
          id: 'dossiers',
          label: 'Dossiers portefeuille',
          value: this.formatCount(this.portefeuille.nombre_dossier),
          meta: `Impayé : ${this.formatMoney(this.portefeuille.encours_impaye)}`,
        },
        {
          id: 'provisions',
          label: 'Provisions',
          value: this.formatMoney(this.portefeuille.provision_total),
        },
      ];
    },
    detailTitle() {
      if (this.activeDetail === 'loan') {
        const num = this.loanDetail?.loan_number || '';
        return num ? `Détail prêt — ${num}` : 'Détail prêt';
      }
      if (this.activeDetail === 'par_bucket' && this.selectedParBucket) {
        return `Détail — ${this.selectedParBucket.label}`;
      }
      const titles = {
        encours: 'Détail — Encours total',
        par: 'Détail — PAR global',
        production: 'Détail — Production du mois',
        new_deal: 'Détail — New Deal',
        dossiers: 'Détail — Dossiers portefeuille',
        provisions: 'Détail — Provisions',
      };
      return titles[this.activeDetail] || '';
    },
    encoursEvolutionChart() {
      const values = this.overview?.encours_evolution || [];
      const rolling = this.rollingMonthYears(this.selectedMonth, this.selectedYear, 12);
      const points = rolling.map((my, index) => ({
        label: `${MONTH_LABELS[my.month - 1]} ${my.year}`,
        shortLabel: `${MONTH_LABELS[my.month - 1].slice(0, 3)}.`,
        value: Number(values[index]) || 0,
      }));
      const max = Math.max(...points.map((p) => p.value), 1);
      return points.map((p) => ({ ...p, percent: Math.round((p.value / max) * 100) }));
    },
    allTopEncours() {
      const map = this.overview?.top_encours || {};
      const rows = [];
      PAR_BUCKET_DEFS.forEach((def) => {
        (map[def.key] || []).forEach((row) => {
          rows.push({ ...row, parKey: def.key, parLabel: def.label });
        });
      });
      return rows.sort((a, b) => (Number(b.outstanding) || 0) - (Number(a.outstanding) || 0));
    },
    parBuckets() {
      const p = this.portefeuille;
      const counts = this.overview?.par_dossier_counts || {};
      // Taux cumulatifs → bandes disjointes pour la barre (visuel proportionnel)
      const keys = PAR_BUCKET_DEFS.map((d) => d.key);
      const rates = keys.map((k) => Number(p[k]) || 0);
      const bands = rates.map((rate, i) => {
        const next = i + 1 < rates.length ? rates[i + 1] : 0;
        return Math.max(rate - next, 0);
      });
      const bandSum = bands.reduce((a, b) => a + b, 0);
      return PAR_BUCKET_DEFS.map((def, i) => {
        const rate = rates[i];
        const encours = Number(p[`encours_${def.key}`]) || 0;
        const dossiers = Number(counts[def.key]) || 0;
        return {
          ...def,
          rate,
          encours,
          dossiers,
          share: bandSum > 0 ? (bands[i] / bandSum) * 100 : 0,
        };
      });
    },
    activeEntrees() {
      const map = this.overview?.entrees_par || {};
      return map[this.activeEntreeTab] || [];
    },
    selectedParBucket() {
      if (!this.activeParBucket) return null;
      return this.parBuckets.find((b) => b.key === this.activeParBucket) || null;
    },
    selectedParTopEncours() {
      if (!this.activeParBucket) return [];
      return this.topEncoursFor(this.activeParBucket);
    },
    selectedParEntrees() {
      if (!this.activeParBucket) return [];
      return (this.overview?.entrees_par || {})[this.activeParBucket] || [];
    },
  },
  mounted() {
    this.initFromRoute();
    this.bootstrap();
    this._onKeydown = (e) => {
      if (e.key === 'Escape') this.closeDetail();
    };
    document.addEventListener('keydown', this._onKeydown);
  },
  beforeUnmount() {
    document.removeEventListener('keydown', this._onKeydown);
    document.body.classList.remove('caf-detail-open');
  },
  watch: {
    '$route.query'() {
      this.initFromRoute();
      if (this.selectedCafCode) {
        this.applyCachedOverview();
        this.loadOverview({ force: !this.overview });
      }
    },
  },
  methods: {
    async bootstrap() {
      if (this.isCaf && this.userManagerCode) {
        this.selectedCafCode = this.userManagerCode;
      } else if (this.showCafSelector) {
        await this.loadManagers();
        if (!this.selectedCafCode && this.managers.length === 1) {
          this.selectedCafCode = this.managers[0].code_gestion_pret;
        }
      }
      if (this.selectedCafCode) {
        this.applyCachedOverview();
        await this.loadOverview({ background: Boolean(this.overview) });
      }
    },
    initFromRoute() {
      const q = this.$route.query;
      if (q.month) this.selectedMonth = Number(q.month);
      if (q.year) this.selectedYear = Number(q.year);
      if (q.caf_code) this.selectedCafCode = String(q.caf_code);
    },
    syncRouteQuery() {
      const query = {
        month: String(this.selectedMonth),
        year: String(this.selectedYear),
      };
      if (this.selectedCafCode) {
        query.caf_code = this.selectedCafCode;
      }
      this.$router.replace({ path: '/vue360/caf', query }).catch(() => {});
    },
    onFilterChange() {
      this.syncRouteQuery();
      if (this.selectedCafCode) {
        this.loadOverview({ force: true });
      }
    },
    applyCachedOverview() {
      const cached = getCachedOverview(
        this.selectedCafCode,
        this.selectedMonth,
        this.selectedYear,
      );
      if (cached?.data) {
        this.overview = cached.data;
        return true;
      }
      return false;
    },
    async loadManagers() {
      const cached = getCachedManagers();
      if (cached) {
        this.managers = cached;
        return;
      }
      this.managersLoading = true;
      try {
        const response = await window.axios.get('/api/v1/dashboard/caf-managers');
        this.managers = response.data?.data || response.data || [];
        setCachedManagers(this.managers);
      } catch (err) {
        this.error = err.response?.data?.message || 'Impossible de charger la liste des CAF.';
      } finally {
        this.managersLoading = false;
      }
    },
    async loadOverview({ background = false, force = false } = {}) {
      if (!this.selectedCafCode) return;

      const cached = getCachedOverview(
        this.selectedCafCode,
        this.selectedMonth,
        this.selectedYear,
      );
      if (cached?.data && !force) {
        this.overview = cached.data;
        if (isOverviewCacheFresh(cached) && !background) {
          this.loading = false;
          this.refreshing = false;
          return;
        }
      }

      if (!this.overview && !background) {
        this.loading = true;
      } else {
        this.refreshing = true;
      }
      this.error = '';

      try {
        const response = await window.axios.get('/api/v1/dashboard/caf-overview', {
          params: {
            caf_code: this.selectedCafCode,
            month: this.selectedMonth,
            year: this.selectedYear,
          },
        });
        const payload = response.data?.data || null;
        this.overview = payload;
        if (!payload) {
          this.error = 'Aucune donnée reçue.';
        } else {
          setCachedOverview(
            this.selectedCafCode,
            this.selectedMonth,
            this.selectedYear,
            payload,
          );
        }
      } catch (err) {
        if (!this.overview) {
          this.error = err.response?.data?.message || 'Erreur lors du chargement de la vue d\'ensemble.';
        }
      } finally {
        this.loading = false;
        this.refreshing = false;
      }
    },
    topEncoursFor(key) {
      return (this.overview?.top_encours || {})[key] || [];
    },
    entreesCount(key) {
      return ((this.overview?.entrees_par || {})[key] || []).length;
    },
    computeParGlobalRate(p) {
      if (!p || !Object.keys(p).length) return 0;
      const explicit = Number(p.par_global);
      if (explicit > 0) return explicit;
      // PAR cumulatif : Global = PAR 0
      const par0 = Number(p.par_0);
      if (par0 > 0) return par0;
      const encours = Number(p.encours_total) || 0;
      const risque = Number(p.encours_risque) || 0;
      if (risque > 0 && encours > 0) return (risque / encours) * 100;
      const impaye = Number(p.encours_impaye) || 0;
      return encours > 0 ? (impaye / encours) * 100 : 0;
    },
    rollingMonthYears(endMonth, endYear, count = 12) {
      const months = [];
      let m = endMonth;
      let y = endYear;
      for (let i = 0; i < count; i += 1) {
        months.push({ month: m, year: y });
        m -= 1;
        if (m < 1) {
          m = 12;
          y -= 1;
        }
      }
      return months.reverse();
    },
    openDetail(id) {
      if (id !== 'par_bucket') {
        this.activeParBucket = null;
      }
      this.loanDetailReturn = null;
      this.loanDetail = null;
      this.loanDetailError = '';
      this.activeDetail = id;
      document.body.classList.add('caf-detail-open');
    },
    openParDetail(key) {
      this.activeParBucket = key;
      this.openDetail('par_bucket');
    },
    async openLoanDetail(loanNumber) {
      const id = String(loanNumber || '').trim();
      if (!id) return;

      if (this.activeDetail && this.activeDetail !== 'loan') {
        this.loanDetailReturn = {
          activeDetail: this.activeDetail,
          activeParBucket: this.activeParBucket,
        };
      } else {
        this.loanDetailReturn = null;
      }

      this.activeDetail = 'loan';
      this.loanDetail = null;
      this.loanDetailError = '';
      this.loanDetailLoading = true;
      document.body.classList.add('caf-detail-open');

      try {
        const response = await window.axios.get(`/api/v1/credits/${encodeURIComponent(id)}`);
        const payload = response.data?.data ?? response.data;
        if (!payload || !payload.loan_number) {
          this.loanDetailError = 'Prêt introuvable.';
          return;
        }
        this.loanDetail = payload;
      } catch (err) {
        const status = err?.response?.status;
        this.loanDetailError = status === 404
          ? 'Prêt introuvable.'
          : 'Impossible de charger le détail du prêt.';
      } finally {
        this.loanDetailLoading = false;
      }
    },
    closeLoanDetail() {
      if (this.loanDetailReturn) {
        this.activeDetail = this.loanDetailReturn.activeDetail;
        this.activeParBucket = this.loanDetailReturn.activeParBucket;
        this.loanDetailReturn = null;
      } else {
        this.activeDetail = null;
        this.activeParBucket = null;
        document.body.classList.remove('caf-detail-open');
      }
      this.loanDetail = null;
      this.loanDetailError = '';
      this.loanDetailLoading = false;
    },
    closeDetail() {
      this.loanDetailReturn = null;
      this.loanDetail = null;
      this.loanDetailError = '';
      this.loanDetailLoading = false;
      this.activeDetail = null;
      this.activeParBucket = null;
      document.body.classList.remove('caf-detail-open');
    },
    goToClientFiche() {
      const clientId = this.loanDetail?.client_id;
      if (!clientId) return;
      this.closeDetail();
      this.$router.push(`/vue360/clients/${encodeURIComponent(clientId)}`);
    },
    healthLabel(status) {
      if (status === 'sain') return 'Sain';
      if (status === 'impaye') return 'Impayé';
      if (status === 'solde') return 'Soldé';
      return status || '—';
    },
    creditProductLabel(credit) {
      const label = String(credit?.product_type || '').trim();
      const code = String(credit?.product_code || '').trim();
      if (label && label !== code && !/^\d+$/.test(label)) return label;
      if (code && !/^\d+$/.test(code)) return code;
      if (code) return `Produit ${code}`;
      return 'Crédit';
    },
    loanStatusLabel(credit) {
      const flex = {
        A: 'Financé',
        L: 'Soldé',
        V: 'Annulé',
        Y: 'Futur déblocage',
        H: 'En attente',
      };
      const code = String(credit?.account_status || '').toUpperCase();
      if (flex[code]) return flex[code];
      return this.healthLabel(credit?.health_status);
    },
    formatMoney(value) {
      const n = Number(value) || 0;
      return `${n.toLocaleString('fr-FR')} FCFA`;
    },
    formatPercent(value) {
      const n = Number(value) || 0;
      return `${n.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`;
    },
    formatCount(value) {
      const n = Number(value) || 0;
      return n.toLocaleString('fr-FR', { maximumFractionDigits: 0 });
    },
    formatDate(value) {
      if (!value) return '—';
      const d = new Date(value);
      if (Number.isNaN(d.getTime())) return String(value);
      return d.toLocaleDateString('fr-FR');
    },
    formatTrend(value) {
      const n = Number(value) || 0;
      const sign = n > 0 ? '+' : '';
      return `${sign}${n.toLocaleString('fr-FR', { maximumFractionDigits: 1 })} %`;
    },
    formatParTrend(value) {
      const n = Number(value) || 0;
      const sign = n > 0 ? '+' : '';
      return `${sign}${n.toLocaleString('fr-FR', { maximumFractionDigits: 1 })}`;
    },
    trendClass(value) {
      const n = Number(value) || 0;
      if (n > 0) return 'trend-up';
      if (n < 0) return 'trend-down';
      return 'trend-flat';
    },
  },
};
</script>

<style scoped>
.caf-overview-page {
  padding: 1.5rem 1.75rem 2.5rem;
  min-height: 100%;
  background: #eef1f4;
}

.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1.25rem;
  margin-bottom: 1.5rem;
}

.hero-badge {
  display: inline-block;
  padding: 0.25rem 0.65rem;
  border-radius: 999px;
  background: rgba(26, 77, 58, 0.1);
  color: #1a4d3a;
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  margin-bottom: 0.5rem;
}

.page-header h1 {
  margin: 0;
  font-size: 1.65rem;
  color: #0f172a;
}

.subtitle {
  margin: 0.35rem 0 0;
  color: #64748b;
  font-size: 0.95rem;
}

.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: 0.75rem;
}

.filter-field {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: #64748b;
}

.filter-field select {
  min-width: 8.5rem;
  padding: 0.55rem 0.75rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.5rem;
  background: #fff;
  color: #0f172a;
  font-size: 0.9rem;
}

.filter-field--wide select {
  min-width: 18rem;
}

.refresh-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.55rem 1rem;
  border: none;
  border-radius: 0.5rem;
  background: #1a4d3a;
  color: #fff;
  font-weight: 600;
  cursor: pointer;
}

.refresh-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.error-banner,
.info-banner {
  padding: 0.85rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
}

.error-banner {
  background: #fef2f2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.info-banner {
  background: #eff6ff;
  color: #1d4ed8;
  border: 1px solid #bfdbfe;
}

.loading-state {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.skeleton-card {
  height: 110px;
  border-radius: 0.75rem;
  background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 50%, #e2e8f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 1rem;
  margin-bottom: 1.25rem;
  align-items: stretch;
}

.kpi-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1rem 1.1rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
  display: flex;
  flex-direction: column;
  height: 100%;
}

.kpi-detail-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  margin-top: auto;
  padding-top: 0.75rem;
  padding: 0.4rem 0.65rem;
  border: 1px solid #cbd5e1;
  border-radius: 0.45rem;
  background: #f8fafc;
  color: #1a4d3a;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
}

.kpi-detail-btn:hover {
  background: #ecfdf5;
  border-color: #1a4d3a;
}

.kpi-detail-btn svg {
  width: 14px;
  height: 14px;
}

.kpi-label {
  display: block;
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 0.35rem;
}

.kpi-value {
  display: block;
  font-size: 1.15rem;
  color: #0f172a;
  line-height: 1.3;
}

.kpi-meta,
.kpi-trend {
  display: block;
  min-height: 1.15rem;
  margin-top: 0.35rem;
  font-size: 0.78rem;
  color: #64748b;
}

.trend-up { color: #16a34a; }
.trend-down { color: #dc2626; }
.trend-flat { color: #64748b; }

.panel {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 0.75rem;
  padding: 1.1rem 1.25rem;
  margin-bottom: 1.25rem;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.panel-head h2 {
  margin: 0;
  font-size: 1.05rem;
  color: #0f172a;
}

.panel-sub {
  font-size: 0.85rem;
  color: #64748b;
}

.par-bar {
  display: flex;
  height: 10px;
  border-radius: 999px;
  overflow: hidden;
  background: #f1f5f9;
  margin-bottom: 1rem;
}

.par-segment {
  min-width: 2px;
  padding: 0;
  border: none;
  cursor: pointer;
  transition: width 0.2s ease, opacity 0.15s ease;
}

.par-segment:hover {
  opacity: 0.85;
}

.par-grid {
  display: grid;
  gap: 0.65rem;
}

.par-item {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 0.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.par-item--clickable {
  width: 100%;
  border: none;
  border-bottom: 1px solid #f1f5f9;
  background: transparent;
  text-align: left;
  font: inherit;
  cursor: pointer;
  border-radius: 0.45rem;
  transition: background 0.15s;
}

.par-item--clickable:hover {
  background: #f1f5f9;
}

.par-item--clickable:last-child {
  border-bottom: none;
}

.par-item-action {
  display: inline-flex;
  align-items: center;
  color: #94a3b8;
  margin-left: 0.25rem;
}

.par-item-action svg {
  width: 16px;
  height: 16px;
}

.par-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.par-info {
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
}

.par-info strong {
  font-size: 0.9rem;
  color: #0f172a;
}

.par-info span {
  font-size: 0.78rem;
  color: #94a3b8;
}

.par-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  justify-content: flex-end;
  font-size: 0.85rem;
  color: #334155;
}

.par-count {
  color: #64748b;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.88rem;
}

th,
td {
  padding: 0.55rem 0.65rem;
  text-align: left;
  border-bottom: 1px solid #f1f5f9;
}

th {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #64748b;
  font-weight: 600;
}

td.num,
th.num {
  text-align: right;
  white-space: nowrap;
}

.empty-state {
  padding: 1.25rem;
  text-align: center;
  color: #94a3b8;
  font-size: 0.9rem;
}

.empty-state.compact {
  padding: 0.75rem;
}

.status-pill {
  display: inline-block;
  padding: 0.15rem 0.45rem;
  border-radius: 999px;
  border: 1px solid #ea580c;
  color: #c2410c;
  font-size: 0.75rem;
  font-weight: 600;
  background: #fff7ed;
}

.tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.45rem 0.75rem;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  background: #f8fafc;
  color: #334155;
  font-size: 0.85rem;
  cursor: pointer;
}

.tab.active {
  background: #1a4d3a;
  border-color: #1a4d3a;
  color: #fff;
}

.tab-badge {
  display: inline-flex;
  min-width: 1.25rem;
  justify-content: center;
  padding: 0.1rem 0.35rem;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.12);
  font-size: 0.75rem;
}

.tab.active .tab-badge {
  background: rgba(255, 255, 255, 0.2);
}

.btn-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.btn-spinner--subtle {
  border-color: rgba(255, 255, 255, 0.25);
  border-top-color: rgba(255, 255, 255, 0.9);
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.detail-overlay {
  position: fixed;
  inset: 0;
  z-index: 1200;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.25rem;
  background: rgba(15, 23, 42, 0.45);
  backdrop-filter: blur(2px);
}

.detail-modal {
  width: min(920px, 100%);
  max-height: min(88vh, 900px);
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 0.85rem;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.2);
  overflow: hidden;
}

.detail-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #e2e8f0;
  background: #f8fafc;
}

.detail-modal-head h2 {
  margin: 0;
  flex: 1;
  min-width: 0;
  font-size: 1.05rem;
  color: #0f172a;
}

.detail-close {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.4rem;
  background: transparent;
  color: #64748b;
  font-size: 1.5rem;
  line-height: 1;
  cursor: pointer;
}

.detail-close:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.detail-modal-body {
  padding: 1.1rem 1.25rem 1.25rem;
  overflow-y: auto;
}

.detail-section-title {
  margin: 1.25rem 0 0.75rem;
  font-size: 0.9rem;
  color: #334155;
}

.detail-kpi-row {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 0.75rem;
}

.detail-stat {
  padding: 0.75rem 0.85rem;
  border: 1px solid #e2e8f0;
  border-radius: 0.55rem;
  background: #f8fafc;
}

.detail-stat span {
  display: block;
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.25rem;
}

.detail-stat strong {
  font-size: 0.95rem;
  color: #0f172a;
}

.detail-par-bar {
  margin-bottom: 1rem;
}

.detail-table-wrap {
  overflow-x: auto;
  border: 1px solid #e2e8f0;
  border-radius: 0.55rem;
}

.detail-table-wrap table {
  margin: 0;
}

.par-dot.inline {
  display: inline-block;
  vertical-align: middle;
  margin-right: 0.35rem;
}

.evo-chart {
  display: flex;
  align-items: flex-end;
  gap: 0.35rem;
  height: 140px;
  padding: 0.5rem 0;
}

.evo-bar-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  height: 100%;
  min-width: 0;
}

.evo-bar {
  width: 100%;
  max-width: 36px;
  min-height: 4px;
  border-radius: 4px 4px 0 0;
  background: linear-gradient(180deg, #1a4d3a, #2d6a4f);
  transition: height 0.2s ease;
}

.evo-label {
  margin-top: 0.35rem;
  font-size: 0.65rem;
  color: #94a3b8;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 100%;
}

.detail-back {
  flex-shrink: 0;
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 0.4rem;
  background: transparent;
  color: #475569;
  font-size: 1.1rem;
  line-height: 1;
  cursor: pointer;
}

.detail-back:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.loan-row {
  cursor: pointer;
  transition: background 0.12s ease;
}

.loan-row:hover,
.loan-row:focus-visible {
  background: #f1f5f9;
  outline: none;
}

.loan-panel {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.loan-panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e2e8f0;
}

.loan-panel-identity {
  min-width: 0;
}

.loan-panel-name {
  margin: 0 0 0.25rem;
  font-size: 1.15rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.3;
}

.loan-panel-ref {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.82rem;
  color: #64748b;
  letter-spacing: 0.02em;
}

.loan-panel-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 0.4rem;
}

.loan-badge {
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 600;
  line-height: 1.2;
  white-space: nowrap;
}

.loan-badge--status {
  background: #e0f2fe;
  color: #0369a1;
}

.loan-badge--sain {
  background: #dcfce7;
  color: #166534;
}

.loan-badge--impaye {
  background: #fee2e2;
  color: #991b1b;
}

.loan-badge--solde {
  background: #e5e7eb;
  color: #374151;
}

.loan-badge--par {
  background: #fef3c7;
  color: #92400e;
}

.loan-kpis {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;
}

@media (max-width: 560px) {
  .loan-kpis {
    grid-template-columns: 1fr;
  }
}

.loan-kpi {
  padding: 0.85rem 1rem;
  border-radius: 0.65rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.loan-kpi--primary {
  background: linear-gradient(135deg, #f0fdf4 0%, #ecfdf5 100%);
  border-color: #bbf7d0;
}

.loan-kpi--primary .loan-kpi-value {
  color: #166534;
}

.loan-kpi--danger .loan-kpi-value {
  color: #b91c1c;
}

.loan-kpi-label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #94a3b8;
}

.loan-kpi-value {
  display: block;
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  line-height: 1.25;
}

.loan-repayment {
  padding: 0.85rem 1rem;
  border-radius: 0.65rem;
  background: #fff;
  border: 1px solid #e2e8f0;
}

.loan-repayment-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 0.55rem;
  font-size: 0.82rem;
  color: #64748b;
}

.loan-repayment-head strong {
  font-size: 0.95rem;
  color: #0f172a;
}

.loan-repayment-bar {
  height: 6px;
  border-radius: 999px;
  background: #e2e8f0;
  overflow: hidden;
}

.loan-repayment-fill {
  height: 100%;
  border-radius: 999px;
  background: linear-gradient(90deg, #1a4d3a, #16a34a);
  transition: width 0.3s ease;
}

.loan-sections {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

@media (max-width: 640px) {
  .loan-sections {
    grid-template-columns: 1fr;
  }
}

.loan-section {
  padding: 1rem;
  border-radius: 0.65rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
}

.loan-section-title {
  margin: 0 0 0.85rem;
  font-size: 0.78rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: #64748b;
}

.loan-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0.75rem 1rem;
  margin: 0;
}

.loan-info-item {
  margin: 0;
  min-width: 0;
}

.loan-info-item--wide {
  grid-column: 1 / -1;
}

.loan-info-item dt {
  margin: 0 0 0.2rem;
  font-size: 0.72rem;
  font-weight: 500;
  color: #94a3b8;
}

.loan-info-item dd {
  margin: 0;
  font-size: 0.88rem;
  font-weight: 600;
  color: #1e293b;
  line-height: 1.4;
  word-break: break-word;
}

.loan-info-mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 0.84rem;
  font-weight: 500;
}

.loan-detail-error {
  margin: 0;
  padding: 0.75rem;
  border-radius: 0.5rem;
  background: #fef2f2;
  color: #b91c1c;
  font-size: 0.9rem;
}

.loan-panel-foot {
  padding-top: 0.25rem;
  border-top: 1px solid #e2e8f0;
}

.btn-client-link {
  padding: 0.55rem 1rem;
  border: 1px solid #1a4d3a;
  border-radius: 0.5rem;
  background: #fff;
  color: #1a4d3a;
  font-size: 0.88rem;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s, color 0.15s;
}

.btn-client-link:hover {
  background: #1a4d3a;
  color: #fff;
}
</style>

<style>
body.caf-detail-open {
  overflow: hidden;
}
</style>
