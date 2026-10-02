<script setup lang="ts">
import { computed } from "vue";

import Badge from "@/components/ui/Badge.vue";

// Centralized status -> badge-variant map for membership / notification / import / tier.
const VARIANT: Record<string, "default" | "success" | "warning" | "info" | "destructive" | "muted"> = {
  active: "success",
  sent: "success",
  ok: "success",
  pro: "warning",
  frozen: "info",
  pending: "muted",
  expired: "muted",
  basic: "muted",
  cancelled: "destructive",
  failed: "destructive",
  error: "destructive",
  duplicate_in_file: "warning",
  duplicate_existing: "warning",
};

const props = defineProps<{ status: string; label?: string }>();
const variant = computed(() => VARIANT[props.status] ?? "muted");
const text = computed(() => props.label ?? props.status.replace(/_/g, " "));
</script>

<template>
  <Badge :variant="variant" class="capitalize">{{ text }}</Badge>
</template>
