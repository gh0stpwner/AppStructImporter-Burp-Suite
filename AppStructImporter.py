"""
Name:           AppStruct Importer
Date:           11/03/2020
Author:         TheNerdOne
Contact:        salvador.diogogomes@gmail.com
Description:    AppStruct Importer is a Burp Suite extension written in python which allows users to 
                load a list of URLs or a file structure directly from the folder and populate your burp targets sitemap with successful connections.
Copyright (c) 2020, Visionware (https://www.visionware.pt)
All rights reserved.
Credits to SmeegeSec, Antonio Sanchez and Dionach

I developed a initial python script that made all of these features by itself but it wasn't integrated with Burp so, i started developing a the same tool with Burp Extensions method when i realized that already existed two unsupported tools that could help me.
This tools are not complete but i used them as a base program to work my ideas and develop the actual plugin.
Tool 1 Folder Scraping and URL Generator ---> https://github.com/SmeegeSec/Directory_File_Listing_Parser_Importer
https://www.smeegesec.com/2013/07/burp-extension-directory-and-file.html
Tool 2 URL Parser and Sitemap Importer ---> https://github.com/SmeegeSec/Burp-Importer
https://www.smeegesec.com/2016/02/burp-suite-extension-burp-importer.html
"""

from burp import IExtensionStateListener
from burp import IBurpExtender
from burp import ITab
from datetime import datetime
from javax import swing
from java.awt import Color
from java.awt import Font
from java.awt import Toolkit
from java.awt.datatransfer import StringSelection
from java.awt.datatransfer import DataFlavor
from java.net import URL
import thread
import java.lang as lang
import os
import re
import xml.dom.minidom
from java.awt import BorderLayout
from javax.swing import JFileChooser, JFrame, JPanel, JOptionPane
import sys,getopt,subprocess,time


class BurpExtender(IBurpExtender, ITab, IExtensionStateListener):

    def	registerExtenderCallbacks(self, callbacks):
        
        print "Loading AppStruct Importer Extension..."

        self._callbacks = callbacks
        self._callbacks.setExtensionName("AppStruct Importer")
        self._callbacks.registerExtensionStateListener(self)
        
        self._helpers = callbacks.getHelpers()

        self.initGui()
        self._callbacks.addSuiteTab(self)

        print "\nExtension Loaded!"

        return

    def initGui(self):
        self.tab = swing.JPanel()
        self.titleLabel = swing.JLabel("AppStruct Importer")
        self.titleLabel.setFont(Font("Tahoma", 1, 16))
        self.titleLabel.setForeground(Color(235,136,0))
        self.infoLabel = swing.JLabel("A tool to populate your target sitemap when you have a list o URLs or even the source running on the server.")
        self.infoLabel.setFont(Font("Tahoma", 0, 12))
        self.fileOptionLabel = swing.JLabel("File Load Option")
        self.fileOptionLabel.setFont(Font("Tahoma", 1, 12))
        self.fileDescLabel = swing.JLabel("Select the file where you already have a list o URLs to be parsed.")
        self.fileDescLabel.setFont(Font("Tahoma", 0, 12))
        self.fileDescLabel2 = swing.JLabel("Supported files: .gnamp, .nessus, .txt")
        self.fileDescLabel2.setFont(Font("Tahoma", 0, 12))
        self.parseFileButton = swing.JButton("Load File to Parse", actionPerformed=self.loadFile)
        self.folderOptionLabel = swing.JLabel("Folder Load Option")
        self.folderOptionLabel.setFont(Font("Tahoma", 1, 12))
        self.folderDescLabel = swing.JLabel("Select the folder where you have your target server files to generate a list of URLs and import them into your target sitemap.")
        self.folderDescLabel.setFont(Font("Tahoma", 0, 12))
        self.parseFolderButton = swing.JButton("Set Folder to Parse", actionPerformed=self.setFolder)
        self.addWebsiteField = swing.JTextField("Enter the base URL...", focusGained=self.clearField, focusLost=self.fillField)
        self.urlLabel = swing.JLabel("URL List")
        self.urlLabel.setFont(Font("Tahoma", 1, 12))
        self.urlDescLabel = swing.JLabel("URLs in this list should be in the format: protocol://host:port/path")
        self.urlDescLabel.setFont(Font("Tahoma", 0, 12))
        self.urlDescLabel2 = swing.JLabel("Example: https://127.0.0.1:443/index. Port is optional, 80 or 443 will be assumed.")
        self.urlDescLabel2.setFont(Font("Tahoma", 0, 12))
        self.pasteButton = swing.JButton("Paste", actionPerformed=self.paste)
        self.loadButton = swing.JButton("Copy List", actionPerformed=self.setClipboardText)
        self.removeButton = swing.JButton("Remove", actionPerformed=self.remove)
        self.clearButton = swing.JButton("Clear", actionPerformed=self.clear)
        self.saveButton = swing.JButton("Save List", actionPerformed=self.save)
        self.urlListModel = swing.DefaultListModel()
        self.urlList = swing.JList(self.urlListModel)
        self.urlListPane = swing.JScrollPane(self.urlList)
        self.addButton = swing.JButton("Add", actionPerformed=self.addURL)
        self.runLabelTitle = swing.JLabel("Parse to Sitemap")
        self.runLabelTitle.setFont(Font("Tahoma", 1, 12))
        self.runLabel = swing.JLabel("<html>Load the URL list to your target sitemap by clicking the following button. (If you desire to make all the requests with a specific cookie, you can input it on Project Options -> Sessions-> Cookie Jar) </html>")
        self.runLabel.setFont(Font("Tahoma", 0, 12))
        self.redirectsCheckbox = swing.JCheckBox("Enable: Follow Redirects (301 or 302 Response)")
        self.runButton = swing.JButton("Parse", actionPerformed=self.runClicked)
        self.runButton.setFont(Font("Tahoma", 1, 12))
        self.addUrlField = swing.JTextField("New URL...", focusGained=self.clearField, focusLost=self.fillField)
        self.logLabel = swing.JLabel("Output Console")
        self.logLabel.setFont(Font("Tahoma", 1, 12))
        self.logPane = swing.JScrollPane()
        self.logArea = swing.JTextArea("AppStruct Importer Log - Parsing and Run details will be appended here.\n")
        self.logArea.setLineWrap(True)
        self.logPane.setViewportView(self.logArea)
        self.webPortDict = {'80':'http','81':'http','82':'http','83':'http','443':'https','2301':'http','2381':'https','8000':'http','8008':'http','8080':'http','8083':'https','8180':'http','8400':'http',\
        '8443':'https','8834':'https','8888':'http','9001':'http','9043':'https','9080':'http','9090':'http','9100':'http','9443':'https'}
        self.bar = swing.JSeparator(swing.SwingConstants.HORIZONTAL)
        self.bar2 = swing.JSeparator(swing.SwingConstants.HORIZONTAL)
        self.bar3 = swing.JSeparator(swing.SwingConstants.HORIZONTAL)
        layout = swing.GroupLayout(self.tab)
        self.tab.setLayout(layout)
        
        layout.setHorizontalGroup(
            layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addGap(15)
                .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
                    .addComponent(self.titleLabel)
                    .addComponent(self.infoLabel)
                    .addComponent(self.fileOptionLabel)
                    .addComponent(self.fileDescLabel)
                    .addComponent(self.fileDescLabel2)
                    .addComponent(self.parseFileButton)
                    .addComponent(self.folderOptionLabel)
                    .addComponent(self.folderDescLabel)
                    .addComponent(self.parseFolderButton)
                    .addComponent(self.bar)
                    .addComponent(self.urlLabel)
                    .addComponent(self.urlDescLabel)
                    .addComponent(self.urlDescLabel2)
                    .addComponent(self.bar2)
                    .addComponent(self.runLabelTitle)
                    .addComponent(self.runLabel)
                    .addComponent(self.redirectsCheckbox)
                    .addComponent(self.runButton)
                    .addComponent(self.bar3)
                    .addComponent(self.logPane, swing.GroupLayout.PREFERRED_SIZE, 525, swing.GroupLayout.PREFERRED_SIZE)
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.TRAILING)
                            .addComponent(self.addButton)
                            .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
                                .addComponent(self.logLabel)
                                .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.TRAILING, False)
                                    .addComponent(self.removeButton, swing.GroupLayout.DEFAULT_SIZE, swing.GroupLayout.DEFAULT_SIZE, lang.Short.MAX_VALUE)
                                    .addComponent(self.pasteButton, swing.GroupLayout.DEFAULT_SIZE, swing.GroupLayout.DEFAULT_SIZE, lang.Short.MAX_VALUE)
                                    .addComponent(self.loadButton, swing.GroupLayout.DEFAULT_SIZE, swing.GroupLayout.DEFAULT_SIZE, lang.Short.MAX_VALUE)
                                    .addComponent(self.clearButton, swing.GroupLayout.DEFAULT_SIZE, swing.GroupLayout.PREFERRED_SIZE, lang.Short.MAX_VALUE)
                                    .addComponent(self.saveButton, swing.GroupLayout.DEFAULT_SIZE, swing.GroupLayout.PREFERRED_SIZE, lang.Short.MAX_VALUE))))
                        .addPreferredGap(swing.LayoutStyle.ComponentPlacement.UNRELATED)
                        .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
                            .addComponent(self.urlListPane, swing.GroupLayout.PREFERRED_SIZE, 350, swing.GroupLayout.PREFERRED_SIZE)
                            .addComponent(self.addUrlField, swing.GroupLayout.PREFERRED_SIZE, 350, swing.GroupLayout.PREFERRED_SIZE))))
                .addContainerGap(26, lang.Short.MAX_VALUE)))

        layout.setVerticalGroup(
            layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
            .addGroup(layout.createSequentialGroup()
                .addGap(15)
                .addComponent(self.titleLabel)
                .addGap(10)
                .addComponent(self.infoLabel)
                .addGap(10)
                .addComponent(self.fileOptionLabel)
                .addGap(10)
                .addComponent(self.fileDescLabel)
                .addGap(10)
                .addComponent(self.fileDescLabel2)
                .addGap(10)
                .addComponent(self.parseFileButton)
                .addGap(10)
                .addComponent(self.folderOptionLabel)
                .addGap(10)
                .addComponent(self.folderDescLabel)
                .addGap(10)
                .addComponent(self.parseFolderButton)
                .addGap(10)
                .addComponent(self.bar)
                .addComponent(self.urlLabel)
                .addGap(10)
                .addComponent(self.urlDescLabel)
                .addGap(10)
                .addComponent(self.urlDescLabel2)
                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.UNRELATED)
                .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
                    .addGroup(layout.createSequentialGroup()
                        .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.LEADING)
                            .addGroup(layout.createSequentialGroup()
                                .addComponent(self.pasteButton)
                                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(self.loadButton)
                                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(self.removeButton)
                                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(self.clearButton)
                                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.RELATED)
                                .addComponent(self.saveButton))
                            .addComponent(self.urlListPane, swing.GroupLayout.PREFERRED_SIZE, 160, swing.GroupLayout.PREFERRED_SIZE))
                        .addGap(10)
                        .addGroup(layout.createParallelGroup(swing.GroupLayout.Alignment.BASELINE)
                            .addComponent(self.addButton)
                            .addComponent(self.addUrlField, swing.GroupLayout.PREFERRED_SIZE, swing.GroupLayout.DEFAULT_SIZE, swing.GroupLayout.PREFERRED_SIZE))))
                .addGap(10)
                .addComponent(self.bar2)
                .addComponent(self.runLabelTitle)
                .addGap(10)
                .addComponent(self.runLabel)
                .addGap(10)
                .addComponent(self.redirectsCheckbox)
                .addGap(10)
                .addComponent(self.runButton)
                .addGap(10)
                .addComponent(self.bar3)
                .addGap(10)
                .addComponent(self.logLabel)
                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.RELATED)
                .addGap(8, 8, 8)
                .addComponent(self.logPane, swing.GroupLayout.PREFERRED_SIZE, 125, swing.GroupLayout.PREFERRED_SIZE)
                .addPreferredGap(swing.LayoutStyle.ComponentPlacement.RELATED)
                .addContainerGap(swing.GroupLayout.DEFAULT_SIZE, lang.Short.MAX_VALUE)))
        return

    def getListOfFiles(self,dirName):
        files= []
        for r, d, f in os.walk(dirName):
            for file in f:
                files.append(os.path.join(r, file))
        return files

    def getTabCaption(self):
        return("AppStruct Importer")

    def getUiComponent(self):
        return self.tab

    def clear(self, e):
        emptyList = []
        self.urlList.setListData(emptyList) 
        currentTime = str(datetime.now()).split('.')[0]            
        self.logArea.append('[%s] URL list cleaned. %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def save(self, e):     
        chooseFile = swing.JFileChooser()
        fileDialog = chooseFile.showDialog(self.tab, "Choose file")
        if fileDialog == swing.JFileChooser.APPROVE_OPTION:
            file = chooseFile.getSelectedFile()
            filename = file.getCanonicalPath()
            fileExtension = os.path.splitext(filename)[1]   
        with open(filename+'.txt','w') as f:
                for elem in self.getUrlList():
                    f.write("%s\n" % elem)
        currentTime = str(datetime.now()).split('.')[0]            
        self.logArea.append('[%s] URL list saved to file. %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def clearField(self, e):
        source = e.getSource()
        if source.getText() == "New URL...":
            source.setText("")

    def fillField(self, e):
        source = e.getSource()
        if not source.getText():
            source.setText("New URL...")

    def remove(self, e):
        indices = self.urlList.getSelectedIndices().tolist()
        currentList = self.getUrlList()
        for index in reversed(indices):   
            del currentList[index]
        self.urlList.setListData(currentList)
        

    def paste(self, e):
        clipboard = self.getClipboardText()        
        if clipboard != None and clipboard != "":
            lines = clipboard.split('\n')
            currentList = self.getUrlList()            
            for line in lines:
                if line not in currentList and not line.isspace():
                    currentList.append(line)            
            self.urlList.setListData(currentList)
        currentTime = str(datetime.now()).split('.')[0]            
        self.logArea.append('[%s] URL new paste. %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def plaintext(self, loadedFile):
        text = loadedFile.readlines()
        currentList = self.getUrlList()        
        for item in text:
            currentList.append(item)        
        self.urlList.setListData(currentList)        
        currentTime = str(datetime.now()).split('.')[0]
        self.logArea.append('[%s] URL List Updated: %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def addURL(self, e):
        currentList = self.getUrlList()
        currentList.append(self.addUrlField.getText())
        self.urlList.setListData(currentList)
        self.addUrlField.setText("New URL...")
        currentTime = str(datetime.now()).split('.')[0]
        self.logArea.append('[%s] URL List Updated: %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def getUrlList(self):
        model = self.urlList.getModel()
        currentList = []   
        for i in range(0, model.getSize()):
            currentList.append(model.getElementAt(i))
        return currentList

    def getClipboardText(self):
        clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
        contents = clipboard.getContents(None)
        gotText = (contents != None) and contents.isDataFlavorSupported(DataFlavor.stringFlavor)
        
        if gotText:
            return contents.getTransferData(DataFlavor.stringFlavor)
        else:
            return None

    def setClipboardText(self, e):
        clipboard = Toolkit.getDefaultToolkit().getSystemClipboard()
        stringUrlList = '\n'.join(self.getUrlList())
        clipboard.setContents(StringSelection(stringUrlList), None)

    def runClicked(self, e):
        args = ()
        thread.start_new_thread(self.runURLs, args)
        return
        
    def runURLs(self):
        self.badUrlList = []
        self.goodUrlList = []
        self.redirectCounter = 0
        self.urlRegex = re.compile('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        urlList = filter(None, self.getUrlList())
        
        for url in urlList:
            if self.urlRegex.match(url):
                self.connect(url)
            else:
                self.badUrlList.append(url)
        currentTime = str(datetime.now()).split('.')[0]
        if self.goodUrlList:
            print '[%s] Number of successful connections: %d/%d\n' % (currentTime, len(self.goodUrlList), len(urlList) + self.redirectCounter)
            self.logArea.append('[%s] Number of successful connections: %d/%d\n' % (currentTime, len(self.goodUrlList), len(urlList) + self.redirectCounter))
        else:
            print '[%s] Number of successful connections: 0/%d\n' % (str(datetime.now()).split('.')[0], len(urlList) + self.redirectCounter)
            self.logArea.append('[%s] Number of successful connections: 0/%d\n' % (currentTime, len(urlList) + self.redirectCounter))
        if self.redirectsCheckbox.isSelected():
            print '[%s] Number of redirects found: %d\n' % (currentTime, self.redirectCounter)
            self.logArea.append('[%s] Number of redirects found: %d\n' % (currentTime, self.redirectCounter))

        if self.badUrlList:
            print '[%s] Incorrect URL format or issue connecting:\n' % currentTime
            self.logArea.append('[%s] Incorrect URL format or issue connecting:\n' % currentTime)
            for badUrl in self.badUrlList:
                print '\t' + badUrl
                self.logArea.append('\t' + badUrl + '\n')
        print '\n'

    def connect(self, url):
        if re.findall('(?:\:\d{2,5})', url) and self.urlRegex.match(url):
            try:
                javaURL = URL(url)
                newRequest = self._helpers.buildHttpRequest(javaURL)
                requestResponse = self._callbacks.makeHttpRequest(self._helpers.buildHttpService(str(javaURL.getHost()), javaURL.getPort(), str(javaURL.getProtocol())), newRequest)
                response = requestResponse.getResponse()
                if response:
                    requestInfo = self._helpers.analyzeResponse(response)
                    responseHeader = requestInfo.getHeaders()
                    if ('301' in responseHeader[0] or '302' in responseHeader[0]) and self.redirectsCheckbox.isSelected():
                        self.redirectCounter += 1
                        for headerLine in responseHeader:
                            if 'Location: ' in headerLine or 'location: ' in headerLine:
                                url = self.locationHeaderConvert(str(headerLine.split(' ')[1]), str(javaURL.getPort()), str(javaURL.getHost()), '')
                                self.connect(url)
                    currentTime = str(datetime.now()).split('.')[0]     
                    print '[%s] Good URL found! - %s\n' % (currentTime,url)
                    print '[%s] Response: %s\n' %  (currentTime,responseHeader[0])
                    self.goodUrlList.append(url)
                    self._callbacks.addToSiteMap(requestResponse)
                else:
                    currentTime = str(datetime.now()).split('.')[0]     
                    print '[%s] Bad URL found! - %s\n' % (currentTime,url)
                    self.badUrlList.append(url)
            except:
                currentTime = str(datetime.now()).split('.')[0]     
                print '[%s] Bad URL found! - %s\n' % (currentTime,url)
                self.badUrlList.append(url)
        else:
            if 'http://' in url:
                fixedUrl = self.addPort(url, '80')
                self.connect(fixedUrl)
            elif 'https://' in url:
                fixedUrl = self.addPort(url, '443')
                self.connect(fixedUrl)
            else:
                currentTime = str(datetime.now()).split('.')[0]     
                print '[%s] Bad URL found!\n' % currentTime
                self.badUrlList.append(url)

    def addPort(self, url, port):
        fixedUrl = ""
        urlSplit = filter(None, url.split('/'))

        for i in range(len(urlSplit) + 1):
            fixedUrl += str(url.split('/')[i])
            if i == 1:
                fixedUrl += '//'
            elif i == 2:
                fixedUrl += ':%s/' % port
            elif i > 2 and i < len(urlSplit):
                fixedUrl += '/'
            elif i == len(urlSplit) and url[-1:] == '/':
                fixedUrl += '/'

        return fixedUrl

    def loadFile(self, e):
        chooseFile = swing.JFileChooser()
        fileDialog = chooseFile.showDialog(self.tab, "Choose file")

        if fileDialog == swing.JFileChooser.APPROVE_OPTION:
            file = chooseFile.getSelectedFile()
            filename = file.getCanonicalPath()
            fileExtension = os.path.splitext(filename)[1]

            try:
                loadedFile = open(filename, "r")
            except IOError as e:
                print "Error reading file.\n" + str(e)
                self.logArea.append('\nError reading File: %s' % filename)

            if fileExtension == '.gnmap':
                self.nmap(loadedFile)
            elif fileExtension == '.nessus':
                self.nessus(loadedFile)
            elif fileExtension == '.txt':
                self.plaintext(loadedFile)
            else:
                print '\nFile %s was read but does not have the correct extension (.gnmap, .nessus, .txt).' % filename
                self.logArea.append('\nFile %s was read but does not have the correct extension (.gnmap, .nessus, .txt).' % filename)

    def setFolder(self, e):
        chooseFolder = swing.JFileChooser()
        chooseFolder.setFileSelectionMode(JFileChooser.DIRECTORIES_ONLY);
        folderDialog = chooseFolder.showDialog(self.tab, "Choose Folder")
        if folderDialog == JFileChooser.APPROVE_OPTION:
            if chooseFolder.getSelectedFile().isDirectory():
                self.file_name = str(chooseFolder.getSelectedFile())
        print '\nFolder selected: %s' % self.file_name
        listOfFiles = self.getListOfFiles(self.file_name)
        currentList = self.getUrlList()        
        path = JOptionPane.showInputDialog("http(s)://[IP]:[PORT]");
        for elem in listOfFiles:
            newElem = elem.replace(self.file_name,path)
            currentList.append(newElem)        
        self.urlList.setListData(currentList)
        currentTime = str(datetime.now()).split('.')[0]
        self.logArea.append('[%s] URL List Updated: %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def nmap(self, loadedFile):
        urlList = self.getUrlList()
        for line in loadedFile.readlines():
            if 'Ports' in line and 'open' in line:
                lineSplit = line.split(' ')
                host = lineSplit[1]
                for openPort in lineSplit[3:]:
                    openPortSplit = openPort.split('/')
                    if '/' in openPort:
                        if openPortSplit[1] == 'open' and openPortSplit[0] in self.webPortDict:
                            urlList.append(self.webPortDict[openPortSplit[0]] + '://' + host + ':' + openPortSplit[0])
        self.urlList.setListData(urlList)
        currentTime = str(datetime.now()).split('.')[0]
        self.logArea.append('[%s] URL List Updated: %d \n' % (currentTime, self.urlList.getModel().getSize()))
            
    def nessus(self, loadedFile):
        urlList = self.getUrlList()
        dom = xml.dom.minidom.parse(loadedFile)
        reportHost = dom.getElementsByTagName('ReportHost')

        for host in reportHost:
            hostIP = host.getAttribute('name')
            for reportItem in host.getElementsByTagName('ReportItem'):
                if reportItem.getAttribute('pluginID') == '24260':
                    port = str(reportItem.getAttribute('port'))
                    pluginOutput = reportItem.getElementsByTagName('plugin_output')[0].firstChild.nodeValue
                    locationHeader = re.search('Location: (.+?)\n', pluginOutput)
                    if locationHeader:
                        url = self.locationHeaderConvert(str(locationHeader.group(1)), port, hostIP, pluginOutput)
                    else:
                        if 'SSL : no' in pluginOutput:
                            url = 'http://' + hostIP + ':' + port + '/'
                            
                        elif 'SSL : yes' in pluginOutput:
                            url = 'https://' + hostIP + ':' + port + '/'
                        else:
                            if port in self.webPortDict.iterkeys():
                                url = self.webPortDict[port] + '://' + hostIP + ':' + port + '/'
                            else:
                                url = 'http://' + hostIP + ':' + port + '/'
                    urlList.append(url)
        self.urlList.setListData(urlList)
        currentTime = str(datetime.now()).split('.')[0]
        self.logArea.append('[%s] URL List Updated: %d \n' % (currentTime, self.urlList.getModel().getSize()))

    def locationHeaderConvert(self, locationHeader, port, host, pluginOutput):
        url = ""

        if 'http://' in locationHeader or 'https://' in locationHeader:
            if re.findall('(?:\:\d{2,5})', locationHeader):
                url = locationHeader
            else:
                url = self.addPort(locationHeader, port)
                if 'http://' in url and port == '443':
                    url = url.replace(':443', ':80')
                elif 'https://' in url and port == '80':
                    url = url.replace(':80', ':443')
        else:
            if 'SSL : no' in pluginOutput:
                url = 'http://' + host + ':' + port + locationHeader
            elif 'SSL : yes' in pluginOutput:
                url = 'https://' + host + ':' + port + locationHeader
            else:
                if locationHeader[0] is not '/':
                    locationHeader = '/' + locationHeader
                if port in self.webPortDict.iterkeys():
                    url = self.webPortDict[port] + '://' + host + ':' + port + locationHeader
                else:
                    url = 'http://' + host + ':' + port + locationHeader
        return url
