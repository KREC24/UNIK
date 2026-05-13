import pdfplumber, json, sys

pdf_path = r'K:\Projects\UNIK\KP\КП Русал КРаз.xlsx - Метал (1).pdf'
out = []
with pdfplumber.open(pdf_path) as pdf:
    out.append(f"Pages: {len(pdf.pages)}")
    for i, page in enumerate(pdf.pages):
        text = page.extract_text()
        tables = page.extract_tables()
        out.append(f"\n=== PAGE {i+1} ===")
        if text:
            out.append(text)
        if tables:
            out.append(f"Tables found: {len(tables)}")
            for ti, t in enumerate(tables):
                out.append(f"  Table {ti+1}:")
                for row in t:
                    out.append(f"    {row}")

result = '\n'.join(out)
with open(r'K:\Projects\UNIK\output\kp_text.txt', 'w', encoding='utf-8') as f:
    f.write(result)
print("Done", len(result), "chars")
