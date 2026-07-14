import { useLocation, useNavigate } from 'react-router-dom';
import { useState } from 'react';
import { saveToLibrary } from '../api/library'; // assume this API helper exists

function ResultPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const generatedScript = (location.state as any)?.script;

  const [saveStatus, setSaveStatus] = useState<string | null>(null);

  if (!generatedScript) {
    // If no script data, redirect back to create page
    navigate('/', { replace: true });
    return null;
  }

  const handleSave = async () => {
    try {
      const {
        video_url,
        title,
        presenter_type,
        language,
        duration,
        subtitle_url,
        ...rest
      } = generatedScript;

      const payload = {
        video_url,
        title: title ?? 'Untitled',
        presenter_type,
        language,
        duration,
        subtitle_url,
        metadata: rest,
      };

      const response = await saveToLibrary(payload);
      if (response.success) {
        setSaveStatus('Video saved successfully.');
      } else if (response.message?.includes('already')) {
        setSaveStatus('This video is already in your library.');
      } else {
        setSaveStatus('Failed to save video.');
      }
    } catch (e) {
      setSaveStatus('Error saving video.');
    }
  };

  const handleDownload = () => {
    const link = document.createElement('a');
    link.href = generatedScript.video_url;
    link.download = `${generatedScript.title || 'video'}.mp4`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleCreateAnother = () => {
    navigate('/create', { replace: true });
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-4">Video Generation Result</h1>
      <div className="mb-4">
        <video
          src={generatedScript.video_url}
          controls
          className="w-full rounded-lg border border-slate-800"
        />
      </div>
      <div className="flex gap-4 mb-4">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-emerald-600 text-white rounded hover:bg-emerald-500 transition"
        >
          Save to Library
        </button>
        <button
          onClick={handleDownload}
          className="px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-500 transition"
        >
          Download MP4
        </button>
        <button
          onClick={handleCreateAnother}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 transition"
        >
          Create Another Video
        </button>
      </div>
      {saveStatus && (
        <div className="mt-2 text-sm text-emerald-300">
          {saveStatus}
        </div>
      )}
    </div>
  );
}

export default ResultPage;
