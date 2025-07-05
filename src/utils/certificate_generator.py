"""
ISO 42001 Compliance Certificate Generator
Generates professional PDF certificates for successful compliance assessments
"""

import os
import io
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import inch, mm
from reportlab.lib.colors import Color, HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.pdfgen import canvas
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics import renderPDF
import qrcode
from PIL import Image as PILImage
import base64

class CertificateGenerator:
    """Professional ISO 42001 compliance certificate generator"""
    
    def __init__(self):
        self.page_width, self.page_height = landscape(A4)
        self.margin = 50
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        
        # Colors
        self.primary_color = HexColor('#2563eb')  # Blue
        self.secondary_color = HexColor('#1e40af')  # Darker blue
        self.accent_color = HexColor('#f59e0b')  # Gold
        self.text_color = HexColor('#1f2937')  # Dark gray
        self.light_gray = HexColor('#f3f4f6')
        
        # Fonts and styles
        self.setup_styles()
    
    def setup_styles(self):
        """Setup custom paragraph styles"""
        self.styles = getSampleStyleSheet()
        
        # Certificate title style
        self.title_style = ParagraphStyle(
            'CertificateTitle',
            parent=self.styles['Heading1'],
            fontSize=36,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica-Bold'
        )
        
        # Subtitle style
        self.subtitle_style = ParagraphStyle(
            'CertificateSubtitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            spaceAfter=30,
            fontName='Helvetica'
        )
        
        # Organization name style
        self.org_style = ParagraphStyle(
            'OrganizationName',
            parent=self.styles['Heading1'],
            fontSize=28,
            textColor=self.text_color,
            alignment=TA_CENTER,
            spaceAfter=10,
            fontName='Helvetica-Bold'
        )
        
        # Body text style
        self.body_style = ParagraphStyle(
            'CertificateBody',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=self.text_color,
            alignment=TA_CENTER,
            spaceAfter=20,
            fontName='Helvetica'
        )
        
        # Details style
        self.details_style = ParagraphStyle(
            'CertificateDetails',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.text_color,
            alignment=TA_LEFT,
            fontName='Helvetica'
        )
        
        # Signature style
        self.signature_style = ParagraphStyle(
            'SignatureStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.text_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    
    def generate_certificate(self, assessment_data: Dict[str, Any], output_path: str) -> str:
        """
        Generate a professional ISO 42001 compliance certificate
        
        Args:
            assessment_data: Dictionary containing assessment and organization data
            output_path: Path where the certificate PDF will be saved
            
        Returns:
            Path to the generated certificate file
        """
        
        # Create the PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=landscape(A4),
            rightMargin=self.margin,
            leftMargin=self.margin,
            topMargin=self.margin,
            bottomMargin=self.margin
        )
        
        # Build the certificate content
        story = []
        
        # Add header with logo and decorative elements
        story.extend(self._create_header())
        
        # Add certificate title
        story.append(Paragraph("CERTIFICATE OF COMPLIANCE", self.title_style))
        story.append(Paragraph("ISO 42001:2023 - Artificial Intelligence Management Systems", self.subtitle_style))
        
        # Add decorative line
        story.append(Spacer(1, 20))
        story.extend(self._create_decorative_line())
        story.append(Spacer(1, 30))
        
        # Add main certificate text
        story.append(Paragraph("This is to certify that", self.body_style))
        story.append(Spacer(1, 10))
        
        # Organization name (highlighted)
        story.append(Paragraph(f"<b>{assessment_data['organization_name']}</b>", self.org_style))
        story.append(Spacer(1, 20))
        
        # Certificate body text
        certificate_text = f"""
        has successfully demonstrated compliance with the requirements of ISO 42001:2023 
        for their AI Management System: <b>{assessment_data['ai_system_name']}</b>
        <br/><br/>
        This certification confirms that the organization has implemented effective 
        artificial intelligence governance, risk management, and operational controls 
        in accordance with international standards.
        """
        story.append(Paragraph(certificate_text, self.body_style))
        story.append(Spacer(1, 30))
        
        # Add assessment details table
        story.extend(self._create_details_table(assessment_data))
        story.append(Spacer(1, 30))
        
        # Add signature section
        story.extend(self._create_signature_section(assessment_data))
        
        # Add footer with QR code and certificate ID
        story.extend(self._create_footer(assessment_data))
        
        # Build the PDF
        doc.build(story, onFirstPage=self._add_background, onLaterPages=self._add_background)
        
        return output_path
    
    def _create_header(self):
        """Create certificate header with logo and decorative elements"""
        elements = []
        
        # Add some spacing for the header
        elements.append(Spacer(1, 20))
        
        # Header text
        header_text = "VULNURIS SECURITY SOLUTIONS LLP"
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Normal'],
            fontSize=16,
            textColor=self.primary_color,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        elements.append(Paragraph(header_text, header_style))
        elements.append(Spacer(1, 10))
        
        # Subtitle
        subtitle_text = "Authorized ISO 42001 Compliance Assessment Provider"
        subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        elements.append(Paragraph(subtitle_text, subtitle_style))
        elements.append(Spacer(1, 30))
        
        return elements
    
    def _create_decorative_line(self):
        """Create decorative line separator"""
        elements = []
        
        # Create a simple decorative line using a table
        line_data = [[''] * 50]  # Empty cells to create a line effect
        line_table = Table(line_data, colWidths=[self.content_width/50] * 50)
        line_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), self.accent_color),
            ('GRID', (0, 0), (-1, -1), 2, self.accent_color),
        ]))
        
        elements.append(line_table)
        return elements
    
    def _create_details_table(self, assessment_data: Dict[str, Any]):
        """Create assessment details table"""
        elements = []
        
        # Prepare table data
        table_data = [
            ['Assessment Details', ''],
            ['Certificate ID:', assessment_data.get('certificate_id', 'CERT-' + datetime.now().strftime('%Y%m%d-%H%M%S'))],
            ['Assessment Date:', assessment_data.get('completion_date', datetime.now().strftime('%B %d, %Y'))],
            ['Compliance Score:', f"{assessment_data.get('final_score', 0):.1f}%"],
            ['Risk Level:', assessment_data.get('risk_level', 'Medium').title()],
            ['Industry:', assessment_data.get('industry', 'Technology').title()],
            ['Valid Until:', (datetime.now() + timedelta(days=365)).strftime('%B %d, %Y')],
        ]
        
        # Create table
        details_table = Table(table_data, colWidths=[3*inch, 4*inch])
        details_table.setStyle(TableStyle([
            # Header row
            ('BACKGROUND', (0, 0), (-1, 0), self.primary_color),
            ('TEXTCOLOR', (0, 0), (-1, 0), HexColor('#ffffff')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('SPAN', (0, 0), (-1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            
            # Data rows
            ('BACKGROUND', (0, 1), (0, -1), self.light_gray),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            
            # Borders
            ('GRID', (0, 0), (-1, -1), 1, self.primary_color),
            ('LINEBELOW', (0, 0), (-1, 0), 2, self.primary_color),
        ]))
        
        elements.append(details_table)
        return elements
    
    def _create_signature_section(self, assessment_data: Dict[str, Any]):
        """Create signature section"""
        elements = []
        
        # Signature table
        signature_data = [
            ['', '', ''],
            ['_' * 30, '', '_' * 30],
            ['Mandar Waghmare', '', f"Date: {datetime.now().strftime('%B %d, %Y')}"],
            ['Authorized Signatory', '', 'Certificate Issue Date'],
            ['Qryti', '', ''],
        ]
        
        signature_table = Table(signature_data, colWidths=[3*inch, 1*inch, 3*inch])
        signature_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 2), (0, 2), 'Helvetica-Bold'),
            ('FONTNAME', (2, 2), (2, 2), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 2), (0, 2), 12),
            ('FONTSIZE', (2, 2), (2, 2), 12),
        ]))
        
        elements.append(signature_table)
        return elements
    
    def _create_footer(self, assessment_data: Dict[str, Any]):
        """Create footer with QR code and additional information"""
        elements = []
        
        elements.append(Spacer(1, 20))
        
        # Footer text
        footer_text = """
        This certificate is issued based on a comprehensive assessment of the organization's 
        AI management system against ISO 42001:2023 requirements. The certificate is valid 
        for one year from the date of issue and may be verified using the certificate ID above.
        """
        
        footer_style = ParagraphStyle(
            'FooterStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=self.text_color,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        elements.append(Paragraph(footer_text, footer_style))
        elements.append(Spacer(1, 10))
        
        # Contact information
        contact_text = "Qryti | ISO 42001 Compliance Assessment | www.qryti.com"
        contact_style = ParagraphStyle(
            'ContactStyle',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=self.secondary_color,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        elements.append(Paragraph(contact_text, contact_style))
        
        return elements
    
    def _add_background(self, canvas, doc):
        """Add background elements to the certificate"""
        canvas.saveState()
        
        # Add border
        canvas.setStrokeColor(self.primary_color)
        canvas.setLineWidth(3)
        canvas.rect(20, 20, self.page_width - 40, self.page_height - 40)
        
        # Add inner border
        canvas.setStrokeColor(self.accent_color)
        canvas.setLineWidth(1)
        canvas.rect(30, 30, self.page_width - 60, self.page_height - 60)
        
        # Add corner decorations
        self._add_corner_decorations(canvas)
        
        canvas.restoreState()
    
    def _add_corner_decorations(self, canvas):
        """Add decorative elements to corners"""
        corner_size = 30
        
        # Top-left corner
        canvas.setFillColor(self.accent_color)
        canvas.circle(50, self.page_height - 50, 5, fill=1)
        
        # Top-right corner
        canvas.circle(self.page_width - 50, self.page_height - 50, 5, fill=1)
        
        # Bottom-left corner
        canvas.circle(50, 50, 5, fill=1)
        
        # Bottom-right corner
        canvas.circle(self.page_width - 50, 50, 5, fill=1)
    
    def generate_qr_code(self, data: str, size: int = 100) -> str:
        """Generate QR code for certificate verification"""
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create QR code image
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64 for embedding
        buffer = io.BytesIO()
        qr_img.save(buffer, format='PNG')
        qr_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return qr_base64

def generate_compliance_certificate(assessment_data: Dict[str, Any], output_dir: str = None) -> str:
    """
    Generate a compliance certificate for a successful assessment
    
    Args:
        assessment_data: Assessment and organization data
        output_dir: Directory to save the certificate (optional)
        
    Returns:
        Path to the generated certificate file
    """
    
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), '..', 'certificates')
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate certificate filename
    org_name = assessment_data.get('organization_name', 'Organization').replace(' ', '_')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"ISO42001_Certificate_{org_name}_{timestamp}.pdf"
    output_path = os.path.join(output_dir, filename)
    
    # Generate the certificate
    generator = CertificateGenerator()
    certificate_path = generator.generate_certificate(assessment_data, output_path)
    
    return certificate_path

# Example usage and testing
if __name__ == "__main__":
    # Test certificate generation
    test_data = {
        'organization_name': 'TechCorp AI Solutions',
        'ai_system_name': 'Customer Service AI Assistant',
        'final_score': 87.5,
        'risk_level': 'medium',
        'industry': 'technology',
        'completion_date': datetime.now().strftime('%B %d, %Y'),
        'certificate_id': 'CERT-20250702-001'
    }
    
    try:
        cert_path = generate_compliance_certificate(test_data)
        print(f"Test certificate generated: {cert_path}")
    except Exception as e:
        print(f"Error generating test certificate: {e}")

