
from tkinter import *
import numpy as np 
from collections import OrderedDict
from getWords import *
import os

if __name__=='__main__':
    # retrieve data 
    manual_blocks = np.load('manual_blocks.npy', allow_pickle=True)[()]
    lesson2word = np.load('lesson2word.npy', allow_pickle=True)[()]
    block_list = np.load('block_list.npy', allow_pickle=True)[()]
    split_blocks = np.load('split_blocks.npy', allow_pickle=True)[()]
    pg_cache = np.load('pg_cache.npy', allow_pickle=True)[()]

    # import from other module
    filename = "/Users/gabrielbirman/Chinese_OCR/107Textbook.pdf"
    doc = fitz.open(filename)
    sf = 25/6
    eps = 1

    # pix = doc[pg_num].getPixmap(matrix = fitz.Matrix(sf,sf))
    # img = Image.open(io.BytesIO(pix.getPNGData()))
    # pg_cache[pg_num] = img
    # block_img = img.crop(bbox)
    # block_img.save("asd.png",dpi=(96,96))

    split_block = split_blocks[2]
    split_block[0] = [[split_block[0][0], split_block[0][1]], split_block[0][2]]
    
    blocking = split_blocks[2]
    iterator = zip(*blocking) if len(blocking) > 1 else blocking
    print(manual_blocks[0])
    quit()
    print(list(iterator))
    quit()

    # update incorrectly detected blocks manually
    for i, blocking in enumerate(manual_blocks):
        iterator = zip(*blocking) if len(blocking) > 1 else blocking
        print(list_iterator)
        for block in zip(*blocking):
            saveBlock(block, "~/test/")
        print('********')
        quit()

    # print(manual_blocks[0])
    # print(block_list[11])
    # print(get_page_num(block_list, manual_blocks[0][0]))

    # sort keys 
    lesson2word = OrderedDict(sorted(lesson2word.items())) 

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



