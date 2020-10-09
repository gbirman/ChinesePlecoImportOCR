
import numpy as np 
from OCR import *
import os
import PySimpleGUI as sg
import bisect

# returns set of images that haven't been saved/flagged yet
def unprocessed_set(img_cache, saved_manual, flagged):
    return img_cache.keys() - saved_manual.keys() - flagged

# number of unprocesssed images
def num_to_go(img_cache, saved_manual, flagged):
    inter_set = unprocessed_set(img_cache, saved_manual, flagged)
    return len(inter_set)

# gid of next unprocessed image
def next_index(img_cache, saved_manual, flagged):
    inter_set = unprocessed_set(img_cache, saved_manual, flagged)
    if len(inter_set) == 0:
        return -1
    return next(iter(inter_set))

# return the status of a given image 
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

# smallest value in iterable a larger than target
def min_target(a, target):
    check = curr = np.inf
    for val in a:
        if val > target and val < curr:
            curr = val 
    # wrap-around
    if curr == check: 
        curr = min(a)
    return curr 

# largest value in iterable a smaller than target
def max_target(a, target):
    check = curr = -np.inf
    for val in a:
        if val < target and val > curr:
            curr = val 
    # wrap-around
    if curr == check: 
        curr = max(a)
    return curr 



if __name__=='__main__':

    # retrieve words that need to be determined manually
    if os.path.exists("manual_words.npy"):
        manual_words = np.load('manual_words.npy', allow_pickle=True)[()]
    else:
        print("make sure manual_words.npy exists")
        quit()

    # load/save images in a format PySimpleGUI accepts
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

    # check there are images to iterate on
    if not img_cache:
        print('image cache is empty')
        quit()

    key_list = list(img_cache.keys()) # list of gids to iterate on

    # load flagged word (gid) 
    if os.path.exists("flagged.npy"):
        flagged = np.load('flagged.npy', allow_pickle=True)[()]
    else:
        flagged = set()

    # load saved words
    if os.path.exists("saved_manual.npy"):
        saved_manual = np.load('saved_manual.npy', allow_pickle=True)[()]
    else:
        saved_manual = defaultdict(tuple)

    # starting index (next unprocessed image)
    gid = next_index(img_cache, saved_manual, flagged)

    toggle_flag = False # iterate through unprocessed vs. flagged

    # start at first image if all words processed
    if gid == -1:
        gid = key_list[0]
        print('All words have been saved or flagged.')

    # display strings 
    remain_string = lambda: f'{num_to_go(img_cache, saved_manual, flagged)}/{len(img_cache)} words left.'
    index_string = lambda: f'Viewing item: {gid}. {get_status(gid, saved_manual, flagged)}'
    toggle_string = lambda: f'Iterate Through Flagged: {toggle_flag}'

    # initial view
    sg.theme('DarkAmber')   # Add a touch of color
    layout = [  [sg.Image(data=img_cache[gid], key='_IMG_')],
                        [sg.Text('Enter Chinese Text'), sg.InputText(key='_TEXT_')],
                        [sg.Text('Enter Lesson Number'), sg.InputText(key='_LESSON_')],
                        [sg.Button('Prev'), sg.Button('Next'), sg.Button('OK', bind_return_key=True), sg.Button('Return'), sg.Button('Flag'), sg.Button('Cancel'), sg.Text(remain_string(), key='_REM_')],
                        [sg.Text(toggle_string(), key='_TOGGLE_'), sg.Button('Toggle')],
                        [sg.Multiline(index_string(), key='_IDX_')],
            ]
    window = sg.Window('Window', layout)

    # GUI event loop
    while True:
        event, values = window.read()
        if event == 'Prev': # go to previous image (in order, regardless of status)
            if toggle_flag:
                gid = max_target(flagged, gid)
            else:
                curr_idx = bisect.bisect_left(key_list, gid)
                assert(key_list[curr_idx] == gid)
                gid = key_list[max(curr_idx-1, 0)]
        if event == 'Next': # go to next image (in order, regardless of status)
            if toggle_flag:
                gid = min_target(flagged, gid)
            else: 
                curr_idx = bisect.bisect_left(key_list, gid)
                assert(key_list[curr_idx] == gid)
                gid = key_list[min(curr_idx+1, len(img_cache)-1)]
        elif event == 'Return': # go to next unprocessed image
            gid = next_index(img_cache, saved_manual, flagged)
        elif event == 'Flag': # flag word 
            print(f'FLAGGED {gid}')
            flagged.add(gid)
            with open('flagged.npy', 'wb') as f:
                np.save(f, flagged)
            gid = next_index(img_cache, saved_manual, flagged)
        elif event == 'Toggle':
            toggle_flag = not toggle_flag
            if toggle_flag:
                gid = min(flagged)
            else: 
                gid = next_index(img_cache, saved_manual, flagged)
        elif event == 'OK': # save word
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
            gid = next_index(img_cache, saved_manual, flagged)
        elif event == sg.WIN_CLOSED or event == 'Cancel': # if user closes window or clicks cancel
            break
        if gid == -1: # start at first image
            gid = key_list[0]
            print('All words have been saved or flagged.')
        window.Element('_REM_').Update(remain_string())
        window.Element('_IDX_').Update(index_string())
        window.Element('_IMG_').Update(data=img_cache[gid])
        window.Element('_LESSON_').Update('')
        window.Element('_TEXT_').Update('')
        window.Element('_TOGGLE_').Update(toggle_string())
        window.Element('_TEXT_').SetFocus()
        
    window.close()
