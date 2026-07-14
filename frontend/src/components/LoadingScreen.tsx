import { useState, useEffect, useMemo } from 'react'
import { createPortal } from 'react-dom'
import { motion, AnimatePresence } from 'framer-motion'

interface LoadingScreenProps {
  duration: string // "1" | "3" | "5" | "10"
  isApiComplete: boolean
  onComplete: () => void
  topic: string
}

const STEPS = [
  'Understanding Topic',
  'Researching Content',
  'Writing Script',
  'Creating Storyboard',
  'Generating AI Images',
  'Creating Voiceover',
  'Synchronizing Audio',
  'Creating Subtitles',
  'Rendering Video',
  'Finalizing',
]

const AI_MESSAGES = [
  'Analyzing your topic...',
  'Writing an engaging educational script...',
  'Generating AI-powered visuals...',
  'Creating natural voice narration...',
  'Synchronizing subtitles...',
  'Rendering your final MP4...',
]

// Estimate average duration targets (in seconds)
const DURATION_ESTIMATES: Record<string, number> = {
  '1': 25,
  '3': 45,
  '5': 70,
  '10': 120,
}

export default function LoadingScreen({ duration, isApiComplete, onComplete, topic }: LoadingScreenProps) {
  const targetTime = useMemo(() => DURATION_ESTIMATES[duration] || 45, [duration])
  const [elapsedTime, setElapsedTime] = useState(0)
  const [progress, setProgress] = useState(0)
  const [messageIndex, setMessageIndex] = useState(0)
  const [isFadingOut, setIsFadingOut] = useState(false)

  // Floating particles initial states
  const particles = useMemo(() => {
    return Array.from({ length: 20 }).map((_, i) => ({
      id: i,
      size: Math.random() * 6 + 2,
      xStart: Math.random() * 100,
      yStart: Math.random() * 100,
      duration: Math.random() * 10 + 10,
      delay: Math.random() * 5,
    }))
  }, [])

  // Rotate AI messages
  useEffect(() => {
    const messageInterval = setInterval(() => {
      setMessageIndex((prev) => (prev + 1) % AI_MESSAGES.length)
    }, 2500)
    return () => clearInterval(messageInterval)
  }, [])

  // Simulated progress timer
  useEffect(() => {
    if (isApiComplete) {
      // API call completed! Accelerate progress to 100%
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(interval)
            // Trigger fade out after showing 100% for a moment
            setTimeout(() => {
              setIsFadingOut(true)
            }, 800)
            return 100
          }
          return Math.min(100, prev + 5)
        })
      }, 50)
      return () => clearInterval(interval)
    }

    const startTime = Date.now()
    const progressInterval = setInterval(() => {
      const elapsed = (Date.now() - startTime) / 1000
      setElapsedTime(elapsed)

      // Logarithmic curve: progress decelerates as it approaches 98%
      const halfLife = targetTime * 0.4
      const calculatedProgress = 98 * (1 - Math.exp(-elapsed / halfLife))
      setProgress(Math.min(98, Math.round(calculatedProgress)))
    }, 100)

    return () => clearInterval(progressInterval)
  }, [isApiComplete, targetTime])

  // Trigger onComplete when fade out animation finishes
  useEffect(() => {
    if (isFadingOut) {
      const timer = setTimeout(() => {
        onComplete()
      }, 600) // matches framer motion exit transition duration
      return () => clearTimeout(timer)
    }
  }, [isFadingOut, onComplete])

  // Active step map based on current progress
  const activeStepIndex = useMemo(() => {
    if (progress >= 100) return STEPS.length // All done
    if (progress >= 94) return 9 // Finalizing
    if (progress >= 85) return 8 // Rendering
    if (progress >= 78) return 7 // Subtitles
    if (progress >= 70) return 6 // Syncing Audio
    if (progress >= 60) return 5 // Voiceover
    if (progress >= 42) return 4 // Generating AI Images (Takes longest)
    if (progress >= 32) return 3 // Storyboard
    if (progress >= 20) return 2 // Script
    if (progress >= 10) return 1 // Research
    return 0 // Understanding
  }, [progress])

  // Calculate estimated time remaining
  const timeRemaining = useMemo(() => {
    if (isApiComplete) return 0
    const remaining = Math.max(1, Math.round(targetTime - elapsedTime))
    // If elapsed time goes over target time, slowly decay remaining time towards 1
    if (elapsedTime >= targetTime) {
      return Math.max(1, Math.round(5 / (elapsedTime - targetTime + 2)))
    }
    return remaining
  }, [elapsedTime, targetTime, isApiComplete])

  return createPortal(
    <AnimatePresence>
      {!isFadingOut && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.6, ease: 'easeInOut' }}
          className="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-slate-950 p-4 sm:p-6"
        >
          {/* Animated Moving Gradient Background */}
          <div className="absolute inset-0 bg-gradient-to-tr from-slate-950 via-brand-950/20 to-slate-950 pointer-events-none" />
          <motion.div
            animate={{
              scale: [1, 1.2, 1],
              x: [0, 40, -40, 0],
              y: [0, -30, 30, 0],
            }}
            transition={{
              duration: 25,
              repeat: Infinity,
              ease: 'linear',
            }}
            className="absolute top-1/4 left-1/4 w-[300px] h-[300px] sm:w-[500px] sm:h-[500px] bg-brand-600/10 rounded-full blur-3xl pointer-events-none"
          />
          <motion.div
            animate={{
              scale: [1.2, 1, 1.2],
              x: [0, -40, 40, 0],
              y: [0, 30, -30, 0],
            }}
            transition={{
              duration: 30,
              repeat: Infinity,
              ease: 'linear',
            }}
            className="absolute bottom-1/4 right-1/4 w-[300px] h-[300px] sm:w-[500px] sm:h-[500px] bg-violet-600/10 rounded-full blur-3xl pointer-events-none"
          />

          {/* Floating Particles */}
          <div className="absolute inset-0 overflow-hidden pointer-events-none">
            {particles.map((particle) => (
              <motion.div
                key={particle.id}
                initial={{
                  x: `${particle.xStart}%`,
                  y: `${particle.yStart + 100}%`,
                  opacity: 0,
                }}
                animate={{
                  y: ['105%', '-5%'],
                  x: [
                    `${particle.xStart}%`,
                    `${particle.xStart + (Math.random() * 20 - 10)}%`,
                    `${particle.xStart + (Math.random() * 20 - 10)}%`,
                  ],
                  opacity: [0, 0.4, 0.4, 0],
                }}
                transition={{
                  duration: particle.duration,
                  delay: particle.delay,
                  repeat: Infinity,
                  ease: 'easeInOut',
                }}
                style={{
                  width: particle.size,
                  height: particle.size,
                }}
                className="absolute rounded-full bg-brand-400 blur-[1px]"
              />
            ))}
          </div>

          {/* Centered Glassmorphic Loading Card */}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2, duration: 0.5 }}
            className="relative w-full max-w-2xl bg-slate-900/40 backdrop-blur-xl border border-slate-800/80 rounded-3xl p-6 sm:p-8 md:p-10 shadow-2xl shadow-black/40 z-10 text-center"
          >
            {/* Rotating & Glowing AI Icon Container */}
            <div className="relative w-20 h-20 mx-auto mb-6 flex items-center justify-center">
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 15, repeat: Infinity, ease: 'linear' }}
                className="absolute inset-0 rounded-2xl bg-gradient-to-tr from-brand-600 to-violet-600 opacity-20 blur-lg animate-pulse"
              />
              <motion.div
                animate={{ rotate: -360 }}
                transition={{ duration: 10, repeat: Infinity, ease: 'linear' }}
                className="w-16 h-16 rounded-2xl bg-slate-950/80 border border-brand-500/30 flex items-center justify-center text-brand-400 shadow-lg shadow-brand-500/10"
              >
                {/* SVG Brain/AI/Video Logo */}
                <svg
                  className="w-8 h-8 text-brand-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M9.813 15.904L9 21m3.688-5.096L15 21M9 10h.01M15 10h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 14a2 2 0 100-4 2 2 0 000 4z"
                  />
                </svg>
              </motion.div>
            </div>

            {/* AI Generator Title */}
            <h3 className="text-xl sm:text-2xl font-bold tracking-tight text-white mb-1">
              Generating Video Space
            </h3>
            <p className="text-sm text-slate-400 font-medium mb-8 truncate max-w-md mx-auto px-4">
              Topic: &ldquo;{topic}&rdquo;
            </p>

            {/* Progress Percentage & Estimated remaining Time */}
            <div className="flex justify-between items-baseline mb-2 px-1">
              <div className="flex items-baseline gap-1.5">
                <span className="text-3xl font-extrabold text-white tracking-tight">
                  {progress}%
                </span>
                <span className="text-xs text-brand-400 uppercase tracking-widest font-semibold">
                  Progress
                </span>
              </div>
              <div className="text-right">
                <span className="text-xs text-slate-500 block uppercase tracking-wider">
                  Estimated Remaining
                </span>
                <span className="text-sm font-semibold text-slate-300">
                  {timeRemaining}s
                </span>
              </div>
            </div>

            {/* Glowing Smooth Progress Bar */}
            <div className="w-full h-3 bg-slate-950 rounded-full overflow-hidden border border-slate-800/80 mb-8 relative shadow-inner">
              <motion.div
                initial={{ width: 0 }}
                animate={{ width: `${progress}%` }}
                transition={{ duration: 0.1, ease: 'easeOut' }}
                className="h-full bg-gradient-to-r from-brand-500 via-indigo-500 to-violet-500 rounded-full relative"
              >
                {/* Glowing light trail */}
                <div className="absolute right-0 top-0 bottom-0 w-8 bg-white/20 blur-sm rounded-full animate-pulse" />
              </motion.div>
            </div>

            {/* Cyclical Informative Message Rotator */}
            <div className="h-8 flex items-center justify-center mb-8">
              <AnimatePresence mode="wait">
                <motion.p
                  key={messageIndex}
                  initial={{ y: 10, opacity: 0 }}
                  animate={{ y: 0, opacity: 1 }}
                  exit={{ y: -10, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                  className="text-brand-300 font-medium text-sm sm:text-base tracking-wide flex items-center gap-2"
                >
                  <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-ping shrink-0" />
                  {AI_MESSAGES[messageIndex]}
                </motion.p>
              </AnimatePresence>
            </div>

            {/* Step-by-Step Generation Steps Checklist */}
            <div className="border-t border-slate-800/60 pt-6 text-left">
              <h4 className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-4 px-1">
                Generation Pipeline Checklist
              </h4>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-x-6 gap-y-3.5">
                {STEPS.map((step, idx) => {
                  const isCompleted = idx < activeStepIndex
                  const isActive = idx === activeStepIndex

                  return (
                    <motion.div
                      key={step}
                      initial={{ opacity: 0.4 }}
                      animate={{
                        opacity: isActive ? 1 : isCompleted ? 0.9 : 0.4,
                      }}
                      className={`flex items-center gap-3 py-1.5 px-2 rounded-xl transition-all duration-300 ${
                        isActive
                          ? 'bg-brand-900/20 border border-brand-800/40 shadow-inner shadow-brand-900/10'
                          : 'border border-transparent'
                      }`}
                    >
                      {/* Left icon marker */}
                      <div className="relative flex items-center justify-center w-5 h-5 shrink-0">
                        {isCompleted ? (
                          // Green Checkmark
                          <motion.svg
                            initial={{ scale: 0 }}
                            animate={{ scale: 1 }}
                            className="w-5 h-5 text-emerald-400"
                            viewBox="0 0 20 20"
                            fill="currentColor"
                          >
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </motion.svg>
                        ) : isActive ? (
                          // Pulsing / Spinning active circle
                          <>
                            <span className="absolute inset-0 rounded-full border-2 border-brand-500/30 animate-ping" />
                            <svg className="animate-spin w-4 h-4 text-brand-400" fill="none" viewBox="0 0 24 24">
                              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="3" />
                              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                            </svg>
                          </>
                        ) : (
                          // Idle Bullet
                          <span className="w-2.5 h-2.5 rounded-full bg-slate-800 border border-slate-700" />
                        )}
                      </div>

                      {/* Step Name */}
                      <span
                        className={`text-xs sm:text-sm font-medium ${
                          isActive
                            ? 'text-brand-300 font-semibold drop-shadow-[0_0_8px_rgba(129,140,248,0.25)]'
                            : isCompleted
                            ? 'text-slate-300 line-through decoration-slate-800/80 decoration-2'
                            : 'text-slate-500'
                        }`}
                      >
                        {step}
                      </span>
                    </motion.div>
                  )
                })}
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>,
    document.body
  )
}
