import { useEffect, useState } from 'react'
import { NavLink } from 'react-router-dom'

import StatisticCard from '../components/StatisticCard'
import VideoCard from '../components/VideoCard'
import LoadingSkeleton from '../components/LoadingSkeleton'
import QuickActionCard from '../components/QuickActionCard'

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
  const hrs = Math.floor(seconds / 3600)
  const mins = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  const parts = []
  if (hrs) parts.push(`${hrs}h`)
  if (mins) parts.push(`${mins}m`)
  if (secs || parts.length === 0) parts.push(`${secs}s`)
  return parts.join(' ')
}

function formatSize(bytes?: number): string {
  if (!bytes) return '-'
  const kb = bytes / 1024
  if (kb < 1024) return `${kb.toFixed(2)} KB`
  const mb = kb / 1024
  if (mb < 1024) return `${mb.toFixed(2)} MB`
  const gb = mb / 1024
  return `${gb.toFixed(2)} GB`
}

export default function Dashboard() {
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

  // Statistics calculations
  const totalVideos = videos.length
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const yesterday = new Date(today)
  yesterday.setDate(yesterday.getDate() - 1)

  const videosCreatedToday = videos.filter(v => {
    const d = new Date(v.created_at)
    d.setHours(0, 0, 0, 0)
    return d.getTime() === today.getTime()
  }).length

  const totalDurationSeconds = videos.reduce((sum, v) => sum + (v.duration || 0), 0)
  const totalStorageBytes = videos.reduce((sum, v) => sum + (v.file_size || 0), 0)

  const recentVideos = [...videos]
    .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    .slice(0, 5)

  // Timeline grouping
  const timelineGroups: { [key: string]: Video[] } = { Today: [], Yesterday: [], Earlier: [] }
  videos.forEach(v => {
    const d = new Date(v.created_at)
    const dMid = new Date(d)
    dMid.setHours(0, 0, 0, 0)
    if (dMid.getTime() === today.getTime()) {
      timelineGroups['Today'].push(v)
    } else if (dMid.getTime() === yesterday.getTime()) {
      timelineGroups['Yesterday'].push(v)
    } else {
      timelineGroups['Earlier'].push(v)
    }
  })

  if (loading) {
    return (
      <div className="p-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <LoadingSkeleton count={4} />
        </div>
        <LoadingSkeleton count={5} />
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

  // Empty state
  if (videos.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen py-20">
        <h1 className="text-3xl font-bold text-white mb-4">Dashboard</h1>
        <p className="text-slate-400 mb-6">No videos have been generated yet.</p>
        <NavLink to="/create" className="px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl transition-colors">
          Create Your First Video
        </NavLink>
      </div>
    )
  }

  return (
    <div className="p-6">
      {/* Hero */}
      <section className="text-center mb-12">
        <h1 className="text-4xl font-bold text-white mb-4">AI Educational Video Generator</h1>
        <p className="text-lg text-slate-300 mb-8">
          Create professional AI educational videos with animated presenters, voice narration, visuals, and burned-in subtitles.
        </p>
        <div className="flex justify-center gap-4">
          <NavLink to="/create" className="px-6 py-3 bg-brand-600 hover:bg-brand-500 text-white rounded-xl transition-colors">
            + Create New Video
          </NavLink>
          <NavLink to="/library" className="px-6 py-3 bg-slate-600 hover:bg-slate-500 text-white rounded-xl transition-colors">
            My Videos
          </NavLink>
        </div>
      </section>

      {/* Statistics */}
      <section className="mb-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <StatisticCard title="Total Videos" value={totalVideos} />
          <StatisticCard title="Videos Created Today" value={videosCreatedToday} />
          <StatisticCard title="Total Video Duration" value={formatDuration(totalDurationSeconds)} />
          <StatisticCard title="Total Storage Used" value={formatSize(totalStorageBytes)} />
        </div>
      </section>

      {/* Quick Actions */}
      <section className="mb-12">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <QuickActionCard title="Create Video" to="/create" bgColor="bg-brand-600" />
          <QuickActionCard title="Browse Library" to="/library" bgColor="bg-slate-600" />
          <QuickActionCard title="Generate Another" to="/create" bgColor="bg-brand-500" description="Start a new video generation" />
        </div>
      </section>

      {/* Recent Videos */}
      <section className="mb-12">
        <h2 className="text-2xl font-semibold text-white mb-4">Recent Videos</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {recentVideos.map(video => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>
      </section>

      {/* Generation History Timeline */}
      <section>
        <h2 className="text-2xl font-semibold text-white mb-4">Generation History</h2>
        {Object.entries(timelineGroups).map(([group, vids]) => (
          vids.length > 0 && (
            <div key={group} className="mb-8">
              <h3 className="text-xl font-medium text-slate-300 mb-4">{group}</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {vids.map(v => (
                  <VideoCard key={v.id} video={v} />
                ))}
              </div>
            </div>
          )
        ))}
      </section>
    </div>
  )
}
