import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { uploadMissingPerson, listMissingPersons, deleteMissingPerson } from '../api';

interface Person {
  person_id: string;
  name: string;
  description?: string;
  last_seen_location?: string;
  date_reported: string;
  contact_info: string;
  photo_urls: string[];
}

const AdminPanel: React.FC = () => {
  const [persons, setPersons] = useState<Person[]>([]);
  const [showUploadForm, setShowUploadForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    date_reported: '',
    contact_info: '',
    description: '',
    last_seen_location: ''
  });
  const [photos, setPhotos] = useState<File[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/admin/login');
      return;
    }
    loadPersons();
  }, []);

  const loadPersons = async () => {
    try {
      const data = await listMissingPersons();
      setPersons(data);
    } catch (err) {
      console.error('Failed to load persons:', err);
    }
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (photos.length === 0) {
      setError('Please select at least one photo');
      return;
    }

    setLoading(true);
    setError('');

    try {
      await uploadMissingPerson({
        ...formData,
        photos
      });
      
      setShowUploadForm(false);
      setFormData({
        name: '',
        date_reported: '',
        contact_info: '',
        description: '',
        last_seen_location: ''
      });
      setPhotos([]);
      loadPersons();
    } catch (err: any) {
      setError(err.response?.data?.error?.message || 'Upload failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (personId: string) => {
    if (!confirm('Are you sure you want to delete this person?')) return;

    try {
      await deleteMissingPerson(personId);
      loadPersons();
    } catch (err) {
      alert('Failed to delete person');
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    navigate('/admin/login');
  };

  return (
    <div>
      <div className="header">
        <h1>Admin Panel</h1>
        <button onClick={handleLogout} className="button" style={{ marginTop: '10px' }}>
          Logout
        </button>
      </div>

      <div className="container">
        <button
          className="button"
          onClick={() => setShowUploadForm(!showUploadForm)}
        >
          {showUploadForm ? 'Cancel' : 'Add Missing Person'}
        </button>

        {showUploadForm && (
          <div className="card" style={{ marginTop: '20px' }}>
            <h2>Upload Missing Person</h2>
            <form onSubmit={handleUpload}>
              <input
                type="text"
                placeholder="Name *"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="input"
                required
              />
              <input
                type="date"
                placeholder="Date Reported *"
                value={formData.date_reported}
                onChange={(e) => setFormData({ ...formData, date_reported: e.target.value })}
                className="input"
                required
              />
              <input
                type="text"
                placeholder="Contact Info *"
                value={formData.contact_info}
                onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
                className="input"
                required
              />
              <input
                type="text"
                placeholder="Last Seen Location"
                value={formData.last_seen_location}
                onChange={(e) => setFormData({ ...formData, last_seen_location: e.target.value })}
                className="input"
              />
              <textarea
                placeholder="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="input"
                rows={3}
              />
              <input
                type="file"
                accept="image/*"
                multiple
                onChange={(e) => setPhotos(Array.from(e.target.files || []))}
                className="input"
                required
              />
              
              {error && (
                <div style={{ color: '#e74c3c', marginBottom: '10px' }}>
                  {error}
                </div>
              )}

              <button type="submit" className="button" disabled={loading}>
                {loading ? 'Uploading...' : 'Upload'}
              </button>
            </form>
          </div>
        )}

        <div className="card" style={{ marginTop: '20px' }}>
          <h2>Missing Persons ({persons.length})</h2>
          {persons.map((person) => (
            <div key={person.person_id} className="match-card">
              <div className="match-info">
                <h3>{person.name}</h3>
                <p><strong>Reported:</strong> {new Date(person.date_reported).toLocaleDateString()}</p>
                {person.last_seen_location && (
                  <p><strong>Last seen:</strong> {person.last_seen_location}</p>
                )}
                <p><strong>Contact:</strong> {person.contact_info}</p>
                {person.description && <p>{person.description}</p>}
                <button
                  onClick={() => handleDelete(person.person_id)}
                  style={{ background: '#e74c3c', marginTop: '10px' }}
                  className="button"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default AdminPanel;
