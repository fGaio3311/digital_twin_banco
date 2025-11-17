from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import json
from datetime import datetime

def format_number(num):
    """Format numbers to be more readable"""
    if isinstance(num, float):
        return f"{num:.2f}"
    return str(num)

# Create PDF
pdf_file = "mongodb_test_report.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=letter)
styles = getSampleStyleSheet()

# Create custom style for title
title_style = ParagraphStyle(
    'CustomTitle',
    parent=styles['Heading1'],
    fontSize=16,
    spaceAfter=30
)

# Create content elements
elements = []

# Add title
title = Paragraph("MongoDB Load Test Results Report", title_style)
elements.append(title)
elements.append(Spacer(1, 20))

# Add test description
description_text = """This report presents the performance metrics of our digital twin application using MongoDB as the database backend.
The test was conducted using Locust, simulating 1000 concurrent users with a spawn rate of 10 users per second over a 1-minute period.
The test focused on basic API operations to evaluate system responsiveness under load."""

description = Paragraph(description_text, styles["Normal"])
elements.append(description)
elements.append(Spacer(1, 20))

# Load test data
with open('mongodb_test_results.json', 'r') as f:
    data = json.load(f)

# General metrics table
general_data = [
    ["Metric", "Value"],
    ["Test Duration (seconds)", format_number(data["test_duration_seconds"])],
    ["Total Requests", format_number(data["total_requests"])],
    ["Requests per Second", format_number(data["requests_per_second"])],
    ["Success Rate (%)", format_number(data["success_rate_percent"])],
]

general_table = Table(general_data, colWidths=[200, 200])
general_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
]))

elements.append(Paragraph("General Metrics", styles["Heading2"]))
elements.append(Spacer(1, 10))
elements.append(general_table)
elements.append(Spacer(1, 20))

# Response times table
response_times_data = [
    ["Response Time Metric", "Value (ms)"],
    ["Average", format_number(data["response_times"]["average_ms"])],
    ["95th Percentile", format_number(data["response_times"]["p95_ms"])],
    ["99th Percentile", format_number(data["response_times"]["p99_ms"])],
]

response_table = Table(response_times_data, colWidths=[200, 200])
response_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
]))

elements.append(Paragraph("Response Times", styles["Heading2"]))
elements.append(Spacer(1, 10))
elements.append(response_table)
elements.append(Spacer(1, 20))

# Endpoint details table
endpoint_data = [
    ["Endpoint", "Total Requests", "Success Rate (%)", "Avg Response (ms)", "P95 Response (ms)"],
]

for endpoint, details in data["endpoint_details"].items():
    endpoint_data.append([
        endpoint,
        format_number(details["total_requests"]),
        format_number(details["success_rate"]),
        format_number(details["average_response_ms"]),
        format_number(details["p95_response_ms"]),
    ])

endpoint_table = Table(endpoint_data, colWidths=[100, 80, 80, 100, 100])
endpoint_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 12),
    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 10),
    ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
]))

elements.append(Paragraph("Endpoint Details", styles["Heading2"]))
elements.append(Spacer(1, 10))
elements.append(endpoint_table)

# Generate PDF
doc.build(elements)
