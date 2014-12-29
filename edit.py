from metagame import *
from ddr import *
from iomidi import *
from piece import *
import pygame
import midi as MIDI # from python-midi vishnubob github, for easy reading/writing of midi files
import config
from collections import deque # this is for fast popping of lists from the left
import itertools

class EditClass( DDRClass ): # inherit from the DDRClass
#### EDIT CLASS
    def __init__( self, piecedir, midi, piecesettings = { "TempoPercent" : 100, "Difficulty" : 0,
                                                    "AllowedDifficulties" : [ 0 ],
                                                    "Sandbox" : config.SANDBOXplay,
                                                    "PlayerStarts" : config.PLAYERstarts,
                                                    "PlayerTrack" : 0,
                                                    "Metronome" : config.METRONOMEdefault } ):
        DDRClass.__init__( self, piecedir, midi, piecesettings )
        self.noteson = {} # notes on that we will eventually turn off.
        self.sandbox = 1 # no matter what, in EDIT mode you should allow sandbox maneuvering
        self.currentvelocity = 100 # default note velocity.
        self.currenttrack = 0
        self.noteclipboard = [] # for copy pasting
    
        # set the default state of the editor
        self.allowedchanges = [ 'state' ]
        self.state = -1 # start uninitialized
        #self.EXITstate = 0 # 
        self.NAVIGATIONstate = 1 # default state after pressing escape.  for copy/pasting, etc.  
        self.SELECTstate = 2 # visual block/line type stuff
        self.COMMANDstate = 3 # after pressing escape, then colon (:).  vim-like command mode
        self.INSERTstate = 4 # after pressing i,I, a,A, you can insert notes on the keyboard
        self.commandlist = deque([], config.COMMANDhistory) # only allow the deck to get so big...
        self.commandlistindex = -1
        self.commandfont = config.FONT
        self.commandfontcolor = (255,255,255)
        self.commandfontsize = 24 * config.FONTSIZEmultiplier
        self.commandbackcolor = (0, 0, 0)
        self.helperfontcolor = (255,255,255)
        self.helperfontsize = 18* config.FONTSIZEmultiplier
        self.helperbackcolor = (0, 0, 0)
        self.statenames = { self.NAVIGATIONstate : "Navigation",
                            self.SELECTstate : "Select",
                            self.COMMANDstate : "Command",
                            self.INSERTstate : "Insert" }
        self.helper = { 
            self.NAVIGATIONstate : [ 0, #start line
                 [ " ctrl+j|k   scroll this helper list down|up",
                   "  h|j|k|l   move left|down|up|right",
                   "  H|J|K|L   move left|down|up|right faster",
                   "      g|G   go to beginning|end of piece",
                   "    SPACE   start/stop piece playing",
                   "",
                   "ESC|/|:|;   go to command mode",
                   "        i   go to insert mode",
                   "        a   insert mode:  rolls on input",
                   "",
                   "        q   quick add note at cursor",
                   "        Q   add note at cursor and advance",
                   "        m   merge notes under cursor",
                   "        M   merge with next note",
                   "      [|]   lower|raise volume at cursor",
                   "shift+[|]   quickly decrease|increase volume",
                   "    ENTER   play note at cursor",
                   "shift+ENT   play existing chord on line",
                   "",
                   "1-9|0|-|+   change time grid duration",
                   "      o|O   offset time grid forward|backward",
                   "",
                   "        y   yank (copy) notes with any overlap",
                   "        p   paste relative to cursor",
                   "        d   delete* notes with any overlap",
                   "        x   carve* note overlap only",
                   "            *both d and x copy the deleted notes",
                   "      X|D   carve|delete but without copying.",
                   "        P   paste and remove notes from underlying region",
                   "   ctrl+p   swap:  paste but copy existing notes",
                   "      v|V   activate/deactivate visual block|line",
                   "   ctrl+v   swap cursor/anchor of visual block",
                   " ctrl+h|l   swap cursor/anchor key position",
                   "",
                   "  PgUp|Dn   move up|down by one screen",
                   " HOME|END   move all the way left|right",
                   "        `   back to last non-trivial jump point",
                   "   ctrl+b   add/delete bookmark here",
                   "      b|B   cycle forward|backward through bookmarks",
                   "        c   toggle click track (metronome)",
                   "        C   toggle click track volume loud/soft",
                    ]
               ],
            self.SELECTstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   " h|j|k|l    move left|down|up|right" ]
               ],
            self.COMMANDstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   "  ESCAPE    go back to navigation mode",
                   " up|down    navigate command history",
                   " ",
                   "Type in and press enter to execute:",
                   "  q|quit    quit PyanoH3ro",
                   "s|save|w    save piece",
                   "  return    return to main menu ",
                   "  reload    reloads the piece from save file",
                   "   clear    clears the piece",
                   "",
                   "    ts X    set time signature to X (beats per measure)",
                   "    Nm/D    set time grid to N/D times measure length ",
                   "    Nn/D    set grid to N/D times quarter note length ",
                   "     t X    set current tempo to X (10 to 300, in bpm)",
                   "  r t|ts   remove (t)empo or (ts) time signature",
                   "       X    go to line X",
                   "",
                   "     e X    edit track X",
                   "     i X    change track instrument to X",
                   "            X can be a number (0 to 127), or a name",
                   "     v X    set input velocity to X (0 to 127)",
                   ]
               ],
            self.INSERTstate : [ 0, #start line
                 [ "ctrl+j|k    scroll this helper list down|up",
                   " h|j|k|l    move left|down|up|right",
                   "  escape    go to navigation mode",
                   "   /|:|;    go to command mode",
                   " Play your dang MIDI keyboard! "
                   ]
               ],
            }
        self.helperlines = [] # current list of text to be written to the screen
        self.helperlinemax = max(1, config.HELPERLINEmax)

        self.setstate( state=self.NAVIGATIONstate )

        # the following variables modify the above editing states:
        self.insertmode = 0    # -1 = Ghost insert, 0 = friendly insert, 1 = aggressive insert
                               # it depends on what the self.state is, what insertmode does.
        self.waitforkeytoplay = 0

        # for grabbing information...
        self.command = ""
        self.listeningaction = {}

        # this helper guy gives information on what the heck you're doing
        self.maxhelperlines = 5 # will spit out at most 5 lines, which you can navigate

        self.anchor = 0 #will go to [ midinote, anchorposition ]
        #self.trackticks = [ 0 for t in self.piece.notes ]

    def addtrack( self ):
        #self.trackticks.append(0)
        self.piece.addtrack()
        self.noisytracks.add( len(self.piece.notes)-1 )

    def setstate( self, **kwargs ):
        for key, value in kwargs.iteritems():
            if key in self.allowedchanges:
                setattr( self, key, value )
                if key == "state":
                    self.setalert("Now in "+self.statenames[value])
                    self.sethelperlines( value )
            else:
                Warn("in EditClass:setstate - key "+ key +" is protected!!") 

    def update( self, dt, midi ):
        DDRClass.update( self, dt, midi )

    def process( self, event, midi ):
        '''here we provide methods for changing things.
        we don't process midi input here; rather we allow for midi output
        when we want to, say on pressing some non-midi device it makes a noise.'''

        if self.state == self.NAVIGATIONstate:
            return self.navprocess( event, midi )
        
        elif self.state == self.INSERTstate:
            return self.insprocess( event, midi )
        
        elif self.state == self.COMMANDstate:
            return self.cmdprocess( event, midi )

        else:
            Error(" UNKNOWN state in EditClass.process( self, event, midi ) ")

    def navprocess( self, event, midi ):
        # NAVIGATION STATE:  after hitting escape, we get to this mode.
        if event.type == pygame.KEYDOWN:
            if ( event.key == 27 ):
                if self.anchor:
                    self.anchor = 0
                else:
                    self.setstate( state=self.COMMANDstate ) 
            elif ( event.key == pygame.K_SLASH
                or event.key == pygame.K_SEMICOLON or event.key == pygame.K_COLON ):
                self.setstate( state=self.COMMANDstate  )
            elif event.key == pygame.K_o:
                # set tick offset
                # SUGGEST:  don't allow note-offset if note does not divide measure...
                self.currentnoteoffset = ( self.currentnoteoffset + self.currentnoteticks // 2 ) % self.currentnoteticks
                self.setcurrentticksandload( 
                    self.roundtonoteticks( self.currentabsoluteticks, 
                        pygame.key.get_mods() & pygame.KMOD_SHIFT 
                    ) 
                )
            elif event.key == pygame.K_i or event.key == pygame.K_a:
                # insert mode.  i = insert at current position, a = set insert, get playing ready
                if event.key == pygame.K_a:
                    self.waitforkeytoplay = 1
                # common to both
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self.insertmode = 1 # aggressive insert
                else:
                    self.insertmode = 0 # friendly insert
                self.setstate( state=self.INSERTstate )

            elif event.key == pygame.K_q:
                # quick insert.  add note at cursor
                if self.anchor:
                    self.setalert("Stay tuned for chord/arpeggio input") 
                else:
                    self.addnoteatcursor( midi )
                    if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                        self.setcurrentticksandload( self.currentabsoluteticks + self.currentnoteticks )
                # NEED NEW FUNCTIONALITY FOR SELECTIONS.
            elif event.key == pygame.K_d:
                self.deletecursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_x:
                self.carvecursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_m:
                self.mergecursorselection( pygame.key.get_mods() & pygame.KMOD_SHIFT )
            
            elif event.key == pygame.K_y:
                # yank (copy)
                self.copycursorselection()
            
            elif event.key == pygame.K_p:
                # paste
                self.pastenoteclipboard( pygame.key.get_mods() & pygame.KMOD_SHIFT,
                    pygame.key.get_mods() & pygame.KMOD_CTRL )

            elif event.key == pygame.K_LEFTBRACKET:
                # lower volume of notes under cursor
                self.changevelocityatcursorselection( midi, -1, pygame.key.get_mods() & pygame.KMOD_SHIFT )
            elif event.key == pygame.K_RIGHTBRACKET:
                # raise volume of notes under cursor
                self.changevelocityatcursorselection( midi,  1, pygame.key.get_mods() & pygame.KMOD_SHIFT )

            elif event.key == pygame.K_v:
                if self.play:
                    currentticks = self.roundtonoteticks( self.currentabsoluteticks )
                else:
                    currentticks = self.currentabsoluteticks

                if self.anchor:
                    # we already have a selection going.
                    if self.anchor[0] != -1 and (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        # we have a selection, but it wasn't full line, but now we want to make it full line.
                        self.anchor[0] = -1
                    elif (pygame.key.get_mods() & pygame.KMOD_CTRL):
                        # switch anchor and cursor
                        switch = [ self.anchor[0], self.anchor[1] ]
                        if switch[0] == -1:
                            # if anchor was holding the entire row...
                            # keep the cursor where it is:
                            switch[0] = self.keymusic.cursorkeyindex + 9   
                            # make sure that it will now, too:
                            self.anchor = [ -1, currentticks ]
                        else:
                            self.anchor = [ self.keymusic.cursorkeyindex + 9, 
                                            currentticks ]
                        self.keymusic.centeredmidinote = switch[0]
                        self.setcurrentticksandload( switch[1] )
                        self.play = False
                        self.setalert("Cursor and visual block anchor switched.")

                    else:
                        # otherwise we hit V again, and we probably want to escape selection mode.
                        self.anchor = 0
                else:
                    # select mode here we come!

                    midinote = -1
                    if not (pygame.key.get_mods() & pygame.KMOD_SHIFT):
                        # if the shift key is not on, pick the note specifically
                        midinote = self.keymusic.cursorkeyindex + 9   
                    
                    self.anchor = [ midinote, currentticks ]
            
            elif event.key == pygame.K_RETURN:
                # play selected notes
                if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    # play the entire line if shift is pressed
                    currentticks = self.roundtonoteticks( self.currentabsoluteticks )
                    if self.anchor:
                        originalanchor0 = self.anchor[0]
                        self.anchor[0] = -1
                    else:
                        originalanchor0 = None
                        self.anchor = [ -1, currentticks ]

                    # check if there were selected notes
                    self.selectcursorselection()
                    if self.selectednotes:
                        for note in self.selectednotes:
                            # hit the key:
                            self.keymusic.hitkey( midi, note[0], 
                                note[1], self.tickstosecs(note[2]),
                                self.piece.channels[self.currenttrack], True 
                            )
                    else:
                        if self.anchor[1] != currentticks:
                            self.setalert("No notes to play in these rows.")
                        else:
                            self.setalert("No notes to play in this row")

                    if originalanchor0 == None:
                        self.anchor = 0
                    else:
                        self.anchor = [ originalanchor0, self.anchor[1] ]
                else:
                    # no notes were selected
                    self.keymusic.hitkey( midi, self.keymusic.cursorkeyindex + 9,
                        100,    # velocity
                        1,      # duration
                        self.piece.channels[self.currenttrack], 
                        True  # play sound
                    )

            elif ( pygame.key.get_mods() & pygame.KMOD_CTRL
            and (event.key == pygame.K_h or event.key == pygame.K_l ) ):
                if self.anchor and self.anchor[0] != -1:
                    swap0 = self.anchor[0]
                    self.anchor[0] = self.keymusic.cursorkeyindex + 9
                    self.keymusic.centeredmidinote = swap0
                    self.setalert("Swapping cursor and visual anchor key position")
            elif self.commonnav( event, midi ):
#                if self.anchor and self.previousabsoluteticks != self.currentabsoluteticks:
#                    if ( self.previousabsoluteticks >= self.anchor[1] and
#                         self.currentabsoluteticks < self.anchor[1] ):
#                        # if had an anchor and now are moving below it,
#                        # reset the anchor to be at a height of...
#                        self.anchor[1] += self.currentnoteticks
#                        # so that it continues to capture the line it was originally on.
#                    elif ( self.previousabsoluteticks < self.anchor[1] and
#                         self.currentabsoluteticks >= self.anchor[1] ):
#                        # if had an anchor and now are moving above it,
#                        # reset the anchor to be at a height of...
#                        self.anchor[1] -= self.currentnoteticks
#                        # so that it continues to capture the line it was originally on.
                        
                return {}
            elif self.metanav( event, midi ):
                return {}
            elif self.commongrid( event, midi ):
                return {}

        ## gamechunk must return a dictionary after processing events.
        ## if you don't want anything to happen, pass an empty dict:
        return {}

    def insprocess( self, event, midi ):
        # INSERT STATE.  From Navigation mode, we can get to INSERT mode by pressing the following keys:
        # NOT YET IMPLEMENTED:
        #   While holding down piano keys, if you move up/down (k/l or arrow keys),
        #   the duration of the note is extended.
        # method 2:
        # Hit keys [ASDFG, QWERTY] (white keys, black keys), which appear over the key on the screen.
        # They appear over different keys, depending on where your cursor is, left/right-speaking.
        if event.type == pygame.KEYDOWN:
            if event.key == 27:
                self.setstate( state=self.NAVIGATIONstate  )
            elif (event.key == pygame.K_SLASH
                   or event.key == pygame.K_SEMICOLON or event.key == pygame.K_COLON ):
                self.setstate( state=self.COMMANDstate  ) 
            elif (event.key == pygame.K_p):
                self.waitforkeytoplay = 1 - self.waitforkeytoplay
                if self.waitforkeytoplay:
                    self.setalert( "Pressing a key will start notes-a-rolling" )
                else:
                    self.setalert( "Static input" )
            elif (event.key == pygame.K_i):
                self.insertmode = 1 - self.insertmode
                if self.insertmode:
                    self.setalert( "Aggressive insert" )
                else:
                    self.setalert( "Friendly insert" )
            elif self.commonnav( event, midi ):
                return {}
            elif self.metanav( event, midi ):
                return {}
            elif self.commongrid( event, midi ):
                return {}
        return {}
    
    def cmdprocess( self, event, midi ):
        # COMMAND STATE.  in navigation mode, press : and then type various commands:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.command = self.command[0:-1] # take out last letter
            elif event.key == pygame.K_RETURN:
                if self.command:
                    if self.command == "quit" or self.command == "q":
                        return { "gamestate" : 0, "printme" : "quitting from edit mode" } 
                    elif self.command == "return":
                        midi.clearall()
                        return { "gamestate" : config.GAMESTATEmainmenu, 
                                 "printme" : "return from edit mode" } 
                    elif self.command == "reload":
                        midi.clearall()
                        self.__init__( self.piece.piecedir, midi )
                    elif self.command == "save" or self.command == "s" or self.command == "w":
                        self.piece.writeinfo()
                        self.piece.writemidi()
                        self.wrapupcommand( self.piece.piecedir+" saved!" )
                        return {}
                    elif self.command == "clear" or self.command == "reset":
                        midi.clearall()
                        self.piece.clear()
                        self.play = False
                        self.setcurrentticksandload(0)
                        self.wrapupcommand( "all notes erased." )
                        return {}
                    else:
                        split = self.command.split()

                        if split[0][0] == "v":
                            try:
                                velocity = int(split[1])
                                if velocity <= 0:
                                    velocity = 1
                                elif velocity > 127:
                                    velocity = 127

                                self.currentvelocity = velocity 
                                self.wrapupcommand("Setting quick-input velocity to "+str(velocity) )
                            except (IndexError, ValueError):
                                self.wrapupcommand("use \"v X\" to set velocity/volume to X")
                            return {}

                        elif split[0][:2] == "te" or split[0] == "t":
                            try:
                                tempo = float(split[1])
                                if tempo < 10:
                                    tempo = 10
                                elif tempo > 300:
                                    tempo = 300
                                
                                self.piece.addtempoevent( tempo, 
                                    self.roundtonoteticks( self.currentabsoluteticks )
                                )
                                self.setcurrentticksandload( self.currentabsoluteticks )

                                self.wrapupcommand("setting current tempo to "+str(tempo) )
                            except (IndexError, ValueError):
                                self.wrapupcommand("use \"t X\" to set tempo to X")
                            return {}
                        
                        elif split[0][:2] == "ts" or split[:7] == "timesig":
                            try:
                                ts = int(split[1])
                                if ts < 1:
                                    ts = 1
                                elif ts > 25:
                                    ts = 25
                                
                                self.piece.addtimesignatureevent( ts,  
                                    self.roundtonoteticks( self.currentabsoluteticks )
                                )
                                self.setcurrentticksandload( self.currentabsoluteticks )

                                self.wrapupcommand("setting current time signature to "+str(ts) )
                            except (IndexError, ValueError):
                                self.wrapupcommand("use \"ts X\" to set time signature numerator to X")
                            return {}
                        elif split[0] == "r":
                            try: 
                                split1 = split[1]
                                if split1 == "ts":
                                    if self.piece.removetimesignatureevent( self.currentabsoluteticks ):
                                        self.wrapupcommand("no current time signature to remove")
                                    else:
                                        self.wrapupcommand("removing current time signature")
                                        self.setcurrentticksandload( self.currentabsoluteticks )
                                elif split1 == "t":
                                    if self.piece.removetempoevent( self.currentabsoluteticks ):
                                        self.wrapupcommand("no current tempo to remove")
                                    else:
                                        self.wrapupcommand("removing current tempo")
                                        self.setcurrentticksandload( self.currentabsoluteticks )
                                else:
                                    raise IndexError
                            except IndexError:
                                self.wrapupcommand("use \"r t\"|\"r ts\" to remove tempo|timesignature")

                            return {}
                        elif split[0] == "i":
                            i = None
                            try:
                                i = int(split[1])
                            except ValueError:
                                try:
                                    i = config.INSTRUMENT[split[1]]
                                except KeyError:
                                    pass
                            except IndexError:
                                self.wrapupcommand("use \"i X\" to set track instrument to X")
                                return {}
                            
                            if i == None:
                                self.wrapupcommand( "unknown instrument" )
                            elif i == "drums":
                                self.piece.setchannel( midi, self.currenttrack, 9 )
                                self.wrapupcommand( "setting track to drums (channel 9)" )
                            else:
                                if i < 0:
                                    i = 0
                                elif i > 127:
                                    i = 127
                                self.piece.setinstrument( midi, self.currenttrack, i )
                                self.wrapupcommand( "setting instrument to "+str(i) )
                                
                            return {}
                        
                        elif split[0] == "e":
                            track = None
                            try:
                                track = int(split[1])
                                
                                if track == self.currenttrack:
                                    self.wrapupcommand("you are editing track "+str(track)+" already")
                                else:
                                    if track < 0:
                                        track = 0
                                        self.wrapupcommand("editing track 0 (no negatives)")
                                    elif track >= len(self.piece.notes): 
                                        track = len(self.piece.notes)
                                        self.addtrack()
                                        self.wrapupcommand("adding track, editing "+str(track))
                                    else:
                                        self.wrapupcommand("editing track "+str(track))
                                    
                                    # switch from one track to another
#                                    self.trackticks[self.currenttrack] = self.currentabsoluteticks
                                    self.currenttrack = track
                                    self.setcurrentticksandload(self.currentabsoluteticks) #self.trackticks[track] )
#                                    self.previousabsoluteticks = 0 
                                    
                            except ValueError:
                                self.wrapupcommand( "unknown track to edit" )
                        elif self.readnotecode( self.command ):
                            self.setcurrentticksandload( self.currentabsoluteticks )
                            self.wrapupcommand( "Set notecode to "+self.notecode )
                        else:
                            # try to see if the command is an integer (for a line count)
                            try:
                                integer = int(split[0])
                                newticks = self.currentnoteticks*integer
                                if newticks != self.currentabsoluteticks:
                                    lastcurrentnoteticks = self.piece.notes[self.currenttrack][-1].absoluteticks
                                    lastmeasureticks = self.piece.getfloormeasureticks( lastcurrentnoteticks )
                                    if newticks != 0 and newticks != lastmeasureticks:
                                        self.previousabsoluteticks = self.currentabsoluteticks

                                    self.setcurrentticksandload( newticks )
                                    
                                self.wrapupcommand("at line "+str(integer))
                                return {}
                                
                            except (IndexError, ValueError):
                                self.wrapupcommand( "unknown command: "+self.command )
                                return {}

                else:
                    # no command text given
                    self.setstate( state=self.NAVIGATIONstate  )
                    
            elif event.key == 27: #escape
                if self.commandlistindex < 0:
                    # if we weren't looking at the commandlist
                    if len(self.command):
                        self.commandlist.appendleft(self.command)
                else:
                    # if we were looking at the commandlist, see if we did not
                    # escape from a command we used previously:
                    if self.command != self.commandlist[self.commandlistindex]:
                        self.commandlist.appendleft(self.command)
                    # otherwise, don't add the command again.
                    self.commandlistindex = -1
                self.command = "" # kill command and go back to nav mode
                self.setstate( state=self.NAVIGATIONstate  )
            
            elif self.metanav( event, midi ):
                return {}

            elif event.key == pygame.K_UP:
                # navigate the command history
                if self.commandlistindex < 0:
                    if len(self.command):
                        if len(self.commandlist):
                            if self.commandlist[0] != self.command:
                                self.commandlist.appendleft(self.command)
                                self.commandlistindex = 0
                        else:
                            self.commandlist.appendleft(self.command)
                            self.commandlistindex = 0
                else:
                    # if we were looking at the commandlist, see if we did not
                    # edit the command we used previously:
                    if self.command != self.commandlist[self.commandlistindex]:
                        self.commandlist = deque( 
                            list(itertools.islice(self.commandlist,0,self.commandlistindex+1))+
                            [self.command] +
                            list(itertools.islice(self.commandlist,self.commandlistindex+1,len(self.commandlist))),
                            config.COMMANDhistory 
                        )
                        #self.commandlist.insert(self.commandlistindex+1, self.command)
                        self.commandlistindex += 1
                    
                self.commandlistindex += 1
                if self.commandlistindex >= len(self.commandlist):
                    self.commandlistindex = len(self.commandlist)-1
                self.command = self.commandlist[ self.commandlistindex ]
                return {} 
            
            elif event.key == pygame.K_DOWN:
                # navigate the command history
                if self.commandlistindex < 0:
                    if len(self.command):
                        if len(self.commandlist):
                            if self.commandlist[0] != self.command:
                                self.commandlist.appendleft(self.command)
                        else:
                            self.commandlist.appendleft(self.command)
                else:
                    # if we were looking at the commandlist, see if we did not
                    # edit the command we used previously:
                    if self.command != self.commandlist[self.commandlistindex]:
                        self.commandlist = deque( 
                            list(itertools.islice(self.commandlist,0,self.commandlistindex))+
                            [self.command] +
                            list(itertools.islice(self.commandlist,self.commandlistindex,len(self.commandlist))),
                            config.COMMANDhistory )
                        #self.commandlistindex -= 1
                    
                self.commandlistindex -= 1
                if self.commandlistindex < 0:
                    self.command = ""
                else:
                    self.command = self.commandlist[ self.commandlistindex ]
                return {} 

            elif (31 < event.key < 128):
                newletter = chr(event.key) #here's our new letter
                if pygame.key.get_mods() & pygame.KMOD_SHIFT: # if the shift key is held down
                    newletter = newletter.upper() #make it uppercase
                self.command += newletter #add it to the message
        return {}

    def wrapupcommand( self, alert ):
        if len(self.commandlist):
            if self.commandlist[0] != self.command:
                self.commandlist.appendleft(self.command)
        else:
            self.commandlist.appendleft(self.command)
        self.commandlistindex = -1
        self.setstate( state=self.NAVIGATIONstate  )
        self.setalert( alert )
        self.command = ""

#### EDIT CLASS
    def processmidi( self, midi ):
        # common processing of midi.  always make the sound.
        newnoteson = midi.newnoteson()
        for note in newnoteson:
            midi.startnote( note[0], note[1], self.currenttrack ) #start note[0] with velocity note[1]
            # also light up the appropriate key on the background
            self.keymusic.brightenkey( note[0], note[1] ) 
            
        newnotesoff = midi.newnotesoff()
        for note in newnotesoff:
            midi.endnote( note, self.currenttrack ) # stop note note

        if self.state == self.INSERTstate:
            if len(newnoteson): 
                if not self.play:  # if we are not playing
                    if self.waitforkeytoplay: # see if we are waiting for a key to start play
                        self.play = True

            # on notes go on no matter what
            for note in newnoteson:
                self.addnoteonpresently( midi, note[0], note[1], False ) # but do not sound again

            # off notes are different depending on whether you play or not.
            if self.play:
                # if playing, let the ends of the notes fall where they may.
                for note in newnotesoff:
                    self.addnoteoffpresently( midi, note )
            else:
                # if not playing, offset the ends of the note by currentnoteticks.
                for note in newnotesoff:
                    self.addnoteoffpresently( midi, note, self.currentnoteticks )
        
        return {}

    def sethelperlines( self, state ):
        start = self.helper[ state ][0] 
        self.helperlines = ([ (self.statenames[ state ]).upper() ] 
                            + self.helper[ state ][1][ start : start+self.helperlinemax ])
        
        if len(self.helperlines):
            fontandsize = pygame.font.SysFont(config.FONT, self.helperfontsize)
            self.helperlabel = []
            self.helperlabelbox = []
            self.maxhelperwidth = 0
            for i in range(len(self.helperlines)):
                self.helperlabel.append( fontandsize.render( self.helperlines[i], 1, self.helperfontcolor ) )
                self.helperlabelbox.append( self.helperlabel[-1].get_rect() )
                if self.helperlabelbox[i].width > self.maxhelperwidth:
                    self.maxhelperwidth = self.helperlabelbox[i].width
        
    def metanav( self, event, midi ):
        # metanav for things that are ctrl based...
        if pygame.key.get_mods() & pygame.KMOD_CTRL:
            if event.key == pygame.K_j or event.key == pygame.K_DOWN: # press down
                # move down in the current helper list
                if self.helper[ self.state ][0] < len(self.helper[ self.state ][1]) - self.helperlinemax:
                    self.helper[ self.state ][0] += 1
                    self.sethelperlines( self.state )
                return 1
            elif event.key == pygame.K_k or event.key == pygame.K_UP: # press up
                # move down in the current helper list
                if self.helper[ self.state ][0] > 0:
                    self.helper[ self.state ][0] -= 1
                    self.sethelperlines( self.state )
                return 1
                
        return 0

#### EDIT CLASS 
    
    def addmidinote( self, note ):
        if note.velocity:
            newnote = MIDI.NoteOnEvent( pitch = note.pitch,
                    velocity = note.data[1] )
        else:
            newnote = MIDI.NoteOffEvent( pitch = note.pitch )
        newnote.absoluteticks = note.absoluteticks 
        self.piece.addmidinote( newnote, self.currenttrack )

    def addnote( self, midi, midinote, velocity, absticks, duration, playsound=True ):
        # abs ticks is the start of the note, duration is how long it is.

        # first delete any notes that are in this vicinity
        selected, midiselected = self.piece.selectnotes( [absticks, absticks+duration], [midinote], self.currenttrack )
        self.piece.deletenotes( selected, self.currenttrack )

        # then add the note 
        # THIS CAUSES THE GHOST DELAY:
        self.piece.addnote( midinote, velocity, absticks, duration, self.currenttrack )
        # and hit a key
        self.keymusic.hitkey( midi, midinote, velocity, self.tickstosecs( duration ),
                              self.piece.channels[self.currenttrack], playsound )

        if not self.play:
            # if we're not playing, then add in the note to the notes that should be sounded
            self.setcurrentticksandload( self.currentabsoluteticks )
        else:
            # if we are playing, we don't want the note to be played twice, once by the player
            # and secondly by the computer.  so just show it onscreen.
            # display turn note on
            reltickpixels = (absticks-self.currentabsoluteticks)* self.pixelspertick
            self.keymusic.addnote( midinote, velocity, reltickpixels )
            reltickpixels += (duration)* self.pixelspertick
            # turn note off after duration...
            self.keymusic.addnote( midinote, 0, reltickpixels )
            

    def addnotepresently( self, midi, midinote, velocity=100, playsound=True ):
        # add note at current absolute ticks, with duration currentnoteticks
        self.addnote( midi, midinote, velocity, 
                      self.roundtonoteticks( self.currentabsoluteticks ), 
                      self.currentnoteticks-1, playsound )
    
    def addnoteonpresently( self, midi, midinote, velocity=100, playsound=True ):
        # add note at current absolute ticks, with duration currentnoteticks
        self.noteson[ midinote ] = [ velocity, self.roundtonoteticks( self.currentabsoluteticks ) ]

        self.keymusic.hitkey( midi, midinote, velocity, 1.0,
                              self.piece.channels[self.currenttrack], playsound )
    
    def addnoteoffpresently( self, midi, midinote, offset=0 ):
        # add note off at current absolute ticks
        try:
            # self.noteson[ midinote] = [ velocity, start_absoluteticks ]
            note = self.noteson[ midinote ]
            # make the note at least as long as the tick-divisions, if not a bit longer...
            notelength = max(   self.currentnoteticks, 
                                ( self.roundtonoteticks( self.currentabsoluteticks ) 
                                 -note[1] + offset )   ) - config.EDITnotespace
            # args:  midi, midinote, velocity, absticks, duration, playsound=True
            self.addnote( midi, midinote, note[0], note[1], notelength, False )
            
            del self.noteson[ midinote ]

        except KeyError:
            pass

    def addnoteatcursor( self, midi ):
        self.addnotepresently( midi, self.keymusic.cursorkeyindex + 9, 
                               self.currentvelocity, True ) # play sound
   
#### EDIT CLASS 

    def changevelocityofselectednotes( self, midi, change, playsound ):
        for note in self.selectedmidinotes:
            if note.name == "Note On":
                note.velocity += change
                if note.velocity > 127:
                    note.velocity = 127
                elif note.velocity <= 0:
                    note.velocity = 1

                if playsound:
                    midi.playnote( note.pitch, note.velocity, 1, 
                                   self.piece.channels[self.currenttrack] )
        
        self.setcurrentticksandload( self.currentabsoluteticks ) 
    
    def changevelocityatcursorselection( self, midi, direction, muchchange=False ):
        tickmin, tickmax, midimin, midimax = self.selectcursorselection()

        if muchchange:
            direction *= 10

        self.changevelocityofselectednotes( midi, direction, True )
        self.setalert( "volume changed "+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" lines." )

#### EDIT CLASS 
    
    def selectnotes( self, tickrange, midirange=None ): 
        self.selectednotes, self.selectedmidinotes = self.piece.selectnotes( 
            tickrange, midirange, self.currenttrack 
        )

    def selectcursorselection( self ):
        if self.anchor:
            self.previousdeltaregion = []
            if self.currentabsoluteticks >= self.anchor[1]:
                # we are ahead of the anchor
                tickmin = self.anchor[1]
                tickmax = self.currentabsoluteticks + self.currentnoteticks
                self.previousdeltaregion.append(self.anchor[1] - self.currentabsoluteticks)
                self.previousdeltaregion.append(self.currentnoteticks)
            else:
                # the anchor is ahead of us
                tickmin = self.currentabsoluteticks
                tickmax = self.anchor[1] + self.currentnoteticks
                self.previousdeltaregion.append(0)
                self.previousdeltaregion.append(self.anchor[1] - self.currentabsoluteticks+ self.currentnoteticks)

            if self.anchor[0] == -1:
                midimin = 0
                midimax = 127
                self.previousdeltaregion.append(-127)
                self.previousdeltaregion.append(127)
            else:
                cursormidi = self.keymusic.cursorkeyindex + 9
                if cursormidi > self.anchor[0]:
                    # we are right of the anchor
                    midimax = cursormidi
                    midimin = self.anchor[0]
                    self.previousdeltaregion.append( self.anchor[0] - cursormidi )
                    self.previousdeltaregion.append(0)
                else:
                    # we are left of the anchor
                    midimax = self.anchor[0]
                    midimin = cursormidi
                    self.previousdeltaregion.append(0)
                    self.previousdeltaregion.append( self.anchor[0] - cursormidi )
        else:
            tickmin = self.currentabsoluteticks
            tickmax = tickmin + self.currentnoteticks
            midimin = self.keymusic.cursorkeyindex + 9
            midimax = midimin
            self.previousdeltaregion = [ 0, self.currentnoteticks, 0, 0 ]

        self.selectnotes( [tickmin,tickmax], [midimin,midimax] )
        return tickmin, tickmax, midimin, midimax

    def deletecursorselection( self, dontkeepnotes=False ):
        # quick delete
        tickmin,tickmax, midimin, midimax = self.selectcursorselection()
        if self.selectednotes:
            # we have a selection going...
            if dontkeepnotes:
                alerttxt = "Deleted notes in "
            else:
                self.copyselectednotes()
                alerttxt = "Cut notes into clipboard from "
            self.piece.deletenotes( self.selectednotes, self.currenttrack )
            self.setcurrentticksandload( self.currentabsoluteticks )
            if midimax-midimin >= 127:
                self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
            else:
                self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                str(midimax-midimin+1)+" columns")
            self.anchor = 0
        else:
            self.setalert("No notes to delete here.")

    def carvecursorselection( self, dontkeepnotes=False ):
        if self.anchor:
            currentticks = self.roundtonoteticks( self.currentabsoluteticks )
            if currentticks >= self.anchor[1]:
                # we are ahead of the anchor
                tickmin = self.anchor[1]
                tickmax = currentticks + self.currentnoteticks
            else:
                # the anchor is ahead of us
                tickmin = currentticks
                tickmax = self.anchor[1] + self.currentnoteticks

            if self.anchor[0] == -1:
                midimin = 0
                midimax = 127
            else:
                cursormidi = self.keymusic.cursorkeyindex + 9
                if cursormidi > self.anchor[0]:
                    # we are right of the anchor
                    midimax = cursormidi
                    midimin = self.anchor[0]
                else:
                    # we are left of the anchor
                    midimax = self.anchor[0]
                    midimin = cursormidi
        else:
            if self.play:
                tickmin = self.roundtonoteticks( self.currentabsoluteticks )
            else:
                tickmin = self.currentabsoluteticks
            currentticks = tickmin
            tickmax = tickmin + self.currentnoteticks
            midimin = self.keymusic.cursorkeyindex + 9
            midimax = midimin

        noteclipboard = self.piece.carveoutregion(     #absolute pitches in this noteclipboard
            [tickmin, tickmax],
            [midimin, midimax],
            self.currenttrack )
       
        if noteclipboard:
            if dontkeepnotes:
                alerttxt="Carved notes in "
            else:
                alerttxt="Carved notes to clipboard from "
                self.noteclipboard = []        # relative pitches/ticks in this noteclipboard
                for note in noteclipboard:
                    self.noteclipboard.append( [ note[0] - self.keymusic.cursorkeyindex - 9,  #pitch
                                              note[1], #velocity
                                              note[2]-currentticks, #absolute ticks
                                              note[3] # duration
                                              ] )
                self.setcurrentticksandload( self.currentabsoluteticks )
            self.anchor = 0
            if midimax-midimin >= 127:
                self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
            else:
                self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                str(midimax-midimin+1)+" columns")
        else:
            self.setalert("No notes to carve here.")

    def mergecursorselection( self, aggressive=False ):
        # quick delete
        tickmin,tickmax, midimin, midimax = self.selectcursorselection()
        # we have a selection going...
        self.piece.deletenotes( self.selectednotes, self.currenttrack )
        
        i = 0
        #imerged = []     # whether note at i merged or not.
        while i < len(self.selectednotes):
            notei = self.selectednotes[i]
            #imerged.append(False)
            j = i + 1 #len(self.selectedmidinotes) - 1
            while j < len(self.selectednotes):
                notej = self.selectednotes[j]
                if notej[0] == notei[0]: # pitch is the same
                    # modify duration of note i:
                    # duration of note j (notej[3]) plus difference in ticks from i to j:
                    notei[3] = notej[3] + (notej[2] - notei[2]) 
                    del self.selectednotes[j]
                    # would like to "break" here but cannot.  must look at all possible futures.
                    #imerged[i] = True
                else: 
                    j += 1
            i += 1
       
        if self.selectednotes:
            if not aggressive:
                alerttxt = "Merged notes in "
                for note in self.selectednotes:
                    self.piece.addnote( note[0],note[1],note[2],note[3], self.currenttrack )
            else:
                alerttxt = "Attempted a merge with every note in "
                for i in range(len(self.selectednotes)):
                    note = self.selectednotes[i]
                    #if imerged[i]:
                    #   self.piece.addnote( note[0],note[1],note[2],note[3], self.currenttrack )
                    #else:
                    midinote = MIDI.NoteOnEvent( pitch=note[0], velocity=note[1] )
                    midinote.absoluteticks = note[2]
                    # keep the on note for sure:
                    self.addmidinote( midinote )
                    # try to delete any subsequent on notes:
                    if self.piece.deletenextonnote( note[0], note[2], self.currenttrack ):
                        # there were no other on notes.  so we need to add an off note.
                        midinote = MIDI.NoteOffEvent( pitch=note[0] )
                        midinote.absoluteticks = note[2]+note[3]
                        self.addmidinote( midinote )

            self.setcurrentticksandload( self.currentabsoluteticks )
            if midimax-midimin >= 127:
                self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows")
            else:
                self.setalert( alerttxt+str(int(round(1.0*(tickmax-tickmin)/self.currentnoteticks)))+" rows, "+
                str(midimax-midimin+1)+" columns")
            self.anchor = 0
        else:
            self.setalert("No notes to merge here.")
    
    def copyselectednotes( self ):
        self.noteclipboard = [] #self.piece.selectednotes[:]
        for note in self.selectednotes:
            self.noteclipboard.append( [ note[0] - self.keymusic.cursorkeyindex - 9,  #pitch
                                         note[1], #velocity
                                         note[2]-self.currentabsoluteticks, #absolute ticks
                                         note[3] # duration
                                       ] )

    def copycursorselection( self ):
        self.selectcursorselection()
        # we have a selection going...
        if self.selectednotes:
            self.copyselectednotes()
            self.anchor = 0
            self.setalert("Copied notes to clipboard.")
        else:
            self.setalert("No notes to copy.")

    def pastenoteclipboard( self, violently=False, copydeleted=False ):
        if len(self.noteclipboard):
            if self.play:
                currentticks = self.roundtonoteticks( self.currentabsoluteticks )
            else:
                currentticks = self.currentabsoluteticks

            midinote = self.keymusic.cursorkeyindex + 9   
            if violently or copydeleted:
                # wipe out existing notes in the same area
                tickrange = [ currentticks + self.previousdeltaregion[0],
                              currentticks + self.previousdeltaregion[1] ]

                midirange = [ midinote + self.previousdeltaregion[2],
                              midinote + self.previousdeltaregion[3] ]
                
                # might as well show the region we are destroying, 
                # if we have no anchor already:
                if self.anchor:
                    # don't worry about it
                    pass
                elif midirange[-1] != midirange[0] or tickrange[0] != tickrange[1]:
                    # show the selected|pasted region
                    midi = -1
                    if midirange[0] == midinote:
                        midi = midirange[1]
                    elif midirange[1] == midinote:
                        midi = midirange[0]
                    
                    tick = currentticks
                    if tickrange[0] == currentticks:
                        tick = tickrange[1] - self.currentnoteticks
                    elif tickrange[1] - self.currentnoteticks == currentticks:
                        tick = tickrange[0]
                    self.anchor = [ midi, tick ]

                deadnotes = self.piece.carveoutregion( tickrange, midirange, self.currenttrack )

                for note in self.noteclipboard:
                    self.piece.addnote( note[0]+midinote, note[1], 
                                        note[2]+currentticks, note[3], self.currenttrack )
                if copydeleted:
                    if deadnotes:
                        self.noteclipboard = []
                        for note in deadnotes:
                            self.noteclipboard.append( [ note[0] - self.keymusic.cursorkeyindex - 9,  #pitch
                                                      note[1], #velocity
                                                      note[2]-currentticks, #absolute ticks
                                                      note[3] # duration
                                                      ] )
                        self.setalert("Pasted and copied existing notes to clipboard.")
                    else:
                        self.setalert("Pasted but no existing notes to copy.")
                else:
                    self.setalert("Violent paste (deleted underlying note region).")
            else:
                # just remove existing notes when they interfere with adding notes
                self.setalert("Pasted notes from clipboard.")
                for note in self.noteclipboard:
                    absnote = [ note[0]+midinote, note[1], 
                                note[2]+currentticks, note[3] ]
                    # carve out where we add the note
                    self.piece.carveoutregion( [ absnote[2], absnote[2]+note[3] ],
                                               [ absnote[0] ], self.currenttrack )
                    self.piece.addnote( absnote[0], absnote[1], absnote[2],
                                        absnote[3], self.currenttrack )

            #self.noteclipboard = []
            
            self.setcurrentticksandload( self.currentabsoluteticks )
        else:
            self.setalert("No notes in clipboard.")

#### EDIT CLASS 

    def draw( self, screen ):
        if self.state == self.NAVIGATIONstate or self.state == self.COMMANDstate:
            self.keymusic.setcursorheight( self.currentnoteticks*self.pixelspertick )

            if self.anchor:
                self.keymusic.setselectanchor( [ self.anchor[0], 
                                                (self.anchor[1] - self.currentabsoluteticks)*self.pixelspertick ] )
            else:
                self.keymusic.setselectanchor( 0 )
        else:
            self.keymusic.setcursorheight( 0 )
            self.keymusic.setselectanchor( 0 )

        DDRClass.draw( self, screen )

        if self.state == self.COMMANDstate: 
            fontandsize = pygame.font.SysFont(self.commandfont, self.commandfontsize)
            commandlabel = fontandsize.render( "cmd: " + self.command, 
                                                1, self.commandfontcolor )
            commandbox = commandlabel.get_rect()
            commandbox.left = 10
            commandbox.bottom = screen.get_height() - 10
            pygame.draw.rect( screen, self.commandbackcolor,  commandbox )
            screen.blit( commandlabel, commandbox )

        if len(self.helperlines):
            #screenwidth, screenheight = screen.get_size()
            leftx = 10
            topy = 10 #0.1*screenheight
            self.helperlabelbox[0].left = leftx
            self.helperlabelbox[0].top = topy
            helperbgbox = Rect(leftx-5, topy-5, 
                               self.maxhelperwidth+10, 
                               len(self.helperlines)*self.helperlabelbox[0].height+10 )
            pygame.draw.rect( screen, self.helperbackcolor, helperbgbox )
            #pygame.draw.rect( screen, self.helperbackcolor,  self.helperlabelbox[0] )
            screen.blit( self.helperlabel[0], self.helperlabelbox[0] )
            for i in range(1,len(self.helperlines)):
                self.helperlabelbox[i].left = leftx
                self.helperlabelbox[i].top = self.helperlabelbox[i-1].bottom 
                #pygame.draw.rect( screen, self.helperbackcolor,  self.helperlabelbox[i] )
                screen.blit( self.helperlabel[i], self.helperlabelbox[i] )

#### END EDIT CLASS
