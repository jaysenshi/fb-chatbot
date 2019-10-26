#!/usr/bin/python3

import json
import sys
import re
from random import randint

MAX_TIME_DELTA_MS = 4 * 60 * 60 * 1000

if len(sys.argv) != 2:
    print("usage: ./stats.py /path/to/message.json")
    sys.exit(0)

data = json.loads(open(sys.argv[1]).read())
msgs = data["messages"]
msgs.reverse()

user = data["participants"][1]["name"]

def reply(input):
    words = input.split(" ")
    best_num_words = 0
    best_reply = []
    for i in range(1,len(msgs)):
        m = msgs[i]
        if m.get("sender_name","") == user:
            num_words = 0
            for word in words:
                pattern = r"(^|[\W])"+word.lower()+r"($|[\W])" #todo: ignore special chars
                if re.findall(pattern,m.get("content","").lower()):
                    #print(re.findall(pattern,m.get("content","")))
                    num_words+=1
            if num_words>=best_num_words:
                for j in range(len(msgs)-i):
                    m2 = msgs[i+j]
                    if m2.get("sender_name","") != user:
                        if m2.get("timestamp_ms")-m.get("timestamp_ms")<=MAX_TIME_DELTA_MS:
                            #print(m.get('content'))
                            #todo: filter out "you set nickname", etc.
                            if num_words>best_num_words:
                                best_reply = []
                            best_reply.append(m2.get("content"))
                            break
                best_num_words = num_words
    if best_num_words>0:
        return best_reply[randint(0,len(best_reply)-1)]
    else:
        while(True):
            msg = msgs[randint(0,len(msgs)-1)]
            if msg.get("sender_name",user) != user:
                return "debug: not found"
                #return msg.get("content")

while(True):
    print(reply(input())) #TODO: serverify for tmrw
