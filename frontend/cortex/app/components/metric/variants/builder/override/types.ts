export type OperationType = 'add' | 'replace' | 'exclude' | 'config'
export type ComponentType = 'measure' | 'dimension' | 'filter' | 'join'

export interface OverrideItem {
  id: string
  operation: OperationType
  componentType?: ComponentType
  data?: any
  excludeNames?: string[]
  configField?: 'table_name' | 'limit' | 'grouped' | 'ordered'
  configValue?: any
}

export const COMPONENT_TYPES: ComponentType[] = ['measure', 'dimension', 'filter', 'join']
export const CONFIG_FIELDS = ['table_name', 'limit', 'grouped', 'ordered'] as const
