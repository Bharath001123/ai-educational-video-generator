import type { VideoFormData } from '../types/video'

const API_BASE_URL = 'http://127.0.0.1:8000'

export interface ScriptScene {
  scene_number: number
  duration_seconds: number
  visual_prompt: string
  voiceover: string
  image_url?: string
  audio_url?: string
  subtitle_url?: string
  visual_source?: 'real' | 'ai'
  search_query?: string
}

export interface ScriptMetadata {
  topic: string
  audience: string
  duration: string
  language: string
  provider: string
  section_count?: number
  scene_count?: number
  video_rendered?: boolean
  presenter_type?: string
}

export interface GeneratedScript {
  title: string
  duration: string
  scenes: ScriptScene[]
  introduction: string
  sections: { title: string; content: string }[]
  conclusion: string
  script: string
  metadata: ScriptMetadata
  video_url?: string
  subtitle_url?: string
  srt_url?: string
}

export interface GenerateVideoResponse {
  message: string
  topic: string
  audience: string
  duration: string
  language: string
  script: GeneratedScript
  video_url?: string
  subtitle_url?: string
}

interface ApiErrorBody {
  detail?: string | { msg: string }[]
}

export async function generateVideo(
  formData: VideoFormData,
): Promise<GenerateVideoResponse> {
  const response = await fetch(`${API_BASE_URL}/api/generate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      topic: formData.topic.trim(),
      audience: formData.audienceLevel,
      duration: formData.duration,
      language: formData.language,
      presenter_type: formData.presenterType,
    }),
  })

  if (!response.ok) {
    let errorMessage = 'Failed to generate video. Please try again.'

    try {
      const errorData: ApiErrorBody = await response.json()
      if (typeof errorData.detail === 'string') {
        errorMessage = errorData.detail
      }
    } catch {
      // Use default error message when response body is not JSON.
    }

    throw new Error(errorMessage)
  }

  return response.json()
}
