<script setup lang="ts">
import { computed, type Component } from "vue";

import Card from "@/components/ui/Card.vue";

const props = defineProps<{
  label: string;
  value: string | number;
  delta?: string;
  deltaPositive?: boolean;
  sub?: string;
  icon?: Component;
  tone?: "blue" | "green" | "amber" | "violet" | "sky";
}>();

const chip = computed(() => ({
  blue: "bg-primary text-primary-foreground",
  green: "bg-success text-success-foreground",
  amber: "bg-accent text-accent-foreground",
  violet: "bg-violet-500 text-white",
  sky: "bg-sky-500 text-white",
}[props.tone ?? "blue"]));
</script>

<template>
  <Card hover class="p-5">
    <div class="flex items-start justify-between">
      <div class="min-w-0">
        <div class="text-sm text-muted-foreground">{{ label }}</div>
        <div class="mt-1 text-2xl font-bold tracking-tight">{{ value }}</div>
        <div v-if="delta" class="mt-1 text-xs font-medium" :class="deltaPositive ? 'text-success' : 'text-destructive'">
          {{ delta }}
        </div>
        <div v-else-if="sub" class="mt-1 text-xs text-muted-foreground">{{ sub }}</div>
      </div>
      <div v-if="icon" class="flex h-11 w-11 shrink-0 items-center justify-center rounded-full" :class="chip">
        <component :is="icon" class="h-5 w-5" />
      </div>
    </div>
  </Card>
</template>
