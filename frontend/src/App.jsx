import React, { useState, useEffect } from 'react';
import Timeline from './Timeline';
import NLPQueryBox from './NLPQueryBox';
import DoctorInsights from './DoctorInsights';
import ChatAssistant from './ChatAssistant';
import './App.css';

function App() {
  const [data, setData] = useState([]);
  const [meds, setMeds] = useState([]);
  const [loading, setLoading] = useState(true);

  // We are viewing PT-1001's record
  const PATIENT_ID = "PT-1001";

  const fetchRecords = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/records/${PATIENT_ID}`, {
        headers: { 'X-User-Role': 'doctor', 'X-User-Id': 'DOC-001' }
      });
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
      const res = await fetch(`http://localhost:8000/api/medications/${PATIENT_ID}`, {
        headers: { 'X-User-Role': 'doctor', 'X-User-Id': 'DOC-001' }
      });
      const fetchedMeds = await res.json();
      if (fetchedMeds && fetchedMeds.length > 0) {
        setMeds(fetchedMeds);
      }
    } catch (err) {
      console.error("Failed to fetch meds", err);
    }
  };

  useEffect(() => {
    Promise.all([fetchRecords(), fetchMedications()]).then(() => {
      setLoading(false);
    });

    // Real-Time Collaboration: Connect to WebSocket
    const ws = new WebSocket(`ws://localhost:8000/ws/timeline/${PATIENT_ID}`);
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
  }, []);

  const handleMedicationAdded = (newMed) => {
    // We can rely on WebSocket for updates, but for immediate UI response, we also add it directly.
    setMeds(prevMeds => {
      if (prevMeds.some(m => m.record_id === newMed.record_id)) return prevMeds;
      return [...prevMeds, newMed];
    });
  };

  const handleExportFHIR = async () => {
    try {
      const res = await fetch(`http://localhost:8000/api/export/fhir/${PATIENT_ID}`, {
        headers: { 'X-User-Role': 'doctor', 'X-User-Id': 'DOC-001' }
      });
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

  return (
    <div className="dashboard-container">
      <div className="header">
        <div>
          <h1>ChronoLab</h1>
          <p>Unified Timeline for Patient Lab Reports</p>
        </div>
        <button className="fhir-button" onClick={handleExportFHIR}>
          Export to FHIR
        </button>
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
