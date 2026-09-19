#!/bin/bash
echo "Testing /api/records/PT-1001"
curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-Role: doctor" -H "X-User-Id: DOC-001" http://localhost:8000/api/records/PT-1001

echo "Testing /api/medications/PT-1001"
curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-Role: doctor" -H "X-User-Id: DOC-001" http://localhost:8000/api/medications/PT-1001

echo "Testing /api/medications/nlp"
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -H "X-User-Role: doctor" -H "X-User-Id: DOC-001" -d '{"patient_id": "PT-1001", "query": "Started taking Aspirin 81mg today"}' http://localhost:8000/api/medications/nlp

echo "Testing /api/insights/PT-1001"
curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-Role: doctor" -H "X-User-Id: DOC-001" http://localhost:8000/api/insights/PT-1001

echo "Testing /api/export/fhir/PT-1001"
curl -s -o /dev/null -w "%{http_code}\n" -H "X-User-Role: doctor" -H "X-User-Id: DOC-001" http://localhost:8000/api/export/fhir/PT-1001

echo "Testing /api/chat"
curl -s -o /dev/null -w "%{http_code}\n" -X POST -H "Content-Type: application/json" -H "X-User-Role: doctor" -H "X-User-Id: DOC-001" -d '{"patient_id": "PT-1001", "question": "What is the highest Total Cholesterol recorded?"}' http://localhost:8000/api/chat
