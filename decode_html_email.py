#!/usr/bin/env python
#coding=utf-8

from flask import Flask, request, Markup
from flask import render_template
import notmuch as nm
import sys

app = Flask(__name__)
db = nm.Database()

@app.route('/search')
def search_messages():
    return render_template('search_form.html')

@app.route('/search', methods=['POST'])
def list_search_results():
    querystr = request.form.get('query')
    return list_messages(querystr)

def list_messages(querystr):
    q = nm.Query(db, querystr)
    msgs = q.search_messages()
    return render_template('msg_list.html',
                           messages=msgs,
                           query=querystr) 

@app.route('/')
@app.route('/tag/<tag>')
def list_messages_by_tag(tag='inbox'):
    return list_messages("tag:{}".format(tag))

def search_type(messages, content_type):
    for part in messages:
        if part.get_content_type() == content_type:
            return part.get_payload(decode=True)

@app.route('/message/<msg_id>')
def get_message(msg_id):
    message = db.find_message(msg_id)
    subject = message.get_header('subject')
    message_parts = message.get_message_parts()
    html_msg = search_type(message_parts, 'text/html')
    if html_msg:
        html_msg = Markup(html_msg.decode('utf-8'))
    txt_msg = search_type(message_parts, 'text/plain')
    if txt_msg:
        txt_msg = txt_msg.decode('utf-8')
    return render_template("show_message.html", 
            msg_id=msg_id,
            subject=subject,
            text_content=txt_msg,
            html_content=html_msg,
            parts=message_parts)

@app.route('/message/<msg_id>/<int:part>')
def get_message_part(msg_id, part):
    message = db.find_message(msg_id)
    message_parts = message.get_message_parts()
    part = message_parts[part]
    payload = part.get_payload(decode=True)
    content_type = part.get_content_type()
    return payload, 200, {'Content-Type' : content_type}
    


#msg_parts = m.get_message_parts()
if __name__ == "__main__":
    app.run(debug=True)

