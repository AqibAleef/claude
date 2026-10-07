"""Swap the illustrated stand-ins for real stock photos from Pexels or Pixabay, then rebuild the recipe.

    PEXELS_API_KEY=...  python3 tools/fetch_stock.py          (or PIXABAY_API_KEY=...)
    python3 tools/build_india.py assets tools/template.recipe.json tools/widths.json India_Beat_Sync_9x16.recipe.json

Free keys: https://www.pexels.com/api/  and  https://pixabay.com/api/docs/
Each scene is replaced by the best portrait result for its search, centre-cropped to 1080x1920. The original
illustration is kept as assets/scenes/<name>.illustration.jpg so you can go back. Both sites' licences allow free
use in videos; credit the photographers when you can (the script prints who shot what).
"""
import io, json, os, shutil, sys, urllib.parse, urllib.request
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SCENES = os.path.join(HERE, '..', 'assets', 'scenes')
SEARCH = {
    'holi': 'holi festival colours india', 'taj': 'taj mahal sunrise', 'kites': 'kite festival india sky', 'fort': 'jaipur amber fort',
    'chai': 'masala chai kulhad', 'varanasi': 'varanasi ghat aarti', 'cricket': 'cricket stadium india night', 'monsoon': 'mumbai monsoon rain',
    'diwali': 'diwali diya lamps',
}


def get(url, headers=None):
    req = urllib.request.Request(url, headers=dict({'User-Agent': 'kinekit-india-beatsync'}, **(headers or {})))
    with urllib.request.urlopen(req, timeout=30) as r: return r.read()


def pexels(q, key):
    j = json.loads(get('https://api.pexels.com/v1/search?' + urllib.parse.urlencode({'query': q, 'orientation': 'portrait', 'per_page': 5}), {'Authorization': key}))
    p = j['photos'][0]; return p['src']['large2x'], f"{p['photographer']} (Pexels {p['url']})"


def pixabay(q, key):
    j = json.loads(get('https://pixabay.com/api/?' + urllib.parse.urlencode({'key': key, 'q': q, 'orientation': 'vertical', 'image_type': 'photo', 'per_page': 5, 'safesearch': 'true'})))
    h = j['hits'][0]; return h['largeImageURL'], f"{h['user']} (Pixabay {h['pageURL']})"


def cover(im, w=1080, h=1920):
    s = max(w / im.width, h / im.height); im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    x, y = (im.width - w) // 2, (im.height - h) // 2; return im.crop((x, y, x + w, y + h))


def main():
    pk, xk = os.environ.get('PEXELS_API_KEY'), os.environ.get('PIXABAY_API_KEY')
    if not (pk or xk): sys.exit('Set PEXELS_API_KEY or PIXABAY_API_KEY first.')
    only = set(sys.argv[1:])
    for name, q in SEARCH.items():
        if only and name not in only: continue
        try:
            url, credit = pexels(q, pk) if pk else pixabay(q, xk)
            im = cover(Image.open(io.BytesIO(get(url))).convert('RGB'))
            dst = os.path.join(SCENES, name + '.jpg'); keep = os.path.join(SCENES, name + '.illustration.jpg')
            if os.path.exists(dst) and not os.path.exists(keep): shutil.copy(dst, keep)
            im.save(dst, quality=90); print(f'{name:9s} <- {credit}')
        except Exception as e:
            print(f'{name:9s} failed: {e}')


if __name__ == '__main__':
    main()
