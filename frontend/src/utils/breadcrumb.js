/** 从路由 meta 解析完整面包屑链（含首页与当前页） */
export function resolveBreadcrumbs(route) {
  const chain = [{ title: '首页', path: '/' }]

  const mids = route.meta?.breadcrumbs
    ?? (route.meta?.parent ? [route.meta.parent] : [])

  chain.push(...mids.filter((item) => item?.title))

  const current = route.meta?.title
  if (current) {
    chain.push({ title: current })
  }

  return chain
}
