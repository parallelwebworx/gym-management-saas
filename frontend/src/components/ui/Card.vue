<script setup lang="ts">
import { computed } from "vue";

import { cn } from "@/lib/utils";

const props = defineProps<{ class?: string; hover?: boolean }>();
const classes = computed(() =>
  cn(
    "rounded-xl border border-border bg-card text-card-foreground shadow-card",
    props.hover && "transition-shadow hover:shadow-card-hover",
    props.class,
  ),
);
</script>

<template>
  <div :class="classes"><slot /></div>
</template>
