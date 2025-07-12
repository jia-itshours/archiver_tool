
from tkinter import StringVar, Label, Tk, Button, Listbox, END, SINGLE
from tkinterdnd2 import TkinterDnD, DND_FILES
from pathlib import Path

from archiver_utils import (
    find_video_dirs_from_path,
    get_sql_table_columns,
    media_info_dict,
    media_info_to_sql,
    folder_files_to_media_info_to_SQL,
    on_drop,
    on_selected_folder,
    populate_folder_listbox
)


def initialize_app_window():
      
      dropped_path = [None]
      selected_folder = [None]

      #UI VARIABLES
      root = TkinterDnD.Tk()
      root.title('Archiver Tool')
      root.geometry('600x300')
      
      path_var = StringVar()
      label = Label(root, textvariable=path_var, width=50, height=4, bg='lightgray', relief='groove')
      label.pack(pady=20)
      

      #DND BOX IN UI
      label.drop_target_register(DND_FILES)
      label.dnd_bind('<<Drop>>', lambda event: on_drop(event, path_var, dropped_path))

      #FOLDER LISTBOX IN UI
      folder_listbox = Listbox(root, selectmode=SINGLE, width=80, height=20)
      folder_listbox.pack(pady=10)
      folder_listbox.bind('<<ListboxSelect>>', lambda event: on_selected_folder(event, folder_listbox, selected_folder, path_var))


      #FIND FOLDERS BUTTON IN UI
      find_folders_button = Button(root, text= 'Find Folders', command=lambda: populate_folder_listbox(dropped_path[0], folder_listbox, path_var))
      find_folders_button.pack(pady=10)

      #PROCESS FILES BUTTON IN UI
      process_button = Button(root, text= 'Process Files', command=lambda: folder_files_to_media_info_to_SQL (folder_path=selected_folder[0], table_name='preupload_scan', db_path = '/home/jia/Desktop/archiver_tool/database/archiver_database.db'))
      process_button.pack(pady=10)

      root.mainloop()

if __name__== "__main__":
    initialize_app_window()



#---------------------------------------------------------------------------------------------------------


#---------------------------------------------------------------------------------------------------------




#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



#---------------------------------------------------------------------------------------------------------



