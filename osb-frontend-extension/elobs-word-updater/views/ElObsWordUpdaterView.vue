<template>
  <div class="px-4">
    <div class="page-title d-flex align-center">
      {{ $t('ElObsWordUpdater.title') }}
    </div>

    <v-alert
      color="nnLightBlue200"
      icon="mdi-information-outline"
      class="text-nnTrueBlue mx-0 my-0 mb-6"
    >
      {{ $t('ElObsWordUpdater.description') }}
    </v-alert>

    <v-card elevation="0" rounded="lg">
      <v-card-text>
        <v-form ref="form" @submit.prevent="generate">
          <!-- Study selector: by ID and/or acronym (resolves to study UID) -->
          <div class="d-flex align-center mb-4">
            <v-autocomplete
              ref="idFieldRef"
              v-model="studyById"
              :items="studiesWithId"
              :label="$t('ElObsWordUpdater.study_id_label')"
              item-title="id"
              return-object
              variant="outlined"
              rounded="lg"
              color="nnBaseBlue"
              density="compact"
              autocomplete="off"
              clearable
              hide-details="auto"
              :loading="studiesLoading"
              :rules="[rules.studySelected]"
              @update:model-value="autoPopulateAcronym"
            />
            <span class="mx-4">{{ $t('ElObsWordUpdater.study_and_or') }}</span>
            <v-autocomplete
              ref="acronymFieldRef"
              v-model="studyByAcronym"
              :items="studiesWithAcronym"
              :label="$t('ElObsWordUpdater.study_acronym_label')"
              item-title="acronym"
              return-object
              variant="outlined"
              rounded="lg"
              color="nnBaseBlue"
              density="compact"
              autocomplete="off"
              clearable
              hide-details="auto"
              :loading="studiesLoading"
              :rules="[rules.studySelected]"
              @update:model-value="autoPopulateId"
            />
          </div>

          <!-- Version picker -->
          <v-select
            v-model="version"
            :items="versionItems"
            :label="$t('ElObsWordUpdater.version_label')"
            item-title="title"
            item-value="value"
            variant="outlined"
            rounded="lg"
            color="nnBaseBlue"
            density="compact"
            class="mb-4"
            :loading="versionsLoading"
            :disabled="!selectedStudy"
          />

          <!-- Template file upload -->
          <v-file-input
            v-model="templateFile"
            :label="$t('ElObsWordUpdater.template_label')"
            :hint="$t('ElObsWordUpdater.template_hint')"
            accept=".docx"
            variant="outlined"
            rounded="lg"
            color="nnBaseBlue"
            density="compact"
            class="mb-4"
            persistent-hint
            :rules="[rules.required]"
          />

          <!-- Tag selection -->
          <div class="mb-4">
            <div class="text-subtitle-2 mb-2">{{ $t('ElObsWordUpdater.tags_label') }}</div>
            <v-checkbox
              v-model="allTags"
              :label="$t('ElObsWordUpdater.tags_all')"
              color="nnBaseBlue"
              density="compact"
              hide-details
              class="mb-1"
            />
            <v-row v-if="!allTags" dense class="mt-1">
              <v-col v-for="tag in availableTags" :key="tag" cols="12" sm="6" md="4">
                <v-checkbox
                  v-model="selectedTags"
                  :label="tag"
                  :value="tag"
                  color="nnBaseBlue"
                  density="compact"
                  hide-details
                />
              </v-col>
            </v-row>
          </div>

          <!-- Generate button -->
          <v-btn
            type="submit"
            color="primary"
            variant="flat"
            rounded="lg"
            prepend-icon="mdi-file-word-outline"
            :loading="isLoading"
          >
            {{ $t('ElObsWordUpdater.generate_button') }}
          </v-btn>
        </v-form>
      </v-card-text>
    </v-card>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { notificationHub } from '@/plugins/notificationHub'
import repository from '@/api/repository'
import extensionsApi from '../api/extensions'

const { t } = useI18n()

const form = ref(null)
const idFieldRef = ref(null)
const acronymFieldRef = ref(null)
const studies = ref([])
const studiesLoading = ref(false)
const studyById = ref(null)
const studyByAcronym = ref(null)
const version = ref(null) // null = "Latest"
const studyVersions = ref([])
const versionsLoading = ref(false)
const templateFile = ref(null)
const allTags = ref(true)
const selectedTags = ref([])
const isLoading = ref(false)

const availableTags = [
  'SB_ProtocolTitle',
  'SB_ProtocolTitleShort',
  'SB_Acronym',
  'SB_StudyID',
  'SB_StudyPhase',
  'SB_EudraCTNumber',
  'SB_INDNumber',
  'SB_UniversalTrialNumber',
  'SB_InclusionCriteria',
  'SB_ExclusionCriteria',
  'SB_ObjectivesEndpoints',
  'SB_Flowchart',
  'SB_SoA',
  'SB_StudydesignGraphic',
]

// The selected study object (carries uid, id, acronym); either field resolves to it.
const selectedStudy = computed(() => studyById.value || studyByAcronym.value)

const studiesWithId = computed(() =>
  studies.value
    .filter((s) => s.id)
    .sort((a, b) => a.id.localeCompare(b.id)),
)
const studiesWithAcronym = computed(() =>
  studies.value
    .filter((s) => s.acronym)
    .sort((a, b) => a.acronym.localeCompare(b.acronym)),
)

// "Latest" (value null) plus every locked version of the selected study.
const versionItems = computed(() => [
  { title: t('ElObsWordUpdater.version_latest'), value: null },
  ...studyVersions.value.map((v) => ({ title: v, value: v })),
])

// Reload the available versions whenever the selected study changes, and
// reset the picker back to "Latest".
watch(selectedStudy, async (study) => {
  version.value = null
  studyVersions.value = []
  if (!study) return
  versionsLoading.value = true
  try {
    const { data } = await repository.get(`/studies/${study.uid}/snapshot-history`, {
      params: { page_size: 0 },
    })
    const items = data.items ?? data ?? []
    const seen = new Set()
    studyVersions.value = items
      .map((it) => it?.current_metadata?.version_metadata?.version_number)
      .filter((v) => v != null && v !== '')
      .filter((v) => (seen.has(v) ? false : seen.add(v)))
  } catch {
    // Best-effort; the user can still generate with "Latest".
  } finally {
    versionsLoading.value = false
  }
})

const rules = {
  required: (v) => !!v || 'Required',
  studySelected: () => !!selectedStudy.value || t('ElObsWordUpdater.study_required'),
}

// The "at least one selected" rule lives on both fields, but Vuetify only re-runs a
// field's rules when its own model changes. Re-validate both so the sibling's error
// clears/appears when the other field changes (e.g. picking an ID with no acronym).
function revalidateStudyFields() {
  nextTick(() => {
    idFieldRef.value?.validate()
    acronymFieldRef.value?.validate()
  })
}

// Keep the two fields in sync: selecting one populates the other from the same study.
function autoPopulateAcronym(study) {
  studyByAcronym.value = study && study.acronym ? study : null
  revalidateStudyFields()
}
function autoPopulateId(study) {
  studyById.value = study && study.id ? study : null
  revalidateStudyFields()
}

onMounted(async () => {
  studiesLoading.value = true
  try {
    const { data } = await repository.get('/studies/list')
    studies.value = data.items ?? data
  } catch {
    // Studies list is best-effort; the form will surface a validation error if empty.
  } finally {
    studiesLoading.value = false
  }
})

async function generate() {
  const { valid } = await form.value.validate()
  if (!valid) return

  isLoading.value = true
  try {
    const tags = allTags.value ? null : selectedTags.value
    const blob = await extensionsApi.generate(
      templateFile.value,
      selectedStudy.value.uid,
      version.value || null,
      tags,
    )

    // Trigger browser download
    const datestamp = new Date().toISOString().slice(0, 10).replace(/-/g, '')
    const baseName = templateFile.value.name.replace(/\.docx$/i, '')
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${baseName}_${datestamp}.docx`
    a.click()
    URL.revokeObjectURL(url)

    notificationHub.add({ msg: t('ElObsWordUpdater.success_message'), type: 'success' })
  } catch {
    notificationHub.add({ msg: t('ElObsWordUpdater.error_message'), type: 'error' })
  } finally {
    isLoading.value = false
  }
}
</script>
