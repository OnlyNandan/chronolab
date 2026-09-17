import os
import random
from datetime import datetime, timedelta
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors

# Ensure data directory exists
os.makedirs(os.path.dirname(os.path.abspath(__file__)), exist_ok=True)

# Fake data pools
PATIENTS = ["PT-1001", "PT-1002", "PT-1003"]
TEST_NAMES = [
    ["HbA1c", "Glycated Hemoglobin", "A1c", "Hemoglobin A1c"],
    ["Glucose, Fasting", "Fasting Blood Sugar", "FBS", "Glucose"],
    ["Total Cholesterol", "Cholesterol, Total", "Chol"],
    ["LDL Cholesterol", "LDL-C", "Low Density Lipoprotein"],
]

UNITS = {
    "HbA1c": ["%", "mmol/mol"],
    "Glucose": ["mg/dL", "mmol/L"],
    "Cholesterol": ["mg/dL", "mmol/L"]
}

def get_random_test_name(category):
    if category == "HbA1c":
        return random.choice(TEST_NAMES[0])
    elif category == "Glucose":
        return random.choice(TEST_NAMES[1])
    elif category == "Cholesterol":
        return random.choice(TEST_NAMES[2])
    elif category == "LDL":
        return random.choice(TEST_NAMES[3])
    return "Unknown Test"

def generate_value(category, unit):
    if category == "HbA1c":
        if unit == "%": return round(random.uniform(5.0, 9.5), 1)
        if unit == "mmol/mol": return round(random.uniform(30.0, 80.0), 1)
    elif category == "Glucose":
        if unit == "mg/dL": return round(random.uniform(70.0, 180.0), 1)
        if unit == "mmol/L": return round(random.uniform(3.9, 10.0), 1)
    elif category == "Cholesterol":
        if unit == "mg/dL": return round(random.uniform(150.0, 250.0), 1)
        if unit == "mmol/L": return round(random.uniform(3.8, 6.5), 1)
    elif category == "LDL":
        if unit == "mg/dL": return round(random.uniform(70.0, 160.0), 1)
        if unit == "mmol/L": return round(random.uniform(1.8, 4.1), 1)
    return 0.0

def generate_clean_layout(c, patient, date):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "MOCK LAB REPORT - CLINIC A")
    
    c.setFont("Helvetica", 12)
    c.drawString(50, 720, f"Patient ID: {patient}")
    c.drawString(50, 700, f"Date: {date}")
    
    c.setStrokeColor(colors.black)
    c.line(50, 680, 550, 680)
    
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 650, "Test Name")
    c.drawString(250, 650, "Result")
    c.drawString(350, 650, "Units")
    c.drawString(450, 650, "Ref Range")
    
    y = 620
    c.setFont("Helvetica", 12)
    
    # Generate 3 tests
    for cat in ["HbA1c", "Glucose", "Cholesterol"]:
        name = get_random_test_name(cat)
        unit = random.choice(UNITS[cat.split(",")[0]] if "," not in cat else UNITS[cat])
        value = generate_value(cat, unit)
        
        c.drawString(50, y, name)
        c.drawString(250, y, str(value))
        c.drawString(350, y, unit)
        
        # Fake ref range based on unit
        if cat == "HbA1c":
            if unit == "%": c.drawString(450, y, "4.0 - 5.6")
            else: c.drawString(450, y, "20 - 38")
        elif cat == "Glucose":
            if unit == "mg/dL": c.drawString(450, y, "70 - 99")
            else: c.drawString(450, y, "3.9 - 5.5")
        elif cat == "Cholesterol":
            if unit == "mg/dL": c.drawString(450, y, "< 200")
            else: c.drawString(450, y, "< 5.2")
        
        y -= 30

def generate_messy_layout(c, patient, date):
    # Simulate a slightly misaligned, OCR-like or printed-then-scanned feel
    # We will use Courier and random slight offsets
    c.setFont("Courier", 14)
    c.drawString(50 + random.randint(-2, 2), 750 + random.randint(-2, 2), "--- PATHOLOGY RESULT ---")
    
    c.setFont("Courier", 10)
    c.drawString(60 + random.randint(-2, 2), 720, f"PT: {patient}")
    c.drawString(200 + random.randint(-2, 2), 720, f"Collected: {date}")
    
    y = 650
    for cat in ["HbA1c", "LDL", "Glucose"]:
        name = get_random_test_name(cat)
        unit = random.choice(UNITS[cat] if cat in UNITS else UNITS["Cholesterol"])
        value = generate_value(cat, unit)
        
        # Print with random noise and different formats
        c.drawString(50 + random.randint(-5, 5), y, f"*{name}*")
        c.drawString(250 + random.randint(-5, 5), y, f"VAL:{value} {unit}")
        
        # Fake ref range based on unit
        if cat == "HbA1c":
            if unit == "%": c.drawString(400, y, "(Ref: 4.0-5.6)")
            else: c.drawString(400, y, "(Ref: 20-38)")
        elif cat == "LDL":
            if unit == "mg/dL": c.drawString(400, y, "(Ref: < 100)")
            else: c.drawString(400, y, "(Ref: < 2.6)")
        elif cat == "Glucose":
            if unit == "mg/dL": c.drawString(400, y, "(Ref: 70-99)")
            else: c.drawString(400, y, "(Ref: 3.9-5.5)")
        
        y -= 40 + random.randint(-5, 15)

def main():
    print("Generating synthetic lab reports...")
    for i in range(1, 9):
        patient = random.choice(PATIENTS)
        date = (datetime.now() - timedelta(days=random.randint(1, 1000))).strftime("%Y-%m-%d")
        
        filename = f"report_{i}_{patient}_{date}.pdf"
        filepath = os.path.join(os.path.dirname(__file__), filename)
        
        c = canvas.Canvas(filepath, pagesize=letter)
        
        if random.choice([True, False]):
            generate_clean_layout(c, patient, date)
        else:
            generate_messy_layout(c, patient, date)
            
        c.save()
        print(f"Generated {filepath}")

if __name__ == "__main__":
    main()
