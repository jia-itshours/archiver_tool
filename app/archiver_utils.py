#--------------------------------------
##### DATABASE RELATED FUNCTIONS ######
#--------------------------------------

## GET SQL TABLE COLUMNS

def get_sql_table_columns (table_name, db_path):
    from pathlib import Path
    import subprocess
    import sqlite3
    
    ### GET SQL TABLE COLUMNS###
    conn = sqlite3.connect(Path(db_path))
    cursor = conn.cursor()

    cursor.execute(f'PRAGMA table_info({table_name})')
    columns_info = cursor.fetchall()
    table_columns = [col[1] for col in columns_info]

    conn.close()
    return table_columns

#---------------------------------------------------------------------------------------------------------

## CREATE MEDIA INFO DICTIONARY (REQUIRES SQL TABLE OTHERWISE IT WONT WORK)

def media_info_dict (func_file_path, func_table_name, func_db_path):

    from pathlib import Path
    import subprocess

    ### MEDIA INFO FROM SPECIFIC FILE ##


    ##FILE PATHS FOR FILE AND
    file_path = Path(func_file_path)

    db_path = Path(func_db_path)

    #Run MediaInfo using subprocess
    mediainfo_process = subprocess.run(["mediainfo",file_path],capture_output=True, text=True)

    ## PULL HASH VALUE INTO VARIABLE ##
    sha256sum_process = subprocess.run(["sha256sum",file_path],capture_output=True, text=True)

    ### TABLE COLUMNS #####
    table_columns = get_sql_table_columns (table_name=func_table_name, db_path=func_db_path)

    ###### MEDIA INFO DATA CLEAN UP AND DICTIONARY ######

    output = mediainfo_process.stdout
    lines = output.splitlines()

    media_info_dict = {}
    current_section = None

    ## DATA CLEAN UP data categories per line to lowercase and adding '_' isntead of spaces##

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line in ['General', 'Video']:
            current_section = line
            continue

        ## APPENDING EACH LINE ITEM TO KEY: VALUE IN DICTIONARY
        if ':' in line:
            key, value = line.split(':',1)
            formatted_key = key.strip().lower().replace(' ', '_')


        ### Filter for General and specific video lines ###
        if current_section == 'General' or (current_section == 'Video' and formatted_key in ['width', 'height', 'display_aspect_ratio']):

            ## Match with SQL Table columns
            if formatted_key in table_columns:
                if value.endswith('UTC'):
                    value = value[:-4].strip()
                media_info_dict[formatted_key] = value.strip()



    ## SPLITS DATA FROM SHA256SUM_PROCESS INTO 2 VARIABLES ##
    hash_value, file_name = sha256sum_process.stdout.strip().split(maxsplit=1)


    ## ADD hash_value to the dictionary ##
    media_info_dict['hash_value'] = hash_value

    return media_info_dict

#---------------------------------------------------------------------------------------------------------

## PULLING DATA FROM DICTIONARY INTO SQL TABLE
def media_info_to_sql (file_path, table_name, db_path):

    
    
    from pathlib import Path
    import subprocess
    import sqlite3

    func_media_info_dict = media_info_dict (func_file_path=file_path, func_table_name=table_name, func_db_path=db_path)

    conn = sqlite3.connect(Path(db_path))
    cursor = conn.cursor()

    table_name = table_name

    # preparing insert variables
    columns = ', '.join(func_media_info_dict.keys())
    placeholders = ', '.join('?' for _ in func_media_info_dict)
    values = tuple(func_media_info_dict.values())

    # Insert data
    sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
    cursor.execute(sql, values)

    conn.commit()
    conn.close()

    return print(f'updated SQL database {table_name}')

#---------------------------------------------------------------------------------------------------------


## READING MULTIPLE FILES FROM A FOLDER THEN PULLING MEDIA INFO + HASH VALUE FROM EACH THEN ADDING TO SQL TABLE
def folder_files_to_media_info_to_SQL (folder_path, table_name, db_path):

    from pathlib import Path

    folder_path = Path(folder_path)

    video_files = [f for f in folder_path.rglob('*') if f.suffix.lower() in ['.mp4', '.mov', '.mkv', '.mts', '.m2ts', '.avi',
    '.wmv', '.mxf', '.braw', '.r3d', '.cine', '.webm']]

    added_files = []

    for file_path in video_files:
        result = media_info_to_sql(
            file_path=file_path,
            table_name=table_name,
            db_path=db_path
        )
        added_files.append(result)

    return f'{len(added_files)} files added to {table_name}'




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
    
    return list(video_dirs)


#--------------------------------------
##### UI RELATED FUNCTIONS FOR PRESCAN AND ADD TO SQL TABLE ######
#--------------------------------------

def on_drop(event, path_var, dropped_path_container):

    from pathlib import Path

    raw_path = event.data.strip('{}')
    dropped_path_container [0] = Path(raw_path)
    path_var.set(f'Dropped: {raw_path}')
    print(f'Dropped path: {dropped_path_container}')

#---------------------------------------------------------------------------------------------------------

def on_selected_folder(event, folder_listbox, selected_folder_container, path_var):
     
     from pathlib import Path

     selection = folder_listbox.curselection()
     if selection:
          index = selection[0]
          selected = folder_listbox.get(index)
          selected_folder_container[0] =Path(selected)
          path_var.set(f'Selected folder: {selected}')

#---------------------------------------------------------------------------------------------------------

def populate_folder_listbox(root_path, folder_listbox, path_var):
     
     from pathlib import Path
     from tkinter import StringVar, Label, Tk, Button, Listbox, END, SINGLE
     from tkinterdnd2 import TkinterDnD, DND_FILES
     from pathlib import Path
     
     folder_listbox.delete(0, END)
     if root_path is None:
          path_var.set('Please drop a folder or drive first!!')
          return
     
     folders = find_video_dirs_from_path(root_path)
     if not folders:
          path_var.set('No video folders found!!!')
          return
     
     for folder in folders:
          folder_listbox.insert(END, str(folder))
     path_var.set(f'Found {len(folders)} folders, Select one.')



#--------------------------------------
##### TEMPLATE FOLDER SELECTION FUNCTIONS ######
#--------------------------------------


#Opens Folder Selection then Updates path_var then calls populate_template_list and passes the selected directory into "directory argument"
# UI DATA TO BACKEND

def select_template_directory(path_var, populate_template_list_func):
    import os
    import shutil
    from tkinter import filedialog

    selected_dir = filedialog.askdirectory(title = 'Select Template Folder Directory')
    if selected_dir:
        path_var.set(f'Template Directory: {selected_dir}')
        populate_template_list_func(selected_dir)


#---------------------------------------------------------------------------------------------------------


# This functions pulls each item in the selected template folder, then sifts only the folders within the folder, ignoring any potential files
# TAKES BACKEND FOLDERS AND BRINGS THEM TO THE UI

def populate_template_list (directory, template_listbox, folder_path_var):
    import os
    import shutil
    from tkinter import filedialog

    template_listbox.delete(0, 'end')
    folder_path_var.set(directory)

    for item in os.listdir(directory):
        full_path = os.path.join(directory, item)
        if os.path.isdir(full_path):
            template_listbox.insert('end', item)


#---------------------------------------------------------------------------------------------------------


# WORKS WITH THE SELECTION IN THE LISTBOX - UPDATES THE SELECTED VARIABLE AND STATUS VARIABLE, LOOKS UP THE OF THE ITEM SELECTED
# TAKES UI DATA AND BRINGS IT BACK TO THE BACKEND

def on_select_template(event, template_listbox, selected_template_var, status_var):
    import os
    import shutil
    from tkinter import filedialog

    selected_index = template_listbox.curselection()
    if selected_index:
        selected_template_var.set(template_listbox.get(selected_index[0]))
        status_var.set(f'Selected Template: {selected_template_var.get()}')



#---------------------------------------------------------------------------------------------------------

# THIS ONE KINDA WORKS LIKE SELECT TEMPLATE DIRECTORY - IT IS ACTUALLY BORDERLINE IDENTICAL
# UI DATA TO BACKEND

def select_destination_directory(destination_path_var, status_var):
    import os
    import shutil
    from tkinter import filedialog

    selected_dir = filedialog.askdirectory(title= 'Select Destination Directory')
    if selected_dir:
        destination_path_var.set(selected_dir)
        status_var.set(f'Destination Set: {selected_dir}')    


#---------------------------------------------------------------------------------------------------------

# COPIES THE SELECTED TEMPLATE FOLDER TO DESTINATION WITH THE NEW NAME!!


def duplicate_template (folder_path_var, selected_template_var, destination_path_var, new_folder_name_var, status_var):
    import os
    import shutil
    from tkinter import filedialog


    template_dir = folder_path_var.get()
    template_name = selected_template_var.get()
    destination_dir = destination_path_var.get()
    new_name = new_folder_name_var.get()

    if not template_dir or not template_name:
        status_var.set('Please select a template first')
        return
    if not destination_dir:
        status_var.set('Please Select a destination folder')
        return
    if not new_name:
        status_var.set('please enter a new name')
        return
    
    src = os.path.join(template_dir, template_name)
    dst = os.path.join(destination_dir, new_name)

    try:
        shutil.copytree(src,dst)
        status_var.set('Template duplicated to: {dst}')
    except Exception as e:
        status_var.set('Error Duplicating: {e}')


#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------