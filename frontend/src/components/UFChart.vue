<script setup>
import { Bar } from 'vue-chartjs'
import { Chart as ChartJS, Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale } from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

const props = defineProps(['chartData'])

const chartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      display: false
    },
    title: {
      display: true,
      text: 'Despesas por UF',
      color: '#E5E7EB',
      font: {
        size: 14,
        weight: 'bold'
      }
    },
    tooltip: {
      backgroundColor: '#111827',
      titleColor: '#E5E7EB',
      bodyColor: '#E5E7EB',
      borderColor: '#374151',
      borderWidth: 1,
      callbacks: {
        label(context) {
          return new Intl.NumberFormat('pt-BR', {
            style: 'currency',
            currency: 'BRL'
          }).format(context.raw)
        }
      }
    }
  },
  scales: {
    x: {
      ticks: {
        color: '#9CA3AF'
      },
      grid: {
        color: '#1F2937'
      }
    },
    y: {
      ticks: {
        color: '#9CA3AF',
        callback(value) {
          return new Intl.NumberFormat('pt-BR', {
            notation: 'compact',
            compactDisplay: 'short'
          }).format(value)
        }
      },
      grid: {
        color: '#1F2937'
      }
    }
  }
}
</script>

<template>
  <div class="relative w-full h-64">
    <Bar :data="props.chartData" :options="chartOptions" />
  </div>
</template>