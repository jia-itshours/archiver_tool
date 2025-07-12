from tkinter import (
    Tk,
    Label,
    Button,
    Listbox,
    StringVar,
    Entry,
    SINGLE
)

from archiver_utils import(
    select_template_directory,
    populate_template_list,
    on_select_template,
    select_destination_directory,
    duplicate_template
)


### UI SETUP ###

root = Tk()
root.title('Template Folder Selector')
root.geometry('600x500')

#Variables

folder_path = StringVar()
selected_template = StringVar()
path_var = StringVar()
status_var = StringVar()
destination_path = StringVar()
new_folder_name = StringVar()



# UI Elements

Label(root, textvariable=path_var).pack(pady=10)

template_listbox = Listbox(root, selectmode=SINGLE, width=50, height=10)
template_listbox.pack(pady=10)

Button(root, text='Select Template Directory',
       command=lambda:select_template_directory(path_var,
                                                lambda dir: populate_template_list(dir, template_listbox, folder_path))).pack(pady=5)

template_listbox.bind('<<ListboxSelect>>', lambda event: on_select_template(event, template_listbox, selected_template, status_var))


Label(root, text='Enter New Folder Name').pack()
Entry(root, textvariable=new_folder_name, width=40).pack(pady=5)

Button(root, text='Select Destination Directory',
       command=lambda: duplicate_template(folder_path, selected_template, destination_path, new_folder_name, status_var)).pack(pady=10)

Label(root, textvariable=status_var).pack(pady=10)


# RUN

root.mainloop()
