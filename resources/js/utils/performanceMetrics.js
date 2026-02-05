/**
 * Utilitaire pour gérer les métriques de performance selon le type de données et l'onglet
 */

/**
 * Détermine les métriques à utiliser selon le type de données et l'onglet
 * @param {string} dataType - Type de données ('client', 'collection', 'credit', etc.)
 * @param {string} collectionTab - Onglet collection ('collecte' ou 'solde')
 * @returns {Object} Objet avec nombreMetric et volumeMetric
 */
export function getPerformanceMetrics(dataType, collectionTab = 'collecte') {
  const metrics = {
    nombreMetric: 'nouveauxClientsM',
    volumeMetric: 'fraisM'
  };

  // Pour la collection, utiliser les métriques selon l'onglet
  if (dataType === 'collection') {
    if (collectionTab === 'collecte') {
      // Pour DOMICILIATION DE FLUX : nombre et volume basés sur collecteM
      metrics.nombreMetric = 'collecteM';
      metrics.volumeMetric = 'collecteM';
    } else if (collectionTab === 'solde') {
      // Pour SOLDE : nombre = sldM (solde du mois), volume = sldM
      metrics.nombreMetric = 'sldM';
      metrics.volumeMetric = 'sldM';
    }
  }

  return metrics;
}

/**
 * Récupère la valeur d'une métrique depuis un objet agence
 * @param {Object} agency - Objet agence
 * @param {string} metric - Nom de la métrique
 * @returns {number} Valeur de la métrique
 */
export function getMetricValue(agency, metric) {
  const metricMap = {
    'nouveauxClientsM': agency.nouveauxClientsM || 0,
    'fraisM': agency.fraisM || 0,
    'collecteM': agency.collecteM || agency.COLLECTE_M || 0,
    'mtEcheance': agency.mtEcheance || agency.MT_ECHEANCE || 0,
    'solde': agency.solde || agency.SOLDE || 0,
    'sldM': agency.sldM || agency.SLD_M || 0
  };

  return metricMap[metric] || 0;
}

/**
 * Extrait les agences depuis les données hiérarchiques
 * @param {Object} data - Données de l'API
 * @param {string} dataType - Type de données
 * @param {string} collectionTab - Onglet collection
 * @param {Function} getAgencyName - Fonction pour obtenir le nom de l'agence
 * @returns {Array} Liste des agences avec leurs métriques
 */
export function extractAgencies(data, dataType, collectionTab, getAgencyName) {
  const agencies = [];
  
  // Extraire les données selon le format de réponse
  let hierarchicalData = null;
  if (data && data.data && data.data.hierarchicalData) {
    hierarchicalData = data.data.hierarchicalData;
  } else if (data && data.hierarchicalData) {
    hierarchicalData = data.hierarchicalData;
  } else if (data && data.data) {
    hierarchicalData = data.data;
  }
  
  if (!hierarchicalData) {
    return agencies;
  }
  
  // Déterminer les métriques à utiliser
  const { nombreMetric, volumeMetric } = getPerformanceMetrics(dataType, collectionTab);
  
  // Fonction pour extraire les agences d'un territoire ou point de service
  const extractFromTerritory = (territory) => {
    if (territory.agencies && Array.isArray(territory.agencies)) {
      territory.agencies.forEach(agency => {
        const agencyName = getAgencyName(agency);
        if (agencyName && agencyName.toUpperCase() !== 'INCONNU' && agencyName.toUpperCase() !== 'UNKNOWN') {
          const nombre = getMetricValue(agency, nombreMetric);
          const volume = getMetricValue(agency, volumeMetric);
          
          agencies.push({
            name: agencyName,
            nouveauxClientsM: agency.nouveauxClientsM || 0,
            nouveauxClientsM1: agency.nouveauxClientsM1 || 0,
            fraisM: agency.fraisM || 0,
            fraisM1: agency.fraisM1 || 0,
            collecteM: agency.collecteM || agency.COLLECTE_M || 0,
            mtEcheance: agency.mtEcheance || agency.MT_ECHEANCE || 0,
            solde: agency.solde || agency.SOLDE || 0,
            sldM: agency.sldM || agency.SLD_M || 0,
            volume: volume,
            nombre: nombre
          });
        }
      });
    }
  };
  
  // Extraire les agences des territoires
  if (hierarchicalData.TERRITOIRE) {
    Object.values(hierarchicalData.TERRITOIRE).forEach(extractFromTerritory);
  }
  
  // Extraire les agences des points de service
  if (hierarchicalData['POINT SERVICES']) {
    Object.values(hierarchicalData['POINT SERVICES']).forEach(extractFromTerritory);
  }
  
  // Si pas de données hiérarchiques, essayer d'autres formats
  if (agencies.length === 0 && data.territories) {
    Object.values(data.territories).forEach(extractFromTerritory);
  }
  
  return agencies;
}
