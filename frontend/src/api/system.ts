export interface SettingItem {
 setting_key: string
 setting_group: string
 value: unknown
 description: string | null
}

export interface HealthResponse {
 status: string
 db: string
 redis: string
 version?: string
}

export const systemApi = {
 settings: () => get<SettingItem[]>('/system/settings'),
 updateSetting: (key: string, value: unknown) => patch<SettingItem>(`/system/settings/${key}`, { value }),
 health: () => get<HealthResponse>('/system/health'),
 jobs: () => get<unknown[]>('/system/jobs'),
}