import apiClient, { type ApiResponse } from './client'

export interface Library {
  id: string
  name: string
  type: string
}

export interface MissingEpisode {
  series_name: string
  seasons: number
  episodes_found: number
}

export interface DuplicateItem {
  name: string
  count: number
  items: Array<{ id: string; path: string; size_mb: number }>
}

export interface TMDBSearchResult {
  tmdb_id: number
  title: string
  overview: string
  poster: string | null
  backdrop: string | null
  release_date: string | null
  vote_average: number
}

export interface TMDBDetail extends TMDBSearchResult {
  genres: string[]
  runtime: number | null
  seasons: Array<{ number: number; name: string; episodes: number }> | null
}

export const mediaApi = {
  async libraries(): Promise<ApiResponse<Library[]>> {
    const res = await apiClient.get('/media/libraries')
    return res.data
  },

  async missingEpisodes(): Promise<ApiResponse<MissingEpisode[]>> {
    const res = await apiClient.get('/media/missing-episodes')
    return res.data
  },

  async duplicates(): Promise<ApiResponse<DuplicateItem[]>> {
    const res = await apiClient.get('/media/duplicates')
    return res.data
  },

  async tmdbSearch(query: string, type = 'movie', page = 1): Promise<ApiResponse<{ results: TMDBSearchResult[]; page: number; total_pages: number }>> {
    const res = await apiClient.get('/media/tmdb/search', { params: { query, type, page } })
    return res.data
  },

  async tmdbUpcoming(type = 'movie', page = 1): Promise<ApiResponse<{ results: TMDBSearchResult[]; page: number }>> {
    const res = await apiClient.get('/media/tmdb/upcoming', { params: { type, page } })
    return res.data
  },

  async tmdbDetail(tmdbId: number, type = 'movie'): Promise<ApiResponse<TMDBDetail>> {
    const res = await apiClient.get(`/media/tmdb/detail/${tmdbId}`, { params: { type } })
    return res.data
  },
}