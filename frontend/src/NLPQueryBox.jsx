import React, { useState, useEffect } from 'react';
import { authFetch } from './auth';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function NLPQueryBox({ patientId, onMedicationAdded }) {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);
  
  // Setup Speech Recognition
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  const recognition = SpeechRecognition ? new SpeechRecognition() : null;
  
  if (recognition) {
    recognition.continuous = false;
    recognition.interimResults = false;
    recognition.lang = 'en-US';
    
    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      setQuery(transcript);
      setIsListening(false);
    };
    
    recognition.onerror = (event) => {
      console.error("Speech recognition error", event.error);
      setIsListening(false);
    };
    
    recognition.onend = () => {
      setIsListening(false);
    };
  }

  const handleMicClick = (e) => {
    e.preventDefault();
    if (!recognition) {
      setError("Speech recognition is not supported in this browser.");
      return;
    }
    
    if (isListening) {
      recognition.stop();
      setIsListening(false);
    } else {
      recognition.start();
      setIsListening(true);
      setError('');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setIsLoading(true);
    setError('');

    try {
      const response = await authFetch(`${API_BASE_URL}/api/medications/nlp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
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
        <button 
          className={`mic-button ${isListening ? 'listening' : ''}`}
          onClick={handleMicClick}
          type="button"
          title="Click to speak"
        >
          {isListening ? '🎙️...' : '🎤'}
        </button>
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
