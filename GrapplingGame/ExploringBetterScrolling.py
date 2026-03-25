import pyglet
import numpy as np
import random

import math

#Creating the empty map
TileMap = np.zeros((1000, 1000), dtype=int)
TileMap.fill(-1)


# Global variables
Yvel = 0
Xvel = 0
CamX = 200
CamY = 200
TileSize = 32
ChunkSize = 32
MouseX, MouseY = 0, 0
LastCamX, LastCamY = 0,0
Grappling = False
GrapplingHookX, GrapplingHookY = 0,0
W,A,D = False,False,False
TouchedFloor = False
Mode = 2 #Mode1 is for playing Mode2 is for map editing
DraggingCam = False
TileType = 0



Window = pyglet.window.Window(vsync=False)
Window.set_fullscreen(True)
fps_display = pyglet.window.FPSDisplay(window=Window)

Block = pyglet.image.load(r"Textures\Block.png")
Face = pyglet.image.load(r"Textures\Face.png")
Body = pyglet.image.load(r"Textures\body3.png")


PlayerStuff = pyglet.graphics.Batch()
CachingList = []

        
CachingList.append(pyglet.shapes.Circle(0,0,5,batch=PlayerStuff))#for the grappling hook
CachingList.append(pyglet.shapes.Line(0, 0,0,0, thickness=2, color=(255, 0, 0),batch=PlayerStuff))#for the grappling line
        
CachingList.append(pyglet.shapes.Line(0, 0, 0, 0, thickness=2, color=(255, 0, 0),batch=PlayerStuff))#for the ray going towards the mouse

#CachingList.append(pyglet.shapes.Rectangle(0,0,TileSize-4,TileSize-4,batch=PlayerStuff))#for the player hitbox
CachingList.append(pyglet.sprite.Sprite(Block,0,0,batch=PlayerStuff))#for the player sprite
CachingList.append(pyglet.sprite.Sprite(Face,0,0,batch=PlayerStuff))#for the player face
    

#making chunks
class chunk():
    def __init__(self, X, Y):
        global TileSize, ChunkSize, TileMap
        self.batch = pyglet.graphics.Batch()
        self.tiles = np.zeros((ChunkSize,ChunkSize),dtype=object)

    def draw(self):
        self.batch.draw()


#adding the chunks to the 2d array
ChunkBank = np.empty((5, 5), dtype=object)
for X in range(5):
    for Y in range(5):
        ChunkBank[X, Y] = chunk(X, Y)

def Cast_Ray_For_Collision(X1, Y1, X2, Y2,XY):
    global TileSize
    dist = 0
    Collided = False
    if XY == "X":
        if X1 < X2:
            dist = abs(X1-X2)
            MoveX = 1
            MoveY = 0
        else:
            MoveX = -1
            MoveY = 0

    elif XY == "Y":
        dist = abs(Y1-Y2)
        if Y1 < Y2:
            MoveX = 0
            MoveY = 1
        else:
            MoveX = 0
            MoveY = -1
        

    for Step in range(int(dist)+int(TileSize/2)):
        RayX = X1 + MoveX * Step
        RayY = Y1 + MoveY * Step

        TileX = int(RayX // TileSize)
        TileY = int(RayY // TileSize)

        if 0 <= TileX < TileMap.shape[0] and 0 <= TileY < TileMap.shape[1]:
            if TileMap[TileX, TileY] == 0:
                Collided = "Block"
                return RayX, RayY,Collided
            
            elif TileMap[TileX, TileY] == 1 and Step < int(dist/1): 
                Collided = "Death"
                return RayX, RayY,Collided
            
    return X2, Y2,Collided

#collision
def Check_Player_Collision():
    global CamX, CamY, LastCamX, LastCamY, Xvel, Yvel,TouchedFloor,TileSize

    playerX = -CamX + Window.width / 2 
    playerY = -CamY + Window.height / 2
    
    LastX = -LastCamX + Window.width / 2 
    LastY = -LastCamY + Window.height / 2
    
    hitX, hitY, CollidiedX = Cast_Ray_For_Collision(LastX, LastY, playerX, LastY,"X")
    
    offset = int(TileSize/2)-2

    if CollidiedX == "Block":
    
        if playerX<LastX:
            CamX = Window.width/2-hitX-offset
        elif playerX-LastX > 0:
            CamX = Window.width/2-hitX+offset
        Xvel = 0
    elif CollidiedX == "Death": 
        CamX = 0
        CamY = 0
        Xvel = 0
        Yvel = 0
        return
    playerX = -CamX + Window.width / 2 


    hitX, hitY, CollidiedY = Cast_Ray_For_Collision(playerX,LastY,playerX,playerY,"Y")
    
    if CollidiedY == "Block":
        
        if playerY<LastY:
            CamY = Window.height/2-hitY-offset
        elif playerY-LastY > 0:
            CamY = Window.height/2-hitY+offset
        
        if LastY >playerY:
            TouchedFloor = True
        Yvel = 0
        Xvel*= 0.95

    elif CollidiedY == False:
            TouchedFloor = False

    elif CollidiedY == "Death": 
        CamX = 0
        CamY = 0
        Xvel = 0
        Yvel = 0
        return
    
def Cast_Ray_For_Grappling_Hook(X1,Y1,X2,Y2): #I have two different raycasting fucntions because I want the hook range to be exactly what I want but mostly cuz Im too lazy to make a toggle 
    Collided = False
    dist = math.sqrt(abs(X2-X1)**2+ abs(Y2-Y1)**2)
    if dist == 0:
        return (0,0,False)

    normanisedX = (X2-X1)/dist
    normanisedY = (Y2-Y1)/dist
    grappler_Range = 400
    
    for Step in range(grappler_Range//10):
        RayX = X1 + normanisedX * (Step*10)
        RayY = Y1 + normanisedY * (Step*10)

        TileX = int(RayX // TileSize)
        TileY = int(RayY // TileSize)

        if 0 <= TileX < TileMap.shape[0] and 0 <= TileY < TileMap.shape[1]:
            if TileMap[TileX, TileY] == 0:
                Collided = True
                return RayX, RayY,Collided
            
    return X1 + normanisedX*grappler_Range, Y1 + normanisedY*grappler_Range,Collided

# mouse and key presses




@Window.event
def on_mouse_press(x, y, button, modifiers):
    global CamX, CamY, MouseX, MouseY,Grappling,GrapplingHookX,GrapplingHookY,Mode
    if Mode == 1:
        MouseX = x
        MouseY = y
        if button == pyglet.window.mouse.LEFT:
            Xp,Yp,Collided =Cast_Ray_For_Grappling_Hook(-CamX + Window.width / 2,-CamY + Window.height / 2, -CamX + MouseX, -CamY + MouseY)
            if Collided == True:
                GrapplingHookX = Xp
                GrapplingHookY = Yp
                Grappling = True
    

@Window.event
def on_mouse_release(x, y, button, modifiers):
    global Grappling,Mode
    if Mode == 1:
        if button == pyglet.window.mouse.LEFT:
            Grappling = False
@Window.event

def on_mouse_drag(x, y, dx, dy, buttons, modifiers):
    global CamX,CamY,Mode,TileSize,ChunkSize,ChunkBank,MouseX,MouseY,TileType,TileMap,Block
    if Mode == 2:
        if buttons == pyglet.window.mouse.RIGHT:
            CamX += dx
            CamY += dy
        elif buttons == pyglet.window.mouse.LEFT:
            
            MouseTileX = int((x-CamX)//TileSize)#finding the mouses real pos
            MouseTileY = int((y-CamY)//TileSize)

            MouseTileChunk = ChunkBank[int(MouseTileX//ChunkSize),int(MouseTileY//ChunkSize)]#finding the chunk the mouse is in

            MouseXInChunk = int((MouseTileX/ChunkSize-math.floor(MouseTileX/ChunkSize))*ChunkSize)#fining the pos of the mouse inside of the chunk its in
            MouseYInChunk = int((MouseTileY/ChunkSize-math.floor(MouseTileY/ChunkSize))*ChunkSize)
            if TileType == 1:
                MouseTileChunk.tiles[MouseXInChunk,MouseYInChunk] = pyglet.shapes.Rectangle(MouseTileX*TileSize,MouseTileY*TileSize,TileSize,TileSize,color=(TileType*40,50,50), batch=MouseTileChunk.batch)#and finnaly chainging the color of the tile the mouse is on
            elif TileType == -1:
                MouseTileChunk.tiles[MouseXInChunk,MouseYInChunk] = None
            elif TileType == 0:
                MouseTileChunk.tiles[MouseXInChunk,MouseYInChunk] = pyglet.sprite.Sprite(img=Block,x= MouseTileX*TileSize,y =MouseTileY*TileSize,batch=MouseTileChunk.batch)
            TileMap[MouseTileX,MouseTileY] = int(TileType)


@Window.event
def on_mouse_motion(x, y, dx, dy):
    global MouseX, MouseY,Mode,CamX,CamY
    MouseX = x
    MouseY = y
        
@Window.event        
def on_mouse_scroll(x, y, scroll_x, scroll_y):
    global Mode,TileType
    if Mode == 2:
        TileType += int(scroll_y)
        if TileType > 1:
            TileType = -1
        if TileType < -1:
            TileType = 1

#managing the key states
@Window.event
def on_key_press(symbol, modifiers):
    global W,A,D,Mode,CamX,CamY,Xvel,Yvel
    if Mode == 1:
        
        if symbol == pyglet.window.key.W or symbol == pyglet.window.key.SPACE :
            W = True
        elif symbol == pyglet.window.key.A:
            A = True
        elif symbol == pyglet.window.key.D:
            D = True
        elif symbol == pyglet.window.key.C:
            Mode = 2
            
    elif Mode == 2:
        if symbol == pyglet.window.key.C:
            Mode = 1

            Xvel = 0
            Yvel = 0 
            CamX = 0
            CamY = 0
            

@Window.event
def on_key_release(symbol, modifiers):
    global W,A,D,Mode
    if Mode == 1:
        if symbol == pyglet.window.key.W or symbol == pyglet.window.key.SPACE :
            W = False
        elif symbol == pyglet.window.key.A:
            A = False
        elif symbol == pyglet.window.key.D:
            D = False




#per-frame and delta-time updates

@Window.event
def update(dt):
    
    global Yvel,Xvel,CamX, CamY,LastCamX,LastCamY,W,A,D,Grappling,TouchedFloor,Mode
    if Mode == 1:
        LastCamX = CamX
        LastCamY = CamY

        if W and TouchedFloor == True:#Movemeant checks
            Yvel-= 10
        if A:
            Xvel+= 0.5
        if D:
            Xvel-= 0.5

        if Grappling:
            playerX = -CamX + Window.width / 2
            playerY = -CamY + Window.height / 2

            dist = math.sqrt(abs(GrapplingHookX-playerX)**2+abs(GrapplingHookY-playerY)**2)
            Xvel -= ((GrapplingHookX-playerX)/dist)*1.5
            Yvel -= ((GrapplingHookY-playerY)/dist)*1.5


        Xvel*= 0.97#air resistance 
        Yvel+=0.4#gravity

        CamY+= Yvel*dt*60
        CamX+= Xvel*dt*60   
        Check_Player_Collision()
        

pyglet.clock.schedule_interval(update,1/60)


@Window.event
def on_draw():
    global CamX, CamY,Grappling,GrapplingHookX,GrapplingHookY,TileSize,Mode,TileType,Block
    
    Window.clear()
    camera_matrix = pyglet.math.Mat4.from_translation(pyglet.math.Vec3(CamX, CamY,0))
    Window.view = camera_matrix
    # Draw visible chunks
    XStart = max(0, int((-CamX) // (TileSize * ChunkSize)))
    YStart = max(0, int((-CamY) // (TileSize * ChunkSize)))
    XEnd = min(5, XStart + int(Window.width // (TileSize * ChunkSize)) + 2)
    YEnd = min(5, YStart + int(Window.height // (TileSize * ChunkSize)) + 2)

    for chunkx in range(XStart, XEnd):
        for chunky in range(YStart, YEnd):
            ChunkBank[chunkx, chunky].draw()

    #calculating the player stuff
    if Mode == 1:
        playerX = -CamX + Window.width / 2
        playerY = -CamY + Window.height / 2
        rayX, rayY,Collided = Cast_Ray_For_Grappling_Hook(playerX, playerY, -CamX + MouseX, -CamY + MouseY)
        
        

        if Grappling == True:
            CachingList[0].batch = PlayerStuff#add back the grappling dot 
            CachingList[1].batch = PlayerStuff #add the grapple line back
            CachingList[2].batch = None # remove the mouse line from batch so we dont draw it

            CachingList[0].x =GrapplingHookX#change the hook dot pos
            CachingList[0].y =GrapplingHookY
            
            CachingList[1].x = playerX#change the grapple line pos
            CachingList[1].y = playerY
            CachingList[1].x2 = GrapplingHookX
            CachingList[1].y2 = GrapplingHookY
            
        else:
            CachingList[0].batch = None # remove the grappling dot from batch
            CachingList[1].batch = None # remove the grappling line from batch
            CachingList[2].batch = PlayerStuff#add back the mouse line to the batch

            CachingList[2].x = playerX#change the mouse line pos
            CachingList[2].y = playerY
            CachingList[2].x2 = rayX
            CachingList[2].y2 = rayY
        
        #CachingList[3].x = playerX-(TileSize/2)+2#change the player hitbox pos
        #CachingList[3].y = playerY-(TileSize/2)+2
        

        
        CachingList[3].x = Window.width/2-CamX-16#change the player sprite pos
        CachingList[3].y = Window.height/2-CamY-16

        SpriteX = (Window.width/2-CamX-16)
        SpriteY = (Window.height/2-CamY-16)

        dist = math.sqrt(abs((SpriteX-(MouseX-CamX))**2) + abs((SpriteY-(MouseY-CamY))**2))
    

        normanisedX = (((MouseX-CamX) - SpriteX))/dist
        normanisedY = (((MouseY-CamY) - SpriteY))/dist

        CachingList[4].x = SpriteX+normanisedX*5#change the player sprite pos
        CachingList[4].y = SpriteY+normanisedY*5
        
        PlayerStuff.draw()
    
        
    
    Window.view = pyglet.math.Mat4()#reseting the camera
    if Mode == 2:
        pyglet.shapes.Rectangle(Window.width-50,0,50,50,color=(int(TileType*40),50,50)).draw()

    fps_display.draw()
    
pyglet.app.run(0)
