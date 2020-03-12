import pygame
import random
import time
import speech_recognition as sr
import random

import threading
from multiprocessing import Queue
# from queue import Queue
from textblob import TextBlob
from textblob import Word
# If running on macOS, you may need to set the
# following environment variable before execution
# OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES

# Worker process: get user input
# -----------------------------------
keywords = {}
keywords['COLOR'] = ['red', 'green', 'blue']

stopgomap = {'stop': 'stop', 'go': 'go', 'pause': 'stop', 'resume': 'go', 'continue': 'go'}
bigsmallmap = {'big': 'big', 'bigger': 'big', 'large':'big', 'larger':'big', 'small': 'small', 'smaller':'small', 'increase':'big', 'decrease':'small'}
speedmap = {'increase':'fast', 'decrease':'slow', 'faster':'fast', 'slower':'slow', 'slow':'slow', 'speed':'fast'}
speedwords = ['speed', 'slow', 'down', 'up', 'faster', 'slower', 'fast', 'slow']

q_color = Queue()
q_size = Queue()
q_go = Queue()
q_speed = Queue()



def changecolor(color):
    if color == 'green':
        q_color.put((0, 255, 0))
    elif color == 'red':
        q_color.put((255, 0, 0))
    elif color == 'blue':
        q_color.put((0, 0, 255))
    else:
        print('*Error in changing color*')

def bigsmall(size, num):
    if size == 'big' and num:
        q_size.put(ball_r + int(num))
    elif size == 'big' and not num:
        q_size.put(ball_r + 15)
    elif size == 'small' and num:
        q_size.put(ball_r - int(num))
    elif size == 'small' and not num:
        q_size.put(ball_r - 15)
    elif not size and num:
        q_size.put(int(num))

def stopgo(command):
    if command == 'stop':
        q_go.put('STOP')
    elif command == 'go':
        q_go.put('GO')
    else:
        print('*Error in Stop/Go*')

def changespeed(speed, num):
    global x_vel, y_vel
    if speed == 'fast' and num:
        q_speed.put([x_vel - int(num), y_vel - int(num)])
    elif speed == 'fast' and not num:
        q_speed.put([x_vel - 15, y_vel - 15])
    elif speed == 'slow' and num:
        q_speed.put([x_vel + int(num), y_vel + int(num)])
    elif speed == 'slow' and not num:
        q_speed.put([x_vel + 15, y_vel + 15])
    elif not speed and num:
        q_speed.put([int(num), int(num)])

def decipher(text):
    tb = TextBlob(text)
    words = tb.words

    lemm = []
    for item in words:
        lemm.append(Word(item).lemmatize().lower())

    col = True
    spec = False
    speed = False
    done = False
    noinc = False
    for item in lemm:
        if item in keywords['COLOR']:
            changecolor(item)
        elif item in stopgomap.keys():
            stopgo(stopgomap[item])
        elif item in bigsmallmap.keys():
            for num in lemm:
                if num.isnumeric():
                    bigsmall(bigsmallmap[item], num)
                    spec = True
                    col = False
            if not spec:
                for x in lemm:
                    if x in speedwords:
                        noinc = True
                if not noinc:
                    bigsmall(bigsmallmap[item], None)
        elif item in speedwords and not done:
            for num in lemm:
                if num.isnumeric():
                    changespeed(speedmap[item], num)
                    speed = True
            if not speed:
                changespeed(speedmap[item], None)
                done = True

        elif item.isnumeric() and col:
            bigsmall(None,item)




def listen():
    r = sr.Recognizer()
    # sr.Microphone.list_microphone_names()
    with sr.Microphone() as source:
        print('Calibrating...')
        r.adjust_for_ambient_noise(source)
        r.energy_threshold = 150
        print('Okay, go!')
        while (1):
            # audio = r.listen(source)
            audio = r.record(source, duration=3)
            try:
                text = r.recognize_google(audio)
            except:
                unrecognized_speech_text = 'Sorry, I didn\'t catch that.'
                text = unrecognized_speech_text
            print(text)
            decipher(text)
            # TODO: use the extracted text to add
            # the correct next actions to the queue
            # q_size.put(random.choice([100, 50]))
            # q_color.put(random.choice([(255, 0, 0), (0, 0, 255)]))
            # q_go.put(random.choice(['STOP', 'GO']))


# Main execution loop
# -----------------------------------

SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()

ball_x = random.randint(0, SCREEN_WIDTH)
ball_y = random.randint(0, SCREEN_HEIGHT)
ball_r = 50
MAX_VEL = 10
x_vel = -MAX_VEL
y_vel = -MAX_VEL

delta_r = 0
ball_color = (255, 0, 0)

listener = threading.Thread(target=listen)
listener.start()

done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True

    # Check for new commands from user
    try:
        ball_color = q_color.get(block=False, timeout=0.1)
    except:
        pass
    try:
        ball_r = q_size.get(block=False, timeout=0.1)
    except:
        pass
    try:
        stop_go = q_go.get(block=False, timeout=0.1)
        x_vel = MAX_VEL if stop_go == 'GO' else 0
        y_vel = MAX_VEL if stop_go == 'GO' else 0
    except:
        pass
    try:
        updated_speed = q_speed.get(block=False, timeout=0.1)
        x_vel = updated_speed[0]
        y_vel = updated_speed[1]
    except:
        pass

    # Move the ball
    ball_x += x_vel
    ball_y += y_vel
    ball_r += delta_r

#TODO: fix the speed - what the heck is going on with the velocity? also set speed
#TODO: breaks on decrease speed

#TODO: add easter egg
#TODO: recheck all commands
    # If the ball hit the wall, reverse direction
    if ball_x + ball_r > SCREEN_WIDTH: x_vel = -x_vel
    if ball_x - ball_r < 0: x_vel = -x_vel
    if ball_y + ball_r > SCREEN_HEIGHT: y_vel = -y_vel
    if ball_y - ball_r < 0: y_vel = -y_vel

    # Update the screen
    # screen.fill((0,0,0))    # clear all previously drawn images
    pygame.draw.circle(screen, ball_color, (ball_x, ball_y), ball_r)
    pygame.display.flip()  # updates the display
    pygame.draw.circle(screen, (0, 0, 0), (ball_x, ball_y), ball_r)

    clock.tick(60)  # pauses execution until 1/60 seconds
    # have passed since the last tick