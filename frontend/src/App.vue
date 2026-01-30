<script setup>
import { ref, onMounted, computed } from 'vue'
import axios from 'axios'
import UfChart from './components/UFChart.vue'

// --- ESTADO ---
const viewMode = ref('list') // 'list' ou 'details'
const selectedOperadora = ref(null) // Dados da operadora selecionada
const operadoras = ref([])
const metadata = ref({ total: 0, page: 1, limit: 10 })
const ufData = ref({ labels: [], datasets: [] })
const searchQuery = ref('')
const loading = ref(false)

// --- FUNÇÕES DE API ---

// 1. Busca Lista
const fetchOperadoras = async (page = 1) => {
  loading.value = true
  try {
    const res = await axios.get('http://127.0.0.1:8000/api/operadoras', {
      params: { page, limit: 10, search: searchQuery.value }
    })
    operadoras.value = res.data.data
    metadata.value = res.data.metadata
  } catch (err) { console.error(err) } 
  finally { loading.value = false }
}

// 2. Busca Gráfico
const fetchUfStats = async () => {
  const res = await axios.get('http://127.0.0.1:8000/api/estatisticas/uf')
  if(res.data.length > 0) {
    ufData.value = {
      labels: res.data.map(i => i.uf),
      datasets: [{ label: 'Total', backgroundColor: '#3b82f6', data: res.data.map(i => i.total) }]
    }
  }
}

// 3. Busca Detalhes (NOVO)
const openDetails = async (cnpj) => {
  loading.value = true
  try {
    const res = await axios.get(`http://127.0.0.1:8000/api/operadoras/${cnpj}/detalhes`)
    selectedOperadora.value = res.data
    viewMode.value = 'details' // Troca a tela
  } catch (err) {
    alert("Erro ao carregar detalhes")
  } finally {
    loading.value = false
  }
}

const backToList = () => {
  viewMode.value = 'list'
  selectedOperadora.value = null
}

const handleSearch = () => fetchOperadoras(1)
const nextPage = () => fetchOperadoras(metadata.value.page + 1)
const prevPage = () => fetchOperadoras(metadata.value.page - 1)
const totalPages = computed(() => Math.ceil(metadata.value.total / metadata.value.limit))

// Formatação de Moeda
const formatMoney = (val) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(val)

onMounted(() => {
  fetchOperadoras()
  fetchUfStats()
})
</script>

<template>
  <div class="min-h-screen bg-gray-100 p-8 font-sans">
    <div class="max-w-6xl mx-auto">
      
      <header class="mb-6">
        <h1 class="text-3xl font-bold text-gray-800">Dashboard ANS</h1>
      </header>

      <div v-if="viewMode === 'list'">
        
        <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div class="lg:col-span-2 bg-white p-4 rounded-lg shadow">
             <UfChart v-if="ufData.labels.length" :chartData="ufData" />
          </div>
          <div class="flex flex-col justify-center gap-4">
             <input v-model="searchQuery" @keyup.enter="handleSearch" placeholder="Buscar operadora..." class="p-3 border rounded shadow-sm" />
             <button @click="handleSearch" class="bg-blue-600 text-white p-3 rounded hover:bg-blue-700">Pesquisar</button>
          </div>
        </div>

        <div class="bg-white rounded-lg shadow overflow-hidden">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Registro</th>
                <th class="px-6 py-3 text-left text-xs font-bold text-gray-500 uppercase">Razão Social</th>
                <th class="px-6 py-3 text-center text-xs font-bold text-gray-500 uppercase">Ação</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-gray-200">
              <tr v-for="op in operadoras" :key="op.cnpj" class="hover:bg-gray-50">
                <td class="px-6 py-4">{{ op.registro_ans }}</td>
                <td class="px-6 py-4">{{ op.razao_social }}</td>
                <td class="px-6 py-4 text-center">
                  <button @click="openDetails(op.cnpj)" class="text-blue-600 hover:text-blue-900 font-bold text-sm">Ver Detalhes</button>
                </td>
              </tr>
            </tbody>
          </table>
          <div class="p-4 flex justify-between bg-gray-50 border-t">
             <button @click="prevPage" :disabled="metadata.page === 1" class="px-4 py-2 border rounded bg-white disabled:opacity-50">Anterior</button>
             <span>Pág {{ metadata.page }} de {{ totalPages }}</span>
             <button @click="nextPage" :disabled="metadata.page >= totalPages" class="px-4 py-2 border rounded bg-white disabled:opacity-50">Próximo</button>
          </div>
        </div>
      </div>

      <div v-else class="bg-white rounded-lg shadow p-8 animate-fade-in">
        <button @click="backToList" class="mb-6 flex items-center text-gray-600 hover:text-blue-600">
          ← Voltar para a lista
        </button>

        <div v-if="selectedOperadora">
          <div class="border-b pb-4 mb-6">
            <h2 class="text-2xl font-bold text-gray-800">{{ selectedOperadora.info.razao_social }}</h2>
            <div class="flex gap-4 mt-2 text-gray-600">
              <span>CNPJ: {{ selectedOperadora.info.cnpj }}</span>
              <span>•</span>
              <span>Registro ANS: {{ selectedOperadora.info.registro_ans }}</span>
            </div>
          </div>

          <h3 class="text-lg font-bold mb-4 text-gray-700">Histórico de Despesas Trimestrais</h3>
          
          <table class="min-w-full border rounded-lg overflow-hidden">
            <thead class="bg-gray-100">
              <tr>
                <th class="px-4 py-3 text-left font-medium">Ano</th>
                <th class="px-4 py-3 text-left font-medium">Trimestre</th>
                <th class="px-4 py-3 text-right font-medium">Valor Despesa</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(hist, index) in selectedOperadora.historico" :key="index" class="border-t hover:bg-gray-50">
                <td class="px-4 py-3">{{ hist.ano }}</td>
                <td class="px-4 py-3">{{ hist.trimestre }}º Trimestre</td>
                <td class="px-4 py-3 text-right font-mono text-blue-700 font-bold">
                  {{ formatMoney(hist.valor_despesa) }}
                </td>
              </tr>
              <tr v-if="selectedOperadora.historico.length === 0">
                <td colspan="3" class="p-4 text-center text-gray-500">Nenhum registro de despesa encontrado.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>
  </div>
</template>