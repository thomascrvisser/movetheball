import speech_recognition as sr
r = sr.Recognizer()

import pyttsx3
engine = pyttsx3.init()
from time import sleep
import json

import nltk
nltk.download('punkt')

import requests
from bs4 import BeautifulSoup

import random
import spacy
import numpy as np
from scipy import spatial
from textblob import TextBlob
from textblob import Word


# print("Loading language model...")
# nlp = spacy.load('en_core_web_md')

intents = ['DIRECTIVE',  'INFO_REQUEST', 'CONV_INQUIRY', 'CONV_OFFER',
            'APPROVAL', 'DISAPPROVAL']

keywords = {}
keywords['DIRECTIVE'] = ["turn on the lights", "Open the door", "Go right at the intersection",
                         "Buy some cupcakes while you're at the store", "Would you turn the lights down please",
                         "Stop", "Stop right there", "please don't do that again", "turn up the volume", "add milk to the shopping list, would you",
                         "eat your vegetables", "don't knock over the vase", "can you pour me a glass of milk please", "i want you to paint this wall blue"]
keywords['INFO_REQUEST'] = ['who', 'what', 'when', 'where', 'why', 'how', 'which', 'tell', 'would', 'can', 'do']
keywords['CONV_INQUIRY'] = ['your', 'you', 'me']
keywords['CONV_OFFER'] = ['i', 'my', 'am']
keywords['APPROVAL'] = ['joy','happy','awesome','cool','satisfied','amazing',
                        'wow','great','wonderful','sweet','love','favorite','good',
                        'haha','funny','like','awesome', 'ha','yeah','score']
keywords['DISAPPROVAL'] = ['angry','mad','stupid','terrible','hate','trash','bad','awful','dumb',
                           'frustrating','annoying','disgust', 'ugly', 'gross','nasty','weird',
                           'uncomfortable','hideous','inappropriate','uncanny','creepy','freaky',
                           'disturbing','traumatizing', 'not']

# expression of approval.txt - do similar thing we did with joy
# expression of disapproval.txt - do similar thing we did with anger/disgust

def get_conv_offer_score(text):
    testimonial = TextBlob(text)
    return testimonial.sentiment.subjectivity

# if the sentence has words in info_request.txt AND conv inquiry, then it's probably conv inquiry
# if the sentence has words in info_request.txt AND NOT conv inquiry, then it's info_request.txt (look for objectivity)
def conv_inquiry_info_request_test(text):
    tb = TextBlob(text)
    words = tb.words

    lemm = []
    for item in words:
        lemm.append(Word(item).lemmatize().lower())

    ir = False
    ci = False
    for item in lemm:
        if item in keywords['INFO_REQUEST']:
            ir = True
        if item in keywords['CONV_INQUIRY']:
            ci = True

    if ir and ci:
        return 3
# look for objectivity
    if ir and not ci:
        # if tb.sentiment.subjectivity < .8:
        #seems to work better without this
        return 2

    return 0

# if the sentence has a verb then it's directive.txt
def directive_test(text):
    tb = TextBlob(text)
    # words = tb.words
    tags = tb.tags

    for item in tags:
        if item[1] in ['VB','VBG'] and item[0].lower() != 'tell' or item[0].lower() == 'turn':
            return 1
    return 0

# conv_offer.txt look for highly subjective sentences with a mix of I/my
def conv_offer_test(text):
    tb = TextBlob(text)
    words = tb.words

    lemm = []
    for item in words:
        lemm.append(Word(item).lemmatize().lower())

    co = False
    for item in lemm:
        if item in keywords['CONV_OFFER']:
            co = True

    # if tb.sentiment.subjectivity > .2 and co:
    if co:
        return 4
    return 0

def approved(words):
    for item in words:
        if item in keywords['APPROVAL']:
            return True

def disapproved(words):
    for item in words:
        if item in keywords['DISAPPROVAL']:
            return True

def approve_disapprove_test(text):
    tb = TextBlob(text)
    words = tb.words
    lemm = []
    for item in words:
        lemm.append(Word(item).lemmatize().lower())

    if tb.sentiment.polarity > 0 or approved(lemm):
        return 5
    elif tb.sentiment.polarity < .2 or disapproved(lemm):
        return 6
    return 0

def detectIntent(text):

    first = conv_inquiry_info_request_test(text)
    if first:
        return first

    second = directive_test(text)
    if second:
        return second

    third = conv_offer_test(text)
    if third:
        return third

    fourth = approve_disapprove_test(text)
    if fourth:
        return fourth

    return 0

def bsoup(SEARCH_PHRASE):
    # create search query

    sleep(0.75)


    url = f'https://api.duckduckgo.com/?q="{SEARCH_PHRASE}"&format=json'

    response = requests.get(url)
    plain_text = response.text

    try:
        response_object = json.loads(plain_text)
    except:
        sleep(4)
        return 'DuckDuckGo thinks you should take a break and see other people. (Try not to send so many requests)'
    output = ''
    if response_object['Abstract']:
        output = response_object['AbstractSource'] + ' says that ' + response_object['AbstractText']
    if len(output.split()) > 30:
        output = output[:output.find('.')] + '...'
    if len(output) > 200:
        output = output[:200] + '...'
    elif response_object['RelatedTopics']:
        output = 'DuckDuckGo says that ' + response_object['RelatedTopics'][0]['Text']
    else:
        output = 'No data found for ' + SEARCH_PHRASE

    return output

def respond(text):
    detectedIntent = detectIntent(text)

    # 0: didn't get categorized
    # 1: Directive
    # 2: Request of objective info
    # 3: conversational inquiry
    # 4: conversational offer of information
    # 5: expression of approval
    # 6: expression of disapproval
    rmap = {0:"I haven't the slightest of what you said", 1: "Ok, I'll do that", 2: "BSoup", 3:"I will now tell you something interesting about myself",
            4: "That's cool", 5: "I'm glad you approve", 6: "I'm sorry you are unhappy"}
    # rmap = {0:"Nope:", 1: "Directive:", 2: "Info_Req:", 3:"Conv_Inquiry:",
    #         4: "Conv_offer:", 5: "Approval:", 6: "Disapproval:"}
    response = rmap[detectedIntent]
    if response == 'BSoup':
        response = bsoup(text.lower().strip('\n'))

    return response


def CountFrequency(my_list):
    # Creating an empty dictionary
    freq = {}
    for items in my_list:
        freq[items] = my_list.count(items)

    for key, value in freq.items():
        print("%s : % d" % (key, value))

if __name__=='__main__':
    # f = open("info_request.txt", "r")
    # answers = []
    # for line in f:
    #     ans = respond(line)
    #     answers.append(ans)
    #     print(ans, str(line))
    # CountFrequency(answers)

    with sr.Microphone() as source:

        r.adjust_for_ambient_noise(source)
        r.energy_threshold = 150
        print("Say something")
        audio = r.listen(source)
        # audio = r.record(source, duration=5)
        text = r.recognize_google(audio)
        response = respond(text)
        engine.say(response)
        engine.runAndWait()