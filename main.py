import pygame, requests, io, sys, csv, random 
from collections import deque
import heapq

# Asset Urls
tilesetLandURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetLand.png"
tilesetLandDarkURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetLandDark.png"

tilesetRoadURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetRoad.png"
tilesetRoadIDURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Road%20Tileset%20ID.csv"
tilesetBuildingURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetBuildings.png"

buttonUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/cee5f3844e0ef08f5e27d42df372283ab2b00162/Button%20UI.png"
logoUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Logo%20UI.png"
fontBoldURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/0c43d5e83145e5ffc92996eb2f8b1b69f19f0a06/Fredoka-Bold.ttf"
fontMediumURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/3e6f66167a9a4ce12c985c05f67b5604e6672751/Fredoka-Medium.ttf"
fontSemiBoldURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/3e6f66167a9a4ce12c985c05f67b5604e6672751/Fredoka-SemiBold.ttf"

riverBasinURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/River%20Basin%20Level.csv"
greenPlainsURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/8cb308005606b15c108ff675a13e9b1022fd1ada/Green%20Plains.csv"
testPlainsURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Test%20Plains.csv"

# Initialization
pygame.init()
pygame.display.set_caption("Supply Chains")
clock = pygame.time.Clock()
tileSize = 32
avaliableMaps = [riverBasinURL, greenPlainsURL]

fontBold = pygame.font.Font(io.BytesIO(requests.get(fontBoldURL).content), 65)
fontSemiBold = pygame.font.Font(io.BytesIO(requests.get(fontSemiBoldURL).content), 16)

global currentRoad, hiddenBridges
placementError = "You cannot place here."

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

pygame.display.set_icon(loadImage(
    "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/72a0b726fe279470a5b22a9f5aea50df0028eee2/WindowIcon.png"
    ))

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

def drawMap(sheet):
    for y, row in enumerate(mapData):
        for x, tileId in enumerate(row):
            if (x, y) in buildingCache.keys():
                continue
            tile = getTileCached(sheet, tileId)
            screen.blit(tile, (x * tileSize, y * tileSize))

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

def editBridge(cache=bridgeTileCache, tile=None, coord=(0,0), bridgeNumber=0):
    if bridgeNumber not in cache:
        cache[bridgeNumber] = []
    cache[bridgeNumber].append([coord, tile])
    bridgeCollision(cache)

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

def deleteRoad(mouseCoord=(0, 0)):
    global currentRoad
    currentRoad = None

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

global validTiles, buildingCache
buildingCache = {}
validTiles = []  

def placeBuilding(sheet=validTiles, depots=1, factories=1):
    buildingCache = {}
    if not validTiles or len(validTiles) < depots+factories: 
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
        return

    for _ in range(depots):
        buildingPos = random.choice(availableTiles)
        availableTiles.remove(buildingPos)

        tileId = random.randint(0, 3)
        buildingCache[buildingPos] = getTileById(tilesetBuilding, tileId)

    drawBuildings()
    return buildingCache

def drawBuildings():
    for pos, tile in buildingCache.items():
        screen.blit(tile, pos)

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
            
            if validLocation and (x * tileSize, y * tileSize) not in [(416, 32),(384, 32),(352, 32),(32,32)]:
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
    (4, 0):[],
    (4, 1):["N", "S"],
    (4, 2):[],
    (4, 3):[],
    (4, 4):["W", "E"],
    (4, 5):[],
    (5, 0):[],
    (5, 1):["N", "S"],
    (5, 2):["N", "S"],
    (5, 3):[],
    (5, 4):[],
    (5, 5):["W", "E"],
    (5, 6):["W", "E"],
    (5, 7):[]
}

pathWeights = {
    (0, 1, 2, 3): 1.5,
    (4, 5): 2
}

def validPath():
    roadId = [item for i in range(4) for item in roadTileMapping[i]]   
    bridgeId = [roadTileMapping[5][i] for i in [1, 2, 5, 6]] + [roadTileMapping[4][i] for i in [1, 4]]
    factoryTile = getTileById(tilesetBuilding, 4)
    depots = []
    factories = []

    for (px, py), tile in buildingCache.items():
        if pygame.image.tostring(factoryTile, 'RGBA') == pygame.image.tostring(tile, 'RGBA'):
            factories.append((px, py))
        else:
            depots.append((px, py))

    if not factories or not depots:
        return False

    oppositeDirections = {"N": "S", "S": "N", "E": "W", "W": "E"}
    directionMapping = {
        "N": (0, -tileSize),
        "S": (0, tileSize),
        "E": (tileSize, 0),
        "W": (-tileSize, 0)
    }
    
    factoryHasValidPath = {factory: False for factory in factories}
    for factory in factories:
        visited = set()
        queue = deque([factory])
        found = False
        visited.add(factory)
        
        while queue:
            currentTile = queue.popleft()
            
            if currentTile in depots:
                found = True
                factoryHasValidPath[factory] = True
                break
            if currentTile in factories and currentTile != factory:
                continue

            isFactory = currentTile == factory
            for direction, (dx, dy) in directionMapping.items():
                neighborX, neighborY = currentTile[0] + dx, currentTile[1] + dy
                neighborTile = (neighborX, neighborY)
                
                if not (0 <= neighborX < mapWidth * tileSize and 0 <= neighborY < mapHeight * tileSize) or neighborTile in visited:
                    continue
                if neighborTile in factories and neighborTile != factory:
                    continue
                
                if isFactory:
                    if neighborTile not in roadTileCache:
                        continue
                        
                    roadConnected = False
                    for roadTile in roadTileCache[neighborTile]:
                        if roadTile not in roadId and roadTile not in bridgeId:
                            continue
                            
                        roadTypeCoord = None
                        for key, tiles in roadTileMapping.items():
                            if roadTile in tiles:
                                roadTypeCoord = (key, tiles.index(roadTile))
                                break
                                
                        if not roadTypeCoord or roadTypeCoord not in validConnections:
                            continue
                            
                        validDirs = validConnections[roadTypeCoord]
                        oppositeDir = oppositeDirections[direction]
                        
                        if oppositeDir in validDirs:
                            roadConnected = True
                            break
                    
                    if roadConnected:
                        visited.add(neighborTile)
                        queue.append(neighborTile)
                
                elif currentTile in roadTileCache:
                    currentRoadConnections = set()
                    for currentRoadTile in roadTileCache[currentTile]:
                        if currentRoadTile not in roadId and currentRoadTile not in bridgeId:
                            continue
                            
                        currentRoadTypeCoord = None
                        for key, tiles in roadTileMapping.items():
                            if currentRoadTile in tiles:
                                currentRoadTypeCoord = (key, tiles.index(currentRoadTile))
                                break
                                
                        if not currentRoadTypeCoord or currentRoadTypeCoord not in validConnections:
                            continue
                        currentRoadConnections.update(validConnections[currentRoadTypeCoord])

                    if direction not in currentRoadConnections:
                        continue

                    if neighborTile in depots:
                        found = True
                        factoryHasValidPath[factory] = True
                        break
                    
                    elif neighborTile in roadTileCache:
                        neighborRoadConnected = False
                        for neighborRoadTile in roadTileCache[neighborTile]:
                            if neighborRoadTile not in roadId and neighborRoadTile not in bridgeId:
                                continue
                                
                            neighborRoadTypeCoord = None
                            for key, tiles in roadTileMapping.items():
                                if neighborRoadTile in tiles:
                                    neighborRoadTypeCoord = (key, tiles.index(neighborRoadTile))
                                    break
                                    
                            if not neighborRoadTypeCoord or neighborRoadTypeCoord not in validConnections:
                                continue
                            neighborValidDirs = validConnections[neighborRoadTypeCoord]
                            oppositeDir = oppositeDirections[direction]
                            if oppositeDir in neighborValidDirs:
                                neighborRoadConnected = True
                                break
                        if neighborRoadConnected:
                            visited.add(neighborTile)
                            queue.append(neighborTile)
        if not found:
            return False
    return all(factoryHasValidPath.values())


global timer, speed
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
        return (pygame.time.get_ticks() - self.startTime) / 1000.0
    
def calculateScore():
    #Was going to use A* pathfinding algorthim and compare to the player's route to calculate score but it was too hard
    if not speed.running:
        return 0
    timeTaken = speed.elapsed()
    baseScore = 9999
    timePenalty = timeTaken * 25.0  
    variation = random.randint(-50, 50)
    finalScore = int(baseScore - timePenalty + variation)
    return max(1, min(9999, finalScore))

timer = Timer()
speed = Timer()
running = True
currentRoad = None
currentMode = "building"

index = 0
state = "menu"
prevState = str()
mapData = loadData(riverBasinURL)
roadMapping()

playRect = pygame.Rect(tileSize * 6, tileSize * 8, tileSize * 3, tileSize)
logoRect = pygame.Rect(tileSize * 5, tileSize * 4, tileSize * 5, tileSize * 2)
exitRect = pygame.Rect(tileSize * 13, tileSize * 1, tileSize, tileSize)
submitRect = pygame.Rect(tileSize * 11, tileSize * 1, tileSize, tileSize)
settingsRect = pygame.Rect(tileSize * 12, tileSize * 1, tileSize, tileSize)
helpRect = pygame.Rect(tileSize * 1, tileSize * 1, tileSize, tileSize)

while running:
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

            if exitRect.collidepoint(event.pos):
                if state == "game":
                    mapData = loadData(riverBasinURL)
                    state = "menu"
                    roadTileCache.clear()
                    bridgeTileCache.clear()
                    currentRoad = None
                elif state == "menu":
                    running = False
                elif state == "help":
                    state = prevState
            elif settingsRect.collidepoint(event.pos):
                print("Settings currently not added into the game. Sorry!")
            elif helpRect.collidepoint(event.pos):
                if state != "help":
                    prevState = state
                    state = "help"
                else:
                    state = prevState
            elif submitRect.collidepoint(event.pos):
                isValid = validPath()
                if isValid:
                    drawMap(tilesetLandDark)
                    score = calculateScore()
                    scoreText = fontBold.render(f"{score}", True, (232, 207, 166))
                    fontSemiBold = pygame.font.Font(io.BytesIO(requests.get(fontSemiBoldURL).content), 12)
                    scoreDescription = fontSemiBold.render(f"Congratulations, you have beaten Supply Chains!", True, (232, 207, 166))

                    screen.blit(scoreText, (tileSize * 5.5, tileSize * 4))
                    screen.blit(scoreDescription, (tileSize * 3.5, tileSize * 6))
                    
                    pygame.display.flip()
                    pygame.time.wait(2500)

                    state = "menu"
                    roadTileCache.clear()
                    bridgeTileCache.clear()
                    currentRoad = None
                    speed.reset()
                else:
                    print("You have not connected all factories to at least one depot. " \
                          "Please try again.")
            elif state == "menu" and playRect.collidepoint(event.pos):
                speed.start()
                mapData = loadData(random.choice(avaliableMaps))
                validTiles = validBuildingTiles()
                buildingCache = placeBuilding(sheet=validTiles, depots=random.randint(1,2), factories=random.randint(2,3))
                state = "game"
            elif state == "game" and currentMode == "building":
                if currentRoad is None:
                    print("Currently placing nothing.")
                    continue
                elif (gridX, gridY) in buildingCache.keys():
                    print("Cannot place on depot/factory.")
                    continue
                bridgeNumber = 0 if not bridgeTileCache else max(bridgeTileCache.keys()) + 1
                isValid = False
                isLand = []

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
        drawMap(tilesetLand)
        drawBuildings()

        if (not exitRect.collidepoint(mouseX, mouseY) 
            and not helpRect.collidepoint(mouseX, mouseY) 
            and not submitRect.collidepoint(mouseX, mouseY)
            and not settingsRect.collidepoint(mouseX, mouseY)):
            if (gridX, gridY) in buildingCache.keys():
                pygame.draw.rect(screen, (255,223,186), outlineRect, width=1)
            elif currentMode == "building":
                pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)
            elif currentMode == "deleting":
                if not timer.running:
                    timer.start()
                if timer.elapsed() <= 0.175:
                    pygame.draw.rect(screen, (255,179,186), outlineRect, width=1)
                else:
                    timer.reset()
                    timer.stop()
                    currentMode = "building"
                    pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)

        if (currentRoad and not exitRect.collidepoint(mouseX, mouseY) 
            and not helpRect.collidepoint(mouseX, mouseY) 
            and not submitRect.collidepoint(mouseX, mouseY)
            and not settingsRect.collidepoint(mouseX, mouseY)):
            
            if (gridX, gridY) in buildingCache.keys():
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
        drawMap(tilesetLandDark) 
        buttonTiles = range(3) if playRect.collidepoint(mouseX, mouseY) else range(3, 6)
        for i, tileIndex in enumerate(buttonTiles):
            screen.blit(getTileCached(tilesetUI, tileIndex), 
                      (playRect.x + i * tileSize, playRect.y))

        tileIndex = 0
        for iy in range(2):
            for ix in range(6):
                screen.blit(getTileCached(tilesetLogoUI, tileIndex),
                            (logoRect.x + ix * tileSize + 0.5 * tileSize, logoRect.y + iy * tileSize))
                tileIndex += 1

    elif state == "help":
        fontSemiBold = pygame.font.Font(io.BytesIO(requests.get(fontSemiBoldURL).content), 12)
        drawMap(tilesetLandDark)
        helpLines = [
            "To win connect all factories to at least one depot.",
            "",
            "Controls:",
            "  Number Keys 1-6 to choose between 6 different tiles to construct your network.",
            "  \"R\" Key to rotate your current tile clockwise.",
            "  \"Q\" Key to cancel current selection.",
            "  Left click to place tile.",
            "  Right click to delete the current tile under the cursor.",
            "",
            "Once complete click on the \"CheckMark\" button to submit network for a score.",
        ]

        screenCenterX = screen.get_width() // 2
        screenCenterY = screen.get_height() // 2
        lineHeight = fontSemiBold.get_height() + 4
        totalTextHeight = len(helpLines) * lineHeight
        startY = screenCenterY - (totalTextHeight // 2)

        for i, line in enumerate(helpLines):
            if line.strip():
                textSurface = fontSemiBold.render(line, True, (232, 207, 166))
                textX = screenCenterX - 220
                textY = startY + (i * lineHeight)
                screen.blit(textSurface, (textX, textY))

    exitTile = 6 if exitRect.collidepoint(mouseX, mouseY) else 7
    screen.blit(getTileCached(tilesetUI, exitTile), exitRect.topleft)

    helpTile = 12 if helpRect.collidepoint(mouseX, mouseY) else 13
    screen.blit(getTileCached(tilesetUI, helpTile), helpRect.topleft)

    settingTile = 8 if settingsRect.collidepoint(mouseX, mouseY) else 9
    screen.blit(getTileCached(tilesetUI, settingTile), settingsRect.topleft)

    if state == "game":
        submitTile = 10 if submitRect.collidepoint(mouseX, mouseY) else 11
        screen.blit(getTileCached(tilesetUI, submitTile), submitRect.topleft)
    pygame.display.flip()
pygame.quit()
