import requests
from bs4 import BeautifulSoup
import xml.sax
import json
import random
import urlparse

def handler(event, context):
    body = event["postBody"]
    cmd = urlparse.parse_qs(body)

    print(cmd)
    response_url = cmd["response_url"][0]
    keyword = None
    if "text" in cmd:
        keyword = cmd["text"][0]

    if keyword and len(keyword):
        ret = search(cmd, keyword)
        if ret:
            post_response(response_url, ret)
        else:
            post_response(response_url, return_error("No fart found"))
    else: # no keyword
        post_response(response_url, random_fart(cmd))

def post_response(response_url, data):
    requests.post(response_url, data=json.dumps(data), headers={'Content-type': 'application/json'})

def search(cmd, keyword):
    fp = open("farts.xml", "r")
    data = fp.read()
    parser = xml.sax.make_parser()
    Handler = FartHandler()
    parser.setContentHandler( Handler )
    parser.parse("farts.xml")
    search = keyword
    search = search.upper()
    matches = []
    for fart in Handler.allfarts:
        if search in fart["content"].upper() or search in fart["title"].upper():
            matches.append([fart["content"], fart["title"], fart["id"]])

    if not len(matches):
        return None

    return return_fart(cmd, *random.choice(matches))

def random_fart(cmd):
    r = requests.get('http://www.asciiartfarts.com/random.cgi')
    soup = BeautifulSoup(r.content, 'html.parser')
    fart = soup.select("td font pre")
    return return_fart(cmd, fart[0].string)

def return_error(msg):
    return {
        "text": msg,
        "color": "danger"
    }

def return_fart(cmd, fart_content, fart_title=None, fart_id=None):
    user_name = cmd["user_name"][0]
    if not fart_title:
        fart_title = "[RANDOM]"
    fart_content = fart_content.replace('```', "'''")  # work around preformatting escape for slack :/
    return {
        "response_type": "in_channel",
        "attachments": [{
            'title': fart_title + " (from " + user_name + ")",
            # "title_link": "FIXME",
            'fallback': fart_content,
            'text': '```' + fart_content + '```',
            'parse': 'none',
            'mrkdwn_in': ['text']
        }]
    }

class FartHandler(xml.sax.ContentHandler):
    FART_LEVEL = 3  # the schema is bad and you should feel bad...
    
    def __init__(self):
        self.lvl = 0
        self.infarts = False
        self.curfart = {}
        self.chars = ""
        self.nodename = ""
        self.allfarts = []
    #print "started..."
    
    def startElement(self, name, attrs):
        #print "start element %s, lvl %d " % (name, self.lvl)
        self.lvl += 1
        if self.lvl == FartHandler.FART_LEVEL and name == "fart":
            #print "Entered a fart... level: %d" % self.lvl
            self.infarts = True
        
        if not self.infarts:
            return
        
        self.nodename = name
    #print "new node: " + name
    
    def characters(self, content):
        self.chars += content
    
    def endElement(self, name):
        self.lvl -= 1
        if self.infarts:
            if self.lvl < FartHandler.FART_LEVEL:
                if "content" not in self.curfart:
                    self.curfart = {}
                    return
                self.allfarts.append(self.curfart)
                self.curfart = {}
            #print "======Exited fart======="
            else:
                self.curfart[name] = self.chars
                self.chars = ""

if __name__ == "__main__":
    print(search({}, "slashdot"))
