from ttkbootstrap import *
from srctools import Keyvalues
import os
from richpresence import main as presence, stop as stoppresence
import threading
from PIL import Image, ImageTk, ImageChops
from tkinter.messagebox import showinfo, showwarning, showerror
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter.font import Font
from ttkbootstrap.scrolled import ScrolledFrame
import sys
import json
import medialist_transform
import webbrowser
import subprocess
from shlex import split as splitcommand
from requests import get as getrequest
from requests.exceptions import RequestException
from time import sleep
from datetime import date
from random import shuffle
from tktooltip import ToolTip
ask_for_gameinfo = medialist_transform.ask_for_gameinfo

def _find_first(s: str, chars: list[str] | tuple[str]) -> int:
    '''
    In `s`, find the first character of `chars` that exists in this string.
    '''
    for i in chars:
        ind = s.find(i)
        if ind != -1:
            return ind
    
    return -1

def _find_last(s: str, chars: list[str] | tuple[str]) -> int:
    '''
    In `s`, find the first character of `chars` that exists in this string, iterating from the end.
    '''
    found_ind = -1
    for ind, i in enumerate(s[::-1]):
        if i in chars:
            found_ind = ind
            break
    
    return len(s) - found_ind

#find_version_number = lambda s: _find_first(s, tuple('01234567890.'))
#find_version_number = lambda s: _find_first(s, tuple('01234567890.'))

def find_version_number(version: str) -> slice:
    return slice(
        _find_first(version, tuple('01234567890.')),
        _find_last(version, tuple('01234567890.'))
    )

def is_newer_version(version: str) -> bool:
    ver_ind = find_version_number(version)
    ver_string_ind = find_version_number(VERSION)
    
    ver_string_ints = [int(i) for i in VERSION[ver_string_ind].split('.')]
    ver_ints = [int(i) for i in version[ver_ind].split('.')]
    
    for i, j in zip(ver_string_ints, ver_ints):
        if i < j:
            return True
        
    return False

VERSION = '0.9.3'

UPDATE_FETCH_FAILED, NOUPDATE, UPDATE_AVAILABLE = range(3)

def checkforupdates_noretry() -> int:
    '''
    Return whether an update is available.
    '''
    try:
        resp = getrequest('https://api.github.com/repos/electrovoyage/electrovoyage-Hammer-Launcher/releases/latest')
        resp_data = resp.json()
        
        if is_newer_version(resp_data['name']):
            return UPDATE_AVAILABLE
        else:
            return NOUPDATE
    except RequestException:
        return UPDATE_FETCH_FAILED
    
def checkforupdates(retries: int = 5, delay_ms: int = 1000) -> int:
    '''
    Check for updates, with a certain amount of retries and a specified delay between them.
    '''
    
    returns = []
    for _ in range(retries):
        result = checkforupdates_noretry()
        returns.append(result)
        
        if result > UPDATE_FETCH_FAILED:
            break
        
        sleep(delay_ms / 1000)
        win.update()
        
    best_return = max(returns)
    
    if best_return == UPDATE_FETCH_FAILED:
        print(f'Update check failed after {retries} retries. Assuming the internet is unavailable. Shutting down Rich Presence.')
        stoppresence()
        
    return best_return
    
def makeversionstring() -> tuple[str, int]:
    update_status = checkforupdates()
    match update_status:
        case 1:
            return (VERSION, update_status)
        case 2:
            return (f'{VERSION} (update available!)', update_status)
        case 0:
            return (f'{VERSION} (failed to check for updates)', update_status)
        
setcursor = lambda x: win.configure(cursor=x) if os.name == 'nt' else lambda x: x
        
def showversionstring() -> int:
    setcursor('starting')
    s, status = makeversionstring()
    statusstr.configure(text=f'Version {s} (SDK format version {medialist_transform.LATEST_SDK_VERSION})')
    setcursor('arrow')
    return status

PYINSTALLER = getattr(sys, 'frozen', False)

def screw_up_words(s: str) -> str:
    '''
    Randomize word order in string.
    '''
    words = [i.strip() for i in s.split(' ')]
    if len(words) < 2: return s
    for _ in range(5):
        shuffle(words)
    return ' '.join(words)

def screw_up_letters(s: str) -> str:
    '''
    Randomize character order in string.
    '''
    chars = list(s)
    for _ in range(5):
        shuffle(chars)
    return ''.join(chars)

def aprilfools(s: str) -> str:
    if date.today().day == 1 and date.today().month == 4:
        if date.today().year % 4 == 0:
            return screw_up_letters(s)
        else:
            return screw_up_words(s)
    return s

if PYINSTALLER:
    try:
        import pyi_splash as spl # type: ignore
        spl.update_text(aprilfools('electrovoyage\'s Hammer Launcher'))
        spl.close()

        del spl
    except:
        pass

# required to use files written into the executable
def getcwd() -> str:
    return os.path.dirname(__file__)

# Workaround for shortcuts / "open with" and working directory
if PYINSTALLER:
    APP_DIRECTORY = os.path.dirname(sys.executable)
    APP_RESOURCE_DIRECTORY = os.path.join(
        os.path.dirname(__file__),
        'resources'
    )
else:
    APP_DIRECTORY = getcwd()
    APP_RESOURCE_DIRECTORY = os.path.join(APP_DIRECTORY, 'resources')

#assetpack = AssetPackWrapper(os.path.join(getcwd(), 'resources', 'assets.packed'), PYINSTALLER, os.path.join(APP_DIRECTORY, 'resources'))

win = Window(aprilfools('electrovoyage.\'s Hammer Launcher'), 'darkly', os.path.join(APP_RESOURCE_DIRECTORY, 'logo.png'), (450, 600), minsize=(450, 300), hdpi=False)
win.withdraw()
if '--shutup' not in sys.argv:
    showwarning(aprilfools('Hammer launcher beta'), aprilfools('This is a beta version of electrovoyage\'s Hammer Launcher. If another program shows up in your Discord profile instead of the Hammer launcher or if you encounter any other sort of issue, please report them to:\n\nelectrovoyagesoftware@gmail.com, or\n\nhttps://github.com/electrovoyage/electrovoyage-Hammer-Launcher/issues\n\nAdd the "--shutup" startup argument to remove this warning.'))
presencethread = threading.Thread(target=presence, daemon=True)

def RightclickMenu(widget: tk.Widget, menu: Menu):
    widget.bind('<Button-3>', lambda x: menu.tk_popup(x.x_root, x.y_root))

def onWindowClosed():
    win.destroy()
    
def dark_title_bar(window: Window):
    '''
    Make window have a dark title bar.
    '''
    import ctypes as ct
    window.update()
    DWMWA_USE_IMMERSIVE_DARK_MODE = 20
    set_window_attribute = ct.windll.dwmapi.DwmSetWindowAttribute
    get_parent = ct.windll.user32.GetParent
    hwnd = get_parent(window.winfo_id())
    rendering_policy = DWMWA_USE_IMMERSIVE_DARK_MODE
    value = 2
    value = ct.c_int(value)
    set_window_attribute(hwnd, rendering_policy, ct.byref(value), ct.sizeof(value))
    
if os.name == 'nt' and '--defaulttitlebar' not in sys.argv:
    dark_title_bar(win)
    
if '--superdark' in sys.argv:
    win.style.theme_use('black')
    
trebuchet_bold = Font(family='Trebuchet MS', size=16, weight='bold')
    
pil_logo = Image.open(os.path.join(APP_RESOURCE_DIRECTORY, 'logo.png'))

global logo, large_logo
logo = ImageTk.PhotoImage(pil_logo.resize((48, 48), Image.BILINEAR))
large_logo = ImageTk.PhotoImage(pil_logo.resize((100, 100), Image.BILINEAR))

welcome_frame = Frame(win, style=DARK)
welcome_frame.pack(side=TOP, fill=BOTH, anchor=N)

welcometext1 = Label(welcome_frame, text=aprilfools('Welcome to'), justify=LEFT, font = ('Trebuchet MS', 11), background='#303030')
welcometext1.grid(row=0, column=0, sticky=NW)
welcometext2 = Label(welcome_frame, text=aprilfools('electrovoyage.\'s Hammer Launcher'), justify=LEFT, font=trebuchet_bold, background='#303030')
welcometext2.grid(row=1, column=0, sticky=SW)
logo_in_the_corner = Label(welcome_frame, image=logo, background='#303030')
logo_in_the_corner.grid(row=0, column=1, rowspan=2, sticky=S)

def on_logo_leftclick(*args):
    logo_in_the_corner.configure(relief=SUNKEN)
    
def on_logo_leftclick_released(*args):
    logo_in_the_corner.configure(relief=FLAT)
    welcometext1.configure(text=welcometext1.cget('text')[::-1])
    welcometext2.configure(text=welcometext2.cget('text')[::-1])
    win.title(win.title()[::-1])
    
logo_in_the_corner.bind('<Button-1>', on_logo_leftclick)
logo_in_the_corner.bind('<ButtonRelease-1>', on_logo_leftclick_released)

logorightclickmenu = Menu(logo_in_the_corner)

logorightclickmenu.add_command(label=aprilfools('Check for updates'), command=showversionstring)
logorightclickmenu.add_separator()
logorightclickmenu.add_command(label=aprilfools('GitHub repository'), command = lambda: webbrowser.open('https://github.com/electrovoyage/electrovoyage-Hammer-Launcher'))
logorightclickmenu.add_command(label=aprilfools('electrovoyage. on YouTube'), command = lambda: webbrowser.open('https://youtube.com/@electrovoyage.'))

RightclickMenu(logo_in_the_corner, logorightclickmenu)

welcome_frame.columnconfigure(0, weight=1)
welcome_frame.columnconfigure(1, weight=0)

#applist.pack(expand=True, fill=BOTH)

appframe = Frame(win)
appframe.pack(expand=True, fill=BOTH)

applist = ScrolledFrame(appframe, padding=10, width=400, bootstyle=ROUND + (LIGHT if '--darkscrollbar' not in sys.argv else ''))
applist.configure(style='')
applist.pack(expand=True, fill=BOTH)

statusstr = Label(win, text='', style=INVERSE + DARK)
if showversionstring() >= NOUPDATE:
    presencethread.start()

statusstr.pack(side=BOTTOM, anchor=S, fill=X)
    
global launcherpath, sdkdata
sdkdata = launcherpath = None

def invertAlpha(_im: Image.Image) -> Image.Image:
    im = _im.copy()
    alpha = im.getchannel('A')
    alpha = ImageChops.invert(alpha)
    im.putalpha(alpha)
    return im

ProgramType = str | None

class App:
    @property
    def invert_image(self) -> bool:
        return self._invert_var.get()
    
    def __init__(self, name: str, iconpath: str, icon: Image.Image, invertedicon: Image.Image, Program: ProgramType = None, ShellExecute: ProgramType = None, groupname: str = '', programid: str = '', invert_image: bool = True, tooltip: str | None = None):
        if not (Program or ShellExecute):
            raise ValueError(f'invalid application {name}: no ShellExecute or Program defined')
        
        if Program:
            self.program = Program
            self.shellexecute = False
        else:
            self.program = ShellExecute
            self.shellexecute = True
        
        self.name = name
        self._invert_var = BooleanVar(value=invert_image)
        self.smallicon = icon.resize((32, 32), Image.NEAREST)
        self.smallicontk = ImageTk.PhotoImage(self.smallicon)
        self.smallinvicon = invertedicon.resize((32, 32), Image.NEAREST)
        self.smallinvicontk = ImageTk.PhotoImage(self.smallinvicon)
        self.groupname = groupname
        self.programid = programid
        self.iconpath = iconpath
        self.tooltip = tooltip
        
        self.STARTED_INVERTED = invert_image
        
    def saveimageinversion(self): 
        self.img_label.configure(image=self.smallicontk if self.STARTED_INVERTED == self.invert_image else self.smallinvicontk)
        
        #medialist = [i.serialize() for i in app_list_manager.apps]
        medialist = {}
        
        for key, val in app_list_manager.group_lists.items():
            medialist[key] = [i.serialize() for i in val]
        
        sdkdata['medialist'] = medialist
        savesdk()
        
    def runcommand(self):
        if self.shellexecute:
            webbrowser.open(self.program)
        else:
            original_directory = os.getcwd()
            os.chdir(sdkdata['binpath'])
            subprocess.Popen(splitcommand(self.program), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            #os.system(self.program)
            os.chdir(original_directory)
            
    def setframe(self, frame: Frame):
        self.frame = frame
        
    def set_image_label(self, label: Label):
        self.img_label = label
        
    def __repr__(self) -> str:
        return f'<application name={self.name}>'
    
    def makemenu(self) -> Menu:
        menu = Menu(win)
        menu.add_command(label='Run', command=self.runcommand)
        menu.add_separator()
        #menu.add_command(label='Move to testgroup', command=lambda: app_list_manager.move_app(self, 'Assets'))
        menu.add_command(label=aprilfools('Move up'), command=lambda: app_list_manager.swap_above(self))
        menu.add_command(label=aprilfools('Move down'), command=lambda: app_list_manager.swap_below(self))
        menu.add_separator()
        menu.add_checkbutton(label=aprilfools('Invert image'), onvalue=True, offvalue=False, variable=self._invert_var, command=self.saveimageinversion)
        
        return menu
    
    def serialize(self) -> dict:
        return {
            'Image': self.iconpath,
            'Program': None if self.shellexecute else self.program,
            'Title': self.name,
            'invert_image': self.invert_image,
            'ShellExecute': self.program if self.shellexecute else None,
            'tooltip': self.tooltip
        }
    
def swapvalues(container: list | tuple, a: int, b: int):
    '''
    Swap values at indices a and b.
    '''
    _container = container.copy()
    old_a_value = _container[a]
    old_b_value = _container[b]
    _container[b] = old_a_value
    _container[a] = old_b_value
    
    return _container
        
class ApplicationList:
    def __init__(self, base: ScrolledFrame):
        self.base = base
        self.apps: list[App] = []
        self.app_frames: list[Frame] = []
        self.app_frame_dict: dict[str, Frame] = []
        self.groups: dict[str, Frame] = {}
        self.group_lists: dict[str, list[App]] = {}
        
    def addApp(self, name: str, iconpath: str, icon: Image.Image, invertedicon: Image.Image, groupname: str, program: ProgramType = None, shellexecute: ProgramType = None, programid: str = '', invert_image: bool = True, tooltip: str | None = None):
        newapp = App(name, iconpath, icon, invertedicon, program, shellexecute, groupname, programid, invert_image, tooltip)
        self.apps.append(newapp)
        if groupname not in tuple(self.group_lists.keys()):
            self.group_lists[groupname] = []
        self.group_lists[groupname].append(newapp)
        self._makeGroupIfNecessary(groupname)
        self._makeframe(newapp, groupname)
        
    def swap_above(self, app: App):
        #print(self.group_lists, sep='\n\n\n')
        item_group_key, item_group = self._find_group(app)
        
        if item_group.index(app) == 0:
            return
        else:
            item_group = swapvalues(item_group, item_group.index(app), item_group.index(app) - 1)
            #self.group_lists[item_group_key] = item_group
            _item_group = self.group_lists[item_group_key]
            
            oldapps = [
                _item_group[_item_group.index(app)],
                _item_group[_item_group.index(app) - 1],
            ]
            
            frames_to_repack = [i.frame for i in item_group]
            
            #print(oldapps)
            for i in oldapps:
                i.frame.pack_forget()
                
            for i in item_group:
                i.frame.pack_forget()
                
            #print(*frames_to_repack, sep='\n')
            for i in frames_to_repack:
                i.pack(side=TOP, expand=True, fill=X)
                
            self.group_lists[item_group_key] = item_group
            
            self.save_new_layout(item_group_key)
            
    def swap_below(self, app: App):
        #print(self.group_lists, sep='\n\n\n')
        item_group_key, item_group = self._find_group(app)
        
        if item_group.index(app) == len(item_group) - 1:
            return
        else:
            item_group = swapvalues(item_group, item_group.index(app), item_group.index(app) + 1)
            #self.group_lists[item_group_key] = item_group
            _item_group = self.group_lists[item_group_key]
            #print(*([(i, j) for i, j in enumerate(item_group)]), sep = '\n')
            oldapps = [
                _item_group[_item_group.index(app)],
                _item_group[_item_group.index(app) + 1],
            ]
            
            frames_to_repack = [i.frame for i in item_group]
            
            #print(oldapps)
            for i in oldapps:
                i.frame.pack_forget()
                
            for i in item_group:
                i.frame.pack_forget()
                
            #print(*frames_to_repack, sep='\n')
            for i in frames_to_repack:
                i.pack(side=TOP, expand=True, fill=X)
                
            self.group_lists[item_group_key] = item_group
            
            self.save_new_layout(item_group_key)
        
    def _find_group(self, app: App) -> tuple[str, list[App]]:
        for key, lst in self.group_lists.items():
            if app in lst:
                return key, lst
            
    def save_new_layout(self, groupname: str):
        #print(medialist, groupname)
        global medialist, sdkdata
        medialist[groupname] = [i.serialize() for i in self.group_lists[groupname]]
        sdkdata['medialist'] = medialist
        
        #print(sdkdata)
        #print(json.dumps(sdkdata, indent=4))
        
        savesdk()        
        
    def _makeGroupIfNecessary(self, groupname: str):
        if groupname in self.groups.keys(): return
        self.groups[groupname] = Labelframe(self.base, text=groupname)
        self.groups[groupname].pack(side=TOP, fill=X, padx=5, pady=5)
        
    def _makeframe(self, app: App, groupname: str):
        frame = Frame(self.groups[groupname], padding=5)
        namelabel = Label(frame, text=aprilfools(app.name), justify=LEFT, font=('Inter', 12))
        namelabel.grid(row=0, column=0)
        imagelabel = Label(frame, image=app.smallicontk)
        imagelabel.grid(column=1, row=0, sticky=E, padx=5)
        
        frame.columnconfigure(0, weight=0)
        frame.columnconfigure(1, weight=1)

        for widget in (frame, namelabel, imagelabel):
            widget.bind('<Button-1>', lambda _: selectApp(app, frame))
            widget.bind('<ButtonRelease-1>', lambda _: releaseAppButton(frame))
            RightclickMenu(widget, app.makemenu())
        frame.pack(side=TOP, expand=True, fill=X)
        app.setframe(frame)
        app.set_image_label(imagelabel)
        self.app_frames.append(frame)
        
        #ToolTip(frame, )
        if app.tooltip != None:
            ToolTip(border=2, borderwidth=2, relief=GROOVE, bg = "#222222", fg="#FFFFFF", aspect = 1000, widget=frame, msg=app.tooltip)
            #ToolTip(parent_kwargs={'bg': '#222222'}, widget=namelabel, msg=app.tooltip)
            #ToolTip(parent_kwargs={'bg': '#222222'}, widget=imagelabel, msg=app.tooltip)
    
    def move_app(self, app: App, newgroup: str):
        app.frame.destroy()
        oldgroup = app.groupname
        newframe = self._makeframe(app, newgroup)
        app.setframe(newframe)
        global sdkdata
        appdata = sdkdata['medialist'][oldgroup].pop(app.programid)
        sdkdata['medialist'][newgroup][app.programid] = appdata
        #print(json.dumps(sdkdata, indent=4))
        
        #self.groups[newgroup]
    
    def run_app(self, app: App):
        #print(app.shellexecute, app.program)
        app.runcommand()
        
def selectApp(app: App, frame: Frame):
    frame.configure(relief=SUNKEN)
    win.update()
    app_list_manager.run_app(app)
    
def releaseAppButton(frame: Frame):
    frame.configure(relief=FLAT)
        
app_list_manager = ApplicationList(applist)
sdkdata: dict[str, dict[str, dict[str, dict[str, str]]]]

def savesdk():
    with open(os.path.join(APP_DIRECTORY, 'sdk.json'), 'w') as sdk:
        json.dump(sdkdata, sdk, indent=4)

def opensdk():
    global sdkdata
    with open(os.path.join(APP_DIRECTORY, 'sdk.json')) as jsfile:
        sdkdata = json.load(jsfile)
        
def reloadsdk():
    opensdk()
    
    global binpath, sdkpath, medialist
    binpath = sdkdata['binpath']
    sdkpath = sdkdata['sdkpath']

    medialist = sdkdata['medialist']
    #print(medialist)

if 'sdk.json' not in os.listdir(APP_DIRECTORY):
    ginfo = ask_for_gameinfo()
    #launcherpath = os.path.join(dir, 'SDKLauncher')
    vproject = os.path.dirname(ginfo)
    binpath = os.path.join(os.path.dirname(vproject), 'bin')
    launcherpath = os.path.join(binpath, 'SDKLauncher')
    with open(os.path.join(launcherpath, 'MediaList.txt')) as fp:
        kv = Keyvalues.parse(fp.read())
        
    sdkdata = medialist_transform.upgradeMediaList({'binpath': binpath, 'sdkpath': launcherpath, 'vproject': vproject, 'medialist': medialist_transform.transformMediaList(kv.as_dict())})

    with open(os.path.join(APP_DIRECTORY, 'sdk.json'), 'w') as jsfile:
        json.dump(sdkdata, jsfile, indent=4)
        
reloadsdk()
    
with open(os.path.join(APP_DIRECTORY, 'sdktemp'), 'w') as sdk:
    sdkdata = medialist_transform.upgradeMediaList(sdkdata)
    json.dump(sdkdata, sdk, indent=4)
    
os.rename(os.path.join(APP_DIRECTORY, 'sdktemp')), os.path.join(APP_DIRECTORY, 'sdk.json')
        
global medialist
medialist = sdkdata['medialist']
for group, programs in medialist.items():
    sdkdata.setdefault('version', '1')
        
    for program in programs:
        _img = Image.open(os.path.join(sdkdata['sdkpath'], 'vgui', program['Image'] + '.tga'))
        img = invertAlpha(_img) if program['invert_image'] else _img
        inverted_img = _img if program['invert_image'] else invertAlpha(_img)
        program.setdefault('Program', None)
        program.setdefault('ShellExecute', None)
        app_list_manager.addApp(program['Title'], program['Image'], img, inverted_img, group, program['Program'], program['ShellExecute'], program['Title'].lower(), program['invert_image'], program['tooltip'])
    
win.wm_protocol('WM_DELETE_WINDOW', onWindowClosed)

os.environ['VPROJECT'] = os.environ['vproject'] = sdkdata['vproject']

win.deiconify()
win.focus()
win.mainloop()