<script setup lang="ts">
import { computed } from "vue";

import { initials } from "@/lib/utils";

const props = defineProps<{ name: string; size?: "sm" | "md" | "lg" }>();
const sizeClass = computed(() => ({
  sm: "h-8 w-8 text-xs",
  md: "h-10 w-10 text-sm",
  lg: "h-12 w-12 text-base",
}[props.size ?? "md"]));
</script>

<template>
  <div
    class="flex shrink-0 items-center justify-center rounded-full bg-primary/10 font-semibold text-primary"
    :class="sizeClass"
  >
    {{ initials(name) }}
  </div>
</template>
