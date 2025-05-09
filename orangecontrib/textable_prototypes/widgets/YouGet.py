"""
Class DemoTextableWidget
Copyright 2025 University of Lausanne
-----------------------------------------------------------------------------
This file is part of the Orange3-Textable-Prototypes package.

Orange3-Textable-Prototypes is free software: you can redistribute 
it and/or modify it under the terms of the GNU General Public License 
as published by the Free Software Foundation, either version 3 of the
License, or (at your option) any later version.

Orange3-Textable-Prototypes is distributed in the hope that it will 
be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Orange3-Textable-Prototypes. If not, see
 <http://www.gnu.org/licenses/>.
"""

__version__ = '0.0.1'
__author__ = "Virgile Albasini, Sophie Ward, Lorelei Chevroulet, Vincent Joris "
__maintainer__ = "Aris Xanthos"
__email__ = "aris.xanthos@unil.ch"


from functools import partial
import time

from _textable.widgets.TextableUtils import (
    OWTextableBaseWidget, VersionedSettingsHandler, ProgressBar,
    InfoBox, SendButton, pluralize, Task
)

from LTTL.Segmentation import Segmentation
from LTTL.Input import Input


# Using the threaded version of LTTL.Segmenter to create
# a "responsive" widget.
import LTTL.SegmenterThread as Segmenter

from Orange.widgets import widget, gui, settings
from Orange.widgets.utils.widgetpreview import WidgetPreview

from youtube_comment_downloader import *
# pour tester l'url
import requests

import re

# import re
import http

from PyQt5.QtWidgets import QMessageBox
from Orange.widgets.settings import Setting


class YouGet(OWTextableBaseWidget):
    """Demo Orange3-Textable widget"""

    name = "YouGet"
    description = "Widget that downloads comments from a youtube URL"
    icon = "icons/YouGet.svg"
    priority = 99

    # Input and output channels (remove if not needed)...
    inputs = []
    outputs = [("New segmentation", Segmentation)]

    # Copied verbatim in every Textable widget to facilitate 
    # settings management.
    settingsHandler = VersionedSettingsHandler(
        version=__version__.rsplit(".", 1)[0]
    )

    # Settings...
    #url = settings.Setting("https://www.youtube.com/watch?v=ScMzIvxBSi4")
    url = settings.Setting("")

    # widget will fetch n=0 comments -> default is all
    n_desired_comments = 0

    #numberOfSegments = settings.Setting("10")


    want_main_area = False

    #------------------------code emprunté--------------------
    DOIs = Setting([])
    autoSend = settings.Setting(False)
    importDOIs = Setting(True)
    importDOIsKey = Setting(u'url')
    DOI = Setting(u'')

    # Ici-dessous les variables qui n'ont pas été copiées, et conçues spécialement pour SciHubator
    importAll = Setting(True)
    importAbstract = Setting(False)
    importText = Setting(False)
    importBibliography = Setting(False)
    #------------------------code emprunté fin-----------------------------


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        #----------------------- code emprunté à scihub--------------------
        self.URLLabel = list()
        self.selectedURLLabel = list()
        self.new_url = u''
        self.extractedText = u''
        self.DOI = u''
        self.DOIs = list()
        #-----------------------code emprunté fin------------------------------

        # Attributes...
        self.inputSegmentationLength = 0

        # This attribute stores scraped comments to prevent duplicate
        # queries and make the widget both faster and less resource-intensive.
        # Comments are stored as follows:
        # 'url': list of comments on url
        self.cached_comments = {}

        # This attribute stores a per-widget number of comments desired as
        # output. This can be changed by the user at any time via the GUI.
        n_desired_comments = 0
        
        # The following attribute is required by every widget
        # that imports new strings into Textable.
        self.createdInputs = list()

        self.infoBox = InfoBox(widget=self.controlArea)
        self.sendButton = SendButton(
            widget=self.controlArea,
            master=self,
            callback=self.sendData,
            cancelCallback=self.cancel_manually,
            infoBoxAttribute="infoBox",
        ) 
# notre vieux code >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>
        # GUI...

        # Top-level GUI boxes are created using method
        # create_widgetbox(), so that they are automatically
        # enabled/disabled when processes are running.
        # optionsBox = self.create_widgetbox(
        #     box=u'Source',
        #     orientation='vertical',
        #     addSpace=False,
        #     )

        # GUI elements can be assigned to variables or even
        # attributes (e.g. self.segmentContentLineEdit) if 
        # they must be referred to elsewhere, e.g., to enable
        # or disable them, etc. It is not the case below.
#         gui.lineEdit(
#             widget=optionsBox,
#             master=self,
#             value="url",
#             orientation="horizontal",
#             label="Url :",
#             labelWidth=130,
#             # self.sendButton.settingsChanged should be used in 
#             # in cases where using a GUI element should result
#             # in sending data to output. If it should result in
#             # other operations being done, use a custom method 
#             # instead, and at the end of it, if data should be
#             # sent to output, call self.sendButton.settingsChanged(). 
#             # If using the GUI element should not result in   
#             # anything at that moment, delete the "callback" 
#             # parameter.
#             callback=self.sendButton.settingsChanged,
#             tooltip=(
#                 "A string that defines the content "
#                 "each segment."
#             ),
#         )
        
# #        gui.comboBox(
# #           widget=optionsBox,
# #            master=self,
# #            value="numberOfSegments",
# #            items=["1", "10", "100", "1000", "10000"],
# #            sendSelectedValue=True,
# #            orientation='horizontal',
# #            label="Number of segments:",
# #            labelWidth=130,
# #            callback=self.sendButton.settingsChanged,
# #            tooltip="Number of segments to create.",
# #        )

#         # Stretchable vertical spacing between "options"
#         # and Send button etc.
#         gui.rubber(self.controlArea)

#         # Draw send button & Info box...
#         self.sendButton.draw()
#         self.infoBox.draw()
        
#         # Send data if needed. 
#         self.sendButton.settingsChanged()

# vieux code fin >>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>


        # -------------- code emprunté à SciHub ------------------------
        # URL box
        URLBox = gui.widgetBox(
            widget=self.controlArea,
            box=u'Sources',
            orientation='vertical',
            addSpace=False,
        )
        URLBoxLine1 = gui.widgetBox(
            widget=URLBox,
            box=False,
            orientation='horizontal',
            addSpace=True,
        )
        self.fileListbox = gui.listBox(
            widget=URLBoxLine1,
            master=self,
            value='selectedURLLabel',
            labels='URLLabel',
            callback=self.updateURLBoxButtons,
            tooltip=(
                u"The list of DOIs whose content will be imported.\n"
                u"\nIn the output segmentation, the content of each\n"
                u"URL appears in the same position as in the list.\n"
                u"\nColumn 1 shows the URL.\n"
                u"Column 2 shows the associated annotation (if any).\n"
                u"Column 3 shows the associated encoding."
            ),
        )
        URLBoxCol2 = gui.widgetBox(
            widget=URLBoxLine1,
            orientation='vertical',
        )
        self.removeButton = gui.button(
            widget=URLBoxCol2,
            master=self,
            label=u'Remove',
            callback=self.remove,
            tooltip=(
                u"Remove the selected URL from the list."
            ),
            disabled = True,
        )
        self.clearAllButton = gui.button(
            widget=URLBoxCol2,
            master=self,
            label=u'Clear All',
            callback=self.clearAll,
            tooltip=(
                u"Remove all DOIs from the list."
            ),
            disabled = True,
        )
        URLBoxLine2 = gui.widgetBox(
            widget=URLBox,
            box=False,
            orientation='vertical',
        )
        # Add URL box
        addURLBox = gui.widgetBox(
            widget=URLBoxLine2,
            box=True,
            orientation='vertical',
            addSpace=False,
        )
        gui.lineEdit(
            widget=addURLBox,
            master=self,
            value='new_url',
            orientation='horizontal',
            label=u'URLS(s):',
            labelWidth=101,
            callback=self.updateURLBoxButtons,
            tooltip=(
                u"The DOI(s) that will be added to the list when\n"
                u"button 'Add' is clicked.\n\n"
                u"Successive DOIs must be separated with ' / ' \n"
                u"(space + slash + space). Their order in the list\n"
                u" will be the same as in this field."
            ),
        )
        advOptionsBox = gui.widgetBox(
            widget=self.controlArea,
            box=u'More Options',
            orientation='vertical',
            addSpace=False,
        )
        optionLine1 = gui.widgetBox(
            widget=advOptionsBox,
            box=False,
            orientation='horizontal',
            addSpace=True,
        )
        commentsSelector = gui.comboBox(
            widget=advOptionsBox,
            master=self,
            value='n_desired_comments',
            label='Select number of comments:',
            tooltip='Default 0 is all comments.',
            items=[1, 5, 10, 100, 1000, 10000, 0],
            #sendSelectedValue=True,
        )

        # gui.checkBox(
        #     widget=advOptionsBox,
        #     master=self,
        #     value='importAll',
        #     label=u'All',
        #     labelWidth=180,
        #     callback=self.sendButton.settingsChanged,
        #     tooltip=(
        #         u"Import DOIs as annotations."
        #     ),
        # )
        # gui.separator(widget=advOptionsBox, height=3)
        # gui.checkBox(
        #     widget=advOptionsBox,
        #     master=self,
        #     value='importAbstract',
        #     label=u'Abstract',
        #     labelWidth=180,
        #     callback=self.sendButton.settingsChanged,
        #     tooltip=(
        #         u"Import DOIs as annotations."
        #     ),
        # )
        # gui.separator(widget=advOptionsBox, height=3)
        # gui.checkBox(
        #     widget=advOptionsBox,
        #     master=self,
        #     value='importText',
        #     label=u'Top Level Sections',
        #     labelWidth=180,
        #     callback=self.sendButton.settingsChanged,
        #     tooltip=(
        #         u"Import DOIs as annotations."
        #     ),
        # )
        # gui.separator(widget=advOptionsBox, height=3)
        # gui.checkBox(
        #     widget=advOptionsBox,
        #     master=self,
        #     value='importBibliography',
        #     label=u'Bibliography',
        #     labelWidth=180,
        #     callback=self.sendButton.settingsChanged,
        #     tooltip=(
        #         u"Import DOIs as annotations."
        #     ),
        # )
        gui.separator(widget=addURLBox, height=3)
        self.addButton = gui.button(
            widget=addURLBox,
            master=self,
            label=u'Add',
            callback=self.add,
            tooltip=(
                u"Add the URL currently displayed in the 'URL'\n"
                u"text field to the list."
            ),
            disabled = True,
        )
        gui.rubber(self.controlArea)
        self.sendButton.draw()
        self.infoBox.draw()
        self.sendButton.sendIf()
        # -------------- code emprunté fin ------------------------

    def sendData(self):
        """Perform every required check and operation 
        before calling the method that does the actual 
        processing.
        """
        # Déplacé plus bas, dans add
        # if self.url == "":
        #     # Use mode "warning" when user needs to do some
        #     # action or provide some information; use mode "error"
        #     # when invalid parameters have been provided; 
        #     # for notifications that don't require user action,
        #     # don't use a mode. Use formulations that emphasize
        #     # what should be done rather than what is wrong or
        #     # missing.
        #     self.infoBox.setText("Please add a YouTube URL.", 
        #                          "warning")
        #     # Make sure to send None and return if the widget 
        #     # cannot operate properly at this point.
        #     self.send("New segmentation", None)
        #     return
        print('another test!')
        print(self.url)

        """ if self.url == "bonjour": """
        if not re.match(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$", self.url):
            print('regex failure')
            self.infoBox.setText("Please only add YouTube URLs.", "error")
            self.send("New segmentation", None)
            #return
            #"https://chatgpt.com/share/6800c404-cb74-8000-afef-e321b9517c47"
        elif self.youtube_video_existe(self.url) == False:
            self.infoBox.setText("Please check your internet connection.", 
                                 "warning")
            # Make sure to send None and return if the widget 
            # cannot operate properly at this point.
            self.send("New segmentation", None)
            return
        


        # If the widget creates new LTTL.Input objects (i.e.
        # if it imports new strings in Textable), make sure to
        # clear previously created Inputs with this method.
        self.clearCreatedInputs()

        # Notify processing in infobox. Typically, there should
        # always be a "processing" step, with optional "pre-
        # processing" and "post-processing" steps before and 
        # after it. If there are no optional steps, notify 
        # "Preprocessing...".
        self.infoBox.setText("Step 1/2: Processing...", "warning")
        
        # Progress bar should be initialized at this point.
        self.progressBarInit()

        # Create a threaded function to do the actual processing
        # and specify its arguments (here there are none).
        threaded_function = partial(
            self.processData,
            # argument1, 
            # argument2, 
            # ...
        )

        # Run the threaded function...
        self.threading(threaded_function)

    def processData(self):
        """Actual processing takes place in this method,
        which is run in a worker thread so that GUI stays
        responsive and operations can be cancelled
        """
        
        # At start of processing, set progress bar to 1%.
        # Within this method, this is done using the following
        # instruction.
        self.signal_prog.emit(1, False)
        urls = [self.url]
        # Indicate the total number of iterations that the
        # progress bar will go through (e.g. number of input
        # segments, number of selected files, etc.), then
        # set current iteration to 1.
        #TODO mettre 1 url max_itr = longueur url
        # number of segment ça veut dire number of url
        max_itr = len(urls)
        cur_itr = 1

        # TODO: remove useless debug statements
        # TODO: change 'borrowed code' to match project
        # TODO: DOIs -> URLs, etc.
        print('url debug:')
        print(urls)
        #print(url)
        print('DOIs:')
        print(self.DOI)
        print(self.DOIs)
        urls = self.DOIs

        # Actual processing...
        
        # For each progress bar iteration...
        #for _ in range(int(self.numberOfSegments)):

        for url in urls:

            # Update progress bar manually...
            self.signal_prog.emit(int(100*cur_itr/max_itr), False)
            cur_itr += 1
            
            # Create an LTTL.Input...  


            #if int(self.numberOfSegments) == 1:

            if len(urls) == 1:
                # self.captionTitle is the name of the widget,
                # which will become the label of the output
                # segmentation.
                label = self.captionTitle
            else:
                label = None # will be set later.

            #print("1")
            # on fetch les commentaires depuis l'url spécifié plus haut, attention ce n'est encore l'url entrée par l'utilisateur

            print('cache checks happens below')
            # Check if we already have an entry for the url in the cached
            # comments. If yes, we return it; if not, we scrape and cache.
            if url in self.cached_comments:
                comments_ycd = self.cached_comments.get(url)
                print('    using the cache')
            else:
                comments_ycd = self.scrape(url)
                self.cached_comments[url] = comments_ycd
                print('    not using the cache')
            print('cache check happened!')

            # Placeholder limit for testing. TODO: delete.
            limit = 5

            # While we cache everything that was scraped, we only return as
            # many as the user requested.
            if limit != 0:
                comments_ycd = comments_ycd[0:limit]

            #on créé une chaine de caractères séparés d'un retour à la ligne 
            comments = "\n".join([comment["text"] for comment in comments_ycd ])
            print(comments_ycd)
            print("2")
            #myInput = Input("hello", label)
            myInput = Input(comments, label) 

            # Extract the first (and single) segment in the 
            # newly created LTTL.Input and annotate it with 
            # the length of the input segmentation. 
            segment = myInput[0]
            segment.annotations["url"]  \
                = self.url
            # For the annotation to be saved in the LTTL.Input, 
            # the extracted and annotated segment must be re-assigned
            # to the first (and only) segment of the LTTL.Input.
            myInput[0] = segment
            
            # Add the  LTTL.Input to self.createdInputs.
            self.createdInputs.append(myInput)
            
            # Cancel operation if requested by user...
            time.sleep(0.00001) # Needed somehow!
            if self.cancel_operation:
                self.signal_prog.emit(100, False)
                return            

        # Update infobox and reset progress bar...
        self.signal_text.emit("Step 2/2: Post-processing...", 
                              "warning")
        self.signal_prog.emit(1, True)

        # If there's only one LTTL.Input created, it is the 
        # widget's output...
        if len(urls) == 1:
            return self.createdInputs[0]

        # Otherwise the widget's output is a concatenation...        
        else:
            return Segmenter.concatenate(
                caller=self,
                segmentations=self.createdInputs,
                label=self.captionTitle,
                import_labels_as=None,
            ) 

    @OWTextableBaseWidget.task_decorator
    def task_finished(self, f):
        """All operations following the successful termination
        of self.processData
        """
        
        # Get the result value of self.processData.
        processed_data = f.result()

        # If it is not None...
        if processed_data:
            message = f"{len(processed_data)} segment@p sent to output " 
            message = pluralize(message, len(processed_data))
            numChars = 0
            for segment in processed_data:
                segmentLength = len(Segmentation.get_data(segment.str_index))
                numChars += segmentLength
            message += f"({numChars} character@p)."
            message = pluralize(message, numChars)
            self.infoBox.setText(message)
            self.send("New segmentation", processed_data)

    # The following method should be copied verbatim in 
    # every Textable widget.
    def setCaption(self, title):
        """Register captionTitle changes and send if needed"""
        if 'captionTitle' in dir(self):
            changed = title != self.captionTitle
            super().setCaption(title)
            if changed:
                self.cancel() # Cancel current operation
                self.sendButton.settingsChanged()
        else:
            super().setCaption(title)

    # The following two methods should be copied verbatim in 
    # every Textable widget that creates LTTL.Input objects.

    def clearCreatedInputs(self):
        """Clear created inputs"""
        for i in self.createdInputs:
            Segmentation.set_data(i[0].str_index, None)
        del self.createdInputs[:]

    def onDeleteWidget(self):
        """Clear created inputs on widget deletion"""
        self.clearCreatedInputs()

    # Pour tester s'il y a une connection internet
    def youtube_video_existe(self, urll):
        headers = {
            "User-Agent": "Mozilla/5.0"  # éviter le blocage par YouTube
        }
        try:
            response = requests.get(urll, headers=headers, timeout=5)
            print(f'headers test: {response}')
            return response.status_code
        except requests.RequestException:
            print('headers errors')
            return False

    def scrape(self, url) -> list:
        """
        Sets up a virtual browser through YoutubeCommentDownloader and uses
        it to scrape all comments on a given url, returning them as a list.
        """
        print(
            f'▓▓▓▓▓▓▓▓▓▓▓▓ scrape()'
            f'    url={url}'
        )

        # that's where we go fetch the comments!
        downloader = YoutubeCommentDownloader()
        comments = downloader.get_comments_from_url(url)
        print(
            f'    returning comments=\n{comments}'
        )
        print('look at all these comments!s')
        print([x for x in comments])
        return [x for x in comments]
    
    #---------------------code emprunté à sci hub ------------------------------------------------------------------------
    def clearAll(self):
        """Remove all DOIs from DOIs attr"""
        del self.DOIs[:]
        del self.selectedURLLabel[:]
        self.sendButton.settingsChanged()
        self.URLLabel = self.URLLabel
        self.clearAllButton.setDisabled(True)

    def remove(self):
        """Remove URL from DOIs attr"""
        if self.selectedURLLabel:
            index = self.selectedURLLabel[0]
            self.DOIs.pop(index)
            del self.selectedURLLabel[:]
            self.sendButton.settingsChanged()
            self.URLLabel = self.URLLabel
        self.clearAllButton.setDisabled(not bool(self.URLLabel))

    def add(self):
        """Add Urls to URLs attr"""
        DOIList = re.split(r',', self.new_url)
        # print(DOIList)
        old_urls = list(self.DOIs)
        print(old_urls)
        for DOI in DOIList:
            print(DOI)
            self.DOIs.append(DOI)
        if self.DOIs:
            tempSet = set(self.DOIs)        # ici on créé un set pour supprimer tous les doublons
            def_set = set(tempSet)    
            if(len(tempSet)<len(self.DOIs)):
                QMessageBox.information(
                    None, "YouGet", "Duplicate URL(s) found and deleted.",
                    QMessageBox.Ok
                )

            #----------------- notre code dans leur code -------------------
            # if self.new_url == "":
            #     # Use mode "warning" when user needs to do some
            #     # action or provide some information; use mode "error"
            #     # when invalid parameters have been provided; 
            #     # for notifications that don't require user action,
            #     # don't use a mode. Use formulations that emphasize
            #     # what should be done rather than what is wrong or
            #     # missing.
            #     self.infoBox.setText("Please add a YouTube URL.", 
            #                         "warning")
            #     # Make sure to send None and return if the widget 
            #     # cannot operate properly at this point.
            #     self.send("New segmentation", None)
            #     return
        
            # if not re.match(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$", self.url):
            #     self.infoBox.setText("Please only add YouTube URLs.", "error")
            #     self.send("New segmentation", None)
            #     return
            #     #"https://chatgpt.com/share/6800c404-cb74-8000-afef-e321b9517c47"
            not_an_url = False
            for single_url in tempSet:
                # si une ou plus url dans la liste n'est pas la forme d'une url ytb, ne pas autoriser l'ajout
                if not re.match(r"^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+$", single_url):
                    not_an_url = True
            if not_an_url == True:
                tempSet = set(old_urls)
                QMessageBox.information(
                    None, "YouGet", "One or more element are not YouTube URLs, please only add YouTube URLs.",
                    QMessageBox.Ok
                )
            elif self.youtube_video_existe(self.new_url) == False:
                self.infoBox.setText("Please check your internet connection.", 
                                    "warning")
                # Make sure to send None and return if the widget 
                # cannot operate properly at this point.
                self.send("New segmentation", None)
                return
            #----------------- notre code dans leur code fin-------------------
            self.DOIs = list(tempSet)
            self.URLLabel = self.DOIs

        # self.URLLabel = self.URLLabel
        self.clearAllButton.setDisabled(not bool(self.DOIs))
        self.sendButton.settingsChanged()
    
    def addDisabledOrNot(self):
        self.addButton.setDisabled(not bool(self.new_url))

    def updateURLBoxButtons(self):
        """Update state of File box buttons"""
        self.addButton.setDisabled(not bool(self.new_url))
        self.removeButton.setDisabled(not bool(self.selectedURLLabel))


    # The following two methods should be copied verbatim in 
    # every Textable widget that creates LTTL.Input objects.

    def clearCreatedInputs(self):
        """Clear created inputs"""
        for i in self.createdInputs:
            Segmentation.set_data(i[0].str_index, None)
        del self.createdInputs[:]

    def onDeleteWidget(self):
        """Clear created inputs on widget deletion"""
        self.clearCreatedInputs()
    #-----------------------------code emprunté à sci hub fin---------------------------------------------------------------------------------


    def updateGUI(self):
        pass

#Fetch.url = ''
#test = Fetch.from_url('https://www.youtube.com/watch?v=ScMzIvxBSi4', limit=5)
#print(test)
#print(len(test))
if __name__ == '__main__':
        WidgetPreview(YouGet).run()



'''import requests
import re
import json

def youtube_video_exists(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return False

        html = response.text

        # Extraction du JSON "ytInitialPlayerResponse"
        initial_data_match = re.search(r'ytInitialPlayerResponse\s*=\s*({.+?});', html)
        if not initial_data_match:
            print("Impossible d'extraire ytInitialPlayerResponse")
            return False

        data = json.loads(initial_data_match.group(1))
        status = data.get("playabilityStatus", {}).get("status", "UNKNOWN")

        if status == "OK":
            return True
        else:
            print(f"Statut de lecture : {status}")
            return False

    except Exception as e:
        print(f"Erreur lors de l'analyse : {e}")
        return False

# Test
url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"  # Change le lien ici pour tester
if youtube_video_exists(url):
    print("✅ La vidéo existe et est accessible.")
else:
    print("❌ La vidéo n'existe pas ou n'est pas disponible.")'''