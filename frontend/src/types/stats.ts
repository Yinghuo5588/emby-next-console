export interface StatsOverview {
 total_play_count: number
 total_play_duration_sec: number
 unique_users: number
 unique_media: number
}

export interface TopUserItem {
 user_id: string
 username: string
 play_count: number
 play_duration_sec: number
}

export interface TopMediaItem {
 media_id: string
 media_name: string
 media_type: string
 play_count: number
}

export interface StatsTrendPoint {
 date: string
 play_count: number
 active_users: number
 total_duration_sec: number
}