import { useState, type FormEvent } from 'react'
import { motion } from 'framer-motion'
import { generateVideo, type GeneratedScript } from '../api/video'
import ScriptResultCard from './ScriptResultCard'
import LoadingScreen from './LoadingScreen'
import { useNavigate } from 'react-router-dom';
import {
  AUDIENCE_OPTIONS,
  DURATION_OPTIONS,
  LANGUAGE_OPTIONS,
  PRESENTER_OPTIONS,
  type VideoFormData,
} from '../types/video'

const initialFormData: VideoFormData = {
  topic: '',
  audienceLevel: 'school',
  duration: '3',
  language: 'english',
  presenterType: 'none',
}

function VideoGeneratorForm() {
  const navigate = useNavigate();
  const [formData, setFormData] = useState<VideoFormData>(initialFormData)
  const [isLoading, setIsLoading] = useState(false)
  const [isApiComplete, setIsApiComplete] = useState(false)
  const [pendingScript, setPendingScript] = useState<GeneratedScript | null>(null)
  const [statusMessage, setStatusMessage] = useState<string | null>(null)
  const [isError, setIsError] = useState(false)
  const [generatedScript, setGeneratedScript] = useState<GeneratedScript | null>(null)

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setStatusMessage(null)
    setIsError(false)
    setGeneratedScript(null)
    setPendingScript(null)
    setIsApiComplete(false)

    if (!formData.topic.trim()) {
      setStatusMessage('Please enter a topic before generating.')
      setIsError(true)
      return
    }

    setIsLoading(true)

    try {
      const response = await generateVideo(formData)
      setStatusMessage(response.message)
      setPendingScript(response.script)
      setIsError(false)
      setIsApiComplete(true)
      // Navigate to result page with script data
      // We'll use navigate after loading completes to ensure video is ready
    } catch (error) {
      const message =
        error instanceof Error
          ? error.message
          : 'Something went wrong. Please try again.'
      setStatusMessage(message)
      setIsError(true)
      setIsLoading(false)
    }
  }

  const handleLoadingComplete = () => {
    // Store generated script
    setGeneratedScript(pendingScript);
    setIsLoading(false);
    setIsApiComplete(false);
    // Navigate to Result page with script data
    navigate('/result', { state: { script: pendingScript } });
    // Keep optional scroll for smooth UX (may be redundant after navigation)
    setTimeout(() => {
      const resultCard = document.querySelector('.script-result-card');
      if (resultCard) {
        resultCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    }, 150);
  }

  const updateField = <K extends keyof VideoFormData>(
    field: K,
    value: VideoFormData[K],
  ) => {
    setFormData((prev) => ({ ...prev, [field]: value }))
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {!isLoading ? (
        <>
          <div>
            <label htmlFor="topic" className="form-label">
              Topic
            </label>
            <input
              id="topic"
              type="text"
              value={formData.topic}
              onChange={(e) => updateField('topic', e.target.value)}
              placeholder="Photosynthesis"
              className="form-input"
              disabled={isLoading}
            />
            <p className="form-hint">
              Enter the subject or concept you want the video to explain.
            </p>
          </div>

          <div className="grid sm:grid-cols-3 gap-6">
            <div>
              <label htmlFor="audienceLevel" className="form-label">
                Audience Level
              </label>
              <div className="relative">
                <select
                  id="audienceLevel"
                  value={formData.audienceLevel}
                  onChange={(e) =>
                    updateField('audienceLevel', e.target.value as VideoFormData['audienceLevel'])
                  }
                  className="form-select"
                  disabled={isLoading}
                >
                  {AUDIENCE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronIcon className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              </div>
            </div>

            <div>
              <label htmlFor="language" className="form-label">
                Language
              </label>
              <div className="relative">
                <select
                  id="language"
                  value={formData.language}
                  onChange={(e) =>
                    updateField('language', e.target.value as VideoFormData['language'])
                  }
                  className="form-select"
                  disabled={isLoading}
                >
                  {LANGUAGE_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronIcon className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              </div>
            </div>

            <div>
              <label htmlFor="presenterType" className="form-label">
                AI Teacher Presenter
              </label>
              <div className="relative">
                <select
                  id="presenterType"
                  value={formData.presenterType}
                  onChange={(e) =>
                    updateField('presenterType', e.target.value as VideoFormData['presenterType'])
                  }
                  className="form-select"
                  disabled={isLoading}
                >
                  {PRESENTER_OPTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                <ChevronIcon className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-500" />
              </div>
            </div>
          </div>

          <div>
            <span className="form-label">Video Duration</span>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-2">
              {DURATION_OPTIONS.map((option) => {
                const isSelected = formData.duration === option.value
                return (
                  <button
                    key={option.value}
                    type="button"
                    onClick={() => updateField('duration', option.value)}
                    disabled={isLoading}
                    className={`duration-option ${isSelected ? 'duration-option-active' : ''}`}
                  >
                    <span className="text-sm font-medium">{option.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          <button type="submit" className="generate-button" disabled={isLoading}>
            <SparklesIcon className={`w-5 h-5 ${isLoading ? 'animate-pulse' : ''}`} />
            {isLoading ? 'Generating...' : 'Generate Video'}
          </button>

          {statusMessage && (
            <div
              role="alert"
              className={`rounded-xl border px-4 py-3 text-sm ${
                isError
                  ? 'border-red-500/30 bg-red-500/10 text-red-300'
                  : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
              }`}
            >
              {statusMessage}
            </div>
          )}
        </>
      ) : (
        <LoadingScreen
          duration={formData.duration}
          isApiComplete={isApiComplete}
          onComplete={handleLoadingComplete}
          topic={formData.topic}
        />
      )}

      {generatedScript && (
        <motion.div
          initial={{ opacity: 0, y: 40 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8, ease: 'easeOut' }}
        >
          <ScriptResultCard script={generatedScript} />
        </motion.div>
      )}
    </form>
  )
}

function ChevronIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  )
}

function SparklesIcon({ className }: { className?: string }) {
  return (
    <svg
      className={className}
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M5 3v4M3 5h4M6 17v4m-2-2h4m5-16l2.286 6.857L21 12l-5.714 2.143L13 21l-2.286-6.857L5 12l5.714-2.143L13 3z"
      />
    </svg>
  )
}

export default VideoGeneratorForm
