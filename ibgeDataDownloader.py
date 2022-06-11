# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IbgeDataDownloader
                                 A QGIS plugin
 This plugin downloads data from IBGE
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
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
from qgis.PyQt.QtCore import (
    QSettings, QTranslator, QCoreApplication,
    Qt, QModelIndex
)
from qgis.PyQt.QtGui import QIcon, QStandardItemModel, QStandardItem, QBrush, QColor
from qgis.PyQt.QtWidgets import (
    QAction, QFileDialog, QProgressBar, QToolButton,
    QDialogButtonBox, QHeaderView, QAbstractItemView,
    QPushButton
)
from qgis.core import Qgis, QgsProject, QgsApplication, QgsVectorLayer
import os, unicodedata, urllib, zipfile, tarfile, http, http.client, socket

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .ibgeDataDownloader_dialog import IbgeDataDownloaderDialog
from .MyHTMLParser import MyHTMLParser
from .MyProgressDialog import MyProgressDialog
from .WorkerDownloadManager import WorkerDownloadManager
from .WorkerSearchManager import WorkerSearchManager
from .HelpDialog import HelpDialog


class IbgeDataDownloader:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'IbgeDataDownloader_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Download data from IBGE')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.firstStart = None

        # Plugin icon
        self.pluginIcon = QIcon(':/plugins/ibgedatadownloader/icon.png')

        # Access to QGIS status bar and progress button
        self.statusBar = self.iface.statusBarIface()
        for i in self.statusBar.children():
            if type(i) == QToolButton:
                for j in i.children():
                    if type(j) == QProgressBar:
                        self.qgisProgressButton = i
                        break

        # Avoid headers and maxlines limit error
        http.client._MAXHEADERS = 999999999999999999
        http.client._MAXLINE = 999999999999999999

        # Saving references
        self.msgBar = self.iface.messageBar()
        self.taskManager = QgsApplication.taskManager()
        self.settings = QSettings()
        self.htmlParser = MyHTMLParser()
        self.geobaseUrl = 'https://geoftp.ibge.gov.br/'
        self.statbaseUrl = 'https://ftp.ibge.gov.br/'
        self.itemsExpanded = []
        self.selectedProductsUrl = []
        self.selectedSearch = ''
        self.dirOutput = ''
        self.itemLastCheckState = None
        self.itemsHighlighted = []

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('IbgeDataDownloader', message)

    def add_action(
            self,
            icon_path,
            text,
            callback,
            enabled_flag=True,
            add_to_menu=True,
            add_to_toolbar=True,
            status_tip=None,
            whats_this=None,
            parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/ibgeDataDownloader/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'IBGE Data Downloader'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.firstStart = True

    def unload(self):
        """Remove the plugin menu item and icon from QGIS GUI."""

        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Download data from IBGE'),
                action)
            self.iface.removeToolBarIcon(action)

    def progressDialog(self, value, text):
        """Creates and returns the progress dialog and bar"""

        dialog = MyProgressDialog()
        dialog.setWindowTitle(self.tr(u'Processing. Please, wait...'))
        dialog.setLabelText(text)
        dialog.setWindowIcon(self.pluginIcon)
        progressBar = QProgressBar(dialog)
        progressBar.setTextVisible(True)
        progressBar.setValue(value)
        dialog.setBar(progressBar)
        dialog.setMinimumWidth(300)
        dialog.setModal(True)
        dialog.setWindowFlag(Qt.WindowCloseButtonHint, False)
        dialog.setAutoClose(False)
        dialog.setAutoReset(False)
        dialog.canceled.connect(self.canceledProgressDialog)
        for i in dialog.children():
            if type(i) == QPushButton:
                self.dlgBarCancelButton = i
                break
        return dialog, progressBar

    def setMaximumProgressBar(self, maxN):
        """Sets maximum of the progress bar"""

        #self.progressBar.reset()
        self.progressValue = 0
        self.progressBar.setRange(self.progressValue, int(maxN))
        self.progressBar.setValue(self.progressValue)
        #print(int(maxN))

    def canceledProgressDialog(self):
        """Cancels the task."""

        self.dlgBarCancelButton.setEnabled(False)
        self.dlgBar.setLabelText(self.tr('{}\nCanceling...').format(self.dlgBar.labelText().split('\n')[0]))
        self.dlgBar.show()
        if not self.threadTask.isCanceled():
            self.threadTask.cancel()

    def setProgressValue(self, val):
        """Defines value of progress bar."""

        self.progressValue = int(val)
        self.progressBar.setValue(self.progressValue)

    def setProgressText(self, txt):
        """Defines the label of the progress dialog."""

        self.dlgBar.setLabelText(txt)
        if self.tr('Extracting files') in txt:
            self.progressBar.setRange(0, 0)
            self.progressBar.setValue(0)

    def dlgDirOutput(self, checked):
        """Opens dialog to indicate the output directory."""

        self.dirOutput = QFileDialog.getExistingDirectory(QFileDialog(), self.tr(u'Output directory'), '')
        self.dlg.lineEdit_Saida.setText(self.dirOutput)

        if self.dirOutput != '':
            self.checkOkButton()
        else:
            self.dlg.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def threadResult(self, result):
        """Keeps reference of the worker result"""

        self.pluginResult = result
        #self.endingProcess()

    def endingProcess(self):
        """Closes progress dialog and finishes the job"""

        # Close progress dialog
        self.dlgBar.setClose(True)
        self.dlgBar.close()

        # Define message title and deal with remaining data, if necessary
        if self.pluginResult[4] == 'download':
            # If the method callback came from WorkerDownloadManager
            if self.tr('canceled') in self.pluginResult[0]:
                msgType = self.tr('Warning')
                # Delete remaining data
                fileName = os.path.basename(self.pluginResult[3])
                if os.path.isfile(os.path.join(self.dirOutput, fileName)):
                    os.remove(os.path.join(self.dirOutput, fileName))
            elif self.pluginResult[1] == Qgis.Critical:
                msgType = self.tr('Error')
            else:
                msgType = self.tr('Success')
                # Add layer (if possible)
                if self.dlg.checkBox_AddLayer.isChecked():
                    for i in self.pluginResult[3]:
                        fileName = os.path.basename(i[1])
                        file = os.path.join(self.dirOutput, fileName)
                        files = None
                        if fileName.endswith('.zip'):
                            files = zipfile.ZipFile(file).namelist()
                        elif fileName.endswith('.tar'):
                            files = tarfile.TarFile(file).getnames()
                        if files:
                            for j in files:
                                if j.endswith('.shp'):
                                    layer = QgsVectorLayer(os.path.join(self.dirOutput, j), j, 'ogr')
                                    # Extent enlarged of 1/25
                                    extent = layer.extent()
                                    xMin = extent.xMinimum()
                                    yMin = extent.yMinimum()
                                    xMax = extent.xMaximum()
                                    yMax = extent.yMaximum()
                                    diagonal = ((xMax - xMin) ** 2 + (yMax - yMin) ** 2) ** 0.5
                                    buffer = 0.04 * diagonal
                                    extent = extent.buffered(buffer)
                                    # Add layer
                                    QgsProject.instance().addMapLayer(layer)
                                    self.iface.mapCanvas().setExtent(extent)
        else:
            # If the method callback came from WorkerSearchManager
            if self.tr('canceled') in self.pluginResult[0]:
                msgType = self.tr('Warning')
            elif self.pluginResult[1] == Qgis.Critical:
                msgType = self.tr('Error')
            else:
                msgType = self.tr('Success')

            if len(self.pluginResult[3]) > 0:
                self.dlgBar, self.progressBar = self.progressDialog(0, self.tr(u'Adding products to Products Tree. This may take several minutes...'))
                self.progressBar.setRange(0, 0)
                self.dlgBar.show()
                for i in self.pluginResult[3]:
                    dirs = i[0].split('/')[2:]
                    #print(i, dirs)
                    if 'geo' in dirs[0]:
                        self.dlg.tabWidget.setCurrentIndex(0)
                        treeView = self.dlg.treeView_Geo
                        model = treeView.model()
                    else:
                        self.dlg.tabWidget.setCurrentIndex(1)
                        treeView = self.dlg.treeView_Stat
                        model = treeView.model()
                    for d in dirs:
                        if d != '':
                            items = model.findItems(d, Qt.MatchExactly | Qt.MatchRecursive)
                            for n, item in enumerate(items):
                                modelIndex = model.indexFromItem(item)
                                itemUrl = self.getItemUrl(modelIndex)
                                #print(itemUrl, i[0])
                                if itemUrl in i[0]:
                                    # Highlight item found
                                    text = self.dlg.lineEdit_SearchWord.text()
                                    if text.lower() in modelIndex.data().lower():
                                        # Set backgroud color to highlight item
                                        item.setBackground(QBrush(QColor(255, 255, 100)))
                                        self.itemsHighlighted.append(item)
                                    if os.path.splitext(item.text())[1] in ('', '.br'):
                                        # If item is expandable
                                        treeView.expand(modelIndex)
                                        # Scroll to first item found
                                        if n == 0:
                                            treeView.scrollTo(modelIndex, QAbstractItemView.PositionAtTop)

                self.dlgBar.setClose(True)
                self.dlgBar.close()

        self.msgBar.clearWidgets()
        if self.pluginResult[2] != []:
            self.msgBar.pushMessage(msgType, self.pluginResult[0], '\n\n'.join(self.pluginResult[2]), self.pluginResult[1], duration=0)
        else:
            self.msgBar.pushMessage(msgType, self.pluginResult[0], self.pluginResult[1], duration=20)

    def padronizaTexto(self, texto):
        """Standardizes texts to check equality."""

        try:
            texto = unicode(texto, 'utf-8')
        except (TypeError, NameError):
            pass
        texto = unicodedata.normalize('NFD', texto)
        texto = texto.encode('ascii', 'ignore')
        texto = texto.decode("utf-8")
        texto = texto.replace(' ', '_')
        return str(texto.lower())

    def populateComboListBox(self, objeto, lista, coluna='', inicial=''):
        """Populates a list or combo object."""

        objeto.clear()
        if inicial != '':
            objeto.addItem(inicial)
        for elemento in lista:
            if coluna == '':
                e = elemento
            else:
                e = elemento[0] + ' - ' + elemento[coluna]
            try:
                item = unicode(e)
            except TypeError:
                item = str(e)
            objeto.addItem(item)

    def getCurrentObjects(self, clear=False):
        """Returns reference objects and clears selection, if needed"""

        if self.dlg.tabWidget.currentIndex() == 0:
            if clear:
                self.statSelectionModel.clear()
            baseUrl = self.geobaseUrl
            treeView = self.dlg.treeView_Geo
            selectionModel = self.geoSelectionModel
        else:
            if clear:
                self.geoSelectionModel.clear()
            baseUrl = self.statbaseUrl
            treeView = self.dlg.treeView_Stat
            selectionModel = self.statSelectionModel

        return baseUrl, treeView, selectionModel

    def getItemUrl(self, modelIndex):
        """Returns the url of the given item (modelIndex)"""

        baseUrl, _, _ = self.getCurrentObjects()

        if modelIndex.column() == 0:
            # Gets all parents and the item to create the URL
            parents = [modelIndex.data()] if ['/{}'.format(modelIndex.data()) if os.path.splitext(modelIndex.data())[1] == '' else modelIndex.data()][0] not in baseUrl else []
            parent = modelIndex.parent()
            #print(modelIndex.parent(), modelIndex.parent().data())
            while parent.data() is not None and ['/{}'.format(parent.data()) if os.path.splitext(parent.data())[1] == '' else parent.data()][0] not in baseUrl:
                parents.insert(0, parent.data())
                parent = parent.parent()
            productUrl = '{base}{subPath}'.format(base=baseUrl, subPath='/'.join(parents))
        else:
            productUrl = ''

        return productUrl

    def clearItemsHighlighted(self):
        """Clears highlighted items"""

        while self.itemsHighlighted:
            for i in self.itemsHighlighted:
                i.setBackground(QBrush())
                self.itemsHighlighted.remove(i)

    def treeViewPressed(self, modelIndex):
        """Keeps reference of the check state of the item about to be clicked"""

        item = modelIndex.model().itemFromIndex(modelIndex)
        self.itemLastCheckState = item.checkState() if item.isCheckable() else None

        # Set background of highlighted items to default
        self.clearItemsHighlighted()

    def treeViewClicked(self, modelIndex):
        """Slot of clicked signal that constructs the items URL and enables the OK button"""

        _, treeView, selectionModel = self.getCurrentObjects()

        # Set background of highlighted items to default
        self.clearItemsHighlighted()

        if modelIndex.column() == 0:
            # Get url of clicked item
            productUrl = self.getItemUrl(modelIndex)

            # Add or remove from products variable
            model = modelIndex.model()
            item = model.itemFromIndex(modelIndex)
            #print(item.checkState())
            if self.itemLastCheckState:
                if self.itemLastCheckState != item.checkState():
                    selectionModel.clear()
            if item.checkState() == Qt.CheckState.Checked:
                self.selectedProductsUrl.append([modelIndex, productUrl, treeView])
                qtdProducts = len(self.selectedProductsUrl)
            else:
                for p in self.selectedProductsUrl:
                    if p[1] == productUrl:
                        self.selectedProductsUrl.remove(p)
                qtdProducts = len(self.selectedProductsUrl)
            self.dlg.label_ProductsSelected.setText(u'{p} {t}'.format(p=qtdProducts, t=self.tr(u'Product(s) selected')))

            # Check if the unzip option can be enabled
            if self.selectedProductsUrl:
                self.dlg.checkBox_AddLayer.setEnabled(True)
                for p in self.selectedProductsUrl:
                    if any(p[1].endswith(ext) for ext in ('.zip', '.tar')):
                        self.dlg.checkBox_Unzip.setEnabled(True)
                        break
                    else:
                        self.dlg.checkBox_Unzip.setEnabled(False)
            else:
                self.dlg.checkBox_Unzip.setEnabled(False)
                self.dlg.checkBox_AddLayer.setEnabled(False)

            # Check if OK button can be enabled
            self.checkOkButton()

    def treeViewExpanded(self, modelIndex):
        """Slot of expanded signal that adds item's children to the tree"""

        _, treeView, _ = self.getCurrentObjects()

        if modelIndex not in self.itemsExpanded:
            # Deletes first empty child
            model = modelIndex.model()
            item = model.itemFromIndex(modelIndex)
            child = item.child(0)
            if child and child.text() == '':
                item.removeRow(0)

            # Adds item's children
            #print('/'.join(parents))
            url = self.getItemUrl(modelIndex)
            #print(url)
            self.htmlParser.resetParent()
            self.htmlParser.resetChildren()
            self.htmlParser.resetChild()
            # Set timeout for requests
            socket.setdefaulttimeout(15)
            try:
                self.htmlParser.feed(http.client.parse_headers(urllib.request.urlopen(url)).as_string())
            except socket.timeout as e:
                self.msgBar.pushMessage(self.tr('Warning'), self.tr('The expand operation of an item fails due to a server timeout.'), e, Qgis.Warning, duration=0)
            # Set timeout for requests to default
            socket.setdefaulttimeout(None)
            children = self.htmlParser.getChildren()

            # Add children to the tree
            #print(children)
            if children:
                for child in children:
                    #print('adicionando {} ao item {}'.format(child.replace('/', ''), modelIndex.data()))
                    child[0] = child[0].replace('/', '')
                    self.addTreeViewParentChildItem(treeView, modelIndex, child)

            # Add the item to expanded list
            self.itemsExpanded.append(modelIndex)

    def searchExactStateChanged(self, state):
        """Enables or disables match score options depending on Exact match checkbox state"""

        if state == Qt.Checked:
            self.dlg.label_Match.setEnabled(False)
            self.dlg.doubleSpinBox_MatchValue.setEnabled(False)
        else:
            self.dlg.label_Match.setEnabled(True)
            self.dlg.doubleSpinBox_MatchValue.setEnabled(True)

    def addTreeViewParentChildItem(self, treeView, parent, child=None):
        """Adds parent or children items to the QTreeView"""

        model = treeView.model()
        if not model:
            model = QStandardItemModel(0, 3)
            model.setHorizontalHeaderLabels([self.tr('Products Tree'), self.tr('File size'), self.tr('Last modified')])
            treeView.setModel(model)

        # Creates standard empty item
        emptyItem = QStandardItem('')

        if not child:
            parentItem = QStandardItem(parent)
            parentItem.appendRow([emptyItem, emptyItem, emptyItem])
            model.appendRow([parentItem, emptyItem, emptyItem])
        else:
            if type(parent) == QModelIndex:
                #print(u'é QModelIndex', child)
                parentItem = model.itemFromIndex(parent)
                childItem = QStandardItem(child[0])
            if '.' not in childItem.text():
                if not childItem.hasChildren():
                    childItem.appendRow(emptyItem)
            else:
                childItem.setCheckable(True)
            #print(child)
            try:
                childItemSize = QStandardItem(child[2])
            except IndexError:
                childItemSize = emptyItem
            try:
                childItemDate = QStandardItem(child[1])
            except IndexError:
                childItemDate = emptyItem
            parentItem.appendRow([childItem, childItemSize, childItemDate])
            #print(childItem.text(), childItem.row(), childItem.column())
            #print(childItemSize.text(), childItemSize.row(), childItemSize.column())
            #print(childItemDate.text(), childItemDate.row(), childItemDate.column())

    def uncheckAll(self):
        """Slot of uncheck all button clicked signal that unchecks all products and options"""

        # Iterate trough products list
        for p in self.selectedProductsUrl:
            model = p[2].model()
            modelIndex = p[0]
            item = model.itemFromIndex(modelIndex)
            item.setCheckState(False)

        # Set label of selected products
        self.dlg.label_ProductsSelected.setText(self.tr(u'0 Product(s) selected'))
        # Clear products urls list
        self.selectedProductsUrl = []
        # Clear selections
        self.geoSelectionModel.clear()
        self.statSelectionModel.clear()
        self.selectedSearch = ''
        # Uncheck options
        self.dlg.checkBox_SearchSelectedOnly.setChecked(False)
        self.dlg.checkBox_SearchSelectedOnly.setEnabled(False)
        self.dlg.checkBox_Unzip.setChecked(False)
        self.dlg.checkBox_Unzip.setEnabled(False)
        self.dlg.checkBox_AddLayer.setChecked(False)
        self.dlg.checkBox_AddLayer.setEnabled(False)
        # Disable OK button
        self.checkOkButton()

    def searchWordTextChanged(self, text):
        """Standardizes text and enables or disables search button if text respects standard features"""

        # Starndardize text
        text = text.replace(' ', '_')
        self.dlg.lineEdit_SearchWord.setText(text)

        # Check if text respect standard structure
        if not any(c in text for c in (' ', ',', '.', ';', '?', 'zip', 'tar', 'shp', 'xls', 'ods', 'pdf')) and text != '':
            self.dlg.pushButton_Search.setEnabled(True)
        else:
            self.dlg.pushButton_Search.setEnabled(False)

    def treeViewSelectionChanged(self, selected, deselected):
        """Permits the selection only if column == 0, feed selectedSearch attribute"""

        _, treeView, selectionModel = self.getCurrentObjects(True)

        if selected.indexes():
            item = treeView.model().itemFromIndex(selected.indexes()[0])
            if item.column() > 0:
                selectionModel.clear()
                self.selectedSearch = ''
            else:
                # Define selected search
                productUrl = self.getItemUrl(selected.indexes()[0])
                self.selectedSearch = productUrl if os.path.splitext(productUrl)[1] == '' else ''
            # Enable or disable selected item search option
            self.radioButtonSearchGeoToggled(self.dlg.radioButton_SearchGeo.isChecked())

    def radioButtonSearchGeoToggled(self, checked):
        """Enables or disables search in selected only depending on the selectem item and FTP selected"""

        if self.selectedSearch != '':
            if checked:
                if self.selectedSearch.startswith('https://geo'):
                    self.dlg.checkBox_SearchSelectedOnly.setEnabled(True)
                else:
                    self.dlg.checkBox_SearchSelectedOnly.setEnabled(False)
            else:
                if self.selectedSearch.startswith('https://ftp'):
                    self.dlg.checkBox_SearchSelectedOnly.setEnabled(True)
                else:
                    self.dlg.checkBox_SearchSelectedOnly.setEnabled(False)
        else:
            self.dlg.checkBox_SearchSelectedOnly.setEnabled(False)

    def searchClicked(self):
        """Searches for products with typed word"""

        # Set background of highlighted items to default
        self.clearItemsHighlighted()

        # Search params
        root = self.geobaseUrl if self.dlg.radioButton_SearchGeo.isChecked() else self.statbaseUrl
        text = self.dlg.lineEdit_SearchWord.text()
        matchContains = self.dlg.checkBox_SearchContains.isChecked()
        matchScore = self.dlg.doubleSpinBox_MatchValue.value()

        # Collapsing all item in the three
        treeView = self.dlg.treeView_Geo if 'geo' in root else self.dlg.treeView_Stat
        treeView.collapseAll()

        # Preparing product search
        self.dlgBar, self.progressBar = self.progressDialog(0, self.tr(u'Searching data...'))
        self.dlgBar.show()
        self.msgBar.pushMessage(self.tr('Processing'), self.tr(u'Searching products with "{}" word.\nThis may take several minutes...').format(text), Qgis.Info, duration=0)
        # Adjusting button text
        self.dlgBarCancelButton.setText(self.tr('Interrupt'))

        # Instantiate the background worker and connects slots to signals
        taskDesc = u'{} {}.\n{}...'.format(self.tr(u'Searching'), text, self.tr('The search may take several minutes'))
        self.threadTask = WorkerSearchManager(
            self.iface,
            taskDesc,
            self.selectedSearch if self.dlg.checkBox_SearchSelectedOnly.isEnabled() and self.dlg.checkBox_SearchSelectedOnly.isChecked() else root,
            text,
            matchContains,
            matchScore
        )
        self.threadTask.begun.connect(lambda: self.setProgressText(taskDesc))
        self.threadTask.progressChanged.connect(self.setProgressValue)
        self.threadTask.barMax.connect(self.setMaximumProgressBar)
        self.threadTask.textProgress.connect(self.setProgressText)
        self.threadTask.processResult.connect(self.threadResult)
        self.threadTask.taskCompleted.connect(self.endingProcess)
        self.threadTask.taskTerminated.connect(self.endingProcess)
        self.taskManager.addTask(self.threadTask)
        # Hide QGIS native progress button
        self.qgisProgressButton.hide()

    def buttonHelpClicked(self):
        """Opens help dialog"""

        self.helpDialog.show()

    def configDialogs(self):
        """Configures dialog and connects signals/slots."""

        # Set window icon
        self.helpDialog.setWindowIcon(self.pluginIcon)
        self.dlg.setWindowIcon(self.pluginIcon)

        # Add top parent to the tree
        self.addTreeViewParentChildItem(self.dlg.treeView_Geo, os.path.basename(os.path.normpath(self.geobaseUrl)))
        self.addTreeViewParentChildItem(self.dlg.treeView_Stat, os.path.basename(os.path.normpath(self.statbaseUrl)))

        # Adjusting headers size mode
        self.dlg.treeView_Geo.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.dlg.treeView_Stat.header().setSectionResizeMode(QHeaderView.ResizeToContents)

        # Set selection mode
        self.dlg.treeView_Geo.setSelectionMode(QAbstractItemView.SingleSelection)
        self.dlg.treeView_Stat.setSelectionMode(QAbstractItemView.SingleSelection)

        # Keep references to selection models
        self.geoSelectionModel = self.dlg.treeView_Geo.selectionModel()
        self.statSelectionModel = self.dlg.treeView_Stat.selectionModel()

        # Connect signals to slots
        self.dlg.pushButton_Dir.clicked.connect(self.dlgDirOutput)
        self.dlg.treeView_Geo.clicked.connect(self.treeViewClicked)
        self.dlg.treeView_Geo.expanded.connect(self.treeViewExpanded)
        self.dlg.treeView_Geo.pressed.connect(self.treeViewPressed)
        self.dlg.treeView_Stat.clicked.connect(self.treeViewClicked)
        self.dlg.treeView_Stat.expanded.connect(self.treeViewExpanded)
        self.dlg.treeView_Stat.pressed.connect(self.treeViewPressed)
        self.dlg.pushButton_UncheckAll.clicked.connect(self.uncheckAll)
        self.dlg.checkBox_SearchContains.stateChanged.connect(self.searchExactStateChanged)
        self.dlg.lineEdit_SearchWord.textChanged.connect(self.searchWordTextChanged)
        self.dlg.pushButton_Search.clicked.connect(self.searchClicked)
        self.dlg.radioButton_SearchGeo.toggled.connect(self.radioButtonSearchGeoToggled)
        self.geoSelectionModel.selectionChanged.connect(self.treeViewSelectionChanged)
        self.statSelectionModel.selectionChanged.connect(self.treeViewSelectionChanged)
        self.dlg.button_box.button(QDialogButtonBox.Help).clicked.connect(self.buttonHelpClicked)

        # Populate tree for product selection
        #url = '{}organizacao_do_territorio/'.format(self.geobaseUrl)

        # Disable OK button
        self.dlg.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        self.dlg.button_box.button(QDialogButtonBox.Cancel).setText(self.tr('Cancel'))
        self.dlg.button_box.button(QDialogButtonBox.Help).setText(self.tr('Help'))
        # Disable options
        self.dlg.checkBox_Unzip.setEnabled(False)
        self.dlg.checkBox_AddLayer.setEnabled(False)
        self.dlg.pushButton_Search.setEnabled(False)

    def checkOkButton(self):
        """Enables or disables OK button"""

        if self.selectedProductsUrl:
            for p in self.selectedProductsUrl:
                if os.path.splitext(p[1])[1] != '' and self.dirOutput != '':
                    # Enable OK button
                    self.dlg.button_box.button(QDialogButtonBox.Ok).setEnabled(True)
                else:
                    # Disable OK button
                    self.dlg.button_box.button(QDialogButtonBox.Ok).setEnabled(False)
        else:
            # Disable OK button
            self.dlg.button_box.button(QDialogButtonBox.Ok).setEnabled(False)

    def execute(self):
        """Does the real work:
           -Download file
           -Extract file, if checked
           -Add selected statistical data *** NOT IMPLEMENTED
           -Add layer to legend panel *** NOT IMPLEMENTED"""

        # Preparing product download
        self.dlgBar, self.progressBar = self.progressDialog(0, self.tr(u'Downloading data...'))
        self.dlgBar.show()
        self.msgBar.pushMessage(self.tr('Processing'), self.tr(u'Working on selected data...'), Qgis.Info, duration=0)

        # Instantiate the background worker and connects slots to signals
        taskDesc = self.tr(u'Processing selected data.')
        self.threadTask = WorkerDownloadManager(
            self.iface,
            taskDesc,
            self.selectedProductsUrl,
            self.dirOutput,
            [self.dlg.checkBox_Unzip.isEnabled(), self.dlg.checkBox_Unzip.isChecked()]
        )
        self.threadTask.begun.connect(lambda: self.setProgressText(taskDesc))
        self.threadTask.progressChanged.connect(self.setProgressValue)
        self.threadTask.barMax.connect(self.setMaximumProgressBar)
        self.threadTask.textProgress.connect(self.setProgressText)
        self.threadTask.processResult.connect(self.threadResult)
        self.threadTask.taskCompleted.connect(self.endingProcess)
        self.threadTask.taskTerminated.connect(self.endingProcess)
        self.taskManager.addTask(self.threadTask)
        # Hide QGIS native progress button
        self.qgisProgressButton.hide()

    def run(self):
        """Run method - plugin callback"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.firstStart:
            self.firstStart = False
            self.dlg = IbgeDataDownloaderDialog()
            self.helpDialog = HelpDialog(self.dlg)
            self.configDialogs()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            self.execute()
