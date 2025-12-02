import os
from shutil import ExecError
import pygame, requests, io, sys, csv, random, time, math
from collections import deque
from typing import Union
from helper import Slider

# Known PROBLEMS
    # none so far (not going to last ahh)

# Nice additions
    # Somehow have a default tile that loads if out of range

# Resource URLs
tilesetLandURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetLand.png"
tilesetLandDarkURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetLandDark.png"

tilesetRoadURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/TilesetRoad.png"
tilesetRoadIDURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Road%20Tileset%20ID.csv"
tilesetBuildingURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/8c426093138d61f43419abfce808298be9692312/TilesetBuildings.png"

buttonsUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/cee5f3844e0ef08f5e27d42df372283ab2b00162/Button%20UI.png"
logoUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Logo%20UI.png"
helpUIURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/4df75d12b5bf19091e2fb8ca04542f0e64815140/assets/HelpUI.png"
iconURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/72a0b726fe279470a5b22a9f5aea50df0028eee2/WindowIcon.png"
mouseCursorURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/95f8b9d3b7fae8e6f7d5523a4b13d4c7172878a2/assets/Downloaded%20Sprites/Sprout%20Lands%20-%20UI%20Pack%20-%20Basic%20pack/Sprite%20sheets/Mouse%20sprites/Triangle%20Mouse%20icon%201.png"

fontBoldURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/0c43d5e83145e5ffc92996eb2f8b1b69f19f0a06/Fredoka-Bold.ttf"
fontMediumURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/3e6f66167a9a4ce12c985c05f67b5604e6672751/Fredoka-Medium.ttf"
fontSemiBoldURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/3e6f66167a9a4ce12c985c05f67b5604e6672751/Fredoka-SemiBold.ttf"

riverBasinURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/River%20Basin%20Level.csv"
greenPlainsURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/8cb308005606b15c108ff675a13e9b1022fd1ada/Green%20Plains.csv"
riverDeltaURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/2fdc5f39cdf85729290c755cf51fc82b6d862941/maps/River%20Delta.csv"
islandURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/2fdc5f39cdf85729290c755cf51fc82b6d862941/maps/Island.csv"
testPlainsURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/956e14ebfc0ec45c8b5df008f392ba7726a613f3/Test%20Plains.csv"

placeSoundURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/f9f5c11b34380495f29bbaa102df044557aaf69e/Place.mp3"
errorSoundURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/f9f5c11b34380495f29bbaa102df044557aaf69e/Error.mp3"
clickSoundURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/f9f5c11b34380495f29bbaa102df044557aaf69e/Click.mp3"
loadingSoundURL = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/1cd216497dbfcc9d9ce2fae17f31cceba660028f/Loading.mp3"

# Map drawing functions and tile caching
def getTileById(sheet, tileId: int) -> pygame.Surface:
    cols = sheet.get_width() // tileSize
    x = (tileId % cols) * tileSize
    y = (tileId // cols) * tileSize
    tile = pygame.Surface((tileSize, tileSize), pygame.SRCALPHA)
    tile.blit(sheet, (0, 0), (x, y, tileSize, tileSize))
    return tile

# Tile cache to optimize tile retrieval
global tileCache
tileCache = {}

# Retrieves tile from cache or loads it if not present /w alpha support
def getTileCached(sheet, tileId: int, alpha: int=255) -> pygame.Surface:
    alpha = int(max(0, min(255, alpha)))  # Clamp alpha between 0 and 255
    key = (id(sheet), tileId, alpha)
    if key in tileCache:
        return tileCache[key]

    baseKey = (id(sheet), tileId, 255)
    if baseKey in tileCache: baseTile = tileCache[baseKey]
    else: 
        baseTile = getTileById(sheet, tileId)
        try:
            baseTile = baseTile.convert_alpha()
        except Exception:
            pass
        tileCache[baseKey] = baseTile

    if alpha == 255: tile = baseTile
    else:
        tile = baseTile.copy()
        try:
            tile = tile.convert_alpha()
        except Exception:
            pass
        tile.fill((255, 255, 255, alpha), special_flags=pygame.BLEND_RGBA_MULT)
    tileCache[key] = tile
    return tile

# Draws the map onto the screen, skipping tiles with buildings
def drawMap(tileset: pygame.Surface):
    for y, row in enumerate(mapData):
        for x, tileId in enumerate(row):
            if buildingCache == None: raise ExecError
            if x < 0 or x >= mapWidth or y < 0 or y >= mapHeight:
                tile = getTileCached(tileset, 16)
                screen.blit(tile, (x * tileSize, y * tileSize))
            else:
                if (x, y) in buildingCache.keys():
                    continue
                tile = getTileCached(tileset, tileId)
                screen.blit(tile, (x * tileSize, y * tileSize))

# Road and bridge editing functions
global bridgeTileCache, roadTileCache, roadTileMapping
bridgeTileCache = {}; dict[tuple[int, int], list[pygame.Surface]]
roadTileCache = {}; dict[tuple[int, int], list[pygame.Surface]] # Coordinates mapped to list of road tiles (not grid coordinates)
roadTileMapping = {
    0: [], # Straight 
    1: [], # Corner 
    2: [], # T-Junction 
    3: [], # Intersection 
    4: [], # Short-Bridge 
    5: [], # Long-Bridge
}

# Edits bridge tiles and manages collisions
def editBridge(tile: pygame.Surface, coord: tuple[int, int]=(0,0), bridgeNumber: int=0):
    if bridgeNumber not in bridgeTileCache:
        bridgeTileCache[bridgeNumber] = []
    bridgeTileCache[bridgeNumber].append([coord, tile])
    bridgeCollision()

# Deletes a bridge and its associated bridge tiles
def deleteBridge(bridgeNumber: int=0):
    if bridgeNumber not in bridgeTileCache:
        return

    for coord, tile in bridgeTileCache[bridgeNumber]:
        if coord in roadTileCache:
            roadTileCache[coord] = [
                t for t in roadTileCache[coord] if t != tile
            ]
            if not roadTileCache[coord]:
                del roadTileCache[coord]
    del bridgeTileCache[bridgeNumber]

# Manages bridge tile collisions to prevent overlapping bridges
def bridgeCollision():
    removeTile = dict()
    removeBridge = set()
    index = sorted(bridgeTileCache.keys())

    for i in index:
        tiles = bridgeTileCache[i]
        for pos, tile in tiles:
            if tile in [roadTileMapping[4][i] for i in [0, 2, 3, 5]] + [roadTileMapping[5][i] for i in [0, 3, 4, 7]]:
                continue
            elif pos in removeTile:
                removeBridge.add(removeTile[pos])
            removeTile[pos] = i

    for bridge in removeBridge:
        if bridge in bridgeTileCache:
            deleteBridge(bridge)

# Locates a bridge number based on tile coordinates
def bridgeLocate(contains: tuple[int, int]) -> Union[int, None]:
    for bridgeNumber, tiles in bridgeTileCache.items():
        for coord, tile in tiles:
            if coord == contains:
                return bridgeNumber
    return None

# Maps road tile IDs to their corresponding surfaces
def roadMapping():
    for y, row in enumerate(tileLocationData):
        for x, tileId in enumerate(row):
            if tileId != -1:
                tile = getTileCached(tilesetRoad, tileId)
                if tile not in roadTileMapping[x]:
                    roadTileMapping[x].append(tile)

# Draws roads onto the map from the road tile cache
def drawRoad(mouseCoordGrid: tuple[int, int]=(0, 0)):
    global hiddenPreviewTiles
    roadSurfaces = [item for i in range(4) for item in roadTileMapping[i]]
    hiddenTiles = []
    if 'hiddenBridges' in globals() and hiddenBridges:
        for idBridge in hiddenBridges:
            if idBridge in bridgeTileCache:
                for coord, tile in bridgeTileCache[idBridge]:
                    hiddenTiles.append([coord, tile]) # List of tiles to hide (bridges) via id of bridge

    for coord, tiles in roadTileCache.items():
        tileGridX = (coord[0] // tileSize) * tileSize
        tileGridY = (coord[1] // tileSize) * tileSize

        for tile in tiles:
            if tile is None: 
                continue  
            if tile in roadSurfaces:
                # Hide underlying road tiles when a preview covers this grid cell
                if (tileGridX, tileGridY) in hiddenPreviewTiles:
                    continue
                if (tileGridX, tileGridY) != mouseCoordGrid:
                    screen.blit(tile, coord)
                elif (tileGridX, tileGridY) == mouseCoordGrid and currentRoad is None:
                    screen.blit(tile, coord)
            elif tile not in roadSurfaces:
                if [coord, tile] in hiddenTiles: 
                    continue
                screen.blit(tile, coord)

# Deletes road tiles or bridges at specified coordinates
def deleteRoad(mouseCoordGrid: tuple[int, int]=(0, 0)):
    global currentRoad
    currentRoad = None 
    
    try: 
        isWater = mapData[mouseCoordGrid[1] // tileSize][mouseCoordGrid[0] // tileSize] in range(12, 17)
    except IndexError:
        isWater = False

    bridgePart = (
        [roadTileMapping[5][i] for i in [0, 3, 4, 7]] +
        [roadTileMapping[4][i] for i in [0, 2, 3, 5]]
    )

    bridgeNumber = bridgeLocate(mouseCoordGrid)
    if bridgeNumber is not None and isWater: # If bridge exists at location and is over water
        deleteBridge(bridgeNumber)
    elif mouseCoordGrid in roadTileCache: # If no bridge, delete road tiles at location
        # Keep only bridge tiles; remove regular road tiles
        roadTileCache[mouseCoordGrid] = [
            tile for tile in roadTileCache[mouseCoordGrid] if tile in bridgePart
        ]
        if not roadTileCache[mouseCoordGrid]:
            del roadTileCache[mouseCoordGrid]

# Building placement functions
global validTiles, buildingCache
buildingCache = {}
validTiles = []  

# Randomly places buildings on the map based on parameters, returns a dictionary of building positions and their corresponding surfaces
def placeBuilding(depots=1, factories=1) -> dict[tuple[int, int], pygame.Surface]:
    global buildingCache
    buildingCache = {}
    validTiles = validBuildingTiles()
    if not validTiles or len(validTiles) < depots+factories: 
        return {}
    factoryPositions = []

    for _ in range(factories):  
        validTiles = validBuildingTiles()
        buildingPos = random.choice(validTiles)
        factoryPositions.append(buildingPos)
        buildingCache[buildingPos] = getTileById(tilesetBuilding, 4)

    validTiles = validBuildingTiles()
    if len(validTiles) < depots:
        return buildingCache

    for _ in range(depots):
        validTiles = validBuildingTiles()
        buildingPos = random.choice(validTiles)
        tileId = random.randint(0, 3)
        buildingCache[buildingPos] = getTileById(tilesetBuilding, tileId)

    drawBuildings()
    return buildingCache

# Draws buildings onto the map from the building cache
def drawBuildings():
    if buildingCache == None: raise ExecError
    for pos, tile in buildingCache.items():
        screen.blit(tile, pos)

# Searches the map for tiles where buildings can spawn
    # 1) Buildings cannot be placed in 3x3 area to other buildings
    # 2) Buildings cannot be placed on specific coordinates (used for UI elements)
    # 3) Buildings cannot be placed on water tiles (IDs 12-16)
def validBuildingTiles() -> list[tuple[int, int]]:
    validTiles = []  
    
    for y in range(mapHeight):
        for x in range(mapWidth):
            try:
                if mapData[y][x] in range(12, 17):
                    continue

                validLocation = True
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        if dy == dx == 0:
                            continue
                        adjX, adjY = x + dx, y + dy
                        if 0 <= adjX < mapWidth and 0 <= adjY < mapHeight:
                            if mapData[adjY][adjX] in range(12, 17):
                                validLocation = False
                                break
                            elif (buildingCache is not None) and ((adjX * tileSize, adjY * tileSize) in buildingCache):
                                validLocation = False
                                break
                    if not validLocation:
                        break
                
                if validLocation and (x * tileSize, y * tileSize) not in [(416, 32),(384, 32),(352, 32),(32,32)]:
                    validTiles.append((x * tileSize, y * tileSize))
            except IndexError:
                 pass
    return validTiles

# Defines valid road connections based on road tile types and orientations
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

# Defines weights for different path types (used for later pathfinding algorithms) soon™
pathWeights = {
    (0, 1, 2, 3): 1.5,
    (4, 5): 2
}

# Validates if all factories have a path to at least one depot
def validPath() -> bool:
    roadId = [item for i in range(4) for item in roadTileMapping[i]]   
    bridgeId = [roadTileMapping[5][i] for i in [1, 2, 5, 6]] + [roadTileMapping[4][i] for i in [1, 4]]
    factoryTile = getTileById(tilesetBuilding, 4)
    depots = []
    factories = []

    if buildingCache == None: raise ExecError
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
    
    # BFS to check path from each factory to any depot
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

# Function to load different types of data from URLs
def loadSound(url) -> pygame.mixer.Sound:
    try:
        response = requests.get(url)
        return pygame.mixer.Sound(io.BytesIO(response.content)) 
    except Exception as e:
        print(f"Error loading sound from {url}:", e)
        sys.exit()

def loadData(url) -> list[list[int]]:
    try:
        csvResp = requests.get(url).text
        csvReader = csv.reader(io.StringIO(csvResp))
        return [[int(cell) for cell in row if cell.strip() != ""] for row in csvReader]
    except Exception as e:
        print("CSV error:", e)
        sys.exit()

def loadImage(url) -> pygame.Surface:
    try:
        response = requests.get(url)
        return pygame.image.load(io.BytesIO(response.content)).convert_alpha()
    except Exception as e:
        print(f"Error loading image from {url}:", e)
        sys.exit()

# Initialize game resources /w loading screen
def initializeGame():
    def drawLoadingBar(progress: int, total: int, item: str):
        loadingBarOutlineRec = pygame.Rect(4 * tileSize, 8 * tileSize, 7 * tileSize, tileSize)
        loadingBarWidth = (progress / total) * (7 * tileSize)
        loadingBarRec = pygame.Rect(4 * tileSize, 8 * tileSize, loadingBarWidth, tileSize)
        fontSemiBold = pygame.font.Font(io.BytesIO(requests.get(fontSemiBoldURL).content), 14)
        text = fontSemiBold.render(f"Loading {item}: {round((progress / total) * 100, 1)}%", True, (232, 207, 166))

        pygame.draw.rect(screen, (0xe8, 0xcf, 0xa6), loadingBarRec, border_radius=10)
        if progress == 1:
            pygame.draw.rect(screen, (0xc6, 0x9d, 0x6f), loadingBarOutlineRec, 3, border_radius=5)
        else: pygame.draw.rect(screen, (0xc6, 0x9d, 0x6f), loadingBarOutlineRec, 3, border_radius=10)
        screen.blit(text, (tileSize * 4, tileSize * 7.25))

    global tilesetLand, tilesetLandDark, tilesetRoad, tilesetBuilding
    global buttonsUI, tilesetLogoUI, tilesetHelpUI
    global fontBold, fontSemiBold
    global tileLocationData, mapData, screen, mapHeight, mapWidth
    global placeSound, errorSound, clickSound, loadingSound

    # Load resources
    assets = [
        ("csv", "mapData", riverBasinURL), 
        ("other", "screen", "NONE"), 

        ("image", "tilesetLandDark", tilesetLandDarkURL),
        ("image", "tilesetLogoUI", logoUIURL),
        ("image", "buttonsUI", buttonsUIURL),
        ("image", "icon", iconURL),
        ("image", "mouseCursor", mouseCursorURL),

        ("image", "tilesetLand", tilesetLandURL),
        ("image", "tilesetRoad", tilesetRoadURL),
        ("image", "tilesetBuilding", tilesetBuildingURL),

        ("image", "tilesetHelpUI", helpUIURL),
        ("image", "tilesetUI", buttonsUIURL),
        ("csv", "tileLocationData", tilesetRoadIDURL),

        ("sound", "placeSound", placeSoundURL),
        ("sound", "errorSound", errorSoundURL),
        ("sound", "clickSound", clickSoundURL),
        ("sound", "loadingSound", loadingSoundURL),
    ]
    
    total = len(assets)
    for i, (typ, label, item) in enumerate(assets, start=1):
        if typ == "other" and item == "NONE":
            match label:
                case "screen": 
                    mapHeight = len(mapData)
                    mapHeight += inventory[1] if inventory[0] else 0
                    mapWidth = max(len(row) for row in mapData)
                    screen = pygame.display.set_mode((mapWidth * tileSize, mapHeight * tileSize))      
        else:
            if typ == "image":
                image = loadImage(item)
                match label:
                    case "tilesetLand": tilesetLand = image
                    case "tilesetLandDark": tilesetLandDark = image
                    case "tilesetRoad": tilesetRoad = image
                    case "tilesetBuilding": tilesetBuilding = image
                    case "tilesetHelpUI": tilesetHelpUI = image
                    case "tilesetUI": buttonsUI = image
                    case "buttonsUI": buttonsUI = image
                    case "tilesetLogoUI": tilesetLogoUI = image
                    case "icon": pygame.display.set_icon(image)
                    case "mouseCursor":
                        try:
                            pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), image))
                        except Exception:
                            pygame.mouse.set_cursor(pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))
            elif typ == "sound":
                sound = loadSound(item)
                match label:
                    case "placeSound": placeSound = sound
                    case "errorSound": errorSound = sound
                    case "clickSound": clickSound = sound
                    case "loadingSound": loadingSound = sound
            elif typ == "csv":
                csv = loadData(item)
                match label:
                    case "mapData": mapData = csv
                    case "tileLocationData": tileLocationData = csv
        try:
            screen.fill((144, 159, 84))
            drawMap(tilesetLandDark)
            tileIndex = 0
            for iy in range(2):
                for ix in range(6):
                    screen.blit(getTileCached(tilesetLogoUI, tileIndex),
                                (logoRect.x + ix * tileSize + 0.5 * tileSize, logoRect.y + iy * tileSize))
                    tileIndex += 1
                    
            screen.blit(getTileCached(buttonsUI, 7), exitRect.topleft)
            screen.blit(getTileCached(buttonsUI, 13), helpRect.topleft)
            screen.blit(getTileCached(buttonsUI, 9), settingsRect.topleft)
        except Exception:
            pass
        drawLoadingBar(i, total, label)
        pygame.display.flip()
    settingsUpdate()

# Updates the settings based on the current stored values
def settingsUpdate():
    try:
        master = float(settings.get("masterVolume", 100)) / 100.0
        music = float(settings.get("musicVolume", 100)) / 100.0
        sfx = float(settings.get("sfxVolume", 100)) / 100.0
        sfxVolume = max(0.0, min(1.0, master * sfx))
        musicVolume = max(0.0, min(1.0, master * music))
        for variable in ("placeSound", "errorSound", "clickSound", "loadingSound"):
            if variable in globals() and globals()[variable] is not None:
                    globals()[variable].set_volume(sfxVolume)
            pygame.mixer.music.set_volume(musicVolume)
    except Exception:
        pass
    
    image = loadImage(mouseCursorURL)
    try:
        scale = settings.get("cursorSize", 1.0)
        if isinstance(scale, (int, float)) and scale != 1.0:
            width = max(1, int(round(image.get_width() * float(scale))))
            height = max(1, int(round(image.get_height() * float(scale))))
            image = pygame.transform.smoothscale(image, (width, height))
        pygame.mouse.set_cursor(pygame.cursors.Cursor((0, 0), image))
    except Exception:
        pygame.mouse.set_cursor(pygame.cursors.Cursor(pygame.SYSTEM_CURSOR_ARROW))

# Does actions based on key presses
def keyInteractions(event):
    global currentRoad, currentMode, index, dragging
    key = getattr(event, "key", None)
                
    if state == "game":
        currentMode = "building"

        # Switches current road/bridge type based on number keys 1-6
        if key is not None and pygame.K_1 <= key <= pygame.K_6:
            index = key - pygame.K_1 # Map keys 1-6 to indices 0-5
            if roadTileMapping[index]:
                currentRoad = roadTileMapping[index][0]
                if dragging == True and index != 0:
                    dragging = False
            else:
                currentRoad = None
        # Rotates current road/bridge tile by 90 degrees clockwise
        elif key == settings.get("rotateKey", pygame.K_r) and currentRoad is not None:
            try:
                surfaceIndex = roadTileMapping[index].index(currentRoad)
                if index == 4: 
                    step = 3
                elif index == 5: 
                    step = 4
                else: 
                    step = 1
                nextSurfaceIndex = (surfaceIndex + step) % len(roadTileMapping[index])
                currentRoad = roadTileMapping[index][nextSurfaceIndex]
            except (ValueError, IndexError):
                currentRoad = None
        elif key == settings.get("flipVerticallyKey", pygame.K_t) and currentRoad is not None:
            surfaceIndex = roadTileMapping[index].index(currentRoad)
            offset = {1:2, 2:1, 3:0, 0:3}
            if index in [0, 3, 4, 5]:
                step = 0
            elif index == 1:
                nextSurfaceIndex = offset.get(surfaceIndex, surfaceIndex)
                currentRoad = roadTileMapping[index][nextSurfaceIndex]
                return
            else:
                step = 2
            nextSurfaceIndex = (surfaceIndex + step) % len(roadTileMapping[index])
            currentRoad = roadTileMapping[index][nextSurfaceIndex]
        elif key == settings.get("deselectKey", pygame.K_q):
            if dragging == True:
                dragging = False
            currentRoad = None
        
# Validates if a road/bridge can be placed at the given coordinates
def validatePlacement(point: tuple[int, int]=(0, 0)) -> bool:
    if not (0 <= point[0] < mapWidth * tileSize and 0 <= point[1] < mapHeight * tileSize):
        return False

    tileRect = pygame.Rect(point[0], point[1], tileSize, tileSize)
    if tileRect.colliderect(exitRect) or tileRect.colliderect(helpRect) or tileRect.colliderect(submitRect) or tileRect.colliderect(settingsRect):
        return False
    elif point in buildingCache.keys():
        return False

    try:
        isWater = mapData[point[1] // tileSize][point[0] // tileSize] in range(12, 17)
    except IndexError:
        return False

    isBridge = index in [4, 5]
    if isBridge:
        isValid = False
        surfaceIsLand = []
        offset = [
            [[0, 1], [0, -1], [1, 0], [-1, 0]],
            [[0, 2], [0, 1], [0, -1], [-2, 0], [-1, 0], [1, 0]]
        ]
        for offsetX, offsetY in offset[index - 4]:
            try:
                idTile = mapData[(point[1] + tileSize * offsetY) // tileSize][(point[0] + tileSize * offsetX) // tileSize]
                surfaceIsLand.append(False if idTile in range(12, 17) else True)
            except IndexError:
                surfaceIsLand.append(None)
        try:
            roadId = list(roadTileMapping[index]).index(currentRoad)
        except Exception:
            roadId = 0
        if index == 4:
            i = 0 if roadId == 0 else 2
            if surfaceIsLand[i] and surfaceIsLand[i + 1] and surfaceIsLand[i] == surfaceIsLand[i + 1]:
                isValid = True
        elif index == 5:
            i = 0 if roadId == 0 else 3
            if surfaceIsLand[i] and surfaceIsLand[i + 2] and not surfaceIsLand[i + 1] and surfaceIsLand[i] == surfaceIsLand[i + 2] and surfaceIsLand[i] != surfaceIsLand[i + 1]:
                isValid = True
        if isWater and isValid:
            return True
        else:
            return False

    if not isWater:
        return True
    return False

# Validates if the point is within bounds
    # Not used currently, but may be useful later
def validateToolBar(point: tuple[int, int]=(0, 0)) -> Union[list, None]:
    if point[0] > mapWidth * tileSize or point[1] > mapHeight * tileSize:
        return [False, "Out of bounds, currently point is outside of the map area."]
    else:
        return [True]
    
# Places a road or bridge tile at the specified coordinates
def placeTile(mouseCoordGrid: tuple[int, int]=(0, 0), index: int=0):
    bridgeNumber = 0 if not bridgeTileCache else max(bridgeTileCache.keys()) + 1
    roadId = [item for i in range(4) for item in roadTileMapping[i]]
    offset = {4: {0: "y", 3: "x"}, 5: {0: "y", 4: "x"}} # Bridge offsets for placing bridges
    try:
        currentIndex = roadTileMapping[index].index(currentRoad)
    except (ValueError, IndexError):
        currentIndex = index

    pygame.mixer.Sound.play(placeSound)
    # Placing regular roads
    if index not in [4, 5]:
        presentTiles = roadTileCache.get((mouseCoordGrid[0], mouseCoordGrid[1]), [])
        bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
        roadTileCache[(mouseCoordGrid[0], mouseCoordGrid[1])] = [currentRoad] + bridgeTiles

    # Placing bridges vertically
    elif offset.get(index, {}).get(currentIndex, None) in ["x", "y"]:
        for i in range(-1, index - 2):
            if offset[index][currentIndex] == "y":
                pos = (mouseCoordGrid[0], mouseCoordGrid[1] + tileSize * i)
            else:
                pos = (mouseCoordGrid[0] - tileSize * i, mouseCoordGrid[1])
            presentTiles = roadTileCache.get(pos, [])
            bridgeTiles = [tile for tile in presentTiles if tile not in roadId]
            newRoad = roadTileMapping[index][currentIndex + i + 1]
            if newRoad not in bridgeTiles:
                roadTileCache[pos] = [newRoad] + presentTiles
                editBridge(newRoad, pos, bridgeNumber)

# Handles mouse click interactions
def clickInteractions(event, mouseCoordGrid: tuple[int, int]=(0, 0)):
    # Handle all mouse click interactions (called from MOUSEBUTTONDOWN in the main loop)
    global running, mapData, buildingCache, currentMode, prevState, elapsed, score, state, currentRoad, index, currentMap
    def reverseElapsed(a: Timer):
        if a.running:
            a.stop()
        elif not a.running:
            a.start()
        
    # Right-click to delete roads (game state only)
    if event.button == 3 and state == "game":
        pygame.mixer.Sound.play(placeSound)
        currentMode = "deleting"
        # deleteRoad expects pixel coordinates
        deleteRoad(mouseCoordGrid)

    # Left-click interactions
    elif event.button == 1:
        currentMode = "building"

        # UI button interactions
        if exitRect.collidepoint(event.pos):
            pygame.mixer.Sound.play(clickSound)
            if state == "game":
                state = "menu"
                roadTileCache.clear()
                bridgeTileCache.clear()
                currentRoad = None
            elif state == "menu":
                pygame.time.delay(300)
                running = False
            elif state == "help":
                state = prevState
            elif state == "settings":
                state = prevState

        # Settings button interaction
        elif settingsRect.collidepoint(event.pos):
            pygame.mixer.Sound.play(clickSound)
            if state != "settings":
                prevState = state
                state = "settings"
            else:
                state = prevState

        # Help button interaction
        elif helpRect.collidepoint(event.pos):
            pygame.mixer.Sound.play(clickSound)
            if state != "help":
                prevState = state
                state = "help"
            else:
                state = prevState

        # Submit path for validation
        elif submitRect.collidepoint(event.pos):
            isValid = validPath()
            if isValid:
                pygame.mixer.Sound.play(clickSound)
                drawMap(tilesetLandDark)
                score = calculateScore()
                scoreText = fontBold.render(f"{score}", True, (232, 207, 166))
                fontSemiBold = pygame.font.Font(io.BytesIO(requests.get(fontSemiBoldURL).content), 12)
                scoreDescription = fontSemiBold.render(
                    f"Congratulations, you have beaten Supply Chains!", True, (232, 207, 166)
                )

                screen.blit(scoreText, (tileSize * 5.5, tileSize * 4))
                screen.blit(scoreDescription, (tileSize * 3.5, tileSize * 6))
                
                pygame.display.flip()
                pygame.time.wait(2500)

                state = "menu"
                roadTileCache.clear()
                bridgeTileCache.clear()
                currentRoad = None
                elapsed.reset()
            else:
                pygame.mixer.Sound.play(errorSound)
                print(
                    "You have not connected all factories to at least one depot. "
                    "Please try again.")

        # Start game from menu
        elif state == "menu" and playRect.collidepoint(event.pos):
            pygame.mixer.Sound.play(clickSound)
            elapsed.start()
            otherMaps = avaliableMaps.copy()
            if len(mapHistory) > 0: 
                for map in mapHistory:
                    otherMaps.remove(map)
                if len(mapHistory) == len(avaliableMaps):
                    mapHistory.clear()
                    otherMaps = avaliableMaps.copy()
            mapHistory.append(random.choice(otherMaps))
            mapData = loadData(mapHistory[-1])
            buildingCache = placeBuilding(depots=random.randint(1, 2), factories=random.randint(2, 5))
            state = "game"

        # Place roads/buildings on the map
        elif state == "game" and currentMode == "building":
            if buildingCache == None:
                raise ExecError
            if currentRoad is None:
                pygame.mixer.Sound.play(errorSound)
                print("Currently placing nothing.")
            elif mouseCoordGrid in buildingCache.keys():
                pygame.mixer.Sound.play(errorSound)
                print("Cannot place on depot/factory.")

            if currentRoad != None and validatePlacement(mouseCoordGrid):
                placeTile(mouseCoordGrid, index)
            else:
                print(placementError)
                pygame.mixer.Sound.play(errorSound)

# Function to preview the cursor outline based on current mode
def cursorPreview(mouseCoordGrid: tuple[int, int]=(0, 0)):
    global currentMode, currentRoad, timer

    isInvalid = False
    if currentMode == "building" and currentRoad is not None:
        isInvalid = not validatePlacement(mouseCoordGrid)

    if currentMode == "deleting" and not isInvalid:
        if not timer.running:
            timer.start()
        if timer.elapsed() <= 0.175:
            pygame.draw.rect(screen, (255, 179, 186), outlineRect, width=1)
        else:
            timer.reset()
            timer.stop()
            currentMode = "building"
            pygame.draw.rect(screen, (255, 255, 255), outlineRect, width=1)
        return

    if isInvalid:
        color = (255, 179, 186)
    elif (mouseCoordGrid[0], mouseCoordGrid[1]) in buildingCache.keys():
        color = (255, 223, 186)
    else:
        color = (255, 255, 255)

    if index in (4, 5):
        try:
            currentIndex = roadTileMapping[index].index(currentRoad)
        except (ValueError, IndexError):
            currentIndex = 0

        offset = {4: {0: "y", 3: "x"}, 5: {0: "y", 4: "x"}}
        if offset.get(index, {}).get(currentIndex, None) == "y":
            rect = pygame.Rect(mouseCoordGrid[0], mouseCoordGrid[1] - 0.5 * tileSize, tileSize, (index - 2) * tileSize)
            pygame.draw.rect(screen, color, rect, width=1)
            return
        elif offset.get(index, {}).get(currentIndex, None) == "x":
            rect =pygame.Rect(mouseCoordGrid[0] - (index - 3.5) * tileSize, mouseCoordGrid[1], (index - 2) * tileSize, tileSize)
            pygame.draw.rect(screen, color, rect, width=1)
            return
    else: pygame.draw.rect(screen, color, outlineRect, width=1)

# Function to preview the tile being placed
def tilePreview(mouseCoordGrid: tuple[int, int]=(0, 0), index: int=0, alpha: int=100):
    global currentRoad, hiddenBridges, hiddenTiles, hiddenPreviewTiles
    hiddenBridges = list() # List of bridge IDs to hide
    bridgeIds = [roadTileMapping[5][i] for i in [1, 2, 5, 6]] + [roadTileMapping[4][i] for i in [1, 4]]
    try:
        currentIndex = roadTileMapping[index].index(currentRoad)
    except (ValueError, IndexError):
        currentIndex = index
    offset = {4: {0: "y", 3: "x"}, 5: {0: "y", 4: "x"}} # Bridge offsets for drawing previews

    # Draw bridge previews if applicable
    if offset.get(index, {}).get(currentIndex, None) in ["y", "x"]:
        for i in range(-1, index - 2):
            newRoad = roadTileMapping[index][currentIndex + i + 1]
            try:
                tileId = tileLocationData[currentIndex + i + 1][index]
                previewTile = getTileCached(tilesetRoad, tileId, alpha)
            except Exception:
                previewTile = newRoad
            if offset.get(index, {}).get(currentIndex, None) == "y":
                pos = (mouseCoordGrid[0], mouseCoordGrid[1] + tileSize * i)
            else:
                pos = (mouseCoordGrid[0] - tileSize * i, mouseCoordGrid[1])
            screen.blit(previewTile, pos)
            if i not in [-1, index - 3]: # Only add middle tiles to hidden preview list
                hiddenPreviewTiles.append(pos)
            if (
                bridgeLocate(contains=pos) is not None and
                newRoad in bridgeIds and
                mapData[pos[1] // tileSize][pos[0] // tileSize] in range(12, 17)
            ):
                hiddenBridges.append(bridgeLocate(contains=pos))

    # Draw road preview if applicable
    elif bridgeLocate(contains=mouseCoordGrid) is None or (
        mapData[mouseCoordGrid[1] // tileSize][mouseCoordGrid[0] // tileSize] not in range(12, 17)
    ):  
        if currentRoad is not None:
            try:
                tileId = tileLocationData[currentIndex][index]
                previewTile = getTileCached(tilesetRoad, tileId, alpha)
                screen.blit(previewTile, mouseCoordGrid)
                hiddenPreviewTiles.append(mouseCoordGrid)
            except Exception:
                screen.blit(currentRoad, mouseCoordGrid)
                hiddenPreviewTiles.append(mouseCoordGrid)

# Function to load the settings UI sliders
def buildSettingsUI() -> None:
    settingsSliders.clear()

    def makeOnChange(key: str):
        def cb(v):
            try:
                # Coerce to int for 0-100 ranges; preview alpha expects 0-255
                settings[key] = int(v)
                settingsUpdate()
            except Exception:
                pass
        return cb

    baseX = tileSize * 2.5
    baseY = tileSize * 4
    spacing = int(tileSize * 2)
    length = tileSize * 9
    outlineColor = (0xc6, 0x9d, 0x6f)
    sliderColor = (0xe8, 0xcf, 0xa6)

    # Master volume
    settingsSliders.append(
        Slider(
            baseX, baseY + spacing * 0, length,
            trackThickness=10, minValue=0, maxValue=100,
            value=settings.get("masterVolume", 100), stepSize=1,
            trackColor=None, fillColor=sliderColor, knobColor=(255, 255, 255),
            cornerRadius=8, borderColor=outlineColor, borderWidth=2,
            showValue=True, font=fontSemiBold, labelText="Master Volume",
            onChange=makeOnChange("masterVolume"),
        )
    )

    # Music volume
    settingsSliders.append(
        Slider(
            baseX, baseY + spacing * 1, length,
            trackThickness=10, minValue=0, maxValue=100,
            value=settings.get("musicVolume", 100), stepSize=1,
            trackColor=None, fillColor=sliderColor, knobColor=(255, 255, 255),
            cornerRadius=8, borderColor=outlineColor, borderWidth=2,
            showValue=True, font=fontSemiBold, labelText="Music Volume",
            onChange=makeOnChange("musicVolume"),
        )
    )

    # SFX volume
    settingsSliders.append(
        Slider(
            baseX, baseY + spacing * 2, length,
            trackThickness=10, minValue=0, maxValue=100,
            value=settings.get("sfxVolume", 100), stepSize=1,
            trackColor=None, fillColor=sliderColor, knobColor=(255, 255, 255),
            cornerRadius=8, borderColor=outlineColor, borderWidth=2,
            showValue=True, font=fontSemiBold, labelText="SFX Volume",
            onChange=makeOnChange("sfxVolume"),
        )
    )

    # Preview Alpha (0-255)
    settingsSliders.append(
        Slider(
            baseX, baseY + spacing * 3, length,
            trackThickness=10, minValue=1, maxValue=255,
            value=settings.get("previewTransparency", 100), stepSize=1,
            trackColor=None, fillColor=sliderColor, knobColor=(255, 255, 255),
            cornerRadius=8, borderColor=outlineColor, borderWidth=2,
            showValue=True, font=fontSemiBold, labelText="Tile preview transparency",
            onChange=makeOnChange("previewTransparency"),
        )
    )
  
# Function to draw the user interface
def drawInterface(state: str="menu"):
    # Menu screen UI
    if state == "menu":
        drawMap(tilesetLandDark) 
        buttonTiles = range(3) if playRect.collidepoint(currentPos[0], currentPos[1]) else range(3, 6)
        for i, tileIndex in enumerate(buttonTiles):
            screen.blit(getTileCached(buttonsUI, tileIndex), 
                      (playRect.x + i * tileSize, playRect.y))

        tileIndex = 0
        for iy in range(2):
            for ix in range(6):
                screen.blit(getTileCached(tilesetLogoUI, tileIndex),
                            (logoRect.x + ix * tileSize + 0.5 * tileSize, logoRect.y + iy * tileSize))
                tileIndex += 1

    # Help screen UI
    elif state == "help":
        drawMap(tilesetLand)
        for y in range(13):
            for x in range(15):
                tileId = y * 15 + x
                tile = getTileById(tilesetHelpUI, tileId)
                screen.blit(tile, (x * tileSize, y * tileSize))
    
    # Game screen UI
    elif state == "game":
        submitTile = 10 if submitRect.collidepoint(currentPos[0], currentPos[1]) else 11
        screen.blit(getTileCached(buttonsUI, submitTile), submitRect.topleft)

    # Settings screen UI
    elif state == "settings":
        drawMap(tilesetLandDark)
        # Draw built sliders
        for slider in settingsSliders:
            try:
                slider.draw(screen)
            except Exception:
                pass
    
    # UIs that are common across states
    exitTile = 6 if exitRect.collidepoint(currentPos[0], currentPos[1]) else 7
    screen.blit(getTileCached(buttonsUI, exitTile), exitRect.topleft)

    helpTile = 12 if helpRect.collidepoint(currentPos[0], currentPos[1]) else 13
    screen.blit(getTileCached(buttonsUI, helpTile), helpRect.topleft)

    settingTile = 8 if settingsRect.collidepoint(currentPos[0], currentPos[1]) else 9
    screen.blit(getTileCached(buttonsUI, settingTile), settingsRect.topleft)

# Function to draw the dragging preview
def drawDraggingPreview(dragging, dragInfo, currentGridPos):
    fromX, fromY = dragInfo["startPos"]
    toX, toY = dragInfo["endPos"]

    # Draw preview based on drag type
    if dragInfo["type"] == "place":
        dx = toX - fromX
        dy = toY - fromY
        if abs(dx) == abs(dy):
            currentIndex = roadTileMapping[index].index(currentRoad)
            dragInfo["orientation"] = "x" if currentIndex == 1 else "y"
        elif abs(dx) >= abs(dy):
            dragInfo["orientation"] = "x"
        else:
            dragInfo["orientation"] = "y"
        oldRoad = currentRoad
        try:
            if dragInfo["orientation"] == "x":
                oriented = roadTileMapping[0][1]
            else:
                oriented = roadTileMapping[0][0]
            globals()["currentRoad"] = oriented
        except Exception:
            pass

        if dragInfo["orientation"] == "y":
            step = tileSize if toY >= fromY else -tileSize
            for y in range(fromY, toY + step, step):
                if validatePlacement((fromX, y)):
                    tilePreview((fromX, y), index, alpha=settings.get("previewTransparency", 100))
        elif dragInfo["orientation"] == "x":
            step = tileSize if toX >= fromX else -tileSize
            for x in range(fromX, toX + step, step):
                if validatePlacement((x, fromY)):
                    tilePreview((x, fromY), index, alpha=settings.get("previewTransparency", 100))  
        globals()["currentRoad"] = oldRoad
    
    # Draw delete preview 
    elif dragInfo["type"] == "delete":
        dx = toX - fromX
        dy = toY - fromY
        minX = fromX if dx >= 0 else toX
        minY = fromY if dy >= 0 else toY
        width = abs(dx) + tileSize
        height = abs(dy) + tileSize
        pygame.draw.rect(screen, (255, 179, 186), pygame.Rect(minX, minY, width, height), width=1)

# Function to place tiles while dragging
def placeDraggedTiles(dragInfo):
    fromX, fromY = dragInfo["startPos"]
    toX, toY = dragInfo["endPos"]

    # Ensure the placed tile orientation matches the drag orientation
    oldRoad = currentRoad
    try:
        if dragInfo["orientation"] == "x":
            oriented = roadTileMapping[0][1]
        else:
            oriented = roadTileMapping[0][0]
        globals()["currentRoad"] = oriented
    except Exception:
        pass
    
    pygame.mixer.Sound.play(placeSound)
    if dragInfo["orientation"] == "y":
        step = tileSize if toY >= fromY else -tileSize
        for y in range(fromY, toY + step, step):
            if validatePlacement((fromX, y)):
                placeTile((fromX, y), index)
    elif dragInfo["orientation"] == "x":
        step = tileSize if toX >= fromX else -tileSize
        for x in range(fromX, toX + step, step):
            if validatePlacement((x, fromY)):
                placeTile((x, fromY), index)

    # Restore previous selection
    globals()["currentRoad"] = oldRoad

# Function to delete tiles while dragging
def deleteDraggedTiles(dragInfo):
    fromX, fromY = dragInfo["startPos"]
    toX, toY = dragInfo["endPos"]

    pygame.mixer.Sound.play(placeSound)
    for x in range(min(fromX, toX), max(fromX, toX) + tileSize, tileSize):
        for y in range(min(fromY, toY), max(fromY, toY) + tileSize, tileSize):
            deleteRoad((x, y))

# Timer class for managing time-based events
global timer, elapsed
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

# Function to calculate the player's score based on time taken
    # Going to refine a better scoring system later (A* soon™)
def calculateScore():
    if not elapsed.running:
        return "None"
    timeTaken = elapsed.elapsed()
    baseScore = 9999
    timePenalty = timeTaken * 25.0  
    variation = random.randint(-50, 50)
    finalScore = int(baseScore - timePenalty + variation)
    score = max(1, min(9999, finalScore))
    if score < 1000:
        return "0" * (4 - len(str(score))) + str(score)
    return str(score)

# Initialization
pygame.init()
pygame.display.set_caption("Supply Chains")

# Set up display and fonts
tileSize = 32
clock = pygame.time.Clock()
screen = pygame.display.set_mode((15 * tileSize, 12 * tileSize))
avaliableMaps = [riverBasinURL, greenPlainsURL, riverDeltaURL, islandURL]
mapHistory = list()

fontBold = pygame.font.Font(io.BytesIO(requests.get(fontBoldURL).content), 65)
fontSemiBold = pygame.font.Font(io.BytesIO(requests.get(fontSemiBoldURL).content), 16)

# Game state variables
global currentRoad, hiddenBridges, currentMode, index, state, prevState, inventory
placementError = "You cannot place here."
inventory = [False, 1]

# Cells covered by the current preview
hiddenPreviewCells = set()

# Timers and flags
timer = Timer()
elapsed = Timer()
running = True
currentRoad = None
currentMode = "building" # Modes: building, deleting

# Mouse and UI variables
index = 0
state = "menu" # States: menu, help, game, settings
prevState = str()

# Global settings
global settings, settingsSliders
settings = {"masterVolume": 100, "musicVolume": 100, "sfxVolume": 100,
            "cursorSize": 1.00, "previewTransparency": 100,
            "rotateKey": pygame.K_r, "flipVerticallyKey": pygame.K_t, "deselectKey": pygame.K_q
            }
settingsSliders: list[Slider] = []

# Mouse dragging variables
dragging = False
dragInfo = {"startPos": (0, 0), "orientation": "", "lastPos": (0, 0), "type": ""}

# UI element rectangles
playRect = pygame.Rect(tileSize * 6, tileSize * 8, tileSize * 3, tileSize)
logoRect = pygame.Rect(tileSize * 5, tileSize * 4, tileSize * 5, tileSize * 2)
exitRect = pygame.Rect(tileSize * 13, tileSize * 1, tileSize, tileSize)
submitRect = pygame.Rect(tileSize * 11, tileSize * 1, tileSize, tileSize)
settingsRect = pygame.Rect(tileSize * 12, tileSize * 1, tileSize, tileSize)
helpRect = pygame.Rect(tileSize * 1, tileSize * 1, tileSize, tileSize)

# Loading screen
initializeGame()
pygame.mixer.Sound.play(loadingSound)
roadMapping()
buildSettingsUI()
buildingCache = {}

# Main loop
while running:    
    windowWidth, windowHeight = pygame.display.get_window_size() # Get current window size
    currentPos = pygame.mouse.get_pos() # Get current mouse position
    currentGrid = (currentPos[0] // tileSize, currentPos[1]// tileSize) # Grid position
    currentGridPos = (currentGrid[0] * tileSize, currentGrid[1] * tileSize) # Pixel position
    outlineRect = pygame.Rect(currentGridPos[0], currentGridPos[1], tileSize, tileSize) # Outline rectangle for building placement
    screen.fill((144, 159, 84))

    # Game Screen UI
    if state == "game":
        hiddenBridges = list()
        hiddenPreviewTiles = []
        drawMap(tilesetLand) 

        if buildingCache == None: raise ExecError
        else: drawBuildings()

        if (not exitRect.collidepoint(currentPos[0], currentPos[1]) 
        and not helpRect.collidepoint(currentPos[0], currentPos[1]) 
        and not submitRect.collidepoint(currentPos[0], currentPos[1])
        and not settingsRect.collidepoint(currentPos[0], currentPos[1])):
            if not dragging:
                cursorPreview(currentGridPos)
                if currentRoad is not None and currentGridPos not in buildingCache.keys():
                    tilePreview(currentGridPos, index, alpha=settings.get("previewTransparency", 100))

        if dragging:
            dragInfo["endPos"] = currentGridPos
            drawDraggingPreview(dragging, dragInfo, currentGridPos)
        drawRoad(currentGridPos)
    
    # Menu and Help Screen UI
    drawInterface(state)

    # Handle events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Route slider interactions when in settings
        if state == "settings" and event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
            try:
                for slider in settingsSliders:
                    slider.handleEvent(event)
            except Exception:
                pass
            settingsUpdate()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if state == "game" and event.button == 1 and index == 0 and currentRoad is not None:
                overUI = exitRect.collidepoint(event.pos) or helpRect.collidepoint(event.pos) or submitRect.collidepoint(event.pos) or settingsRect.collidepoint(event.pos)
                if not overUI:
                    if not dragging:
                        dragInfo["type"] = "place"
                        dragInfo["startPos"] = currentGridPos
                    dragging = True
            elif state == "game" and event.button == 3:
                currentRoad = None
                if not dragging:
                    dragInfo["type"] = "delete"
                    dragInfo["startPos"] = currentGridPos
                dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            if dragging == True:
                dragging = False
                dragInfo["endPos"] = currentGridPos
                if dragInfo.get("endPos") != dragInfo.get("startPos"):
                    if dragInfo["type"] == "place":
                        placeDraggedTiles(dragInfo)
                    elif dragInfo["type"] == "delete":
                        deleteDraggedTiles(dragInfo)
                else:
                    clickInteractions(event, currentGridPos)
            else:
                clickInteractions(event, currentGridPos)
        elif event.type == pygame.KEYDOWN:
            # Save screenshot when 'P' is pressed
            if event.key == pygame.K_p:
                downloadsFolder = os.path.join(os.path.expanduser("~"), "Downloads")
                savePath = os.path.join(downloadsFolder, f"screenshot.png")
                pygame.image.save(screen, savePath)
                print(f"Map saved to: {savePath}")
            else:
                keyInteractions(event)
    pygame.display.flip()
    clock.tick(60)
pygame.quit()

