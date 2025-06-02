import pygame, requests, io, sys, csv, random 
from collections import deque #For Breadth-first search garbage later on

# Asset Urls
tilesetLandURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetLand.png"
tilesetLandDarkURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetLandDark.png"

tilesetRoadURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetRoad.png"
tilesetRoadIDURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Road%20Tileset%20ID.csv"
tilesetBuildingURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetBuildings.png"

buttonUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/cf7bc343463db246c12b7dd2baf18744e0877d9d/Button%20UI.png"
logoUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Logo%20UI.png"


riverBasinURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/River%20Basin%20Level.csv"
greenPlainsURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Green%20Plains.csv"
testPlainsURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Test%20Plains.csv"

# Initialization
pygame.init()
pygame.display.set_caption("Supply Chains")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24)
tileSize = 32
avaliableMaps = [riverBasinURL, greenPlainsURL]
currentMap = random.choice(avaliableMaps)

global currentRoad, hiddenBridges
placementError = "You cannot place here."

# CSV Loading
def loadData(url=riverBasinURL):
    try:
        csvResp = requests.get(url).text
        csvReader = csv.reader(io.StringIO(csvResp))
        return [[int(cell) for cell in row if cell.strip() != ""] for row in csvReader]
    except Exception as e:
        print("CSV error:", e)
        sys.exit()

global mapData, tileData
mapData = loadData(riverBasinURL)
tileData = loadData(tilesetRoadIDURL)
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

tilesetLand = loadImage(tilesetLandURL)
tilesetLandDark = loadImage(tilesetLandDarkURL)
tilesetRoad = loadImage(tilesetRoadURL)

tilesetBuilding = loadImage(tilesetBuildingURL)
tilesetUI = loadImage(buttonUIURL)
tilesetLogoUI = loadImage(logoUIURL)

#Set windows icon
pygame.display.set_icon(loadImage(
    "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/72a0b726fe279470a5b22a9f5aea50df0028eee2/WindowIcon.png"
    ))

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
            if (x, y) in buildingCache.keys(): # type: ignore
                continue
            tile = getTileCached(sheet, tileId)
            screen.blit(tile, (x * tileSize, y * tileSize))

# Road Tile Placement
global bridgeTileCache, roadTileCache, roadTileMapping
bridgeTileCache = {}
roadTileCache = {}
roadTileMapping = {
    0: [], # Straight 
    1: [], # Corner 
    2: [], # T-Junction 
    3: [], # Intersection 
    4: [], # Short-Bridge 
    5: [], # Long-Bridge
}

def findRoadTypeByID(sheet, surface):
    for roadType, ids in sheet.items():
        if surface in ids:
            return roadType
    return None
#Editing bridges in bridgeTileCache
def editBridge(cache=bridgeTileCache, tile=None, coord=(0,0), bridgeNumber=0):
    if bridgeNumber not in cache:
        cache[bridgeNumber] = []
    cache[bridgeNumber].append([coord, tile])
    bridgeCollision(cache)

#Deleting entire bridges from bridgeTileCache and updating roadTileCache
def deleteBridge(cache=bridgeTileCache, bridgeNumber=0):
    if bridgeNumber not in cache:
        return

    for coord, tile in cache[bridgeNumber]:
        if coord in roadTileCache:
            roadTileCache[coord] = [
                t for t in roadTileCache[coord] if t != tile
            ]
            if not roadTileCache[coord]:
                del roadTileCache[coord]
    del cache[bridgeNumber]

#Detects bridge collision
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

#Locates the bridge number if it has a tile in contains
def bridgeLocate(cache=bridgeTileCache, contains=(0, 0)):
    for bridgeNumber, tiles in bridgeTileCache.items():
        for coord, tile in tiles:
            if coord == contains:
                return bridgeNumber
    return None

#Updates roadTileMapping for tile changing/orientations
def roadMapping(sheet=tileData):
    for y, row in enumerate(sheet):
        for x, tileId in enumerate(row):
            if tileId != -1:
                tile = getTileCached(tilesetRoad, tileId)
                if tile not in roadTileMapping[x]:
                    roadTileMapping[x].append(tile)

#Updates the map to show the roads placed
def drawRoad(sheet=roadTileCache, mouseCoord=(0, 0)):
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
            if tile is None: 
                continue  
            if tile in roadId:
                if (gridXTile, gridYTile) != mouseCoord:
                    screen.blit(tile, coord)
                elif (gridXTile, gridYTile) == mouseCoord and currentRoad is None:
                    screen.blit(tile, coord)
            elif tile not in roadId:
                if [coord, tile] in hiddenTiles: 
                    continue
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

    bridgeNumber = bridgeLocate(bridgeTileCache, contains=mouseCoord)
    if bridgeNumber is not None and isWater:
        deleteBridge(bridgeTileCache, bridgeNumber)
    elif mouseCoord in roadTileCache:
        roadTileCache[mouseCoord] = [
            tile for tile in roadTileCache[mouseCoord] if tile in bridgePart
        ]
        if not roadTileCache[mouseCoord]:
            del roadTileCache[mouseCoord]

# Building Placement
global validTiles, buildingCache
buildingCache = {}
validTiles = []  

#Updates buildingCache with random building coordinates
def placeBuilding(sheet=validTiles, depots=1, factories=1):
    buildingCache = {}
    if not validTiles or len(validTiles) < depots+factories: 
        print("Insufficent valid tiles")
        return
    availableTiles = validTiles.copy()
    factoryPositions = []

    for _ in range(factories):  
        buildingPos = random.choice(availableTiles)
        availableTiles.remove(buildingPos)
        factoryPositions.append(buildingPos)
        buildingCache[buildingPos] = getTileById(tilesetBuilding, 4)

    for factoryPos in factoryPositions:
        factoryX, factoryY = factoryPos
        tilesToRemove = []
        for tile in availableTiles:
            tileX, tileY = tile
            if abs(tileX - factoryX) <= tileSize and abs(tileY - factoryY) <= tileSize:
                tilesToRemove.append(tile)
        
        for tile in tilesToRemove:
            if tile in availableTiles:
                availableTiles.remove(tile)

    if len(availableTiles) < depots:
        print("Insufficient valid tiles for depots after factory placement restrictions")
        return

    for _ in range(depots):
        buildingPos = random.choice(availableTiles)
        availableTiles.remove(buildingPos)

        tileId = random.randint(0, 3)
        buildingCache[buildingPos] = getTileById(tilesetBuilding, tileId)

    drawBuildings()
    return buildingCache

#Draws building to map
def drawBuildings():
    for pos, tile in buildingCache.items(): # type: ignore # type: ignore
        screen.blit(tile, pos)

#Updates validTiles with tiles that do not have a water tile within 3x3 tile range
def validBuildingTiles():
    validTiles = []  
    
    for y in range(mapHeight):
        for x in range(mapWidth):
            if mapData[y][x] in range(12, 17):
                continue

            validLocation = True
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    adjX, adjY = x + dx, y + dy
                    if 0 <= adjX < mapWidth and 0 <= adjY < mapHeight:
                        if mapData[adjY][adjX] in range(12, 17):
                            validLocation = False
                            break
                if not validLocation:
                    break
            
            if validLocation and (x * tileSize, y * tileSize) not in [(416, 32),(384, 32),(352, 32)]: #Exit, Settings, Submit button doesn't appear in validTiles
                validTiles.append((x * tileSize, y * tileSize))
    return validTiles

validConnections = {
    (0, 0):["N", "S"],
    (0, 1):["W", "E"],
    (1, 0):["W", "S"],
    (1, 1):["W", "N"],
    (1, 2):["N", "E"],
    (1, 3):["E", "S"],
    (2, 0):["N", "W", "S"],
    (2, 1):["W", "N", "E"],
    (2, 2):["N", "E", "S"],
    (2, 3):["W", "E", "S"],
    (3, 0):["N", "E", "S", "W"],
    (3, 1):["N", "E", "S", "W"],
    (4, 0):["N", "S"],
    (4, 1):["E", "W"],
    (5, 0):["N", "S"],
    (5, 1):["E", "W"]
}

pathWeights = {
    (0, 1, 2, 3): 1.5, # Roads have 1.5x Cost
    (4, 5): 2} # Bridges have 2x Cost

# Check if all deports/factories are connected via a valid path
def validPath():
    depot = []
    factory = []

    buildingTypeCache = {}
    for coord, building in buildingCache.items():
        for tileId in range(5):  # 0-3 are depots, 4 is factory
            reference_tile = getTileById(tilesetBuilding, tileId)
            if (building.get_size() == reference_tile.get_size() and 
                building.get_at((16, 16)) == reference_tile.get_at((16, 16))):  # Sample center pixel
                buildingTypeCache[coord] = tileId
                break
    
    # Categorize buildings
    for coord, tileId in buildingTypeCache.items():
        if tileId in range(4):  # Depot tiles (0-3)
            depot.append(coord)
        elif tileId == 4:  # Factory tile
            factory.append(coord)

    print(f"Debug: Found {len(factory)} factories and {len(depot)} depots")
    print(f"Factories at: {factory}")
    print(f"Depots at: {depot}")
    
    if not factory or not depot:
        print("Debug: Missing factories or depots")
        return False

    directions = {
        "N": (0, -tileSize),
        "S": (0, tileSize),
        "E": (tileSize, 0),
        "W": (-tileSize, 0)
    }

    for factoryPos in factory:
        foundDepot = False
        visited = set()
        queue = deque([factoryPos])

        while queue:
            x, y = queue.popleft()
            if (x, y) in visited:
                continue
            visited.add((x, y))

            if (x, y) in depot:
                foundDepot = True
                break

            if (x, y) in buildingCache:
                for direction in directions.values():
                    nx, ny = x + direction[0], y + direction[1]
                    if 0 <= nx < mapWidth * tileSize and 0 <= ny < mapHeight * tileSize:
                        if (nx, ny) not in visited:
                            if (nx, ny) in roadTileCache or (nx, ny) in buildingCache:
                                queue.append((nx, ny))
            
            # If we're on a road tile, check valid connections
            elif (x, y) in roadTileCache:
                # Find what type of road tile this is
                roadTile = roadTileCache[(x, y)][0] if roadTileCache[(x, y)] else None
                if roadTile:
                    # Find the road type and orientation
                    rType = None
                    roadOrientation = None
                    
                    for rType, tiles in roadTileMapping.items():
                        if roadTile in tiles:
                            rType = rType
                            roadOrientation = tiles.index(roadTile)
                            break
                    
                    # Get valid connections for this road tile
                    if rType is not None and (rType, roadOrientation) in validConnections:
                        connections = validConnections[(rType, roadOrientation)]
                        
                        for direction in connections:
                            if direction in directions:
                                nx, ny = x + directions[direction][0], y + directions[direction][1]
                                if 0 <= nx < mapWidth * tileSize and 0 <= ny < mapHeight * tileSize:
                                    if (nx, ny) not in visited:
                                        if (nx, ny) in roadTileCache or (nx, ny) in buildingCache:
                                            queue.append((nx, ny))

        if not foundDepot:
            print(f"Debug: Factory at {factoryPos} could not reach any depot")
            return False
        else:
            print(f"Debug: Factory at {factoryPos} successfully connected to depot")
    return True    

            





# Calculate the score
def calculateScore():
    pass


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

index = 0
state = "menu"
mapData = loadData(riverBasinURL)
roadMapping()

playRect = pygame.Rect(tileSize * 6, tileSize * 8, tileSize * 3, tileSize)
logoRect = pygame.Rect(tileSize * 5, tileSize * 4, tileSize * 5, tileSize * 2)
exitRect = pygame.Rect(tileSize * 13, tileSize * 1, tileSize, tileSize)
submitRect = pygame.Rect(tileSize * 11, tileSize * 1, tileSize, tileSize)
settingsRect = pygame.Rect(tileSize * 12, tileSize * 1, tileSize, tileSize)

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
                    mapData = loadData(riverBasinURL)
                    state = "menu"
                    roadTileCache.clear()
                    bridgeTileCache.clear()
                elif state == "menu":
                    running = False
            elif settingsRect.collidepoint(event.pos):
                print("Settings currently not added into the game. Sorry!")
            elif submitRect.collidepoint(event.pos):
                print(validPath())
                #ADD CODE HERE LATER FOR GAME END
            elif state == "menu" and playRect.collidepoint(event.pos):
                mapData = loadData(riverBasinURL) # LOAD MAP HERE FOR GAME
                validTiles = validBuildingTiles()
                buildingCache = placeBuilding(sheet=validTiles, depots=2, factories=2)
                state = "game"
            elif state == "game" and currentMode == "building":
                # Update roadTileMapping for placement cache
                if currentRoad is None:
                    print("Currently placing nothing.")
                    continue
                elif (gridX, gridY) in buildingCache.keys(): # type: ignore
                    print("Cannot place on depot/factory.")
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
                            screen.blit(getTileCached(tilesetLand, idTile), (32, 32))
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

                # Update roadTileCache to reflect changes
                isWater = mapData[gridY // tileSize][gridX // tileSize] in range(12, 17)
                isBridge = index in [4, 5]
                roadId = [item for i in range(4) for item in roadTileMapping[i]]

                if index not in [4, 5]:
                    if not isWater and not isBridge:
                        presentTiles = roadTileCache.get((gridX, gridY), [])
                        bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                        roadTileCache[(gridX, gridY)] = [currentRoad] + bridgeTiles
                    else:
                        print(placementError)
                elif index in [4, 5] and isWater and isBridge and isValid:
                    currentIndex = roadTileMapping[index].index(currentRoad)
                    if index == 4:
                        if currentIndex == 0:
                            for i in range(-1, 2):
                                pos = (gridX, gridY + tileSize * i)
                                presentTiles = roadTileCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTileCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                        elif currentIndex == 3:
                            for i in range(-1, 2):
                                pos = (gridX - tileSize * i, gridY)
                                presentTiles = roadTileCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTileCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                    elif index == 5:
                        if currentIndex == 0:
                            for i in range(-1, 3):
                                pos = (gridX, gridY + tileSize * i)
                                presentTiles = roadTileCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTileCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                        elif currentIndex == 4:
                            for i in range(-1, 3):
                                pos = (gridX - tileSize * i, gridY)
                                presentTiles = roadTileCache.get(pos, [])
                                bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
                                newRoad = roadTileMapping[index][currentIndex + i + 1]
                                if newRoad not in bridgeTiles:
                                    roadTileCache[pos] = [newRoad] + presentTiles
                                    editBridge(bridgeTileCache, newRoad, pos, bridgeNumber)
                else: 
                    print(placementError)
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
                        if index == 4: 
                            step = 3
                        elif index == 5: 
                            step = 4
                        else: 
                            step = 1

                        nextIndex = (currentIndex + step) % len(roadTileMapping[index])
                        currentRoad = roadTileMapping[index][nextIndex]
                    except (ValueError, IndexError):
                        currentRoad = None
                elif event.key == pygame.K_q:
                    currentRoad = None

    if state == "game":
        hiddenBridges = list()
        # Road Drawing to cursor
        drawMap(tilesetLand)
        drawBuildings()

        # Tile outline
        if (not exitRect.collidepoint(mouseX, mouseY) 
            and not settingsRect.collidepoint(mouseX, mouseY) 
            and not submitRect.collidepoint(mouseX, mouseY)):
            if (gridX, gridY) in buildingCache.keys(): # type: ignore
                pygame.draw.rect(screen, (255,223,186), outlineRect, width=1) #Hovering over building
            elif currentMode == "building":
                pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)
            elif currentMode == "deleting":
                if not timer.running:
                    timer.start()
                if timer.elapsed() <= 0.175:
                    pygame.draw.rect(screen, (255,179,186), outlineRect, width=1) # Delete mode
                else:
                    timer.reset()
                    timer.stop()
                    currentMode = "building"
                    pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)


        # Tile bilt current tile onto screen (cursor)
        if (currentRoad and not exitRect.collidepoint(mouseX, mouseY) 
            and not settingsRect.collidepoint(mouseX, mouseY) 
            and not submitRect.collidepoint(mouseX, mouseY)):
            
            if (gridX, gridY) in buildingCache.keys(): # type: ignore
                continue
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
            elif bridgeLocate(contains=(gridX, gridY)) is None or (
                mapData[gridY // tileSize][gridX // tileSize] not in range(12, 17)
            ):
                screen.blit(currentRoad, (gridX, gridY))

        drawRoad(roadTileCache, (gridX, gridY))


    elif state == "menu":
        # Play Button
        drawMap(tilesetLandDark) 
        buttonTiles = range(3) if playRect.collidepoint(mouseX, mouseY) else range(3, 6)
        for i, tileIndex in enumerate(buttonTiles):
            screen.blit(getTileCached(tilesetUI, tileIndex), 
                      (playRect.x + i * tileSize, playRect.y))

        # Logo
        tileIndex = 0
        for iy in range(2):
            for ix in range(6):
                screen.blit(getTileCached(tilesetLogoUI, tileIndex),
                            (logoRect.x + ix * tileSize, logoRect.y + iy * tileSize))
                tileIndex += 1

    exitTile = 6 if exitRect.collidepoint(mouseX, mouseY) else 7 #Exit Button
    screen.blit(getTileCached(tilesetUI, exitTile), exitRect.topleft)
    settingTile = 8 if settingsRect.collidepoint(mouseX, mouseY) else 9 #Setting Button
    screen.blit(getTileCached(tilesetUI, settingTile), settingsRect.topleft)

    if state == "game":
        submitTile = 10 if submitRect.collidepoint(mouseX, mouseY) else 11
        screen.blit(getTileCached(tilesetUI, submitTile), submitRect.topleft)
    pygame.display.flip()
pygame.quit()