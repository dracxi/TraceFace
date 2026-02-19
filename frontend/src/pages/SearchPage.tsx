import React, { useState } from 'react';
import { searchFace, textSearch } from '../api';
import { useToast } from '../contexts/ToastContext';
import ImageUpload from '../components/ImageUpload';
import LoadingSpinner from '../components/LoadingSpinner';
import Input from '../components/Input';
import Select from '../components/Select';

interface Match {
  person_id: string;
  name: string;
  age?: number;
  gender?: string;
  similarity_score?: number;
  photo_url?: string;
  photo_urls?: string[];
  last_seen_location?: string;
  date_reported: string;
  contact_info: string;
  status: string;
}

const SearchPage: React.FC = () => {
  const [searchMode, setSearchMode] = useState<'face' | 'text'>('face');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedPerson, setSelectedPerson] = useState<Match | null>(null);
  
  // Text search filters
  const [nameQuery, setNameQuery] = useState('');
  const [ageMin, setAgeMin] = useState('');
  const [ageMax, setAgeMax] = useState('');
  const [gender, setGender] = useState('');
  const [location, setLocation] = useState('');
  const [status, setStatus] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);

  const { addToast } = useToast();

  const handleImageSelect = (files: File[]) => {
    if (files.length > 0) {
      setSelectedFile(files[0]);
      setMatches([]);
      setSelectedPerson(null);
    }
  };

  const handleFaceSearch = async () => {
    if (!selectedFile) {
      addToast({ type: 'error', message: 'Please select an image first' });
      return;
    }

    setLoading(true);
    try {
      const result = await searchFace(selectedFile);
      
      if (!result.query_face_detected) {
        addToast({ type: 'warning', message: 'No face detected in the image' });
        setMatches([]);
      } else {
        setMatches(result.matches);
        if (result.matches.length === 0) {
          addToast({ type: 'info', message: 'No matches found' });
        } else {
          addToast({ type: 'success', message: `Found ${result.matches.length} match(es)` });
        }
      }
    } catch (err: any) {
      addToast({ type: 'error', message: err.response?.data?.error?.message || 'Search failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleTextSearch = async () => {
    setLoading(true);
    try {
      const params: any = { page, page_size: 20 };
      if (nameQuery) params.q = nameQuery;
      if (ageMin) params.age_min = parseInt(ageMin);
      if (ageMax) params.age_max = parseInt(ageMax);
      if (gender) params.gender = gender;
      if (location) params.location = location;
      if (status) params.status = status;

      const result = await textSearch(params);
      setMatches(result.results);
      setTotal(result.total);
      setTotalPages(result.total_pages);
      
      if (result.results.length === 0) {
        addToast({ type: 'info', message: 'No results found' });
      } else {
        addToast({ type: 'success', message: `Found ${result.total} result(s)` });
      }
    } catch (err: any) {
      addToast({ type: 'error', message: 'Search failed' });
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => {
    setNameQuery('');
    setAgeMin('');
    setAgeMax('');
    setGender('');
    setLocation('');
    setStatus('');
    setPage(1);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-blue-800 text-white py-8 shadow-lg">
        <div className="container mx-auto px-4">
          <h1 className="text-4xl font-bold mb-2">Missing Person Face Recognition</h1>
          <p className="text-blue-100">Help reunite families by searching our database</p>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Search Mode Toggle */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-6">
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => {
                setSearchMode('face');
                setMatches([]);
                setSelectedPerson(null);
              }}
              className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                searchMode === 'face'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              🔍 Face Search
            </button>
            <button
              onClick={() => {
                setSearchMode('text');
                setMatches([]);
                setSelectedPerson(null);
                setSelectedFile(null);
              }}
              className={`flex-1 py-3 px-6 rounded-lg font-semibold transition-colors ${
                searchMode === 'text'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              📝 Text Search
            </button>
          </div>

          {/* Face Search */}
          {searchMode === 'face' && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Upload a Photo</h2>
              <ImageUpload onImageSelect={handleImageSelect} preview={true} />
              <button
                onClick={handleFaceSearch}
                disabled={!selectedFile || loading}
                className="w-full mt-4 bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Searching...' : 'Search by Face'}
              </button>
            </div>
          )}

          {/* Text Search */}
          {searchMode === 'text' && (
            <div>
              <h2 className="text-2xl font-bold mb-4">Search by Details</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                <Input
                  label="Name"
                  placeholder="Enter name or partial name"
                  value={nameQuery}
                  onChange={(e) => setNameQuery(e.target.value)}
                />
                <Input
                  label="Location"
                  placeholder="Last seen location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                />
                <Input
                  label="Min Age"
                  type="number"
                  placeholder="Minimum age"
                  value={ageMin}
                  onChange={(e) => setAgeMin(e.target.value)}
                />
                <Input
                  label="Max Age"
                  type="number"
                  placeholder="Maximum age"
                  value={ageMax}
                  onChange={(e) => setAgeMax(e.target.value)}
                />
                <Select
                  label="Gender"
                  value={gender}
                  onChange={(e) => setGender(e.target.value)}
                  options={[
                    { value: '', label: 'All' },
                    { value: 'male', label: 'Male' },
                    { value: 'female', label: 'Female' },
                    { value: 'other', label: 'Other' }
                  ]}
                />
                <Select
                  label="Status"
                  value={status}
                  onChange={(e) => setStatus(e.target.value)}
                  options={[
                    { value: '', label: 'All' },
                    { value: 'missing', label: 'Missing' },
                    { value: 'traced', label: 'Traced' }
                  ]}
                />
              </div>
              <div className="flex gap-4">
                <button
                  onClick={handleTextSearch}
                  disabled={loading}
                  className="flex-1 bg-blue-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                >
                  {loading ? 'Searching...' : 'Search'}
                </button>
                <button
                  onClick={clearFilters}
                  className="px-6 py-3 bg-gray-200 text-gray-700 rounded-lg font-semibold hover:bg-gray-300 transition-colors"
                >
                  Clear
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Loading */}
        {loading && (
          <div className="flex justify-center py-12">
            <LoadingSpinner size="large" message="Searching..." />
          </div>
        )}

        {/* Results */}
        {!loading && matches.length > 0 && (
          <div className="bg-white rounded-lg shadow-md p-6">
            <h2 className="text-2xl font-bold mb-4">
              {searchMode === 'face' ? `Matches Found (${matches.length})` : `Results (${total})`}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {matches.map((match) => (
                <div
                  key={match.person_id}
                  onClick={() => setSelectedPerson(match)}
                  className="border rounded-lg overflow-hidden hover:shadow-lg transition-shadow cursor-pointer"
                >
                  <img
                    src={match.photo_url || match.photo_urls?.[0] || '/placeholder.jpg'}
                    alt={match.name}
                    className="w-full h-48 object-cover"
                  />
                  <div className="p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="text-lg font-bold">{match.name}</h3>
                      <span className={match.status === 'missing' ? 'status-missing' : 'status-traced'}>
                        {match.status}
                      </span>
                    </div>
                    {match.similarity_score !== undefined && (
                      <p className="text-sm text-green-600 font-semibold mb-2">
                        {(match.similarity_score * 100).toFixed(1)}% Match
                      </p>
                    )}
                    {match.age && <p className="text-sm text-gray-600">Age: {match.age}</p>}
                    {match.gender && <p className="text-sm text-gray-600">Gender: {match.gender}</p>}
                    {match.last_seen_location && (
                      <p className="text-sm text-gray-600">Last seen: {match.last_seen_location}</p>
                    )}
                    <p className="text-sm text-gray-500 mt-2">
                      Reported: {new Date(match.date_reported).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>

            {/* Pagination */}
            {searchMode === 'text' && totalPages > 1 && (
              <div className="flex justify-center gap-2 mt-6">
                <button
                  onClick={() => setPage(Math.max(1, page - 1))}
                  disabled={page === 1}
                  className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                >
                  Previous
                </button>
                <span className="px-4 py-2">
                  Page {page} of {totalPages}
                </span>
                <button
                  onClick={() => setPage(Math.min(totalPages, page + 1))}
                  disabled={page === totalPages}
                  className="px-4 py-2 bg-gray-200 rounded disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            )}
          </div>
        )}

        {/* Detail Modal */}
        {selectedPerson && (
          <div
            className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 animate-fade-in"
            onClick={() => setSelectedPerson(null)}
          >
            <div
              className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <h2 className="text-2xl font-bold">{selectedPerson.name}</h2>
                  <button
                    onClick={() => setSelectedPerson(null)}
                    className="text-gray-500 hover:text-gray-700 text-2xl"
                  >
                    ×
                  </button>
                </div>
                
                {selectedPerson.photo_urls && selectedPerson.photo_urls.length > 0 && (
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    {selectedPerson.photo_urls.map((url, idx) => (
                      <img
                        key={idx}
                        src={url}
                        alt={`${selectedPerson.name} ${idx + 1}`}
                        className="w-full h-48 object-cover rounded"
                      />
                    ))}
                  </div>
                )}

                <div className="space-y-3">
                  <div>
                    <span className="font-semibold">Status:</span>{' '}
                    <span className={selectedPerson.status === 'missing' ? 'status-missing' : 'status-traced'}>
                      {selectedPerson.status}
                    </span>
                  </div>
                  {selectedPerson.age && (
                    <p><span className="font-semibold">Age:</span> {selectedPerson.age}</p>
                  )}
                  {selectedPerson.gender && (
                    <p><span className="font-semibold">Gender:</span> {selectedPerson.gender}</p>
                  )}
                  {selectedPerson.last_seen_location && (
                    <p><span className="font-semibold">Last Seen:</span> {selectedPerson.last_seen_location}</p>
                  )}
                  <p>
                    <span className="font-semibold">Date Reported:</span>{' '}
                    {new Date(selectedPerson.date_reported).toLocaleDateString()}
                  </p>
                  <p><span className="font-semibold">Contact:</span> {selectedPerson.contact_info}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SearchPage;
