import pygame, requests, io, sys, csv, random

# Asset Urls
tilesetUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/main/Tileset.png"
tilesetDarkUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/a3e090b36c60e35889e90da922884cdd78a3395b/TilesetDark.png"

tilesetRoadUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/6b92357a8a5a5ae25b231ee267b21f739032b31d/TilesetRoad.png"
tilesetRoadID = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/f28de1c880fb890960f9d7c56b21c03bc112ab48/Road%20Tileset%20ID.csv"

tilesetUiUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/e051ba39af9120a147405ab5d56e7359e1882959/TilemapUI.png"
riverBasinUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/434a2e2d30e6535dd466531759447a4809f8ae6c/River%20Basin%20Level.csv"
greenplainsUrl = "https://raw.githubusercontent.com/Tiger0-o/Supply-Chains/6b92357a8a5a5ae25b231ee267b21f739032b31d/Green%20Plains.csv"


# Initialization
pygame.init()
pygame.display.set_caption("Supply Chains")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 24)
tileSize = 32
avaliableMaps = [riverBasinUrl, greenplainsUrl]

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
mapData = loadData(random.choice(avaliableMaps))
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

# Tile Functions
def getTileById(sheet, tileId):
    cols = sheet.get_width() // tileSize
    x = (tileId % cols) * tileSize
    y = (tileId // cols) * tileSize
    tile = pygame.Surface((tileSize, tileSize), pygame.SRCALPHA)
    tile.blit(sheet, (0, 0), (x, y, tileSize, tileSize))
    return tile

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
roadTilePlacementCache = {}
roadTileMapping = {
    0: [], # Straight 
    1: [], # Corner 
    2: [], # T-Junction 
    3: [], # Intersection 
    4: [], # Short-Bridge 
    5: [], # Long-Bridge
}

def roadMapping(sheet=tileData):
    for y, row in enumerate(sheet):
        for x, tileId in enumerate(row):
            if tileId != -1:
                tile = getTileCached(tilesetRoad, tileId)
                if tile not in roadTileMapping[x]:
                    roadTileMapping[x].append(tile)

# Main Loop
running = True
currentRoad = None
index = 0
state = "menu"
roadMapping()

playRect = pygame.Rect(tileSize * 6, tileSize * 8, tileSize * 3, tileSize)
exitRect = pygame.Rect(tileSize * 13, tileSize * 1, tileSize, tileSize)

while running:
    mouseX, mouseY = pygame.mouse.get_pos()
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONUP:
            if exitRect.collidepoint(event.pos):
                if state == "game":
                    state = "menu"
                elif state == "menu":
                    running = False
            elif state == "menu" and playRect.collidepoint(event.pos):
                state = "game"
        elif event.type == pygame.KEYDOWN:
            if state == "game":
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
        drawMap(tileset)
        if currentRoad:
            currentIndex = roadTileMapping[index].index(currentRoad)
            gridX = (mouseX // tileSize) * tileSize
            gridY = (mouseY // tileSize) * tileSize

            if index == 4:  # Short-Bridge (3 tiles)
                if currentIndex == 0:
                    for i in range(-1,2,1): 
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad,(gridX, gridY + tileSize * i))
                elif currentIndex == 3:
                    for i in range(-1,2,1): 
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad,(gridX - tileSize * i, gridY))

            elif index == 5:  # Long-Bridge (4 tiles)
                if currentIndex == 0:
                    for i in range(-1,3,1): 
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad,(gridX, gridY + tileSize * i))
                elif currentIndex == 3:
                    for i in range(-1,3,1): 
                        newRoad = roadTileMapping[index][currentIndex + i + 1]
                        screen.blit(newRoad,(gridX - tileSize * i, gridY))
            else:  # Regular roads
                screen.blit(currentRoad, (gridX, gridY))
    
    elif state == "menu":
        drawMap(tilesetDark)
        buttonTiles = range(3) if playRect.collidepoint(mouseX, mouseY) else range(3, 6)
        for i, tileIndex in enumerate(buttonTiles):
            screen.blit(getTileCached(tilesetUi, tileIndex), 
                      (playRect.x + i * tileSize, playRect.y))
    
    exitTile = 6 if exitRect.collidepoint(mouseX, mouseY) else 7
    screen.blit(getTileCached(tilesetUi, exitTile), exitRect.topleft)

    pygame.display.flip()

print(roadTileMapping)
pygame.quit()