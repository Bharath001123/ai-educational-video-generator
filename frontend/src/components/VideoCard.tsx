import { useState } from 'react'
import Modal from './Modal'
import { deleteVideo } from '../api/library'

type Video = {
  id: number
  title: string
  created_at: string
  duration: number
  presenter_type: string
  voice?: string
  language?: string
  file_size?: number
  resolution?: string
  thumbnail_path?: string
  video_path?: string
  subtitle_path?: string
  status?: string
}

function formatDuration(seconds: number): string {
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}m ${secs}s`
}

export default function VideoCard({ video, onDelete }: { video: Video; onDelete?: (id: number) => void }) {
  const [previewOpen, setPreviewOpen] = useState(false)
  const [detailsOpen, setDetailsOpen] = useState(false)

  return (
    <div className="bg-slate-900/60 rounded-2xl border border-slate-800 shadow-xl hover:shadow-2xl transition-shadow p-4 flex flex-col">
      {/* Thumbnail */}
      {video.thumbnail_path ? (
        <img
          src={video.thumbnail_path}
          alt={video.title}
          className="w-full h-48 object-cover rounded-lg mb-4"
        />
      ) : (
        <div className="w-full h-48 bg-slate-800 rounded-lg mb-4 flex items-center justify-center text-slate-500">
          No thumbnail
        </div>
      )}

      {/* Basic info */}
      <h3 className="text-lg font-semibold text-white mb-2 truncate" title={video.title}>
        {video.title}
      </h3>
      <div className="text-sm text-slate-400 mb-2">
        <span className="mr-2">{video.presenter_type}</span>
        {video.language && <span className="mr-2">{video.language}</span>}
        <span>{formatDuration(video.duration || 0)}</span>
      </div>
      <div className="text-xs text-slate-500 mb-2">
        {new Date(video.created_at).toLocaleDateString()}
      </div>
      {/* Status badge */}
      {video.status && (
        <span
          className={`inline-block px-2 py-0.5 text-xs rounded ${
            video.status === 'completed' ? 'bg-green-600/30 text-green-200' : 'bg-amber-600/30 text-amber-200'
          }`}
        >
          {video.status}
        </span>
      )}

      {/* Action buttons */}
      <div className="mt-4 space-x-2">
        <button
          onClick={() => setPreviewOpen(true)}
          className="px-3 py-1 rounded bg-brand-600 hover:bg-brand-500 text-white text-sm transition-colors"
        >
          ▶ Preview
        </button>
        {video.video_path && (
          <a
            href={video.video_path}
            download
            className="px-3 py-1 rounded bg-slate-600 hover:bg-slate-500 text-white text-sm transition-colors"
          >
            ⬇ Download
          </a>
        )}
        <button
          onClick={() => setDetailsOpen(true)}
          className="px-3 py-1 rounded bg-slate-700 hover:bg-slate-600 text-white text-sm transition-colors"
        >
          ℹ Details
        </button>
        {onDelete && (
          <button
            onClick={async () => {
              const result = await deleteVideo(video.id);
              if (result.success) {
                onDelete(video.id);
              } else {
                alert(result.message || 'Failed to delete video');
              }
            }}
            className="px-3 py-1 rounded bg-red-600 hover:bg-red-500 text-white text-sm transition-colors"
            title="Delete video"
          >
            🗑️ Delete
          </button>
        )}
      </div>

      {/* Preview Modal */}
      {previewOpen && video.video_path && (
        <Modal onClose={() => setPreviewOpen(false)}>
          <h2 className="text-xl font-bold text-white mb-4">{video.title}</h2>
          <video
            src={video.video_path}
            controls
            className="w-full rounded mb-4"
          />
          <div className="text-sm text-slate-300">
            <p>Presenter: {video.presenter_type}</p>
            <p>Duration: {formatDuration(video.duration || 0)}</p>
            <p>Created: {new Date(video.created_at).toLocaleString()}</p>
          </div>
        </Modal>
      )}

      {/* Details Modal */}
      {detailsOpen && (
        <Modal onClose={() => setDetailsOpen(false)}>
          <h2 className="text-xl font-bold text-white mb-4">Video Details</h2>
          <dl className="grid grid-cols-1 gap-2 text-sm text-slate-300">
            <div>
              <dt className="font-medium text-slate-400">Title</dt>
              <dd>{video.title}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Presenter</dt>
              <dd>{video.presenter_type}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Voice</dt>
              <dd>{video.voice || '-'}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Language</dt>
              <dd>{video.language || '-'}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Duration</dt>
              <dd>{formatDuration(video.duration || 0)}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Created</dt>
              <dd>{new Date(video.created_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">File size</dt>
              <dd>{video.file_size ? `${(video.file_size / (1024 * 1024)).toFixed(2)} MB` : '-'}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Resolution</dt>
              <dd>{video.resolution || '-'}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-400">Status</dt>
              <dd>{video.status || '-'}</dd>
            </div>
          </dl>
        </Modal>
      )}
    </div>
  )
}
