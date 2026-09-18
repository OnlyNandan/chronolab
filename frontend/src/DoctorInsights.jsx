import React, { useState, useEffect } from 'react';

function DoctorInsights({ patientId }) {
  const [insights, setInsights] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchInsights = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/insights/${patientId}`, {
          headers: {
            'X-User-Role': 'doctor',
            'X-User-Id': 'DOC-001'
          }
        });
        const data = await res.json();
        setInsights(data.insights);
      } catch (err) {
        console.error("Failed to fetch insights", err);
        setInsights("Failed to load insights from Doctor Mode AI.");
      } finally {
        setLoading(false);
      }
    };

    fetchInsights();
  }, [patientId]);

  return (
    <div className="insights-container">
      <h3>Doctor Mode AI Insights</h3>
      {loading ? (
        <div className="insights-loading">
          <div className="nlp-spinner"></div>
          <span>Analyzing mathematical trends...</span>
        </div>
      ) : (
        <div className="insights-content">
          <p>{insights}</p>
        </div>
      )}
    </div>
  );
}

export default DoctorInsights;
