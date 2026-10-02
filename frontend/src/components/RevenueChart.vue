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

/** Read an HSL design token (e.g. "221 83% 53%") and wrap it as a CSS color. */
function token(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v ? `hsl(${v})` : fallback;
}

// Mixed bar+line datasets: typed as any since chart.js's Bar typing expects a
// single dataset type. Colors follow the design tokens so charts match the theme.
const chartData = computed<any>(() => ({
  labels: props.points.map((p) => p.date.slice(5)), // MM-DD
  datasets: [
    {
      type: "bar" as const,
      label: "Revenue (₹)",
      data: props.points.map((p) => p.revenue_paise / 100),
      backgroundColor: token("--primary", "#2563eb"),
      borderRadius: 4,
      maxBarThickness: 22,
      order: 2,
    },
    {
      type: "line" as const,
      label: "Cumulative (₹)",
      data: props.points.map((p) => p.cumulative_paise / 100),
      borderColor: token("--accent", "#f59e0b"),
      backgroundColor: token("--accent", "#f59e0b"),
      tension: 0.35,
      pointRadius: 0,
      borderWidth: 2,
      order: 1,
    },
  ],
}));

const options = {
  responsive: true,
  maintainAspectRatio: false,
  interaction: { mode: "index" as const, intersect: false },
  plugins: { legend: { position: "bottom" as const, labels: { usePointStyle: true, boxWidth: 8 } } },
  scales: {
    y: { beginAtZero: true, grid: { color: "rgba(100,116,139,0.12)" }, border: { display: false } },
    x: { grid: { display: false } },
  },
};
</script>

<template>
  <div class="h-72">
    <Bar :data="chartData" :options="options" />
  </div>
</template>
