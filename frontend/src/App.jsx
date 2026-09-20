import React, { useState, useEffect } from 'react';
import Timeline from './Timeline';
import NLPQueryBox from './NLPQueryBox';
import DoctorInsights from './DoctorInsights';
import ChatAssistant from './ChatAssistant';
import Login from './Login';
import { getSession, logout, authFetch, authWsUrl } from './auth';
import './App.css';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';

function App() {
  const [session, setSession] = useState(getSession());
  const [data, setData] = useState([]);
  const [meds, setMeds] = useState([]);
  const [loading, setLoading] = useState(true);

  // Doctors view a demo patient; patients only ever see their own timeline
  // (the backend enforces this via AVP regardless of what's requested here).
  const PATIENT_ID = session?.role === 'patient' ? session.patientId : 'PT-1001';

  const fetchRecords = async () => {
    try {
      const res = await authFetch(`${API_BASE_URL}/api/records/${PATIENT_ID}`);
      const fetchedData = await res.json();
      if (fetchedData && fetchedData.length > 0) {
        setData(fetchedData);
      }
    } catch (err) {
      console.error("Failed to fetch records", err);
    }
  };

  const fetchMedications = async () => {
    try {
      const res = await authFetch(`${API_BASE_URL}/api/medications/${PATIENT_ID}`);
      const fetchedMeds = await res.json();
      if (fetchedMeds && fetchedMeds.length > 0) {
        setMeds(fetchedMeds);
      }
    } catch (err) {
      console.error("Failed to fetch meds", err);
    }
  };

  useEffect(() => {
    if (!session) return;

    Promise.all([fetchRecords(), fetchMedications()]).then(() => {
      setLoading(false);
    });

    // Real-Time Collaboration: Connect to WebSocket
    const ws = new WebSocket(authWsUrl(`${WS_BASE_URL}/ws/timeline/${PATIENT_ID}`));
    ws.onmessage = (event) => {
      const message = JSON.parse(event.data);
      if (message.type === 'NEW_MEDICATION') {
        // Prevent duplicates if the user adding it already got it from the POST response
        setMeds(prevMeds => {
          if (prevMeds.some(m => m.record_id === message.data.record_id)) return prevMeds;
          return [...prevMeds, message.data];
        });
      }
    };

    return () => ws.close();
  }, [session]);

  const handleMedicationAdded = (newMed) => {
    // We can rely on WebSocket for updates, but for immediate UI response, we also add it directly.
    setMeds(prevMeds => {
      if (prevMeds.some(m => m.record_id === newMed.record_id)) return prevMeds;
      return [...prevMeds, newMed];
    });
  };

  const handleExportFHIR = async () => {
    try {
      const res = await authFetch(`${API_BASE_URL}/api/export/fhir/${PATIENT_ID}`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `patient_${PATIENT_ID}_fhir_bundle.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Failed to export FHIR", err);
    }
  };

  if (!session) {
    return <Login onLoggedIn={setSession} />;
  }

  const handleLogout = () => {
    logout();
    setSession(null);
  };

  return (
    <div className="dashboard-container">
      <div className="header">
        <div>
          <h1>ChronoLab</h1>
          <p>Unified Timeline for Patient Lab Reports</p>
        </div>
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <button className="fhir-button" onClick={handleExportFHIR}>
            Export to FHIR
          </button>
          <button className="fhir-button" onClick={handleLogout}>
            Log out ({session.role})
          </button>
        </div>
      </div>
      
      <div className="top-widgets">
        <NLPQueryBox patientId={PATIENT_ID} onMedicationAdded={handleMedicationAdded} />
        <DoctorInsights patientId={PATIENT_ID} />
      </div>
      
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-muted)' }}>
          Loading timeline data...
        </div>
      ) : (
        <Timeline 
          data={data.filter(d => d.test_name_canonical === 'HbA1c')} 
          medications={meds} 
          title="HbA1c Over Time" 
        />
      )}
      
      {!loading && data.some(d => d.test_name_canonical === 'Total Cholesterol') && (
        <Timeline 
          data={data.filter(d => d.test_name_canonical === 'Total Cholesterol')} 
          medications={[]} 
          title="Total Cholesterol" 
        />
      )}

      {/* Floating Chat Assistant */}
      <ChatAssistant patientId={PATIENT_ID} />
    </div>
  );
}

export default App;
