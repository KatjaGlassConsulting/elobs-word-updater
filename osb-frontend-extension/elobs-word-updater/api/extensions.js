import repository from '../../../api/repositoryExtensions'

export default {
  /**
   * Generate a populated Word document.
   *
   * @param {File}     template  - The .docx template file
   * @param {string}   studyUid  - OpenStudyBuilder study UID
   * @param {string}   [version] - Study version number; omit for latest
   * @param {string[]} [tags]    - SB_* tags to update; omit for all
   * @returns {Promise<Blob>}    - The populated .docx as a Blob
   */
  async generate(template, studyUid, version = null, tags = null) {
    const form = new FormData()
    form.append('template', template)
    form.append('study_uid', studyUid)
    if (version) form.append('version', version)
    if (tags && tags.length > 0) tags.forEach((tag) => form.append('tags', tag))

    const response = await repository.post('/elobs-word-updater-ext/generate', form, {
      responseType: 'blob',
    })
    return response.data
  },
}
