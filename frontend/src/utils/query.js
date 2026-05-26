/** 构建列表查询参数，空字符串 / 空数组会自动剔除 */
export function buildListParams(fields, pagination = {}) {
  const params = { ...fields, ...pagination }
  Object.keys(params).forEach((k) => {
    const v = params[k]
    if (v === '' || v === null || v === undefined) {
      delete params[k]
    } else if (Array.isArray(v) && v.length === 0) {
      delete params[k]
    }
  })
  return params
}
