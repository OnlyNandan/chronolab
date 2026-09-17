import React from 'react';
import { 
  ComposedChart, 
  Line, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { AlertCircle } from 'lucide-react';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="tooltip-custom">
        <span className="tooltip-label">{label}</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <span className="tooltip-value">{data.standardized_value} {data.standardized_unit}</span>
          {data.confidence < 0.7 && (
            <span className="badge badge-warning" style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <AlertCircle size={12} /> Needs Review
            </span>
          )}
        </div>
        <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)' }}>
          Reference: {data.reference_range?.low ?? '0'} - {data.reference_range?.high ?? 'N/A'} {data.standardized_unit}
        </div>
        {data.confidence < 0.7 && (
          <div style={{ fontSize: '0.75rem', color: 'var(--warning)', marginTop: '0.5rem' }}>
            Low confidence extraction ({Math.round(data.confidence * 100)}%)
          </div>
        )}
      </div>
    );
  }
  return null;
};

const Timeline = ({ data, medications = [], title = "Lab Results Timeline" }) => {
  // Sort data chronologically
  const sortedData = [...data].sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  
  // Create an area bounds for the reference range
  const chartData = sortedData.map(d => ({
    ...d,
    ref_low: d.reference_range?.low || 0,
    ref_high: typeof d.reference_range?.high === 'number' ? d.reference_range.high : (d.reference_range?.low ? d.reference_range.low * 2 : 100),
    isLowConfidence: d.confidence < 0.7
  }));

  const CustomDot = (props) => {
    const { cx, cy, payload } = props;
    if (payload.isLowConfidence) {
      return (
        <svg x={cx - 6} y={cy - 6} width={12} height={12} fill="var(--warning)" viewBox="0 0 24 24">
          <circle cx="12" cy="12" r="10" stroke="var(--bg-dark)" strokeWidth="2" />
        </svg>
      );
    }
    return (
      <circle cx={cx} cy={cy} r={5} fill="var(--accent-primary)" stroke="var(--bg-dark)" strokeWidth={2} />
    );
  };

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 600, margin: 0 }}>{title}</h2>
        {chartData.some(d => d.isLowConfidence) && (
          <div className="badge badge-warning" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <AlertCircle size={14} /> Contains unverified data
          </div>
        )}
      </div>
      
      <div className="chart-container">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis 
              dataKey="date" 
              axisLine={false}
              tickLine={false}
              tickMargin={15}
            />
            <YAxis 
              axisLine={false}
              tickLine={false}
              tickMargin={15}
            />
            <Tooltip content={<CustomTooltip />} />
            
            <Area 
              type="monotone" 
              dataKey="ref_high" 
              stroke="none" 
              fill="rgba(255, 255, 255, 0.03)" 
              activeDot={false}
            />
            <Area 
              type="monotone" 
              dataKey="ref_low" 
              stroke="none" 
              fill="var(--bg-dark)" 
              activeDot={false}
            />

            {medications.map((med, idx) => (
              <ReferenceLine 
                key={idx}
                x={med.start_date} 
                stroke="var(--accent-secondary)" 
                strokeDasharray="4 4"
                label={{ position: 'insideTopLeft', value: `Start: ${med.drug_name}`, fill: 'var(--accent-secondary)', fontSize: 12 }} 
              />
            ))}

            <Line 
              type="monotone" 
              dataKey="standardized_value" 
              stroke="var(--accent-primary)" 
              strokeWidth={3}
              dot={<CustomDot />}
              activeDot={{ r: 8, strokeWidth: 0 }}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default Timeline;
