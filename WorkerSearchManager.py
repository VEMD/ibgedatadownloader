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
from qgis.PyQt.QtCore import pyqtSignal, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.core import QgsTask, Qgis, QgsProject
import os, urllib, zipfile, tarfile, http, http.client, time
from .MyHTMLParser import MyHTMLParser

class WorkerSearchManager(QgsTask):
    ######################################
    # SEARCHES IN A FTP'S URL FOR A WORD #
    ######################################

    # Signals emitted
    textProgress = pyqtSignal(str) # text for progress dialog
    processResult = pyqtSignal(list) # process result
    barMax = pyqtSignal(float) # max number of progress bar

    def __init__(self, iface, desc, rootFtp, txtSearch, matchExact, matchScore):
        """Constructor."""

        # Mother class constructor QgsTask (subclass)
        super(WorkerSearchManager, self).__init__(desc, flags=QgsTask.CanCancel)
        
        # Saving references
        self.iface = iface
        self.project = QgsProject.instance()
        self.msgBar = self.iface.messageBar()
        self.htmlParser = MyHTMLParser()
        self.rootFtp = rootFtp
        self.txtSearch = txtSearch
        self.matchExact = matchExact
        self.matchScore = matchScore
        self.pluginIcon = QIcon(':/plugins/ibgedatadownloader/icon.png')
        self.exception = []

        # Avoid headers limit error
        http.client._MAXHEADERS = 999999999999999999

    def finished(self, result):
        """This function is called automatically when the task is completed and is
        called from the main thread so it is safe to interact with the GUI etc here"""

        if result is False:
            self.msgBar.pushMessage(self.tr(u'Error'), self.tr(u'Oops, something went wrong! Please, contact the developer by e-mail.'), Qgis.Critical, duration=0)
        elif self.exception != []:
            self.msgBar.pushMessage(self.tr(u'Warning'), self.tr(u'Process partially completed.'), Qgis.Warning, duration=0)
        else:
            self.msgBar.pushMessage(self.tr(u'Success'), self.tr(u'Process completed.'), Qgis.Success, duration=0)

    def run(self):
        """Principal method that is automatically called when the task runs."""

        self.barMax.emit(0)

        matchUrl = []

        self.htmlParser.resetParent()
        self.htmlParser.resetChildren()
        self.htmlParser.resetChild()
        self.htmlParser.feed(http.client.parse_headers(urllib.request.urlopen(self.rootFtp)).as_string())
        children = self.htmlParser.getChildren()

        fails = 0
        if children:
            searchUrls = []
            for child in children:
                searchUrls.append([self.rootFtp + child[0], child[1]])
                if self.txtSearch in child[0]:
                    matchUrl.append([self.rootFtp + child[0], child[1]])
                    self.textProgress.emit(self.tr('{} Product(s) found.\nThe search may take several minutes...').format(len(matchUrl)))
            loop = 0
            while True:
                for sUrl in searchUrls:
                    # Check if task was canceled by the user
                    if self.isCanceled():
                        self.processResult.emit([self.tr(u'The process was canceled by the user.'), Qgis.Warning, self.exception, matchUrl, 'search'])
                        return False
                    loop += 1
                    #print(loop, len(searchUrls))
                    self.htmlParser.resetParent()
                    self.htmlParser.resetChildren()
                    self.htmlParser.resetChild()
                    try:
                        self.htmlParser.feed(http.client.parse_headers(urllib.request.urlopen(sUrl[0])).as_string())
                    except urllib.error.HTTPError as e:
                        #print(e.code, e.reason, e.headers)
                        #print('tentando novamente em 5 segundos...')
                        time.sleep(5)
                        try:
                            self.htmlParser.feed(http.client.parse_headers(urllib.request.urlopen(sUrl[0])).as_string())
                        except urllib.error.HTTPError as e:
                            #print(e.code, e.reason, e.headers)
                            self.exception.append(e.reason)
                            searchUrls.remove(sUrl)
                            fails += 1
                            continue
                    children = self.htmlParser.getChildren()
                    if children:
                        for child in children:
                            searchUrls.append([sUrl[0] + child[0], child[1]])
                            if self.txtSearch in child[0]:
                                matchUrl.append([sUrl[0] + child[0], child[1]])
                                self.textProgress.emit(self.tr('{} Product(s) found.\nThe search may take several minutes...').format(len(matchUrl)))
                    try:
                        searchUrls.remove(sUrl)
                    except:
                        pass

        self.processResult.emit([self.tr(u'Search completed with {fails} fails.').format(fails=fails), Qgis.Success, self.exception, matchUrl, 'search'])
        return True