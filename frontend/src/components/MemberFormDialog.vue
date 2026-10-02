<script setup lang="ts">
import { reactive, ref, watch } from "vue";

import BaseModal from "@/components/BaseModal.vue";
import { useCheckPhone, useSaveMember } from "@/composables/useMembers";
import type { Member } from "@/lib/types";

const props = defineProps<{ member?: Member | null }>();
const emit = defineEmits<{ close: []; saved: [Member] }>();

const form = reactive({
  full_name: props.member?.full_name ?? "",
  phone: props.member?.phone ?? "",
  email: props.member?.email ?? "",
  gender: props.member?.gender ?? "unspecified",
  date_of_birth: props.member?.date_of_birth ?? "",
  address: props.member?.address ?? "",
  notes: props.member?.notes ?? "",
});

const phoneWarning = ref<string>("");
const checkPhone = useCheckPhone();
const save = useSaveMember();
const error = ref("");

let phoneTimer: ReturnType<typeof setTimeout> | undefined;
watch(
  () => form.phone,
  (val) => {
    phoneWarning.value = "";
    clearTimeout(phoneTimer);
    if (!val || val.replace(/\D/g, "").length < 10) return;
    phoneTimer = setTimeout(async () => {
      try {
        const res = await checkPhone.mutateAsync({ phone: val, exclude: props.member?.id });
        if (res.exists) {
          phoneWarning.value = `Already a member: ${res.member?.full_name}`;
        }
      } catch {
        /* invalid phone — surfaced on submit */
      }
    }, 350);
  },
);

async function submit() {
  error.value = "";
  try {
    const payload: Partial<Member> & { id?: number } = {
      id: props.member?.id,
      full_name: form.full_name,
      phone: form.phone,
      email: form.email,
      gender: form.gender as Member["gender"],
      date_of_birth: form.date_of_birth || null,
      address: form.address,
      notes: form.notes,
    };
    const saved = await save.mutateAsync(payload);
    emit("saved", saved);
  } catch (e: any) {
    error.value =
      e?.response?.data?.details?.phone?.[0] ??
      e?.response?.data?.error ??
      (e instanceof Error ? e.message : "Save failed");
  }
}

const input =
  "w-full rounded border border-input px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring/40";
</script>

<template>
  <BaseModal :title="member ? 'Edit member' : 'Add member'" @close="emit('close')">
    <form class="space-y-3" @submit.prevent="submit">
      <div>
        <label class="text-sm text-muted-foreground">Full name</label>
        <input v-model="form.full_name" required :class="input" />
      </div>
      <div>
        <label class="text-sm text-muted-foreground">Phone</label>
        <input v-model="form.phone" required placeholder="+91 98765 43210" :class="input" />
        <p v-if="phoneWarning" class="mt-1 text-xs text-amber-600">⚠ {{ phoneWarning }}</p>
      </div>
      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="text-sm text-muted-foreground">Gender</label>
          <select v-model="form.gender" :class="input">
            <option value="unspecified">Unspecified</option>
            <option value="male">Male</option>
            <option value="female">Female</option>
            <option value="other">Other</option>
          </select>
        </div>
        <div>
          <label class="text-sm text-muted-foreground">Date of birth</label>
          <input v-model="form.date_of_birth" type="date" :class="input" />
        </div>
      </div>
      <div>
        <label class="text-sm text-muted-foreground">Email</label>
        <input v-model="form.email" type="email" :class="input" />
      </div>
      <div>
        <label class="text-sm text-muted-foreground">Address</label>
        <input v-model="form.address" :class="input" />
      </div>
      <div>
        <label class="text-sm text-muted-foreground">Notes</label>
        <textarea v-model="form.notes" rows="2" :class="input" />
      </div>

      <p v-if="error" class="text-sm text-red-600">{{ error }}</p>

      <div class="flex justify-end gap-2 pt-2">
        <button type="button" class="rounded px-3 py-2 text-sm text-muted-foreground hover:bg-muted" @click="emit('close')">
          Cancel
        </button>
        <button
          type="submit"
          :disabled="save.isPending.value"
          class="rounded bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-60"
        >
          {{ save.isPending.value ? "Saving…" : "Save" }}
        </button>
      </div>
    </form>
  </BaseModal>
</template>
