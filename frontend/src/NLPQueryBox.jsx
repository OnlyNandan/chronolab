import React, { useState } from 'react';

function NLPQueryBox({ patientId, onMedicationAdded }) {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await fetch('http://localhost:8000/api/medications/nlp', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-User-Role': 'doctor', // Satisfy Cedar Auth
          'X-User-Id': 'DOC-001'
        },
        body: JSON.stringify({ query, patient_id: patientId })
      });

      const data = await response.json();
      
      if (data.status === 'success') {
        setQuery('');
        if (onMedicationAdded) onMedicationAdded(data.medication);
      } else {
        setError(data.message || 'Failed to process natural language input.');
      }
    } catch (err) {
      setError('Connection error. Is the backend running?');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="nlp-container">
      <h3>AI Medication Entry</h3>
      <p className="nlp-subtitle">Describe medication changes in plain English. The Strands NLP agent will parse it automatically.</p>
      
      <form onSubmit={handleSubmit} className="nlp-form">
        <input 
          type="text" 
          className="nlp-input"
          placeholder="e.g. Started 500mg Metformin on 2024-05-12"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          disabled={isLoading}
        />
        <button type="submit" className="nlp-button" disabled={isLoading}>
          {isLoading ? <div className="nlp-spinner"></div> : 'Extract & Add'}
        </button>
      </form>
      
      {error && <div className="nlp-error">{error}</div>}
    </div>
  );
}

export default NLPQueryBox;
