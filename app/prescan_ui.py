import tkinter as tk
from tkinter import (
     StringVar,
     BooleanVar, 
     Label, 
     Tk, 
     Button,
     Entry, 
     Listbox, 
     filedialog, 
     END, 
     SINGLE)
from tkinterdnd2 import TkinterDnD, DND_FILES
from pathlib import Path

from archiver_utils import (
    folder_files_to_media_info_to_SQL,
    on_drop,
    on_selected_folder,
    populate_folder_listbox,
    toggle_custom_name,
    toggle_name_root_folder,
    clear_placeholder,
    restore_placeholder,
    on_enter,
    start_archival,
    copy_file_check
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
      folder_listbox = Listbox(root, selectmode=SINGLE, width=50, height=10)
      folder_listbox.pack(pady=10)
      folder_listbox.bind('<<ListboxSelect>>', lambda event: on_selected_folder(event, folder_listbox, selected_folder, path_var))


      #FIND FOLDERS BUTTON IN UI
      find_folders_button = Button(root, text= 'Find Folders', command=lambda: populate_folder_listbox(dropped_path[0], folder_listbox, path_var))
      find_folders_button.pack(pady=10)

      #PROCESS FILES BUTTON IN UI
      process_button = Button(root, text= 'Process Files', command=lambda: folder_files_to_media_info_to_SQL (folder_path=selected_folder[0], table_name='preupload_scan', db_path = '/home/jia/Desktop/archiver_tool/database/archiver_database.db'))
      process_button.pack(pady=10)

      


      ###---------------------------------------------------------------------

      # TYPE ENTRY BOX AND CHECKBOX VARIABLES
      single_camera_enabled = BooleanVar()
      custom_name_enabled = BooleanVar()
      name_root_folder_enabled = BooleanVar()
      name_var = StringVar()
      placeholder_text = 'Type Name And Press Enter'


      # CHECK BOX FOR SINGLE CAM MODE

      single_camera_cb = tk.Checkbutton(root, text='Single Camera Mode', variable=single_camera_enabled)
      single_camera_cb.pack(pady=5)

      # CHECK BOX FOR CUSTOM NAME
      custom_name_cb = tk.Checkbutton(root, text='Custom Name', variable= custom_name_enabled,
                                      command=lambda: toggle_custom_name (custom_name_enabled, name_root_folder_enabled, name_entry, name_var, placeholder_text, feedback_label))
      custom_name_cb.pack(pady=(20,5))


      # CHECK BOX FOR ROOT STORAGE FOLDER NAME
      name_root_cb = tk.Checkbutton(root, text='Use Root Folder Name', variable=name_root_folder_enabled,
                                    command=lambda: toggle_name_root_folder (name_root_folder_enabled, custom_name_enabled, name_entry, name_var, feedback_label))
      name_root_cb.pack(pady=5)


      # DEFAULT STATUS FOR DATA ENTRY (DISABLED)
      name_entry = tk.Entry(root,textvariable=name_var, state='disabled', width=30)
      name_entry.pack()

      
      #BEHAVIOR FOR ENTRY, THE OUTCOME OF THE INPUT VARIABLES IN THE CHECK BOXES AND THE TEXTBOX
      name_entry.bind('<<FocusIn>>', lambda event: clear_placeholder(event, name_var, name_entry, placeholder_text))
      name_entry.bind('<<FocusOut>>', lambda event: restore_placeholder(event, name_var, name_entry, placeholder_text))
      name_entry.bind('<Return>', lambda event: on_enter(event, name_var, feedback_label, placeholder_text))


      #FEEDBACK INFORMATION IN UI
      feedback_label = tk.Label(root, text="", fg='green')
      feedback_label.pack(pady=10)


      ## SELECT FOLDER TO COPY TO

      template_folder = [None]

      select_template_btn = Button(root, text = 'Select Template Folder',
                                   command=lambda: template_folder.__setitem__(0,filedialog.askdirectory()))
      select_template_btn.pack(pady=10)


      
      #ARCHIVE FILES BUTTON IN UI
      process_button = Button(root, text= 'Archive Files', command=lambda: start_archival (template_folder[0], path_var.get(), custom_name_enabled.get(), name_root_folder_enabled.get(),single_camera_enabled.get(), name_var.get()))
      process_button.pack(pady=10)


          ## SELECT FOLDER TO COPY TO

      copied_folder = [None]

      select_copied_btn = Button(root, text = 'Select Copied Folder',
                                   command=lambda: copied_folder.__setitem__(0,filedialog.askdirectory()))
      select_copied_btn.pack(pady=10)
      
      
      corruption_check_button = Button(root, text= 'Corruption Check', command=lambda: copy_file_check (template_folder[0], path_var.get(), custom_name_enabled.get(), name_root_folder_enabled.get(), name_var.get()))
      corruption_check_button.pack(pady=10)

      root.mainloop()

if __name__== "__main__":
    initialize_app_window()







