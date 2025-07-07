#---------------------------------------------------------------------------------------------------------

## Dropped Path Function within Tkinter

def on_drop(event, path_var, dropped_path_container):

    from tkinter import StringVar
    from pathlib import Path

    raw_path = event.data.strip('{}')
    dropped_path_container [0] = Path(raw_path)
    path_var.set(f'Dropped:{raw_path}')
    print(f'dropped path: {dropped_path_container}')

#---------------------------------------------------------------------------------------------------------

## Tkinter Initialize Window W/ Dropped Path Function in Window

def initialize_dnd_window():

    from tkinter import StringVar, Label, Tk
    from pathlib import Path
    from tkinterdnd2 import TkinterDnD, DND_FILES

    dropped_path=[None]

    root = TkinterDnD.Tk()
    root.title('Drop Camera SD Card, or Camera Drive')
    root.geometry('500x500')

    path_var = StringVar()
    label = Label(root, textvariable=path_var, width=50, height=4, bg='lightgray', relief='groove')
    label.pack(pady=40)

    label.drop_target_register(DND_FILES)

    label.dnd_bind('<<Drop>>', lambda event: on_drop(event, path_var, dropped_path))

    root.mainloop()
    return dropped_path[0]


#---------------------------------------------------------------------------------------------------------


## SEARCH FOR DIRECTORY WITH VIDEO FILES

def find_video_dirs_from_path(root_path, extensions=None):

    from pathlib import Path
    
    if extensions is None:
        extensions = ['.mp4', '.mov', '.mkv', '.mts', '.m2ts', '.avi',
    '.wmv', '.mxf', '.braw', '.r3d', '.cine', '.webm']
        
    elif isinstance(extensions, str):
        extensions = [extensions.lower()]
                      
    else:
        extensions = [ext.lower() for ext in extensions]

    root = Path(root_path)
    video_dirs = set()

    for file_path in root.rglob('*'):
        if file_path.suffix.lower() in extensions:
            video_dirs.add(file_path.parent)
    
    return list(video_dirs) if video_dirs else None


#---------------------------------------------------------------------------------------------------------




#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



