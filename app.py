#!/usr/bin/python3

from flask import Flask, request, redirect, url_for
import os

app = Flask(__name__)
count = 0

@app.route('/')
def index():
    return open(os.getcwd()+"/index.html").read()

@app.route('/style.css')
def style():
    return open(os.getcwd()+"/style.css").read()

@app.route('/chat/<count>')
def chat(count):
    return open(os.getcwd()+"/chat.html").read().replace("TEMP",str(count))

@app.route('/', methods=['POST'])
def file_upload():
    global count
    file = request.files["json"]
    file.save(os.getcwd()+"/message_"+str(count)+".json")
    count+=1
    return redirect(url_for("chat", count=count-1))
