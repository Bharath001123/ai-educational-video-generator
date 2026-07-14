import { useEffect, useState } from 'react'
import VideoCard from '../components/VideoCard'
import LoadingSkeleton from '../components/LoadingSkeleton'

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

export default function MyVideos() {
  const [videos, setVideos] = useState<Video[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchVideos = async () => {
    setLoading(true)
    setError(null)
    try {
      const resp = await fetch('/api/library')
      if (!resp.ok) throw new Error('Network response was not ok')
      const data = await resp.json()
      setVideos(data.videos)
    } catch (e: any) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchVideos()
  }, [])

  if (loading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          <LoadingSkeleton count={6} />
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-900/60 text-red-200 p-4 rounded-lg flex justify-between items-center">
          <span>Failed to load videos: {error}</span>
          <button onClick={fetchVideos} className="underline hover:text-white">Retry</button>
        </div>
      </div>
    )
  }

  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-20">
        <p className="text-slate-400 mb-4">No videos generated yet.</p>
        <a href="/" className="bg-brand-600 hover:bg-brand-500 text-white px-4 py-2 rounded">Create Your First Video</a>
      </div>
    )
  }

  const handleDelete = (id: number) => {
    setVideos((prev) => prev.filter((v) => v.id !== id));
  };

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-white mb-6">My Videos</h1>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {videos.map((video) => (
          <VideoCard key={video.id} video={video} onDelete={handleDelete} />
        ))}
      </div>
    </div>
  )
}
