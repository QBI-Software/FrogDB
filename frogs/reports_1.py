from reportlab.pdfgen import canvas
from django.http import HttpResponse
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from io import BytesIO
from .models import *
from .tables import PermitReportTable

from reportlab.lib.pagesizes import letter, A4

class MyPrint:
    def __init__(self, buffer, pagesize):
        self.buffer = buffer
        if pagesize == 'A4':
            self.pagesize = A4
        elif pagesize == 'Letter':
            self.pagesize = letter
        self.width, self.height = self.pagesize

    def froglog(self,species):
        buffer = self.buffer
        doc = SimpleDocTemplate(buffer,
                                rightMargin=72,
                                leftMargin=72,
                                topMargin=72,
                                bottomMargin=72,
                                pagesize=self.pagesize)

        # Our container for 'Flowable' objects
        elements = []

        # A large collection of style sheets pre-made for us
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='centered', alignment=TA_CENTER))
        elements.append(Paragraph(species, styles['Heading1']))
        s = styles["BodyText"]
        s.wordWrap = 'CJK'
        # Draw things on the PDF. Here's where the PDF generation happens.
        # See the ReportLab documentation for the full list of functionality.
        shipments = Permit.objects.filter(species__name=species)

        table = PermitReportTable(shipments)
        data = [[Paragraph(cell, s) for cell in row] for row in table.rows]
        t = Table(data)
        t.setStyle(TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
                       ('TEXTCOLOR',(1,1),(-2,-2),colors.red),
                       ('VALIGN',(0,0),(0,-1),'TOP'),
                       ('TEXTCOLOR',(0,0),(0,-1),colors.blue),
                       ('ALIGN',(0,-1),(-1,-1),'CENTER'),
                       ('VALIGN',(0,-1),(-1,-1),'MIDDLE'),
                       ('TEXTCOLOR',(0,-1),(-1,-1),colors.green),
                       ('INNERGRID', (0,0), (-1,-1), 0.25, colors.black),
                       ('BOX', (0,0), (-1,-1), 0.25, colors.black),
                       ]))

        elements.append(t)
        doc.build(elements)

        # Get the value of the BytesIO buffer and write it to the response.
        pdf = buffer.getvalue()
        buffer.close()
        return pdf


def print_froglog(request):
    #print('DEBUG:Request=', request)
    species = "X.borealis"
    filename = "%s_FrogLog.pdf" % species
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="%s"' % filename

    buffer = BytesIO()

    report = MyPrint(buffer, 'A4')
    pdf = report.froglog(species)

    response.write(pdf)
    return response



def test_view(request):
    # Create the HttpResponse object with the appropriate PDF headers.
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="test.pdf"'

    # Create the PDF object, using the response object as its "file."
    p = canvas.Canvas(response)

    # Draw things on the PDF. Here's where the PDF generation happens.
    # See the ReportLab documentation for the full list of functionality.
    p.drawString(100, 100, "Hello world.")

    # Close the PDF object cleanly, and we're done.
    p.showPage()
    p.save()
    return response


