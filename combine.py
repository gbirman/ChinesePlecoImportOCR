
import os
from collections import OrderedDict
import numpy as np  
from pypinyin import lazy_pinyin

if __name__=='__main__':

    # load manually saved dictionary
    # maps: gid -> (lesson, word)

    if os.path.exists("saved_manual.npy"):
        saved_manual = np.load('saved_manual.npy', allow_pickle=True)[()]
    else:
        print("make sure saved_manual.npy exists")
        quit()

    # load OCR saved dictionary
    # maps: lesson -> word
    if os.path.exists("lesson2word.npy"):
        lesson2word = np.load('lesson2word.npy', allow_pickle=True)[()]
    else: 
        print("make sure lesson2word.npy exists")
        quit()

    # aggregate manual
    for lesson, word in saved_manual.values():
        lesson2word[lesson].append(word)

    ##### CUSTOM MODIFICATIONS #######
    ### flagged
    lesson2word[1].append('关系')
    lesson2word[29].append('关系')
    lesson2word[32].append('婚外关系')
    lesson2word[44].append('角')
    lesson2word[3].append('角度')
    lesson2word[36].append('联系')
    lesson2word[16].append('奶奶')
    lesson2word[41].append('日子')
    lesson2word[20].append('如果')
    lesson2word[38].append('申请')
    lesson2word[22].append('天安门')
    lesson2word[41].append('污染')
    lesson2word[40].append('衣食住行')
    lesson2word[2].append('一切')
    lesson2word[46].append('有用')
    ### incorrect 
    # NOTE: I'm only consistently doing it for 
    # lessons I haven't added manually beforehand, i.e. lesson num. > 30
    lesson2word[3].remove('除了。。。以外')
    lesson2word[3].append('除了...以外')
    lesson2word[21].remove('遵宁')
    lesson2word[21].append('遵守')
    lesson2word[44].remove('毕竞')
    lesson2word[44].append('毕竟')
    lesson2word[39].remove('可了')
    lesson2word[39].append('可耻')
    lesson2word[39].remove('退体')
    lesson2word[39].append('退休')
    lesson2word[39].remove('自二以来')
    lesson2word[39].append('自古以来')
    lesson2word[46].remove('词江')
    lesson2word[46].append('词汇')
    lesson2word[48].remove('竞')
    lesson2word[48].append('竟')
    #### page not included ####
    lesson2word[48].append('国力')
    lesson2word[48].append('强盛')
    lesson2word[48].append('朝代')
    lesson2word[48].append('吸收')
    lesson2word[48].append('汉朝')
    lesson2word[48].append('丝绸之路')
    lesson2word[48].append('引进')
    lesson2word[48].append('中亚')
    lesson2word[48].append('西亚')
    lesson2word[48].append('葡萄')
    lesson2word[48].append('胡瓜')
    lesson2word[48].append('黄瓜')
    lesson2word[48].append('胡琴')
    lesson2word[48].append('乐器')

    # sort keys (i.e. orders lessons)
    lesson2word = OrderedDict(sorted(lesson2word.items()))

    # remove text file if exists
    if os.path.exists("flashcards.txt"):
        os.remove("flashcards.txt")

    # create flashcards
    for lesson, words in lesson2word.items(): 
        if lesson <= 30:
            continue
        # sort by alphabetical pinyin
        words.sort(key = lambda chars : ' '.join(lazy_pinyin(chars))) 
        # write to text file
        with open('flashcards.txt', 'a') as wfile:
            wfile.write(f'\n//Lesson {lesson} 107\n')
            for word in words:
                wfile.write(f'{word}\n')