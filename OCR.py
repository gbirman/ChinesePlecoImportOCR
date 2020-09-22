
from operator import itemgetter
from itertools import groupby, chain
import fitz
from tesserocr import PyTessBaseAPI, OEM, PSM
from collections import defaultdict, Counter, OrderedDict
import kmeans1d 
from PIL import Image
import io
import re
from pypinyin import lazy_pinyin
import numpy as np
import bisect 
import unidecode
from string import ascii_uppercase

filename = "/Users/gabrielbirman/Chinese_OCR/107Textbook.pdf"
doc = fitz.open(filename)

# get chapter references 
table_of_contents_pages = [5,6,7]
ref_start = 5
num_chapters = 48
#################

sf = 25/6
eps = 1
offset = 18
pagenums = range(445+offset, 471+offset+1) #471+18 (incl.)
letters_cache = True # cache the bid to start of each new letter

# get total bounding box r1 U r2 
# assumes bbox has form (x0, y0, x1, y1)
def union(r1, r2):
    # print(r1)
    # print(r2)
    return (min(r1[0],r2[0]), min(r1[1],r2[1]), max(r1[2], r2[2]), max(r1[3],r2[3]))

# checks if box is a letter
def isLetter(text):
    return len(text) == 1 and text.isalpha()

# pads bbox with unit padding or directional padding before scaling by sf factor
def resize(bbox, sf, pad):
    if type(pad) is int:
        pad = 4*[pad]
    return (sf*(bbox[0]-pad[0]), sf*(bbox[1]-pad[1]), sf*(bbox[2]+pad[2]), sf*(bbox[3]+pad[3]))

# returns a PNG of a bbox on a given page
def getImg(pg_num, bbox):
    bbox_resize = resize(bbox, sf, eps)
    pix = doc[pg_num].getPixmap(matrix = fitz.Matrix(sf,sf))
    img = Image.open(io.BytesIO(pix.getPNGData()))
    block_img = img.crop(bbox_resize)
    return block_img

# TODO:
# - create GUI  
# - improve character recognition using multiple OCR + vocab tools
# - one pass OCR
# - modularize code 
# - get lesson and page through tesseract 
# - create index links word to page
# - create OCR layer in index
# - OCR on entire textbook 
# - Lesson verification: lesson maps to page range from table of contents
# - get lesson/page number on next page if there is a break 

def test_word_format(word):
    assert('wid' in word)
    assert('groups' in word)
    groups = word['groups']
    assert(type(groups) is list)
    assert(len(groups) >= 1)
    for group in groups:
        assert('bid' in group)
        assert('bbox' in group)
        assert('pg' in group)
        assert('text' in group)
        bids = group['bid']
        bbox = group['bbox']
        pg = group['pg']
        text = group['text']
        assert(type(bids) is list)
        assert(type(bbox) is tuple)
        assert(type(pg) is int)
        assert(type(text) is str)
        assert(len(bids) >= 1)
        assert(len(bbox) == 4)

# format of a block:
# bid 
# bbox 
# cluster 

# format of a word (essentially multiple groups)
# list of bid lists --> each bid list contains bids corresponding to the equivalent index bbox
# list of bbox ---> each bbox is 4-tuple containing sides of rectangle

# format of a group:
# group id
# bid list 
# bbox 

bid = 0
block_dict = {}
def add_block(block):
    global bid 
    global block_dict
    assert('bid' not in block)
    block['bid'] = bid


# add a new word to a list of words 
wid = 0
def add_word(words, word):
    global wid
    assert('wid' not in word)
    word['wid'] = wid
    words.append(word)
    wid += 1

# add a new group to a word
gid = 0
def add_group(word, group):
    global gid
    assert('gid' not in group)
    group['gid'] = gid
    if word:
        word['groups'].append(group)
    else:
        word['groups'] = [group]
    gid += 1
    return word

def add_block(group, block):
    global bid
    bid, bbox, pg, text = block['bid'], block['bbox'], block['pg'], block['text']
    # use the last group if there are multiple
    if type(group) is list:
        group = group[-1]
    if 'bid' in group:
        group['bid'].append(bid)
        group['bbox'] = union(group['bbox'], bbox)
        assert(group['pg'] == pg) # should be on the same page
        group['text'] += text # inefficient but fine for now
    else:
        group['bid'] = [bid]
        group['bbox'] = bbox
        group['pg'] = pg
        group['text'] = text
    return group

def groupBlocks(blocks_in, prev_word, pg_num):

    # Cluster blocks horizontally by the following 5 categories:
    # left word, left cont., center, right word, right cont.
    clusters, centroids = kmeans1d.cluster([block['bbox'][0] for block in blocks_in], 5)

    # add the cluster component to the blocks
    blocks = [{**block, 'cluster': cluster} for block, cluster in zip(blocks_in, clusters)]
    # sort in vertical direction 
    blocks.sort(key=lambda block: (block['bbox'][1]+block['bbox'][3])/2 + (1e5 if block['bbox'][0] > centroids[2] else 0)) 

    left_words = [] # words on left side of page
    right_words = [] # words on right side of page
    split_words = [] # words that are split across sides/pages
    left_word = [] # holds data for left-side words
    right_word = [] # holds data for right-side words
    insert_word = None # used to hold data from a split word
    for block in blocks:
        cluster = block['cluster']
        if cluster == 0: # start of phrase (left side)
            if prev_word:
                insert_word = prev_word
                prev_word = False
            if left_word:
                add_word(left_words, left_word)
            left_word = add_group({}, add_block({}, block))
        elif cluster == 1: # continuation of phrase (left side)
            if prev_word:
                split_word = add_group(prev_word, add_block({}, block))
                add_word(split_words, split_word)
                prev_word = None
                continue
            assert(left_word)
            add_block(left_word['groups'], block)
        elif cluster == 3: # start of phrase (right side) 
            if right_word:
                add_word(right_words, right_word)
            elif left_word:
                add_word(left_words, left_word)
                left_word = None
            right_word = add_group({}, add_block({}, block))
        elif cluster == 4: # continuation of phrase (right side)
            if right_word:  
                add_block(right_word['groups'], block)
            else:
                assert(left_word)
                split_word = add_group(left_word, add_block({}, block)) 
                add_word(split_words, split_word)
                left_word = None

    # make sure we terminate with the last item on either side
    last_word = right_word if right_word else left_word
    return left_words + right_words, split_words, last_word, insert_word

def getWords(pages, letters_cache):

    standard_words, split_words, letters = [], [], {'bid': [], 'letters': []}
    prev_word = None
    letter_detect = PyTessBaseAPI(psm=8, lang='eng')
    letter_detect.SetVariable('tessedit_char_whitelist', ascii_uppercase)
    bid = 0
    for pg_num in pages:
        page = doc[pg_num]

        # get initial block bounding boxes
        blocks = [] 
        for block in page.getText("blocks"):            
            bbox = block[:4]
            text = block[4].strip()
            if len(text) != 1: # not a single letter
                blocks.append({'bid': bid, 'bbox': bbox, 'pg': page.number, 'text': text})
                bid += 1
            elif not letters_cache:
                # maps each bid to a corresponding dictionary letter 
                # this provides a heuristic for our search
                sf, eps = 25/6, 1
                pix = page.getPixmap(matrix = fitz.Matrix(sf,sf))
                img = Image.open(io.BytesIO(pix.getPNGData()))
                bbox = resize(bbox, sf, eps)
                block_img = img.crop(bbox)
                letter_detect.SetImage(block_img)
                letter_detect.Recognize()
                letter = letter_detect.AllWords()[0]
                assert(len(letter) == 1)
                letters['bid'].append(bid)
                letters['letters'].append(letter.lower())

        standard, split, prev_word, insert_word = groupBlocks(blocks, prev_word, pg_num)

        # last block from previous page (no spillover)
        if insert_word:
            add_word(standard, insert_word)

        # clean up 
        standard_words.extend(standard)
        split_words.extend(split)

    # add the last word 
    if prev_word:
        add_word(standard, prev_word) 

    # make sure all the blocks are properly formatted
    for word in chain(standard_words, split_words):
        test_word_format(word)

    return standard_words, split_words, letters

def classify(img, ocr):
    ocr.SetImage(img)
    ocr.Recognize()
    return ocr.MapWordConfidences()

def getChinese(mapping):
    char_pattern = re.compile(u'[\u4e00-\u9fff]+') # chinese chars
    first_char = False
    chars = []
    char_confs = []
    pinyin = []
    for i, (text, conf) in enumerate(mapping): # ignore first word if character
        if re.search(char_pattern, text) and i != 0:
            first_char = True
            matches = re.findall(char_pattern, text) 
            text = ''.join(matches)
            chars.append(text)
            char_confs.append(conf)
        elif first_char:
            break
        else:
            text = ''.join(filter(str.isalpha, text)).lower()
            pinyin.append(text)
    chars = ''.join(chars)
    pinyin = ''.join(pinyin)

    return pinyin, chars, char_confs

def getEnglish(mapping):
    thresh = 80
    nums = []
    pinyin = []
    num_pattern = re.compile("^[0-9]")
    done_flag = False
    for text, conf in mapping:
        if re.search(num_pattern, text):
            text = ''.join(filter(str.isdigit, text))
            if text and conf > thresh:
                nums.append(int(text))
        elif not done_flag:
            # go until first comma
            if re.search(',', text):
                text = unidecode.unidecode(''.join(filter(str.isalpha, text))).lower()
                pinyin.append(text)
                done_flag = True
    pinyin = ''.join(pinyin)

    nums = nums if len(nums) == 2 else None      
    return pinyin, nums

def refine(chars, char_confs, chi_pinyin, eng_pinyin, bid, letters):

    # get pinyin from characters
    # w/ slight modifications
    def extract(chars):
        lp = lazy_pinyin(chars)
        if lp[-1] == 'er':
            lp[-1] = 'r'
        return ''.join(lp)

    # return if empty
    if not chars:
        return None

    # try for all heteronym combinations
    # make sure lettering order is preserved 
    ordered = True
    to_pinyin = extract(chars)
    letter_idx = bisect.bisect(letters['bid'], bid) - 1
    letter = letters['letters'][letter_idx]
    if to_pinyin[0] != letter:
         ordered = False
        
    # valid if all characters greater than threshold
    thresh = 60
    if np.all(np.array(char_confs) > thresh):
        return chars if ordered else None

    # assume a pinyin match is a high enough probability real match
    if to_pinyin == chi_pinyin or to_pinyin == eng_pinyin:
        return chars if ordered else None

    # small alterations
    if len(chars) > 1:  
        # try removing first character
        to_pinyin = extract(chars[1:])
        if to_pinyin == chi_pinyin or to_pinyin == eng_pinyin:
            return chars[1:] if to_pinyin[0] == letter else None

        # try removing last character
        to_pinyin = extract(chars[:-1])
        if to_pinyin == chi_pinyin or to_pinyin == eng_pinyin:
            return chars[:-1] if ordered else None

        # try removing both
        if len(chars) > 2:
            to_pinyin = extract(chars[1:-1])
            if to_pinyin == chi_pinyin or to_pinyin == eng_pinyin:
                return chars[1:-1] if to_pinyin[0] == letter else None
    
    return None

if __name__ == "__main__":

    standard_words, split_words, letters = getWords(pagenums, letters_cache)

    if letters_cache:
        letters = {'bid': [1, 20, 156, 293, 487, 492, 585, 758, 866, 1059, 1122, 1215, 1298, 1355, 1358, 1412, 1502, 1561, 1792, 1919, 1988, 2130, 2315], 'letters': ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'w', 'x', 'y', 'z']}

    manual_words = []
    success_words = []
    pg_cache = {}
    lesson2word = OrderedDict()
    chi_detector_multi = PyTessBaseAPI(psm=3, lang="chi_sim")
    chi_detector = PyTessBaseAPI(psm=7, lang="chi_sim")
    eng_detector_multi = PyTessBaseAPI(psm=3, lang="eng")
    eng_detector = PyTessBaseAPI(psm=7, lang="eng")
        
    total_count = missed_count = 0
    for word in chain(split_words, standard_words):
        wid = word['wid']
        total_count += 1
        chi_map, eng_map = [], []
        for group in word['groups']: # convert to [bidlist, bbox]
            bids, bbox, pg_num = group['bid'], group['bbox'], group['pg']
            bbox = resize(bbox, sf, [eps,0,eps,0])
            if pg_num in pg_cache:
                img = pg_cache[pg_num]
            else:
                pix = doc[pg_num].getPixmap(matrix = fitz.Matrix(sf,sf))
                img = Image.open(io.BytesIO(pix.getPNGData()))
                pg_cache[pg_num] = img
            block_img = img.crop(bbox)
            if len(bids) == 1: # single line 
                chi_map.extend(classify(block_img, chi_detector))
                eng_map.extend(classify(block_img, eng_detector))
            else: # multi-line 
                chi_map.extend(classify(block_img, chi_detector_multi))
                eng_map.extend(classify(block_img, eng_detector_multi))
        chi_pinyin, chars, char_confs = getChinese(chi_map)
        eng_pinyin, nums = getEnglish(eng_map)
        guess = refine(chars, char_confs, chi_pinyin, eng_pinyin, bids[0], letters)
        # print(word, chars, char_confs, chi_pinyin, eng_pinyin, bids)
        if guess and nums:
            lesson, pg_dest = nums
            if lesson in lesson2word:
                lesson2word[lesson].append(guess)
            else:
                lesson2word[lesson] = [guess]
            success_words.append(word)
            print(f'{wid}: SUCCESS -- {guess}, {eng_pinyin}')
        else:
            missed_count += 1
            manual_words.append(word)
            print(f'{wid}: FAILURE -- {guess}, {eng_pinyin}')

    print(f'Unable to classify {missed_count}/{total_count} ({round(missed_count/total_count,2)*100}%)')

    # quit() # safety precaution
    np.save("success_words", success_words)
    np.save("manual_words", manual_words)
    np.save("lesson2word", lesson2word)
    np.save("split_words", split_words)
    np.save("pg_cache", pg_cache)