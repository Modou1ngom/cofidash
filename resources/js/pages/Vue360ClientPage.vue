<template>
  <div class="vue360-client-page">
    <div class="vue360-content" v-if="loading">
      <p class="loading">Chargement du client…</p>
    </div>
    <div class="vue360-content" v-else-if="error">
      <p class="error-msg">{{ error }}</p>
      <router-link to="/vue360/recherche" class="back-link">← Retour à la recherche</router-link>
    </div>
    <div class="vue360-content" v-else-if="client">
      <router-link to="/vue360/recherche" class="back-link">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M15 18l-6-6 6-6" stroke-linecap="round" stroke-linejoin="round"/></svg>
        Retour à la recherche
      </router-link>

      <div class="client-hero">
        <div class="client-header">
          <div class="avatar">{{ initials }}</div>
          <div class="client-info">
            <h1>{{ client.full_name }}</h1>
            <p class="client-meta">
              <span>{{ client.id }}</span>
              <span class="dot">·</span>
              <span>{{ client.segment }}</span>
            </p>
            <p class="client-agency">{{ client.agency }}</p>
          </div>
          <span class="status-badge" :class="client.status">{{ statusLabel(client.status) }}</span>
        </div>

        <nav class="tabs" aria-label="Sections client">
          <button
            v-for="tab in tabs"
            :key="tab.id"
            type="button"
            class="tab"
            :class="{ active: activeTab === tab.id }"
            @click="activeTab = tab.id"
          >
            {{ tab.label }}
          </button>
        </nav>
      </div>

      <div v-show="activeTab === 'synthese'" class="panel">
        <section class="synthese-section">
          <h3 class="section-title">Soldes</h3>
          <div class="kpi-grid kpi-grid--soldes">
            <div class="kpi-card kpi-card--solde">
              <span class="kpi-label">Solde comptable</span>
              <strong class="kpi-value kpi-value--money kpi-value--positive">{{ formatMoney(summary.solde_comptable) }}</strong>
            </div>
            <div class="kpi-card kpi-card--solde">
              <span class="kpi-label">Solde net</span>
              <strong class="kpi-value kpi-value--money kpi-value--positive">{{ formatMoney(summary.solde_net) }}</strong>
            </div>
            <div class="kpi-card kpi-card--exigible">
              <span class="kpi-label">Exigible</span>
              <strong class="kpi-value kpi-value--money kpi-value--danger">{{ formatMoney(summary.total_exigible) }}</strong>
            </div>
          </div>
        </section>

        <section class="synthese-section">
          <div class="section-head">
            <h3 class="section-title">Montant global dû</h3>
            <span class="section-total">{{ formatMoney(repartitionTotal) }}</span>
          </div>
          <div
            v-if="encoursRepartition.length"
            class="repartition-bar"
            :class="{ 'repartition-bar--zero': encoursRepartitionAllZero }"
            role="presentation"
          >
            <div
              v-for="item in encoursRepartitionBar"
              :key="item.id"
              class="repartition-segment"
              :style="{
                width: `${item.percent || 0}%`,
                background: item.color,
                opacity: item.muted ? 0.28 : 1,
              }"
              :title="`${item.label} : ${formatMoney(item.amount)}`"
            />
          </div>
          <ul class="repartition-list">
            <li v-for="item in encoursRepartition" :key="item.id" class="repartition-item">
              <span class="repartition-dot" :style="{ background: item.color }" />
              <span class="repartition-label">{{ item.label }}</span>
              <strong class="repartition-amount">{{ formatMoney(item.amount) }}</strong>
              <span class="repartition-percent">{{ item.percent }} %</span>
            </li>
          </ul>
        </section>

        <section class="synthese-section">
          <h3 class="section-title">Dernier mouvement crédit</h3>
          <div v-if="lastCreditMovement" class="last-movement-card">
            <div class="last-movement-main">
              <span class="last-movement-date">{{ formatDate(lastCreditMovement.date) }}</span>
              <strong class="last-movement-label">{{ lastCreditMovement.label }}</strong>
              <span v-if="lastCreditMovement.loan_number" class="last-movement-loan">
                Prêt {{ lastCreditMovement.loan_number }}
              </span>
            </div>
            <strong
              class="last-movement-amount"
              :class="lastCreditMovement.direction === 'credit' ? 'credit' : 'debit'"
            >
              {{ lastCreditMovement.direction === 'credit' ? '+' : '−' }}{{ formatMoney(lastCreditMovement.amount) }}
            </strong>
          </div>
          <p v-else class="empty-inline">Aucun mouvement crédit enregistré</p>
        </section>

        <section class="synthese-section synthese-section--secondary">
          <div class="kpi-grid kpi-grid--3">
            <div class="kpi-card kpi-card--risk">
              <span class="kpi-label">Score risque</span>
              <strong v-if="hasActiveCredit" class="kpi-value">
                {{ summary.risk_score }} <small>/ {{ summary.risk_score_max || 1000 }}</small>
              </strong>
              <strong v-else class="kpi-value kpi-value--muted">—</strong>
              <span class="kpi-hint">{{ creditRiskLabel }}</span>
            </div>
            <div class="kpi-card kpi-card--eligibility">
              <span class="kpi-label">Éligibilité crédit</span>
              <strong class="kpi-value">{{ creditEligibilityLabel }}</strong>
              <span class="kpi-hint">{{ creditEligibilityHint }}</span>
            </div>
            <div class="kpi-card kpi-card--encours">
              <span class="kpi-label">Encours crédit</span>
              <strong class="kpi-value" :class="{ 'kpi-value--money': hasActiveCredit, 'kpi-value--muted': !hasActiveCredit }">
                {{ hasActiveCredit ? formatMoney(creditEncoursTotal) : 'Aucun crédit' }}
              </strong>
            </div>
          </div>
          <div class="stats-row">
            <div class="stat-item">
              <span class="stat-label">Segmentation</span>
              <span class="stat-value">{{ summary.segmentation || client.segment }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Agence</span>
              <span class="stat-value">{{ summary.agency || client.agency }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">Taux remboursement</span>
              <span class="stat-value">{{ hasActiveCredit ? `${summary.repayment_rate ?? 0} %` : '—' }}</span>
            </div>
            <button
              type="button"
              class="stat-item stat-item--clickable"
              :title="hasActiveCredit ? 'Voir le détail des crédits' : 'Ouvrir l’onglet Crédits'"
              @click="openCreditsTab"
            >
              <span class="stat-label">PAR (jours)</span>
              <span class="stat-value">
                {{ hasActiveCredit ? (summary.par_days ?? 0) : '—' }}
                <svg class="stat-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true">
                  <path d="M9 18l6-6-6-6" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </span>
            </button>
          </div>
        </section>
      </div>

      <div v-show="activeTab === 'kyc'" class="panel">
        <div v-if="kycLoading" class="loading">Chargement KYC…</div>
        <template v-else-if="kyc">
          <div v-if="kyc.record_stat" class="kyc-status-row">
            <span class="kyc-status-label">Statut dossier</span>
            <span class="kyc-status-badge" :class="kycStatusClass">{{ kycStatusLabel }}</span>
          </div>
          <div class="kyc-sections">
            <div
              v-for="section in kycDisplaySections"
              :key="section.id"
              class="kyc-section-card"
            >
              <div class="kyc-section-head">
                <span class="kyc-section-icon">{{ section.icon }}</span>
                <h3>{{ section.title }}</h3>
              </div>
              <div class="kyc-fields">
                <div
                  v-for="field in section.fields"
                  :key="field.key"
                  class="kyc-field"
                >
                  <span class="kyc-field-label">{{ field.label }}</span>
                  <span class="kyc-field-value">{{ formatKycField(field) }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
        <p v-else class="empty">KYC indisponible</p>
      </div>

      <div v-show="activeTab === 'banque'" class="panel">
        <div v-if="accountsLoading" class="loading">Chargement comptes…</div>
        <template v-else>
          <div class="bank-type-filters">
            <button
              v-for="t in accountTypes"
              :key="t.id"
              type="button"
              class="bank-type-btn"
              :class="{ active: selectedAccountType === t.id }"
              @click="selectAccountType(t.id)"
            >
              <span class="bank-type-icon">{{ accountTypeIcon(t.id) }}</span>
              <span class="bank-type-label">{{ t.label }}</span>
              <span class="bank-type-count">{{ t.count }}</span>
            </button>
          </div>

          <section v-if="filteredAccounts.length" class="account-list-section">
            <h3 class="section-title">Comptes</h3>
            <ul class="account-list">
              <li
                v-for="acc in filteredAccounts"
                :key="acc.account_number"
                class="account-card"
                :class="{ selected: selectedAccount?.account_number === acc.account_number }"
                @click="selectAccount(acc)"
              >
                <div class="account-card-main">
                  <span class="account-type">{{ acc.type_description || acc.type_label }}</span>
                  <strong class="account-number">{{ acc.account_number }}</strong>
                </div>
                <div class="account-card-balance">
                  <span class="balance-label">Solde</span>
                  <strong>{{ formatMoney(acc.balance) }}</strong>
                </div>
              </li>
            </ul>
          </section>
          <p v-else class="empty">Aucun compte pour ce type</p>

          <div v-if="selectedAccount" class="account-detail">
            <div class="account-detail-head">
              <h4>Compte {{ selectedAccount.account_number }}</h4>
              <span class="account-detail-type">{{ selectedAccount.type_description || selectedAccount.type_label }}</span>
            </div>
            <div class="stats-row stats-row--bank">
              <div class="stat-item">
                <span class="stat-label">Agence</span>
                <span class="stat-value">{{ selectedAccount.branch_name || '—' }}</span>
              </div>
              <div class="stat-item stat-item--highlight">
                <span class="stat-label">Solde comptable</span>
                <span class="stat-value stat-value--money">{{ formatMoney(selectedAccount.balance) }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">Solde disponible</span>
                <span class="stat-value stat-value--money">{{ formatMoney(selectedAccount.available_balance) }}</span>
              </div>
              <div class="stat-item" :class="{ 'stat-item--due': (selectedAccount.amount_due || 0) > 0 }">
                <span class="stat-label">Montant dû</span>
                <span class="stat-value stat-value--money">{{ formatMoney(selectedAccount.amount_due) }}</span>
              </div>
            </div>
            <div
              v-if="selectedAccount.transactions?.length"
              class="transactions-block"
            >
              <h5 class="transactions-title">Dernières écritures</h5>
              <ul class="transactions-list">
                <li v-for="(tx, i) in selectedAccount.transactions.slice(0, 5)" :key="i" class="tx-row">
                  <span class="tx-date">{{ formatTxDate(tx) }}</span>
                  <span class="tx-label">{{ tx.entry_label || tx.description || tx.batch_label || 'Opération' }}</span>
                  <strong class="tx-amount" :class="tx.direction === 'credit' ? 'credit' : 'debit'">
                    {{ tx.direction === 'credit' ? '+' : '−' }}{{ formatMoney(Math.abs(tx.amount || tx.credit || tx.debit || 0)) }}
                  </strong>
                </li>
              </ul>
            </div>
          </div>
        </template>
      </div>

      <div v-show="activeTab === 'credits'" class="panel">
        <div v-if="creditsLoading" class="loading">Chargement crédits…</div>
        <template v-else>
          <section class="credits-global">
            <h3 class="section-title">Vue globale</h3>
            <div class="kpi-grid kpi-grid--credits">
              <div class="kpi-card kpi-card--encours">
                <span class="kpi-label">Encours global</span>
                <strong class="kpi-value kpi-value--money">{{ formatMoney(creditsSummary.encours_global) }}</strong>
                <span class="kpi-hint">{{ creditsSummary.encours_global_label || 'Capital + intérêts + pénalités' }}</span>
              </div>
              <div class="kpi-card kpi-card--eligibility">
                <span class="kpi-label">Encours sain</span>
                <strong class="kpi-value kpi-value--money kpi-value--sain">{{ formatMoney(creditsSummary.total_encours_sain) }}</strong>
              </div>
              <div class="kpi-card kpi-card--risk">
                <span class="kpi-label">Encours impayé</span>
                <strong class="kpi-value kpi-value--money kpi-value--impaye">{{ formatMoney(creditsSummary.total_encours_impaye) }}</strong>
              </div>
              <div class="kpi-card kpi-card--due">
                <span class="kpi-label">Total exigible</span>
                <strong class="kpi-value kpi-value--money">{{ formatMoney(creditsSummary.total_exigible) }}</strong>
              </div>
              <div class="kpi-card kpi-card--score">
                <span class="kpi-label">Soft scoring</span>
                <strong class="kpi-value kpi-value--score">{{ creditsSummary.soft_scoring ?? '—' }} <small>/ 100</small></strong>
              </div>
            </div>
          </section>

          <div class="credit-filters">
            <button
              v-for="f in creditFilters"
              :key="f.id"
              type="button"
              class="credit-filter-btn"
              :class="{ active: creditFilter === f.id, [`filter--${f.id}`]: true }"
              @click="creditFilter = f.id"
            >
              <span class="credit-filter-icon">{{ creditFilterIcon(f.id) }}</span>
              <span class="credit-filter-label">{{ f.label }}</span>
              <span class="credit-filter-count">{{ f.count }}</span>
            </button>
          </div>

          <section v-if="filteredCredits.length" class="credit-list-section">
            <h3 class="section-title">Liste des crédits</h3>
            <ul class="credit-list">
              <li
                v-for="(credit, index) in filteredCredits"
                :key="credit.id"
                class="credit-card"
                :class="{ expanded: selectedCredit?.id === credit.id, [`health--${credit.health_status}`]: true }"
              >
                <div class="credit-card-row">
                  <span class="credit-label">Prêt {{ index + 1 }}</span>
                  <div class="credit-summary-line">
                    <span class="credit-summary-item credit-summary-item--number">{{ credit.loan_number }}</span>
                    <span class="credit-summary-sep">/</span>
                    <span class="credit-summary-item">{{ formatMoney(credit.financed_amount) }}</span>
                    <span class="credit-summary-sep">/</span>
                    <span class="credit-summary-item credit-summary-item--encours">{{ formatMoney(creditEncours(credit)) }}</span>
                    <span class="credit-summary-sep">/</span>
                    <span class="credit-summary-item">{{ formatDisbursementDate(credit.disbursement_date) }}</span>
                  </div>
                  <div class="credit-actions">
                    <button
                      type="button"
                      class="credit-action-btn"
                      :class="{ active: selectedCredit?.id === credit.id && creditPanelMode === 'detail' }"
                      @click="openCreditPanel(credit, 'detail')"
                    >
                      Détail
                    </button>
                    <button
                      type="button"
                      class="credit-action-btn credit-action-btn--ta"
                      :class="{ active: selectedCredit?.id === credit.id && creditPanelMode === 'ta' }"
                      @click="openCreditPanel(credit, 'ta')"
                    >
                      TA
                    </button>
                  </div>
                </div>
                <div v-if="selectedCredit?.id === credit.id && creditPanelMode === 'detail'" class="credit-detail">
                  <div class="stats-row stats-row--credit stats-row--detail">
                    <div class="stat-item">
                      <span class="stat-label">Statut</span>
                      <span class="stat-value">{{ loanStatusLabel(credit) }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Compte</span>
                      <span class="stat-value stat-value--mono">{{ credit.linked_account || '—' }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Solde</span>
                      <span class="stat-value stat-value--money">{{ formatMoney(credit.account_balance) }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Type de prêt</span>
                      <span class="stat-value">{{ creditProductLabel(credit) }}</span>
                    </div>
                    <div class="stat-item">
                      <span class="stat-label">Chargé d'affaires</span>
                      <span class="stat-value">{{ credit.manager || '—' }}</span>
                    </div>
                    <div class="stat-item stat-item--highlight">
                      <span class="stat-label">Encours total</span>
                      <span class="stat-value stat-value--money">{{ formatMoney(credit.total_outstanding || credit.outstanding) }}</span>
                    </div>
                    <div class="stat-item" :class="{ 'stat-item--due': (credit.unpaid_amount || 0) > 0 }">
                      <span class="stat-label">Impayé</span>
                      <span class="stat-value stat-value--money">{{ formatMoney(credit.unpaid_amount) }}</span>
                    </div>
                    <div class="stat-item stat-item--repayment">
                      <span class="stat-label">% remboursé</span>
                      <span class="stat-value">{{ credit.repayment_percent ?? 0 }} %</span>
                      <div class="repayment-bar" role="presentation">
                        <div class="repayment-bar-fill" :style="{ width: `${Math.min(100, credit.repayment_percent || 0)}%` }" />
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else-if="selectedCredit?.id === credit.id && creditPanelMode === 'ta'" class="credit-ta">
                  <div v-if="taLoading" class="credit-ta-loading">Chargement du tableau d'amortissement…</div>
                  <p v-else-if="taError" class="credit-ta-error">{{ taError }}</p>
                  <div v-else-if="taData" class="credit-ta-table-wrap">
                    <table class="credit-ta-table">
                      <thead>
                        <tr>
                          <th>N°</th>
                          <th>Date échéance</th>
                          <th>Montant</th>
                          <th>Payé</th>
                          <th>Impayé</th>
                          <th>Pénalité</th>
                          <th>Exigible</th>
                          <th>Statut</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr
                          v-for="row in taData.installments"
                          :key="`${credit.id}-${row.installment_number}`"
                          :class="`ta-row--${row.status}`"
                        >
                          <td>{{ row.installment_number }}</td>
                          <td>{{ formatDate(row.due_date) }}</td>
                          <td>{{ formatMoney(row.installment_amount) }}</td>
                          <td>{{ formatMoney(row.paid_amount) }}</td>
                          <td>{{ formatMoney(row.unpaid_amount) }}</td>
                          <td>{{ formatMoney(row.penalty) }}</td>
                          <td>{{ formatMoney(row.due_total) }}</td>
                          <td>
                            <span class="ta-status" :class="`ta-status--${row.status}`">
                              {{ row.status_label || '—' }}
                            </span>
                          </td>
                        </tr>
                      </tbody>
                      <tfoot v-if="taData.totals && Object.keys(taData.totals).length">
                        <tr class="ta-totals-row">
                          <td colspan="2"><strong>Total</strong></td>
                          <td>{{ formatMoney(taData.totals.installment_amount) }}</td>
                          <td>{{ formatMoney(taData.totals.paid_amount) }}</td>
                          <td>{{ formatMoney(taData.totals.unpaid_amount) }}</td>
                          <td>{{ formatMoney(taData.totals.penalty) }}</td>
                          <td>{{ formatMoney(taData.totals.due_total) }}</td>
                          <td />
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                  <p v-else class="empty">Aucune échéance pour ce prêt</p>
                </div>
              </li>
            </ul>
          </section>
          <p v-else class="empty">Aucun crédit pour ce filtre</p>
        </template>
      </div>
    </div>
  </div>
</template>

<script>
const DEFAULT_ENCOURS_REPARTITION = [
  { id: 'capital', label: 'Capital dû', amount: 0, percent: 0, color: '#14B8A6' },
  { id: 'interest', label: 'Intérêt dû', amount: 0, percent: 0, color: '#EAB308' },
  { id: 'ftc', label: 'FTC dû', amount: 0, percent: 0, color: '#3B82F6' },
  { id: 'acs', label: 'Charge ACS dû', amount: 0, percent: 0, color: '#8B5CF6' },
  { id: 'opening_fee', label: "Frais d'ouverture dû", amount: 0, percent: 0, color: '#F59E0B' },
  { id: 'coficarte_fee', label: 'Frais coficarte dû', amount: 0, percent: 0, color: '#EC4899' },
];

export default {
  name: 'Vue360ClientPage',
  data() {
    return {
      client: null,
      summary: {},
      kyc: null,
      accountsData: null,
      credits: [],
      creditsSummary: {},
      creditFilter: 'all',
      selectedCredit: null,
      creditPanelMode: null,
      taData: null,
      taLoading: false,
      taError: '',
      loading: true,
      kycLoading: false,
      accountsLoading: false,
      creditsLoading: false,
      error: '',
      activeTab: 'synthese',
      selectedAccountType: null,
      selectedAccount: null,
      tabs: [
        { id: 'synthese', label: 'Synthèse' },
        { id: 'kyc', label: 'KYC' },
        { id: 'banque', label: 'Banque au quotidien' },
        { id: 'credits', label: 'Crédits' },
      ],
    };
  },
  computed: {
    clientId() {
      return this.$route.params.id;
    },
    initials() {
      const name = this.client?.full_name || '';
      return name.split(' ').slice(0, 2).map((p) => p[0]).join('').toUpperCase() || '?';
    },
    kycSections() {
      return this.kyc?.sections || [];
    },
    kycDisplaySections() {
      if (this.kycSections.length) {
        return this.kycSections.map((s) => ({
          id: s.id,
          title: s.title,
          icon: s.icon || '📋',
          fields: (s.fields || []).filter((f) => f.value),
        }));
      }
      if (!this.kyc) return [];
      const groups = [
        {
          id: 'identite',
          title: 'Identité',
          icon: '🪪',
          fields: [
            { key: 'full_name', label: 'Nom complet' },
            { key: 'categorie', label: 'Catégorie' },
            { key: 'customer_no', label: 'N° client' },
            { key: 'numero_nafa', label: 'Numéro NAFA' },
            { key: 'date_of_birth', label: 'Date de naissance' },
            { key: 'place_of_birth', label: 'Lieu de naissance' },
            { key: 'sex', label: 'Sexe' },
          ],
        },
        {
          id: 'contact',
          title: 'Contact',
          icon: '📞',
          fields: [
            { key: 'telephone', label: 'Téléphone' },
            { key: 'mobile_number', label: 'Mobile' },
            { key: 'e_mail', label: 'E-mail' },
            { key: 'd_address1', label: 'Adresse' },
          ],
        },
        {
          id: 'piece',
          title: "Pièce d'identité",
          icon: '🆔',
          fields: [
            { key: 'unique_id_name', label: 'Type de pièce' },
            { key: 'unique_id_value', label: 'N° pièce' },
            { key: 'p_national_id', label: 'CNI' },
            { key: 'passport_no', label: 'Passeport' },
            { key: 'ppt_exp_date', label: 'Expiration passeport' },
          ],
        },
        {
          id: 'agence',
          title: 'Agence & rattachement',
          icon: '🏦',
          fields: [
            { key: 'branch_name', label: 'Agence' },
            { key: 'local_branch', label: 'Code agence' },
            { key: 'date_creation', label: 'Date création' },
            { key: 'cust_cat_desc', label: 'Segment client' },
          ],
        },
      ];
      return groups
        .map((g) => ({
          ...g,
          fields: g.fields
            .map((f) => ({ ...f, value: this.kyc[f.key] }))
            .filter((f) => f.value),
        }))
        .filter((g) => g.fields.length > 0);
    },
    kycStatusLabel() {
      const s = (this.kyc?.record_stat || '').toUpperCase();
      if (s === 'O' || s === 'OUVERT') return 'Ouvert';
      if (s === 'C' || s === 'CLOS') return 'Clos';
      return this.kyc?.record_stat || '—';
    },
    kycStatusClass() {
      const s = (this.kyc?.record_stat || '').toUpperCase();
      if (s === 'O' || s === 'OUVERT') return 'open';
      if (s === 'C' || s === 'CLOS') return 'closed';
      return 'neutral';
    },
    accountTypes() {
      return this.accountsData?.types || [];
    },
    filteredAccounts() {
      if (!this.accountsData?.accounts) return [];
      if (!this.selectedAccountType) return this.accountsData.accounts;
      return this.accountsData.accounts.filter((a) => a.type === this.selectedAccountType);
    },
    creditFilters() {
      const counts = this.creditsSummary.counts || {};
      return [
        { id: 'all', label: 'Tous', count: this.credits.length },
        { id: 'sain', label: 'Sain', count: counts.sain || 0 },
        { id: 'impaye', label: 'Impayé', count: counts.impaye || 0 },
        { id: 'solde', label: 'Soldé', count: counts.solde || 0 },
      ];
    },
    filteredCredits() {
      if (this.creditFilter === 'all') return this.credits;
      return this.credits.filter((c) => c.health_status === this.creditFilter);
    },
    encoursRepartition() {
      const raw =
        this.summary?.encours_repartition
        || this.summary?.encours_breakdown
        || this.summary?.outstanding_distribution
        || [];
      return raw.length ? raw : DEFAULT_ENCOURS_REPARTITION;
    },
    repartitionTotal() {
      const due = Number(this.summary?.total_due_amount ?? 0);
      if (due > 0) return due;
      return this.encoursRepartition.reduce(
        (sum, item) => sum + (Number(item.amount) || 0),
        0,
      );
    },
    encoursRepartitionWithAmount() {
      return this.encoursRepartition.filter((item) => (item.amount || 0) > 0);
    },
    encoursRepartitionAllZero() {
      return this.encoursRepartition.length > 0 && !this.encoursRepartitionWithAmount.length;
    },
    encoursRepartitionBar() {
      const withAmount = this.encoursRepartitionWithAmount;
      if (withAmount.length) return withAmount;
      const slice = 100 / this.encoursRepartition.length;
      return this.encoursRepartition.map((item) => ({
        ...item,
        percent: slice,
        muted: true,
      }));
    },
    lastCreditMovement() {
      return this.summary?.last_credit_movement || null;
    },
    hasActiveCredit() {
      if (this.summary?.has_active_credit === false) return false;
      if (this.summary?.has_active_credit === true) return true;
      const count = Number(this.summary?.active_credits_count ?? this.client?.active_credits_count ?? 0);
      const encours = Number(
        this.summary?.credit_encours_global
        ?? this.summary?.encours_credit
        ?? this.client?.total_outstanding
        ?? 0,
      );
      return count > 0 || encours > 0 || this.credits.length > 0;
    },
    creditEncoursTotal() {
      return Number(
        this.summary?.credit_encours_global
        ?? this.summary?.encours_credit
        ?? this.summary?.encours_global
        ?? 0,
      );
    },
    creditRiskLabel() {
      if (!this.hasActiveCredit) return 'Sans crédit actif';
      return this.summary?.risk_label || '—';
    },
    creditEligibilityLabel() {
      if (!this.hasActiveCredit) return 'À étudier';
      return this.summary?.eligibility_label || '—';
    },
    creditEligibilityHint() {
      if (!this.hasActiveCredit) return 'Dossier crédit à constituer';
      const suggested = Number(this.summary?.suggested_amount ?? 0);
      if (suggested > 0) return `${this.formatMoney(suggested)} suggéré`;
      return 'Montant à valider en agence';
    },
  },
  watch: {
    activeTab(tab) {
      if (tab === 'kyc' && !this.kyc) this.loadKyc();
      if (tab === 'banque' && !this.accountsData) this.loadAccounts();
      if (tab === 'credits' && !this.credits.length && !this.creditsLoading) this.loadCredits();
    },
    clientId: {
      immediate: true,
      handler() {
        this.loadClient();
      },
    },
  },
  methods: {
    openCreditsTab() {
      this.activeTab = 'credits';
      if (!this.credits.length && !this.creditsLoading) {
        this.loadCredits();
      }
    },
    async loadClient() {
      this.loading = true;
      this.error = '';
      this.kyc = null;
      this.accountsData = null;
      this.credits = [];
      this.creditsSummary = {};
      this.creditFilter = 'all';
      this.selectedCredit = null;
      try {
        const { data } = await window.axios.get(`/api/v1/clients/${encodeURIComponent(this.clientId)}`);
        this.client = data.data;
        this.summary = this.client.summary || {};
      } catch (err) {
        this.error = err.response?.data?.message || 'Client introuvable';
      } finally {
        this.loading = false;
      }
    },
    async loadKyc() {
      this.kycLoading = true;
      try {
        const { data } = await window.axios.get(`/api/v1/clients/${encodeURIComponent(this.clientId)}/kyc`);
        this.kyc = data.data;
      } catch {
        this.kyc = null;
      } finally {
        this.kycLoading = false;
      }
    },
    async loadAccounts() {
      this.accountsLoading = true;
      try {
        const { data } = await window.axios.get(`/api/v1/clients/${encodeURIComponent(this.clientId)}/accounts`);
        this.accountsData = data.data;
        const firstType = this.accountTypes.find((t) => t.count > 0);
        if (firstType) {
          this.selectAccountType(firstType.id);
        }
      } catch {
        this.accountsData = { types: [], accounts: [] };
      } finally {
        this.accountsLoading = false;
      }
    },
    async selectAccountType(typeId) {
      this.selectedAccountType = typeId;
      this.selectedAccount = null;
      try {
        const { data } = await window.axios.get(
          `/api/v1/clients/${encodeURIComponent(this.clientId)}/accounts`,
          { params: { type: typeId } },
        );
        this.accountsData = data.data;
        if (this.filteredAccounts.length) {
          await this.selectAccount(this.filteredAccounts[0]);
        }
      } catch {
        /* ignore */
      }
    },
    async selectAccount(acc) {
      this.selectedAccount = acc;
      try {
        const { data } = await window.axios.get(
          `/api/v1/clients/${encodeURIComponent(this.clientId)}/accounts/${encodeURIComponent(acc.account_number)}`,
        );
        this.selectedAccount = { ...acc, ...data.data };
      } catch {
        /* keep list row data */
      }
    },
    async loadCredits() {
      this.creditsLoading = true;
      this.selectedCredit = null;
      this.creditPanelMode = null;
      this.taData = null;
      this.taError = '';
      try {
        const { data } = await window.axios.get('/api/v1/credits', {
          params: { client_id: this.clientId },
        });
        const payload = data.data;
        if (payload && payload.summary) {
          this.creditsSummary = payload.summary;
          this.credits = payload.credits || [];
        } else {
          this.credits = Array.isArray(payload) ? payload : [];
          this.creditsSummary = {};
        }
      } catch {
        this.credits = [];
        this.creditsSummary = {};
      } finally {
        this.creditsLoading = false;
      }
    },
    openCreditPanel(credit, mode) {
      const same = this.selectedCredit?.id === credit.id && this.creditPanelMode === mode;
      if (same) {
        this.selectedCredit = null;
        this.creditPanelMode = null;
        this.taData = null;
        this.taError = '';
        return;
      }
      this.selectedCredit = credit;
      this.creditPanelMode = mode;
      if (mode === 'ta') {
        this.loadTa(credit);
      } else {
        this.taData = null;
        this.taError = '';
      }
    },
    async loadTa(credit) {
      this.taLoading = true;
      this.taData = null;
      this.taError = '';
      try {
        const loanId = credit.loan_number || credit.id;
        const { data } = await window.axios.get(`/api/v1/credits/${encodeURIComponent(loanId)}/ta`);
        this.taData = data.data || null;
      } catch {
        this.taError = 'Impossible de charger le tableau d\'amortissement.';
      } finally {
        this.taLoading = false;
      }
    },
    healthLabel(status) {
      if (status === 'sain') return 'Sain';
      if (status === 'impaye') return 'Impayé';
      if (status === 'solde') return 'Soldé';
      return status || '—';
    },
    creditProductLabel(credit) {
      const label = String(credit.product_type || '').trim();
      const code = String(credit.product_code || '').trim();
      if (label && label !== code && !/^\d+$/.test(label)) return label;
      if (code && !/^\d+$/.test(code)) return code;
      if (code) return `Produit ${code}`;
      return 'Crédit';
    },
    creditEncours(credit) {
      return credit.total_outstanding ?? credit.outstanding ?? 0;
    },
    loanStatusLabel(credit) {
      const flex = {
        A: 'Financé',
        L: 'Soldé',
        V: 'Annulé',
        Y: 'Futur déblocage',
        H: 'En attente',
      };
      const code = String(credit.account_status || '').toUpperCase();
      if (flex[code]) return flex[code];
      return this.healthLabel(credit.health_status);
    },
    formatDate(value) {
      if (!value) return '—';
      const raw = String(value).trim();
      const iso = raw.match(/^(\d{4})-(\d{2})-(\d{2})/);
      if (iso) {
        return `${iso[3]}/${iso[2]}/${iso[1]}`;
      }
      const d = new Date(raw);
      if (Number.isNaN(d.getTime())) return raw;
      return d.toLocaleDateString('fr-FR', { day: '2-digit', month: '2-digit', year: 'numeric' });
    },
    formatKycField(field) {
      if (!field?.value) return '—';
      if (/date|naissance|birth|expir|creation/i.test(field.key || field.label || '')) {
        return this.formatDate(field.value);
      }
      return field.value;
    },
    formatDisbursementDate(value) {
      return this.formatDate(value);
    },
    formatMoney(value) {
      const n = Number(value) || 0;
      return `${n.toLocaleString('fr-FR')} FCFA`;
    },
    formatTxDate(tx) {
      const raw = tx.accounting_date || tx.date_comptable || tx.value_date || tx.date_valeur || tx.date || '';
      return this.formatDate(raw);
    },
    accountTypeIcon(typeId) {
      const icons = {
        courant: '💳',
        epargne: '🏦',
        dat: '📅',
        depot_garantie: '🔒',
      };
      return icons[typeId] || '📋';
    },
    creditFilterIcon(filterId) {
      const icons = {
        all: '📊',
        sain: '✓',
        impaye: '⚠',
        solde: '✔',
      };
      return icons[filterId] || '📋';
    },
    statusLabel(status) {
      if (status === 'active') return 'Actif';
      if (status === 'at_risk') return 'À risque';
      return status || '—';
    },
  },
};
</script>

<style scoped>
.vue360-client-page {
  min-height: 100%;
  background: transparent;
}

.vue360-content {
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 20px 28px 40px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 16px;
  padding: 8px 14px;
  color: #1a4d3a;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 500;
  font-size: 0.875rem;
  transition: background 0.15s, border-color 0.15s;
}

.back-link svg {
  width: 18px;
  height: 18px;
}

.back-link:hover {
  background: #f0fdf4;
  border-color: #86efac;
}

.client-hero {
  background: #fff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(26, 77, 58, 0.08);
  border: 1px solid rgba(26, 77, 58, 0.06);
  margin-bottom: 20px;
}

.client-header {
  display: flex;
  align-items: center;
  gap: 20px;
  background: linear-gradient(135deg, #1a4d3a 0%, #2d6a4f 60%, #1e293b 100%);
  color: white;
  padding: 28px 32px;
}

.avatar {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  border: 3px solid rgba(255, 255, 255, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 1.35rem;
  flex-shrink: 0;
}

.client-info {
  flex: 1;
  min-width: 0;
}

.client-header h1 {
  margin: 0 0 6px;
  font-size: clamp(1.25rem, 2.5vw, 1.6rem);
  font-weight: 700;
  letter-spacing: -0.02em;
}

.client-meta {
  margin: 0 0 4px;
  font-size: 0.9rem;
  opacity: 0.9;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.client-meta .dot {
  opacity: 0.6;
}

.client-agency {
  margin: 0;
  font-size: 0.85rem;
  opacity: 0.75;
}

.status-badge {
  margin-left: auto;
  padding: 8px 16px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
  flex-shrink: 0;
}

.status-badge.active {
  background: #22c55e;
  color: #fff;
}

.status-badge.at_risk {
  background: #f59e0b;
  color: #fff;
}

.status-badge.inactive {
  background: #6b7280;
  color: #fff;
}

.tabs {
  display: flex;
  gap: 4px;
  padding: 0 16px;
  background: #f9fafb;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.tab {
  padding: 14px 20px;
  border: none;
  background: transparent;
  cursor: pointer;
  font-weight: 500;
  font-size: 0.9rem;
  color: #6b7280;
  border-bottom: 3px solid transparent;
  margin-bottom: 0;
  transition: color 0.15s, border-color 0.15s;
}

.tab:hover {
  color: #1a4d3a;
}

.tab.active {
  color: #dc2626;
  border-bottom-color: #dc2626;
  background: #fff;
  font-weight: 600;
}

.panel {
  background: white;
  border-radius: 16px;
  padding: 28px 32px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.04);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.kpi-grid--3 {
  grid-template-columns: repeat(3, 1fr);
}

.kpi-grid--soldes {
  grid-template-columns: repeat(3, 1fr);
}

@media (max-width: 900px) {
  .kpi-grid--3,
  .kpi-grid--soldes {
    grid-template-columns: 1fr;
  }
}

.synthese-section {
  margin-bottom: 28px;
}

.synthese-section:last-child {
  margin-bottom: 0;
}

.synthese-section--secondary {
  padding-top: 24px;
  border-top: 1px solid #f3f4f6;
}

.section-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.section-total {
  font-size: 1rem;
  font-weight: 700;
  color: #1a4d3a;
  font-variant-numeric: tabular-nums;
}

.kpi-card--solde {
  border-left: 4px solid #16a34a;
  background: #f0fdf4;
}

.kpi-card--exigible {
  border-left: 4px solid #dc2626;
  background: #fef2f2;
}

.kpi-value--positive {
  color: #16a34a;
}

.kpi-value--danger {
  color: #dc2626;
}

.repartition-bar {
  display: flex;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: #f3f4f6;
  margin-bottom: 16px;
}

.repartition-segment {
  min-width: 2px;
  transition: width 0.3s ease;
}

.repartition-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px 20px;
}

@media (max-width: 720px) {
  .repartition-list {
    grid-template-columns: 1fr;
  }
}

.repartition-item {
  display: grid;
  grid-template-columns: 10px 1fr auto auto;
  align-items: center;
  gap: 8px 10px;
  padding: 10px 12px;
  background: #f9fafb;
  border-radius: 10px;
  border: 1px solid #f3f4f6;
}

.repartition-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.repartition-label {
  font-size: 0.84rem;
  color: #4b5563;
}

.repartition-amount {
  font-size: 0.88rem;
  color: #111827;
  font-variant-numeric: tabular-nums;
}

.repartition-percent {
  font-size: 0.78rem;
  color: #9ca3af;
  min-width: 42px;
  text-align: right;
}

.last-movement-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 18px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  border-left: 4px solid #1a4d3a;
}

.last-movement-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.last-movement-date {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9ca3af;
}

.last-movement-label {
  font-size: 0.95rem;
  color: #111827;
}

.last-movement-loan {
  font-size: 0.8rem;
  color: #6b7280;
  font-family: ui-monospace, monospace;
}

.last-movement-amount {
  font-size: 1.1rem;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

.last-movement-amount.credit {
  color: #16a34a;
}

.last-movement-amount.debit {
  color: #dc2626;
}

.empty-inline {
  margin: 0;
  color: #9ca3af;
  font-size: 0.9rem;
}

@media (max-width: 900px) {
  .kpi-grid--3 {
    grid-template-columns: 1fr;
  }
}

.kpi-card {
  padding: 20px;
  background: #f9fafb;
  border-radius: 12px;
  border: 1px solid #f3f4f6;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.kpi-card--risk { border-left: 4px solid #1d4ed8; }
.kpi-card--eligibility { border-left: 4px solid #16a34a; }
.kpi-card--encours { border-left: 4px solid #1a4d3a; }

.kpi-label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #6b7280;
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #111827;
  line-height: 1.2;
}

.kpi-value small {
  font-size: 0.9rem;
  font-weight: 500;
  color: #9ca3af;
}

.kpi-value--money {
  font-size: 1.25rem;
}

.kpi-hint {
  font-size: 0.82rem;
  color: #6b7280;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  padding-top: 20px;
  border-top: 1px solid #f3f4f6;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stat-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9ca3af;
}

.stat-value {
  font-size: 0.95rem;
  font-weight: 600;
  color: #111827;
}

.kpi-value--muted {
  color: #9ca3af;
  font-size: 1rem;
}

.stat-item--clickable {
  border: none;
  background: transparent;
  text-align: left;
  padding: 0;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.15s;
}

.stat-item--clickable:hover {
  background: #f3f4f6;
}

.stat-item--clickable .stat-value {
  display: inline-flex;
  align-items: center;
  gap: 0.2rem;
  color: #1a4d3a;
}

.stat-chevron {
  width: 14px;
  height: 14px;
  opacity: 0.7;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 12px 24px;
}

.info-grid dt {
  font-size: 0.75rem;
  color: #6b7280;
  margin-bottom: 2px;
}

.info-grid dd {
  margin: 0;
  font-weight: 500;
}

.section-card {
  margin-bottom: 20px;
}

.section-card h3 {
  margin: 0 0 12px;
  color: #1a4d3a;
  font-size: 1rem;
}

/* ── KYC ── */
.kyc-status-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
  padding-bottom: 20px;
  border-bottom: 1px solid #f3f4f6;
}

.kyc-status-label {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9ca3af;
}

.kyc-status-badge {
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 0.8rem;
  font-weight: 600;
}

.kyc-status-badge.open {
  background: #dcfce7;
  color: #166534;
}

.kyc-status-badge.closed {
  background: #fee2e2;
  color: #991b1b;
}

.kyc-status-badge.neutral {
  background: #f3f4f6;
  color: #4b5563;
}

.kyc-sections {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
}

@media (max-width: 900px) {
  .kyc-sections {
    grid-template-columns: 1fr;
  }
}

.kyc-section-card {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 20px;
  border-left: 4px solid #1a4d3a;
}

.kyc-section-head {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 16px;
}

.kyc-section-icon {
  font-size: 1.25rem;
  line-height: 1;
}

.kyc-section-head h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1a4d3a;
}

.kyc-fields {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px 20px;
}

@media (max-width: 600px) {
  .kyc-fields {
    grid-template-columns: 1fr;
  }
}

.kyc-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.kyc-field-label {
  font-size: 0.72rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: #9ca3af;
}

.kyc-field-value {
  font-size: 0.92rem;
  font-weight: 600;
  color: #111827;
  word-break: break-word;
}

.type-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

/* ── Banque au quotidien ── */
.bank-type-filters {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 24px;
}

.bank-type-btn {
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-width: 0;
  padding: 10px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.bank-type-btn:hover {
  border-color: #86efac;
  background: #f9fafb;
}

.bank-type-btn.active {
  border-color: #1a4d3a;
  background: #f0fdf4;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.bank-type-icon {
  font-size: 1.1rem;
  line-height: 1;
  flex-shrink: 0;
}

.bank-type-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
  white-space: nowrap;
}

.bank-type-btn.active .bank-type-label {
  color: #1a4d3a;
}

.bank-type-count {
  font-size: 0.95rem;
  font-weight: 700;
  color: #1a4d3a;
  margin-left: auto;
}

.account-list-section {
  margin-bottom: 24px;
}

.account-card {
  padding: 16px 20px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 10px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  transition: border-color 0.15s, box-shadow 0.15s, background 0.15s;
}

.account-card-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
}

.account-type {
  font-size: 0.78rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #6b7280;
}

.account-number {
  font-size: 0.95rem;
  color: #111827;
  font-family: ui-monospace, monospace;
}

.account-card-balance {
  text-align: right;
  flex-shrink: 0;
}

.balance-label {
  display: block;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
  color: #9ca3af;
  margin-bottom: 2px;
}

.account-card-balance strong {
  font-size: 1.05rem;
  color: #1a4d3a;
}

.account-card:hover {
  border-color: #6e8b7a;
  box-shadow: 0 2px 10px rgba(26, 77, 58, 0.08);
}

.account-card.selected {
  border-color: #1a4d3a;
  background: #f0fdf4;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.08);
}

.account-detail {
  margin-top: 8px;
  padding: 24px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
}

.account-detail-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 20px;
  flex-wrap: wrap;
}

.account-detail-head h4 {
  margin: 0;
  font-size: 1.05rem;
  color: #1a4d3a;
}

.account-detail-type {
  font-size: 0.82rem;
  color: #6b7280;
  font-weight: 500;
}

.stats-row--bank {
  border-top: none;
  padding-top: 0;
}

.stat-item--highlight .stat-value--money {
  color: #1a4d3a;
  font-size: 1.1rem;
}

.stat-item--due .stat-value--money {
  color: #dc2626;
}

.stat-value--money {
  font-variant-numeric: tabular-nums;
}

.transactions-block {
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.transactions-title {
  margin: 0 0 12px;
  font-size: 0.9rem;
  font-weight: 600;
  color: #374151;
}

.transactions-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tx-row {
  display: grid;
  grid-template-columns: 90px 1fr auto;
  gap: 12px;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.85rem;
}

.tx-row:last-child {
  border-bottom: none;
}

.tx-date {
  color: #9ca3af;
  font-size: 0.8rem;
}

.tx-label {
  color: #4b5563;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.tx-amount {
  font-size: 0.88rem;
  font-variant-numeric: tabular-nums;
}

.tx-amount.credit {
  color: #16a34a;
}

.tx-amount.debit {
  color: #dc2626;
}

.type-btn {
  padding: 12px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  min-width: 110px;
  transition: border-color 0.15s, background 0.15s;
}

.type-btn.active {
  border-color: #1a4d3a;
  background: #f0fdf4;
}

.type-btn .count {
  font-size: 1.2rem;
  font-weight: 700;
  color: #1a4d3a;
}

.account-list,
.credit-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.loading,
.empty,
.error-msg {
  color: #6b7280;
  padding: 24px;
  text-align: center;
}

.error-msg {
  color: #dc2626;
}

.section-title {
  margin: 0 0 16px;
  font-size: 1.05rem;
  font-weight: 600;
  color: #1a4d3a;
}

.credits-global {
  margin-bottom: 24px;
}

.kpi-grid--credits {
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
}

.kpi-card--due {
  border-left: 4px solid #d97706;
}

.kpi-card--score {
  border-left: 4px solid #7c3aed;
}

.kpi-value--sain {
  color: #16a34a;
}

.kpi-value--impaye {
  color: #dc2626;
}

.kpi-value--score {
  color: #1d4ed8;
}

.stat-value--mono {
  font-family: ui-monospace, monospace;
  font-size: 0.88rem;
}

.stat-value--impaye {
  color: #dc2626;
  font-weight: 700;
}

/* ── Crédits ── */
.credit-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 24px;
}

.credit-filter-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  min-width: 90px;
  padding: 14px 18px;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  background: #fff;
  cursor: pointer;
  transition: all 0.15s;
}

.credit-filter-btn:hover {
  border-color: #86efac;
  background: #f9fafb;
}

.credit-filter-btn.active {
  border-color: #1a4d3a;
  background: #f0fdf4;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.1);
}

.credit-filter-btn.filter--impaye.active {
  border-color: #dc2626;
  background: #fef2f2;
  box-shadow: 0 0 0 3px rgba(220, 38, 38, 0.08);
}

.credit-filter-icon {
  font-size: 1.1rem;
  line-height: 1;
}

.credit-filter-label {
  font-size: 0.82rem;
  font-weight: 600;
  color: #374151;
}

.credit-filter-btn.active .credit-filter-label {
  color: #1a4d3a;
}

.credit-filter-btn.filter--impaye.active .credit-filter-label {
  color: #dc2626;
}

.credit-filter-count {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1a4d3a;
}

.credit-list-section {
  margin-bottom: 8px;
}

.credit-card {
  padding: 0;
  border: 2px solid #e5e7eb;
  border-radius: 12px;
  margin-bottom: 10px;
  overflow: hidden;
  transition: border-color 0.15s, box-shadow 0.15s;
}

.credit-card:hover {
  border-color: #6e8b7a;
  box-shadow: 0 2px 10px rgba(26, 77, 58, 0.08);
}

.credit-card.expanded {
  border-color: #1a4d3a;
  box-shadow: 0 0 0 3px rgba(26, 77, 58, 0.08);
}

.credit-card.health--impaye {
  border-left: 4px solid #dc2626;
}

.credit-card.health--sain {
  border-left: 4px solid #16a34a;
}

.credit-card.health--solde {
  border-left: 4px solid #9ca3af;
}

.credit-card-row {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  flex-wrap: nowrap;
}

.credit-label {
  flex-shrink: 0;
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.03em;
  color: #1a4d3a;
  min-width: 52px;
}

.credit-summary-line {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 0;
  font-size: 0.88rem;
  color: #374151;
}

.credit-summary-sep {
  margin: 0 10px;
  color: #d1d5db;
  font-weight: 300;
}

.credit-summary-item {
  white-space: nowrap;
}

.credit-summary-item--number {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-weight: 600;
  color: #111827;
}

.credit-summary-item--encours {
  font-weight: 700;
  color: #1a4d3a;
}

.stats-row--detail {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px 20px;
}

@media (max-width: 900px) {
  .stats-row--detail {
    grid-template-columns: repeat(2, 1fr);
  }
}

.credit-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.credit-action-btn {
  border: 1px solid #d1d5db;
  background: #fff;
  color: #374151;
  border-radius: 8px;
  padding: 6px 12px;
  font-size: 0.78rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
}

.credit-action-btn:hover {
  border-color: #1a4d3a;
  color: #1a4d3a;
}

.credit-action-btn.active {
  background: #1a4d3a;
  border-color: #1a4d3a;
  color: #fff;
}

.credit-action-btn--ta.active {
  background: #2563eb;
  border-color: #2563eb;
}

.credit-ta {
  padding: 0 18px 18px;
}

.credit-ta-loading,
.credit-ta-error {
  padding: 16px 0 4px;
  font-size: 0.9rem;
  color: #6b7280;
}

.credit-ta-error {
  color: #dc2626;
}

.credit-ta-table-wrap {
  overflow-x: auto;
  margin-top: 4px;
}

.credit-ta-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.82rem;
}

.credit-ta-table th,
.credit-ta-table td {
  padding: 10px 12px;
  border-bottom: 1px solid #e5e7eb;
  text-align: left;
  white-space: nowrap;
}

.credit-ta-table th {
  background: #f9fafb;
  color: #6b7280;
  font-weight: 700;
  text-transform: uppercase;
  font-size: 0.72rem;
  letter-spacing: 0.03em;
}

.credit-ta-table tbody tr:hover {
  background: #f9fafb;
}

.ta-totals-row td {
  background: #f3f4f6;
  font-weight: 700;
}

.ta-status {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 0.72rem;
  font-weight: 700;
}

.ta-status--i {
  background: #fee2e2;
  color: #dc2626;
}

.ta-status--r {
  background: #dcfce7;
  color: #16a34a;
}

.ta-status--a {
  background: #dbeafe;
  color: #2563eb;
}

.stat-item--repayment {
  min-width: 120px;
}

.repayment-bar {
  margin-top: 8px;
  height: 6px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}

.repayment-bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #1a4d3a, #16a34a);
  border-radius: 999px;
  transition: width 0.3s ease;
}

.credit-detail {
  padding: 20px 24px 24px;
  background: #f9fafb;
  border-top: 1px solid #e5e7eb;
}

.credit-detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.credit-detail-head h4 {
  margin: 0;
  font-size: 1rem;
  color: #1a4d3a;
}

.stats-row--credit {
  border-top: none;
  padding-top: 0;
  margin-bottom: 16px;
}

.stats-row--credit.stats-row--last {
  margin-bottom: 0;
}

.health-badge {
  margin-left: auto;
  padding: 5px 12px;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.health-badge.sain { background: #dcfce7; color: #166534; }
.health-badge.impaye { background: #fee2e2; color: #991b1b; }
.health-badge.solde { background: #e5e7eb; color: #374151; }

@media (max-width: 640px) {
  .vue360-content {
    padding: 16px;
  }

  .client-header {
    flex-wrap: wrap;
    padding: 20px;
  }

  .status-badge {
    margin-left: 0;
  }

  .tabs {
    overflow-x: auto;
    padding: 0 8px;
  }

  .tab {
    padding: 12px 14px;
    font-size: 0.8rem;
    white-space: nowrap;
  }

  .panel {
    padding: 20px 16px;
  }

  .bank-type-filters {
    grid-template-columns: repeat(2, 1fr);
  }

  .credit-card-row {
    flex-wrap: wrap;
    align-items: flex-start;
  }

  .credit-summary-line {
    width: 100%;
  }

  .stats-row--detail {
    grid-template-columns: 1fr;
  }
}
</style>
