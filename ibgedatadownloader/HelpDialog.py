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
from qgis.PyQt.QtCore import QSettings
from qgis.PyQt.QtWidgets import QDialog, QTextBrowser, QGridLayout
import os


class HelpDialog(QDialog):
    """CREATES AND PREPARE THE HELP DIALOG"""

    def __init__(self, parent):
        """Constructor."""

        # Mother class constructor QgsTask (subclass)
        super(HelpDialog, self).__init__(parent)

        # initialize file directory
        self.fileDir = os.path.dirname(__file__)

        # Keep reference of the sotfware language
        self.locale = QSettings().value('locale/userLocale')[0:2]

        # Configuring window
        self.setWindowTitle(self.tr('Help of IBGE Data Downloader'))
        self.resize(600, 500)

        # Create grid to organize objects
        grid = QGridLayout(self)
        grid.setObjectName('mainGridLayout')

        # Create the browser
        self.helpBrowser = QTextBrowser()

        # Connect browser's signal to slot
        self.helpBrowser.anchorClicked.connect(self.helpBrowserAnchorClicked)

        # Add browser to the window
        grid.addWidget(self.helpBrowser)

        # Load corresponding file
        htmlPage = open(os.path.join(self.fileDir, 'pluginHelp', self.locale, 'home.html'))
        self.helpBrowser.setHtml(htmlPage.read())
        htmlPage.close()

    def helpBrowserAnchorClicked(self, link):
        """Change page of help dialog when an anchor is clicked"""

        htmlPage = open(os.path.join(self.fileDir, 'pluginHelp', self.locale, link.toString()))
        self.helpBrowser.setHtml(htmlPage.read())
        htmlPage.close()
