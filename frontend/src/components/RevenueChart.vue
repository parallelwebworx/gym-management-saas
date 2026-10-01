<script setup lang="ts">
import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { computed } from "vue";
import { Bar } from "vue-chartjs";

import type { TrendPoint } from "@/composables/useReports";

ChartJS.register(
  CategoryScale, LinearScale, BarElement, LineElement, PointElement, Tooltip, Legend,
);

const props = defineProps<{ points: TrendPoint[] }>();

// Mixed bar+line datasets: typed as any since chart.js's Bar typing expects a
// single dataset type.
const chartData = computed<any>(() => ({
  labels: props.points.map((p) => p.date.slice(5)), // MM-DD
  datasets: [
    {
      type: "bar" as const,
      label: "Revenue (₹)",
      data: props.points.map((p) => p.revenue_paise / 100),
      backgroundColor: "#0f172a",
      borderRadius: 3,
      order: 2,
    },
    {
      type: "line" as const,
      label: "Cumulative (₹)",
      data: props.points.map((p) => p.cumulative_paise / 100),
      borderColor: "#0ea5e9",
      backgroundColor: "#0ea5e9",
      tension: 0.3,
      pointRadius: 0,
      order: 1,
    },
  ],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index" as const, intersect: false },
  plugins: { legend: { position: "bottom" as const } },
  scales: { y: { beginAtZero: true } },
};
</script>

<template>
  <div class="h-72">
    <Bar :data="chartData" :options="options" />
  </div>
</template>
