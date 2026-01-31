<script setup>
import { ref, onMounted } from 'vue'
import UfChart from './components/UFChart.vue'
import { useOperadoras } from './composables/useOperadoras' // Importando a lógica

// Usando o Composable (Extraindo o que precisamos)
const { 
  operadoras, 
  metadata, 
  loading, 
  totalPages, 
  selectedOperadora, 
  fetchOperadoras, 
  fetchDetalhes 
} = useOperadoras()

// Estado Local (Coisas que são só da tela, não da regra de negócio)
const viewMode = ref('list')
const searchQuery = ref('')
const ufData = ref({ labels: [], datasets: [] })

// Funções de Interface (Ligam a tela à lógica)
const handleSearch = () => fetchOperadoras(1, searchQuery.value)

const nextPage = () => {
  if (metadata.value.page < totalPages.value) fetchOperadoras(metadata.value.page + 1, searchQuery.value)
}

const prevPage = () => {
  if (metadata.value.page > 1) fetchOperadoras(metadata.value.page - 1, searchQuery.value)
}

const openDetails = async (cnpj) => {
  const success = await fetchDetalhes(cnpj)
  if (success) viewMode.value = 'details'
}

const backToList = () => {
  viewMode.value = 'list'
  selectedOperadora.value = null
}

// Gráfico 
import axios from 'axios' // Só para o gráfico
const fetchUfStats = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/estatisticas/uf')
  if(res.data.length > 0) {
    ufData.value = {
      labels: res.data.map(i => i.uf),
      datasets: [
        { 
          label: 'Total', 
          backgroundColor: '#3B82F6', 
          hoverBackgroundColor: '#60A5FA', 
          borderRadius: 6, 
          barThickness: 24, 
          borderSkipped: false, 
          data: res.data.map(i => i.total) }]
    }
  }
}

const formatMoney = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)

onMounted(() => {
  fetchOperadoras()
  fetchUfStats()
})
</script>

<template>
  <div class="min-h-screen w-full bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
    
    <div class="w-full h-full py-10 px-4">
      
      <header class="mb-8 text-center">
        <h1 class="text-4xl font-extrabold text-blue-900 dark:text-blue-400 tracking-tight">Dashboard ANS</h1>
        <p class="mt-2 text-lg text-gray-600 dark:text-gray-400">Visão geral e consulta de operadoras</p>
      </header>

      <div v-if="viewMode === 'list'" class="space-y-8">
        
        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-6">
          <h2 class="text-lg font-semibold text-gray-700 dark:text-gray-200 mb-4">
            Distribuição por Estado
          </h2>          
          <div class="h-64 w-full">
             <UfChart v-if="ufData.labels.length" :chartData="ufData" />
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 p-10 flex flex-col md:flex-row gap-8 items-center justify-between">
          <div class="w-full">
             <label class="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-3">Pesquisar Operadora</label>
             <div class="relative">
               <input 
                 v-model="searchQuery" 
                 @keyup.enter="handleSearch" 
                 placeholder="Digite o CNPJ ou registro..." 
                 class="w-full pl-4 pr-12 py-3 rounded-lg
                  bg-white dark:bg-gray-900
                  text-gray-900 dark:text-gray-100
                  border border-gray-300 dark:border-gray-700
                  focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                  outline-none transition-all" 
               />
               <button 
                 @click="handleSearch"
                 class="absolute right-2 top-2 bottom-2 bg-blue-600 text-white px-4 rounded-md hover:bg-blue-700 font-medium text-sm"
               >
                 Buscar
               </button>
             </div>
          </div>
          <div class="text-sm text-gray-500 dark:text-gray-400">
            Total de registros: <span class="font-bold text-gray-900 dark:text-gray-100">{{ metadata.total }}</span>
          </div>
        </div>

        <div class="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-200 dark:border-gray-700 overflow-hidden">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th class="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Registro ANS</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">CNPJ</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Razão Social</th>
                  <th class="px-6 py-4 text-xs font-bold text-gray-500 dark:text-gray-400 uppercase tracking-wider">Ações</th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="op in operadoras" :key="op.cnpj" class="hover:bg-blue-50 dark:hover:bg-gray-700 transition-colors duration-150">
                  <td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">
                    {{ op.registro_ans }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-500 dark:text-gray-400">
                    {{ op.cnpj }}
                  </td>
                  <td class="px-6 py-4 text-sm text-gray-700 dark:text-gray-300">
                    {{ op.razao_social }}
                  </td>
                  <td class="px-6 py-4 whitespace-nowrap text-center text-sm font-medium">
                    <button 
                      @click="openDetails(op.cnpj)" 
                      class="text-blue-600 dark:text-blue-400
                        bg-blue-50 dark:bg-blue-900/30
                        hover:bg-blue-100 dark:hover:bg-blue-900/50
                        px-3 py-1 rounded-full transition-colors"
                    >
                      Ver Detalhes
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="bg-gray-50 dark:bg-gray-900 px-6 py-4 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <button 
              @click="prevPage" 
              :disabled="metadata.page === 1" 
              class="px-4 py-2 border rounded-md text-sm font-medium
                bg-white dark:bg-gray-800
                text-gray-700 dark:text-gray-300
                border-gray-300 dark:border-gray-700
                hover:bg-gray-50 dark:hover:bg-gray-700
                disabled:opacity-50"
            >
              Anterior
            </button>
            <span class="text-sm text-gray-300">
              Página <span class="font-bold">{{ metadata.page }}</span> de <span class="font-bold">{{ totalPages }}</span>
            </span>
            <button 
              @click="nextPage" 
              :disabled="metadata.page >= totalPages" 
              class="px-4 py-2 border rounded-md text-sm font-medium
                bg-white dark:bg-gray-800
                text-gray-700 dark:text-gray-300
                border-gray-300 dark:border-gray-700
                hover:bg-gray-50 dark:hover:bg-gray-700
                disabled:opacity-50"
            >
              Próximo
            </button>
          </div>
        </div>

      </div>

      <div v-else class="max-w-4xl mx-auto
         bg-white dark:bg-gray-800
         rounded-xl shadow-lg
         border border-gray-200 dark:border-gray-700
         overflow-hidden animate-fade-in-up"
        >
        <div class="bg-blue-600 dark:bg-blue-700 px-8 py-6">
          <button @click="backToList" class="text-white hover:text-blue-100 flex items-center mb-4 transition-colors">
            <span class="mr-2 text-xl">←</span> Voltar para lista
          </button>
          <h2 class="text-2xl font-bold text-white mb-1" v-if="selectedOperadora">{{ selectedOperadora.info.razao_social }}</h2>
          <div class="flex gap-4 text-blue-100 text-sm" v-if="selectedOperadora">
             <span>CNPJ: {{ selectedOperadora.info.cnpj }}</span>
             <span>|</span>
             <span>Registro: {{ selectedOperadora.info.registro_ans }}</span>
          </div>
        </div>

        <div class="p-8">
          <h3 class="text-lg font-bold
             text-gray-800 dark:text-gray-100
             mb-6 border-b
             border-gray-200 dark:border-gray-700
             pb-2"
            >
              Histórico Financeiro
            </h3>
          
          <div class="overflow-hidden border rounded-lg border-gray-200 dark:border-gray-700" v-if="selectedOperadora">
            <table class="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
              <thead class="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Ano</th>
                  <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Período</th>
                  <th class="px-6 py-3 text-right text-xs font-bold text-gray-500 dark:text-gray-400 uppercase">Despesa Assistencial</th>
                </tr>
              </thead>
              <tbody class="bg-white dark:bg-gray-800 divide-y divide-gray-200 dark:divide-gray-700">
                <tr v-for="(hist, index) in selectedOperadora.historico" :key="index" class="hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
                  <td class="px-6 py-4 text-sm text-gray-900 dark:text-gray-100">{{ hist.ano }}</td>
                  <td class="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{{ hist.trimestre }}º Trimestre</td>
                  <td class="px-6 py-4 text-sm text-right font-mono font-bold text-blue-700 dark:text-gray-400">
                    {{ formatMoney(hist.valor_despesa) }}
                  </td>
                </tr>
                <tr v-if="!selectedOperadora.historico.length">
                  <td colspan="3" class="px-6 py-8 text-center text-gray-500 dark:text-gray-400">Nenhum dado financeiro disponível.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>