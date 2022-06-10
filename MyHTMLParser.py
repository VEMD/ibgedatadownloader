# -*- coding: utf-8 -*-
"""
/***************************************************************************
        begin                : 2021-11-17
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Vinicius Etchebeur Medeiros Dória
        email                : vinicius_etchebeur@hotmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from html.parser import HTMLParser
import re


class MyHTMLParser(HTMLParser):
    """PERSONALIZED HTML PARSER"""

    def __init__(self):
        """Constructor."""

        # Mother class constructor HTMLParser (subclass)
        super(MyHTMLParser, self).__init__()

        # Attribute that receive parent tree
        self.parent = None
        # Attribute that receive children tree
        self.children = []
        # Attribute that receives child information
        self.child = []
        # Attribute that receives tag <tr> in and out information
        self.trElement = False

    def handle_starttag(self, tag, attrs):
        """Overrides to feed parent and child"""

        if tag == 'tr':
            self.trElement = True
            #print(tag, self.trElement)

        if tag == 'a':
            for attr in attrs:
                if attr[1]:
                    if attr[1].startswith('/'):
                        # Set parent
                        self.parent = attr[1]
                    if not any(attr[1].startswith(item) for item in ('?', '/')):
                        # Set child name
                        self.child = [attr[1]]
                        #print('adicionou handle_starttag')
            #print(tag, self.child)

    def handle_endtag(self, tag):
        """Overrides to feed children and reset child"""

        if tag == 'tr':
            self.trElement = False
            # If child is valid, append to children
            if self.child != []:
                self.children.append(self.child)
            # Reset child
            self.resetChild()
            #print(tag, self.trElement)

    def handle_data(self, data):
        """Overrides to feed information about child"""

        # Remove white spaces at start / end of the string
        data = data.lstrip().rstrip()
        # Set child last modified date
        match = re.match(r'(\d+-\d+-\d+ \d+:\d+)', data)
        if match and self.child != []:
            self.child.append(data)
            #print(self.child)
        # Set child file size using regular expression
        match = re.match(r'(\d+[A-Za-z])', data)  # N...X
        matchType = 1
        if not match:
            match = re.match(r'(\d+\.?\d+[A-Za-z])', data)  # N.N...X
        if not match:
            match = re.match(r'(^\d+$)', data)  # N...
            matchType = 2
        if match and self.child != []:
            # Adds a space between value and unit and a B as sufix
            if matchType == 1:
                self.child.append('{} {}B'.format(data[:-1], data[-1]))
            elif matchType == 2:
                self.child.append('{} B'.format(data))
            #print(self.child)

    def getChildren(self):
        """Returns childs"""

        return self.children if self.children else None

    def getParent(self):
        """Returns parent"""

        return self.parent

    def resetChild(self):
        """Resets child attribute"""

        self.child = []

    def resetChildren(self):
        """Resets children attribute"""

        self.children = []

    def resetParent(self):
        """Resets parent attribute"""

        self.parent = None
