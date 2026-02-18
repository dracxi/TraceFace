import React, { useState } from 'react';
import { searchFace } from '../api';

interface Match {
  person_id: string;
  name: string;
  similarity_score: number;
  photo_url: string;
  last_seen_location?: string;
  date_reported: string;
  contact_info: string;
}

const SearchPage: React.FC = () => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string>('');
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [noFaceDetected, setNoFaceDetected] = useState(false);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreview(URL.createObjectURL(file));
      setMatches([]);
      setError('');
      setNoFaceDetected(false);
    }
  };

  const handleSearch = async () => {
    if (!selectedFile) return;

    setLoading(true);
    setError('');
    setNoFaceDetected(false);

    try {
      const result = await searchFace(selectedFile);
      
      if (!result.query_face_detected) {
        setNoFaceDetected(true);
        setMatches([]);
      } else {
        setMatches(result.matches);
      }
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <div className="header">
        <h1>Missing Person Face Recognition</h1>
        <p>Upload a photo to search for missing persons</p>
      </div>

      <div className="container">
        <div className="card">
          <h2>Upload Photo</h2>
          <input
            type="file"
            accept="image/*"
            onChange={handleFileSelect}
            className="input"
          />
          
          {preview && (
            <div style={{ marginTop: '20px' }}>
              <img src={preview} alt="Preview" style={{ maxWidth: '300px', borderRadius: '8px' }} />
            </div>
          )}

          <button
            className="button"
            onClick={handleSearch}
            disabled={!selectedFile || loading}
            style={{ marginTop: '20px' }}
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {error && (
          <div className="card" style={{ background: '#e74c3c', color: 'white' }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        {noFaceDetected && (
          <div className="card" style={{ background: '#f39c12', color: 'white' }}>
            <strong>No face detected</strong> in the uploaded image. Please upload a clear photo containing a face.
          </div>
        )}

        {matches.length > 0 && (
          <div className="card">
            <h2>Matches Found ({matches.length})</h2>
            {matches.map((match) => (
              <div key={match.person_id} className="match-card">
                <img src={match.photo_url} alt={match.name} className="match-photo" />
                <div className="match-info">
                  <h3>{match.name}</h3>
                  <p className="similarity-score">
                    {(match.similarity_score * 100).toFixed(1)}% Match
                  </p>
                  {match.last_seen_location && (
                    <p><strong>Last seen:</strong> {match.last_seen_location}</p>
                  )}
                  <p><strong>Reported:</strong> {new Date(match.date_reported).toLocaleDateString()}</p>
                  <p><strong>Contact:</strong> {match.contact_info}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {matches.length === 0 && !loading && !error && !noFaceDetected && selectedFile && (
          <div className="card">
            <p>No matches found. The person may not be in our database.</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
