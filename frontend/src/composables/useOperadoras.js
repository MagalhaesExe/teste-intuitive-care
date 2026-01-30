// src/composables/useOperadoras.js
import { ref, computed } from 'vue'
import axios from 'axios'

export function useOperadoras() {
  // Estado
  const operadoras = ref([])
  const metadata = ref({ total: 0, page: 1, limit: 10 })
  const loading = ref(false)
  const error = ref(null)
  const selectedOperadora = ref(null)

  // Computed
  const totalPages = computed(() => Math.ceil(metadata.value.total / metadata.value.limit))

  // Ações
  const fetchOperadoras = async (page = 1, search = '') => {
    loading.value = true
    error.value = null
    try {
      const res = await axios.get('http://127.0.0.1:8000/api/operadoras', {
        params: { page, limit: 10, search }
      })
      operadoras.value = res.data.data
      metadata.value = res.data.metadata
    } catch (err) {
      error.value = "Erro ao buscar dados"
      console.error(err)
    } finally {
      loading.value = false
    }
  }

  const fetchDetalhes = async (cnpj) => {
    loading.value = true
    try {
      const res = await axios.get(`http://127.0.0.1:8000/api/operadoras/${cnpj}/detalhes`)
      selectedOperadora.value = res.data
      return true // Indica sucesso
    } catch (err) {
      alert("Erro ao carregar detalhes")
      return false
    } finally {
      loading.value = false
    }
  }

  return {
    operadoras,
    metadata,
    loading,
    error,
    totalPages,
    selectedOperadora,
    fetchOperadoras,
    fetchDetalhes
  }
}