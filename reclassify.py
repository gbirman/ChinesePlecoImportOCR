
from tkinter import *
import numpy as np 
from collections import OrderedDict
from getWords import *
import os
import PySimpleGUI as sg
from PIL import ImageTk

if __name__=='__main__':
    # retrieve data 
    manual_blocks = np.load('manual_blocks.npy', allow_pickle=True)[()]
    lesson2word = np.load('lesson2word.npy', allow_pickle=True)[()]
    block_list = np.load('block_list.npy', allow_pickle=True)[()]
    split_blocks = np.load('split_blocks.npy', allow_pickle=True)[()]
    pg_cache = np.load('pg_cache.npy', allow_pickle=True)[()]
    
    if os.path.exists("imgcache.npy"):
        imgcache = np.load('imgcache.npy', allow_pickle=True)[()]
    else: 
        imgcache = []
        for i, blocking in enumerate(manual_blocks):
            for block in zip(*blocking):
                img = getImg(block, block_list)
                imgByteArr = io.BytesIO()
                img.save(imgByteArr, format='PNG')
                imgByteArr = imgByteArr.getvalue()
                imgcache.append(imgByteArr)
        np.save("imgcache", imgcache)

    if len(imgcache) == 0:
        print('image cache is empty')
        quit()

    layout = [  [sg.Image(data=imgcache[0], key='_IMG_')],
                        [sg.Text('Enter Chinese Text'), sg.InputText(key='_TEXT_')],
                        [sg.Text('Enter Lesson Number'), sg.InputText(key='_LESSON_')],
                        [sg.Button('Prev'), sg.Button('Next'), sg.Button('OK', bind_return_key=True), sg.Button('Cancel')]
            ]
    window = sg.Window('Window', layout)
    sg.theme('DarkAmber')   # Add a touch of color


    if os.path.exists("saved.npy"):
        saved = np.load('saved.npy', allow_pickle=True)[()]
    else:
        saved = defaultdict(tuple)

    # Event Loop to process "events" and get the "values" of the inputs
    i = 0
    while True:
        event, values = window.read()
        if event == 'Prev':
            i = max(i-1, 0)
            window.Element('_IMG_').Update(data=imgcache[i])
            window.Element
        if event == 'Next':
            i = min(i+1, len(imgcache)-1)
            window.Element('_IMG_').Update(data=imgcache[i])
        elif event == 'OK':
            text = values['_TEXT_']
            if values['_LESSON_'].isnumeric():
                lesson = int(values['_LESSON_'])
                saved[i] = (lesson, text)
                with open('saved.npy', 'wb') as f:
                    np.save(f, saved)
            else:
                continue
            print(f'{lesson}: {text}')
            i += 1
            if i == len(imgcache):
                break
            window.Element('_IMG_').Update(data=imgcache[i])
        elif event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        window.Element('_LESSON_').Update('')
        window.Element('_TEXT_').Update('')
        window.Element('_TEXT_').SetFocus()
        
    window.close()
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



