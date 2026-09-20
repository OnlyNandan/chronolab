// Doctors can view records, view insights, add medications, and export FHIR
// for any patient. Loaded into Amazon Verified Permissions by scripts/bootstrap.sh —
// this is the source of truth, never embed policy text in Python.
permit (
    principal,
    action in [
        ChronoLab::Action::"ViewRecords",
        ChronoLab::Action::"ViewInsights",
        ChronoLab::Action::"AddMedication",
        ChronoLab::Action::"ExportFHIR"
    ],
    resource
)
when { principal.role == "doctor" };
