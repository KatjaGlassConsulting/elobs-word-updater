import roles from '@/constants/roles'

const elObsWordUpdaterRoute = {
  path: 'elobs-word-updater',
  name: 'ElObsWordUpdater',
  component: () => import('../views/ElObsWordUpdaterView.vue'),
  meta: {
    resetBreadcrumbs: true,
    authRequired: true,
    section: 'Studies',
    requiredPermission: roles.STUDY_READ,
  },
}

export function addExtensionRoutes(routes) {
  const studiesRoute = routes.find((route) => route.path === '/studies')
  if (studiesRoute?.children) {
    studiesRoute.children.push(elObsWordUpdaterRoute)
  }
}
