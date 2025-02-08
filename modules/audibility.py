# ============================================
# Module: Calculate audibility of surface squares and buildings voxels in multiprocessing mode
# ============================================

# Modules import
# ============================================

# Standart modules
import multiprocessing as mp # Use multiprocessing
from multiprocessing.shared_memory import SharedMemory # Use shared memory
import ctypes # Use primitive datatypes for multiprocessing data exchange

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition

# ============================================
# Get integer vertical coordinate of the first voxel of building in (x, y) cell with UIB=uib
# x, y - integer coordinates of cell
# uib - integer UIB of building
# uib cannot be negative. Do not use this function for a cells without buildings
# ============================================
def GetFirstBuildingVoxel(x, y, uib):
    # Global variables
    global ground, buildingsSize, buildings
    if cfg.BuildingGroundMode != 'levels':
        return buildings[uib*buildingsSize+1]
    else:
        return ground[x*boundsY+y]

# ============================================
# Check audibility on destination voxel with integer coordinates (xDst, yDst, zDst)
# from megaphone on source voxel with integer coordinates (xSrc, ySrc, zSrc)
# uibDst - UIB of building on checked destination voxel, -1 if not exists
# uibSrc - UIB of building, where is source megaphone based
# ============================================
def CheckAudibility(xDst, yDst, zDst, uibDst, xSrc, ySrc, zSrc, uibSrc):

    # Global variables
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, megaphonesCount, megaphonesLeft, \
           checksCount, checksMade

    # Common building is audibility by default
    if ((uibSrc>=0) and (uibDst == uibSrc)):
        return True
    
    # Calculate distance between source and destination voxels
    dx = xDst - xSrc
    dy = yDst - ySrc
    dz = zDst - zSrc
    distance = (dx*dx + dy*dy + dz*dz)**0.5
    if distance == 0: # Avoid division by zero
        return True
    maxAxisDistance = max(abs(dx), abs(dy), abs(dz))
    step = cfg.sizeStep /maxAxisDistance # Step size to check audibility of voxels

    # Analyze segment between source and destination voxels
    # We move in small steps along the segment and check for extraneous buildings or the earth's surface.
    t = 0.0
    while t <= 1.0:
        # Calculate coordinates of the Intermediate voxel (x, y, z) on the segment
        x = int(round(xSrc + t * dx))
        y = int(round(ySrc + t * dy))
        z = int(round(zSrc + t * dz))
        uib = uibs[x*boundsY+y]

        # if intermediate voxel does not belong to source or destination buildings
        if (uib >= 0) and (uib != uibSrc) and (uib != uibDst):
            # If there is an extraneous building on the intermediate voxel, check if the intermediate voxel is higher than the building
            if z < (GetFirstBuildingVoxel(x,y,uib) + buildings[uib*buildingsSize]):
                return False
            
        # If there is no building there, check if the intermediate voxel is higher than the earth's surface
        if uib < 0:
            if z < ground[x* boundsY+y] - 1:
                return False

        t = t + step # Go to the next step on the segment

    # If no obstacles were found, the destination voxel is audible
    return True

# ============================================
# Initialize calculation audibility of squares and voxels by the specific megaphone
# Retrieve scalar variables from parameters of function 
# and store them in global variables of this module of current proccess
# ============================================
def InitializeAudibilityOfMegaphone(pCellsSize, pCells, pCellsCount, pCellsIndex, pBuffers, pBuffersCount, pBuffersIndex,
                                   pBoundsX, pBoundsY, pBoundsZ, pGround, pAudibility2D, pUIB, pVoxelIndex,
                                   pAudibilityVoxels, pBuildingsSize, pBuildings, pMegaphonesCount, pMegaphonesLeft, 
                                   pChecksCount, pChecksMade):
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, megaphonesCount, megaphonesLeft, \
           checksCount, checksMade
    cellsSize = pCellsSize
    cells = pCells
    cells_count = pCellsCount
    cells_index = pCellsIndex
    buffers = pBuffers
    buffers_count = pBuffersCount
    buffers_index = pBuffersIndex
    boundsX = pBoundsX
    boundsY = pBoundsY
    boundsZ = pBoundsZ
    ground = pGround
    audibility2D = pAudibility2D
    uibs = pUIB
    VoxelIndex = pVoxelIndex
    audibilityVoxels = pAudibilityVoxels
    buildingsSize = pBuildingsSize
    buildings = pBuildings
    megaphonesCount = pMegaphonesCount
    megaphonesLeft = pMegaphonesLeft
    checksCount = pChecksCount
    checksMade = pChecksMade

# ============================================
# Calculate audibility of squares and voxels by the specific megaphone
# ============================================
def CalculateAudibilityOfMegaphone(uim):
    # Global variables
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, megaphonesCount, megaphonesLeft, \
           checksCount, checksMade
    
    # Global counters
    global countCheckedSquares, countAudibilitySquares, countCheckedVoxels, countAudibilityVoxels
    countCheckedSquares = 0
    countAudibilitySquares = 0
    countCheckedVoxels = 0
    countAudibilityVoxels = 0

    env.logger.info('Start megaphone #{} of {}', uim+1, megaphonesCount)
    standaloneMegaphoneHeight = round(cfg.heightStansaloneMegaphone / cfg.sizeVoxel)

    # Loop through megaphones cells
    idxCell = cells_index[uim]
    for i in range(cells_count[uim]):

        xCell = cells[idxCell] # Coordinates of megaphone cell
        yCell = cells[idxCell+1]
        uibMegaphone = uibs[xCell*boundsY+yCell] # UIB of megaphone building (if exists)
        # Height of megaphone
        if uibMegaphone<0:
            zCell = ground[xCell*boundsY+yCell] + standaloneMegaphoneHeight
        else:
            zCell = GetFirstBuildingVoxel(xCell, yCell, uibMegaphone) + buildings[uibMegaphone*env.sizeBuilding]

        # Loop through buffer zone
        idxBuffer = buffers_index[uim]
        for j in range(buffers_count[uim]):
            xBuffer = buffers[idxBuffer] # Coordinates of test cell
            yBuffer = buffers[idxBuffer+1]
            uibTest = uibs[xBuffer*boundsY+yBuffer] # UIB building on test cell (if exists)
            zStart = ground[xBuffer*boundsY+yBuffer]

            # Check ground square audibility
            countCheckedSquares = countCheckedSquares + 1
            flag = (audibility2D[xBuffer*boundsY+yBuffer] > 0)
            if not(flag): # If voxel is not audibility yet
                flag = CheckAudibility(xBuffer, yBuffer, zStart, uibTest, xCell, yCell, zCell, uibMegaphone)
                audibility2D[xBuffer*boundsY+yBuffer] = (1 if flag else -1)
            countAudibilitySquares = countAudibilitySquares + (1 if flag else 0)

            # There is any building on tested square
            if uibTest>=0:
                flats = buildings[uibTest*env.sizeBuilding+2]
                if flats>0: # If this is a living building
                    zStart = GetFirstBuildingVoxel(xBuffer, yBuffer, uibTest)
                    floors = buildings[uibTest*env.sizeBuilding]
                    # Loop through floors of building
                    for floor in range(floors):
                        # Check building voxel audibility
                        countCheckedVoxels = countCheckedVoxels + 1
                        flag = (audibilityVoxels[ VoxelIndex[xBuffer*boundsY+yBuffer] + floor ] > 0)
                        if not(flag): # If voxel is not audibility yet
                            flag = CheckAudibility(xBuffer, yBuffer, zStart+floor, uibTest, xCell, yCell, zCell, uibMegaphone)
                            audibilityVoxels[ VoxelIndex[xBuffer*boundsY+yBuffer] + floor ] = (1 if flag else -1)
                        countAudibilityVoxels = countAudibilityVoxels + (1 if flag else 0)

            idxBuffer = idxBuffer + cellsSize # Go to next test cell

        idxCell = idxCell + cellsSize # Go to next megaphone cell
        checksMade.value = checksMade.value + buffers_count[uim]

    megaphonesLeft.value = megaphonesLeft.value - 1
    env.logger.info(checksMade.value)
    env.logger.success('Finish #{}. {} ({}) audibility squares, {} ({}) audibility voxels found. {} tasks left: {} done',
                       uim+1,
                       env.printLong(countAudibilitySquares), f'{countAudibilitySquares/countCheckedSquares:.0%}', 
                       env.printLong(countAudibilityVoxels), f'{countAudibilityVoxels/countCheckedVoxels:.0%}',
                       megaphonesLeft.value, f'{(1-megaphonesLeft.value/megaphonesCount):.0%}' )

# ============================================
# Calculate audibility of all squares and voxels
# ============================================
def CalculateAudibility():
    env.logger.info("Switching to multiprocessing mode...")

    # Collect array of processes parameters
    params = []
    for uim in range(env.countMegaphones):
        params.append((uim,))

    # Create in shared memory integer variable for progress counters
    env.leftMegaphones = mp.Value(ctypes.c_uint, env.countMegaphones)
    env.madeChecks = mp.Value(ctypes.c_ulonglong, 0)

    # Schedule processes
    with mp.Pool(processes=mp.cpu_count(), initializer=InitializeAudibilityOfMegaphone, 
                 initargs=(env.sizeCell, env.MegaphonesCells, env.MegaphonesCells_count, env.MegaphonesCells_index,
                           env.MegaphonesBuffers, env.MegaphonesBuffers_count, env.MegaphonesBuffers_index,
                           env.bounds[0], env.bounds[1], env.bounds[2], env.ground, env.audibility2D, env.uib, env.VoxelIndex,
                           env.audibilityVoxels, env.sizeBuilding, env.buildings, env.countMegaphones, env.leftMegaphones, 
                           env.countChecks, env.madeChecks)) as pool:
        pool.starmap_async(CalculateAudibilityOfMegaphone, params)

        while not pool._state == 'TERMINATE':
            env.logger.info(f'Megaphones left: {env.leftMegaphones.value}')
            time.sleep(20)

        pool.close()
        pool.join()


