import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  uploadMissingPerson,
  listMissingPersons,
  deleteMissingPerson,
  getDashboardStats,
  updatePersonStatus,
  updatePersonDetails,
  exportData,
  validateToken
} from '../api';
import { useToast } from '../contexts/ToastContext';
import ImageUpload from '../components/ImageUpload';
import LoadingSpinner from '../components/LoadingSpinner';
import Input from '../components/Input';
import Select from '../components/Select';
import TextArea from '../components/TextArea';
import Logo from '../components/Logo';
import Footer from '../components/Footer';

interface Person {
  person_id: string;
  name: string;
  age?: number;
  gender?: string;
  description?: string;
  last_seen_location?: string;
  date_reported: string;
  contact_info: string;
  status: string;
  traced_date?: string;
  traced_notes?: string;
  photo_urls: string[];
}

interface DashboardStats {
  total_records: number;
  missing_count: number;
  traced_count: number;
  searches_today: number;
  recent_uploads: any[];
}

const AdminPanel: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'dashboard' | 'manage' | 'add'>('dashboard');
  const [persons, setPersons] = useState<Person[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [editingPerson, setEditingPerson] = useState<Person | null>(null);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [statusPerson, setStatusPerson] = useState<Person | null>(null);
  const [showImageModal, setShowImageModal] = useState(false);
  const [viewingPerson, setViewingPerson] = useState<Person | null>(null);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  
  // Form state
  const [formData, setFormData] = useState({
    name: '',
    age: '',
    gender: '',
    date_reported: '',
    contact_info: '',
    description: '',
    last_seen_location: ''
  });
  const [photos, setPhotos] = useState<File[]>([]);
  const [formErrors, setFormErrors] = useState<any>({});

  const navigate = useNavigate();
  const { addToast } = useToast();

  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      navigate('/admin/login');
      return;
    }
    
    // Validate token and load dashboard
    const initializeDashboard = async () => {
      try {
        // First validate the token
        await validateToken();
        // If validation succeeds, load dashboard
        await loadDashboard();
      } catch (error) {
        // Token is invalid, redirect to login
        localStorage.removeItem('token');
        addToast({ type: 'error', message: 'Session expired. Please login again.' });
        navigate('/admin/login');
      }
    };
    
    initializeDashboard();
  }, []);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [statsData, personsData] = await Promise.all([
        getDashboardStats(),
        listMissingPersons()
      ]);
      setStats(statsData);
      setPersons(personsData);
    } catch (err) {
      addToast({ type: 'error', message: 'Failed to load dashboard data' });
    } finally {
      setLoading(false);
    }
  };

  const validateForm = () => {
    const errors: any = {};
    if (!formData.name) errors.name = 'Name is required';
    if (!formData.date_reported) errors.date_reported = 'Date is required';
    if (!formData.contact_info) errors.contact_info = 'Contact info is required';
    if (photos.length === 0 && !editingPerson) errors.photos = 'At least one photo is required';
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      addToast({ type: 'error', message: 'Please fill in all required fields' });
      return;
    }

    setLoading(true);
    try {
      await uploadMissingPerson({
        name: formData.name,
        age: formData.age ? parseInt(formData.age) : undefined,
        gender: formData.gender || undefined,
        date_reported: formData.date_reported,
        contact_info: formData.contact_info,
        description: formData.description || undefined,
        last_seen_location: formData.last_seen_location || undefined,
        photos
      });
      
      addToast({ type: 'success', message: 'Person added successfully!' });
      resetForm();
      setActiveTab('manage');
      loadDashboard();
    } catch (err: any) {
      addToast({ type: 'error', message: err.response?.data?.error?.message || 'Upload failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingPerson) return;

    setLoading(true);
    try {
      await updatePersonDetails(editingPerson.person_id, {
        name: formData.name,
        age: formData.age ? parseInt(formData.age) : undefined,
        gender: formData.gender || undefined,
        description: formData.description || undefined,
        last_seen_location: formData.last_seen_location || undefined,
        contact_info: formData.contact_info
      });
      
      addToast({ type: 'success', message: 'Person updated successfully!' });
      setEditingPerson(null);
      resetForm();
      loadDashboard();
    } catch (err) {
      addToast({ type: 'error', message: 'Update failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (personId: string) => {
    if (!confirm('Are you sure you want to delete this person?')) return;

    setLoading(true);
    try {
      await deleteMissingPerson(personId);
      addToast({ type: 'success', message: 'Person deleted successfully' });
      loadDashboard();
    } catch (err) {
      addToast({ type: 'error', message: 'Delete failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleStatusUpdate = async (status: string, tracedDate?: string, tracedNotes?: string) => {
    if (!statusPerson) return;

    setLoading(true);
    try {
      await updatePersonStatus(statusPerson.person_id, {
        status,
        traced_date: tracedDate,
        traced_notes: tracedNotes
      });
      
      addToast({ type: 'success', message: 'Status updated successfully!' });
      setShowStatusModal(false);
      setStatusPerson(null);
      loadDashboard();
    } catch (err) {
      addToast({ type: 'error', message: 'Status update failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async (format: 'csv' | 'excel') => {
    setLoading(true);
    try {
      await exportData(format);
      addToast({ type: 'success', message: `Exported to ${format.toUpperCase()}` });
    } catch (err) {
      addToast({ type: 'error', message: 'Export failed' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setFormData({
      name: '',
      age: '',
      gender: '',
      date_reported: '',
      contact_info: '',
      description: '',
      last_seen_location: ''
    });
    setPhotos([]);
    setFormErrors({});
  };

  const startEdit = (person: Person) => {
    setEditingPerson(person);
    setFormData({
      name: person.name,
      age: person.age?.toString() || '',
      gender: person.gender || '',
      date_reported: person.date_reported.split('T')[0],
      contact_info: person.contact_info,
      description: person.description || '',
      last_seen_location: person.last_seen_location || ''
    });
    setActiveTab('add');
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    addToast({ type: 'info', message: 'Logged out successfully' });
    navigate('/admin/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Header */}
      <div className="bg-gradient-to-r from-gray-800 to-gray-900 text-white py-6 shadow-lg">
        <div className="container mx-auto px-4 flex justify-between items-center">
          <div className="flex items-center gap-4">
            <Logo size="medium" />
            <h1 className="text-3xl font-bold">Admin Dashboard</h1>
          </div>
          <button
            onClick={handleLogout}
            className="bg-red-600 hover:bg-red-700 px-4 py-2 rounded-lg transition-colors"
          >
            Logout
          </button>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Tabs */}
        <div className="bg-white rounded-lg shadow-md mb-6">
          <div className="flex border-b">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'dashboard'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              📊 Dashboard
            </button>
            <button
              onClick={() => setActiveTab('manage')}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'manage'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              👥 Manage Records
            </button>
            <button
              onClick={() => {
                setActiveTab('add');
                setEditingPerson(null);
                resetForm();
              }}
              className={`flex-1 py-4 px-6 font-semibold transition-colors ${
                activeTab === 'add'
                  ? 'border-b-2 border-blue-600 text-blue-600'
                  : 'text-gray-600 hover:text-gray-800'
              }`}
            >
              ➕ Add New
            </button>
          </div>
        </div>

        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="large" message="Loading..." />
          </div>
        )}

        {/* Dashboard Tab */}
        {!loading && activeTab === 'dashboard' && stats && (
          <div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-gray-600 text-sm font-semibold mb-2">Total Records</h3>
                <p className="text-3xl font-bold text-blue-600">{stats.total_records}</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-gray-600 text-sm font-semibold mb-2">Missing</h3>
                <p className="text-3xl font-bold text-red-600">{stats.missing_count}</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-gray-600 text-sm font-semibold mb-2">Traced</h3>
                <p className="text-3xl font-bold text-green-600">{stats.traced_count}</p>
              </div>
              <div className="bg-white rounded-lg shadow-md p-6">
                <h3 className="text-gray-600 text-sm font-semibold mb-2">Searches Today</h3>
                <p className="text-3xl font-bold text-purple-600">{stats.searches_today}</p>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-2xl font-bold">Recent Uploads</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => handleExport('csv')}
                    className="bg-green-600 text-white px-4 py-2 rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Export CSV
                  </button>
                  <button
                    onClick={() => handleExport('excel')}
                    className="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 transition-colors"
                  >
                    Export Excel
                  </button>
                </div>
              </div>
              <div className="space-y-4">
                {stats.recent_uploads.map((upload: any) => (
                  <div key={upload.person_id} className="border-b pb-4">
                    <h3 className="font-semibold">{upload.name}</h3>
                    <p className="text-sm text-gray-600">
                      Uploaded by {upload.uploaded_by || 'Unknown'} on{' '}
                      {new Date(upload.uploaded_at).toLocaleString()}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Manage Tab */}
        {!loading && activeTab === 'manage' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-6">All Records ({persons.length})</h2>
            <div className="space-y-4">
              {persons.map((person) => (
                <div key={person.person_id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex justify-between items-start gap-4">
                    {/* Photo thumbnail */}
                    {person.photo_urls && person.photo_urls.length > 0 && (
                      <div 
                        className="flex-shrink-0 cursor-pointer"
                        onClick={() => {
                          setViewingPerson(person);
                          setCurrentImageIndex(0);
                          setShowImageModal(true);
                        }}
                      >
                        <img
                          src={person.photo_urls[0]}
                          alt={person.name}
                          className="w-24 h-24 object-cover rounded-lg border-2 border-gray-200 hover:border-blue-500 transition-colors"
                        />
                        {person.photo_urls.length > 1 && (
                          <p className="text-xs text-center text-gray-500 mt-1">
                            +{person.photo_urls.length - 1} more
                          </p>
                        )}
                      </div>
                    )}
                    
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="text-xl font-bold">{person.name}</h3>
                        <span className={person.status === 'missing' ? 'status-missing' : 'status-traced'}>
                          {person.status}
                        </span>
                      </div>
                      {person.age && <p className="text-gray-600">Age: {person.age}</p>}
                      {person.gender && <p className="text-gray-600">Gender: {person.gender}</p>}
                      {person.last_seen_location && (
                        <p className="text-gray-600">Last seen: {person.last_seen_location}</p>
                      )}
                      <p className="text-gray-600">
                        Reported: {new Date(person.date_reported).toLocaleDateString()}
                      </p>
                      <p className="text-gray-600">Contact: {person.contact_info}</p>
                      {person.photo_urls && person.photo_urls.length > 0 && (
                        <button
                          onClick={() => {
                            setViewingPerson(person);
                            setCurrentImageIndex(0);
                            setShowImageModal(true);
                          }}
                          className="text-blue-600 hover:text-blue-800 text-sm mt-2"
                        >
                          View {person.photo_urls.length} photo{person.photo_urls.length > 1 ? 's' : ''}
                        </button>
                      )}
                    </div>
                    <div className="flex flex-col gap-2">
                      <button
                        onClick={() => startEdit(person)}
                        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition-colors"
                      >
                        Edit
                      </button>
                      <button
                        onClick={() => {
                          setStatusPerson(person);
                          setShowStatusModal(true);
                        }}
                        className="bg-yellow-600 text-white px-4 py-2 rounded hover:bg-yellow-700 transition-colors"
                      >
                        Status
                      </button>
                      <button
                        onClick={() => handleDelete(person.person_id)}
                        className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700 transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Add/Edit Tab */}
        {!loading && activeTab === 'add' && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-6">
              {editingPerson ? 'Edit Person' : 'Add New Missing Person'}
            </h2>
            <form onSubmit={editingPerson ? handleUpdate : handleUpload} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Input
                  label="Name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  error={formErrors.name}
                  required
                />
                <Input
                  label="Age"
                  type="number"
                  value={formData.age}
                  onChange={(e) => setFormData({ ...formData, age: e.target.value })}
                />
                <Select
                  label="Gender"
                  value={formData.gender}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  options={[
                    { value: '', label: 'Select gender' },
                    { value: 'male', label: 'Male' },
                    { value: 'female', label: 'Female' },
                    { value: 'other', label: 'Other' }
                  ]}
                />
                <Input
                  label="Date Reported"
                  type="date"
                  value={formData.date_reported}
                  onChange={(e) => setFormData({ ...formData, date_reported: e.target.value })}
                  error={formErrors.date_reported}
                  required
                />
                <Input
                  label="Contact Info"
                  value={formData.contact_info}
                  onChange={(e) => setFormData({ ...formData, contact_info: e.target.value })}
                  error={formErrors.contact_info}
                  required
                />
                <Input
                  label="Last Seen Location"
                  value={formData.last_seen_location}
                  onChange={(e) => setFormData({ ...formData, last_seen_location: e.target.value })}
                />
              </div>
              
              <TextArea
                label="Description"
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                rows={4}
              />

              {!editingPerson && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Photos <span className="text-red-500">*</span>
                  </label>
                  <ImageUpload
                    onImageSelect={setPhotos}
                    multiple={true}
                    preview={true}
                  />
                  {formErrors.photos && (
                    <p className="mt-2 text-sm text-red-600">{formErrors.photos}</p>
                  )}
                </div>
              )}

              <div className="flex gap-4">
                <button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Saving...' : editingPerson ? 'Update Person' : 'Add Person'}
                </button>
                {editingPerson && (
                  <button
                    type="button"
                    onClick={() => {
                      setEditingPerson(null);
                      resetForm();
                    }}
                    className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                  >
                    Cancel
                  </button>
                )}
              </div>
            </form>
          </div>
        )}
      </div>

      {/* Image Viewer Modal */}
      {showImageModal && viewingPerson && viewingPerson.photo_urls && (
        <div
          className="fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50 p-4"
          onClick={() => setShowImageModal(false)}
        >
          <div
            className="relative max-w-4xl w-full"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Close button */}
            <button
              onClick={() => setShowImageModal(false)}
              className="absolute top-4 right-4 bg-white text-gray-800 rounded-full w-10 h-10 flex items-center justify-center hover:bg-gray-200 transition-colors z-10"
            >
              ✕
            </button>

            {/* Person info */}
            <div className="bg-white rounded-t-lg p-4">
              <h2 className="text-2xl font-bold">{viewingPerson.name}</h2>
              <p className="text-gray-600">
                {viewingPerson.age && `Age: ${viewingPerson.age} • `}
                {viewingPerson.gender && `${viewingPerson.gender} • `}
                Status: {viewingPerson.status}
              </p>
            </div>

            {/* Image display */}
            <div className="bg-white p-4">
              <img
                src={viewingPerson.photo_urls[currentImageIndex]}
                alt={`${viewingPerson.name} - Photo ${currentImageIndex + 1}`}
                className="w-full h-auto max-h-[60vh] object-contain rounded-lg"
              />
            </div>

            {/* Navigation */}
            {viewingPerson.photo_urls.length > 1 && (
              <div className="bg-white rounded-b-lg p-4">
                <div className="flex items-center justify-between">
                  <button
                    onClick={() => setCurrentImageIndex(Math.max(0, currentImageIndex - 1))}
                    disabled={currentImageIndex === 0}
                    className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    ← Previous
                  </button>
                  <span className="text-gray-600">
                    {currentImageIndex + 1} / {viewingPerson.photo_urls.length}
                  </span>
                  <button
                    onClick={() => setCurrentImageIndex(Math.min(viewingPerson.photo_urls.length - 1, currentImageIndex + 1))}
                    disabled={currentImageIndex === viewingPerson.photo_urls.length - 1}
                    className="bg-gray-200 text-gray-800 px-4 py-2 rounded hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    Next →
                  </button>
                </div>
                
                {/* Thumbnail strip */}
                <div className="flex gap-2 mt-4 overflow-x-auto">
                  {viewingPerson.photo_urls.map((url, idx) => (
                    <img
                      key={idx}
                      src={url}
                      alt={`Thumbnail ${idx + 1}`}
                      onClick={() => setCurrentImageIndex(idx)}
                      className={`w-16 h-16 object-cover rounded cursor-pointer border-2 transition-all ${
                        idx === currentImageIndex ? 'border-blue-600 scale-110' : 'border-gray-300 hover:border-blue-400'
                      }`}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Status Update Modal */}
      {showStatusModal && statusPerson && (
        <div
          className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowStatusModal(false)}
        >
          <div
            className="bg-white rounded-lg p-6 max-w-md w-full"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 className="text-2xl font-bold mb-4">Update Status: {statusPerson.name}</h2>
            <div className="space-y-4">
              <button
                onClick={() => handleStatusUpdate('missing')}
                className="w-full bg-red-600 text-white py-3 rounded-lg hover:bg-red-700 transition-colors"
              >
                Mark as Missing
              </button>
              <button
                onClick={() => {
                  const tracedDate = new Date().toISOString();
                  const tracedNotes = prompt('Enter notes (optional):');
                  handleStatusUpdate('traced', tracedDate, tracedNotes || undefined);
                }}
                className="w-full bg-green-600 text-white py-3 rounded-lg hover:bg-green-700 transition-colors"
              >
                Mark as Traced/Found
              </button>
              <button
                onClick={() => setShowStatusModal(false)}
                className="w-full bg-gray-200 text-gray-700 py-3 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      <Footer />
    </div>
  );
};

export default AdminPanel;
