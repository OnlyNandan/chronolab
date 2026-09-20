// Patients can view records only for their own patient_id. This is the whole point:
// a string comparison in a header cannot express this — a real Cedar engine can.
// Loaded into Amazon Verified Permissions by scripts/bootstrap.sh.
permit (
    principal,
    action == ChronoLab::Action::"ViewRecords",
    resource
)
when { principal.patient_id == resource.patient_id };
