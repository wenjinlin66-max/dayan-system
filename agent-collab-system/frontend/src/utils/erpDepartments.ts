export const ERP_DEPARTMENT_OPTIONS = [
  { value: 'ceo', label: 'CEO / 全局查看' },
  { value: 'production', label: '生产部' },
  { value: 'supply_chain', label: '供应链部' },
  { value: 'procurement', label: '采购部' },
  { value: 'warehouse', label: '仓储部' },
  { value: 'sales', label: '销售部' },
  { value: 'finance', label: '财务部' },
  { value: 'quality', label: '质检部' },
  { value: 'maintenance', label: '设备维护部' },
  { value: 'hr', label: '人力资源部' },
] as const

export type ErpDepartmentValue = (typeof ERP_DEPARTMENT_OPTIONS)[number]['value']

const ERP_DEPARTMENT_LABELS = new Map<string, string>(ERP_DEPARTMENT_OPTIONS.map((item) => [item.value, item.label]))

export const getDepartmentLabel = (value: string | null | undefined) => ERP_DEPARTMENT_LABELS.get(value ?? '') ?? value ?? '未分配部门'
