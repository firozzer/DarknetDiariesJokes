import os, re
from PIL import Image, ImageFont, ImageDraw

os.chdir(os.path.dirname(os.path.abspath(__file__)))

filenames = next(os.walk(os.path.dirname(os.path.abspath(__file__))), (None, None, []))[2]  # [] if no file

for filename in filenames:
    if filename[-4:] != ".jpg": continue
    blackBgBase = Image.new('RGBA', (1000, 563), color=(0,0,0,255)) # need RGBA for opacity work on text
    fgArtwork = Image.open(filename).convert('RGBA') # foreground Artwork

    if fgArtwork.width != 1000:
        newHt = int(1000 * fgArtwork.height / fgArtwork.width)
        fgArtwork = fgArtwork.resize((1000,newHt))

    if fgArtwork.height > 563:
        newWd = int(563 * fgArtwork.width / fgArtwork.height)
        fgArtwork = fgArtwork.resize((newWd, 563))

    centerOffset = ((blackBgBase.width - fgArtwork.width) // 2, (blackBgBase.height - fgArtwork.height) // 2)
    blackBgBase.paste(fgArtwork, centerOffset)

    newFname = re.search('EP \d{2,6} ', filename)
    newFname = newFname[0][3:-1]
    epNoName = "Ep" + filename[2:-4]
    
    layerForTxt = Image.new("RGBA", blackBgBase.size, (255, 255, 255, 0)) # to give opacity to text bg, need to create this layer & then alpha_composite it once texting is done
    font = ImageFont.truetype('calibri.ttf', 50)
    cntr = (blackBgBase.width/2, (blackBgBase.height/4)*3) # width center & height at 75%
    draw = ImageDraw.Draw(layerForTxt)
    bbox = draw.textbbox(cntr, epNoName, font=font, anchor='mm') # anchor mm centre aligns (it is like transfomr(translate) from CSS)
    draw.rectangle(bbox, (0,0,0,150))
    draw.text(cntr, epNoName, font=font, fill="white", anchor="mm")    
    out = Image.alpha_composite(blackBgBase, layerForTxt)
    out.convert("RGB").save(f'j{newFname}.jpg') # RGBA cant be saved as JPG so converting again