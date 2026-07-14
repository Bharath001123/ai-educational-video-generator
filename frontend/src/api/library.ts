const API_BASE_URL = 'https://ai-video-generator-backend-24gk.onrender.com';

export async function getLibrary() {
  const response = await fetch(`${API_BASE_URL}/api/library`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch library.');
  }

  return response.json();
}

export async function saveToLibrary(scriptData: any) {
  const response = await fetch(`${API_BASE_URL}/api/library/save`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(scriptData),
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return {
      success: false,
      message: errorData.detail || 'Failed to save video.',
    };
  }

  const data = await response.json();
  return {
    success: true,
    data,
  };
}
export async function deleteVideo(id: number) {
  const response = await fetch(`${API_BASE_URL}/api/library/${id}`, {
    method: 'DELETE',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    return { success: false, message: errorData.detail || 'Failed to delete video.' };
  }
  return { success: true };
}
