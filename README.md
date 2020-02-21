# pysplash
PySplash is a GUI inspired by SPLASH for quickly and easily plotting StarSmasher and MESA data

# Things to Fix
* After using the log or 10^ buttons, hovering the mouse over the plot no longer gives proper (x,y) positions. It seems the position is relative to the old data still. We must have to update the toolbar or something when replotting.

# Future feature wishlist
* Create a system that allows the user to specify their files' data type, so that any file can be read in
* Change aspect ratio from 'auto' to 'equal'
* Automatic adjustment of limits on/off
* Change particle marker type and size
* Adjust the plotting space
    * Manipulate whitespace
    * Change padding between axis and colorbar
    * Change tick lengths and directions
    * Add/remove minor ticks
* Save/Load settings
* Add total velocity calculations v = sqrt(vx^2 + vy^2 + vz^2)
* Ability to read in energy*.sph files and make a v0 plot
* Ability to read in col*.sph files and make a p0 plot
* Custom units adjustments for all axes
* Custom axis labels
* Add annotations to the plot window
