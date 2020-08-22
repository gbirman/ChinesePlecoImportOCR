
from operator import itemgetter
from itertools import groupby
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

# get total bounding box r1 U r2 
# assumes bbox has form (x0, y0, x1, y1)
def union(r1, r2):
    return (min(r1[0],r2[0]), min(r1[1],r2[1]), max(r1[2], r2[2]), max(r1[3],r2[3]))

# checks if there is block spill over
def peeknext(block):
    return False

# checks if box is a letter
def isLetter(text):
    return len(text) == 1 and text.isalpha()

# pads bbox with unit padding or directional padding before scaling by sf factor
def resize(bbox, sf, pad):
    if type(pad) is int:
        pad = 4*[pad]
    return (sf*(bbox[0]-pad[0]), sf*(bbox[1]-pad[1]), sf*(bbox[2]+pad[2]), sf*(bbox[3]+pad[3]))

# get page number from box id or box object
def get_page_num(block_list, entry):
    # print(entry)
    if type(entry) is int:
        return block_list[entry][0]
    else:
        return block_list[entry[0][0]][0]

# get page number from box id or box object
def get_text(block_list, entry):
    # print(entry)
    if type(entry) is int:
        return block_list[entry][1]
    else:
        return block_list[entry[0][0]][1]

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

filename = "/Users/gabrielbirman/Desktop/107Textbook.pdf"
doc = fitz.open(filename)

# get chapter references 
table_of_contents_pages = [5,6,7]
ref_start = 5
num_chapters = 48
#################

def groupBlocks(bboxs, prevblock):

    # Cluster blocks horizontally by the following 5 categories:
    # left word, left cont., center, right word, right cont.
    clusters, centroids = kmeans1d.cluster([bbox[1][0] for bbox in bboxs], 5)

    blocks = [(bbox[0], bbox[1], cluster) for bbox, cluster in zip(bboxs, clusters)]
    blocks.sort(key=lambda block: (block[1][1]+block[1][3])/2 + (1e5 if block[1][0] > centroids[2] else 0)) # sort in vertical direction

    left_blocks = [] # items on left side
    right_blocks = [] # items on right side
    split_blocks = [] # items that are split across sides/pages
    left_block = []
    right_block = []
    insertblock = None
    for block in blocks:
        bid, bbox, cluster = block
        if cluster == 0:
            if prevblock:
                insertblock = prevblock
                prevblock = False
            if left_block:
                left_blocks.append([left_block])
            left_block = [[block[0]], block[1]]
        elif cluster == 1:
            if prevblock:
                split_block = prevblock
                split_block[0].append(bid)
                split_block[1] = [split_block[1]] + [bbox]
                split_blocks.append(split_block)
                prevblock = None
                continue
            assert(left_block)
            left_block[0].append(bid)
            left_block[1] = union(left_block[1], bbox)
        elif cluster == 3:
            if right_block:
                right_blocks.append([right_block])
            elif left_block:
                left_blocks.append([left_block])
                left_block = None
            right_block = [[block[0]], block[1]]
        elif cluster == 4:
            if right_block:   
                right_block[0].append(bid)
                right_block[1] = union(right_block[1], bbox)
            else:
                assert(left_block)
                split_block = left_block
                split_block[0].append(bid)
                split_block[1] = [split_block[1]] + [bbox]
                split_blocks.append(split_block)
                left_block = None

    # make sure we terminate with the last item on either side
    lastblock = right_block if right_block else left_block
    return left_blocks + right_blocks, split_blocks, lastblock, insertblock

def getBlocks(pages):

    standard_blocks, split_blocks, block_list, letter_list = [], [], [], []
    prevblock = None
    bid = 0
    letter_detect = PyTessBaseAPI(psm=8, lang='eng')
    letter_detect.SetVariable('tessedit_char_whitelist', ascii_uppercase)
    for pg_num in pages:
        page = doc[pg_num]
            
        # get initial block bounding boxes
        bboxs = [] 
        for block in page.getText("blocks"):            
            bbox = block[:4]
            text = block[4].strip()
            if len(text) != 1: # not a single letter
                bboxs.append((bid,bbox))
                block_list.append((page.number,text,bbox))
                bid += 1
            else:
                pass
                # sf, eps = 25/6, 1
                # pix = page.getPixmap(matrix = fitz.Matrix(sf,sf))
                # img = Image.open(io.BytesIO(pix.getPNGData()))
                # bbox = resize(bbox, sf, eps)
                # block_img = img.crop(bbox)
                # letter_detect.SetImage(block_img)
                # letter_detect.Recognize()
                # letter = letter_detect.AllWords()[0]
                # assert(len(letter) == 1)
                # letter_list.append((bid, letter.lower()))

        standard, split, prevblock, insertblock = groupBlocks(bboxs, prevblock)

        # last block from previous page (no spillover)
        if insertblock:
            standard_blocks.append([insertblock])

        standard_blocks.extend(standard)
        split_blocks.extend(split)
    
    # clean up 
    standard.append([prevblock]) # add the last item 
    standard_blocks.extend(standard)
    split_blocks.extend(split)

    # # draw blocks
    # for block in all_blocks:
    #     block_pg = get_page_num(box_list, block)
    #     shape = doc[block_pg].newShape()
    #     shape.drawRect(block[1])
    #     shape.finish(color=(1,0,0), width=0.3)
    #     shape.commit()

    return standard_blocks, split_blocks, block_list, letter_list

def classify(img, ocr):
    ocr.SetImage(img)
    ocr.Recognize()
    return ocr.MapWordConfidences()

def getChinese(mapping):
    char_pattern = re.compile(u'[\u4e00-\u9fff]+')
    first_char = False
    chars = []
    char_confs = []
    pinyin = []
    # ignore_first = re.search(char_pattern, mapping[0][0])
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
    # pinyin_pattern = re.compile("^(a|ai|an|ang|ao|ba|bai|ban|bang|bao|bei|ben|beng|bi|bian|biao|bie|bin|bing|bo|bu|ca|cai|can|cang|cao|ce|cen|ceng|cha|chai|chan|chang|chao|che|chen|cheng|chi|chong|chou|chu|chua|chuai|chuan|chuang|chui|chun|chuo|ci|cong|cou|cu|cuan|cui|cun|cuo|da|dai|dan|dang|dao|de|den|dei|deng|di|dia|dian|diao|die|ding|diu|dong|dou|du|duan|dui|dun|duo|e|ei|en|eng|er|fa|fan|fang|fei|fen|feng|fo|fou|fu|ga|gai|gan|gang|gao|ge|gei|gen|geng|gong|gou|gu|gua|guai|guan|guang|gui|gun|guo|ha|hai|han|hang|hao|he|hei|hen|heng|hong|hou|hu|hua|huai|huan|huang|hui|hun|huo|ji|jia|jian|jiang|jiao|jie|jin|jing|jiong|jiu|ju|juan|jue|jun|ka|kai|kan|kang|kao|ke|ken|keng|kong|kou|ku|kua|kuai|kuan|kuang|kui|kun|kuo|la|lai|lan|lang|lao|le|lei|leng|li|lia|lian|liang|liao|lie|lin|ling|liu|long|lou|lu|lv|luan|lue|lve|lun|luo|ma|mai|man|mang|mao|me|mei|men|meng|mi|mian|miao|mie|min|ming|miu|mo|mou|mu|na|nai|nan|nang|nao|ne|nei|nen|neng|ni|nian|niang|niao|nie|nin|ning|niu|nong|nou|nu|nv|nuan|nuo|nun|ou|pa|pai|pan|pang|pao|pei|pen|peng|pi|pian|piao|pie|pin|ping|po|pou|pu|qi|qia|qian|qiang|qiao|qie|qin|qing|qiong|qiu|qu|quan|que|qun|ran|rang|rao|re|ren|reng|ri|rong|rou|ru|ruan|rui|run|ruo|sa|sai|san|sang|sao|se|sen|seng|sha|shai|shan|shang|shao|she|shei|shen|sheng|shi|shou|shu|shua|shuai|shuan|shuang|shui|shun|shuo|si|song|sou|su|suan|sui|sun|suo|ta|tai|tan|tang|tao|te|teng|ti|tian|tiao|tie|ting|tong|tou|tu|tuan|tui|tun|tuo|wa|wai|wan|wang|wei|wen|weng|wo|wu|xi|xia|xian|xiang|xiao|xie|xin|xing|xiong|xiu|xu|xuan|xue|xun|ya|yan|yang|yao|ye|yi|yin|ying|yo|yong|you|yu|yuan|yue|yun|za|zai|zan|zang|zao|ze|zei|zen|zeng|zha|zhai|zhan|zhang|zhao|zhe|zhei|zhen|zheng|zhi|zhong|zhou|zhu|zhua|zhuai|zhuan|zhuang|zhui|zhun|zhuo|zi|zong|zou|zu|zuan|zui|zun|zuo)+$")
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

def refine(chars, char_confs, chi_pinyin, eng_pinyin, bid, letter_list):

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
    # x = pypinyin.pinyin('堡',heteronym=True)
    # print(chars, char_confs, chi_pinyin, eng_pinyin)
    # make sure lettering order is preserved 
    ordered = True
    to_pinyin = extract(chars)
    letter_idx = bisect.bisect(letter_list[0], bid) - 1
    letter = letter_list[1][letter_idx]
    if to_pinyin[0] != letter:
         ordered = False
        
    # valid if all characters greater than threshold
    thresh = 60
    if np.all(np.array(char_confs) > thresh):
        return chars if ordered else None

    # assume a pinyin match is high enough probability real match
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

if __name__ == "main":
    sf = 25/6
    eps = 1
    offset = 18
    pagenums = range(445+offset, 471+offset+1) #471+18 (incl.)

    standard_blocks, split_blocks, block_list, _ = getBlocks(pagenums)
    # letter_list = list(zip(*letter_list))

    letter_list = [(1, 20, 156, 293, 487, 492, 585, 758, 866, 1059, 1122, 1215, 1298, 1355, 1358, 1412, 1502, 1561, 1792, 1919, 1988, 2130, 2315), ('a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'w', 'x', 'y', 'z')]

    manual_blocks = []
    pg_cache = {}
    lesson2word = OrderedDict()
    chi_detector_multi = PyTessBaseAPI(psm=3, lang="chi_sim")
    chi_detector = PyTessBaseAPI(psm=7, lang="chi_sim")
    eng_detector_multi = PyTessBaseAPI(psm=3, lang="eng")
    eng_detector = PyTessBaseAPI(psm=7, lang="eng")

    for blocking in split_blocks:
        for block in zip(*blocking):
            pass

    total_count = missed_count = 0
    for blocking in standard_blocks:
        total_count += 1
        skip = False
        iterator = zip(*blocking) if len(blocking) > 1 else blocking
        chi_map, eng_map = [], []
        for block in iterator:
            bids, bbox = block
            # if bids[0] < 0:
            #     skip = True
            #     break
            bbox = resize(bbox, sf, [eps,0,eps,0])
            pg_num = get_page_num(block_list, block)
            if pg_num in pg_cache:
                img = pg_cache[pg_num]
            else:
                pix = doc[pg_num].getPixmap(matrix = fitz.Matrix(sf,sf))
                img = Image.open(io.BytesIO(pix.getPNGData()))
                pg_cache[pg_num] = img
            block_img = img.crop(bbox)
            # block_img.save("asd.png",dpi=(96,96))
            if len(bids) == 1:
                chi_map.extend(classify(block_img, chi_detector))
                eng_map.extend(classify(block_img, eng_detector))
            else:
                chi_map.extend(classify(block_img, chi_detector_multi))
                eng_map.extend(classify(block_img, eng_detector_multi))
        # if skip:
        #     continue
        chi_pinyin, chars, char_confs = getChinese(chi_map)
        eng_pinyin, nums = getEnglish(eng_map)
        word = refine(chars, char_confs, chi_pinyin, eng_pinyin, bids[0], letter_list)
        print(word, chars, char_confs, chi_pinyin, eng_pinyin, bids)
        if word and nums:
            lesson, pg_dest = nums
            if lesson in lesson2word:
                lesson2word[lesson].append(word)
            else:
                lesson2word[lesson] = []
        else:
            missed_count += 1
            manual_blocks.append(blocking)

    print(missed_count, total_count)

    np.save("manual_blocks", manual_blocks)
    np.save("lesson2word", lesson2word)
    np.save("block_list", block_list)
    np.save("split_blocks", split_blocks)
    np.save("pg_cache", pg_cache)