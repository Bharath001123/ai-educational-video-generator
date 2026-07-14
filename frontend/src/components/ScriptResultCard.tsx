import type { GeneratedScript } from '../api/video'

interface ScriptResultCardProps {
  script: GeneratedScript
}

function ScriptResultCard({ script }: ScriptResultCardProps) {
  const hasScenes = script.scenes && script.scenes.length > 0

  return (
    <div className="script-result-card">
      <div className="flex items-start gap-3 pb-4 mb-6 border-b border-slate-800">
        <div className="w-10 h-10 rounded-xl bg-emerald-600/20 flex items-center justify-center shrink-0">
          <svg
            className="w-5 h-5 text-emerald-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
        </div>
        <div className="min-w-0">
          <p className="text-xs font-medium uppercase tracking-wider text-emerald-400 mb-1">
            Generated Project
          </p>
          <h3 className="text-lg sm:text-xl font-semibold text-slate-100 break-words">
            {script.title}
          </h3>
          <div className="flex flex-wrap gap-2 mt-3">
            <span className="script-meta-tag">
              {script.duration ?? script.metadata.duration}
            </span>
            {hasScenes && (
              <span className="script-meta-tag">{script.scenes.length} scenes</span>
            )}
            <span className="script-meta-tag">{script.metadata.audience}</span>
            <span className="script-meta-tag">{script.metadata.language}</span>
            {script.metadata.presenter_type && script.metadata.presenter_type !== 'none' && (
              <span className="script-meta-tag flex items-center gap-1.5 border-emerald-800/80 bg-emerald-950/20 text-emerald-400">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Teacher: {script.metadata.presenter_type.toUpperCase()}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Watch Rendered Video Section */}
      {script.video_url && (
        <div className="mb-8 rounded-xl border border-slate-800 bg-slate-950/60 p-4 sm:p-5">
          <h4 className="text-sm font-semibold text-brand-300 mb-3 flex items-center gap-2">
            <span className="w-2.5 h-2.5 rounded-full bg-brand-500 animate-pulse" />
            Watch Generated Video
          </h4>
          <div className="relative aspect-video rounded-lg overflow-hidden border border-slate-800 bg-black shadow-inner">
            <video
              src={script.video_url}
              controls
              className="w-full h-full object-contain"
              crossOrigin="anonymous"
            >
              {script.subtitle_url && (
                <track
                  kind="subtitles"
                  src={script.subtitle_url}
                  srcLang={script.metadata.language.toLowerCase()}
                  label={`${script.metadata.language} Subtitles`}
                  default
                />
              )}
              Your browser does not support the video tag.
            </video>
          </div>
          {script.subtitle_url && (
            <div className="mt-3 flex justify-between items-center text-xs text-slate-500">
              <span className="flex items-center gap-1.5">
                <svg className="w-4 h-4 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Subtitles loaded (WebVTT)
              </span>
              <a
                href={script.srt_url || script.subtitle_url.replace('.vtt', '.srt')}
                download
                className="text-brand-400 hover:text-brand-300 font-medium transition-colors inline-flex items-center gap-1"
                target="_blank"
                rel="noopener noreferrer"
              >
                Download SRT
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </a>
            </div>
          )}
        </div>
      )}

      {hasScenes ? (
        <div className="space-y-4">
          <h4 className="text-sm font-semibold text-slate-400 mb-1 px-1">
            Scene Breakdown
          </h4>
          {script.scenes.map((scene) => (
            <div key={scene.scene_number} className="scene-card">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-center gap-2">
                  <h4 className="text-sm font-semibold text-brand-300">
                    Scene {scene.scene_number}
                  </h4>
                  {scene.visual_source && (
                    scene.visual_source === 'real' ? (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-emerald-950/80 text-emerald-400 border border-emerald-800/60" title={`Retrieved from Wikimedia Commons using query: ${scene.search_query}`}>
                        Real Image
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 text-[10px] font-semibold rounded-full bg-blue-950/80 text-blue-400 border border-blue-900/60">
                        AI Generated
                      </span>
                    )
                  )}
                </div>
                <span className="text-xs text-slate-500">
                  {scene.duration_seconds}s
                </span>
              </div>
              <div className="space-y-4">
                {scene.image_url && (
                  <div>
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                      {scene.visual_source === 'real' 
                        ? `Retrieved Image ${scene.search_query ? `(Search: "${scene.search_query}")` : ''}` 
                        : 'AI Generated Image'}
                    </p>
                    <img
                      src={scene.image_url}
                      alt={`Scene ${scene.scene_number} visual`}
                      className="scene-image"
                      loading="lazy"
                    />
                  </div>
                )}
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">
                    Visual Prompt
                  </p>
                  <p className="text-sm text-slate-400 leading-relaxed">
                    {scene.visual_prompt}
                  </p>
                </div>
                <div>
                  <p className="text-xs uppercase tracking-wide text-slate-500 mb-1">
                    Voiceover
                  </p>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {scene.voiceover}
                  </p>
                </div>
                {scene.audio_url && (
                  <div className="pt-2 border-t border-slate-900/60">
                    <p className="text-xs uppercase tracking-wide text-slate-500 mb-2">
                      Play Voiceover Audio
                    </p>
                    <audio
                      src={scene.audio_url}
                      controls
                      className="w-full max-w-md h-8 rounded bg-slate-950 border border-slate-800"
                    />
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="script-content">
          <pre className="script-text">{script.script}</pre>
        </div>
      )}
    </div>
  )
}

export default ScriptResultCard
