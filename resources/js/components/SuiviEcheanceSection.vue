<template>
  <section class="echeance">
    <header class="head">
      <div class="head-top">
     
        <div class="segment" role="tablist" aria-label="Affichage">
          <button type="button" :class="{ on: view === 'dashboard' }" @click="view = 'dashboard'">Dashboard</button>
          <button type="button" :class="{ on: view === 'detail' }" @click="view = 'detail'">Détail</button>
          <button type="button" :class="{ on: view === 'performance' }" @click="view = 'performance'">Performance</button>
         <!-- <button type="button" :class="{ on: view === 'promesses' }" @click="view = 'promesses'">Promesses</button>-->
        </div>
        <label class="chip chip-year">
          <span>Année</span>
          <select v-model.number="year" @change="load">
            <option v-for="item in years" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label class="chip chip-month">
          <span>Mois</span>
          <select v-model.number="month" @change="load">
            <option v-for="item in monthOptions" :key="item.value" :value="item.value">{{ item.label }}</option>
          </select>
        </label>
        <button type="button" class="refresh" :disabled="loading" title="Actualiser" @click="reload">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
            <path d="M20 12a8 8 0 1 1-2.2-5.5" stroke-linecap="round" />
            <path d="M20 4v5h-5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
        </button>
      </div>
      <div v-if="view !== 'objectif' && view !== 'promesses'" class="filters">
        <label class="chip">
          <span>Agence</span>
          <select v-model="agence" @change="page = 1">
            <option value="">Toutes</option>
            <option v-for="item in agencyOptions" :key="item.code" :value="item.code">{{ item.label }}</option>
          </select>
        </label>
        <label class="chip">
          <span>CAF</span>
          <select v-model="caf" @change="page = 1">
            <option value="">Tous</option>
            <option v-for="item in cafOptions" :key="item" :value="item">{{ item }}</option>
          </select>
        </label>
        <label class="chip">
          <span>Semaine</span>
          <select v-model="week" @change="page = 1">
            <option value="">Toutes</option>
            <option v-for="item in weekCards" :key="item.key" :value="item.key">{{ item.label }} · {{ item.range }}</option>
          </select>
        </label>
        <label class="chip">
          <span>Statut</span>
          <select v-model="status" @change="page = 1">
            <option value="">Tous</option>
            <option value="I">Impayé</option>
            <option value="R">Remboursé</option>
            <option value="A">Échéance A</option>
            <option value="none">Sans échéance du mois</option>
          </select>
        </label>
      </div>
    </header>

    <p v-if="error" class="banner error">{{ error }}</p>
    <p v-else-if="warning" class="banner warn">{{ warning }}</p>
    <p v-else-if="loading && !rows.length" class="banner">Chargement du suivi échéance…</p>
    <p v-else-if="!loading && rows.length && !rowsInObjectif.length" class="banner warn">
      Aucun prêt du tombé du mois ne figure dans l'objectif de recouvrement. Ces dossiers ne sont pas affichés.
    </p>

    <div v-if="view === 'dashboard' && rowsInObjectif.length" class="kpis">
      <article
        v-for="card in kpiCards"
        :key="card.key"
        class="kpi-card"
        :class="{ on: activeKpi === card.key }"
        :style="{ '--accent': card.accent }"
        role="button"
        tabindex="0"
        :aria-label="`Détail ${card.label}`"
        @click="openKpi(card.key)"
        @keydown.enter.prevent="openKpi(card.key)"
      >
        <span class="kpi-top">
          <i class="kpi-icon" aria-hidden="true" v-html="kpiIcon(card.key)"></i>
          <span>{{ card.label }}</span>
        </span>
        <strong>{{ formatKpi(card) }}</strong>
        <small>
          {{ card.unit }}
          <em v-if="card.share != null">{{ formatPercent(card.share) }}</em>
        </small>
      </article>
      <article
        v-for="card in formulaCards"
        :key="card.key"
        :style="{ '--accent': card.accent }"
      >
        <span class="kpi-top">
          <i class="kpi-icon" aria-hidden="true" v-html="kpiIcon(card.key)"></i>
          <span>{{ card.label }}</span>
        </span>
        <strong>{{ formatKpi(card) }}</strong>
        <small>{{ card.unit }}</small>
      </article>
    </div>

    <div v-if="view === 'dashboard' && activeKpiCard" class="kpi-overlay" @click.self="closeKpi">
      <section class="kpi-panel" role="dialog" aria-modal="true" :aria-label="activeKpiCard.label">
        <header class="kpi-panel-head">
          <div>
            <p>Détail</p>
            <h3>{{ activeKpiCard.label }}</h3>
          </div>
          <button type="button" class="kpi-close" aria-label="Fermer" @click="closeKpi">×</button>
        </header>
        <div class="kpi-panel-stats">
          <p>
            <span>{{ activeKpiCard.money === false ? 'Dossiers' : 'Montant' }}</span>
            <strong>{{ formatKpi(activeKpiCard) }}</strong>
          </p>
          <p><span>Lignes</span><strong>{{ formatCount(kpiDetailRows.length) }}</strong></p>
        </div>
        <label class="kpi-search">
          <span>Recherche</span>
          <input v-model.trim="kpiQuery" type="search" placeholder="N° de prêt, client, agence" @input="kpiPage = 1">
        </label>
        <div class="kpi-panel-table">
          <table>
            <thead>
              <tr>
                <th>N° prêt</th>
                <th>Matricule</th>
                <th>Client</th>
                <th>Compte</th>
                <th class="num">Objectif</th>
                <th class="num">Réalisé du mois</th>
                <th class="num">Global dû</th>
                <th>Déblocage</th>
                <th class="num">Capital accordé</th>
                <th class="num">Encours total</th>
                <th class="num">% remb.</th>
                <th>Statut prêt</th>
                <th>Statut déclassement</th>
                <th>Code gestion</th>
                <th>CAF</th>
                <th class="num">Solde dépôt garantie</th>
                <th>Date échéance</th>
                <th class="num">N° échéance</th>
                <th class="num">Solde compte</th>
                <th class="num">Montant échéance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, index) in kpiPageRows" :key="row.no_pret ? rowKey(row) : `${row.account_number}-${index}`">
                <td>{{ row.no_pret || row.account_number || '—' }}</td>
                <td>{{ lineOf(row).matricule_client || '—' }}</td>
                <td>{{ lineOf(row).nom_client || '—' }}</td>
                <td>{{ lineOf(row).compte || '—' }}</td>
                <td class="num">{{ formatMoney(objectifOf(row)) }}</td>
                <td class="num">{{ formatMoney(realiseCell(row)) }}</td>
                <td class="num">{{ formatMoney(globalDuCell(row)) }}</td>
                <td>{{ formatDate(lineOf(row).date_deblocage) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).montant_capital_accorde) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).encours_total) }}</td>
                <td class="num">{{ formatPercent(lineOf(row).pourcentage_remboursement) }}</td>
                <td>{{ lineOf(row).statut_pret || row.statut_pret || '—' }}</td>
                <td>{{ lineOf(row).statut_declassement || '—' }}</td>
                <td>{{ lineOf(row).code_gestion_pret || '—' }}</td>
                <td>{{ lineOf(row).charge_affaire || '—' }}</td>
                <td class="num">{{ formatMoney(lineOf(row).solde_depot_garantie) }}</td>
                <td>{{ formatDate(lineOf(row).schedule_due_date) }}</td>
                <td class="num">{{ lineOf(row).numero_echeance ?? '—' }}</td>
                <td class="num">{{ formatMoney(lineOf(row).solde_cpte) }}</td>
                <td class="num">{{ formatMoney(lineOf(row).montant_echeance_m) }}</td>
              </tr>
              <tr v-if="!kpiPageRows.length">
                <td colspan="20" class="empty">Aucune ligne pour cet indicateur.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer v-if="kpiPageCount > 1" class="pager">
          <button type="button" :disabled="kpiPage <= 1" @click="kpiPage -= 1">Précédent</button>
          <span>{{ kpiPage }} / {{ kpiPageCount }}</span>
          <button type="button" :disabled="kpiPage >= kpiPageCount" @click="kpiPage += 1">Suivant</button>
        </footer>
      </section>
    </div>

    <div v-if="view === 'dashboard' && rowsInObjectif.length" class="grid-2">
      <article class="panel">
        <header class="panel-head">
          <h2>Échéances par agence</h2>
        </header>
        <div v-if="agencyBars.length" class="chart-scroll">
          <div class="chart-box tall" :style="{ width: agencyChartWidth }">
            <canvas ref="barCanvas"></canvas>
          </div>
        </div>
        <p v-else class="empty">Aucune échéance pour cette sélection.</p>
        <ul v-if="agencyBars.length" class="inline-legend stack-legend">
          <li v-for="item in weekSeries" :key="item.key">
            <span class="swatch square" :style="{ background: item.color }"></span>
            {{ item.label }}
          </li>
          <li>
            <span class="swatch line"></span>
            Objectif
          </li>
        </ul>
      </article>

      <article class="panel">
        <header class="panel-head">
          <h2>Répartition par statut</h2>
        </header>
        <div v-if="statusSlices.length" class="donut-layout">
          <div class="donut">
            <canvas ref="donutCanvas"></canvas>
            <div class="donut-center">
              <strong>{{ formatCount(statusTotal) }}</strong>
              <span>dossiers</span>
            </div>
          </div>
          <ul class="legend">
            <li v-for="slice in statusSlices" :key="slice.key">
              <span class="swatch" :style="{ background: slice.color }"></span>
              <span class="legend-name">{{ slice.label }}</span>
              <span class="legend-value">{{ formatCount(slice.value) }}</span>
            </li>
          </ul>
        </div>
        <p v-else class="empty">Aucune échéance pour cette sélection.</p>
      </article>
    </div>

    <section v-if="view === 'detail'" class="matrix-wrap">
      <div v-if="detailTerritories.length" class="table-container">
        <table class="agencies-table">
          <thead>
            <tr>
              <th class="col-label col-agence">Agence</th>
              <th class="col-label col-gest">CAF</th>
              <th><span class="th-title">Objectif</span><span class="th-unit">(FCFA)</span></th>
              <th><span class="th-title">Réalisé</span><span class="th-unit">(FCFA)</span></th>
              <th><span class="th-title">Global dû</span><span class="th-unit">(FCFA)</span></th>
              <th><span class="th-title">En attente</span><span class="th-unit">(FCFA)</span></th>
              <th><span class="th-title">En retard</span><span class="th-unit">(FCFA)</span></th>
              <th><span class="th-title">TRO</span><span class="th-unit">(%)</span></th>
            </tr>
          </thead>
          <tbody>
            <tr class="level-1-row" @click="toggleExpand('TERRITOIRE')">
              <td class="level-1 col-label col-agence">
                <span class="cell-line">
                  <button type="button" class="expand-btn" @click.stop="toggleExpand('TERRITOIRE')">{{ expanded.TERRITOIRE ? '−' : '+' }}</button>
                  <strong>TERRITOIRE</strong>
                </span>
              </td>
              <td class="col-label col-gest">—</td>
              <td><strong>{{ formatMoney(detailTotals.objectif) }}</strong></td>
              <td><strong>{{ formatMoney(detailTotals.realise) }}</strong></td>
              <td><strong>{{ formatMoney(detailTotals.global) }}</strong></td>
              <td><strong>{{ formatMoney(detailTotals.attente) }}</strong></td>
              <td><strong>{{ formatMoney(detailTotals.retard) }}</strong></td>
              <td><strong>{{ formatTro(detailTotals) }}</strong></td>
            </tr>
            <template v-if="expanded.TERRITOIRE">
              <template v-for="territory in detailTerritories" :key="territory.key">
                <tr class="level-2-row" @click="toggleExpand(territory.key)">
                  <td class="level-2 col-label col-agence">
                    <span class="cell-line">
                      <button type="button" class="expand-btn" @click.stop="toggleExpand(territory.key)">{{ expanded[territory.key] ? '−' : '+' }}</button>
                      <span>{{ territory.name }}</span>
                    </span>
                  </td>
                  <td class="col-label col-gest">—</td>
                  <td><strong>{{ formatMoney(territory.objectif) }}</strong></td>
                  <td><strong>{{ formatMoney(territory.realise) }}</strong></td>
                  <td><strong>{{ formatMoney(territory.global) }}</strong></td>
                  <td><strong>{{ formatMoney(territory.attente) }}</strong></td>
                  <td><strong>{{ formatMoney(territory.retard) }}</strong></td>
                  <td><strong>{{ formatTro(territory) }}</strong></td>
                </tr>
                <template v-if="expanded[territory.key]">
                  <template v-for="agency in territory.agencies" :key="agency.key">
                    <tr class="level-3-row" @click="toggleExpand(agency.key)">
                      <td class="level-3 col-label col-agence">
                        <span class="cell-line">
                          <button type="button" class="expand-btn" @click.stop="toggleExpand(agency.key)">{{ expanded[agency.key] ? '−' : '+' }}</button>
                          <span class="agency-name" :title="agency.label">{{ agency.label }}</span>
                        </span>
                      </td>
                      <td class="col-label col-gest">—</td>
                      <td>{{ formatMoney(agency.objectif) }}</td>
                      <td>{{ formatMoney(agency.realise) }}</td>
                      <td>{{ formatMoney(agency.global) }}</td>
                      <td>{{ formatMoney(agency.attente) }}</td>
                      <td>{{ formatMoney(agency.retard) }}</td>
                      <td>{{ formatTro(agency) }}</td>
                    </tr>
                    <template v-if="expanded[agency.key]">
                      <template v-for="caf in agency.cafs" :key="caf.key">
                        <tr class="level-4-row" @click="toggleExpand(caf.key)">
                          <td class="level-4 col-label col-agence">
                            <span class="cell-line">
                              <button type="button" class="expand-btn" @click.stop="toggleExpand(caf.key)">{{ expanded[caf.key] ? '−' : '+' }}</button>
                              <span class="agency-code">{{ agency.code }}</span>
                            </span>
                          </td>
                          <td class="col-label col-gest">{{ caf.label }}</td>
                          <td>{{ formatMoney(caf.objectif) }}</td>
                          <td>{{ formatMoney(caf.realise) }}</td>
                          <td>{{ formatMoney(caf.global) }}</td>
                          <td>{{ formatMoney(caf.attente) }}</td>
                          <td>{{ formatMoney(caf.retard) }}</td>
                          <td>{{ formatTro(caf) }}</td>
                        </tr>
                        <template v-if="expanded[caf.key]">
                          <tr v-for="loan in caf.loans" :key="loan.key" class="level-5-row">
                            <td class="level-5 col-label col-agence">
                              <span class="loan-no">{{ loan.pret }}</span>
                            </td>
                            <td class="col-label col-gest">{{ loan.client }}</td>
                            <td>{{ formatMoney(loan.objectif) }}</td>
                            <td>{{ formatMoney(loan.realise) }}</td>
                            <td>{{ formatMoney(loan.global) }}</td>
                            <td>{{ formatMoney(loan.attente) }}</td>
                            <td>{{ formatMoney(loan.retard) }}</td>
                            <td>{{ formatTro(loan) }}</td>
                          </tr>
                        </template>
                      </template>
                    </template>
                  </template>
                </template>
              </template>
            </template>
            <tr class="total-row">
              <td class="col-label col-agence">Total</td>
              <td class="col-label col-gest">—</td>
              <td>{{ formatMoney(detailTotals.objectif) }}</td>
              <td>{{ formatMoney(detailTotals.realise) }}</td>
              <td>{{ formatMoney(detailTotals.global) }}</td>
              <td>{{ formatMoney(detailTotals.attente) }}</td>
              <td>{{ formatMoney(detailTotals.retard) }}</td>
              <td>{{ formatTro(detailTotals) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <p v-else class="empty">Aucun dossier pour cette sélection.</p>
    </section>

    <section v-if="view === 'promesses'" class="promesses">
      <div class="promise-toolbar">
        <input v-model.trim="promiseQuery" type="search" placeholder="Client, matricule ou n° de prêt">
        <button type="button" class="promise-add" @click="openPromiseForm">Nouvelle promesse</button>
      </div>
      <p v-if="promiseError && !promiseOpen" class="banner error">{{ promiseError }}</p>
      <div class="kpis">
        <article v-for="card in promiseCards" :key="card.key" :style="{ '--accent': card.accent }">
          <span class="kpi-top"><span>{{ card.label }}</span></span>
          <strong>{{ formatCount(card.value) }}</strong>
          <small>{{ card.unit }}</small>
        </article>
      </div>
      <div class="segment promise-tabs" role="tablist" aria-label="Statut des promesses">
        <button type="button" :class="{ on: promiseStatus === 'all' }" @click="promiseStatus = 'all'">Toutes</button>
        <button type="button" :class="{ on: promiseStatus === 'attente' }" @click="promiseStatus = 'attente'">En attente</button>
        <button type="button" :class="{ on: promiseStatus === 'retard' }" @click="promiseStatus = 'retard'">En retard</button>
        <button type="button" :class="{ on: promiseStatus === 'partiel' }" @click="promiseStatus = 'partiel'">Partiellement réalisées</button>
        <button type="button" :class="{ on: promiseStatus === 'realise' }" @click="promiseStatus = 'realise'">Réalisées</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Client</th>
              <th class="num">Montant promis</th>
              <th class="num">Réglé</th>
              <th>Date promise</th>
              <th>Statut</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in promiseRows" :key="row.id">
              <td>
                <strong>{{ row.nom_client || '—' }}</strong>
                <span class="promise-sub">Mat. {{ row.matricule_client || '—' }} · {{ row.no_pret }}</span>
              </td>
              <td class="num">{{ formatMoney(row.montant_promis) }}</td>
              <td class="num">{{ formatMoney(row.montant_regle) }}</td>
              <td>{{ formatDate(row.date_paiement) }}</td>
              <td><span class="promise-badge" :class="row.statut_calcule">{{ promiseLabel(row.statut_calcule) }}</span></td>
              <td class="promise-actions">
                <button type="button" @click="openHistorique(row)">Historique</button>
                <button v-if="row.statut_calcule !== 'annulee' && row.statut_calcule !== 'reportee'" type="button" @click="openReporter(row)">Reporter</button>
                <button v-if="row.statut_calcule !== 'annulee' && row.statut_calcule !== 'reportee'" type="button" @click="openAnnuler(row)">Annuler</button>
              </td>
            </tr>
            <tr v-if="!promiseLoading && !promiseRows.length">
              <td colspan="6" class="empty">Aucune promesse pour cette sélection.</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div v-if="promiseOpen" class="kpi-overlay" @click.self="closePromiseForm">
        <section class="kpi-panel promise-panel" role="dialog" aria-modal="true" aria-label="Promesse de paiement">
          <header class="kpi-panel-head">
            <div>
              <p>{{ promiseMode === 'historique' ? 'Historique' : 'Promesse de paiement' }}</p>
              <h3>{{ promiseHeading }}</h3>
            </div>
            <button type="button" class="kpi-close" aria-label="Fermer" @click="closePromiseForm">×</button>
          </header>
          <p v-if="promiseError" class="banner error">{{ promiseError }}</p>

          <form v-if="promiseMode === 'create' || promiseMode === 'reporter'" class="promise-form" @submit.prevent="promiseMode === 'reporter' ? submitReporter() : submitPromise()">
            <label v-if="promiseMode === 'create'" class="promise-field">
              <span>Dossier</span>
              <input v-model.trim="dossierQuery" type="search" placeholder="Matricule, client ou n° de prêt" :disabled="!!promiseDossier">
            </label>
            <ul v-if="dossierHits.length" class="dossier-hits">
              <li v-for="row in dossierHits" :key="row.no_pret">
                <button type="button" @click="pickDossier(row)">
                  <strong>{{ row.nom_client || '—' }}</strong>
                  <span>Mat. {{ row.matricule_client || '—' }} · {{ row.no_pret }}</span>
                </button>
              </li>
            </ul>
            <p v-if="promiseDossier" class="dossier-picked">
              {{ promiseDossier.nom_client }} · {{ promiseDossier.no_pret }}
              <button type="button" @click="clearDossier">Changer</button>
            </p>
            <label class="promise-field">
              <span>Type d'échange</span>
              <select v-model="promiseForm.type_echange">
                <option value="appel">Appel téléphonique</option>
                <option value="visite">Visite client</option>
                <option value="sms">SMS / WhatsApp</option>
                <option value="autre">Autre</option>
              </select>
            </label>
            <label class="promise-field">
              <span>Date de l'échange</span>
              <input v-model="promiseForm.date_echange" type="date" required>
            </label>
            <label class="promise-field">
              <span>Montant exigible (FCFA)</span>
              <input :value="formatMoney(promiseForm.montant_exigible)" type="text" readonly>
            </label>
            <label class="promise-field">
              <span>Montant promis (FCFA)</span>
              <input v-model.number="promiseForm.montant_promis" type="number" min="1" step="1" required>
            </label>
            <p class="promise-hint">Reste à promettre : {{ formatMoney(promiseReste) }} FCFA</p>
            <label class="promise-field">
              <span>Date prévue de paiement</span>
              <input v-model="promiseForm.date_paiement" type="date" required>
            </label>
            <label class="promise-field">
              <span>Prochaine relance</span>
              <input v-model="promiseForm.date_relance" type="date">
            </label>
            <label class="promise-field">
              <span>Commentaire</span>
              <textarea v-model.trim="promiseForm.commentaire" rows="3" placeholder="Ce que le client a confirmé"></textarea>
            </label>
            <button type="submit" class="promise-add" :disabled="promiseSaving">{{ promiseSaving ? 'Enregistrement…' : 'Enregistrer la promesse' }}</button>
          </form>

          <form v-else-if="promiseMode === 'annuler'" class="promise-form" @submit.prevent="submitAnnuler">
            <label class="promise-field">
              <span>Motif d'annulation</span>
              <textarea v-model.trim="promiseForm.motif" rows="3" required placeholder="Pourquoi cette promesse est annulée"></textarea>
            </label>
            <button type="submit" class="promise-add" :disabled="promiseSaving">Annuler la promesse</button>
          </form>

          <div v-else class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Date</th>
                  <th>Échange</th>
                  <th>Résultat</th>
                  <th>Prochaine action</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in echanges" :key="item.id">
                  <td>{{ formatDate(item.date_echange) }}</td>
                  <td>{{ exchangeLabel(item.type_echange) }}</td>
                  <td>{{ item.resultat || '—' }}</td>
                  <td>{{ item.prochaine_action || '—' }}</td>
                </tr>
                <tr v-if="!echanges.length">
                  <td colspan="4" class="empty">Aucun échange pour ce dossier.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </section>

    <section v-if="view === 'performance'" class="perf-page">
      <div v-if="bestMarks.length" class="podium">
        <article v-for="mark in bestMarks" :key="mark.key" :class="'is-' + mark.key">
          <span class="podium-ico" v-html="mark.icon"></span>
          <div class="podium-copy">
            <p class="kicker">{{ mark.kicker }}</p>
            <strong class="podium-name">{{ displayName(mark.label) }}</strong>
          </div>
          <span class="podium-tro">{{ mark.rateText }}</span>
        </article>
      </div>
      <div class="perf-grid">
        <article v-for="card in perfCards" :key="card.key" class="perf-card" :class="[card.tone, card.key]">
          <header class="perf-head">
            <span class="perf-ico" v-html="card.icon"></span>
            <h2>{{ card.title }}</h2>
          </header>
          <ol v-if="card.rows.length" class="rank-list">
            <li v-for="(row, index) in card.rows" :key="row.key">
              <span class="rank-index" :class="'pos-' + (index + 1)">{{ index + 1 }}</span>
              <div class="rank-id">
                <div class="rank-line">
                  <span class="rank-name">{{ displayName(row.label) }}</span>
                  <span v-if="row.hint" class="rank-hint">{{ displayName(row.hint) }}</span>
                </div>
                <span class="rank-meta">{{ formatCompact(row.realise) }} réalisé · obj. {{ formatCompact(row.objectif) }}</span>
                <i class="track"><em :style="{ width: troBar(row.tro) + '%' }"></em></i>
              </div>
              <b class="rate">{{ formatPercent(row.tro) }}</b>
            </li>
          </ol>
          <p v-else class="empty">{{ card.empty }}</p>
        </article>
      </div>
    </section>

    <div v-if="view === 'detail' && selectedAgencyRow" class="kpi-overlay" @click.self="closeAgency">
      <section class="kpi-panel" role="dialog" aria-modal="true" :aria-label="selectedAgencyRow.label">
        <header class="kpi-panel-head">
          <div>
            <p>Détail</p>
            <h3>{{ selectedAgencyRow.label }}</h3>
          </div>
          <button type="button" class="kpi-close" aria-label="Fermer" @click="closeAgency">×</button>
        </header>
        <div class="kpi-panel-stats">
          <p><span>Tombé</span><strong>{{ formatCompact(selectedAgencyRow.tombe) }}</strong></p>
          <p><span>Réalisé</span><strong>{{ formatCompact(selectedAgencyRow.realise) }}</strong></p>
          <p><span>Lignes</span><strong>{{ formatCount(agencyDetailRows.length) }}</strong></p>
        </div>
        <label class="kpi-search">
          <span>Recherche</span>
          <input v-model.trim="agencyQuery" type="search" placeholder="N° de prêt, client, compte" @input="agencyPage = 1">
        </label>
        <div class="kpi-panel-table">
          <table>
            <thead>
              <tr>
                <th>N° prêt</th>
                <th>Matricule</th>
                <th>Client</th>
                <th>Compte</th>
                <th class="num">Objectif</th>
                <th class="num">Réalisé du mois</th>
                <th class="num">Global dû</th>
                <th>Déblocage</th>
                <th class="num">Capital accordé</th>
                <th class="num">Encours total</th>
                <th class="num">% remb.</th>
                <th>Statut prêt</th>
                <th>Statut déclassement</th>
                <th>Code gestion</th>
                <th>CAF</th>
                <th class="num">Solde dépôt garantie</th>
                <th>Date échéance</th>
                <th class="num">N° échéance</th>
                <th class="num">Solde compte</th>
                <th class="num">Montant échéance</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in agencyPageRows" :key="rowKey(row)">
                <td>{{ row.no_pret || '—' }}</td>
                <td>{{ row.matricule_client || '—' }}</td>
                <td>{{ row.nom_client || '—' }}</td>
                <td>{{ row.compte || '—' }}</td>
                <td class="num">{{ formatMoney(objectifOf(row)) }}</td>
                <td class="num">{{ formatMoney(row.montant_echeance_paye) }}</td>
                <td class="num">{{ formatMoney(row.mt_global_due_a_date) }}</td>
                <td>{{ formatDate(row.date_deblocage) }}</td>
                <td class="num">{{ formatMoney(row.montant_capital_accorde) }}</td>
                <td class="num">{{ formatMoney(row.encours_total) }}</td>
                <td class="num">{{ formatPercent(row.pourcentage_remboursement) }}</td>
                <td>{{ row.statut_pret || '—' }}</td>
                <td>{{ row.statut_declassement || '—' }}</td>
                <td>{{ row.code_gestion_pret || '—' }}</td>
                <td>{{ row.charge_affaire || '—' }}</td>
                <td class="num">{{ formatMoney(row.solde_depot_garantie) }}</td>
                <td>{{ formatDate(row.schedule_due_date) }}</td>
                <td class="num">{{ row.numero_echeance ?? '—' }}</td>
                <td class="num">{{ formatMoney(row.solde_cpte) }}</td>
                <td class="num">{{ formatMoney(row.montant_echeance_m) }}</td>
              </tr>
              <tr v-if="!agencyPageRows.length">
                <td colspan="20" class="empty">Aucun dossier pour cette agence.</td>
              </tr>
            </tbody>
          </table>
        </div>
        <footer v-if="agencyPageCount > 1" class="pager">
          <button type="button" :disabled="agencyPage <= 1" @click="agencyPage -= 1">Précédent</button>
          <span>{{ agencyPage }} / {{ agencyPageCount }}</span>
          <button type="button" :disabled="agencyPage >= agencyPageCount" @click="agencyPage += 1">Suivant</button>
        </footer>
      </section>
    </div>

    <div v-if="view === 'objectif'" class="detail-bar">
      <input
        v-model.trim="objectifQuery"
        type="search"
        placeholder="N° de prêt"
        @input="objectifPage = 1"
      />
    </div>
    <p v-if="view === 'objectif' && objectifWarning" class="banner warn">{{ objectifWarning }}</p>
    <div v-if="view === 'objectif' && objectifRows.length" class="kpis kpis-objectif">
      <article v-for="card in objectifCards" :key="card.label" :style="{ '--accent': card.accent }">
        <span>{{ card.label }}</span>
        <strong>{{ card.money ? formatMoney(card.value) : formatCount(card.value) }}</strong>
        <small v-if="card.money">FCFA</small>
      </article>
    </div>
    <div v-if="view === 'objectif' && filteredObjectifRows.length" class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>N° prêt</th>
            <th>Statut prêt</th>
            <th class="num">Exigible M-1</th>
            <th class="num">Montant échéance</th>
            <th class="num">Objectif recouvrement</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, index) in objectifPageRows" :key="`${row.account_number}-${index}`">
            <td>{{ row.account_number || '—' }}</td>
            <td>{{ row.statut_pret || '—' }}</td>
            <td class="num">{{ formatMoney(row.exigible_m_1) }}</td>
            <td class="num">{{ formatMoney(row.montant_echeance) }}</td>
            <td class="num">{{ formatMoney(row.objectif_recouvrement) }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <footer v-if="view === 'objectif' && objectifPageCount > 1" class="pager">
      <button type="button" :disabled="objectifPage <= 1" @click="objectifPage -= 1">Précédent</button>
      <span>{{ objectifPage }} / {{ objectifPageCount }} — {{ formatCount(filteredObjectifRows.length) }} lignes</span>
      <button type="button" :disabled="objectifPage >= objectifPageCount" @click="objectifPage += 1">Suivant</button>
    </footer>
  </section>
</template>

<script>
import {
  Chart,
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  DoughnutController,
  ArcElement,
} from 'chart.js';
import { userFacingError } from '../utils/userFacingError.js';

Chart.register(
  BarController,
  BarElement,
  LineController,
  LineElement,
  PointElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  DoughnutController,
  ArcElement,
);

const AGENCY_SERIES = [
  { key: 'realise', label: 'Réalisé', color: '#86efac' },
  { key: 'reste', label: 'Reste', color: '#1a4d3a' },
];

function formatAxis(value) {
  const amount = Number(value) || 0;
  if (Math.abs(amount) >= 1e9) {
    return `${(amount / 1e9).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} Md`;
  }
  if (Math.abs(amount) >= 1e6) {
    return `${(amount / 1e6).toLocaleString('fr-FR', { maximumFractionDigits: 1 })} M`;
  }
  return amount.toLocaleString('fr-FR');
}

function agencyLabel(name) {
  return String(name || '')
    .toLowerCase()
    .replace(/(^|[\s-])([a-zàâäéèêëïîôùûüç])/g, (_match, sep, letter) => sep + letter.toUpperCase());
}

const TERRITORY_ORDER = [
  { key: 'territoire_dakar_ville', name: 'TERRITOIRE DAKAR VILLE' },
  { key: 'territoire_dakar_banlieue', name: 'TERRITOIRE DAKAR BANLIEUE' },
  { key: 'territoire_province_centre_sud', name: 'TERRITOIRE PROVINCE CENTRE-SUD' },
  { key: 'territoire_province_nord', name: 'TERRITOIRE PROVINCE NORD' },
];
const TERRITORY_TOKENS = [
  ['TAMBACOUNDA', 'territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'],
  ['PRINCIPALE POINT E', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['LAMINE GUEYE', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['SAINT LOUIS', 'territoire_province_nord', 'TERRITOIRE PROVINCE NORD'],
  ['GRAND COMPTE', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['ZINGUINCHOR', 'territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'],
  ['ZIGUINCHOR', 'territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'],
  ['NIARRY TALLI', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['NIARRY TALLY', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['NIARY TALLY', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['KEUR MASSAR', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['OUROSSOGUI', 'territoire_province_nord', 'TERRITOIRE PROVINCE NORD'],
  ['GUEDIAWAYE', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['PARCELLES', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['DIOURBEL', 'territoire_province_nord', 'TERRITOIRE PROVINCE NORD'],
  ['RUFISQUE', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['SCAT URBAM', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['NGUELAW', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['LINGUERLA', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['LINGUERE', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['KAOLACK', 'territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'],
  ['MARISTES', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['CASTORS', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['PIKINE', 'territoire_dakar_banlieue', 'TERRITOIRE DAKAR BANLIEUE'],
  ['MBOUR', 'territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'],
  ['THIES', 'territoire_province_centre_sud', 'TERRITOIRE PROVINCE CENTRE-SUD'],
  ['TOUBA', 'territoire_province_nord', 'TERRITOIRE PROVINCE NORD'],
  ['LOUGA', 'territoire_province_nord', 'TERRITOIRE PROVINCE NORD'],
  ['POINT E', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['GUEYE', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
  ['SIEGE', 'territoire_dakar_ville', 'TERRITOIRE DAKAR VILLE'],
];

function resolveTerritory(label) {
  const text = String(label || '').toUpperCase().replace(/[-']/g, ' ').replace(/\s+/g, ' ').trim();
  const hit = TERRITORY_TOKENS.find(([token]) => text.includes(token));
  if (!hit) return { key: 'non_rattache', name: 'NON RATTACHÉ' };
  return { key: hit[1], name: hit[2] };
}

function emptyMetrics() {
  return { objectif: 0, realise: 0, global: 0, attente: 0, retard: 0 };
}

function addMetrics(target, source) {
  target.objectif += source.objectif;
  target.realise += source.realise;
  target.global += source.global;
  target.attente += source.attente;
  target.retard += source.retard;
}

const barLabels = {
  id: 'echeanceBarLabels',
  afterDatasetsDraw(chart) {
    const { ctx } = chart;
    const { datasets } = chart.data;
    const count = chart.data.labels.length;
    ctx.save();
    ctx.font = '700 11px Segoe UI, sans-serif';
    ctx.fillStyle = '#2563eb';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'bottom';
    for (let index = 0; index < count; index += 1) {
      const total = datasets.reduce((sum, dataset) => {
        if (dataset.stack !== 'echeance') return sum;
        return sum + (Number(dataset.data[index]) || 0);
      }, 0);
      if (!total) continue;
      let top = null;
      let x = null;
      datasets.forEach((dataset, datasetIndex) => {
        if (dataset.stack !== 'echeance') return;
        if (!(Number(dataset.data[index]) || 0)) return;
        const bar = chart.getDatasetMeta(datasetIndex).data[index];
        if (!bar) return;
        if (top === null || bar.y < top) {
          top = bar.y;
          x = bar.x;
        }
      });
      if (top === null) continue;
      ctx.fillText(formatAxis(total), x, top - 4);
    }
    ctx.restore();
  },
};

const PAGE_SIZE = 40;
const suiviEcheanceCache = new Map();

function periodKey(year, month) {
  return `${year}-${String(month).padStart(2, '0')}`;
}
const MONTHS = [
  'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
  'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre',
];

export default {
  name: 'SuiviEcheanceSection',
  data() {
    const now = new Date();
    const year = now.getFullYear();
    return {
      loading: false,
      error: '',
      rows: [],
      periodLabel: '',
      year,
      month: now.getMonth() + 1,
      years: [year, year - 1, year - 2],
      warning: '',
      snapshotLabel: '',
      view: 'dashboard',
      search: '',
      selectedAgency: '',
      agencyQuery: '',
      agencyPage: 1,
      objectifRows: [],
      objectifWarning: '',
      objectifQuery: '',
      objectifPage: 1,
      activeKpi: '',
      kpiQuery: '',
      kpiPage: 1,
      agence: '',
      caf: '',
      status: '',
      week: '',
      page: 1,
      promiseStatus: 'all',
      promesses: [],
      promiseQuery: '',
      promiseError: '',
      promiseLoading: false,
      promiseSaving: false,
      promiseOpen: false,
      promiseMode: 'create',
      promiseTarget: null,
      promiseDossier: null,
      dossierQuery: '',
      echanges: [],
      promiseForm: {
        type_echange: 'appel',
        date_echange: '',
        montant_exigible: '',
        montant_promis: '',
        date_paiement: '',
        date_relance: '',
        commentaire: '',
        motif: '',
      },
      expanded: { TERRITOIRE: true },
      iconUser: '<svg viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="8" r="3.2"/><path d="M5.4 19.2c.6-3.2 3-4.8 6.6-4.8s6 1.6 6.6 4.8a.7.7 0 0 1-.7.8H6.1a.7.7 0 0 1-.7-.8Z"/></svg>',
      iconAgency: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M4 20V9.5L12 4l8 5.5V20h-5.2v-5.2H9.2V20H4Z"/></svg>',
      iconZone: '<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 3.2 14.2 8l5.3.8-3.8 3.7.9 5.3L12 15.3 7.4 17.8l.9-5.3L4.5 8.8 9.8 8 12 3.2Z"/></svg>',
    };
  },
  created() {
    this.donutChart = null;
    this.barChart = null;
  },
  watch: {
    view(value) {
      if (value === 'promesses') this.loadPromesses();
    },
    chartSignature: {
      handler() {
        this.destroyCharts();
        if (this.view !== 'dashboard') return;
        this.renderCharts();
      },
      flush: 'post',
    },
  },
  computed: {
    monthOptions() {
      return MONTHS.map((label, index) => ({ value: index + 1, label }));
    },
    objectifLoanIds() {
      const ids = new Set();
      this.objectifRows.forEach((row) => {
        const id = this.loanKey(row.account_number);
        if (id) ids.add(id);
      });
      return ids;
    },
    tombeRows() {
      const excluded = new Set();
      this.rows.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (!id || row.schedule_due_date) return;
        if (String(row.statut_declassement || '').trim().toUpperCase() !== 'NORM') return;
        excluded.add(id);
      });
      if (!excluded.size) return this.rows;
      return this.rows.filter((row) => !excluded.has(this.loanKey(row.no_pret)));
    },
    rowsInObjectif() {
      const ids = this.objectifLoanIds;
      if (!ids.size) return [];
      return this.tombeRows.filter((row) => ids.has(this.loanKey(row.no_pret)) && this.hasObjectif(row));
    },
    suiviByLoan() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (!id || map.has(id)) return;
        map.set(id, row);
      });
      return map;
    },
    objectifByLoan() {
      return this.objectifMap(this.objectifRows);
    },
    agencyOptions() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        if (!row.code_agence || map.has(row.code_agence)) return;
        map.set(row.code_agence, `${row.code_agence} — ${row.nom_agence || row.code_agence}`);
      });
      return [...map.entries()]
        .map(([code, label]) => ({ code, label }))
        .sort((a, b) => a.label.localeCompare(b.label, 'fr'));
    },
    cafOptions() {
      return [...new Set(this.rowsInObjectif.map((row) => row.charge_affaire).filter(Boolean))]
        .sort((a, b) => a.localeCompare(b, 'fr'));
    },
    filteredRows() {
      const query = this.search.toLowerCase();
      return this.rowsInObjectif.filter((row) => {
        if (this.agence && row.code_agence !== this.agence) return false;
        if (this.caf && row.charge_affaire !== this.caf) return false;
        if (this.status === 'none' && row.status_ech) return false;
        if (this.status && this.status !== 'none' && row.status_ech !== this.status) return false;
        if (this.week && this.weekOf(row) !== this.week) return false;
        if (!query) return true;
        return [
          row.no_pret,
          row.nom_client,
          row.matricule_client,
          row.compte,
          row.charge_affaire,
          row.code_gestion_pret,
          row.code_agence,
          row.nom_agence,
          row.type_pret,
        ].filter(Boolean).join(' ').toLowerCase().includes(query);
      });
    },
    pageCount() {
      return Math.max(1, Math.ceil(this.filteredRows.length / PAGE_SIZE));
    },
    pageRows() {
      const start = (this.page - 1) * PAGE_SIZE;
      return this.filteredRows.slice(start, start + PAGE_SIZE);
    },
    weekSeries() {
      return AGENCY_SERIES;
    },
    chartSignature() {
      const total = this.filteredRows.reduce(
        (sum, row) => sum + (Number(row.mt_global_due_a_date) || 0),
        0,
      );
      return `${this.view}|${this.filteredRows.length}|${total}|${this.agence}|${this.caf}|${this.status}|${this.week}|${this.search}`;
    },
    statusSlices() {
      let realise = 0;
      let attente = 0;
      let retard = 0;
      this.dossiersByLoan.forEach((items) => {
        if (this.dossierRetard(items)) {
          retard += 1;
          return;
        }
        if (this.dossierAttente(items)) {
          attente += 1;
          return;
        }
        if (items.some((row) => this.realiseMatchesObjectif(row))) realise += 1;
      });
      return [
        { key: 'realise', label: 'Réalisé', color: '#15803d', value: realise },
        { key: 'attente', label: 'En attente', color: '#d97706', value: attente },
        { key: 'retard', label: 'En retard', color: '#dc2626', value: retard },
      ].filter((slice) => slice.value > 0);
    },
    statusTotal() {
      return this.statusSlices.reduce((sum, slice) => sum + slice.value, 0);
    },
    detailBreakdown() {
      const agencies = new Map();
      const seen = new Set();
      const place = (loan) => {
        const territory = resolveTerritory(loan.agenceLabel);
        if (!agencies.has(territory.key)) {
          agencies.set(territory.key, { key: territory.key, name: territory.name, agencies: new Map() });
        }
        const zone = agencies.get(territory.key);
        const agencyKey = `${loan.agence || '—'}`;
        if (!zone.agencies.has(agencyKey)) {
          zone.agencies.set(agencyKey, {
            key: `${territory.key}-${agencyKey}`,
            code: loan.agence || '—',
            label: agencyLabel(String(loan.agenceLabel || agencyKey).replace(/^AGENCE\s+/i, '')),
            cafs: new Map(),
            ...emptyMetrics(),
          });
        }
        const agency = zone.agencies.get(agencyKey);
        const cafKey = loan.caf || '—';
        if (!agency.cafs.has(cafKey)) {
          agency.cafs.set(cafKey, {
            key: `${agency.key}-${cafKey}`,
            label: cafKey,
            loans: [],
            ...emptyMetrics(),
          });
        }
        const caf = agency.cafs.get(cafKey);
        caf.loans.push(loan);
        addMetrics(caf, loan);
        addMetrics(agency, loan);
      };

      this.dossiersByLoan.forEach((items, pret) => {
        const id = this.loanKey(pret);
        seen.add(id);
        const head = items[0] || {};
        const objectif = Number(this.objectifByLoan.get(id)) || 0;
        const global = items.reduce((sum, row) => sum + (Number(row.mt_global_due_a_date) || 0), 0);
        place({
          key: id || pret,
          pret: head.no_pret || pret || '—',
          client: head.nom_client || '—',
          agence: head.code_agence || '—',
          agenceLabel: head.nom_agence || head.code_agence || 'Non rattaché',
          caf: head.charge_affaire || '—',
          objectif,
          realise: objectif - global,
          global,
          attente: this.dossierAttente(items) ? global : 0,
          retard: this.dossierRetard(items) ? global : 0,
        });
      });

      if (!this.hasSuiviFilter) {
        this.objectifByLoan.forEach((value, id) => {
          if (seen.has(id)) return;
          const objectif = Number(value) || 0;
          place({
            key: id,
            pret: id,
            client: '—',
            agence: '—',
            agenceLabel: 'Non rattaché',
            caf: '—',
            objectif,
            realise: objectif,
            global: 0,
            attente: 0,
            retard: 0,
          });
        });
      }

      const totals = emptyMetrics();
      const ordered = [
        ...TERRITORY_ORDER.filter((item) => agencies.has(item.key)).map((item) => agencies.get(item.key)),
        ...[...agencies.values()].filter((group) => !TERRITORY_ORDER.some((item) => item.key === group.key)),
      ];
      const territories = ordered.map((group) => {
        const metrics = emptyMetrics();
        const agencyList = [...group.agencies.values()]
          .map((agency) => {
            addMetrics(metrics, agency);
            return {
              key: agency.key,
              code: agency.code,
              label: agency.label,
              objectif: agency.objectif,
              realise: agency.realise,
              global: agency.global,
              attente: agency.attente,
              retard: agency.retard,
              cafs: [...agency.cafs.values()]
                .map((caf) => ({
                  ...caf,
                  loans: [...caf.loans].sort((left, right) => right.objectif - left.objectif || String(left.pret).localeCompare(String(right.pret), 'fr')),
                }))
                .sort((left, right) => right.objectif - left.objectif || left.label.localeCompare(right.label, 'fr')),
            };
          })
          .sort((left, right) => right.objectif - left.objectif || left.label.localeCompare(right.label, 'fr'));
        addMetrics(totals, metrics);
        return { key: group.key, name: group.name, ...metrics, agencies: agencyList };
      });
      return { territories, totals };
    },
    detailTerritories() {
      return this.detailBreakdown.territories;
    },
    detailTotals() {
      return this.detailBreakdown.totals;
    },
    zoneRanks() {
      return this.detailTerritories
        .filter((zone) => zone.key !== 'non_rattache' && Number(zone.objectif) > 0)
        .map((zone) => ({
          key: zone.key,
          label: String(zone.name || '').replace(/^territoire\s+/i, '').trim() || zone.name,
          realise: zone.realise,
          objectif: zone.objectif,
          tro: (zone.realise / zone.objectif) * 100,
        }))
        .sort((left, right) => right.tro - left.tro || right.realise - left.realise);
    },
    agencyRanks() {
      const rows = this.detailTerritories.flatMap((zone) => (zone.agencies || [])
        .filter((agency) => agency.code !== '—' && !/non rattach/i.test(agency.label) && Number(agency.objectif) > 0)
        .map((agency) => ({
          key: agency.key,
          label: agency.label,
          hint: String(zone.name || '').replace(/^territoire\s+/i, '').trim(),
          realise: agency.realise,
          objectif: agency.objectif,
          tro: (agency.realise / agency.objectif) * 100,
        })));
      return this.rankByTro(rows);
    },
    cafRanks() {
      const grouped = new Map();
      this.detailTerritories.forEach((zone) => {
        (zone.agencies || []).forEach((agency) => {
          if (/non rattach/i.test(agency.label)) return;
          (agency.cafs || []).forEach((caf) => {
            if (!caf.label || caf.label === '—' || !(Number(caf.objectif) > 0)) return;
            const label = this.displayName(caf.label);
            const key = label.toLocaleLowerCase('fr-FR');
            if (!grouped.has(key)) {
              grouped.set(key, { key, label, agencies: new Set(), realise: 0, objectif: 0 });
            }
            const bucket = grouped.get(key);
            bucket.agencies.add(agency.label);
            bucket.realise += Number(caf.realise) || 0;
            bucket.objectif += Number(caf.objectif) || 0;
          });
        });
      });
      const rows = [...grouped.values()].map((row) => ({
        key: row.key,
        label: row.label,
        hint: row.agencies.size > 1 ? `${row.agencies.size} agences` : [...row.agencies][0],
        realise: row.realise,
        objectif: row.objectif,
        tro: row.objectif ? (row.realise / row.objectif) * 100 : 0,
      }));
      return this.rankByTro(rows);
    },
    topAgencies() {
      return this.agencyRanks.top;
    },
    flopAgencies() {
      return this.agencyRanks.flop;
    },
    topCafs() {
      return this.cafRanks.top;
    },
    flopCafs() {
      return this.cafRanks.flop;
    },
    otherZones() {
      return this.zoneRanks.slice(1).map((zone) => ({
        ...zone,
        short: String(zone.label || '').replace(/^province\s+/i, '').trim(),
      }));
    },
    bestMarks() {
      const shown = (row) => {
        if (!row) return null;
        return {
          label: row.label,
          hint: row.hint ? (/^\d/.test(row.hint) ? row.hint : this.displayName(row.hint)) : '',
          amountText: this.formatCompact(row.realise),
          targetText: row.objectif ? this.formatCompact(row.objectif) : '',
          rateText: this.formatPercent(row.tro),
          bar: this.troBar(row.tro),
          tone: this.troClass(row.tro),
        };
      };
      return [
        ['caf', 'Meilleur CAF', this.topCafs[0], this.iconUser],
        ['agency', 'Meilleure agence', this.topAgencies[0], this.iconAgency],
        ['zone', 'Meilleur territoire', this.zoneRanks[0], this.iconZone],
      ].flatMap(([key, kicker, row, icon]) => {
        const view = shown(row);
        return view ? [{ key, kicker, icon, ...view }] : [];
      });
    },
    perfCards() {
      return [
        { key: 'top-caf', title: 'Top 5 des CAF', tone: 'is-top', icon: this.iconUser, rows: this.topCafs, empty: 'Aucun CAF sur cette sélection.' },
        { key: 'flop-caf', title: 'Flop 5 des CAF', tone: 'is-flop', icon: this.iconUser, rows: this.flopCafs, empty: 'Pas assez de CAF pour un flop.' },
        { key: 'top-agency', title: 'Top 5 des agences', tone: 'is-top', icon: this.iconAgency, rows: this.topAgencies, empty: 'Aucune agence sur cette sélection.' },
        { key: 'flop-agency', title: 'Flop 5 des agences', tone: 'is-flop', icon: this.iconAgency, rows: this.flopAgencies, empty: 'Pas assez d’agences pour un flop.' },
      ];
    },
    promiseCards() {
      const rows = this.decoratedPromesses.filter((row) => row.statut_calcule !== 'annulee');
      const sum = (list) => list.reduce((total, row) => total + (Number(row.montant_promis) || 0), 0);
      const attente = rows.filter((row) => row.statut_calcule === 'attente');
      const realise = rows.filter((row) => row.statut_calcule === 'realisee');
      const retard = rows.filter((row) => row.statut_calcule === 'non_tenue');
      return [
        { key: 'all', label: 'Promesses enregistrées', value: rows.length, unit: this.formatCompact(sum(rows)), accent: '#1a4d3a' },
        { key: 'attente', label: 'En attente', value: attente.length, unit: this.formatCompact(sum(attente)), accent: '#d97706' },
        { key: 'realise', label: 'Réalisées', value: realise.length, unit: this.formatCompact(sum(realise)), accent: '#16a34a' },
        { key: 'retard', label: 'En retard', value: retard.length, unit: this.formatCompact(sum(retard)), accent: '#dc2626' },
      ];
    },
    paidByLoan() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (!id) return;
        map.set(id, (map.get(id) || 0) + (Number(row.montant_echeance_paye) || 0));
      });
      return map;
    },
    decoratedPromesses() {
      return this.promesses.map((row) => {
        const paid = this.paidByLoan.get(this.loanKey(row.no_pret)) || 0;
        const promis = Number(row.montant_promis) || 0;
        return {
          ...row,
          montant_regle: paid,
          reliquat: Math.max(0, promis - paid),
          statut_calcule: this.promiseStatut(row, paid),
        };
      });
    },
    dossierHits() {
      const query = this.dossierQuery.trim().toLowerCase();
      if (query.length < 2 || this.promiseDossier) return [];
      const seen = new Map();
      this.rowsInObjectif.forEach((row) => {
        if (!row.no_pret || seen.has(row.no_pret)) return;
        seen.set(row.no_pret, row);
      });
      return [...seen.values()].filter((row) => [
        row.no_pret,
        row.nom_client,
        row.matricule_client,
        row.charge_affaire,
      ].filter(Boolean).join(' ').toLowerCase().includes(query)).slice(0, 8);
    },
    promiseReste() {
      const exigible = Number(this.promiseForm.montant_exigible) || 0;
      const promis = Number(this.promiseForm.montant_promis) || 0;
      return Math.max(0, exigible - promis);
    },
    promiseHeading() {
      if (this.promiseMode === 'annuler') return 'Annuler la promesse';
      if (this.promiseMode === 'reporter') return 'Reporter la promesse';
      if (this.promiseMode === 'historique') return this.promiseTarget?.nom_client || 'Échanges';
      return 'Nouvelle promesse';
    },
    promiseRows() {
      const rows = this.decoratedPromesses.filter((row) => {
        if (this.promiseStatus === 'all') return true;
        if (this.promiseStatus === 'retard') return row.statut_calcule === 'non_tenue';
        if (this.promiseStatus === 'partiel') return row.statut_calcule === 'partielle';
        if (this.promiseStatus === 'realise') return row.statut_calcule === 'realisee';
        return row.statut_calcule === this.promiseStatus;
      });
      const query = this.promiseQuery.toLowerCase();
      if (!query) return rows;
      return rows.filter((row) => [
        row.nom_client,
        row.matricule_client,
        row.no_pret,
        row.charge_affaire,
      ].filter(Boolean).join(' ').toLowerCase().includes(query));
    },
    weekCards() {
      const buckets = [
        { key: 'S1', label: 'S1', range: '1 – 7', tombe: 0, realise: 0, count: 0 },
        { key: 'S2', label: 'S2', range: '8 – 14', tombe: 0, realise: 0, count: 0 },
        { key: 'S3', label: 'S3', range: '15 – 21', tombe: 0, realise: 0, count: 0 },
        { key: 'S4', label: 'S4', range: '22 – 31', tombe: 0, realise: 0, count: 0 },
      ];
      const byKey = Object.fromEntries(buckets.map((item) => [item.key, item]));
      this.rowsInObjectif.forEach((row) => {
        if (this.agence && row.code_agence !== this.agence) return;
        if (this.caf && row.charge_affaire !== this.caf) return;
        const key = this.weekOf(row);
        if (!key || !byKey[key]) return;
        const paye = Number(row.montant_echeance_paye) || 0;
        const reste = Number(row.montant_echeance_m) || 0;
        byKey[key].tombe += paye + reste;
        if (this.realiseMatchesObjectif(row)) byKey[key].realise += paye;
        byKey[key].count += 1;
      });
      return buckets.map((item) => ({
        ...item,
        rate: item.tombe > 0 ? Math.min(100, (item.realise / item.tombe) * 100) : 0,
      }));
    },
    agencyBars() {
      const map = new Map();
      this.rowsInObjectif.forEach((row) => {
        if (this.agence && row.code_agence !== this.agence) return;
        if (this.caf && row.charge_affaire !== this.caf) return;
        if (this.week && this.weekOf(row) !== this.week) return;
        if (!row.schedule_due_date) return;
        const code = row.code_agence || '—';
        const name = agencyLabel(String(row.nom_agence || code).replace(/^AGENCE\s+/i, ''));
        if (!map.has(code)) {
          map.set(code, {
            key: code,
            label: name,
            tombe: 0,
            realise: 0,
            reste: 0,
            objectif: 0,
            loans: new Set(),
          });
        }
        const item = map.get(code);
        const paye = Number(row.montant_echeance_paye) || 0;
        const reste = Number(row.montant_echeance_m) || 0;
        item.tombe += paye + reste;
        if (this.realiseMatchesObjectif(row)) item.realise += paye;
        const id = this.loanKey(row.no_pret);
        if (id && !item.loans.has(id)) {
          item.loans.add(id);
          item.objectif += Number(this.objectifOf(row)) || 0;
        }
      });
      return [...map.values()]
        .map((item) => ({
          key: item.key,
          label: item.label,
          tombe: item.tombe,
          realise: item.realise,
          objectif: item.objectif,
          reste: Math.max(0, item.tombe - item.realise),
        }))
        .sort((left, right) => right.tombe - left.tombe || left.label.localeCompare(right.label, 'fr'));
    },
    agencyChartWidth() {
      return `${Math.max(this.agencyBars.length * 88, 640)}px`;
    },
    selectedAgencyRow() {
      return this.agencyBars.find((row) => row.key === this.selectedAgency) || null;
    },
    agencyDetailRows() {
      if (!this.selectedAgency) return [];
      const query = this.agencyQuery.toLowerCase();
      return this.rowsInObjectif.filter((row) => {
        if ((row.code_agence || '—') !== this.selectedAgency) return false;
        if (this.caf && row.charge_affaire !== this.caf) return false;
        if (this.week && this.weekOf(row) !== this.week) return false;
        if (!query) return true;
        return [
          row.no_pret,
          row.nom_client,
          row.matricule_client,
          row.compte,
          row.charge_affaire,
          row.code_gestion_pret,
        ].filter(Boolean).join(' ').toLowerCase().includes(query);
      });
    },
    agencyPageCount() {
      return Math.max(1, Math.ceil(this.agencyDetailRows.length / PAGE_SIZE));
    },
    agencyPageRows() {
      const start = (this.agencyPage - 1) * PAGE_SIZE;
      return this.agencyDetailRows.slice(start, start + PAGE_SIZE);
    },
    suiviLoanIds() {
      const ids = new Set();
      this.filteredRows.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (id) ids.add(id);
      });
      return ids;
    },
    hasSuiviFilter() {
      return Boolean(this.agence || this.caf || this.week || this.status || this.search);
    },
    filteredObjectifRows() {
      const ids = this.hasSuiviFilter ? this.suiviLoanIds : null;
      const query = this.objectifQuery.toLowerCase();
      return this.objectifRows.filter((row) => {
        const id = this.loanKey(row.account_number);
        if (!id) return false;
        if (ids && !ids.has(id)) return false;
        if (!query) return true;
        return (row.account_number || '').toLowerCase().includes(query);
      });
    },
    objectifPageCount() {
      return Math.max(1, Math.ceil(this.filteredObjectifRows.length / PAGE_SIZE));
    },
    objectifPageRows() {
      const start = (this.objectifPage - 1) * PAGE_SIZE;
      return this.filteredObjectifRows.slice(start, start + PAGE_SIZE);
    },
    objectifCards() {
      const seen = new Set();
      let exigible = 0;
      let echeance = 0;
      this.filteredObjectifRows.forEach((row) => {
        echeance += Number(row.montant_echeance) || 0;
        const id = row.account_number;
        if (!id || seen.has(id)) return;
        seen.add(id);
        exigible += Number(row.exigible_m_1) || 0;
      });
      let objectif = 0;
      this.objectifMap(this.filteredObjectifRows).forEach((value) => {
        objectif += Number(value) || 0;
      });
      return [
        { label: 'Prêts financés', value: seen.size, money: false, accent: '#1a4d3a' },
        { label: 'Exigible M-1', value: exigible, money: true, accent: '#7c3aed' },
        { label: 'Montant échéance', value: echeance, money: true, accent: '#2563eb' },
        { label: 'Objectif recouvrement', value: objectif, money: true, accent: '#2563eb' },
      ];
    },
    activeKpiCard() {
      return this.kpiCards.find((card) => card.key === this.activeKpi) || null;
    },
    dossiersByLoan() {
      const map = new Map();
      this.filteredRows.forEach((row) => {
        const id = row.no_pret;
        if (!id) return;
        if (!map.has(id)) map.set(id, []);
        map.get(id).push(row);
      });
      return map;
    },
    globalDuByLoan() {
      const map = new Map();
      this.filteredRows.forEach((row) => {
        const id = this.loanKey(row.no_pret);
        if (!id) return;
        map.set(id, (map.get(id) || 0) + (Number(row.mt_global_due_a_date) || 0));
      });
      return map;
    },
    suiviMetrics() {
      const rows = this.filteredRows;
      const sum = (list, key) => list.reduce((total, row) => total + (Number(row[key]) || 0), 0);
      let objectif = 0;
      if (this.hasSuiviFilter) {
        this.suiviLoanIds.forEach((id) => {
          objectif += Number(this.objectifByLoan.get(id)) || 0;
        });
      } else {
        this.objectifByLoan.forEach((value) => {
          objectif += Number(value) || 0;
        });
      }
      objectif = Math.round(objectif);
      let attente = 0;
      let retard = 0;
      const global = Math.round(sum(rows, 'mt_global_due_a_date'));
      this.dossiersByLoan.forEach((items) => {
        const volume = sum(items, 'mt_global_due_a_date');
        if (this.dossierRetard(items)) retard += volume;
        else if (this.dossierAttente(items)) attente += volume;
      });
      rows.forEach((row) => {
        if (row.no_pret) return;
        const volume = Number(row.mt_global_due_a_date) || 0;
        const echeance = String(row.status_ech || '').trim().toUpperCase();
        if (!this.isNormOrImmo(row.statut_declassement)) retard += volume;
        else if (echeance === 'A') attente += volume;
      });
      attente = Math.round(attente);
      retard = Math.round(retard);
      const realise = objectif - global;
      const taux = objectif ? (realise / objectif) * 100 : 0;
      return {
        objectif,
        realise,
        attente,
        retard,
        global,
        taux,
      };
    },
    kpiAmountLabel() {
      if (this.activeKpi === 'global') return 'Global dû';
      return 'MT recouvré';
    },
    kpiDetailRows() {
      const query = this.kpiQuery.toLowerCase();
      let rows = [];
      if (this.activeKpi === 'objectif') {
        const ids = this.hasSuiviFilter ? this.suiviLoanIds : null;
        rows = this.objectifRows.filter((row) => {
          const id = this.loanKey(row.account_number);
          return id && (!ids || ids.has(id));
        });
      } else if (this.activeKpi === 'global') {
        rows = this.filteredRows.filter((row) => this.hasObjectif(row) && (Number(row.mt_global_due_a_date) || 0) !== 0);
      } else if (this.activeKpi === 'realise') {
        const seen = new Set();
        rows = this.filteredObjectifRows.filter((row) => {
          const id = this.loanKey(row.account_number);
          if (!id || seen.has(id)) return false;
          seen.add(id);
          return true;
        });
      } else if (this.activeKpi === 'retard') {
        const loans = [];
        this.dossiersByLoan.forEach((items) => {
          if (this.dossierRetard(items)) loans.push(...items);
        });
        rows = loans;
      } else if (this.activeKpi === 'attente') {
        const loans = [];
        this.dossiersByLoan.forEach((items) => {
          if (this.dossierAttente(items)) loans.push(...items);
        });
        rows = loans;
      }
      if (!query) return rows;
      return rows.filter((row) => [
        row.account_number,
        row.no_pret,
        row.nom_client,
        row.matricule_client,
        row.code_agence,
        row.nom_agence,
        row.compte,
        row.statut_pret,
        row.statut_declassement,
      ].filter(Boolean).join(' ').toLowerCase().includes(query));
    },
    kpiPageCount() {
      return Math.max(1, Math.ceil(this.kpiDetailRows.length / PAGE_SIZE));
    },
    kpiPageRows() {
      const start = (this.kpiPage - 1) * PAGE_SIZE;
      return this.kpiDetailRows.slice(start, start + PAGE_SIZE);
    },
    kpiCards() {
      const metrics = this.suiviMetrics;
      const objectif = Number(metrics.objectif) || 0;
      const shareOf = (value) => (objectif ? (Number(value) / objectif) * 100 : 0);
      return [
        {
          key: 'objectif',
          label: 'Objectif de recouvrement',
          value: metrics.objectif,
          money: true,
          unit: 'FCFA',
          accent: '#2563eb',
        },
        {
          key: 'realise',
          label: 'Réalisé du mois',
          value: metrics.realise,
          share: shareOf(metrics.realise),
          money: true,
          unit: 'FCFA',
          accent: '#16a34a',
        },
        {
          key: 'global',
          label: 'Global dû à date',
          value: metrics.global,
          share: shareOf(metrics.global),
          money: true,
          unit: 'FCFA',
          accent: '#db2777',
        },
        {
          key: 'attente',
          label: 'En attente',
          value: metrics.attente,
          share: shareOf(metrics.attente),
          money: true,
          unit: 'FCFA',
          accent: '#f59e0b',
        },
        {
          key: 'retard',
          label: 'En retard',
          value: metrics.retard,
          share: shareOf(metrics.retard),
          money: true,
          unit: 'FCFA',
          accent: '#ef4444',
        },
      ];
    },
    formulaCards() {
      const metrics = this.suiviMetrics;
      return [
        {
          key: 'taux',
          label: 'Taux de réalisation',
          value: metrics.taux,
          percent: true,
          unit: 'réalisé',
          accent: '#7c3aed',
        },
      ];
    },
  },
  mounted() {
    this.load();
  },
  activated() {
    this.$nextTick(() => {
      this.donutChart?.resize();
      this.barChart?.resize();
    });
  },
  updated() {
    const canvas = this.$refs.barCanvas;
    if (!canvas || this.view !== 'dashboard' || !this.agencyBars.length) return;
    if (Chart.getChart(canvas)) return;
    this.renderBars();
  },
  beforeUnmount() {
    this.destroyCharts();
  },
  methods: {
    weekOf(row) {
      const text = String(row?.schedule_due_date || '');
      const match = text.match(/(\d{4})-(\d{2})-(\d{2})/);
      const day = match ? Number(match[3]) : 0;
      if (!day) return '';
      if (day <= 7) return 'S1';
      if (day <= 14) return 'S2';
      if (day <= 21) return 'S3';
      return 'S4';
    },
    realiseMatchesObjectif(row) {
      const objectif = Math.round(Number(this.objectifOf(row)) || 0);
      const realise = Math.round(Number(row?.montant_echeance_paye) || 0);
      const status = String(row?.status_ech || '').trim().toUpperCase();
      return objectif > 0 && objectif === realise && status !== 'I';
    },
    globalDuCell(row) {
      if (this.activeKpi !== 'realise') return this.lineOf(row).mt_global_due_a_date;
      const id = this.loanKey(row?.no_pret || row?.account_number);
      return Number(this.globalDuByLoan.get(id)) || 0;
    },
    realiseCell(row) {
      if (this.activeKpi !== 'realise') return this.lineOf(row).montant_echeance_paye;
      const id = this.loanKey(row?.no_pret || row?.account_number);
      const objectif = Number(this.objectifByLoan.get(id)) || 0;
      return objectif - (Number(this.globalDuByLoan.get(id)) || 0);
    },
    isNormOrImmo(status) {
      const value = String(status || '').trim().toUpperCase();
      return value === 'NORM' || value === 'IMMO';
    },
    dossierRetard(items) {
      return !this.isNormOrImmo(items[0]?.statut_declassement);
    },
    dossierAttente(items) {
      const sain = this.isNormOrImmo(items[0]?.statut_declassement);
      const echeanceA = items.some((row) => String(row?.status_ech || '').trim().toUpperCase() === 'A');
      return sain && echeanceA;
    },
    kpiIcon(key) {
      const paths = {
        objectif: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
        global: '<rect x="4" y="5" width="16" height="14" rx="2"/><path d="M8 3v4M16 3v4M4 10h16"/>',
        realise: '<path d="M20 7L9 18l-5-5"/>',
        attente: '<circle cx="12" cy="12" r="8"/><path d="M12 8v5l3 2"/>',
        retard: '<path d="M12 4l8 14H4L12 4z"/><path d="M12 10v4M12 16h.01"/>',
        taux: '<path d="M19 5L5 19"/><circle cx="7.5" cy="7.5" r="2.5"/><circle cx="16.5" cy="16.5" r="2.5"/>',
      };
      const body = paths[key] || paths.objectif;
      return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">${body}</svg>`;
    },
    formatKpi(card) {
      if (!card) return '—';
      if (card.percent) return this.formatPercent(card.value);
      if (card.money === false) return this.formatCount(card.value);
      return this.formatMoney(card.value);
    },
    openKpi(key) {
      if (key === 'objectif') {
        this.activeKpi = '';
        this.view = 'objectif';
        this.objectifQuery = '';
        this.objectifPage = 1;
        return;
      }
      this.activeKpi = key;
      this.kpiQuery = '';
      this.kpiPage = 1;
    },
    closeKpi() {
      this.activeKpi = '';
      this.kpiQuery = '';
      this.kpiPage = 1;
    },
    kpiAmount(row) {
      if (this.activeKpi === 'global') return row.mt_global_due_a_date;
      if (this.activeKpi === 'realise') return row.montant_echeance_paye;
      if (this.activeKpi === 'attente') return row.montant_echeance_m;
      return row.exigible_ech;
    },
    destroyCharts() {
      if (this.donutChart) {
        this.donutChart.destroy();
        this.donutChart = null;
      }
      if (this.barChart) {
        this.barChart.destroy();
        this.barChart = null;
      }
    },
    renderCharts() {
      this.renderBars();
      this.renderDonut();
    },
    renderDonut() {
      const canvas = this.$refs.donutCanvas;
      if (!canvas || !this.statusSlices.length) return;
      this.donutChart = new Chart(canvas, {
        type: 'doughnut',
        data: {
          labels: this.statusSlices.map((slice) => slice.label),
          datasets: [{
            data: this.statusSlices.map((slice) => slice.value),
            backgroundColor: this.statusSlices.map((slice) => slice.color),
            borderColor: '#fff',
            borderWidth: 3,
            hoverOffset: 4,
          }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          cutout: '66%',
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const value = context.parsed || 0;
                  const share = this.statusTotal ? Math.round((value / this.statusTotal) * 100) : 0;
                  return ` ${context.label} : ${this.formatCount(value)} (${share} %)`;
                },
              },
            },
          },
        },
      });
    },
    renderBars() {
      const canvas = this.$refs.barCanvas;
      const rows = this.agencyBars;
      if (!canvas || !rows.length) return;
      const existing = Chart.getChart(canvas);
      if (existing) existing.destroy();
      const width = Math.max(rows.length * 88, 640);
      const height = 360;
      canvas.width = width;
      canvas.height = height;
      canvas.style.width = `${width}px`;
      canvas.style.height = `${height}px`;
      this.barChart = new Chart(canvas, {
        type: 'bar',
        plugins: [barLabels],
        data: {
          labels: rows.map((row) => row.label),
          datasets: [
            ...AGENCY_SERIES.map((serie) => ({
              label: serie.label,
              data: rows.map((row) => row[serie.key] || 0),
              backgroundColor: serie.color,
              stack: 'echeance',
              maxBarThickness: 46,
              borderWidth: 0,
              order: 2,
            })),
            {
              type: 'line',
              label: 'Objectif',
              data: rows.map((row) => row.objectif || 0),
              borderColor: '#2563eb',
              backgroundColor: '#2563eb',
              pointBackgroundColor: '#fff',
              pointBorderColor: '#2563eb',
              pointBorderWidth: 2,
              pointRadius: 4,
              pointHoverRadius: 5,
              borderWidth: 2,
              tension: 0.35,
              fill: false,
              stack: 'objectif',
              order: 1,
            },
          ],
        },
        options: {
          responsive: false,
          animation: false,
          layout: { padding: { top: 22 } },
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { display: false },
            tooltip: {
              callbacks: {
                label: (context) => {
                  const value = Number(context.parsed.y) || 0;
                  if (!value) return null;
                  return ` ${context.dataset.label} : ${formatAxis(value)}`;
                },
                footer: (items) => {
                  const total = items.reduce((sum, item) => {
                    if (item.dataset.stack !== 'echeance') return sum;
                    return sum + (Number(item.parsed.y) || 0);
                  }, 0);
                  return `Tombé : ${formatAxis(total)}`;
                },
              },
            },
          },
          scales: {
            x: {
              stacked: true,
              grid: { display: false },
              ticks: {
                color: '#64748b',
                maxRotation: 0,
                autoSkip: false,
                font: { size: 11 },
                callback(value) {
                  const label = String(this.getLabelForValue(value) || '');
                  const words = label.split(/\s+/).filter(Boolean);
                  if (words.length < 2) return label;
                  const mid = Math.ceil(words.length / 2);
                  return [words.slice(0, mid).join(' '), words.slice(mid).join(' ')];
                },
              },
            },
            y: {
              stacked: true,
              beginAtZero: true,
              ticks: { color: '#64748b', callback: (value) => formatAxis(value) },
              grid: { color: '#e8eef5' },
              border: { display: false },
            },
          },
        },
      });
    },
    applyCachedPeriod(cached) {
      this.rows = cached.rows;
      this.periodLabel = cached.periodLabel;
      this.warning = cached.warning;
      this.snapshotLabel = cached.snapshotLabel;
      this.objectifRows = cached.objectifRows;
      this.objectifWarning = cached.objectifWarning;
      this.error = cached.error || '';
    },
    reload() {
      return this.load(true);
    },
    async load(force = false) {
      if (force && typeof force !== 'boolean') {
        force = false;
      }
      const key = periodKey(this.year, this.month);
      const cached = suiviEcheanceCache.get(key);
      if (!force && cached) {
        this.applyCachedPeriod(cached);
        this.loading = false;
        return;
      }
      this.loading = !cached;
      this.error = '';
      this.warning = '';
      this.objectifWarning = '';
      this.page = 1;
      this.objectifPage = 1;
      const params = { year: this.year, month: this.month };
      try {
        const [suiviResult, objectifResult] = await Promise.allSettled([
          window.axios.get('/api/oracle/data/suivi-echeance', { params }),
          window.axios.get('/api/oracle/data/objectif-recouvrement', { params }),
        ]);
        if (suiviResult.status === 'fulfilled') {
          const payload = suiviResult.value.data || {};
          this.rows = Array.isArray(payload.rows) ? payload.rows : [];
          this.periodLabel = payload.period?.label || '';
          this.warning = payload.warning || '';
          this.snapshotLabel = payload.snapshot?.jour
            ? this.formatDate(payload.snapshot.jour)
            : '';
        } else {
          this.rows = [];
          this.periodLabel = '';
          this.warning = '';
          this.snapshotLabel = '';
          this.error = userFacingError(suiviResult.reason, 'Le suivi échéance n\'a pas pu être chargé.');
        }
        if (objectifResult.status === 'fulfilled') {
          const payload = objectifResult.value.data || {};
          this.objectifRows = Array.isArray(payload.rows) ? payload.rows : [];
          this.objectifWarning = payload.warning || '';
        } else {
          this.objectifRows = [];
          this.objectifWarning = userFacingError(
            objectifResult.reason,
            'L\'objectif de recouvrement n\'a pas pu être chargé.',
          );
        }
        if (!this.error) {
          suiviEcheanceCache.set(key, {
            rows: this.rows,
            periodLabel: this.periodLabel,
            warning: this.warning,
            snapshotLabel: this.snapshotLabel,
            objectifRows: this.objectifRows,
            objectifWarning: this.objectifWarning,
            error: '',
          });
        }
      } finally {
        this.loading = false;
      }
    },
    loanKey(value) {
      return String(value || '').trim().toUpperCase();
    },
    objectifMap(rows) {
      const map = new Map();
      (rows || []).forEach((row) => {
        const id = this.loanKey(row.account_number || row.no_pret);
        if (!id) return;
        const exigible = Number(row.exigible_m_1) || 0;
        const stored = Number(row.objectif_recouvrement);
        const line = Number.isFinite(stored)
          ? stored
          : exigible + (Number(row.montant_echeance) || 0);
        if (!map.has(id)) {
          map.set(id, line);
          return;
        }
        map.set(id, map.get(id) + line - exigible);
      });
      return map;
    },
    objectifOf(row) {
      const id = this.loanKey(row?.no_pret || row?.account_number);
      if (!id || !this.objectifByLoan.has(id)) return null;
      return this.objectifByLoan.get(id);
    },
    hasObjectif(row) {
      return (Number(this.objectifOf(row)) || 0) > 0;
    },
    lineOf(row) {
      if (row?.no_pret) return row;
      return this.suiviByLoan.get(this.loanKey(row?.account_number)) || row || {};
    },
    rowKey(row) {
      return `${row.no_pret}-${row.numero_echeance || 'x'}-${row.schedule_due_date || 'nodue'}-${row.date_deblocage || ''}`;
    },
    toggleExpand(key) {
      this.expanded = { ...this.expanded, [key]: !this.expanded[key] };
    },
    formatTro(bucket) {
      if (!bucket || !Number(bucket.objectif)) return '—';
      return this.formatPercent((Number(bucket.realise) / Number(bucket.objectif)) * 100);
    },
    rankByTro(rows) {
      const floors = [20000000, 5000000, 0];
      let pool = rows;
      floors.some((floor) => {
        const next = rows.filter((row) => Number(row.objectif) >= floor);
        if (next.length >= 8) {
          pool = next;
          return true;
        }
        if (next.length) pool = next;
        return false;
      });
      const ordered = [...pool].sort((left, right) => right.tro - left.tro || right.realise - left.realise);
      const top = ordered.slice(0, 5);
      const topKeys = new Set(top.map((row) => row.key));
      const flop = [...ordered]
        .filter((row) => !topKeys.has(row.key))
        .sort((left, right) => left.tro - right.tro || left.realise - right.realise)
        .slice(0, 5);
      return { top, flop };
    },
    troClass(value) {
      const rate = Number(value);
      if (!Number.isFinite(rate)) return '';
      if (rate >= 80) return 'positive';
      if (rate >= 50) return 'mid';
      return 'negative';
    },
    troBar(value) {
      const rate = Number(value);
      if (!Number.isFinite(rate) || rate <= 0) return 0;
      return Math.min(100, rate);
    },
    displayName(value) {
      return String(value || '')
        .toLocaleLowerCase('fr-FR')
        .replace(/(^|[\s'’-])(\p{L})/gu, (_, sep, letter) => sep + letter.toLocaleUpperCase('fr-FR'));
    },
    openAgency(row) {
      if (this.selectedAgency === row.key) {
        this.closeAgency();
        return;
      }
      this.selectedAgency = row.key;
      this.agencyQuery = '';
      this.agencyPage = 1;
    },
    closeAgency() {
      this.selectedAgency = '';
      this.agencyQuery = '';
      this.agencyPage = 1;
    },
    formatCompact(value) {
      const amount = Number(value) || 0;
      const abs = Math.abs(amount);
      const sign = amount < 0 ? '−' : '';
      const text = (base, digits) => (abs / base).toLocaleString('fr-FR', {
        minimumFractionDigits: digits,
        maximumFractionDigits: digits,
      });
      if (abs >= 1e9) return `${sign}${text(1e9, 1)} Md`;
      if (abs >= 1e6) return `${sign}${text(1e6, 1)} M`;
      if (abs >= 1e3) return `${sign}${text(1e3, 0)} k`;
      return `${sign}${Math.round(abs).toLocaleString('fr-FR')}`;
    },
    agencyRate(row) {
      const tombe = Number(row?.tombe) || 0;
      if (!tombe) return 0;
      return ((Number(row.realise) || 0) / tombe) * 100;
    },
    formatCount(value) {
      return new Intl.NumberFormat('fr-FR').format(value || 0);
    },
    formatMoney(value) {
      if (value === null || value === undefined || value === '') return '—';
      const amount = Number(value);
      if (!Number.isFinite(amount)) return '—';
      return new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 0 }).format(amount);
    },
    formatPercent(value) {
      if (value === null || value === undefined || value === '') return '—';
      const amount = Number(value);
      if (!Number.isFinite(amount)) return '—';
      return `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 2 }).format(amount)} %`;
    },
    formatDate(value) {
      if (!value) return '—';
      const text = String(value);
      if (/^\d{4}-\d{2}-\d{2}/.test(text)) {
        const [year, month, day] = text.slice(0, 10).split('-');
        return `${day}/${month}/${year}`;
      }
      return text;
    },
    authHeaders() {
      const token = localStorage.getItem('token');
      return token ? { Authorization: `Bearer ${token}` } : {};
    },
    todayIso() {
      const now = new Date();
      const month = String(now.getMonth() + 1).padStart(2, '0');
      const day = String(now.getDate()).padStart(2, '0');
      return `${now.getFullYear()}-${month}-${day}`;
    },
    promiseStatut(row, paid) {
      if (row.statut === 'annulee' || row.statut === 'reportee') return row.statut;
      const promis = Number(row.montant_promis) || 0;
      const settled = Number(paid) || 0;
      const due = String(row.date_paiement || '').slice(0, 10);
      const late = due && due < this.todayIso();
      if (promis > 0 && settled >= promis) return 'realisee';
      if (settled > 0 && settled < promis) return 'partielle';
      if (late) return 'non_tenue';
      return 'attente';
    },
    promiseLabel(statut) {
      return {
        attente: 'En attente',
        realisee: 'Réalisée',
        partielle: 'Partiellement réalisée',
        non_tenue: 'Non tenue',
        reportee: 'Reportée',
        annulee: 'Annulée',
      }[statut] || statut;
    },
    exchangeLabel(type) {
      return {
        appel: 'Appel téléphonique',
        visite: 'Visite client',
        sms: 'SMS / WhatsApp',
        autre: 'Autre',
      }[type] || type || '—';
    },
    resetPromiseForm() {
      this.promiseForm = {
        type_echange: 'appel',
        date_echange: this.todayIso(),
        montant_exigible: '',
        montant_promis: '',
        date_paiement: '',
        date_relance: '',
        commentaire: '',
        motif: '',
      };
      this.promiseDossier = null;
      this.dossierQuery = '';
      this.promiseError = '';
    },
    async loadPromesses() {
      this.promiseLoading = true;
      this.promiseError = '';
      try {
        const { data } = await window.axios.get('/api/promesses', { headers: this.authHeaders() });
        this.promesses = data.promesses || [];
      } catch (error) {
        this.promiseError = 'Impossible de charger les promesses.';
      } finally {
        this.promiseLoading = false;
      }
    },
    openPromiseForm() {
      this.promiseMode = 'create';
      this.promiseTarget = null;
      this.resetPromiseForm();
      this.promiseOpen = true;
    },
    closePromiseForm() {
      this.promiseOpen = false;
      this.promiseTarget = null;
      this.echanges = [];
    },
    loanExigible(noPret) {
      return this.rowsInObjectif
        .filter((row) => row.no_pret === noPret)
        .reduce((sum, row) => sum + (Number(row.mt_global_due_a_date) || 0), 0);
    },
    pickDossier(row) {
      this.promiseDossier = row;
      this.dossierQuery = '';
      this.promiseForm.montant_exigible = Math.round(this.loanExigible(row.no_pret));
    },
    clearDossier() {
      this.promiseDossier = null;
      this.promiseForm.montant_exigible = '';
    },
    promisePayload(dossier) {
      return {
        no_pret: dossier.no_pret,
        matricule_client: dossier.matricule_client || null,
        nom_client: dossier.nom_client || null,
        code_agence: dossier.code_agence || null,
        nom_agence: dossier.nom_agence || null,
        charge_affaire: dossier.charge_affaire || null,
        compte: dossier.compte || null,
        type_echange: this.promiseForm.type_echange,
        date_echange: this.promiseForm.date_echange,
        montant_exigible: Number(this.promiseForm.montant_exigible) || 0,
        montant_promis: Number(this.promiseForm.montant_promis) || 0,
        date_paiement: this.promiseForm.date_paiement,
        date_relance: this.promiseForm.date_relance || null,
        commentaire: this.promiseForm.commentaire || null,
      };
    },
    async submitPromise() {
      if (!this.promiseDossier) {
        this.promiseError = 'Choisissez un dossier.';
        return;
      }
      if (!(Number(this.promiseForm.montant_promis) > 0) || !this.promiseForm.date_paiement) {
        this.promiseError = 'Le montant promis et la date de paiement sont obligatoires.';
        return;
      }
      this.promiseSaving = true;
      this.promiseError = '';
      try {
        await window.axios.post('/api/promesses', this.promisePayload(this.promiseDossier), { headers: this.authHeaders() });
        this.closePromiseForm();
        await this.loadPromesses();
      } catch (error) {
        this.promiseError = 'La promesse n’a pas pu être enregistrée.';
      } finally {
        this.promiseSaving = false;
      }
    },
    openReporter(row) {
      this.promiseMode = 'reporter';
      this.promiseTarget = row;
      this.resetPromiseForm();
      this.promiseDossier = row;
      this.promiseForm.montant_exigible = row.montant_exigible;
      this.promiseForm.montant_promis = row.montant_promis;
      this.promiseForm.date_paiement = String(row.date_paiement || '').slice(0, 10);
      this.promiseOpen = true;
    },
    async submitReporter() {
      if (!this.promiseTarget) return;
      this.promiseSaving = true;
      this.promiseError = '';
      try {
        await window.axios.post(`/api/promesses/${this.promiseTarget.id}/reporter`, {
          type_echange: this.promiseForm.type_echange,
          date_echange: this.promiseForm.date_echange,
          montant_promis: Number(this.promiseForm.montant_promis) || 0,
          date_paiement: this.promiseForm.date_paiement,
          date_relance: this.promiseForm.date_relance || null,
          commentaire: this.promiseForm.commentaire || null,
        }, { headers: this.authHeaders() });
        this.closePromiseForm();
        await this.loadPromesses();
      } catch (error) {
        this.promiseError = 'Le report n’a pas pu être enregistré.';
      } finally {
        this.promiseSaving = false;
      }
    },
    openAnnuler(row) {
      this.promiseMode = 'annuler';
      this.promiseTarget = row;
      this.resetPromiseForm();
      this.promiseOpen = true;
    },
    async submitAnnuler() {
      if (!this.promiseTarget || !this.promiseForm.motif) {
        this.promiseError = 'Le motif d’annulation est obligatoire.';
        return;
      }
      this.promiseSaving = true;
      this.promiseError = '';
      try {
        await window.axios.post(`/api/promesses/${this.promiseTarget.id}/annuler`, {
          motif: this.promiseForm.motif,
        }, { headers: this.authHeaders() });
        this.closePromiseForm();
        await this.loadPromesses();
      } catch (error) {
        this.promiseError = 'L’annulation n’a pas pu être enregistrée.';
      } finally {
        this.promiseSaving = false;
      }
    },
    async openHistorique(row) {
      this.promiseMode = 'historique';
      this.promiseTarget = row;
      this.promiseError = '';
      this.echanges = [];
      this.promiseOpen = true;
      try {
        const { data } = await window.axios.get(`/api/promesses/${row.id}/echanges`, { headers: this.authHeaders() });
        this.echanges = data.echanges || [];
      } catch (error) {
        this.promiseError = 'Impossible de charger l’historique.';
      }
    },
    exportCsv() {
      const headers = [
        'N° prêt', 'Matricule', 'Client', 'Compte', 'Objectif', 'Réalisé du mois', 'Global dû',
        'Déblocage', 'Capital accordé', 'Encours total', '% remboursé', 'Statut prêt',
        'Statut déclassement', 'Code gestion', 'CAF', 'Solde dépôt garantie', 'Date échéance',
        'N° échéance', 'Solde compte', 'Montant échéance',
      ];
      const lines = this.filteredRows.map((row) => [
        row.no_pret, row.matricule_client, row.nom_client, row.compte,
        this.objectifOf(row), row.montant_echeance_paye, row.mt_global_due_a_date,
        row.date_deblocage, row.montant_capital_accorde, row.encours_total,
        row.pourcentage_remboursement, row.statut_pret, row.statut_declassement,
        row.code_gestion_pret, row.charge_affaire, row.solde_depot_garantie,
        row.schedule_due_date, row.numero_echeance, row.solde_cpte,
        row.montant_echeance_m,
      ]);
      const csv = [headers, ...lines]
        .map((line) => line.map((value) => `"${String(value ?? '').replaceAll('"', '""')}"`).join(';'))
        .join('\n');
      const blob = new Blob([`\uFEFF${csv}`], { type: 'text/csv;charset=utf-8' });
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = `suivi-echeance-${this.year}-${String(this.month).padStart(2, '0')}.csv`;
      link.click();
      URL.revokeObjectURL(link.href);
    },
  },
};
</script>

<style scoped>
.echeance {
  padding: 0.75rem 1.25rem 2rem;
}

.head {
  display: flex;
  flex-direction: column;
  gap: 18px;
  margin-bottom: 16px;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid #e3eee8;
  border-radius: 16px;
}

.head-top,
.filters {
  display: flex;
  align-items: center;
  gap: 10px;
}

.head h2 {
  margin: 0;
  flex: 0 0 auto;
  font-size: 1.2rem;
  color: #111827;
  white-space: nowrap;
}

.segment {
  display: flex;
  flex: 0 0 auto;
  height: 40px;
  margin-left: 8px;
  padding: 3px;
  background: #f3f6f4;
  border-radius: 10px;
}

.segment button {
  border: 0;
  background: transparent;
  color: #4d6158;
  font-weight: 700;
  font-size: 13px;
  padding: 0 18px;
  border-radius: 8px;
  cursor: pointer;
}

.segment button.on {
  background: #1a4d3a;
  color: #fff;
}

.chip {
  display: flex;
  align-items: center;
  gap: 8px;
  height: 40px;
  padding: 0 30px 0 12px;
  background: #f3f6f4 url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M2.5 4.5 6 8l3.5-3.5' fill='none' stroke='%236b7c74' stroke-width='1.4' stroke-linecap='round' stroke-linejoin='round'/%3E%3C/svg%3E") right 10px center no-repeat;
  border-radius: 10px;
}

.chip-year,
.chip-month { flex: 0 0 auto; margin-left: 0; }
.chip-year { margin-left: auto; }

.filters .chip { flex: 1 1 0; min-width: 0; }

.chip span {
  flex: 0 0 auto;
  font-size: 11px;
  font-weight: 700;
  color: #6b7c74;
}

.chip select {
  flex: 1 1 auto;
  width: auto;
  min-width: 4.5rem;
  height: 100%;
  border: 0;
  background: transparent;
  color: #1c2b24;
  font-size: 13px;
  font-weight: 600;
  padding: 0;
  appearance: none;
  cursor: pointer;
}

.refresh {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 40px;
  width: 40px;
  height: 40px;
  border: 0;
  border-radius: 10px;
  background: #1a4d3a;
  color: #fff;
  cursor: pointer;
}

.refresh svg { width: 16px; height: 16px; }
.refresh:disabled { opacity: 0.65; cursor: wait; }

.detail-bar {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

input[type="search"],
.btn {
  height: 36px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #fff;
  font-size: 0.875rem;
  color: #111827;
}

input[type="search"] {
  flex: 1;
  min-width: 220px;
  padding: 0 0.75rem;
}

.btn {
  padding: 0 0.9rem;
  cursor: pointer;
  font-weight: 600;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.kpis {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.kpis-objectif {
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-bottom: 14px;
}


.kpis article {
  background: #fff;
  border: 1px solid #e4eee8;
  border-top: 3px solid var(--accent, #1a4d3a);
  border-radius: 14px;
  padding: 14px 16px 12px;
  box-shadow: 0 8px 22px rgba(20, 61, 46, 0.04);
}

.kpi-card {
  cursor: pointer;
  text-align: left;
}

.kpi-card:hover,
.kpi-card.on,
.kpi-card:focus-visible {
  border-color: var(--accent, #1a4d3a);
  outline: none;
}

.kpi-overlay {
  position: fixed;
  inset: 0;
  z-index: 40;
  display: flex;
  justify-content: flex-end;
  background: rgba(15, 23, 42, 0.35);
}

.kpi-panel {
  width: min(1280px, 100%);
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fff;
  box-shadow: -12px 0 40px rgba(15, 23, 42, 0.16);
}

.kpi-panel-head {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  padding: 18px 20px 8px;
}

.kpi-panel-head p {
  margin: 0 0 4px;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #1a4d3a;
}

.kpi-panel-head h3 {
  margin: 0;
  font-size: 22px;
  color: #0f2744;
}

.kpi-close {
  width: 32px;
  height: 32px;
  border: 0;
  border-radius: 8px;
  background: #f3f6f4;
  color: #334155;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
}

.kpi-panel-stats {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  padding: 8px 20px 12px;
}

.kpi-panel-stats p {
  margin: 0;
  padding: 10px 12px;
  border-radius: 10px;
  background: #f4f7f5;
}

.kpi-panel-stats span {
  display: block;
  margin-bottom: 4px;
  font-size: 11px;
  color: #64748b;
}

.kpi-search {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin: 0 20px 12px;
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.kpi-panel-table {
  flex: 1;
  overflow: auto;
  margin: 0 20px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
}

.kpi-panel .pager {
  padding: 12px 20px 16px;
}

.kpis .kpi-top {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 40px;
  margin-bottom: 8px;
}

.kpis .kpi-top > span {
  font-size: 14px;
  line-height: 1.2;
  color: var(--accent, #1a4d3a);
}

.kpi-icon {
  width: 40px;
  height: 40px;
  flex-shrink: 0;
  display: grid;
  place-items: center;
  border-radius: 10px;
  color: #fff;
  background: var(--accent, #1a4d3a);
}

.kpi-icon :deep(svg) {
  width: 24px;
  height: 24px;
}

.kpis span {
  display: block;
  color: #6b7c74;
  font-size: 11px;
  font-weight: 700;
  line-height: 1.25;
}

.kpis strong {
  display: block;
  font-size: 1.05rem;
  letter-spacing: -0.03em;
  color: #0b1f33;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.kpis small {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-top: 2px;
  color: #94a3b8;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.kpis small em {
  margin-left: auto;
  font-style: normal;
  letter-spacing: 0;
  color: var(--accent, #1a4d3a);
}

.banner {
  padding: 0.85rem 1rem;
  border-radius: 8px;
  background: #f9fafb;
  color: #4b5563;
  margin-bottom: 1rem;
}

.banner.error {
  background: #fef2f2;
  color: #b91c1c;
}

.banner.warn {
  background: #fffbeb;
  color: #92400e;
}

.table-wrap {
  overflow: auto;
  max-height: calc(100vh - 280px);
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

table {
  width: max-content;
  min-width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

th,
td {
  padding: 0.55rem 0.7rem;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
  vertical-align: top;
}

th {
  position: sticky;
  top: 0;
  background: #f3f4f6;
  color: #374151;
  font-weight: 600;
  z-index: 1;
}

.num {
  text-align: right;
}

tbody tr:hover {
  background: #f9fafb;
}

.code {
  display: inline-block;
  margin-right: 0.35rem;
  padding: 0.05rem 0.35rem;
  border-radius: 4px;
  background: #ecfdf5;
  color: #065f46;
  font-size: 0.75rem;
  font-weight: 600;
}

.client,
.sub {
  display: block;
}

.sub {
  color: #6b7280;
  font-size: 0.75rem;
}

.badge {
  display: inline-block;
  padding: 0.12rem 0.45rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.is-late {
  background: #fee2e2;
  color: #991b1b;
}

.is-paid {
  background: #dcfce7;
  color: #166534;
}

.is-wait {
  background: #fef3c7;
  color: #92400e;
}

.is-empty {
  background: #f3f4f6;
  color: #4b5563;
}

.pager,
.count {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 0.75rem;
  margin-top: 0.75rem;
  color: #4b5563;
  font-size: 0.875rem;
}

.pager button {
  height: 32px;
  padding: 0 0.7rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  background: #fff;
  cursor: pointer;
}

.pager button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.grid-2 {
  display: grid;
  grid-template-columns: 1.4fr 0.8fr;
  gap: 12px;
  margin-top: 14px;
}

.panel {
  background: #fff;
  border: 1px solid #e4eee8;
  border-radius: 16px;
  padding: 16px;
  min-width: 0;
  box-shadow: 0 8px 24px rgba(20, 61, 46, 0.04);
}

.panel-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: baseline;
  margin-bottom: 12px;
}

.panel-head h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: #143d2e;
}

.panel-head span {
  font-size: 12px;
  color: #6b7c74;
}

.chart-box { position: relative; min-height: 240px; }
.chart-scroll { overflow-x: auto; }
.chart-box.tall { height: 360px; min-width: 100%; }
.stack-legend { justify-content: center; }

.rank-panel { margin-top: 12px; }
.rank-table { overflow: auto; }
.rank-table table { width: 100%; border-collapse: collapse; }
.rank-table th {
  text-align: left;
  font-size: 11px;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: #6b7c74;
  padding: 8px 10px;
  border-bottom: 1px solid #e4eee8;
}
.rank-table td {
  padding: 9px 10px;
  border-bottom: 1px solid #f1f5f3;
  color: #143d2e;
  font-size: 13px;
  font-weight: 600;
}
.rank-table th.num,
.rank-table td.num { text-align: right; font-variant-numeric: tabular-nums; }
.rank-index {
  width: 36px;
  color: #64748b;
  font-variant-numeric: tabular-nums;
}
.rank-row { cursor: pointer; }
.rank-row:hover td { background: #f4faf6; }
.rank-row.on td { background: #e7f6ee; }
.rank-index.pos-1,
.rank-index.pos-2,
.rank-index.pos-3 { color: #15803d; }
.rank-table td.is-gap,
.rate-cell strong.is-gap { color: #dc2626; }
.agency-detail { margin-top: 12px; }
.agency-detail .detail-bar { margin: 0 0 12px; }
.agency-detail .kpi-close {
  border: 0;
  background: transparent;
  font-size: 22px;
  line-height: 1;
  cursor: pointer;
  color: #64748b;
}
.rate-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 180px;
}
.rate-track {
  flex: 1;
  height: 8px;
  border-radius: 99px;
  background: #e8f5ee;
  overflow: hidden;
}
.rate-track span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: #16a34a;
}
.rate-cell strong {
  width: 64px;
  text-align: right;
  font-size: 12px;
  color: #143d2e;
}

.donut-layout {
  display: flex;
  gap: 18px;
  align-items: center;
  min-height: 280px;
}

.donut {
  position: relative;
  width: 230px;
  height: 230px;
  flex-shrink: 0;
}

.donut-center {
  position: absolute;
  inset: 26%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  pointer-events: none;
}

.donut-center strong {
  font-size: 22px;
  font-weight: 800;
  color: #143d2e;
  letter-spacing: -0.03em;
}

.donut-center span {
  font-size: 12px;
  font-weight: 700;
  color: #64748b;
}

.legend,
.inline-legend {
  list-style: none;
  margin: 0;
  padding: 0;
}

.legend {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend li,
.inline-legend li {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
}

.legend-value {
  font-variant-numeric: tabular-nums;
  font-weight: 700;
  color: #143d2e;
}

.inline-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 16px;
  margin-top: 10px;
  color: #334155;
  font-size: 13px;
  font-weight: 600;
}

.swatch {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  flex-shrink: 0;
}

.swatch.square {
  width: 14px;
  height: 10px;
  border-radius: 2px;
}

.swatch.line {
  width: 18px;
  height: 3px;
  border-radius: 2px;
  background: #2563eb;
}

.empty {
  margin: 24px 0;
  color: #6b7c74;
}

@media (max-width: 1100px) {
  .kpis { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .strip p,
  .strip button { flex: 1 1 140px; }
  .grid-2 { grid-template-columns: 1fr; }
  .head-top,
  .filters { flex-wrap: wrap; }
  .chip-year { margin-left: 0; }
  .filters .chip { flex: 1 1 180px; }
}

.matrix-wrap { margin-top: 4px; }
.table-container { overflow-x: auto; }
.agencies-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  min-width: 980px;
}
.agencies-table thead th {
  position: sticky;
  top: 0;
  z-index: 2;
  background: #dc2626;
  color: #fff;
  padding: 10px 8px;
  text-align: right;
  font-weight: 700;
  white-space: nowrap;
  border-bottom: none;
}
.agencies-table th.col-label { text-align: left; }
.th-title { display: block; }
.th-unit { display: block; font-size: 10px; font-weight: 600; opacity: 0.9; }
.agencies-table td {
  padding: 8px;
  text-align: right;
  font-variant-numeric: tabular-nums;
  border-bottom: 1px solid #ececec;
}
.agencies-table td.col-label { text-align: left; }
.agencies-table tbody tr.level-1-row td { background: #1f2937; color: #fff; font-weight: 700; cursor: pointer; }
.agencies-table tbody tr.level-2-row td { background: #1e3a5f; color: #fff; font-weight: 600; cursor: pointer; }
.agencies-table tbody tr.level-3-row td { background: #dbeafe; color: #1e3a5f; cursor: pointer; }
.agencies-table tbody tr.level-4-row td { background: #fef3c7; color: #78350f; cursor: pointer; }
.agencies-table tbody tr.level-5-row td { background: #ffffff; color: #1c2b24; }
.agencies-table tbody tr.level-5-row:nth-child(even) td { background: #f1f5f9; }
.level-2 { padding-left: 16px; }
.level-3 { padding-left: 28px; }
.level-4 { padding-left: 40px; }
.level-5 { padding-left: 56px; }
.loan-no { font-variant-numeric: tabular-nums; font-weight: 600; }
.agencies-table tbody tr.level-1-row:hover td { background: #111827; color: #fff; }
.agencies-table tbody tr.level-2-row:hover td { background: #1e40af; color: #fff; }
.agencies-table tbody tr.level-3-row:hover td { background: #bfdbfe; color: #1e3a5f; }
.agencies-table tbody tr.level-4-row:hover td { background: #fde68a; color: #78350f; }
.agencies-table tbody tr.level-5-row:hover td { background: #e2e8f0; color: #1c2b24; }
.cell-line { display: flex; align-items: center; gap: 8px; }
.expand-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.1);
  color: inherit;
  border-radius: 3px;
  cursor: pointer;
  font-weight: 700;
}
.level-2 .expand-btn {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.45);
  background: rgba(255, 255, 255, 0.12);
}
.level-3 .expand-btn {
  color: #1e3a5f;
  border-color: #93c5fd;
  background: #eff6ff;
}
.level-4 .expand-btn {
  color: #78350f;
  border-color: #fcd34d;
  background: #fffbeb;
}
.agency-name, .agency-code { font-weight: 600; }
.total-row { background: #dc2626; color: #fff; font-weight: 700; }
.total-row td { border-bottom: none; background: #dc2626; color: #fff; }
.agencies-table tbody tr.total-row:hover td { background: #dc2626; color: #fff; }
.col-agence { min-width: 220px; }
.col-gest { min-width: 140px; }

.promise-tabs { width: fit-content; margin: 4px 0 12px; }
.promise-toolbar { display: flex; gap: 10px; align-items: center; margin-bottom: 12px; }
.promise-toolbar input {
  flex: 1;
  height: 40px;
  padding: 0 12px;
  border: 1px solid #e3eee8;
  border-radius: 10px;
  background: #fff;
}
.promise-add {
  height: 40px;
  padding: 0 14px;
  border: 0;
  border-radius: 10px;
  background: #1a4d3a;
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}
.promise-sub { display: block; margin-top: 2px; font-size: 12px; color: #64748b; }
.promise-actions { display: flex; gap: 6px; white-space: nowrap; }
.promise-actions button {
  border: 0;
  background: #f3f6f4;
  color: #1a4d3a;
  border-radius: 8px;
  padding: 4px 8px;
  font-weight: 700;
  cursor: pointer;
}
.promise-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 700;
  background: #f3f4f6;
  color: #374151;
}
.promise-badge.attente { background: #fff4e5; color: #b45309; }
.promise-badge.realisee { background: #e7f6ec; color: #15803d; }
.promise-badge.partielle { background: #e7f0fb; color: #1d4ed8; }
.promise-badge.non_tenue { background: #fde8ea; color: #be123c; }
.promise-badge.reportee { background: #f3f4f6; color: #4b5563; }
.promise-badge.annulee { background: #f3f4f6; color: #6b7280; }
.promesses .table-wrap { background: #fff; border: 1px solid #e7eeea; border-radius: 14px; overflow: auto; }
.promesses table { width: 100%; }
.promesses .empty { padding: 28px 16px; text-align: center; color: #64748b; }
.promise-panel { max-width: 560px; }
.promise-form { display: flex; flex-direction: column; gap: 10px; padding: 4px 2px 8px; }
.promise-field { display: flex; flex-direction: column; gap: 4px; font-size: 13px; font-weight: 700; color: #143d2e; }
.promise-field input, .promise-field select, .promise-field textarea {
  font-weight: 500;
  border: 1px solid #e3eee8;
  border-radius: 8px;
  padding: 8px 10px;
  background: #fff;
}
.promise-hint { margin: 0; font-size: 12px; color: #64748b; }
.dossier-hits { list-style: none; margin: 0; padding: 0; border: 1px solid #e3eee8; border-radius: 10px; overflow: hidden; }
.dossier-hits button { display: flex; flex-direction: column; width: 100%; text-align: left; padding: 8px 10px; border: 0; background: #fff; cursor: pointer; }
.dossier-hits button:hover { background: #f3faf6; }
.dossier-hits span { font-size: 12px; color: #64748b; }
.dossier-picked { display: flex; justify-content: space-between; gap: 8px; margin: 0; padding: 8px 10px; border-radius: 10px; background: #f3faf6; }
.dossier-picked button { border: 0; background: transparent; color: #1a4d3a; font-weight: 700; cursor: pointer; }
.podium { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 12px; align-items: stretch; }
.podium article {
  --pod: #d97706;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 14px;
  background: #fff;
  border: 1px solid #e7eeea;
  border-top: 3px solid var(--pod);
  box-shadow: 0 1px 2px rgba(18, 38, 28, 0.04);
  color: #12261c;
}
.podium article.is-agency { --pod: #15803d; }
.podium article.is-zone { --pod: #2563eb; }
.podium-ico {
  display: grid;
  place-items: center;
  flex: 0 0 46px;
  width: 46px;
  height: 46px;
  border-radius: 12px;
  background: #fff4e5;
  color: var(--pod);
}
.podium article.is-agency .podium-ico { background: #e8f6ee; }
.podium article.is-zone .podium-ico { background: #e7f0fb; }
.podium-ico :deep(svg) { width: 26px; height: 26px; }
.podium-copy { min-width: 0; flex: 1; }
.kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--pod);
}
.podium-name { display: block; margin-top: 2px; font-size: 17px; line-height: 1.2; color: #12261c; }
.podium-tro {
  margin-left: auto;
  font-size: 26px;
  font-weight: 800;
  line-height: 1;
  letter-spacing: -0.03em;
  color: var(--pod);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.perf-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; align-items: start; }
.perf-card {
  background: #fff;
  border: 1px solid #e7eeea;
  border-radius: 16px;
  box-shadow: 0 8px 18px rgba(20, 40, 30, 0.05);
  overflow: hidden;
}
.perf-head { display: flex; align-items: center; gap: 10px; padding: 12px 14px; }
.perf-card.top-caf .perf-head { background: #e7f6ee; }
.perf-card.flop-caf .perf-head { background: #fde8ec; }
.perf-card.top-agency .perf-head { background: #e7f0fb; }
.perf-card.flop-agency .perf-head { background: #fff1dc; }
.perf-head h2 { margin: 0; font-size: 15px; color: #14563a; }
.perf-card.flop-caf .perf-head h2 { color: #9f1239; }
.perf-card.top-agency .perf-head h2 { color: #1d3f73; }
.perf-card.flop-agency .perf-head h2 { color: #9a3412; }
.perf-ico { display: grid; place-items: center; width: 28px; height: 28px; border-radius: 8px; background: #fff; color: #14563a; }
.perf-card.flop-caf .perf-ico { color: #be123c; }
.perf-card.top-agency .perf-ico { color: #1d3f73; }
.perf-card.flop-agency .perf-ico { color: #c2410c; }
.perf-ico :deep(svg) { width: 16px; height: 16px; }
.rank-list { list-style: none; margin: 0; padding: 6px 12px 14px; }
.rank-list li { display: flex; align-items: center; gap: 12px; padding: 10px 8px; border-radius: 12px; }
.rank-list li + li { margin-top: 2px; }
.rank-index {
  display: grid;
  place-items: center;
  flex: 0 0 28px;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  background: #e8f6ee;
  color: #14563a;
  font-size: 13px;
  font-weight: 800;
}
.perf-card.is-top .pos-1 { background: #14563a; color: #fff; }
.perf-card.is-top .pos-2 { background: #3d8f68; color: #fff; }
.perf-card.is-top .pos-3 { background: #b7d8c6; color: #143d2e; }
.perf-card.is-flop .rank-index { background: #fde8ea; color: #be123c; }
.rank-id { min-width: 0; flex: 1; }
.rank-line { display: flex; align-items: baseline; gap: 8px; min-width: 0; }
.rank-name { font-weight: 700; color: #12261c; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-hint { flex: 0 1 auto; font-size: 12px; color: #7b8b84; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.rank-meta { display: block; margin-top: 2px; font-size: 12px; color: #7b8b84; font-variant-numeric: tabular-nums; }
.track { display: block; height: 6px; margin-top: 8px; border-radius: 999px; background: #eef3f0; overflow: hidden; }
.track em { display: block; height: 100%; border-radius: inherit; background: #1f8a4c; }
.perf-card.flop-caf .track em { background: #e11d48; }
.perf-card.top-agency .track em { background: #2563eb; }
.perf-card.flop-agency .track em { background: #ea580c; }
.rank-list .rate {
  flex: 0 0 auto;
  min-width: 72px;
  padding: 6px 8px;
  border-radius: 10px;
  background: #e8f6ee;
  color: #146c3a;
  text-align: center;
  font-size: 13px;
  font-variant-numeric: tabular-nums;
}
.perf-card.flop-caf .rate { background: #fff; color: #be123c; }
.perf-card.top-agency .rate { background: #fff; color: #1d4ed8; }
.perf-card.flop-agency .rate { background: #fff; color: #c2410c; }
.perf-card.top-agency .rank-index { background: #dbe7f8; color: #1d3f73; }
.perf-card.top-agency .pos-1 { background: #1d3f73; color: #fff; }
.perf-card.top-agency .pos-2 { background: #3b6cb5; color: #fff; }
.perf-card.top-agency .pos-3 { background: #b9ccee; color: #1d3f73; }
.perf-card.flop-agency .rank-index { background: #ffedd5; color: #c2410c; }
.perf-card .empty { margin: 0; padding: 8px 18px 20px; }
@media (max-width: 1100px) {
  .podium, .perf-grid { grid-template-columns: 1fr; }
}
</style>
