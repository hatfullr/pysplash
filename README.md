# pysplash
PySplash is a GUI inspired by SPLASH for quickly and easily plotting StarSmasher and MESA data

## Dependencies
* ![Python3](https://www.python.org/downloads/) or Python2
  * If using Python2, please install the [Enum](https://pypi.org/project/enum34/) package
* ![Tkinter](https://tkdocs.com/tutorial/install.html) (pre-installed with most Python distributions)
* ![Numpy](https://numpy.org/install/) (pre-installed with most Python distributions)
* ![Matplotlib 3.7.0](https://github.com/matplotlib/matplotlib/releases/tag/v3.7.0)
* ![Numba](https://numba.pydata.org/numba-doc/latest/user/installing.html) (optional)


It is strongly encouraged that you use Python3 and install Numba. Doing so will allow PySplash to access the GPU and run up to ~450x faster.

## Setup
Link the executable `pysplash` to your user's bin directory after downloading. In the PySplash directory, run these commands:
```bash
mkdir ~/bin
ln -s pysplash ~/bin
```
Check if your bin directory is included in your `PATH` variable,
```bash
echo $PATH | grep "$HOME/bin"
```
If you get no output, then run
```bash
export PATH=$PATH:$HOME/bin
```
and add that command to either your `.bashrc` or `.bash_profile` file in your `$HOME` directory.

## How to use
First, make sure you have data files to run with PySplash. You should edit the file `read_file.py` in the PySplash directory with a function for reading your data files. Additional instructions are included in `read_file.py`. Now, run PySplash from the terminal with the data files as input. For example,
```bash
pysplash out*.sph
```

If you happen to have Python2 installed as your default Python version and run into problems, try running pysplash explicitly with Python3,
```bash
python3 $HOME/bin/pysplash out*.sph
```

## Troubleshooting
* ```numba.cuda.cudadrv.error.CudaSupportError: Error at driver init: Call to cuInit results in UNKNOWN_CUDA_ERROR (804)```
  * Your NVIDIA driver might not match your CUDA library. If the output of the command `nvidia-smi` is `Failed to initialize NVML: Driver/library version mismatch`, then this is indeed the problem. First try rebooting your computer, then if that doesn't work check to be sure you have the latest NVIDIA drivers installed.