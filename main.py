import pygame, requests, io, sys, csv, random

# Asset Urls
tilesetUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/main/Tileset.png"
tilesetDarkUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/a3e090b36c60e35889e90da922884cdd78a3395b/TilesetDark.png"

tilesetRoadUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/6b92357a8a5a5ae25b231ee267b21f739032b31d/TilesetRoad.png"
tilesetRoadID = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/f28de1c880fb890960f9d7c56b21c03bc112ab48/Road%20Tileset%20ID.csv"

tilesetUiUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/e051ba39af9120a147405ab5d56e7359e1882959/TilemapUI.png"
logoUiUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/a386c76485b0b04b18e17b51acbda0c544ccfb14/Logo.png"
riverBasinUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/434a2e2d30e6535dd466531759447a4809f8ae6c/River%20Basin%20Level.csv"
greenplainsUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/a47a02e15256fb7914f5dc01ef5c7827af088e1a/Green%20Plains.csv"
greenplainstestUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/6b50712d6b090a5b4fcaff660ab57f222b274b80/Green%20Plains%20Test.csv"

# Initialization
pygame.init()
pygame.display.set_caption("Supply Chains")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24)
tileSize = 32
avaliableMaps = [riverBasinUrl, greenplainsUrl]
currentMap = random.choice(avaliableMaps)

global currentRoad, hiddenBridges
placementError = "You cannot place here."

# CSV Loading
def loadData(url=riverBasinUrl):
    try:
        csvResp = requests.get(url).text
        csvReader = csv.reader(io.StringIO(csvResp))
        return [[int(cell) for cell in row if cell.strip() != ""] for row in csvReader]
    except Exception as e:
        print("CSV error:", e)
        sys.exit()

global mapData, tileData
mapData = loadData(riverBasinUrl)
tileData = loadData(tilesetRoadID)
mapHeight = len(mapData)
mapWidth = max(len(row) for row in mapData)
screen = pygame.display.set_mode((mapWidth * tileSize, mapHeight * tileSize))

# Asset Loading
def loadImage(url):
    try:
        response = requests.get(url)
        return pygame.image.load(io.BytesIO(response.content)).convert_alpha()
    except Exception as e:
        print(f"Error loading image from {url}:", e)
        sys.exit()

tileset = loadImage(tilesetUrl)
tilesetDark = loadImage(tilesetDarkUrl)

tilesetRoad = loadImage(tilesetRoadUrl)
tilesetUi = loadImage(tilesetUiUrl)
tilesetLogoUi = loadImage(logoUiUrl)

# Tile Functions
def getTileById(sheet, tileId):
    cols = sheet.get_width() // tileSize
    x = (tileId % cols) * tileSize
    y = (tileId // cols) * tileSize
    tile = pygame.Surface((tileSize, tileSize), pygame.SRCALPHA)
    tile.blit(sheet, (0, 0), (x, y, tileSize, tileSize))
    return tile

global tileCache
tileCache = {}
def getTileCached(sheet, tileId):
    key = (id(sheet), tileId)
    if key not in tileCache:
        tileCache[key] = getTileById(sheet, tileId)
    return tileCache[key]

# Map Loading
def drawMap(sheet):
    for y, row in enumerate(mapData):
        for x, tileId in enumerate(row):
            tile = getTileCached(sheet, tileId)
            screen.blit(tile, (x * tileSize, y * tileSize))

# Road Tile Placement
global bridgeTileCache, roadTilePlacementCache, roadTileMapping
bridgeTileCache = {}
roadTilePlacementCache = {}
roadTileMapping = {
    0: [], # Straight 
    1: [], # Corner 
    2: [], # T-Junction 
    3: [], # Intersection 
    4: [], # Short-Bridge 
    5: [], # Long-Bridge
}

def editBridge(cache=bridgeTileCache, tile=None, coord=(0,0), bridgeNumber=0):
    if bridgeNumber not in cache:
        cache[bridgeNumber] = []
    cache[bridgeNumber].append([coord, tile])
    bridgeCollision(cache)

def deleteBridge(cache=bridgeTileCache, bridgeNumber=0):
    if bridgeNumber not in cache:
        return

    for coord, tile in cache[bridgeNumber]:
        if coord in roadTilePlacementCache:
            roadTilePlacementCache[coord] = [
                t for t in roadTilePlacementCache[coord] if t != tile
            ]
            if not roadTilePlacementCache[coord]:
                del roadTilePlacementCache[coord]
    del cache[bridgeNumber]


def bridgeCollision(cache=bridgeTileCache):
    removeTile = dict()
    removeBridge = set()
    index = sorted(cache.keys())

    for i in index:
        tiles = cache[i]
        for pos, tile in tiles:
            if tile in [roadTileMapping[4][i] for i in [0, 2, 3, 5]] + [roadTileMapping[5][i] for i in [0, 3, 4, 7]]:
                continue
            elif pos in removeTile:
                removeBridge.add(removeTile[pos])
            removeTile[pos] = i
    
    for bridge in removeBridge:
        if bridge in cache:
            deleteBridge(cache, bridge)

def bridgeLocate(cache=bridgeTileCache, contains=(0, 0)):
    for bridgeNumber, tiles in bridgeTileCache.items():
        for coord, tile in tiles:
            if coord == contains:
                return bridgeNumber
    return None

def roadMapping(sheet=tileData):
    for y, row in enumerate(sheet):
        for x, tileId in enumerate(row):
            if tileId != -1:
                tile = getTileCached(tilesetRoad, tileId)
                if tile not in roadTileMapping[x]:
                    roadTileMapping[x].append(tile)

def drawRoad(sheet=roadTilePlacementCache, mouseCoord=(0, 0)):
    roadId = [item for i in range(4) for item in roadTileMapping[i]]
    hiddenTiles = []
    if 'hiddenBridges' in globals() and hiddenBridges:
        for idBridge in hiddenBridges:
            if idBridge in bridgeTileCache:
                for coord, tile in bridgeTileCache[idBridge]:
                    hiddenTiles.append([coord, tile])

    for coord, tiles in sheet.items():
        gridXTile = (coord[0] // tileSize) * tileSize
        gridYTile = (coord[1] // tileSize) * tileSize
        
        for tile in tiles:
            if tile is None: continue  
            if tile in roadId:
                if (gridXTile, gridYTile) != mouseCoord:
                    screen.blit(tile, coord)
            elif tile not in roadId:
                if [coord, tile] in hiddenTiles: continue
                screen.blit(tile, coord)
                
#Road Tile deletion
def deleteRoad(mouseCoord=(0, 0)):
    global currentRoad
    currentRoad = None  # Reset the current road selection or status

    x, y = mouseCoord
    isWater = mapData[y // tileSize][x // tileSize] in range(12, 17)

    bridgePart = (
        [roadTileMapping[5][i] for i in [0, 3, 4, 7]] +
        [roadTileMapping[4][i] for i in [0, 2, 3, 5]]
    )

    print(isWater)
    bridgeNumber = bridgeLocate(bridgeTileCache, contains=mouseCoord)
    if bridgeNumber is not None and isWater:
        print("Deleting bridge")
        deleteBridge(bridgeTileCache, bridgeNumber)
    elif mouseCoord in roadTilePlacementCache:
        print("Deleting Road")
        # Delete road tiles at this coord that are NOT part of bridge tiles
        roadTilePlacementCache[mouseCoord] = [
            tile for tile in roadTilePlacementCache[mouseCoord] if tile in bridgePart
        ]
        if not roadTilePlacementCache[mouseCoord]:
            del roadTilePlacementCache[mouseCoord]
        print(mouseCoord)
        print(roadTilePlacementCache)


# Clock class - too annoying to make using functions
class Timer:
    def __init__(self):
        self.startTime = None
        self.running = False

    def start(self):
        self.startTime = pygame.time.get_ticks()
        self.running = True

    def reset(self):
        self.startTime = pygame.time.get_ticks()

    def stop(self):
        self.running = False

    def elapsed(self):
        if not self.running or self.startTime is None:
            return 0
        return (pygame.time.get_ticks() - self.startTime) / 1000.0  # seconds

# Main Loop
timer = Timer()
running = True
currentRoad = None
currentMode = "building"

a = 1
index = 0
state = "menu"
mapData = loadData(riverBasinUrl)
roadMapping()

playRect = pygame.Rect(tileSize * 6, tileSize * 8, tileSize * 3, tileSize)
logoRect = pygame.Rect(tileSize * 5, tileSize * 4, tileSize * 5, tileSize * 2)
exitRect = pygame.Rect(tileSize * 13, tileSize * 1, tileSize, tileSize)

while running:
    #Mouse Positioning
    mouseX, mouseY = pygame.mouse.get_pos()
    gridX = (mouseX // tileSize) * tileSize
    gridY = (mouseY // tileSize) * tileSize
    outlineRect = pygame.Rect(gridX, gridY, tileSize, tileSize)
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 3:
            currentMode = "deleting"
            deleteRoad(mouseCoord=(gridX, gridY))
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            currentMode = "building"

            #Exit button clicked logic
            if exitRect.collidepoint(event.pos):
                if state == "game":
                    mapData = loadData(riverBasinUrl)
                    state = "menu"
                    roadTilePlacementCache.clear()
                    bridgeTileCache.clear()
                elif state == "menu":
                    running = False
            elif state == "menu" and playRect.collidepoint(event.pos):
                mapData = loadData(greenplainstestUrl) # LOAD MAP HERE FOR GAME
                state = "game"
            elif state == "game" and currentMode == "building":
                # Update roadTileMapping for placement cache
                if currentRoad == None:
                    print("Currently placing nothing.")
                    continue
                bridgeNumber = 0 if not bridgeTileCache else max(bridgeTileCache.keys()) + 1
                isValid = False
                isLand = []

                # Valid Bridge placement check
                if index in [4, 5]:
                    offset = [
                        [[0, 1], [0, -1], [1, 0], [-1, 0]],
                        [[0, 2], [0, 1], [0, -1], [-2, 0], [-1, 0], [1, 0]]
                    ]
                    for offsetX, offsetY in offset[index - 4]:
                        try:
                            idTile = mapData[(gridY + tileSize * offsetY) // tileSize][(gridX + tileSize * offsetX) // tileSize]
                            screen.blit(getTileCached(tileset, idTile), (32, 32))
                            isLand.append(False if idTile in range(12, 17) else True)
                        except IndexError:
                            isLand.append(None)
                    roadId = list(roadTileMapping[index]).index(currentRoad)
                    if index == 4:
                        i = 0 if roadId == 0 else 2
                        if isLand[i] and isLand[i + 1] and isLand[i] == isLand[i + 1]:
                            isValid = True
                    elif index == 5:
                        i = 0 if roadId == 0 else 3
                        if isLand[i] and isLand[i + 2] and not isLand[i + 1] and isLand[i] == isLand[i + 2] and isLand[i] != isLand[i + 1]:
                            isValid = True

                # Update roadTileplacementCache to reflect changes
                isWater = mapData[gridY // tileSize][gridX // tileSize] in range(12, 17)
                isBridge = index in [4, 5]
                roadId = [item for i in range(4) for item in roadTileMapping[i]]

                if index not in [4, 5]:
                    if not isWater and not isBridge:
                        presentTiles = roadTilePlacementCache.get((gridX, gridY), [])
                        bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                        roadTilePlacementCache[(gridX, gridY)] = [currentRoad] + bridgeTiles
                    else:
                        print(placementError)
                elif index in [4, 5] and isWater and isBridge and isValid:
                    currentIndex = roadTileMapping[index].index(currentRoad)
                    if index == 4:
                        if currentIndex == 0:
                            for i in range(-1, 2):
                                pos = (gridX, gridY + tileSize * i)
                                presentTiles = roadTilePlacementCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTilePlacementCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                        elif currentIndex == 3:
                            for i in range(-1, 2):
                                pos = (gridX - tileSize * i, gridY)
                                presentTiles = roadTilePlacementCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTilePlacementCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                    elif index == 5:
                        if currentIndex == 0:
                            for i in range(-1, 3):
                                pos = (gridX, gridY + tileSize * i)
                                presentTiles = roadTilePlacementCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTilePlacementCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                        elif currentIndex == 4:
                            for i in range(-1, 3):
                                pos = (gridX - tileSize * i, gridY)
                                presentTiles = roadTilePlacementCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTilePlacementCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                else: print(placementError)
        elif event.type == pygame.KEYDOWN:
            if state == "game":
                currentMode = "building"
                if pygame.K_1 <= event.key <= pygame.K_6:
                    index = event.key - pygame.K_1
                    if roadTileMapping[index]:
                        currentRoad = roadTileMapping[index][0]
                    else:
                         currentRoad = None
                elif event.key == pygame.K_r and currentRoad:
                    try:
                        currentIndex = roadTileMapping[index].index(currentRoad)
                        if index == 4: step = 3
                        elif index == 5: step = 4
                        else: step = 1
                            
                        nextIndex = (currentIndex + step) % len(roadTileMapping[index])
                        currentRoad = roadTileMapping[index][nextIndex]
                    except (ValueError, IndexError):
                        currentRoad = None

    if state == "game":
        hiddenBridges = list()
        # Road Drawing to cursor
        drawMap(tileset)

        # Tile outline
        if not exitRect.collidepoint(mouseX, mouseY):
            if currentMode == "building":
                pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)
            elif currentMode == "deleting":
                if not timer.running:   # start the timer only once when entering deleting mode
                    timer.start()
                if timer.elapsed() <= 0.175:
                    pygame.draw.rect(screen, (255,50,50), outlineRect, width=1)
                else:
                    timer.reset()
                    timer.stop()
                    currentMode = "building"
                    pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)


        # Tile bilt current tile onto screen (cursor)
        if currentRoad and not exitRect.collidepoint(mouseX, mouseY):
            bridgeId = [roadTileMapping[5][i] for i in [1, 2, 5, 6]] + [roadTileMapping[4][i] for i in [1, 4]]
            currentIndex = roadTileMapping[index].index(currentRoad)
            gridX = (mouseX // tileSize) * tileSize
            gridY = (mouseY // tileSize) * tileSize

            if index == 4:
                if currentIndex == 0:
                    for i in range(-1, 2):
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad, (gridX, gridY + tileSize * i))
                        if (
                            bridgeLocate(contains=(gridX, gridY + tileSize * i)) is not None and
                            newRoad in bridgeId and
                            mapData[(gridY + tileSize * i) // tileSize][gridX // tileSize] in range(12, 17)
                        ):
                            hiddenBridges.append(bridgeLocate(contains=(gridX, gridY + tileSize * i)))
                elif currentIndex == 3:
                    for i in range(-1, 2):
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad, (gridX - tileSize * i, gridY))
                        if (
                            bridgeLocate(contains=(gridX - tileSize * i, gridY)) is not None and
                            newRoad in bridgeId and
                            mapData[gridY // tileSize][(gridX - tileSize * i) // tileSize] in range(12, 17)
                        ):
                            hiddenBridges.append(bridgeLocate(contains=(gridX - tileSize * i, gridY)))
            elif index == 5:
                if currentIndex == 0:
                    for i in range(-1, 3):
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad, (gridX, gridY + tileSize * i))
                        if (
                            bridgeLocate(contains=(gridX, gridY + tileSize * i)) is not None and
                            newRoad in bridgeId and
                            mapData[(gridY + tileSize * i) // tileSize][gridX // tileSize] in range(12, 17)
                        ):
                            hiddenBridges.append(bridgeLocate(contains=(gridX, gridY + tileSize * i)))
                elif currentIndex == 4:
                    for i in range(-1, 3):
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad, (gridX - tileSize * i, gridY))
                        if (
                            bridgeLocate(contains=(gridX - tileSize * i, gridY)) is not None and
                            newRoad in bridgeId and
                            mapData[gridY // tileSize][(gridX - tileSize * i) // tileSize] in range(12, 17)
                        ):
                            hiddenBridges.append(bridgeLocate(contains=(gridX - tileSize * i, gridY)))
            elif bridgeLocate(contains=(gridX, gridY)) is None or not (
                mapData[gridY // tileSize][gridX // tileSize] in range(12, 17)
            ):
                screen.blit(currentRoad, (gridX, gridY))

        drawRoad(roadTilePlacementCache, (gridX, gridY))

    
    elif state == "menu":
        # Play Button
        drawMap(tilesetDark) 
        buttonTiles = range(3) if playRect.collidepoint(mouseX, mouseY) else range(3, 6)
        for i, tileIndex in enumerate(buttonTiles):
            screen.blit(getTileCached(tilesetUi, tileIndex), 
                      (playRect.x + i * tileSize, playRect.y))
        
        # Logo
        tileIndex = 0
        for iy in range(2):
            for ix in range(6):
                screen.blit(getTileCached(tilesetLogoUi, tileIndex),
                            (logoRect.x + ix * tileSize, logoRect.y + iy * tileSize))
                tileIndex += 1
    
    exitTile = 6 if exitRect.collidepoint(mouseX, mouseY) else 7
    screen.blit(getTileCached(tilesetUi, exitTile), exitRect.topleft)
    
    if currentMode != a:
        print(currentMode)
        a = currentMode
    pygame.display.flip()
pygame.quit()
