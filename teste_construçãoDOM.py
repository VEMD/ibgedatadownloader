from html.parser import HTMLParser
from html.entities import name2codepoint
import urllib, http

class MyHTMLParser(HTMLParser):
    ############################
    # PERSONALIZED HTML PARSER #
    ############################
    def __init__(self):
        """Constructor."""
        # Mother class constructor HTMLParser (subclass)
        super(MyHTMLParser, self).__init__()
        # Attribute that receive parent tree
        self.__parent__ = None
        # Attribute that receive childs tree
        self.__children__ = []
    def handle_starttag(self, tag, attrs):
        """Overrides to feed __parent__ and __children__ attributes"""
        if tag == 'a':
            for attr in attrs:
                if attr[1].startswith('/'):
                    # Set parent
                    self.__parent__ = attr[1]
                if not any(attr[1].startswith(item) for item in ('?', '/')):
                    # Add child
                    self.__children__.append(attr[1])
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