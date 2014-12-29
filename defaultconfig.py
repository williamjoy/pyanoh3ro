# IMPORTANT SOUND SETTINGS
# how to make the fluidsynth go.  
FLUIDSYNTHdriver = "alsa"
# full list of choices:
# 'alsa', 'oss', 'jack', 'portaudio', 'sndmgr', 'coreaudio' or 'Direct Sound'
# ( see https://code.google.com/p/mingus/wiki/tutorialFluidsynth )
# For PyanoH3ro to work, you need python-mingus.  See the README.

# DISPLAY SETTINGS
# display resolution
DEFAULTresolution = (960,540)

# size of the white / black keys
WHITEKEYfraction = 0.13 # fraction of the size of the vertical screen
BLACKKEYwhitefraction = 0.7 # fraction of the size of a white key

FONT = "monospace"
FONTSIZEmultiplier = 1
DIVIDERcolor = (100,120,80)
MEASUREcolor = (10,0,10)

# SETTINGS FOR PLAY AND EDIT

# click track or metronome settings
METRONOMEdefault = False    # whether to default to a metronome/clicktrack or not
CLICKTRACKvolume = 0.05     # number from 0 to 1

# PLAY SETTINGS
SANDBOXplay = 1 # default whether to play sandbox mode or not.  can change in game.
DEFAULTdifficulty = 0

# PIANO KEYBOARD SETTINGS - how big, what colors, etc.
# rainbow colors for the keyboard.  starts on C, then chromatic up to B
# in the (R,G,B) format, values from 0 to 255 inclusive.
#               C           C#        D         Eb              E           F
rainbow = [ (255,0,0), (245, 40, 0), (210,80,0), (190,130,0), (220,220,0), (140,228,0), 
            (0,240,0), (0,159,199), (0,55,248), (33,0,252), (114,0,228), (180,0,180) ]
#               F#          G           Ab          A           Bb          B
# technically it can be whatever colors you want, without it being a rainbow.
# The following affect the appearance of the keys and notes during regular play/edit:
NOTEwidth = 20
KEYwidth = 50
PIXELSperbeat = 100

# MORE SOUND SETTINGS
# instrument bank.  originally copied from /usr/share/sounds/sf2/FluidR3_GM.sf2,
# but then I found an augmented version online.  See copyright in attrib.
SOUNDfont = "resources/FluidR3_GM-2.sf2"
#SOUNDfont = "resources/The_Nes_Soundfont.sf2"
# 0, 1 = piano
# 2 = honky tonk piano
# 3 = tacky piano
# 4,5 = electric piano
# ... see http://en.wikipedia.org/wiki/General_MIDI#Program_change_events
# 124 = telephone
# 125 = helicopter
# 126 = water??
# 127 = gunshot
SOUNDfontPIANO = 1
SOUNDfontORGAN = 19
SOUNDfontHONKY = 2

INSTRUMENT = { 
    "drums" : "drums",  # drums get their own special channel (9)
    "piano" : 1,
    "organ" : 19,
    "epiano" : 4,
    "bass" : 33,    # anywhere between 32 and 39 actually
    "violin" : 40,
    "viola" : 41,
    "cello" : 42,
    "whistle" : 78,
    "ocarina": 79,
    "square" : 80,
    "saw" : 81,
    "voice" : 85,
    "choir" : 91
}

# defaults for channels:
PIANOchannel = 0

# Default instrument
DEFAULTinstrument = 0

# EDIT SETTINGS
COMMANDhistory = 100 # number of lines to keep
HELPERLINEmax = 5
CURSORcolor = (100,250,250)
# defaults for new compositions
# get the tempo and stuff from the midi file.
PLAYERstarts = True # true for solo piano pieces, false when there is background music
ALLOWEDplayertracks = [0] # which track does the player have to play?  
ALLOWEDdifficulties = [0] # list of allowed difficulties
TEMPO = 120
DEFAULTplayertrack = 0

# resolution = # of ticks per beat.  
EDITresolution = 5040   # (1 * 2 * 3 * 2 * 5 * 7 * 2 * 3 * 2 * 2 * 2)/4 
                        # if EDITresolution = 5040, and there are four beats per measure,
                        # this means we can represent these various notes by these numbers of ticks:
                        # NOTE            # TICKS
                        # whole            20,160
                        # half             10,080
                        # third             6,720
                        # quarter           5,040
                        # fifth             4,032
                        # quarter-triplets  3,360
                        # seventh           2,880
                        # eighth            2,520
                        # sixteenth         1,260
                        # thirty-secondth     630
                        # sixty-fourth        315
                        # and many others in between.
#
EDITstaccato = 0.5 # fraction of time duration that stacatto notes get based on the current note duration
EDITnotespace = 20 # # of ticks to give white-space letting a note go and hitting the next

# GAME relevant variables
# GAMESTATEexit = 0 # exit the game, MUST BE ZERO, so no choice :)
GAMESTATEplay = 1 # playing a piece
GAMESTATEpiecesettings = 2  # setting various settings for the piece -- tempo, etc.
GAMESTATEpieceselection = 3 # selecting the piece from the "pieces" directory
GAMESTATEmainmenu = 4 # main menu
GAMESTATEsettings = 5 # settings menu
GAMESTATEeditmenu = 6 # menu to choose which piece to edit
GAMESTATEedit = 7 # editting/creating a piece

PIECEdirectory = "songs"
RESOURCEdirectory = "resources"