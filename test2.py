import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

Nx = 101
Ny = 101

xmin = -5
xmax = 5
ymin = -5
ymax = 5

xpos = np.linspace(xmin,xmax,Nx)
ypos = np.linspace(ymin,ymax,Ny)

dx = xpos[1]-xpos[0]
dy = ypos[1]-ypos[0]

print(dx,dy)

xp = 0.32
yp = 0.32
hp = 3.5

neighborhood = []

ip = (xp-xmin)/dx
jp = (yp-ymin)/dy

r2 = hp*hp
rE = xp+hp
bE = yp+hp

print("Okay")
dx_grid = xp - xpos[int(round((xp-xpos[0])/dx,0))]
dy_grid = yp - ypos[int(round((yp-ypos[0])/dy,0))]

#dx_grid = xpos[np.argmin(np.abs(xpos-xp))]-xp
#dy_grid = ypos[np.argmin(np.abs(ypos-yp))]-yp

print(dx_grid)
#quit()

xpos_shifted = xpos - xp
ypos_shifted = ypos - yp

imin = int((xp-hp - xpos[0])/dx)
imax = int((xp+hp - xpos[0])/dx)

#imin = int(((xp-dx_grid)-hp-xpos[0])/dx) + 1
#imax = int(((xp-dx_grid)+hp-xpos[0])/dx) + 1
for i in range(imin,imax):
    #print(hp**2,(xpos_shifted[i])**2)
    delta_x = xpos[i]-xp
    if abs(delta_x-hp) > 1.e-6:
        maxdy = hp*np.sin(np.arccos(abs(delta_x/hp)))
    else:
        maxdy = 0

    if not np.isfinite(maxdy):
        print(delta_x,hp)
        print(maxdy)
        raise
        
    #maxdy = math.sqrt(hp**2 - (xpos_shifted[i])**2)
    yposmin = yp-maxdy
    yposmax = yp+maxdy
    jmin = int(round((yposmin-ypos_shifted[0])/dy,6)) + 1
    jmax = int(round((yposmax-ypos_shifted[0])/dy,6)) + 1
    for j in range(jmin,jmax):
        neighborhood.append((xpos[i],ypos[j]))

"""
xpos_in_circle = np.arange(xp-hp,xp+hp,dx)

for x in xpos_in_circle:
    print(hp**2,((x-xp)-dx_grid)**2)
    yspan = math.sqrt(hp**2 - (x-xp)**2)
    for y in np.arange(yp-yspan,yp+yspan,dy):
        neighborhood.append((x+dx_grid,y+dy_grid))
"""
"""
x = xp-dx_grid
while x < xp+hp:
    yspan = math.sqrt(hp**2 - ((xp-x))**2)
    #yspan = hp*np.sin(np.arccos((xp-x)/hp))
    y = yp-dy_grid
    while y < yp+yspan:
        neighborhood.append((x,y))
        y+=dy
    x+=dx
"""
"""
imax = hp/dx
for i in range(int(imax)+1):
    jmax = math.sqrt((hp/dy)**2 - i**2)
    for j in range(int(jmax)+1):
        neighborhood.append((xpos[int(ip)+i],ypos[int(jp)+j]))
"""
neighborhood = np.array(neighborhood)

print(len(neighborhood))


xypos = np.column_stack((
    np.repeat(xpos,len(ypos)),
    np.tile(ypos,len(xpos)),
))

fig, ax = plt.subplots(dpi=200)
ax.scatter(xypos[:,0],xypos[:,1],s=1, color='k')
ax.scatter(neighborhood[:,0],neighborhood[:,1],s=1,color='r')

ax.add_patch(Circle((xp,yp),hp,fill=False))

ax.set_xlim(xmin,xmax)
ax.set_ylim(ymin,ymax)
ax.set_aspect('equal')

plt.show()
