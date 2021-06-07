from m5stack import *
from m5ui import *
from uiflow import *

from m5stack import lcd

# setting the width, height and zoom  
# of the image to be created 
w, h, zoom = lcd.screensize()[1],lcd.screensize()[0],1

for row in range(w):
    for col in range(h):
        lcd.pixel(col, row, 0x0f0000)
    
# setting up the variables according to  
# the equation to  create the fractal 
cX, cY = -0.7, 0.27015
moveX, moveY = 0.0, 0.0
maxIter = 255

for x in range(w): 
    for y in range(h): 
        zx = 1.5*(x - w/2)/(0.5*zoom*w) + moveX 
        zy = 1.0*(y - h/2)/(0.5*zoom*h) + moveY 
        i = maxIter 
        while zx*zx + zy*zy < 4 and i > 1: 
            tmp = zx*zx - zy*zy + cX 
            zy,zx = 2.0*zx*zy + cY, tmp 
            i -= 1

        # convert byte to RGB (3 bytes), kinda  
        # magic to get nice colors 
        pix = (i << 21) + (i << 10) + i*8
        lcd.pixel(y, x, pix)