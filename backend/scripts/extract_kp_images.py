import fitz, os

pdf_path = r'K:\Projects\UNIK\KP\КП Русал КРаз.xlsx - Метал (1).pdf'
doc = fitz.open(pdf_path)
os.makedirs(r'K:\Projects\UNIK\output\kp_images', exist_ok=True)

for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=150)
    pix.save(rf'K:\Projects\UNIK\output\kp_images\page_{i+1}.png')
    images = page.get_images(full=True)
    print(f'Page {i+1}: {len(images)} embedded images')
    for j, img in enumerate(images):
        xref = img[0]
        base = doc.extract_image(xref)
        ext = base['ext']
        fp = rf'K:\Projects\UNIK\output\kp_images\page{i+1}_img{j}.{ext}'
        with open(fp, 'wb') as f:
            f.write(base['image'])
        print(f'  Saved ({len(base["image"])} bytes)')

doc.close()
print('Done')
