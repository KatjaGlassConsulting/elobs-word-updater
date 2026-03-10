import { i18n } from '@/plugins/i18n'

export default {
  menuItems: {
    Studies: {
      items: [
        {
          title: i18n.t('ElObsWordUpdater.menu_label'),
          url: { name: 'ElObsWordUpdater' },
          icon: 'mdi-file-word-outline',
        },
      ],
    },
  },
}
