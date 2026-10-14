/* Tutti API client. One function per endpoint; see README "API" for shapes.
   Every call returns a Promise of the parsed JSON, or rejects with an Error that has
   .status (HTTP status, 0 for network failure) and a human-readable .message. */
(function () {
  const MAX_UPLOAD_BYTES = 500 * 1024 * 1024;

  function toError(status, message) {
    const error = new Error(message);
    error.status = status;
    return error;
  }

  async function request(method, path, body) {
    const options = { method, credentials: 'same-origin', headers: {} };
    if (body !== undefined) {
      options.headers['Content-Type'] = 'application/json';
      options.body = JSON.stringify(body);
    }
    let response;
    try {
      response = await fetch(path, options);
    } catch (networkError) {
      console.error('Tutti API network error', path, networkError);
      throw toError(0, 'Could not reach the Tutti server. Check that "python3 run.py" is still running.');
    }
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw toError(response.status, data.error || `The server answered ${response.status}.`);
    return data;
  }

  function withQuery(path, params) {
    const query = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') query.set(key, value);
    });
    const text = query.toString();
    return text ? `${path}?${text}` : path;
  }

  /* Raw MP4 body with metadata in the query string. onProgress(fraction 0..1) is optional. */
  function upload(path, params, file, onProgress) {
    return new Promise((resolve, reject) => {
      if (!file) return reject(toError(0, 'Choose an MP4 video first.'));
      if (file.size > MAX_UPLOAD_BYTES) return reject(toError(0, 'That file is over the 500 MB limit. Export a shorter or smaller MP4.'));
      const xhr = new XMLHttpRequest();
      xhr.open('POST', withQuery(path, params));
      xhr.setRequestHeader('Content-Type', 'video/mp4');
      xhr.upload.onprogress = (event) => onProgress && event.lengthComputable && onProgress(event.loaded / event.total);
      xhr.onerror = () => reject(toError(0, 'The upload was interrupted. Check your connection and try again.'));
      xhr.onload = () => {
        let data = {};
        try { data = JSON.parse(xhr.responseText); } catch (parseError) { console.error('Bad upload response', parseError); }
        if (xhr.status >= 200 && xhr.status < 300) resolve(data);
        else reject(toError(xhr.status, data.error || `The upload failed (${xhr.status}).`));
      };
      xhr.send(file);
    });
  }

  const get = (path, params) => request('GET', withQuery(path, params));

  window.api = {
    MAX_UPLOAD_BYTES,
    // Session
    me: () => get('/api/me'),
    accounts: () => get('/api/accounts'),
    signIn: (email, password) => request('POST', '/api/sign-in', { email, password }),
    signInAs: (role) => request('POST', '/api/sign-in-as', { role }),
    switchTo: (userId) => request('POST', '/api/switch', { user_id: userId }),
    signOut: () => request('POST', '/api/sign-out'),
    // Sections and feed (public)
    sections: () => get('/api/sections'),
    section: (category) => get(`/api/sections/${category}`),
    feed: (params) => get('/api/feed', params),
    clips: (params) => get('/api/clips', params),
    // Musicians
    musicians: (params) => get('/api/musicians', params),
    musician: (handle) => get(`/api/musicians/${encodeURIComponent(handle)}`),
    updateMe: (fields) => request('PUT', '/api/me', fields),
    createPost: (body, category, clipId) => request('POST', '/api/posts', { body, category, clip_id: clipId }),
    uploadClip: (file, { title, instrument }, onProgress) => upload('/api/clips', { title, instrument }, file, onProgress),
    // Auditions
    auditions: (params) => get('/api/auditions', params),
    audition: (id) => get(`/api/auditions/${id}`),
    createAudition: (fields) => request('POST', '/api/auditions', fields),
    editAudition: (id, fields) => request('PUT', `/api/auditions/${id}`, fields),
    // Submissions
    mySubmissions: () => get('/api/my/submissions'),
    submitClip: (auditionId, { clipId, note, timestamps }) =>
      request('POST', `/api/auditions/${auditionId}/submissions`, { clip_id: clipId, note, timestamps }),
    submitUpload: (auditionId, file, { note, timestamps }, onProgress) =>
      upload(`/api/auditions/${auditionId}/submissions`, { note, timestamps: JSON.stringify(timestamps || []) }, file, onProgress),
    // Director
    dashboard: () => get('/api/director/dashboard'),
    auditionSubmissions: (auditionId, status) => get(`/api/auditions/${auditionId}/submissions`, { status }),
    submission: (id) => get(`/api/submissions/${id}`),
    submissionVideoUrl: (id) => `/api/submissions/${id}/video`,
    saveReview: (id, review) => request('PUT', `/api/submissions/${id}/review`, review),
  };
})();
