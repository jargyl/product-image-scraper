import requests
from bs4 import BeautifulSoup
import csv
from PIL import Image, ImageDraw, ImageFont
import os.path
import time
from collage import create_collage

LOGFILE = "names.txt"

def get_items_from_csv(path):
    item_list = []
    with open(path) as csvfile:
        csv_reader = csv.reader(csvfile)
        for row in csv_reader:
            item_list.append(row)
    item_list.pop(0)
    # SORT BY SIZE
    item_list.sort(key=lambda x: x[1])
    return item_list


def get_product_picture_from_url(url, logfile, size):
    # GET PRODUCT IMAGE URL
    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')
    images = soup.find_all('img')
    link = ""
    for image in images:
        link = image['src']
        if link.startswith('https://media.restocks.net/products/'):
            break
    # GET PRODUCT NAME
    product_title = soup.find('div', {'class': 'product__title'}).find(
        "h1", recursive=False)
    add_product_name_to_logs(product_title.text, size, logfile)
    slug = url.replace(url[0:26], "")
    save_product_picture_with_size(slug, size, link)


def get_product_picture_from_sku(sku, logfile, size):
    sku = sku.upper()
    r = requests.get("https://restocks.net/nl/shop/search?q={}&page=1".format(sku)).json()
    if r['data']:
        product = r['data'][0]
        if product['sku'] == sku:
            product_picture = product['image']
            product_picture = product_picture.replace('400.png', '1000.png')
            product_name = product['name']
            add_product_name_to_logs(product_name, size, logfile)
            slug = (product['slug']).replace((product['slug'])[0:26], "")
            save_product_picture_with_size(slug, size, product_picture)
        else:
            print('No exact match with SKU {} found.'.format(sku))
    else:
        print("No match with SKU {}.".format(sku))


def add_product_name_to_logs(name, size, path):
    text = name + " - EU " + size
    print(text)
    file = open(path, 'a')
    file.write(text + "\n")
    file.close()


def save_product_picture_with_size(name, size, img_url):
    name = name.replace(' ', '-').replace('"', '')
    size = size.replace('/', 'l').replace(' ', '_')
    filename = size + "_" + name
    path = "images/{}".format(filename)
    if not (os.path.exists(path + ".png")):
        with open(path + '.png', 'wb') as f:
            im = requests.get(img_url)
            f.write(im.content)
        # ADD SIZE TO IMAGE
        im = Image.open("images/" + filename + '.png').convert('RGBA')
        title_font = ImageFont.truetype("arial.ttf", size=100)
        title_text = size.replace('_', ' ')
        image_editable = ImageDraw.Draw(im)
        image_editable.text((15, 15), title_text, (0, 0, 0), font=title_font)
        im.save("images/" + filename + ".png")


# CLEAR TXT FILE
product_names = open('names.txt', 'w').close

# PROMPT USER TO CHOOSE MODE
modes = ['SCRAPE', 'COLLAGE']
user_input = ''
input_message = "Choose a mode:\n"
for index, item in enumerate(modes):
    input_message += f'{index + 1}) {item}\n'
input_message += 'Your choice: '
while user_input not in map(str, range(1, len(modes) + 1)):
    user_input = input(input_message)
print('Starting ' + modes[int(user_input) - 1] + " mode ...\n" )

start_time = time.time()
data = []
if user_input == "1":
    data = get_items_from_csv('scrape.csv')
    for p in data:
        if p[0].startswith("http"):
            get_product_picture_from_url(p[0], LOGFILE, p[1])
        else:
            get_product_picture_from_sku(p[0], LOGFILE, p[1])
if user_input == "2":
    print("Choose height & width of collage (eg. 4x8)")
    while True:
        try:
            vertical = int(input("Height: "))
            horizontal = int(input("Width: "))
            break
        except ValueError:
            print("Please enter a number")
    create_collage(vertical, horizontal)
print("--- %s seconds ---" % round((time.time() - start_time), 2))
