"""
This is a gui that is intended to make it easy to plot csv data printed
to the Arduino serial monitor.  Users should be able to paste data into 
the text box and get a plot fairly easily.
"""

############################################
#
# Next Steps:
#
# ----------------
#

#############################################

#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii
#
"""This gui is intended to automate various aspects of the process for grading
files downloaded from blackboard"""
# Issues:
#
#
# Resovled:
#  
#iiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiii

import tkinter
import tkinter as tk
from tkinter import ttk

#from matplotlib.backends.backend_tkagg import (
#    FigureCanvasTkAgg, NavigationToolbar2Tk)
# Implement the default Matplotlib key bindings.

from tkinter import ttk
from tkinter.messagebox import showinfo

import pandas as pd
from pandastable import Table, TableModel

import gmail_smtp

# stuff to fix before pusing to pypi:
# - txt_mixin and rwkos are in krauss_misc
# - this is a different tkinter_utils from pybd_gui
#     - could I put this tkinter_utils in krauss_misc?
#     - do I merge the tkinter_utils versions into one file in krauss_misc?
# - serial_utils is a dependency
#     - so is pyserial

from krauss_misc import tkinter_utils, rwkos, txt_mixin
import krauss_misc.tkinter_utils as tu
import bb_utils

import os, glob, time, re
#import serial, serial_utils

pad_options = {'padx': 5, 'pady': 5}

def clean_notes(notes_in):
    notes_out = notes_in.strip()
    bad_strs = ['\n','\r','\t']
    for item in bad_strs:
        notes_out = notes_out.replace(item, ' ')
    
    # put it in quotes
    if len(notes_out) > 0 and (notes_out[0] not in ['"', "'"]):
        notes_out = '"%s"' % notes_out

    return notes_out


class grading_gui(tk.Tk, tkinter_utils.abstract_window):
    def __init__(self):
        super().__init__()
        self.option_add('*tearOff', False)
        #self.geometry("900x600")
        self.mylabel = 'Tkinter Grading GUI'
        self.title(self.mylabel)
        self.resizable(1, 1)

        self.delim = ","
        # configure the grid
        self.columnconfigure(0, weight=4)
        self.columnconfigure(1, weight=1)
        #self.rowconfigure(4, weight=2)
        self.rowconfigure(3, weight=4)        

        self.options = {'padx': 5, 'pady': 5}

        self.menubar = tk.Menu(self)
        self['menu'] = self.menubar
        self.menu_file = tk.Menu(self.menubar)
        self.menu_grading = tk.Menu(self.menubar)        
        ## self.menu_codegen = tk.Menu(self.menubar)        
        self.menubar.add_cascade(menu=self.menu_file, label='File')
        self.menubar.add_cascade(menu=self.menu_grading, label='Grading')        
        ## self.menubar.add_cascade(menu=self.menu_codegen, label='Code Generation')        
        ## self.menu_file.add_command(label='Save', command=self.on_save_menu)
        ## self.menu_file.add_command(label='Load', command=self.on_load_menu)        
        ## #menu_file.add_command(label='Open...', command=openFile)
        self.menu_file.add_command(label='Save CSV', command=self.save_csv)
        self.menu_file.add_command(label='Quit', command=self._quit)

        self.menu_grading.add_command(label="Fresh Start", command=self.fresh_start)
        self.menu_grading.add_command(label='BB Rename', command=self.bb_rename)
        self.menu_grading.add_command(label='Create Grading CSV', \
                command=self.create_grading_csv)
        self.menu_grading.add_command(label='Find Files for Username', \
                command=self.find_files_for_username)
        self.menu_grading.add_command(label='Open Files for Username', \
                command=self.open_files_for_student)
        self.menu_grading.add_command(label='Assign Grades to Student', \
                command=self.assign_grades_to_student)
        self.menu_grading.add_command(label='Increment Student', \
                command=self.increment_student)
        self.menu_grading.add_command(label='Email Feedback', \
                command=self.email_feedback)


        
         


        # need a set baudrate menu item
                                         ## self.menu_codegen.add_command(label='Set Arduino Template File', command=self.set_arduino_template)
        ## self.menu_codegen.add_command(label='Get Arduino Template File', command=self.get_arduino_template)
        ## self.menu_codegen.add_command(label='Set Arduino Output Path', \
        ##                               command=self.set_arduino_output_folder)
        ## self.menu_codegen.add_command(label='Generate Arduino Code', command=self.arduino_codegen)                

        #self.bind("<Key>", self.key_pressed)
        self.bind('<Control-q>', self._quit)
        self.bind('<Command-q>', self._quit)
        ## self.bind('<Control-s>', self.on_save_menu)
        self.bind("<Control-f>", self.fake_test)
        self.bind('<Control-i>', self.increment_student)
        self.bind('<Control-h>', self.grade_100)
        self.bind('<Control-z>', self.grade_0)
        self.bind('<Control-s>', self.save_csv)
        self.bind('<Control-f>', self.fresh_start)
        self.bind('<Control-o>', self.open_files_for_student)
        self.bind('<Control-e>', self.email_feedback)
        self.bind('<Control-a>', self.assign_grades_to_student)

        ## self.bind('<Control-a>', self.add_block)
        ## self.bind('<Control-P>', self.on_place_btn)
        ## self.bind('<Alt-p>', self.on_place_btn)
        ## self.bind('<Control-d>', self.on_draw_btn)
        
        # configure the root window
        self.make_widgets()
        self.table.bind("<Button-1>",self.handle_left_click)
        self.get_folder()
        self.set_bb_rename_text()
        self.guess_things()
        self.find_label()
        #self.load_csv()


    def fresh_start(self, *args):
        print("in fresh_start")
        self.bb_rename()
        self.create_grading_csv()
        self.find_files_for_username()
        self.open_files_for_student()


    def grade_100(self, *args):
        print("in grade_100")
        self.grade_box_var.set("100")
        self.increment_student()


    def grade_0(self, *args):
        print("in grade_0")
        self.grade_box_var.set("0")
        self.increment_student()



    def check_notebooks_for_feedback_user(self, user):
        nb_files = bb_utils.find_notebooks_for_username(user)
        fb_files = []
        for path in nb_files:
            #print("path: %s" % path)
            myfile = txt_mixin.txt_file_with_list(path)
            # search for "# Feedback" or "# feedback"
            list1 = myfile.findall("# Feedback")
            list2 = myfile.findall("# feedback")
            total_list = list1 + list2
            if len(total_list) > 0:
                fb_files.append(path)
        return fb_files



    def get_thing_for_email(self):
        myvar = self.assign_type_var.get()
        assign_num = self.assign_num_var.get()
        self.thing = "%s %s" % (myvar, assign_num)
        print("thing: %s" % self.thing)


        
        
    def email_feedback(self, event=None):
        self.get_thing_for_email()
        title = "Email Subject Check"
        subject = "Feedback on %s" % self.thing
        message = "The email subject will be: %s.  Is this correct?" % subject
        out = tkinter.messagebox.askquestion

        print("tkinter message out = %s" % out)
        self.save_csv()
        # force a reload?

        # - increment over students
        # - check for feedback column not empty
        # - check for "# [Ff]eedback" in notebooks
        # - unless grade == 100, assert feedback of some kind
        for user in self.usernames:
            has_feedback = False
            #print("user: %s" % user)
            row_ind = self.get_row_index(user)
            grade = self.df.iat[row_ind, -2]
            notes = self.df.iat[row_ind, -1]
            #print("grade: %s, notes: %s" % (grade, notes))
            if pd.isna(notes):
                #print("empty notes")
                notes = None
            else:
                notes = str(notes)
                has_feedback = True
            
            fb_files = self.check_notebooks_for_feedback_user(user)
            if len(fb_files) > 0:
                has_feedback = True
                #print("have feedback in notebook(s):")
                for item in fb_files:
                    print(item)
            if pd.isna(grade):
                grade = 0
            else:
                grade = float(grade)

            if grade < 100 and not has_feedback:
                print("no feedback with < 100: %s" % user)


            if has_feedback:
                email = "%s@mail.gvsu.edu" % user
               
                if notes is not None:
                    body = "Grading Notes:\n%s\n" % notes
                else:
                    body = ""

                if len(fb_files) > 0:
                    if len(fb_files) > 1:
                        msg = "The attached notebook files contain some feedback for you."
                    else:
                        msg = "The attached notebook file contains some feedback for you."
                    body += msg


                print("body:\n%s" % body)

                gmail_smtp.send_mail_gmail([email], subject, body, \
                        attachmentFilePaths=fb_files)

            print("="*20)


    def load_grades_for_student(self):
        curuser = self.cur_student_var.get()
        row_ind = self.get_row_index(curuser)
        grade = self.df.iat[row_ind, -2]
        notes = self.df.iat[row_ind, -1]
        self.clear_grades()
        if not pd.isna(grade):
            self.grade_box_var.set(grade)
        if not pd.isna(notes):
            tkinter_utils.replace_text(self.notes_box, notes)


    def set_student_by_index(self, index):
        curuser = self.usernames[index]
        self.cur_student_var.set(curuser)
        self.load_grades_for_student()
        self.table.setSelectedRow(index)



    def handle_left_click(self, event):   
        rowclicked = self.table.get_row_clicked(event)
        print("RowClicked", rowclicked)
        #set user based on rowclicked index
        self.set_student_by_index(rowclicked)

    

    def load_csv(self):
        if self.csvname and os.path.exists(self.csvname):
            # need function to load it and set usernames and load it as a df
            self.table.importCSV(self.csvname)
            self.df = pd.read_csv(self.csvname)
            self.usernames = list(self.df['Username'])
            self.read_username()
            self.load_grades_for_student()
            


    def find_files_for_username(self):
        curuser = self.cur_student_var.get()
        print("curuser: %s" % curuser)
        self.curfiles = bb_utils.find_files_for_username(curuser)
        N = len(self.curfiles)
        self.log("files found: %i" % N)
        self.log(self.curfiles)


    def open_files_for_student(self,*args):
        bb_utils.open_files_for_student(self.curfiles)


    def find_and_open_files_for_username(self):
        self.find_files_for_username()
        self.open_files_for_student()


    def get_row_index(self, userid):
        ind = self.usernames.index(userid)
        return ind


    def save_csv(self,*args):
        print("saving to csv")
        self.df.to_csv(self.csvname,index=0)



    def assign_grades_to_student(self):
        #self.focus_next_window()
        self.grade_box_entry.event_generate("<Tab>")

        grade = self.grade_box_var.get()
        grade = grade.strip()
        notes = self.notes_box.get("1.0",tk.END)
        # need to clean and strip notes here
        notes = clean_notes(notes)
        userid = self.cur_student_var.get()
        row_ind = self.get_row_index(userid)
        if grade:
            self.df.iat[row_ind, -2] = grade
        if notes:
            self.df.iat[row_ind, -1] = notes
        self.table.model.df = self.df
        #pt.show()
        self.table.redraw()


    def clear_grades(self):
        self.grade_box_var.set("")
        self.notes_box.delete("1.0","end")



    def increment_username(self):
        curuser = self.cur_student_var.get()
        bb_utils.write_prev_student(curuser)
        nextuser = bb_utils.get_next_student_id(self.usernames)
        self.cur_student_var.set(nextuser)


    def fake_test(self, *args):
        print("in fake_test")

    def increment_student(self, *args):
        # - submit grade and notes if not done
        # - clear grade and notes boxes
        # - get new id
        # - open new files
        print("in increment_student")
        self.assign_grades_to_student()
        self.save_csv()
        self.clear_grades()
        self.clear_log()
        self.increment_username()
        self.find_and_open_files_for_username()
       

    def log(self, lines):
        if isinstance(lines, str):
            mystr = lines
        else:
            mystr = '\n'.join(lines)
        self.log_box.insert(tk.END,"\n"+mystr)


    def clear_log(self):
        self.log_box.delete("1.0","end")


    def read_username(self):
        curuser = bb_utils.read_student_id()
        if not curuser:
            curuser = self.usernames[0]
        
        self.cur_student_var.set(curuser)



    def find_label(self):
        self.csv_files = bb_utils.find_csv_bb_files_walking_up(self.dir)
        print("csv files found:")
        for item in self.csv_files:
            print(item)
        if self.regexp_str:
            self.col_label = \
                    bb_utils.find_csv_label_in_list_of_files(\
                            self.regexp_str, \
                            self.csv_files)
            self.col_label_var.set(self.col_label)



    def get_folder(self):
        self.dir = os.getcwd()
        print("self.dir = %s" % self.dir)
        rest, self.folder = os.path.split(self.dir)
        print("self.folder = %s" % self.folder)
        self.csvname = self.folder + '_grades.csv'
        tu.replace_text(self.csvname_box, self.csvname)


    def set_bb_rename_text(self):
        self.bbrename_var.set(self.folder+'_') 

       
    def key_pressed(self, event):
        print("pressed:")
        print(repr(event.char))


    def _quit(self, *args, **kwargs):
        print("in _quit")
        #self.save_params()
        self.quit()     # stops mainloop
        self.destroy()  # this is necessary on Windows to prevent
                        # Fatal Python Error: PyEval_RestoreThread: NULL tstate


    def bb_rename(self, *args, **kwargs):
        mystr = self.bbrename_var.get()
        cmd = "bb_rename.py %s" % mystr
        print(cmd)
        os.system(cmd)


    def create_grading_csv(self, *args, **kwargs):
        mylabel = self.col_label_var.get()
        bb_file = self.csv_files[0]
        bb_utils.create_grading_csv(self.csvname, \
                mylabel, bb_file)
        self.load_csv()#<-- not sure if this will cause problems 
                       #    and should just be a separate menu thing


    def guess_things(self):
        # what do I need to guess?
        # - assignment type
        # - assignment #
        # - csv name
        self.assign_num = bb_utils.get_assign_number(self.folder)
        self.assign_num_var.set(str(self.assign_num))
        self.assign_type_str = bb_utils.get_assign_type(self.folder)
        if self.assign_type_str in bb_utils.label_regexp_base_pats_dict:
            self.regexp_str = \
                bb_utils.label_regexp_base_pats_dict[self.assign_type_str] + \
                    str(self.assign_num)
            self.regexp_var.set(self.regexp_str)    
        else:
            self.regexp_str = None

    def focus_next_window(self, event):
        event.widget.tk_focusNext().focus()
        return("break")



    def make_widgets(self):
        # don't assume that self.parent is a root window.
        # instead, call `winfo_toplevel to get the root window
        #self.winfo_toplevel().title("Simple Prog")
        #self.wm_title("Python Block Diagram GUI")        


        # column 0
        mycol = 0
        self.make_label_and_grid_sw("Assignment Type", 0, 0)
        self.make_combo_and_var_grid_nw("assign_type",1,0)
        self.assign_type_keys = list(bb_utils.folder_to_assignment_dict.keys())
        self.assign_type_combobox['values'] = self.assign_type_keys
        self.assign_type_combobox['state'] = 'readonly'
        self.assign_type_combobox.set(self.assign_type_keys[0])
        myvar = self.assign_type_var.get()
        print("myvar = %s" % myvar)
        self.make_label_and_grid_sw("Assignment Number", 2, mycol)
        self.make_entry_and_var_grid_nw("assign_num", 3, mycol)
        self.make_label_and_grid_sw("BB Rename Base", 4, mycol)
        self.make_entry_and_var_grid_nw('bbrename', \
                                        5, mycol)

        myrow = 6
        self.csvname_var = tk.StringVar()
        self.make_label_and_grid_sw("CSV Name", myrow, mycol)
        self.csvname_box = self.make_text_box_and_grid_nw(myrow+1, \
                              mycol, 30,1)

        myrow = 8
        self.make_label_and_grid_sw("Label Regexp Pat", myrow, mycol)
        self.make_entry_and_var_grid_nw('regexp', myrow+1, mycol)

        myrow = 10
        self.make_label_and_grid_sw("Label Found", myrow, mycol)
        self.make_entry_and_var_grid_nw("col_label", myrow+1, mycol)
        self.col_label_entry.width = 100

        myrow = 12
        self.make_label_and_grid_sw("Current Student", myrow, mycol)
        self.make_entry_and_var_grid_nw("cur_student", myrow+1, mycol)

        myrow = 14
        self.make_label_and_grid_sw("Grade", myrow, mycol)
        self.make_entry_and_var_grid_nw("grade_box", myrow+1, mycol)

        self.grade_box_entry.bind("<Tab>", self.focus_next_window)


        myrow = 16
        self.make_label_and_grid_sw("Notes", myrow, mycol)
        self.notes_box = self.make_text_box_and_grid_nw(myrow+1, \
                              mycol, 50,4)

        myrow = 18
        self.make_label_and_grid_sw("Log", myrow, mycol)
        self.log_box = self.make_text_box_and_grid_nw(myrow+1, \
                              mycol, 50,4)

        frame = tk.Frame(self)
        frame.grid(row=0, column=1, sticky='NW', \
                pady=(5,1), padx=10, rowspan=20)


        self.table = Table(frame, showtoolbar=True, showstatusbar=True)
        #self.table.importCSV(filepath)
        self.table.show()

        self.columnconfigure(1, weight=2)


        ## receive_text doesn't fit well with my graph

        # - side by side or notebook?
        # - make sure the force read button is always visible


        ## self.button_frame1 = ttk.Frame(self)
        ## self.quit_button = ttk.Button(self.button_frame1, text="Quit", command=self._quit)
        ## self.quit_button.grid(column=0, row=0, **self.options)

        ## self.draw_button = ttk.Button(self.button_frame1, text="Draw", command=self.on_draw_btn)
        ## self.draw_button.grid(column=1, row=0, **self.options)

        ## self.xlim_label = ttk.Label(self.button_frame1, text="xlim:")
        ## self.xlim.grid(row=0,column=2,sticky='E')
        ## self.xlim_var = tk.StringVar()
        ## self.xlim_box = ttk.Entry(self.button_frame1, textvariable=self.xlim_var)
        ## self.xlim_box.grid(column=3, row=0, sticky="W", padx=(0,5))


       
        
if __name__ == "__main__":
    app = grading_gui()
    app.mainloop()
