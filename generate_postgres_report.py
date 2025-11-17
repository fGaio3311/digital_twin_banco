from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import json
from datetime import datetime

def format_number(num):
    if isinstance(num, float):
        return f"{num:.2f}"
    return str(num)

pdf_file = "postgres_test_report.pdf"
doc = SimpleDocTemplate(pdf_file, pagesize=letter)
styles = getSampleStyleSheet()

# Title style
title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=16, spaceAfter=20)

elements = []

# Title
title = Paragraph("PostgreSQL Load Test Results Report", title_style)
elements.append(title)
elements.append(Spacer(1, 12))

# Description
description_text = """This report presents the performance metrics of our digital twin application using PostgreSQL as the database backend.
The test executed 100 sequential requests to /ping from inside the API container to measure baseline latency and connectivity."""

elements.append(Paragraph(description_text, styles['Normal']))
elements.append(Spacer(1, 12))

# Load data
with open('postgres_test_results.json', 'r') as f:
    data = json.load(f)

# General metrics
general_data = [
    ['Metric', 'Value'],
    ['Test Duration (s)', format_number(data.get('test_duration_seconds', 0))],
    ['Total Requests', format_number(data.get('total_requests', 0))],
    ['Requests per Second', format_number(data.get('requests_per_second', 0))],
    ['Success Rate (%)', format_number(data.get('success_rate_percent', 0))],
]

general_table = Table(general_data, colWidths=[250, 200])
general_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 1, colors.black)
]))

elements.append(Spacer(1,12))
elements.append(Paragraph('General Metrics', styles['Heading2']))
elements.append(Spacer(1,8))
elements.append(general_table)
elements.append(Spacer(1,12))

# Response times
rt = data.get('response_times', {})
response_times_data = [
    ['Metric', 'Value (ms)'],
    ['Average', format_number(rt.get('average_ms', 0))],
    ['Median', format_number(rt.get('median_ms', 0))],
    ['Min', format_number(rt.get('min_ms', 0))],
    ['Max', format_number(rt.get('max_ms', 0))],
    ['Std Dev', format_number(rt.get('stdev_ms', 0))],
]

response_table = Table(response_times_data, colWidths=[250, 200])
response_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 1, colors.black)
]))

elements.append(Paragraph('Response Time Metrics', styles['Heading2']))
elements.append(Spacer(1,8))
elements.append(response_table)
elements.append(Spacer(1,12))

# Endpoint details
endpoint_data = [['Endpoint', 'Total Requests', 'Success Rate (%)', 'Avg (ms)', 'Failures']]
for endpoint, details in data.get('endpoint_details', {}).items():
    endpoint_data.append([
        endpoint,
        format_number(details.get('total_requests', 0)),
        format_number(details.get('success_rate', 0)),
        format_number(details.get('average_response_ms', 0)),
        format_number(details.get('failures', 0)),
    ])

endpoint_table = Table(endpoint_data, colWidths=[120, 100, 100, 100, 80])
endpoint_table.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.grey),
    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('GRID', (0,0), (-1,-1), 1, colors.black)
]))

elements.append(Paragraph('Endpoint Details', styles['Heading2']))
elements.append(Spacer(1,8))
elements.append(endpoint_table)

# Build PDF
doc.build(elements)
print('Postgres report written to', pdf_file)
