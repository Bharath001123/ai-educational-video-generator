import VideoGeneratorForm from './VideoGeneratorForm'

function GeneratorSection() {
  return (
    <section id="generator" className="relative py-12 sm:py-20">
      <div className="absolute inset-0 bg-gradient-to-b from-brand-900/20 via-transparent to-transparent pointer-events-none" />
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[500px] h-[500px] bg-brand-600/10 rounded-full blur-3xl pointer-events-none" />

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6">
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-brand-900/50 border border-brand-700/50 text-brand-300 text-sm mb-6">
            <span className="w-2 h-2 rounded-full bg-brand-400 animate-pulse" />
            AI Video Studio
          </div>
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-4">
            Create Your
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-brand-400 to-brand-200">
              {' '}
              Educational Video
            </span>
          </h1>
          <p className="text-slate-400 text-base sm:text-lg max-w-xl mx-auto">
            Configure your topic, audience, and preferences — then let AI handle
            the rest.
          </p>
        </div>

        <div className="generator-card">
          <div className="flex items-center gap-3 pb-6 mb-6 border-b border-slate-800">
            <div className="w-10 h-10 rounded-xl bg-brand-600/20 flex items-center justify-center">
              <svg
                className="w-5 h-5 text-brand-400"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={1.5}
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
                />
              </svg>
            </div>
            <div>
              <h2 className="font-semibold text-lg">Video Configuration</h2>
              <p className="text-sm text-slate-500">
                Fill in the details below to generate your video
              </p>
            </div>
          </div>

          <VideoGeneratorForm />
        </div>
      </div>
    </section>
  )
}

export default GeneratorSection
