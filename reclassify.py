
from tkinter import *
import numpy as np 
from collections import OrderedDict
from getWords import *

# retrieve data 
manual_blocks = np.load('manual_blocks.npy', allow_pickle=True)[()]
lesson2word = np.load('lesson2word.npy', allow_pickle=True)[()]
block_list = np.load('block_list.npy', allow_pickle=True)[()]
split_blocks = np.load('split_blocks.npy', allow_pickle=True)[()]

print(split_blocks[0])
quit()

# 
for blocking in manual_blocks:
    iterator = zip(*blocking) if len(blocking) > 1 else blocking
    for block in iterator:
        bids, bbox = block
        print(bids, bbox)


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


