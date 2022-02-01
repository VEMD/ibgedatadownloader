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
from qgis.PyQt.QtWidgets import QProgressDialog

class MyProgressDialog(QProgressDialog):
    ###################
    # PROGRESS DIALOG #
    ###################

    def __init__(self):
        """Constructor."""

        # Mother class constructor QProgressDialog (subclass)
        super(MyProgressDialog, self).__init__()

        # Attribute that keeps the dialog opened
        self.__close__ = False

    def setClose(self, var):
        """Defines if the dialog can be closed"""

        self.__close__ = var

    def closeEvent(self, event):
        """Overrides closeEvent (closing dialog)"""

        if self.__close__:
            super(MyProgressDialog, self).closeEvent(event)
        else:
            event.ignore()