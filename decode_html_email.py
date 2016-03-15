#!/usr/bin/env python
#coding=utf-8

from flask import Flask, request, Markup
from flask import render_template
import notmuch as nm
import sys
from bs4 import BeautifulSoup
import re

app = Flask(__name__)

@app.template_filter('removecitations')
def removecitations(s):
    lines = [line for line in s.splitlines() if not re.match("^>", line)]
    return "\n".join(lines)



@app.route('/search')
def search_messages():
    return render_template('search_form.html')

@app.route('/search', methods=['POST'])
def list_search_results():
    querystr = request.form.get('query')
    return list_messages(querystr)

def list_messages(querystr):
    with  nm.Database() as db:
        q = nm.Query(db, querystr)
        msgs = q.search_messages()
        response_html = render_template('msg_list.html',
                               messages=msgs,
                               query=querystr) 
    return response_html

@app.route('/')
@app.route('/tag/<tag>')
def list_messages_by_tag(tag='inbox'):
    return list_messages("tag:{}".format(tag))

def search_type(messages, content_type):
    for part in messages:
        if part.get_content_type() == content_type:
            payload = part.get_payload(decode=True)
            encoding = part.get_content_charset()
            return payload.decode(encoding)

@app.route('/thread/<thread_id>')
def list_thread(thread_id):
    querystr = "thread:{}".format(thread_id)
    with nm.Database() as db:
        q = nm.Query(db, querystr)
        msgs = q.search_messages()
        parsed_messages = map(parse_message, msgs)

    return render_template('show_thread.html',
            thread_subject = parsed_messages[-1]['subject'],
            message_list=parsed_messages[::-1])

def parse_message(message):
    subject = message.get_header('subject')
    from_addr = message.get_header('from')
    to_addr = message.get_header('to')
    cc_addr = message.get_header('cc')
    date = message.get_header('date')
    tags = message.get_tags()
    message_parts = message.get_message_parts()
    html_msg = search_type(message_parts, 'text/html')
    txt_msg = search_type(message_parts, 'text/plain')
    msg_id = message.get_message_id() 
    thread_id = message.get_thread_id()

    if html_msg:
        parsed_html = BeautifulSoup(html_msg)
        html_msg = parsed_html.body.renderContents().decode('utf-8')
        html_msg = Markup(html_msg)
    message_dict = {
            'id' : msg_id, 
            'thread_id' : thread_id,
            'subject' : subject,
            'from' : from_addr,
            'to' : to_addr,
            'cc' : cc_addr,
            'date' : date,
            'tags' : tags,
            'html' : html_msg,
            'plaintext' : txt_msg,
            'parts' : message_parts
            }
    return message_dict

@app.route('/message/<msg_id>')
def get_message(msg_id):
    with nm.Database() as db:
        message = db.find_message(msg_id)
        message_dict = parse_message(message)

    return render_template("show_message.html", 
            message=message_dict)

@app.route('/message/<msg_id>/<int:part>')
def get_message_part(msg_id, part):
    with nm.Database() as db:
        message = db.find_message(msg_id)
        message_parts = message.get_message_parts()
        part = message_parts[part]
    payload = part.get_payload(decode=True)
    content_type = part.get_content_type()
    headers = {'Content-Type' : content_type}
    fname = part.get_filename()
    if fname:
        headers['Content-Disposition'] = 'inline; filename="{}"'.format(fname)
    return payload, 200, headers 
    
if __name__ == "__main__":
    app.run(debug=True)

