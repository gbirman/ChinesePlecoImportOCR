
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

    # sort keys 
    lesson2word = OrderedDict(sorted(lesson2word.items()))

    for lesson, words in lesson2word.items(): 
        # sort by alphabetical pinyin
        words.sort(key = lambda chars : ' '.join(lazy_pinyin(chars))) 
        # write to text file
        with open('flashcards_test.txt', 'a') as wfile:
            wfile.write(f'\n//Lesson {lesson}\n')
            for word in words:
                wfile.write(f'{word}\n')


    print(lesson2word)
    quit()

    print(len(lesson2word[1]))
    print(np.unique(lesson2word[1]))

    quit()

    # iterate through key-value pairs 
    for k, v in lesson2word.items():
        print(k)

    with open('flashcards.txt', 'a') as wfile:
        for lesson, words in lesson2word:
            wfile.write(f'\n//Lesson {lesson}\n')
            for word in words:
                wfile.write(f'{word}\n')