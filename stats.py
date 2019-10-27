#!/usr/bin/env python3

import os
from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

import json
import sys
import re
import string
from math import sqrt
from random import randint
import os

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './Test1-7c40fa5b9a66.json'

MAX_TIME_DELTA_MS = 4 * 60 * 60 * 1000
MAX_CONSECUTIVE_TIME_DELTA_MS = 30 * 1000
COMMON_WORDS_FILE = "100_most_common_english_words.json"
ACRONYMS_FILE = "acronyms.json"

"""if len(sys.argv) != 3:
    print("usage: ./stats.py /path/to/message.json <local_debug_boolean>")
    print("set <local_debug_boolean> to true for local debugging, anything else otherwise")
    sys.exit(0)
"""

data = None
msgs = None
user = None

LOCAL_DEBUG = True if sys.argv[1] == "true" or sys.argv[1] == "t" else False
if not LOCAL_DEBUG:
    import asyncio
    import websockets
    print("server mode init")
else:
    print("local mode init")
    data = json.loads(open(sys.argv[2]).read())
    msgs = data["messages"]
    msgs.reverse()
    user = data["participants"][1]["name"]

# list of 100 most common english words from wordfrequency.info
common_words = json.load(open(COMMON_WORDS_FILE))

# need to clean common_words
common_words_score = {}
frequencies = [common_words[i]['Frequency'] for i in range(len(common_words))]
lowest_freq = min(frequencies)
for i in range(len(common_words)):
    word = common_words[i]['Word']
    freq = common_words[i]['Frequency']
    ratio = freq / lowest_freq
    score = sqrt(1 / ratio)
    common_words_score[word] = score
# 'the' has a score of .13 while 'many' has a score of .99

# list of common acronyms
acronyms_json = json.load(open(ACRONYMS_FILE))

# clean acronyms
acronyms = {}
for key in acronyms_json.keys():
    acronyms[key] = acronyms_json[key]['expanded']

def get_sentiment(text):
    client = language.LanguageServiceClient()
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)
    try:
        sentiment = client.analyze_sentiment(document=document).document_sentiment
    except:
        return 0
    return sentiment.score

def match_sentiment(input, best_replies):
    reply_sentiments = []
    input_sentiment = get_sentiment(input)
    for reply in best_replies:
        sentiments = []
        for phrase in reply:
            sentiments.append(get_sentiment(phrase) + randint(-100, 100) / 1000)
        avg_sentiment = sum(sentiments) / len(sentiments)
        reply_sentiments.append(avg_sentiment)
    sentiment_diff = [abs(a - input_sentiment) for a in reply_sentiments]
    matching_reply_key = sentiment_diff.index(min(sentiment_diff))
    return best_replies[matching_reply_key]

def expand_acronym(word):
    if word in acronyms.keys():
        return acronyms[word]
    return word

def expand_acronyms_phrase(words):
    new_phrase = ""
    words = words.split()
    for word in words:
        new_phrase = new_phrase + " " + expand_acronym(word)
    return new_phrase

def reply(input):
    words = input.split(" ")
    best_score = 0
    best_replies = []
    counts = {} # keeps track of frequencies of each phrase
    for i in range(1,len(msgs)):
        m = msgs[i]
        if m.get("sender_name","") == user:
            score = 0
            for word in words:
                # need to "normalize" the word and the message: all lowercase and get rid of punctuation and replace acronyms
                word_normalized = expand_acronym(word.lower().translate(string.punctuation))
                if not word_normalized.isalnum() and word not in acronyms.keys():
                    continue
                curr_content_normalized = expand_acronyms_phrase(m.get("content","").lower().translate(string.punctuation))
                pattern = r"(^|[\W])"+word_normalized+r"($|[\W])" #todo: ignore special chars
                if re.findall(pattern,curr_content_normalized):
                    #print(re.findall(pattern,m.get("content","")))
                    score += common_words_score[word_normalized] if word_normalized in common_words_score.keys() else 1
            if score >= best_score:
                for j in range(len(msgs)-i):
                    m2 = msgs[i+j]
                    if m2.get("sender_name","") != user:
                        # if the time between two messages is too long, the messages
                        # are likely not realted anymore so we can just skip those cases
                        if m2.get("timestamp_ms")-m.get("timestamp_ms") <= MAX_TIME_DELTA_MS:
                            #todo: filter out "you set nickname", etc.
                            if score>best_score:
                                best_replies = []
                            # get the message block that corresponds to this matched message
                            msg_block = []

                            next_msg = msgs[i + j]
                            next_content = None
                            k = 0

                            while next_msg.get("sender_name", "") != user \
                                and next_msg.get("timestamp_ms") - m2.get("timestamp_ms") < MAX_CONSECUTIVE_TIME_DELTA_MS:
                                if next_msg.get("content"):
                                    next_content = next_msg.get("content")
                                """elif not next_content and m2.get("sticker"):
                                    if m2.get("sticker").get("uri") == "messages/stickers_used/39178562_1505197616293642_5411344281094848512_n_369239263222822.png":
                                        next_content = "*Thumbs up*"
                                    else:
                                        next_content = "*Sends sticker*"
                                elif not next_content:
                                    next_content = "*Sends pic*"
                                    """
                                k += 1
                                m2 = next_msg
                                next_msg = msgs[i + j + k]
                                msg_block.append(next_content)

                            best_replies.append(msg_block)
                            break
                best_score = score
        else:
            # other user (the one we're trying to mimic)
            curr_msg = expand_acronyms_phrase(m.get("content","").lower().translate(string.punctuation))
            if curr_msg:
                if curr_msg not in counts.keys():
                    counts[curr_msg] = 0
                else:
                    counts[curr_msg] += 1

    neg = None
    neutral = None
    pos = None
    # bounds for neutral sentiment
    upper_bound = .2
    lower_bound = -.2

    for phrase, frequency in sorted(counts.items(), key=lambda item: item[1], reverse=True):
        sentiment = get_sentiment(phrase)
        if neg and pos and neutral:
            break
        if sentiment > upper_bound and not pos:
            pos = (phrase, sentiment)
        elif sentiment < lower_bound and not neg:
            neg = (phrase, sentiment)
        elif not neutral:
            neutral = (phrase, sentiment)

    if best_score > 0:
        #reply = best_replies[randint(0,len(best_replies)-1)]
        reply = match_sentiment(input, best_replies)
        return reply
    else:
        normalized_input = expand_acronyms_phrase(input.lower().translate(string.punctuation))
        if not normalized_input:
            return ["please enter at least one word"]
        input_sentiment = get_sentiment(normalized_input)
        if input_sentiment > upper_bound:
            return [pos[0]]
        elif input_sentiment < lower_bound:
            return [neg[0]]
        else:
            return [neutral[0]]

if LOCAL_DEBUG:
    while True:
        print(reply(input()))

async def chat(websocket, path):
    print("accepted client")
    async for count in websocket:
        global data
        global msgs
        global user
        data = json.loads(open(os.getcwd()+"/message_"+count+".json").read())
        msgs = data["messages"]
        msgs.reverse()
        user = data["participants"][1]["name"]
        break
    async for msg in websocket:
        result = reply(msg)
        for phrase in result:
            await websocket.send(phrase)

start_server = websockets.serve(chat, "127.0.0.1", 8080)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
