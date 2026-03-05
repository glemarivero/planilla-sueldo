import argparse
import yaml
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    FrameBreak,
    KeepInFrame,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm

ACCENT_COLOR = colors.HexColor("#1d3557")
HEADER_FILL = colors.HexColor("#eef2ff")
LINE_COLOR = colors.HexColor("#c7cddb")
PAGE_SIZE = landscape(A4)
PAGE_WIDTH = PAGE_SIZE[0]
PAGE_HEIGHT = PAGE_SIZE[1]
MARGIN_LEFT = 20 * mm
MARGIN_RIGHT = 20 * mm
MARGIN_TOP = 10 * mm
MARGIN_BOTTOM = 10 * mm
FULL_TABLE_WIDTH = PAGE_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
BADGE_COL_WIDTH = 40 * mm
BLOCK_GAP = 12


def _format_currency(value):
    thousands, decimals = f"{value:,.2f}".split(".")
    thousands = thousands.replace(",", ".")
    return f"$ {thousands},{decimals}"

def process_info(data):
    incomes = data["ingresos"]
    excluded_income_names = set(data.get("ingresos_no_deducibles", []))
    deductible_income_total = sum(
        value for name, value in incomes.items()
        if name not in excluded_income_names
    )
    discount_percentages = data["descuentos"]
    discount_entries = []
    for name, percentage in discount_percentages.items():
        raw_amount = deductible_income_total * percentage / 100 if deductible_income_total else 0.0
        amount = round(raw_amount)
        discount_entries.append((name, amount))
    total_inc = sum(incomes.values())
    total_disc = sum(amount for _, amount in discount_entries)
    net_pay = total_inc - total_disc
    return {
        "incomes": incomes,
        "discount_entries": discount_entries,
        "total_inc": total_inc,
        "total_disc": total_disc,
        "net_pay": net_pay,
        "transport": data.get("transporte", 0)
    }


def _receipt_block(styles, label, data, available_width):

    elements = []
    info = process_info(data)
    incomes = info["incomes"]
    discount_entries = info["discount_entries"]
    total_inc = info["total_inc"]
    total_disc = info["total_disc"]
    net_pay = info["net_pay"]

    employer_info = (
        f"<b>{data['empleador']}</b><br/>"
        f"{data['direccion']}<br/>"
        f"<font size=9>GRUPO: {data['grupo']} / BPS: {data['bps']} / RUT: {data['rut']}</font>"
    )

    badge_content = (
        "<font size=9>RECIBO DE HABERES</font><br/>"
        f"<b>{label}</b>"
    )

    header = Table(
        [
            [
                Paragraph(employer_info, styles["Employer"]),
                Paragraph(badge_content, styles["Badge"])
            ]
        ],
        colWidths=[available_width - BADGE_COL_WIDTH, BADGE_COL_WIDTH],
        hAlign="RIGHT"
    )
    header.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), HEADER_FILL),
        ("TEXTCOLOR", (0,0), (0,0), ACCENT_COLOR),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("BACKGROUND", (1,0), (1,0), ACCENT_COLOR),
        ("TEXTCOLOR", (1,0), (1,0), colors.white),
        ("ALIGN", (1,0), (1,0), "CENTER"),
        ("BOX", (0,0), (-1,-1), 0.6, LINE_COLOR),
        ("LEFTPADDING", (0,0), (0,0), 8),
        ("RIGHTPADDING", (0,0), (0,0), 8),
        ("TOPPADDING", (0,0), (0,0), 6),
        ("BOTTOMPADDING", (0,0), (0,0), 6),
        ("TOPPADDING", (1,0), (1,0), 10),
        ("BOTTOMPADDING", (1,0), (1,0), 10),
    ]))
    elements.append(header)
    elements.append(Spacer(1, 8))

    def simple_table(headers, values, col_widths):
        t = Table([headers, values], colWidths=col_widths, hAlign="RIGHT")
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), HEADER_FILL),
            ("TEXTCOLOR", (0,0), (-1,0), ACCENT_COLOR),
            ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
            ("BOTTOMPADDING", (0,0), (-1,0), 6),
            ("LINEBELOW", (0,0), (-1,0), 0.4, LINE_COLOR),
            ("LINEABOVE", (0,0), (-1,0), 0.4, LINE_COLOR),
            ("BOX", (0,0), (-1,-1), 0.4, LINE_COLOR),
            ("LEFTPADDING", (0,0), (-1,-1), 6),
            ("RIGHTPADDING", (0,0), (-1,-1), 6),
            ("TOPPADDING", (0,1), (-1,-1), 4),
            ("BOTTOMPADDING", (0,1), (-1,-1), 4),
        ]))
        return t

    elements.append(simple_table(
        ["APELLIDO Y NOMBRE", "C.I.", "FECHA INGRESO"],
        [data["empleado"], data["ci"], data["fecha_ingreso"]],
        [available_width * 0.5, available_width * 0.25, available_width * 0.25]
    ))
    elements.append(Spacer(1, 4))

    elements.append(simple_table(
        ["INSTITUCIÓN FINANCIERA", "NUMERO DE CUENTA"],
        [data["institucion"], data["cuenta"]],
        [available_width * 0.5, available_width * 0.5]
    ))
    elements.append(Spacer(1, 4))

    elements.append(simple_table(
        ["PERÍODO DE PAGO", "TIPO"],
        [data["periodo"], data["tipo_pago"]],
        [available_width * 0.6, available_width * 0.4]
    ))
    elements.append(Spacer(1, 8))

    elements.append(Paragraph("<b>DETALLE DE LA LIQUIDACIÓN</b>", styles["Section"]))
    elements.append(Spacer(1, 3))

    def _filter_zeros(concepts):
        return [(name, value) for name, value in concepts.items() if round(value, 2) != 0]

    income_list = _filter_zeros(incomes)
    discounts_list = [(label, value) for label, value in discount_entries if round(value, 2) != 0]

    detail = [[
        Paragraph("CONCEPTOS", styles["SmallBold"]),
        Paragraph("REMUNERATIVA", styles["SmallBoldRight"]),
        Paragraph("DESCUENTOS", styles["SmallBoldRight"])
    ]]

    for name, value in income_list:
        detail.append([
            name,
            Paragraph(_format_currency(value), styles["SmallRight"]),
            ""
        ])

    for name, value in discounts_list:
        detail.append([
            name,
            "",
            Paragraph(_format_currency(value), styles["SmallRight"])
        ])

    detail.append([
        Paragraph("TOTALES", styles["SmallBold"]),
        Paragraph(_format_currency(total_inc), styles["SmallBoldRight"]),
        Paragraph(_format_currency(total_disc), styles["SmallBoldRight"])
    ])

    det_table = Table(
        detail,
        colWidths=[available_width * 0.47, available_width * 0.265, available_width * 0.265],
        hAlign="RIGHT"
    )
    detail_style = [
        ("BACKGROUND", (0,0), (-1,0), HEADER_FILL),
        ("TEXTCOLOR", (0,0), (-1,0), ACCENT_COLOR),
        ("FONT", (0,0), (-1,0), "Helvetica-Bold"),
        ("ALIGN", (1,0), (2,0), "RIGHT"),
        ("ALIGN", (1,1), (-1,-1), "RIGHT"),
        ("LINEABOVE", (0,0), (-1,0), 1, ACCENT_COLOR),
        ("LINEBELOW", (0,0), (-1,0), 1, ACCENT_COLOR),
        ("LINEABOVE", (0,-1), (-1,-1), 0.8, ACCENT_COLOR),
        ("LINEBELOW", (0,-1), (-1,-1), 0.8, ACCENT_COLOR),
        ("FONT", (0,-1), (-1,-1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0,-1), (-1,-1), ACCENT_COLOR),
        ("TOPPADDING", (0,0), (-1,0), 6),
        ("BOTTOMPADDING", (0,0), (-1,0), 6),
        ("TOPPADDING", (0,1), (-1,-2), 4),
        ("BOTTOMPADDING", (0,1), (-1,-2), 4),
        ("TOPPADDING", (0,-1), (-1,-1), 6),
        ("BOTTOMPADDING", (0,-1), (-1,-1), 6),
        ("BOX", (0,0), (-1,-1), 0.5, LINE_COLOR),
    ]
    for row in range(1, len(detail)-1):
        if row % 2 == 1:
            detail_style.append(("BACKGROUND", (0,row), (-1,row), HEADER_FILL))
        else:
            detail_style.append(("BACKGROUND", (0,row), (-1,row), colors.white))
            detail_style.append(("LINEBELOW", (0,row), (-1,row), 0.1, LINE_COLOR))
    det_table.setStyle(TableStyle(detail_style))
    elements.append(det_table)
    elements.append(Spacer(1, 8))

    net_pay_block = Table(
        [[
            Paragraph("REMUNERACIÓN LÍQUIDA", styles["SmallBold"]),
            Paragraph(_format_currency(net_pay), styles["Liquido"])
        ]],
        colWidths=[available_width * 0.65, available_width * 0.35],
        hAlign="RIGHT"
    )
    net_pay_block.setStyle(TableStyle([
        ("BOX", (0,0), (-1,-1), 0.4, ACCENT_COLOR),
        ("BACKGROUND", (0,0), (0,0), HEADER_FILL),
        ("BACKGROUND", (1,0), (1,0), colors.white),
        ("ALIGN", (0,0), (0,0), "LEFT"),
        ("ALIGN", (1,0), (1,0), "RIGHT"),
        ("VALIGN", (0,0), (0,0), "MIDDLE"),
        ("VALIGN", (1,0), (1,0), "MIDDLE"),
        ("LEFTPADDING", (0,0), (-1,-1), 6),
        ("RIGHTPADDING", (0,0), (-1,-1), 6),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    elements.append(net_pay_block)
    elements.append(Spacer(1, 8))

    elements.append(simple_table(
        ["LUGAR Y FECHA DE PAGO", "FORMA DE PAGO"],
        [f"{data['lugar_pago']}, {data['fecha_pago']}", data["forma_pago"]],
        [available_width * 0.6, available_width * 0.4]
    ))
    elements.append(Spacer(1, 6))
    elements.append(
        Paragraph(
            "Recibí el importe de esta liquidación en pago de mi remuneración correspondiente "
            "al período indicado y duplicado de la misma conforme a la ley vigente.",
            styles["Small"]
        )
    )
    elements.append(Spacer(1, 10))
    signature = Table(
        [[""], [""], [Paragraph("Firma", styles["SmallBold"])]],
        colWidths=[available_width],
        hAlign="RIGHT"
    )
    signature.setStyle(TableStyle([
        ("LINEABOVE", (0,0), (-1,0), 0.4, LINE_COLOR),
        ("TOPPADDING", (0,0), (-1,0), 12),
        ("TOPPADDING", (0,2), (-1,2), 2),
    ]))
    elements.append(signature)
    return elements


def generate_uruguay_receipt_one_page(pdf_file, data):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="Small", fontSize=9, leading=11, textColor=ACCENT_COLOR, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name="SmallBold", parent=styles["Small"], fontName="Helvetica-Bold", spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name="SmallRight", parent=styles["Small"], alignment=2))
    styles.add(ParagraphStyle(name="SmallBoldRight", parent=styles["SmallBold"], alignment=2))
    styles.add(ParagraphStyle(name="Liquido", fontSize=10, leading=12, alignment=2, textColor=ACCENT_COLOR, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name="Employer", fontSize=12, leading=14, textColor=ACCENT_COLOR, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name="Badge", fontSize=11, alignment=1, textColor=colors.white, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name="Section", fontSize=11, textColor=ACCENT_COLOR, spaceBefore=0, spaceAfter=4, leftIndent=6))
    styles["Normal"].textColor = ACCENT_COLOR
    styles["Normal"].spaceBefore = 0
    styles["Normal"].spaceAfter = 0
    styles["Title"].fontSize = 11
    styles["Title"].textColor = ACCENT_COLOR
    styles["Title"].spaceBefore = 0
    styles["Title"].spaceAfter = 0

    doc = BaseDocTemplate(
        pdf_file,
        pagesize=PAGE_SIZE,
        rightMargin=MARGIN_RIGHT,
        leftMargin=MARGIN_LEFT,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM
    )

    block_width = (FULL_TABLE_WIDTH - BLOCK_GAP) / 2
    block_height = PAGE_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

    frames = [
        Frame(
            MARGIN_LEFT,
            MARGIN_BOTTOM,
            block_width,
            block_height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="left",
        ),
        Frame(
            MARGIN_LEFT + block_width + BLOCK_GAP,
            MARGIN_BOTTOM,
            block_width,
            block_height,
            leftPadding=0,
            rightPadding=0,
            topPadding=0,
            bottomPadding=0,
            id="right",
        ),
    ]
    doc.addPageTemplates([PageTemplate(id="two-column", frames=frames)])

    elements = []
    original_block = KeepInFrame(block_width, block_height, _receipt_block(styles, "ORIGINAL", data, block_width), mode="shrink")
    copy_block = KeepInFrame(block_width, block_height, _receipt_block(styles, "COPIA", data, block_width), mode="shrink")

    elements.append(original_block)
    elements.append(FrameBreak())
    elements.append(copy_block)

    doc.build(elements)

def _parse_cli_args():
    parser = argparse.ArgumentParser(description="Generate a payroll receipt for a given month")
    parser.add_argument("month", help="Payroll month in YYYY-MM format (matches config/<month>.yaml)")
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_cli_args()
    month = args.month
    with open(f"config/{month}.yaml", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    generate_uruguay_receipt_one_page(f"receipts/{month}.pdf", data)
    print(f"Generated receipt for {month} at receipts/{month}.pdf")
    info = process_info(data)
    print("Net salary: " + _format_currency(info["net_pay"]))
    print("Transport allowance: " + _format_currency(info["transport"]))
    print(f"Transfer amount: {_format_currency(info['net_pay'] + info['transport'])}")