export type AudienceLevel = 'school' | 'ug' | 'pg'

export type VideoDuration = '1' | '3' | '5' | '10'

export type Language = 'english' | 'hindi' | 'telugu'

export type PresenterType = 'female' | 'male' | 'robot' | 'none'

export interface VideoFormData {
  topic: string
  audienceLevel: AudienceLevel
  duration: VideoDuration
  language: Language
  presenterType: PresenterType
}

export const PRESENTER_OPTIONS: { value: PresenterType; label: string }[] = [
  { value: 'female', label: 'Female Teacher' },
  { value: 'male', label: 'Male Teacher' },
  { value: 'robot', label: 'Robot Teacher' },
  { value: 'none', label: 'Slides Only' },
]

export const AUDIENCE_OPTIONS: { value: AudienceLevel; label: string }[] = [
  { value: 'school', label: 'School' },
  { value: 'ug', label: 'Undergraduate (UG)' },
  { value: 'pg', label: 'Postgraduate (PG)' },
]

export const DURATION_OPTIONS: { value: VideoDuration; label: string }[] = [
  { value: '1', label: '1 minute' },
  { value: '3', label: '3 minutes' },
  { value: '5', label: '5 minutes' },
  { value: '10', label: '10 minutes' },
]

export const LANGUAGE_OPTIONS: { value: Language; label: string }[] = [
  { value: 'english', label: 'English' },
  { value: 'hindi', label: 'Hindi' },
  { value: 'telugu', label: 'Telugu' },
]
