try:
    from PIL import Image
except ImportError:
    import Image
import pytesseract
from pytesseract import Output

res = pytesseract.image_to_data(Image.open('images/Excel/ExcelTabelle.png'), output_type=Output.DATAFRAME)
res['mytext'] = res['text'].apply(lambda x: str(x))
res = res.groupby(by=['level', 'page_num', 'block_num'])['mytext'].apply(' '.join)
res.to_csv('test.csv', header=True)

# image_to_string => String of text
# image_to_boxes => position of chars
# image_to_data => level, page_num, block_num, par_num, line_num, word_num, left, top, width, height, conf, text
# image_to_osd => Some Data about the Image

# ExcelTabelle.png
# ExcelTabelleEineSpalte.png
# ExcelTabelleEineZeile.png
# ExcelText.png
