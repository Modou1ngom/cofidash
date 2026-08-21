<template>
  <div class="python-chart-container" :style="containerStyle">
    <div v-if="loading && !error" class="chart-loading" :style="containerStyle">
      <p>Chargement du graphique...</p>
    </div>
    <div v-if="error" class="chart-error" :style="containerStyle">
      <p>{{ error }}</p>
      <button @click="loadChart" class="retry-btn">Réessayer</button>
    </div>
    <div
      ref="chartContainer"
      class="chart-wrapper"
      :style="{ ...wrapperStyle, display: loading || error ? 'none' : 'block' }"
    ></div>
  </div>
</template>

<script>
import { ref, onMounted, watch, onBeforeUnmount, nextTick, computed } from 'vue';
import axios from 'axios';
import Plotly from 'plotly.js-dist';

export default {
  name: 'PythonChart',
  props: {
    chartType: {
      type: String,
      required: true,
      validator: (value) => ['line', 'bar', 'groupedbar', 'multiseries', 'area', 'pie'].includes(value)
    },
    chartData: {
      type: Object,
      required: true
    },
    height: {
      type: Number,
      default: 400
    }
  },
  setup(props) {
    const chartContainer = ref(null);
    const loading = ref(true);
    const error = ref(null);

    const containerStyle = computed(() => ({
      minHeight: `${props.height}px`,
      height: `${props.height}px`,
    }));

    const wrapperStyle = computed(() => ({
      minHeight: `${props.height}px`,
      height: `${props.height}px`,
    }));

    const loadChart = async () => {
      loading.value = true;
      error.value = null;

      try {
        if (typeof Plotly === 'undefined') {
          error.value = 'Plotly n\'est pas chargé. Vérifiez l\'installation.';
          loading.value = false;
          return;
        }

        // Attendre que le conteneur soit disponible
        await nextTick();
        
        // Si le conteneur n'est pas disponible, attendre un peu plus
        let attempts = 0;
        while (!chartContainer.value && attempts < 5) {
          await new Promise(resolve => setTimeout(resolve, 100));
          await nextTick();
          attempts++;
        }
        
        if (!chartContainer.value) {
          error.value = 'Conteneur de graphique non disponible. Veuillez recharger la page.';
          loading.value = false;
          return;
        }

        // Déterminer l'endpoint selon le type de graphique
        let endpoint = '/api/charts/evolution'; // Par défaut
        
        if (props.chartType === 'bar') {
          endpoint = '/api/charts/barchart';
        } else if (props.chartType === 'groupedbar') {
          endpoint = '/api/charts/groupedbar';
        } else if (props.chartType === 'multiseries') {
          endpoint = '/api/charts/multiseries';
        } else if (props.chartType === 'area') {
          endpoint = '/api/charts/timeseries';
        } else if (props.chartType === 'pie') {
          endpoint = '/api/charts/pie';
        }

        const response = await axios.post(endpoint, props.chartData);

        if (response.data && response.data.chart) {
          let chartData = response.data.chart;
          
          // Pour les aires, convertir en graphique en aires
          if (props.chartType === 'area' && chartData.data) {
            chartData = {
              ...chartData,
              data: chartData.data.map(trace => ({
                ...trace,
                fill: 'tonexty',
                mode: 'lines',
                line: { ...trace.line, shape: 'spline' }
              }))
            };
          }

          if (chartContainer.value) {
            // S'assurer que le layout utilise toute la largeur
            let layout = {
              ...chartData.layout,
              autosize: true,
              width: null,
              height: props.height,
            };
            
            // Ajuster les marges selon le type de graphique
            const hasTitle = Boolean(chartData.layout?.title?.text);
            const compact = props.height <= 220;

            if (props.chartType === 'pie') {
              layout.margin = {
                l: 8,
                r: 8,
                t: hasTitle ? 40 : 8,
                b: compact ? 72 : 60,
              };
            } else {
              layout.margin = {
                l: compact ? 56 : 72,
                r: compact ? 48 : 16,
                t: hasTitle ? 52 : 28,
                b: compact ? 48 : 55,
              };
            }
            
            await Plotly.newPlot(
              chartContainer.value,
              chartData.data,
              layout,
              {
                responsive: true,
                autosizable: true,
                displayModeBar: false,
                displaylogo: false,
                locale: 'fr',
                useResizeHandler: true
              }
            );
            
            // Mettre à jour loading avant de redimensionner pour que le conteneur soit visible
            loading.value = false;
            
            // Attendre que le DOM soit mis à jour et que le conteneur soit visible
            await nextTick();
            await new Promise(resolve => setTimeout(resolve, 50));
            
            // Vérifier que l'élément est visible avant de redimensionner
            if (chartContainer.value && chartContainer.value.offsetParent !== null) {
              try {
                Plotly.Plots.resize(chartContainer.value);
              } catch (resizeErr) {
                console.warn('Erreur lors du redimensionnement du graphique:', resizeErr);
                // Ne pas bloquer l'affichage du graphique si le resize échoue
              }
            }
          }
        } else {
          error.value = 'Format de données invalide reçu du serveur';
          loading.value = false;
        }
      } catch (err) {
        console.error('Erreur lors de la génération du graphique:', err);
        error.value = err.response?.data?.message || err.message || 'Erreur lors de la génération du graphique';
        loading.value = false;
      }
    };

    const resizeChart = () => {
      if (chartContainer.value && chartContainer.value.offsetParent !== null) {
        try {
          Plotly.Plots.resize(chartContainer.value);
        } catch (resizeErr) {
          console.warn('Erreur lors du redimensionnement du graphique:', resizeErr);
        }
      }
    };

    onMounted(async () => {
      // Attendre plusieurs cycles pour s'assurer que le DOM est complètement rendu
      await nextTick();
      await new Promise(resolve => setTimeout(resolve, 100));
      await nextTick();
      
      // Vérifier que le conteneur est disponible
      if (!chartContainer.value) {
        console.warn('Conteneur non disponible immédiatement, nouvelle tentative...');
        await new Promise(resolve => setTimeout(resolve, 200));
        await nextTick();
        
        if (!chartContainer.value) {
          error.value = 'Conteneur de graphique non disponible. Veuillez recharger la page.';
          loading.value = false;
          return;
        }
      }
      
      // Charger le graphique
      loadChart();
      
      window.addEventListener('resize', resizeChart);
    });

    watch([() => props.chartType, () => props.chartData, () => props.height], () => {
      loadChart();
    }, { deep: true });

    onBeforeUnmount(() => {
      window.removeEventListener('resize', resizeChart);
      if (chartContainer.value) {
        Plotly.purge(chartContainer.value);
      }
    });

    return {
      chartContainer,
      loading,
      error,
      loadChart,
      containerStyle,
      wrapperStyle,
    };
  }
}
</script>

<style scoped>
.python-chart-container {
  width: 100%;
  position: relative;
  display: flex;
  flex-direction: column;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.chart-wrapper {
  width: 100% !important;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

.chart-loading,
.chart-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  width: 100%;
  background: #f5f5f5;
  border-radius: 4px;
  gap: 10px;
}

.chart-error {
  color: #dc2626;
}

.chart-loading p,
.chart-error p {
  font-size: 14px;
}

.retry-btn {
  padding: 8px 16px;
  background: #1A4D3A;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.retry-btn:hover {
  background: #153d2a;
}
</style>
