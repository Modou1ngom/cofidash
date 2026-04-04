<template>
  <div class="prepaid-card-recharge-section">
    <div class="section-header">
      <h2 class="section-title">
        <span class="title-text">Rechargement Cartes <span class="title-highlight">prépayées</span></span>
        <span class="card-icon">💳</span>
      </h2>
    </div>

    <div class="content-container">
      <!-- Tableau de données -->
      <div class="table-container">
        <table class="recharge-table">
          <thead>
            <tr>
              <th>AGENCE</th>
              <th>Objectif</th>
              <th>Rechargement M-1</th>
              <th>Rechargement M</th>
              <th>Ecart</th>
              <th>Variation (%)</th>
              <th>Atteinte</th>
              <th>Contribution agence sur la zone</th>
            </tr>
          </thead>
          <tbody>
            <!-- TERRITOIRE -->
            <tr class="category-row">
              <td class="category-cell">
                <button class="expand-btn">+</button>
                <strong>TERRITOIRE</strong>
              </td>
              <td><strong>375</strong></td>
              <td><strong>31,91</strong></td>
              <td><strong>13,06</strong></td>
              <td class="negative"><strong>-18,85</strong></td>
              <td class="negative"><strong>-59%</strong></td>
              <td class="negative"><strong>3%</strong></td>
              <td class="contribution"><strong>95%</strong></td>
            </tr>

            <!-- TERRITOIRE DAKAR VILLE -->
            <tr class="sub-agency level-2-row">
              <td class="indent-cell level-2">
                <button class="expand-btn">+</button>
                TERRITOIRE DAKAR VILLE
              </td>
              <td><strong>245</strong></td>
              <td><strong>24,67</strong></td>
              <td><strong>11,11</strong></td>
              <td class="negative"><strong>-13,56</strong></td>
              <td class="negative"><strong>-55%</strong></td>
              <td class="negative"><strong>5%</strong></td>
              <td class="contribution"><strong>81%</strong></td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">POINT E</td>
              <td>80</td>
              <td>7,78</td>
              <td>6,33</td>
              <td class="negative">-1,45</td>
              <td class="negative">-19%</td>
              <td class="negative">8%</td>
              <td class="contribution">57%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">NIARRY TALLY</td>
              <td>30</td>
              <td>0,55</td>
              <td>0,18</td>
              <td class="negative">-0,37</td>
              <td class="negative">-67%</td>
              <td class="negative">1%</td>
              <td class="contribution">2%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">CASTOR</td>
              <td>30</td>
              <td>16,33</td>
              <td>4,50</td>
              <td class="negative">-11,84</td>
              <td class="negative">-72%</td>
              <td class="negative">15%</td>
              <td class="contribution">40%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">PARCELLES</td>
              <td>30</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">LAMINE GUEYE</td>
              <td>30</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>

            <!-- TERRITOIRE DAKAR BANLIEUE -->
            <tr class="sub-agency level-2-row">
              <td class="indent-cell level-2">
                <button class="expand-btn">+</button>
                TERRITOIRE DAKAR BANLIEUE
              </td>
              <td><strong>75</strong></td>
              <td><strong>0</strong></td>
              <td><strong>0,10</strong></td>
              <td class="positive"><strong>0,10</strong></td>
              <td>0%</td>
              <td class="negative"><strong>0%</strong></td>
              <td class="contribution"><strong>1%</strong></td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">PIKINE</td>
              <td>37</td>
              <td>-</td>
              <td>0,10</td>
              <td class="positive">0,10</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="contribution">1%</td>
            </tr>

            <!-- TERRITOIRE PROVINCE CENTRE-SUD -->
            <tr class="sub-agency level-2-row">
              <td class="indent-cell level-2">
                <button class="expand-btn">+</button>
                TERRITOIRE PROVINCE CENTRE-SUD
              </td>
              <td><strong>130</strong></td>
              <td><strong>7,24</strong></td>
              <td><strong>1,96</strong></td>
              <td class="negative"><strong>-5,29</strong></td>
              <td class="negative"><strong>-73%</strong></td>
              <td class="negative"><strong>2%</strong></td>
              <td class="contribution"><strong>14%</strong></td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">MBOUR</td>
              <td>30</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">KAOLACK</td>
              <td>20</td>
              <td>7,17</td>
              <td>1,96</td>
              <td class="negative">-5,21</td>
              <td class="negative">-73%</td>
              <td class="negative">10%</td>
              <td class="contribution">100%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">THIES</td>
              <td>25</td>
              <td>0,07</td>
              <td>-</td>
              <td class="negative">-0,07</td>
              <td class="negative">-100%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">TOUBA</td>
              <td>35</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">SAINT-LOUIS</td>
              <td>20</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>

            <!-- TERRITOIRE PROVINCE NORD -->
            <tr class="sub-agency level-2-row">
              <td class="indent-cell level-2">
                <button class="expand-btn">+</button>
                TERRITOIRE PROVINCE NORD
              </td>
              <td><strong>45</strong></td>
              <td><strong>0</strong></td>
              <td><strong>0</strong></td>
              <td><strong>0</strong></td>
              <td>0%</td>
              <td class="negative"><strong>0%</strong></td>
              <td class="negative"><strong>0%</strong></td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">SAINT-LOUIS</td>
              <td>20</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">DIOURBEL</td>
              <td>7</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">LOUGA</td>
              <td>8</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">OUROSSOGUI</td>
              <td>5</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">TAMBA</td>
              <td>8</td>
              <td>-</td>
              <td>-</td>
              <td>-</td>
              <td>0%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>
            <tr class="sub-agency">
              <td class="indent-cell level-3">LINGUERE'LA</td>
              <td>7</td>
              <td>4,69</td>
              <td>-</td>
              <td class="negative">-4,69</td>
              <td class="negative">-100%</td>
              <td class="negative">0%</td>
              <td class="negative">0%</td>
            </tr>

            <!-- TOTAL -->
            <tr class="total-row">
              <td class="category-cell">TOTAL</td>
              <td><strong>450</strong></td>
              <td><strong>36,59</strong></td>
              <td><strong>13,79</strong></td>
              <td class="negative"><strong>-22,80</strong></td>
              <td class="negative"><strong>-62%</strong></td>
              <td class="negative"><strong>3%</strong></td>
              <td>-</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Graphiques -->
      <div class="charts-container">
        <!-- Pie Chart - Contribution des zones -->
        <div class="chart-wrapper">
          <h3 class="chart-title">CONTRIBUTION DES ZONES</h3>
          <div class="chart-container">
            <canvas ref="contributionChart"></canvas>
          </div>
        </div>

        <!-- Bar Chart - TOP 5 -->
        <div class="chart-wrapper">
          <h3 class="chart-title">TOP 5 RECHARGEMENT CARTE</h3>
          <div class="chart-container">
            <canvas ref="top5Chart"></canvas>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend
);

export default {
  name: 'PrepaidCardRechargeSection',
  setup() {
    const contributionChart = ref(null);
    const top5Chart = ref(null);
    let contributionChartInstance = null;
    let top5ChartInstance = null;

    const createCharts = async () => {
      await nextTick();
      
      // Pie Chart - Contribution des zones
      if (contributionChart.value) {
        try {
          const ctx = contributionChart.value.getContext('2d');
          
          if (!ctx) {
            console.error('Impossible d\'obtenir le contexte 2D pour Contribution');
            return;
          }
          
          if (contributionChartInstance) {
            contributionChartInstance.destroy();
          }

          contributionChartInstance = new ChartJS(ctx, {
            type: 'pie',
            data: {
              labels: ['ZONE DAKAR', 'ZONE PROVINCE', 'RETAIL'],
              datasets: [{
                label: 'Contribution',
                data: [81, 14, 5],
                backgroundColor: ['#808080', '#DC2626', '#DC2626'],
                borderWidth: 0
              }]
            },
            options: {
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: true,
                  position: 'bottom',
                  labels: {
                    color: '#ffffff',
                    font: {
                      size: 11
                    },
                    padding: 15
                  }
                },
                tooltip: {
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  titleColor: '#fff',
                  bodyColor: '#fff',
                  padding: 10,
                  callbacks: {
                    label: function(context) {
                      return `${context.label}: ${context.parsed}%`;
                    }
                  }
                }
              }
            }
          });
        } catch (error) {
          console.error('Erreur lors de la création du graphique Contribution:', error);
        }
      } else {
        console.warn('Référence contributionChart.value est null');
      }

      // TOP 5 Bar Chart
      if (top5Chart.value) {
        try {
          const ctx = top5Chart.value.getContext('2d');
          
          if (!ctx) {
            console.error('Impossible d\'obtenir le contexte 2D pour TOP 5');
            return;
          }
          
          if (top5ChartInstance) {
            top5ChartInstance.destroy();
          }

          top5ChartInstance = new ChartJS(ctx, {
            type: 'bar',
            data: {
              labels: ['CASTOR', 'KAOLACK', 'POINT E', 'MARISTES', 'NIARRY TALLY'],
              datasets: [{
                label: 'Rechargement',
                data: [0.15, 0.10, 0.07, 0.02, 0.005],
                backgroundColor: '#DC2626',
                borderRadius: 0
              }]
            },
            options: {
              indexAxis: 'y',
              responsive: true,
              maintainAspectRatio: false,
              plugins: {
                legend: {
                  display: false
                },
                tooltip: {
                  backgroundColor: 'rgba(0, 0, 0, 0.8)',
                  titleColor: '#fff',
                  bodyColor: '#fff',
                  padding: 10,
                  callbacks: {
                    label: function(context) {
                      return `Rechargement: ${context.parsed.x}`;
                    }
                  }
                }
              },
              scales: {
                x: {
                  beginAtZero: true,
                  max: 0.16,
                  ticks: {
                    stepSize: 0.02,
                    font: {
                      size: 11
                    },
                    color: '#e5e7eb'
                  },
                  grid: {
                    color: 'rgba(255, 255, 255, 0.1)',
                    lineWidth: 1
                  }
                },
                y: {
                  ticks: {
                    font: {
                      size: 11
                    },
                    color: '#e5e7eb'
                  },
                  grid: {
                    color: 'rgba(255, 255, 255, 0.1)',
                    lineWidth: 1
                  }
                }
              }
            }
          });
        } catch (error) {
          console.error('Erreur lors de la création du graphique TOP 5:', error);
        }
      } else {
        console.warn('Référence top5Chart.value est null');
      }
    };

    onMounted(async () => {
      await nextTick();
      setTimeout(async () => {
        await nextTick();
        console.log('Initialisation des graphiques de rechargement...', {
          contributionChart: contributionChart.value,
          top5Chart: top5Chart.value
        });
        await createCharts();
      }, 200);
    });

    onBeforeUnmount(() => {
      if (contributionChartInstance) {
        contributionChartInstance.destroy();
      }
      if (top5ChartInstance) {
        top5ChartInstance.destroy();
      }
    });

    return {
      contributionChart,
      top5Chart
    };
  }
}
</script>

<style scoped>
.prepaid-card-recharge-section {
  width: 100%;
  padding: 30px;
  background: #FFFFFF;
  min-height: calc(100vh - 100px);
  position: relative;
}

.section-header {
  margin-bottom: 30px;
  position: relative;
  z-index: 1;
}

.section-title {
  font-size: 36px;
  font-weight: 800;
  color: #1f2937;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 15px;
  letter-spacing: 1px;
}

.title-text {
  color: #1f2937;
}

.title-highlight {
  color: #DC2626;
  -webkit-text-fill-color: #DC2626;
}

.card-icon {
  font-size: 40px;
  color: #DC2626;
  filter: 
    drop-shadow(0 0 10px rgba(220, 38, 38, 0.8))
    drop-shadow(0 0 20px rgba(220, 38, 38, 0.4));
}

.content-container {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 30px;
  position: relative;
  z-index: 1;
}

.table-container {
  overflow-x: auto;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.recharge-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
  min-width: 1200px;
  font-size: 13px;
}

.recharge-table thead {
  background: #DC2626;
  color: white;
}

.recharge-table th {
  padding: 12px 8px;
  text-align: center;
  font-weight: 600;
  font-size: 12px;
  border-right: 1px solid #444;
  white-space: nowrap;
}

.recharge-table th:first-child {
  text-align: left;
  padding-left: 16px;
}

.recharge-table td {
  padding: 10px 8px;
  font-size: 13px;
  text-align: center;
  border-bottom: 1px solid #EEE;
  border-right: 1px solid #F0F0F0;
}

.recharge-table td:first-child {
  text-align: left;
  padding-left: 16px;
}

.category-row {
  background: #2A2A2A;
  color: white;
  font-weight: 700;
  cursor: pointer;
}

.category-cell {
  font-size: 16px;
  padding-left: 16px !important;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  color: white;
}

.sub-agency {
  background: white;
}

.sub-agency:hover {
  background: #f5f5f5;
}

.indent-cell {
  padding-left: 48px !important;
  color: #333;
  cursor: pointer;
}

.level-3 {
  padding-left: 48px !important;
  color: #333;
  cursor: pointer;
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

.expand-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.positive {
  color: #10B981;
  font-weight: 600;
}

.negative {
  color: #EF4444;
  font-weight: 600;
}

.contribution {
  color: #10B981;
  font-weight: 600;
}

.total-row {
  background: #F5F5F5;
  font-weight: 600;
}

.total-row td {
  border-top: 2px solid #333;
  border-bottom: 2px solid #333;
  color: #333;
}

.charts-container {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.chart-wrapper {
  background: #2a2a2a;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  border: none;
  min-height: 250px;
  display: flex;
  flex-direction: column;
}

.chart-title {
  font-size: 16px;
  font-weight: 700;
  color: #ffffff;
  margin-bottom: 15px;
  text-align: center;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.chart-container {
  height: 200px;
  position: relative;
  background: #2a2a2a;
  flex: 1;
  width: 100%;
  min-height: 200px;
  display: block;
  overflow: hidden;
}

.chart-container canvas {
  display: block !important;
  width: 100% !important;
  height: 100% !important;
}

@media (max-width: 1200px) {
  .content-container {
    grid-template-columns: 1fr;
  }
  
  .charts-container {
    flex-direction: row;
  }
  
  .chart-wrapper {
    flex: 1;
  }
}

@media (max-width: 768px) {
  .prepaid-card-recharge-section {
    padding: 15px;
  }
  
  .section-title {
    font-size: 24px;
  }
  
  .card-icon {
    font-size: 28px;
  }
  
  .charts-container {
    flex-direction: column;
  }
  
  .recharge-table {
    font-size: 11px;
  }
  
  .recharge-table th,
  .recharge-table td {
    padding: 8px 4px;
  }
}
</style>
