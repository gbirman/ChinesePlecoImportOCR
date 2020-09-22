
from tkinter import *
import numpy as np 
from collections import OrderedDict
from getWords import *
import os
import PySimpleGUI as sg
from PIL import ImageTk
import bisect

if __name__=='__main__':
    # # retrieve data 
    # standard_blocks = np.load('standard_blocks.npy', allow_pickle=True)[()]
    # lesson2word = np.load('lesson2word.npy', allow_pickle=True)[()]
    # block_list = np.load('block_list.npy', allow_pickle=True)[()]
    # split_blocks = np.load('split_blocks.npy', allow_pickle=True)[()]
    # pg_cache = np.load('pg_cache.npy', allow_pickle=True)[()]
    manual_words = np.load('manual_words.npy', allow_pickle=True)[()]
    if os.path.exists("img_cache.npy"):
        img_cache = np.load('img_cache.npy', allow_pickle=True)[()]
    else: 
        img_cache = {}
        for word in manual_words:
            for group in word['groups']:
                gid, pg, bbox = group['gid'], group['pg'], group['bbox']
                print(f'Processing: {gid}')
                img = getImg(pg, bbox)
                imgByteArr = io.BytesIO()
                img.save(imgByteArr, format='PNG')
                imgByteArr = imgByteArr.getvalue()
                img_cache[gid] = imgByteArr
        np.save("img_cache", img_cache)

    if not img_cache:
        print('image cache is empty')
        quit()

    key_list = list(img_cache.keys())

    def unprocessed_set(saved_manual, flagged):
        return img_cache.keys() - saved_manual.keys() - flagged

    def num_to_go(saved_manual, flagged):
        inter_set = unprocessed_set(saved_manual, flagged)
        return len(inter_set)

    def next_index(saved_manual, flagged):
        inter_set = unprocessed_set(saved_manual, flagged)
        if len(inter_set) == 0:
            return -1
        return next(iter(inter_set))

    def get_status(gid, saved_manual, flagged): 
        from enum import Enum
        class Status(Enum):
            SAVE = 'Item saved.'
            FLAG = 'Item flagged.'
            PROCESSING = 'No operations performed.'

        if gid in saved_manual.keys():
            return repr(Status.SAVE)
        elif gid in flagged:
            return repr(Status.FLAG)
        
        return repr(Status.PROCESSING)

    if os.path.exists("flagged.npy"):
        flagged = np.load('flagged.npy', allow_pickle=True)[()]
    else:
        flagged = set()

    if os.path.exists("saved_manual.npy"):
        saved_manual = np.load('saved_manual.npy', allow_pickle=True)[()]
    else:
        saved_manual = defaultdict(tuple)

    # starting index
    gid = next_index(saved_manual, flagged)

    # all words processed
    if gid == -1:
        gid = key_list[0]
        print('All words have been saved or flagged.')

    # display strings 
    remain_string = lambda: f'{num_to_go(saved_manual, flagged)}/{len(img_cache)} words left.'
    index_string = lambda: f'Viewing item: {gid}. {get_status(gid, saved_manual, flagged)}'

    # initial view
    sg.theme('DarkAmber')   # Add a touch of color
    layout = [  [sg.Image(data=img_cache[gid], key='_IMG_')],
                        [sg.Text('Enter Chinese Text'), sg.InputText(key='_TEXT_')],
                        [sg.Text('Enter Lesson Number'), sg.InputText(key='_LESSON_')],
                        [sg.Button('Prev'), sg.Button('Next'), sg.Button('OK', bind_return_key=True), sg.Button('Return'), sg.Button('Flag'), sg.Button('Cancel'), sg.Text(remain_string(), key='_REM_')],
                        [sg.Text(index_string(), key='_IDX_')],
                        [sg.Text('')]
            ]
    window = sg.Window('Window', layout)

    # Event Loop to process "events" and get the "values" of the inputs
    while True:
        event, values = window.read()
        if event == 'Prev':
            curr_idx = bisect.bisect_left(key_list, gid)
            assert(key_list[curr_idx] == gid)
            gid = key_list[max(curr_idx-1, 0)]
        if event == 'Next':
            curr_idx = bisect.bisect_left(key_list, gid)
            assert(key_list[curr_idx] == gid)
            gid = key_list[min(curr_idx+1, len(img_cache)-1)]
        elif event == 'Return':
            gid = next_index(saved_manual, flagged)
            if gid == -1:
                gid = key_list[0]
                print('All words have been saved or flagged.')
        elif event == 'Flag':
            print(f'FLAGGED {gid}')
            flagged.add(gid)
            with open('flagged.npy', 'wb') as f:
                np.save(f, flagged)
            gid = next_index(saved_manual, flagged)
            if gid == -1:
                gid = key_list[0]
                print('All words have been saved or flagged.')
        elif event == 'OK':
            text = values['_TEXT_']
            if values['_LESSON_'].isnumeric():
                lesson = int(values['_LESSON_'])
                saved_manual[gid] = (lesson, text)
                # modify this to async/append if too slow
                with open('saved_manual.npy', 'wb') as f:
                    np.save(f, saved_manual)
            else:
                continue
            print(f'SAVED {gid}: {lesson} --> {text}')
            gid = next_index(saved_manual, flagged)
            if gid == -1:
                gid = key_list[0]
                print('All words have been saved or flagged.')
        elif event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        window.Element('_REM_').Update(remain_string())
        window.Element('_IDX_').Update(index_string())
        window.Element('_IMG_').Update(data=img_cache[gid])
        window.Element('_LESSON_').Update('')
        window.Element('_TEXT_').Update('')
        window.Element('_TEXT_').SetFocus()
        
    window.close()
    quit()

    # print(manual_words[0])
    # print(block_list[11])
    # print(get_page_num(block_list, manual_words[0][0]))

    # # sort keys 
    # lesson2word = OrderedDict(sorted(lesson2word.items())) 

    # print(len(lesson2word[1]))
    # print(np.unique(lesson2word[1]))

    # # iterate through key-value pairs 
    # for k, v in lesson2word.items():
    #     print(k)

    # with open('flashcards.txt', 'a') as wfile:
    #     for lesson, words in lesson2word:
    #         wfile.write(f'\n//Lesson {lesson}\n')
    #         for word in words:
    #             wfile.write(f'{word}\n')


imgcache = np.load('imgcache.npy', allow_pickle=True)[()]
img_set = set()
unique_idx = set()
for idx, img in enumerate(imgcache):
    if img not in img_set:
        unique_idx.add(idx)
    else:
        img_set.add(img)

old2new = {}


count = 0
idx2gid = {}
for gid, img1 in img_cache.items():
    for idx, img2 in enumerate(imgcache):
        if img1 == img2:
            idx2gid[idx] = gid
            break
    



import os
if os.path.exists("vision.txt"):
    os.remove("vision.txt")
ab = list(chain.from_iterable(lesson2word.values()))
ab.sort(key = lambda x : ' '.join(lazy_pinyin(x)))
for item in ab:   
    py = ' '.join(lazy_pinyin(item))
    with open('vision.txt', 'a') as f:
        f.write(f'{py}, {item}\n')

idx2gid = {0: 7, 1: 18, 2: 21, 3: 23, 4: 27, 5: 29, 6: 32, 7: 44, 8: 49, 9: 50, 10: 51, 11: 52, 12: 53, 13: 66, 14: 67, 15: 72, 16: 74, 17: 78, 18: 88, 19: 94, 20: 95, 21: 102, 22: 110, 23: 128, 24: 129, 25: 132, 26: 133, 27: 137, 28: 139, 29: 142, 30: 144, 31: 152, 32: 160, 33: 162, 34: 163, 35: 166, 36: 168, 37: 171, 38: 173, 39: 180, 40: 188, 41: 191, 42: 192, 43: 195, 44: 209, 45: 223, 46: 231, 47: 232, 48: 241, 49: 246, 50: 247, 51: 255, 52: 256, 53: 261, 54: 270, 55: 274, 56: 275, 57: 285, 58: 290, 59: 303, 60: 305, 61: 311, 62: 312, 63: 325, 64: 329, 65: 333, 66: 334, 67: 335, 68: 345, 69: 346, 70: 360, 71: 364, 72: 367, 73: 371, 74: 377, 75: 382, 76: 383, 77: 386, 78: 388, 79: 389, 80: 391, 81: 392, 82: 393, 83: 395, 84: 398, 85: 423, 86: 424, 87: 429, 88: 439, 89: 442, 90: 443, 91: 450, 92: 451, 93: 454, 94: 455, 95: 457, 96: 461, 97: 464, 98: 466, 99: 471, 100: 472, 101: 499, 102: 504, 103: 507, 104: 511, 105: 512, 106: 513, 107: 514, 108: 519, 109: 520, 110: 521, 111: 523, 112: 529, 113: 530, 114: 533, 115: 541, 116: 550, 117: 551, 118: 552, 119: 568, 120: 578, 121: 581, 122: 611, 123: 614, 124: 620, 125: 621, 126: 625, 127: 626, 128: 628, 129: 630, 130: 643, 131: 647, 132: 648, 133: 649, 134: 654, 135: 659, 136: 663, 137: 672, 138: 678, 139: 681, 140: 684, 141: 692, 142: 694, 143: 695, 144: 697, 145: 698, 146: 700, 147: 714, 148: 716, 149: 718, 150: 719, 152: 726, 153: 728, 154: 729, 155: 732, 156: 752, 157: 753, 158: 781, 159: 783, 160: 784, 161: 785, 162: 786, 163: 792, 164: 799, 151: 723, 165: 804, 166: 806, 167: 808, 168: 809, 169: 814, 170: 817, 171: 818, 172: 833, 173: 839, 174: 844, 175: 845, 176: 848, 177: 851, 178: 852, 179: 853, 180: 857, 181: 865, 182: 867, 183: 871, 184: 879, 185: 880, 186: 881, 187: 882, 188: 884, 189: 888, 190: 893, 191: 897, 192: 900, 193: 903, 194: 907, 195: 910, 196: 911, 197: 912, 198: 913, 199: 919, 200: 929, 201: 932, 202: 933, 203: 934, 204: 937, 205: 940, 206: 941, 207: 944, 208: 945, 209: 950, 210: 951, 211: 953, 212: 957, 213: 966, 214: 967, 215: 969, 216: 974, 217: 981, 218: 982, 219: 989, 220: 998, 221: 1000, 222: 1002, 223: 1004, 224: 1011, 225: 1015, 226: 1018, 227: 1022, 228: 1028, 229: 1036, 230: 1039, 231: 1045, 232: 1049, 233: 1054, 234: 1078, 235: 1080, 236: 1081, 237: 1086, 238: 1090, 239: 1092, 240: 1100, 241: 1104, 242: 1109, 243: 1121, 244: 1126, 245: 1129, 246: 1134, 247: 1139, 248: 1144, 249: 1152, 250: 1158, 251: 1164, 253: 1168, 254: 1170, 255: 1172, 256: 1174, 257: 1184, 258: 1186, 259: 1187, 260: 1188, 261: 1189, 262: 1193, 263: 1194, 264: 1199, 265: 1201, 266: 1202, 267: 1211, 268: 1221, 269: 1224, 270: 1230, 252: 1165, 271: 1239, 272: 1240, 273: 1249, 274: 1253, 275: 1255, 276: 1259, 277: 1260, 278: 1265, 279: 1280, 280: 1285, 281: 1286, 282: 1288, 283: 1289, 284: 1290, 285: 1292, 286: 1295, 287: 1297, 288: 1300, 289: 1301, 290: 1307, 291: 1312, 292: 1314, 293: 1318, 294: 1320, 295: 1322, 296: 1323, 297: 1325, 298: 1332, 299: 1333, 300: 1338, 301: 1342, 302: 1348, 303: 1349, 304: 1356, 305: 1363, 306: 1364, 307: 1365, 308: 1368, 309: 1369, 310: 1377, 311: 1383, 312: 1388, 313: 1392, 314: 1396, 315: 1402, 316: 1404, 317: 1413, 318: 1424, 319: 1427, 320: 1429, 321: 1433, 322: 1441, 324: 1444, 325: 1446, 326: 1449, 327: 1456, 328: 1462, 329: 1464, 330: 1465, 331: 1466, 332: 1475, 333: 1478, 334: 1479, 335: 1483, 336: 1485, 337: 1487, 338: 1492, 339: 1496, 340: 1502, 341: 1503, 342: 1506, 343: 1507, 344: 1515, 323: 1443, 346: 1521, 347: 1525, 348: 1534, 349: 1536, 350: 1537, 351: 1551, 352: 1553, 353: 1557, 354: 1563, 355: 1565, 356: 1567, 357: 1571, 358: 1575, 359: 1578, 360: 1580, 361: 1585, 362: 1592, 363: 1593, 364: 1594, 345: 1519, 365: 1606, 366: 1608, 367: 1609, 368: 1625, 369: 1633, 370: 1639, 371: 1644, 372: 1645, 373: 1647, 374: 1660, 375: 1661, 376: 1664, 377: 1670, 378: 1684, 379: 1688, 380: 1690, 381: 1703, 382: 1709, 383: 1717, 384: 1720, 385: 1722, 386: 1723, 387: 1725, 388: 1726, 389: 1728, 390: 1729, 391: 1744, 392: 1745, 393: 1746, 394: 1750, 395: 1753, 396: 1759, 397: 1761, 398: 1772, 399: 1777, 400: 1779, 401: 1784, 402: 1786, 403: 1791, 404: 1804, 405: 1809, 406: 1823, 407: 1833, 408: 1834, 409: 1844, 410: 1849, 411: 1853, 412: 1863, 413: 1876, 414: 1880, 415: 1881, 416: 1885, 417: 1887, 418: 1890, 419: 1898, 420: 1904, 421: 1907, 422: 1908, 423: 1909, 424: 1921, 425: 1924}
saved_manual = {}
for idx, pair in manual_pairs.items():
    saved_manual[idx2gid[idx]] = pair
with open('saved_manual.npy', 'wb') as f:
    np.save(f, saved_manual)

flagged_list = list(flagged)
tmp = set()
for i, idx in enumerate(flagged_list):
    if idx in idx2gid:
        tmp.add(idx2gid[idx])
flagged = tmp
with open('flagged.npy', 'wb') as f:
    np.save(f, flagged)

