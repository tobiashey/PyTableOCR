try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract'
print(pytesseract.image_to_data(Image.open('images/Excel/ExcelTabelle.png')))

# image_to_string => String of text
# image_to_boxes => position of chars
# image_to_data => level, page_num, block_num, par_num, line_num, word_num	left, top, width, height, conf, text
# image_to_osd => Some Data about the Image

# ExcelTabelle.png
# ExcelTabelleEineSpalte.png
# ExcelTabelleEineZeile.png
# ExcelText.png