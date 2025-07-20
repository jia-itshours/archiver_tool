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

def sql_table_all_hash_values_to_list(table_name, db_path):


    import sqlite3

    conn = sqlite3.connect(f'{db_path}')
    cursor = conn.cursor()


    cursor.execute(f'SELECT hash_value FROM {table_name}')
    hash_list = [row[0] for row in cursor.fetchall()]

    for row in rows:
        print(row)

    conn.close()

    return hash_list


#---------------------------------------------------------------------------------------------------------




## This is to call the correct ffmpeg version in relation to the OS

def platform_check_ffmpeg():

    import platform
    import os
    base = '/home/jia/Desktop/archiver_tool/ffmpeg'

    system = platform.system().lower()

    ffmpeg_path = {
        'linux':os.path.join(base,'linux','ffmpeg','bin','ffmpeg',),
        'windows':os.path.join(base,'windows', 'ffmpeg','bin','ffmpeg.exe'),
        'darwin':os.path.join(base,'darwin','ffmpeg')
    }.get(system)

    return ffmpeg_path



#---------------------------------------------------------------------------------------------------------


def is_supported(file_path):
    from pathlib import Path
    
    supported_formats= {'.mp4', '.mov', '.mkv', '.mts', '.m2ts', '.avi', '.wmv', '.mxf', '.webm'}

    return Path(file_path).suffix.lower().strip() in supported_formats


#---------------------------------------------------------------------------------------------------------


def ffmpeg_corruption_check(file_path):
    import subprocess
    import os
    from pathlib import Path

    if is_supported(file_path):

        ffmpeg_lib_path = '/home/jia/Desktop/archiver_tool/ffmpeg/linux/ffmpeg/lib'
        env = os.environ.copy()
        env['LD_LIBRARY_PATH'] = ffmpeg_lib_path + ':' + env.get('LD_LIBRARY_PATH', '')


        ffmpeg_path = platform_check_ffmpeg()
        
        

        file_path = Path(file_path)

        result = subprocess.run(
            [ffmpeg_path, '-v', 'error', '-i', str(file_path), '-frames:v', '10', '-f', 'null', '-'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )


        error_lines = [line for line in result.stderr.splitlines() if 'error' in line.lower()]



        if error_lines:
            print("----- FFmpeg STDERR OUTPUT -----")
            print(result.stderr)
            print("----- END OUTPUT -----")
            return 'corrupted' 
        
        else:
            return 'all_good'
    else:
        return 'skipped_unsupported_file_type_for_corruption_check'

#---------------------------------------------------------------------------------------------------------

## CREATE MEDIA INFO DICTIONARY (REQUIRES SQL TABLE OTHERWISE IT WONT WORK)

def media_info_dict (func_file_path, func_table_name, func_db_path, seen_hashes):

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
    ## SPLITS DATA FROM SHA256SUM_PROCESS INTO 2 VARIABLES ##
    hash_value, file_name = sha256sum_process.stdout.strip().split(maxsplit=1)



    ## CORRUPTION CHECK INTO VARIABLE ##
    corruption_status = ffmpeg_corruption_check(file_path)

    ### TABLE COLUMNS PREUPLOAD #####
    table_columns = get_sql_table_columns (table_name=func_table_name, db_path=func_db_path)

    good_media_info_dict = {}
    corrupt_media_info_dict = {}



    ## ADD CORRUPTION STATUS TO DICTIONARY ##
    if corruption_status == 'corrupted' or hash_value in seen_hashes:

        output = mediainfo_process.stdout
        lines = output.splitlines()

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
                    corrupt_media_info_dict[formatted_key] = value.strip()


            ## ADD hash_value to the dictionary ##
        corrupt_media_info_dict['hash_value'] = hash_value
        
        ## CORRUPTION STATUS
        if hash_value in seen_hashes:
            corrupt_media_info_dict['status'] = 'duplicate'
        else:
            corrupt_media_info_dict['status'] = 'corrupted'            


        return None, corrupt_media_info_dict

    
    else:
        ###### MEDIA INFO DATA CLEAN UP AND DICTIONARY ######

        output = mediainfo_process.stdout
        lines = output.splitlines()

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
                    good_media_info_dict[formatted_key] = value.strip()


            ## ADD hash_value to the dictionary ##
        good_media_info_dict['hash_value'] = hash_value
        seen_hashes.append(hash_value)

        return good_media_info_dict, None 
    

#---------------------------------------------------------------------------------------------------------

## PULLING DATA FROM DICTIONARY INTO SQL TABLE
def media_info_to_sql (file_path, table_name, db_path, seen_hashes):

    
    
    from pathlib import Path
    import subprocess
    import sqlite3

    good_media_info_dict, corrupt_media_info_dict = media_info_dict (func_file_path=file_path, func_table_name=table_name, func_db_path=db_path, seen_hashes=seen_hashes)

    if good_media_info_dict:
        conn = sqlite3.connect(Path(db_path))
        cursor = conn.cursor()

        table_name = table_name

        # preparing insert variables
        columns = ', '.join(good_media_info_dict.keys())
        placeholders = ', '.join('?' for _ in good_media_info_dict)
        values = tuple(good_media_info_dict.values())

        # Insert data
        sql = f'INSERT INTO {table_name} ({columns}) VALUES ({placeholders})'
        cursor.execute(sql, values)
    
        conn.commit()
        conn.close()

        return print(f'updated SQL database {table_name}')

    elif corrupt_media_info_dict:
        conn = sqlite3.connect(Path(db_path))
        cursor = conn.cursor()

        table_name = 'corrupted_files'

        # preparing insert variables
        columns = ', '.join(corrupt_media_info_dict.keys())
        placeholders = ', '.join('?' for _ in corrupt_media_info_dict)
        values = tuple(corrupt_media_info_dict.values())

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
    
    seen_hashes=[]



    for file_path in video_files:
        
        result = media_info_to_sql(
            file_path=file_path,
            table_name=table_name,
            db_path=db_path,
            seen_hashes=seen_hashes
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
    
        if any ('trash' in part.lower() for part in file_path.parts):
            continue

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
          path_var.set(selected)

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

#---------------------------------------------------------------------------------------------------------

#### FOR USE WITH THE start_archival Functions below ######
# GATHER STORAGE VOLUME NAME AND REMOVE ALL OTHER PARTS FROM THE FILE PATH


# Windows FIRST

def get_volume_label_windows (drive_letter):
    import platform
    from pathlib import Path
    import ctypes
    
    volume_name_buf = ctypes.create_unicode_buffer(1024)
    rc = ctypes.windll.kernel32.GetVolumeInformation(
        ctypes.c_wchar_p(drive_letter + '\\'),
        volume_name_buf,
        ctypes.sizeof(volume_name_buf),
        None, None, None, None, 0
    )
    return volume_name_buf if rc else None


#---------------------------------------------------------------------------------------------------------

### SAME AS ABOVE EXCEPT FOR UNIX BASED SYSTEMS LIKE MACOS + LINUX

def get_volume_label_unix(path_str):
    import platform
    from pathlib import Path
    import ctypes

    parts = Path(path_str).resolve().parts

    if 'Volumes' in parts:
        idx = parts.index('Volumes')
        return parts[idx + 1] if idx + 1 <len(parts) else None
    elif 'media' in parts:
        idx = parts.index('media')
        return parts[idx + 2] if idx + 2 <len(parts) else None
    
    return None


#---------------------------------------------------------------------------------------------------------



### ACTUAL FUNCTION TO GATHER THE PATH, DETERMINE THE OS, THEN EDIT THE PATH VARIABLE TO JUST BE THE VOLUME NAME



def get_volume_label(source_path):
    import platform
    from pathlib import Path
    import ctypes
    
    system = platform.system()
    
    if system == 'Windows':
        drive = Path(source_path).drive.rstrip('\\')
        return get_volume_label_windows(drive)
    
    elif system in ('Linux', 'Darwin'):
        return get_volume_label_unix(source_path)
    else:
        return None

#---------------------------------------------------------------------------------------------------------


## Gathers the current folder and finds the project folder name for the re-naming function


def get_project_folder_name(copied_folder_path):
    
    from pathlib import Path
    
    parts = copied_folder_path.resolve().parts
    current_folder_name = copied_folder_path.name

    if current_folder_name in parts:
        idx = parts.index(current_folder_name)

        if idx >= 2:
            return parts[idx - 2]
    raise ValueError (f"'{current_folder_name}' not found in path: {copied_folder_path}")

#---------------------------------------------------------------------------------------------------------

#PULL ALLLLL GOOOOOD TO COPY FILES TO A LIST VARIABLE 

def get_good_files_paths(table_name, db_path):
    import sqlite3
    from pathlib import Path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f'''
    SELECT complete_name
    FROM {table_name}
    '''
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return [Path(row[0]) for row in results]

#---------------------------------------------------------------------------------------------------------

## PULL GOOD FILE hash_value

def get_good_files_hash(table_name, db_path):
    import sqlite3
    from pathlib import Path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f'''
    SELECT hash_value
    FROM {table_name}
    WHERE corruption_status = 'all_good' AND copy_status = 'all_good'
    '''
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return [Path(row[0]) for row in results]

#---------------------------------------------------------------------------------------------------------


## PULL GOOD FILE id

def get_good_files_id(table_name, db_path):
    import sqlite3
    from pathlib import Path

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = f'''
    SELECT id
    FROM {table_name}
    WHERE corruption_status = 'all_good' AND copy_status = 'all_good'
    '''
    cursor.execute(query)
    results = cursor.fetchall()
    conn.close()

    return [Path(row[0]) for row in results]

#---------------------------------------------------------------------------------------------------------

## GOOD FILE SQL to DICTIONARY ##

def get_good_files_to_dictionary(table_name, db_path):

    import sqlite3

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute(f'SELECT id, hash_value, complete_name FROM {table_name}')
    rows = cursor.fetchall()

    return {
        row[0]: {
            'hash_value': row[1],
            'complete_name' : row[2],
            'id': row[0]
        }
        for row in rows
    }


#---------------------------------------------------------------------------------------------------------

# COPIES THE VIDEO FOLDER FROM STORAGE DEVICE THAT WAS ADDED TO THE SQL TABLE INTO THE SELECTED TEMPLATE FOLDER
# PULLS THE VOLUME NAME FROM THE SOURCE PATH FROM WINDOWS, MAC, OR LINUX OS
# THEN RENAMES THE COPIED FOLDER TO THE NAME OF THE ORIGINAL ROOT STORAGE DEVICE, IF BOX IS CHECKED, IF NOT THEN WHATEVER IS WRITTEN IN TEXT ENTRY VARIABLE
# THEN RENAMES ALL FILES THE USING THE FOLLOWING NAMING CONVENTION:
# ProjectFolder_CAMERA_#


def start_archival (template_path, source_video_folder, check_box, check_box_2, single_cam_mode, typed_name):
    import shutil
    from pathlib import Path

    good_files = get_good_files_to_dictionary(table_name='preupload_scan', db_path='/home/jia/Desktop/archiver_tool/database/archiver_database.db')


    if single_cam_mode:

        media_extensions = ['.mp4', '.mov', '.mkv', '.mts', '.m2ts', '.avi',
        '.wmv', '.mxf', '.braw', '.r3d', '.cine', '.webm']

        Path(template_path).mkdir(parents=True, exist_ok=True)

        project_name = Path(template_path).parent.name


        if check_box_2:
            camera_name = get_volume_label(source_video_folder)
        elif check_box:
            camera_name = typed_name
        else:
            raise ValueError ('Single-cam mode requires colume or custom name for renaming.')
        
        rename_base = f'{project_name}_{camera_name}'


        for i, (file_id, file_info) in enumerate(sorted(good_files.items()), start=1):
            f= Path(file_info['complete_name'])
            if f.suffix.lower() in media_extensions:
                new_filename = f'{rename_base}_{i}{f.suffix}'
                shutil.copy2(f, Path(template_path) / new_filename)



        folder_files_to_media_info_to_SQL (template_path, table_name='copy_buffer', db_path='/home/jia/Desktop/archiver_tool/database/archiver_database.db')



    
    else:
        # COPIES THE FOLDER TO THE TEMPLATE FOLDER
    
        target_path = Path(str(template_path)) / Path(source_video_folder).name
        target_path.mkdir(parents=True, exist_ok=True)


        #COPY GOOD FILES INTO TARGET FOLDER

        for file_id, file_info in sorted(good_files.items()):
            f= Path(file_info['complete_name'])
            shutil.copy2(f, target_path/ f.name)
        
        # PULLS VOLUME NAME
        
        volume_label = get_volume_label(source_video_folder)

        
        # RENAMES THE COPIED FOLDER TO THE ORIGINAL ROOT IF BOX IS CHECKED


        if check_box_2 and volume_label:
            new_path = target_path.parent / volume_label ##THIS IS GOING TO BE JUST THE VOLUME NAME
            target_path.rename(new_path)
            target_path = new_path
        elif check_box:
            new_path = target_path.parent / typed_name
            target_path.rename(new_path)
            target_path = new_path

        # RENAMES FILES IN THE NEW RE-NAMED FOLDER SEQUENTIALLY USING {template_folder_name}_{copied_folder_name}_{index}
        

        media_extensions = ['.mp4', '.mov', '.mkv', '.mts', '.m2ts', '.avi',
        '.wmv', '.mxf', '.braw', '.r3d', '.cine', '.webm']

        files = sorted(target_path.glob('*'))

        for f in files:
            if f.is_file() and f.suffix.lower() not in media_extensions:
                f.unlink()

        files = sorted(target_path.glob('*'))
        
        
   
        template_folder_name = get_project_folder_name(target_path)
        copied_folder_name = target_path.name

        for i, f in enumerate(files, start=1):
            if f.is_file() and f.suffix.lower() in media_extensions:
                new_filename = f'{template_folder_name}_{copied_folder_name}_{i}{f.suffix}'
                f.rename(f.parent / new_filename)
         
    
        folder_files_to_media_info_to_SQL (target_path, table_name='copy_buffer', db_path='/home/jia/Desktop/archiver_tool/database/archiver_database.db')

    #-------COPIED FILE CHECK-------#

def copy_file_check(template_path, source_video_folder, typed_name):

    ## Make sure all copied files copied, make sure there are no extras/files that escape corruption check
        
    pre_good_files = get_good_files_to_dictionary(table_name='preupload_scan', db_path='/home/jia/Desktop/archiver_tool/database/archiver_database.db')

    copy_good_files = get_good_files_to_dictionary(table_name='copy_buffer', db_path='/home/jia/Desktop/archiver_tool/database/archiver_database.db')

    missing_hashes = pre_good_files['hash_value'] - copy_good_files['hash_value']
    extra_hashes = copy_good_files['hash_value'] - pre_good_files['hash_value']


    if missing_hashes:
        
        for i in missing_hashes:

            media_extensions = ['.mp4', '.mov', '.mkv', '.mts', '.m2ts', '.avi',
            '.wmv', '.mxf', '.braw', '.r3d', '.cine', '.webm']

            Path(template_path).mkdir(parents=True, exist_ok=True)

            project_name = Path(template_path).parent.name


            if check_box_2:
                camera_name = get_volume_label(source_video_folder)
            elif check_box:
                camera_name = typed_name
            else:
                raise ValueError ('Single-cam mode requires colume or custom name for renaming.')
            
            rename_base = f'{project_name}_{camera_name}'

            index = 1 ### POPULATE WITH MISSING INDEX
            for f in sorted(good_files):
                if f.suffix.lower() in media_extensions:
                    new_filename = f'{rename_base}_{index}{f.suffix}'
                    shutil.copy2(f, Path(template_path) / new_filename)
                    index += 1









 
        


    
    

            





    

#---------------------------------------------------------------------------------------------------------

## ALL OF THESE FUNCTIONS CORRESPOND TO THE TEXT BOX FOR THE IF STATEMENT FOR RENAMING COPIED FOLDER 
## THESE ARE MOSTLY JUST VARIABLE ASSIGNMENT FUNCTIONS FOR THE UI VARIABLES


## CHECKBOX FOR TURNING ON CUSTOM NAME

def toggle_custom_name(custom_name_enabled, name_root_folder_enabled, name_entry, name_var, placeholder_text, feedback_label):
    import tkinter as tk
    from tkinter import StringVar, BooleanVar

    if custom_name_enabled.get():
        name_root_folder_enabled.set(False)
        name_entry.config(state='normal', fg='grey')
        name_var.set(placeholder_text)
        feedback_label.config(text='')
    else:
        name_entry.config(state='disabled')
        name_var.set('')
        feedback_label.config(text='')


#---------------------------------------------------------------------------------------------------------


## CHECKBOX FOR TURNING ON ROOT FOLDER NAMING INSTEAD

def toggle_name_root_folder(name_root_folder_enabled, custom_name_enabled, name_entry, name_var, feedback_label):
    import tkinter as tk
    from tkinter import StringVar, BooleanVar
    if name_root_folder_enabled.get():
        custom_name_enabled.set(False)
        name_entry.config(state='disabled')
        name_var.set('')
        feedback_label.config(text='')


#---------------------------------------------------------------------------------------------------------


## FOR CLEARING THE PLACE HOLDER TEXT

def clear_placeholder(event, name_var, name_entry, placeholder_text):
    import tkinter as tk
    from tkinter import StringVar, BooleanVar

    if name_var.get() == placeholder_text:
        name_entry.delete(0, 'end')
        name_entry.config(fg='black')

#---------------------------------------------------------------------------------------------------------


## RESTORING PLACEHOLDER TEXT

def restore_placeholder(event, name_var, name_entry, placeholder_text):
    import tkinter as tk
    from tkinter import StringVar, BooleanVar

    if name_var.get() == '':
        name_entry.insert(0,placeholder_text)
        name_entry.config(fg='grey')

#---------------------------------------------------------------------------------------------------------


## VARIABLE ASSIGNMENTS FOR PRESSING ENTER

def on_enter(event, name_var, feedback_label, placeholder_text):
    import tkinter as tk
    from tkinter import StringVar, BooleanVar

    typed_name = name_var.get()
    if typed_name and typed_name != placeholder_text:
        feedback_label.config(text=f'✅ Assigned name will be: {typed_name}', fg='green')
    else:
        feedback_label.config(text=f'❌ Please enter a valid name', fg='red')

#---------------------------------------------------------------------------------------------------------

#--------------------------------------
##### TEMPLATE FOLDER SELECTION + DUPLICATE FUNCTIONS ######
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
        status_var.set(f'Template duplicated to: {dst}')
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