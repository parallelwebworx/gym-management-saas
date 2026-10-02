<script setup lang="ts">
import { ref } from "vue";

import AddOnFormDialog from "@/components/AddOnFormDialog.vue";
import PlanFormDialog from "@/components/PlanFormDialog.vue";
import {
  useAddOns,
  useDeleteAddOn,
  useDeletePlan,
  usePlans,
} from "@/composables/useCatalogue";
import { formatPaise } from "@/lib/money";
import type { AddOn, Plan } from "@/lib/types";

const { data: plans, isLoading: plansLoading } = usePlans();
const { data: addons, isLoading: addonsLoading } = useAddOns();
const deletePlan = useDeletePlan();
const deleteAddOn = useDeleteAddOn();

const showPlan = ref(false);
const editingPlan = ref<Plan | null>(null);
const showAddOn = ref(false);
const editingAddOn = ref<AddOn | null>(null);

function addPlan() { editingPlan.value = null; showPlan.value = true; }
function editPlan(p: Plan) { editingPlan.value = p; showPlan.value = true; }
function addAddOn() { editingAddOn.value = null; showAddOn.value = true; }
function editAddOn(a: AddOn) { editingAddOn.value = a; showAddOn.value = true; }

async function removePlan(p: Plan) {
  if (confirm(`Delete plan "${p.name}"?`)) await deletePlan.mutateAsync(p.id);
}
async function removeAddOn(a: AddOn) {
  if (confirm(`Delete add-on "${a.name}"?`)) await deleteAddOn.mutateAsync(a.id);
}

const planTypeLabel: Record<string, string> = {
  general: "General", cardio: "Cardio", gym_cardio: "Gym + Cardio", custom: "Custom",
};
</script>

<template>
  <div class="space-y-8">
    <h1 class="text-xl font-semibold text-slate-800">Catalogue</h1>

    <!-- Plans -->
    <section class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="font-medium text-slate-700">Plans</h2>
        <button class="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-800" @click="addPlan">+ Add plan</button>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-left text-slate-500">
            <tr>
              <th class="px-4 py-2">Name</th><th class="px-4 py-2">Type</th>
              <th class="px-4 py-2">Duration</th><th class="px-4 py-2">Price</th>
              <th class="px-4 py-2">Active</th><th class="px-4 py-2 w-24"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="plansLoading"><td colspan="6" class="px-4 py-6 text-center text-slate-400">Loading…</td></tr>
            <tr v-else-if="plans && plans.results.length === 0"><td colspan="6" class="px-4 py-6 text-center text-slate-400">No plans yet.</td></tr>
            <tr v-for="p in plans?.results" :key="p.id" class="border-t">
              <td class="px-4 py-2">{{ p.name }}</td>
              <td class="px-4 py-2">{{ planTypeLabel[p.plan_type] }}</td>
              <td class="px-4 py-2">{{ p.duration_days }} days</td>
              <td class="px-4 py-2">{{ formatPaise(p.price_paise) }}</td>
              <td class="px-4 py-2">{{ p.is_active ? "Yes" : "No" }}</td>
              <td class="px-4 py-2 text-right">
                <button class="text-slate-500 hover:text-slate-800 mr-3" @click="editPlan(p)">Edit</button>
                <button class="text-red-500 hover:text-red-700" @click="removePlan(p)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- Add-ons -->
    <section class="space-y-3">
      <div class="flex items-center justify-between">
        <h2 class="font-medium text-slate-700">Add-ons</h2>
        <button class="rounded bg-slate-900 px-3 py-1.5 text-sm text-white hover:bg-slate-800" @click="addAddOn">+ Add add-on</button>
      </div>
      <div class="rounded-xl border border-slate-200 bg-white overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-slate-50 text-left text-slate-500">
            <tr>
              <th class="px-4 py-2">Name</th><th class="px-4 py-2">Type</th>
              <th class="px-4 py-2">Price</th><th class="px-4 py-2">Auto-apply</th>
              <th class="px-4 py-2">Active</th><th class="px-4 py-2 w-24"></th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="addonsLoading"><td colspan="6" class="px-4 py-6 text-center text-slate-400">Loading…</td></tr>
            <tr v-else-if="addons && addons.results.length === 0"><td colspan="6" class="px-4 py-6 text-center text-slate-400">No add-ons yet.</td></tr>
            <tr v-for="a in addons?.results" :key="a.id" class="border-t">
              <td class="px-4 py-2">{{ a.name }}</td>
              <td class="px-4 py-2 capitalize">{{ a.addon_type.replace("_", "-") }}</td>
              <td class="px-4 py-2">{{ formatPaise(a.price_paise) }}</td>
              <td class="px-4 py-2">{{ a.auto_apply_on_first_enrollment ? "Yes" : "No" }}</td>
              <td class="px-4 py-2">{{ a.is_active ? "Yes" : "No" }}</td>
              <td class="px-4 py-2 text-right">
                <button class="text-slate-500 hover:text-slate-800 mr-3" @click="editAddOn(a)">Edit</button>
                <button class="text-red-500 hover:text-red-700" @click="removeAddOn(a)">Delete</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <PlanFormDialog v-if="showPlan" :plan="editingPlan" @close="showPlan = false" @saved="showPlan = false" />
    <AddOnFormDialog v-if="showAddOn" :addon="editingAddOn" @close="showAddOn = false" @saved="showAddOn = false" />
  </div>
</template>
