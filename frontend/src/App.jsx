import React, { useState, useEffect } from 'react';
import Timeline from './Timeline';
import './App.css';

// Task 3: Hardcoded mock array
const MOCK_LAB_DATA = [
  {
    patient_id: "PT-1001",
    test_name_canonical: "HbA1c",
    date: "2023-01-15",
    standardized_value: 8.2,
    standardized_unit: "%",
    reference_range: { low: 4.0, high: 5.6 },
    confidence: 0.95
  },
  {
    patient_id: "PT-1001",
    test_name_canonical: "HbA1c",
    date: "2023-06-20",
    standardized_value: 7.5,
    standardized_unit: "%",
    reference_range: { low: 4.0, high: 5.6 },
    confidence: 0.85
  },
  {
    patient_id: "PT-1001",
    test_name_canonical: "HbA1c",
    date: "2024-01-10",
    standardized_value: 6.8,
    standardized_unit: "%",
    reference_range: { low: 4.0, high: 5.6 },
    confidence: 0.6  // Low confidence example
  }
];

const MOCK_MEDICATIONS = [
  {
    drug_name: "Metformin",
    start_date: "2023-02-01",
    end_date: null
  }
];

function App() {
  const [data, setData] = useState(MOCK_LAB_DATA);
  const [meds, setMeds] = useState(MOCK_MEDICATIONS);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Task 4: Fetch from FastAPI server
    fetch('http://localhost:8000/api/records/PT-1001')
      .then(res => res.json())
      .then(fetchedData => {
        if (fetchedData && fetchedData.length > 0) {
          setData(fetchedData);
        }
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch from backend, using mocks", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="dashboard-container">
      <div className="header">
        <h1>ChronoLab</h1>
        <p>Unified Timeline for Patient Lab Reports</p>
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
    </div>
  );
}

export default App;
