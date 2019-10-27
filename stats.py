#!/usr/bin/env python3

# import os


# # Imports the Google Cloud client library
# from google.cloud import language
# from google.cloud.language import enums
# from google.cloud.language import types


import json
import sys
import re
import string
from random import randint

# os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './Test1-7c40fa5b9a66.json'

MAX_TIME_DELTA_MS = 4 * 60 * 60 * 1000

if len(sys.argv) != 2:
    print("usage: ./stats.py /path/to/message.json")
    sys.exit(0)

data = json.loads(open(sys.argv[1]).read())
msgs = data["messages"]
msgs.reverse()

user = data["participants"][1]["name"]

# def get_sentiment(text):
#     # Instantiates a client
#     client = language.LanguageServiceClient()

#     # The text to analyze
#     #text = u'I like to fuck bitches and get money!'
#     document = types.Document(
#         content=text,
#         type=enums.Document.Type.PLAIN_TEXT)

#     # Detects the sentiment of the text
#     sentiment = client.analyze_sentiment(document=document).document_sentiment

#     #print('Text: {}'.format(text))
#     #print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))
#     return sentiment.score, sentiment.magnitude

# instead of numwords, use totalscore where each word is assigned a score based on "importance"
# dictionary for converting i'm --> I'm --> im

def reply(input):
    words = input.split(" ")
    best_num_words = 0
    best_reply = []
    for i in range(1,len(msgs)):
        m = msgs[i]
        if m.get("sender_name","") == user:
            num_words = 0
            for word in words:
                # need to "normalize" the word and the message: all lowercase and get rid of punctuation
                word_normalized = word.lower().translate(string.punctuation)
                curr_content_normalized = m.get("content","").lower().translate(string.punctuation)
                pattern = r"(^|[\W])"+word_normalized+r"($|[\W])" #todo: ignore special chars
                if re.findall(pattern,curr_content_normalized):
                    #print(re.findall(pattern,m.get("content","")))
                    num_words+=1
            if num_words>=best_num_words:
                for j in range(len(msgs)-i):
                    m2 = msgs[i+j]
                    if m2.get("sender_name","") != user:
                        # if the time between two messages is too long, the messages
                        # are likely not realted anymore so we can just skip those cases
                        if m2.get("timestamp_ms")-m.get("timestamp_ms")<=MAX_TIME_DELTA_MS:
                            #print(m.get('content'))
                            #todo: filter out "you set nickname", etc.
                            if num_words>best_num_words:
                                best_reply = []
                            best_reply.append(m2.get("content"))
                            break
                best_num_words = num_words
    if best_num_words>0:
        reply = best_reply[randint(0,len(best_reply)-1)]
        # print('Input sentiment: ' + str(get_sentiment(input)[0]))
        # print(reply)
        # return ('Reply sentiment: ' + str(get_sentiment(reply)[0]))
        return reply
    else:
        while(True):
            msg = msgs[randint(0,len(msgs)-1)]
            if msg.get("sender_name",user) != user:
                return "debug: not found"
                #return msg.get("content")

while(True):
    print(reply(input())) #TODO: serverify for tmrw

