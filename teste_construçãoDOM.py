from html.parser import HTMLParser
from html.entities import name2codepoint
import urllib, http, time

class MyHTMLParser(HTMLParser):
    ############################
    # PERSONALIZED HTML PARSER #
    ############################
    def __init__(self):
        """Constructor."""
        # Mother class constructor HTMLParser (subclass)
        super(MyHTMLParser, self).__init__()
        # Attribute that receives parent tree
        self.__parent__ = None
        # Attribute that receives childs tree
        self.__children__ = []
        # Attribute that receives child information
        self.__child__ = []
    def handle_starttag(self, tag, attrs):
        """Overrides to feed __parent__ and __children__ attributes"""
        if tag == 'a':
            # If child is valid, append to __children__
            if self.__child__ != []:
                self.__children__.append(self.__child__)
            # Clear __child__ attribute
            self.__child__ = []
            for attr in attrs:
                if attr[1].startswith('/'):
                    # Set parent
                    self.__parent__ = attr[1]
                if not any(attr[1].startswith(item) for item in ('?', '/')):
                    # Set child name
                    self.__child__.append(attr[1])
    def handle_data(self, data):
        # Set child last modified date
        match = re.match(r'(\d+-\d+-\d+ \d+:\d+)', data)
        if match:
            self.__child__.append(data.rstrip())
        # Set child file size
        match = re.match(r'(\d+M)', data)
        if match:
            self.__child__.append(data)
    def getChildren(self):
        """Returns childs"""
        return self.__children__ if self.__children__ else None
    def getParent(self):
        """Returns parent"""
        return self.__parent__
    def resetChildren(self):
        self.__children__ = []
    def resetParent(self):
        self.__parent__ = None

htmlParser = MyHTMLParser()

url = 'https://geoftp.ibge.gov.br/organizacao_do_territorio/malhas_territoriais/malhas_municipais/'
htmlParser.reset()
htmlParser.feed(http.client.parse_headers(urllib.request.urlopen(url)).as_string())
parent = os.path.basename(os.path.normpath(url)).replace('_', ' ').title()
children = htmlParser.getChildren()
print(children)
listParentChild = []
# Add all children and others to the tree
for child in children:
    listParentChild.append([parent, child])
    if child.endswith('/'):
        print(child)
        print(listParentChild)
        urlChild = url + child
        print(urlChild)
        htmlParser.resetParent()
        htmlParser.resetChildren()
        htmlParser.feed(http.client.parse_headers(urllib.request.urlopen(urlChild)).as_string())
        childChildren = htmlParser.getChildren()
        #print(childChildren)
        for childChild in childChildren:
            listParentChild.append([child, childChild])
    break