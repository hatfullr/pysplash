from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
import os
import signal
import subprocess
from lib.threadedtask import ThreadedTask
from widgets.progressbar import ProgressBar
#from widgets.tooltip import ToolTip

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull,'wb')



def download_data_from_server(gui):
    DataFromServer(gui)

class DataFromServer(tk.Toplevel,object):
    def __init__(self,gui):
        # Setup the window
        super(DataFromServer,self).__init__(gui)
        
        self.gui = gui
        
        root = gui.winfo_toplevel()
        self.pad = 5
        aspect = root.winfo_screenheight()/root.winfo_screenwidth()
        self.width = int(root.winfo_screenwidth() / 4)
        height = self.width*aspect

        root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.tmp_path = os.path.join(root_path,"tmp")

        
        
        self.withdraw()

        self.protocol("WM_DELETE_WINDOW",self.close)
        self.resizable(False,False)
        self.title("Get data from server")
        self.configure(width=self.width,height=height)

        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
        self.filelist = []
        self.total_size = 0
        self.filenames = []
        self.server = ""

        self.thread = None

        # Show the window
        self.tk.eval('tk::PlaceWindow '+str(self)+' center')

        self.canceled = False
        self.subprocess = None
        
        self.grab_set()

    def create_variables(self,*args,**kwargs):
        # Gather the preferences
        preference = self.gui.get_preference("getdatafromserver") 
        if preference is None:
            preference = {'username':'','address':'','path':''}
        
        # Create variables
        self.username = tk.StringVar(value=preference['username'])
        self.address = tk.StringVar(value=preference['address'])
        self.path = tk.StringVar(value=preference['path'])

        self.command_choice = tk.StringVar(value='scp')
        self.command_options = tk.StringVar(value='-Cp')
        
    def create_widgets(self,*args,**kwargs):
        # Create widgets
        self.description = ttk.Label(
            self,
            text="You must first ensure that you can ssh to the specified server without a password prompt. You can either specify a path to a single file, such as '/home/myuser/data0.dat' or to a pattern of files, such as '/home/myuser/data*.dat'.",
            wraplength=self.width-2*self.pad,
            justify='left',
        )
        self.server_info_frame = tk.Frame(self)

        self.server_username_label = tk.Label(
            self.server_info_frame,
            text="Username:",
        )
        self.server_username_entry = tk.Entry(
            self.server_info_frame,
            width=30,
            textvariable=self.username,
        )

        self.server_address_label = tk.Label(
            self.server_info_frame,
            text="Server address:",
        )
        self.server_address_entry = tk.Entry(
            self.server_info_frame,
            width=30,
            textvariable=self.address,
        )

        self.filepath_label = tk.Label(
            self.server_info_frame,
            text="Remote file path:",
        )
        self.filepath_entry = tk.Entry(
            self.server_info_frame,
            width=30,
            textvariable=self.path,
        )



        
        self.command_choice_label = tk.Label(
            self.server_info_frame,
            text='Command:',
        )
        self.command_choice_frame = tk.Frame(self.server_info_frame)
        
        self.scp_button = tk.Radiobutton(
            self.command_choice_frame,
            text="scp",
            value="scp",
            variable=self.command_choice,
            command=self.on_scp_button_pressed,
        )
        self.rsync_button = tk.Radiobutton(
            self.command_choice_frame,
            text="rsync",
            value="rsync",
            variable=self.command_choice,
            command=self.on_rsync_button_pressed,
        )

        self.command_options_label = tk.Label(
            self.server_info_frame,
            text="Options:",
        )
        self.command_options_entry = tk.Entry(
            self.server_info_frame,
            textvariable=self.command_options,
        )

        

        self.progressbar = ProgressBar(
            self,
            orient='horizontal',
            maximum=100,
            mode='determinate'
        )


        self.buttons_frame = tk.Frame(self)
        self.download_button = tk.Button(
            self.buttons_frame,
            text="Download",
            width=len("Download"),
            command=self.download_pressed,
        )
        self.close_button = tk.Button(
            self.buttons_frame,
            text="Close",
            command=self.close_soft,
        )

    
    def place_widgets(self,*args,**kwargs):
        # Place widgets
        self.description.pack(side='top',fill='x',padx=self.pad,pady=(self.pad,0))
    
        self.server_username_label.grid(row=0,column=0,sticky='nes')
        self.server_username_entry.grid(row=0,column=1,sticky='news')
        self.server_address_label.grid(row=1,column=0,sticky='nes')
        self.server_address_entry.grid(row=1,column=1,sticky='news')
        self.filepath_label.grid(row=2,column=0,sticky='nes')
        self.filepath_entry.grid(row=2,column=1,sticky='news')

        self.command_choice_label.grid(row=3,column=0,sticky='nes')
        self.rsync_button.pack(side='right',fill='both',expand=True)
        self.scp_button.pack(side='right',fill='both',expand=True)
        self.command_choice_frame.grid(row=3,column=1,sticky='nws')

        self.command_options_label.grid(row=4,column=0,sticky='nes')
        self.command_options_entry.grid(row=4,column=1,sticky='nws')
        
        self.server_info_frame.columnconfigure(1,weight=1)
        self.server_info_frame.pack(side='top',padx=self.pad,pady=(0,self.pad))
        
        self.progressbar.pack(side='left',fill='x',expand=True,padx=(self.pad,0),pady=0)
        self.download_button.pack(side='right')
        self.close_button.pack(side='right')
        self.buttons_frame.pack(side='right', fill='y', pady=(0,self.pad),padx=self.pad)

    def close(self,*args,**kwargs):
        self.grab_release()
        self.destroy()
        
    def close_soft(self,*args,**kwargs):
        self.grab_release()
        self.cancel()
        self.destroy()
        
    def cancel(self,*args,**kwargs):
        self.canceled = True

        self.download_button.configure(relief='raised',text='Download',command=self.download_pressed)
        self.progressbar.set_text("Download canceled")
        self.progressbar.configure(value=0)
        self.enable_widgets()
        
        if self.thread is not None: self.thread.stop()
        if self.subprocess is not None:
            try:
                os.killpg(os.getpgid(self.subprocess.pid), signal.SIGTERM)
            except OSError:
                pass
        
        

    def on_scp_button_pressed(self,*args,**kwargs):
        self.command_options.set("-Cp")
        
    def on_rsync_button_pressed(self,*args,**kwargs):
        self.command_options.set("-a")

    def set_widget_states(self,state):
        for child in self.server_info_frame.winfo_children():
            if hasattr(child,"configure") and 'state' in child.configure():
                child.configure(state=state)
        
    def disable_widgets(self,*args,**kwargs):
        self.set_widget_states('disabled')
        # Don't know why, but the radio buttons don't behave normally
        self.rsync_button.configure(state='disabled')
        self.scp_button.configure(state='disabled')
    def enable_widgets(self,*args,**kwargs):
        self.set_widget_states('normal')
        # Don't know why, but the radio buttons don't behave normally
        self.rsync_button.configure(state='normal')
        self.scp_button.configure(state='normal')

    def download_pressed(self,*args,**kwargs):
        # Save the entries in the gui preferences so they pop up
        # automatically the next time we want to use them
        self.gui.set_preference(
            "getdatafromserver",
            {
                'username' : self.username.get(),
                'address' : self.address.get(),
                'path' : self.path.get(),
            },
        )

        self.disable_widgets()
        
        # Reset the progressbar
        self.progressbar.configure(value=0)

        # Get the server
        self.server = self.username.get()+"@"+self.address.get()
        
        # Get the file list
        self.thread = ThreadedTask(
            self,
            target=self.get_file_list,
        )

        self.canceled = False
        self.download_button.configure(relief='sunken',text="Cancel",command=self.cancel)
        
        # Block until the task has finished
        while self.thread.isAlive():
            self.update()

        if not self.canceled:
            # After getting the file list, start downloading the files
            self.progressbar.set_text("Starting download...")
            self.thread = ThreadedTask(
                self,
                target=self.download_files,
            )

            # Wait until the thread had finished
            while self.thread.isAlive():
                self.download_update()

            if not self.canceled:
                # When the thread has finished, return things to normal
                #self.download_button.configure(relief='raised',state='normal',text='Download')
                #self.progressbar.set_text("Download complete")
                #self.update()

                # Now add the downloaded files to the gui file list
                self.gui.update_filenames()

                self.gui.plotcontrols.current_file.set(self.gui.filenames[0])

                self.close()
                return

        self.subprocess = None
        self.enable_widgets()
        self.progressbar.configure(value=0)

    def download_files(self,*args,**kwargs):
        cmd = self.command_choice.get()+" "+self.command_options.get()+" "+self.server+":"+self.path.get()+" "+self.tmp_path
        self.subprocess = subprocess.Popen(
            cmd.split(" "),
            stdout=DEVNULL,
            stderr=subprocess.STDOUT,
            preexec_fn=os.setsid,
        )
        self.subprocess.communicate()
                
    def get_file_list(self,*args,**kwargs):
        # Get the list of files that will be downloaded
        self.progressbar.set_text("Retrieving file list...")
        self.subprocess = subprocess.Popen([
            "ssh",
            self.server,
            "stat -c '%s %n'",
            self.path.get(),
        ],stdout=subprocess.PIPE,stderr=DEVNULL,preexec_fn=os.setsid)

        stdout, stderr = self.subprocess.communicate()
        if not self.canceled:
            stdout = stdout.decode('ascii').strip().split("\n")
            self.filelist = [o.split(" ") for o in stdout]
            self.filenames = [f[1] for f in self.filelist]
            self.total_size = sum([int(f[0].strip("'")) for f in self.filelist])

    def download_update(self,*args,**kwargs):
        filebasenames = [os.path.basename(filename) for filename in self.filenames]

        filesintmp = os.listdir(self.tmp_path)

        tmpfilenames = []
        for filename in filebasenames:
            for tmpfilename in filesintmp:
                if filename in tmpfilename:
                    tmpfilenames.append(os.path.join(self.tmp_path,tmpfilename))
                

        if tmpfilenames:
            cmd = "stat -c '%s' "+" ".join(tmpfilenames)
            result = None
            try:
                result = subprocess.check_output(
                    cmd.split(" "),
                    stderr=DEVNULL,
                ).decode('ascii').strip().split("\n")
            except subprocess.CalledProcessError:
                # This probably only happens when we search for a file that isn't there
                # (namely when rsync renames its temporary files to the expected filenames)
                pass

            if result is not None:
                for i in range(len(result)):
                    result[i] = float(result[i].strip("'"))
            
                progress = sum(result)
                current = progress/float(self.total_size) * 100
                self.progressbar.configure(value=current)
                self.progressbar.set_text("Downloading... (%3.2f%%)" % current)
            
        self.update()
        
        
        
    

    

        
    
    
    




    

    
