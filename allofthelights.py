import time
import random
import threading
import cv2
import numpy as np
import spotipy
import spotipy.util as util

## -- Variables -- ##

random.seed()
display_img = np.zeros([100,100,3])
scope = 'user-read-playback-state'
username = 'nikhil_bhat'
keepPlaying = {}

## -- Functions -- ##

def bpm2ti(bpm):
    ''' Gets time interval between beats'''
    return 60/bpm

def rgb2img(r,g,b):
    ''' Gets an image with the given RGB values'''
    img = np.zeros([500,500,3])
    img[:,:,0] = np.ones([500,500])*b/255.0
    img[:,:,1] = np.ones([500,500])*g/255.0
    img[:,:,2] = np.ones([500,500])*r/255.0
    return img

def energy2img(nrg):
    ''' Gets an image, given an energy level'''
    # Developers are welcome to add more colors to the dictionary, as they see fit
    colors2img = {'red':rgb2img(255,0,0), 'orange':rgb2img(255,128,0), "pink": rgb2img(249, 62, 249), 'yellow':rgb2img(255,255,0),
                 'dark blue':rgb2img(0,120,0), 'blue':rgb2img(0,0,255), 'purple':(102,0,102)}
    return colors2img[energy2color(nrg)]

def energy2color(nrg):
    ''' Gets a color, given an energy level'''
    # Developers are welcome to add more energy levels, with respective colors as they see fit
    colors = {'high': ["red", "orange", "yellow", "pink"], 'low': ['blue', 'dark blue', 'purple']}
    level = 'low' if nrg < 0.5 else 'high'
    
    return random.choice(colors[level])

def displayTest(r,g,b):
    '''See what a color with the given RGB value looks like'''
    start = time.time()
    while time.time() - start < 2:
        cv2.imshow('test', rgb2img(r,g,b))
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cv2.destroyAllWindows()

## -- Threaded Classes -- ##

class colorFrames(object):
    val = None
    def __init__(self, id, interval=.001):
        self.interval = interval
        self.id = id
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):

        global display_img
        global keepPlaying
        trackObj = sp.track(self.id)
        keepPlaying[self.id] = True
        analyzed_dict = sp.audio_analysis(self.id)
        sections = analyzed_dict['sections']
        features = sp.audio_features(self.id)
        energy = features[0]['energy']
        durations = []
        tempos = []

        for section in sections:
            durations.append(section['duration'])
            tempos.append(section['tempo'])

        for i in range(len(durations)):
            start = time.time()
            while time.time() - start < durations[i]:
                display_img = energy2img(energy)
                cv2.putText(display_img,trackObj['name'], (100, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                artists = ""
                for artist in trackObj['artists']:
                    artists += artist['name'] + " "
                cv2.putText(display_img,artists, (100, 280), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
                time.sleep(bpm2ti(tempos[i]))
                if not keepPlaying[self.id]:
                    break 
            if not keepPlaying[self.id]:
                break

class getCurrentSong(object):
    val = None
    def __init__(self, sp, interval=.001):
        self.interval = interval
        self.sp = sp
        thread = threading.Thread(target=self.run, args=())
        thread.daemon = True
        thread.start()

    def run(self):
        global keepPlaying
        current_song_name = ""
        current_song_id = None
        while True:
            current_playback = self.sp.current_playback()
            current_id = current_playback['item']['id']
            current_track = self.sp.track(current_id)
            current_track_name = current_track['name']
            if current_song_name != current_track_name:
                print(current_track_name)
                if current_song_id in keepPlaying:
                    keepPlaying[current_song_id] = False
                    keepPlaying[current_id] = True
                current_song_name = current_track_name
                current_song_id = current_id
                colorFrames(current_id)

## -- Main -- ##

if __name__ == '__main__':

    token = util.prompt_for_user_token(username, scope)

    if token:
        sp = spotipy.Spotify(auth=token)
        current = sp.current_playback()

        if current is None:
            print("Not listening to anything - instead using previous song!")
            scope = 'user-read-recently-played'
            token = util.prompt_for_user_token(username, scope)
            sp2 = spotipy.Spotify(auth=token)
            recents = sp2.current_user_recently_played(limit=1)

            for val in recents['items']:
                colorFrames(val['track']['id'])
        else:
            item = current['item']
            getCurrentSong(sp)

    else:
        print("Can't get token for", username)

    while True:
        cv2.imshow('music', display_img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
