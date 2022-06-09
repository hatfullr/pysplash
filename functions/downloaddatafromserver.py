from sys import version_info
if version_info.major >= 3:
    import tkinter as tk
    from tkinter import ttk
else:
    import Tkinter as tk
    import ttk
from widgets.button import Button
from widgets.entry import Entry
from widgets.popupwindow import PopupWindow
import os
import signal
import subprocess
from lib.threadedtask import ThreadedTask
from widgets.progressbar import ProgressBar
import globals

try:
    from subprocess import DEVNULL
except ImportError:
    DEVNULL = open(os.devnull,'wb')



def download_data_from_server(gui):
    DownloadDataFromServer(gui)

class DownloadDataFromServer(PopupWindow,object):
    default_scp_options = "-Cp"
    default_rsync_options = "-a"
    
    def __init__(self,gui):
        if globals.debug > 1: print("downloaddatafromserver.__init__")
        # Setup the window
        super(DownloadDataFromServer,self).__init__(
            gui,
            title="Download data from server",
            oktext="Download",
            canceltext="Close",
            okcommand=self.download_pressed,
            cancelcommand=self.close_soft,
        )
        
        self.gui = gui
        self.root = self.gui.winfo_toplevel()

        root_path = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        self.tmp_path = os.path.join(root_path,"tmp")
        
        self.create_variables()
        self.create_widgets()
        self.place_widgets()
        
        self.filelist = []
        self.total_size = 0
        self.filenames = []
        self.server = ""

        self.previous_command_choice = self.command_choice.get()
        
        if self.command_choice.get() == 'scp':
            self.previous_scp_options = self.command_options.get()
            self.previous_rsync_options = DownloadDataFromServer.default_rsync_options
        elif self.command_choice.get() == 'rsync':
            self.previous_scp_options = DownloadDataFromServer.default_scp_options
            self.previous_rsync_options = self.command_options.get()

        self.thread = None

        self.canceled = False
        self.subprocess = None
        
    def create_variables(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.create_variables")
        # Gather the preferences
        preference = self.gui.get_preference("downloaddatafromserver")
        if preference is None:
            preference = {'username':'','address':'','path':'','command':'scp','command options':'-Cp'}
            
        # Create variables
        self.username = tk.StringVar(value=preference['username'])
        self.address = tk.StringVar(value=preference['address'])
        self.path = tk.StringVar(value=preference['path'])

        command = preference['command']
        self.command_choice = tk.StringVar(value=command)

        if command == 'scp':
            self.command_options = tk.StringVar(value=preference.get('command options', DownloadDataFromServer.default_scp_options))
        elif command == 'rsync':
            self.command_options = tk.StringVar(value=preference.get('command options', DownloadDataFromServer.default_rsync_options))
        else:
            raise ValueError("Preference 'command' in 'downloaddatafromserver' must be either 'scp' or 'rsync'. Received '"+preference['command']+"'")
        
    def create_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.create_widgets")
        # Create widgets
        self.description = ttk.Label(
            self.contents,
            text="You must first ensure that you can ssh to the specified server without a password prompt. You can either specify a path to a single file, such as '/home/myuser/data0.dat' or to a pattern of files, such as '/home/myuser/data*.dat'.",
            wraplength=self.width-2*self.cget('padx'),
            justify='left',
        )
        self.server_info_frame = tk.Frame(self.contents)

        self.server_username_label = tk.Label(
            self.server_info_frame,
            text="Username:",
        )
        self.server_username_entry = Entry(
            self.server_info_frame,
            textvariable=self.username,
        )

        self.server_address_label = tk.Label(
            self.server_info_frame,
            text="Server address:",
        )
        self.server_address_entry = Entry(
            self.server_info_frame,
            textvariable=self.address,
        )

        self.filepath_label = tk.Label(
            self.server_info_frame,
            text="Remote file path:",
        )
        self.filepath_entry = Entry(
            self.server_info_frame,
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
            self.buttons_frame,
            maximum=100,
        )

    
    def place_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.place_widgets")
        self.description.pack(side='top',fill='x',pady=(0,self.cget('pady')))
    
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
        self.command_options_entry.grid(row=4,column=1,sticky='news')
        
        self.server_info_frame.columnconfigure(1,weight=1)
        self.server_info_frame.pack(side='top',fill='x',expand=True)
        
        self.progressbar.pack(anchor='center',side='left',fill='both',expand=True,padx=(0,self.cget('padx')))
        
    def close_soft(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.close_soft")
        self.cancel()
        self.close()
        
    def cancel(self, event=None, message="Download canceled"):
        if globals.debug > 1: print("downloaddatafromserver.cancel")

        self.canceled = True
        
        if self.thread is not None: self.thread.stop()
        if self.subprocess is not None:
            try:
                os.killpg(os.getpgid(self.subprocess.pid), signal.SIGTERM)
            except OSError:
                pass

        self.okbutton.configure(relief='raised',text='Download',command=self.download_pressed)
        self.progressbar.set_text(message)
        self.progressbar.configure(value=0)
        self.enable_widgets()
        self.canceled = True

    def on_scp_button_pressed(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.on_scp_button_pressed")
        if self.previous_command_choice == 'rsync':
            self.previous_rsync_options = self.command_options.get()
        self.command_options.set(self.previous_scp_options)
        self.previous_command_choice = 'scp'
        
    def on_rsync_button_pressed(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.on_rsync_button_pressed")
        if self.previous_command_choice == 'scp':
            self.previous_scp_options = self.command_options.get()
        self.command_options.set(self.previous_rsync_options)
        self.previous_command_choice = 'rsync'

    def set_widget_states(self,state):
        if globals.debug > 1: print("downloaddatafromserver.set_widget_states")
        for child in self.server_info_frame.winfo_children():
            if hasattr(child,"configure") and 'state' in child.configure():
                child.configure(state=state)
        
    def disable_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.disable_widgets")
        self.set_widget_states('disabled')
        # Don't know why, but the radio buttons don't behave normally
        self.rsync_button.configure(state='disabled')
        self.scp_button.configure(state='disabled')
    def enable_widgets(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.enable_widgets")
        self.set_widget_states('normal')
        # Don't know why, but the radio buttons don't behave normally
        self.rsync_button.configure(state='normal')
        self.scp_button.configure(state='normal')

    def download_pressed(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.download_pressed")
        # Save the entries in the gui preferences so they pop up
        # automatically the next time we want to use them
        self.gui.set_preference(
            "downloaddatafromserver",
            {
                'username' : self.username.get(),
                'address' : self.address.get(),
                'path' : self.path.get(),
                'command' : self.command_choice.get(),
                'command options' : self.command_options.get(),
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
        self.okbutton.configure(relief='sunken',text="Cancel",command=self.cancel)

        # Block until the task has finished
        while self.thread.isAlive():
            self.root.update()

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
                # Now add the downloaded files to the gui file list
                self.close()
                
                self.gui.update_filenames()
                self.gui.filecontrols.current_file.set(self.gui.filenames[0])
                self.gui.read()
                self.gui.interactiveplot.reset()
                self.gui.interactiveplot.update()
                self.gui.controls.save_state()

                return

        self.subprocess = None
        self.enable_widgets()
        self.progressbar.configure(value=0)

    def download_files(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.download_files")
        #print(self.filenames)
        #cmd = self.command_choice.get()+" "
        cmd = self.command_choice.get()+" "+self.command_options.get()+" "+self.server
        if self.command_choice.get() == "scp":
            if " " in self.path.get():
                print("When using the scp command, you cannot specify multiple files by separating them with a space. You must use wildcard patterns instead. Consider using rsync instead.")
                self.cancel(message="Error. See terminal.")
                return
            else:
                cmd += ":"+self.path.get()
        elif self.command_choice.get() == "rsync":
            cmd += " ".join([":"+name for name in self.path.get().split(" ")])

        cmd += " "+self.tmp_path
            
        self.subprocess = subprocess.Popen(
            cmd.split(" "),
            stdout=DEVNULL,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        stdout, stderr = self.subprocess.communicate()
        if stderr is not None and len(stderr) != 0:
            print(stderr.decode('ascii').strip())
            self.cancel(message="Error. See terminal.")
                
    def get_file_list(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.get_file_list")
        # Get the list of files that will be downloaded
        self.progressbar.set_text("Retrieving file list...")
        self.subprocess = subprocess.Popen([
            "ssh",
            self.server,
            "stat -c '%s %n'",
            self.path.get(),
        ],stdout=subprocess.PIPE,stderr=subprocess.PIPE,preexec_fn=os.setsid)
        stdout, stderr = self.subprocess.communicate()
        if not self.canceled:
            if stderr is not None and len(stderr) != 0:
                cmd = self.command_choice.get()+" "+self.command_options.get()+" "+self.server+":"+self.path.get()+" "+self.tmp_path
                print("Tried command:",cmd)
                print(stderr.decode('ascii').strip())
                self.cancel(message="Error. See terminal.")
            else:
                stdout = stdout.decode('ascii').strip().split("\n")
                self.filelist = [o.split(" ") for o in stdout]
                self.filenames = [f[1] for f in self.filelist]
                self.total_size = sum([int(f[0].strip("'")) for f in self.filelist])

    def download_update(self,*args,**kwargs):
        if globals.debug > 1: print("downloaddatafromserver.download_update")
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

        self.root.update()
        
        
        
    

    

        
    
    
    




    

    
