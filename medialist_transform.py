import os
import sys
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showwarning, showinfo

def ask_for_gameinfo() -> str:
    showinfo('Specify gameinfo path', 'Please locate your game\'s gameinfo in the next dialog.')
    while True:
        ginfo = askopenfilename(title='Locate your gameinfo', filetypes=[('Gameinfo / text file', '.txt')], defaultextension='.txt')
        if not ginfo.strip():
            sys.exit()
        elif not os.path.exists(os.path.join(
            os.path.dirname(os.path.dirname(ginfo)), 'bin'
        )):
            showwarning('Invalid path', 'This file does not appear to be in a valid Source engine game or it is not inside a valid content folder. Please specify a valid path.')
        else: break
        
    return ginfo

def transformMediaList(medialist: dict) -> dict:
    '''
    Convert MediaList.txt contents to sdk.json contents.
    '''
    media = medialist['media']
    images: dict[str, dict] = media['images']
    image_directory = {}
    for _, i in images.items():
        image_directory.update({i['index']: i['image']})
        
    newdict = {}
        
    #print(image_directory)
        
    sections: dict[str, dict[str, dict]] = media['sections']
    for _group, i in sections.items():
        group = i.pop('name')
        i.pop('id')
        newdict[group] = {}
        for program, j in i.items():
            newdict[group][program] = {}
            
            #print(program, j)
            newdict[group][program]['Image'] = image_directory[j['image']]
            if 'shellexecute' in j.keys():
                newdict[group][program]['ShellExecute'] = j['shellexecute']
            elif 'program' in j.keys():
                newdict[group][program]['Program'] = j['program']
            else:
                raise ValueError(f'invalid program {j['title']}: no Program or ShellExecute value')
            newdict[group][program]['Title'] = j['title']
            
    return newdict

LATEST_SDK_VERSION = '3.1'
VALVE_ORIGINAL_ICONS = ['icon_create', 'icon_document', 'icon_faceposer', 'icon_file', 'icon_files', 'icon_folder', 'icon_folder_16', 'icon_hammer', 'icon_hl2_media', 'icon_hlmv', 'icon_refresh', 'icon_reset', 'icon_scenemanager', 'icon_soft', 'icon_weblink']

def upgradeMediaList(_medialist: dict) -> dict:
    '''
    Convert a sdk.json file to the latest version.
    '''
    medialist = _medialist.copy()
    medialist.setdefault('version', '1')
    version = medialist['version']
    #print(medialist)
    if version == LATEST_SDK_VERSION:
        return medialist
    elif float(version) > float(LATEST_SDK_VERSION):
        raise ValueError('sdk.json version is too new. To regenerate file, please delete it and restart program.')
    else:
        if int(version) < 3:
            medialist.setdefault('vproject')
            if medialist['vproject']:
                contentpath = medialist['vproject']
            else:
                ginfo = ask_for_gameinfo()
                contentpath = os.path.dirname(ginfo)
        #match version:
        #    case '1':
        #        newmedialist: dict[str, list[dict[str, str]]] = {}
        #        for categoryname, categoryapps in medialist['medialist'].items():
        #            #print(categoryname, categoryapps)
        #            newmedialist[categoryname] = []
        #            
        #            for _, programdata in categoryapps.items():
        #                programdata['invert_image'] = programdata['Image'] not in VALVE_ORIGINAL_ICONS
        #                programdata['tooltip'] = None
        #                newmedialist[categoryname].append(programdata)
        #                
        #        #return {
        #        #    'binpath': medialist['binpath'],
        #        #    'sdkpath': medialist['sdkpath'],
        #        #    'vproject': contentpath,
        #        #    'version': LATEST_SDK_VERSION,
        #        #    'medialist': newmedialist,
        #        #}
        #    case '2':
        #        newmedialist = medialist.copy()
        #        newmedialist['vproject'] = contentpath
        #        newmedialist['version'] = LATEST_SDK_VERSION
        #        
        #        for programlist in newmedialist['medialist'].values():
        #            for program in programlist:
        #                program['tooltip'] = None
        #        
        #        return newmedialist
        #    
        #    case '3':
        #        
        fver = float(version)
        if fver < 2:
            newmedialist: dict[str, list[dict[str, str]]] = {}
            for categoryname, categoryapps in medialist['medialist'].items():
                    newmedialist[categoryname] = []
                    
                    for programdata in categoryapps.values():
                        programdata['invert_image'] = programdata['Image'] not in VALVE_ORIGINAL_ICONS
                        programdata['tooltip'] = None
                        newmedialist[categoryname].append(programdata)
                        
            medialist['medialist'] = newmedialist
            
        if fver < 3:
            medialist['vproject'] = contentpath
            
        if fver < 3.1:
            for programlist in medialist['medialist'].values():
                for program in programlist:
                    program['tooltip'] = None
                    
        medialist['version'] = LATEST_SDK_VERSION
        return medialist