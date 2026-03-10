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
          <!-- Study selector -->
          <v-autocomplete
            v-model="selectedStudy"
            :items="studies"
            :label="$t('ElObsWordUpdater.study_label')"
            :placeholder="$t('ElObsWordUpdater.study_placeholder')"
            item-title="uid"
            item-value="uid"
            variant="outlined"
            rounded="lg"
            color="nnBaseBlue"
            density="compact"
            class="mb-4"
            :rules="[rules.required]"
          />

          <!-- Version picker -->
          <v-text-field
            v-model="version"
            :label="$t('ElObsWordUpdater.version_label')"
            :placeholder="$t('ElObsWordUpdater.version_latest')"
            variant="outlined"
            rounded="lg"
            color="nnBaseBlue"
            density="compact"
            class="mb-4"
            clearable
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
import { ref, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { notificationHub } from '@/plugins/notificationHub'
import repository from '@/api/repository'
import extensionsApi from '../api/extensions'

const { t } = useI18n()

const form = ref(null)
const studies = ref([])
const selectedStudy = ref(null)
const version = ref(null)
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

const rules = {
  required: (v) => !!v || 'Required',
}

onMounted(async () => {
  try {
    const { data } = await repository.get('/studies', { params: { page_size: 0 } })
    studies.value = data.items ?? data
  } catch {
    // Studies list is best-effort; user can type the UID manually if needed
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
      selectedStudy.value,
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
