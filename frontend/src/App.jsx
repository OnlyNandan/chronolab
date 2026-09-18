import React, { useState, useEffect } from 'react';
import Timeline from './Timeline';
import NLPQueryBox from './NLPQueryBox';
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
  }, []);

  const handleMedicationAdded = (newMed) => {
    setMeds([...meds, newMed]);
  };

  return (
    <div className="dashboard-container">
      <div className="header">
        <h1>ChronoLab</h1>
        <p>Unified Timeline for Patient Lab Reports</p>
      </div>
      
      <NLPQueryBox patientId={PATIENT_ID} onMedicationAdded={handleMedicationAdded} />
      
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
    </div>
  );
}

export default App;
