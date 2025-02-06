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
# Check audibility on destination voxel with integer coordinates (xDst, yDst, zDst)
# from megaphone on source voxel with integer coordinates (xSrc, ySrc, zSrc)
# uibDst - UIB of building on checked destination voxel, -1 if not exists
# floorDst - number of floor of checked destination voxel, 0 in there is no building where
# uibSrc - UIB of building, where is source megaphone based
# ============================================
def CheckAudibility(xDst, yDst, zDst, uibDst, floorDst, xSrc, ySrc, zSrc, uibSrc):

    # Global variables
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uib, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings

    if zDst<=zSrc:
        return True
    return False

# ============================================
# Initialize calculation audibility of squares and voxels by the specific megaphone
# Retrieve scalar variables from parameters of function 
# and store them in global variables of this module of current proccess
# ============================================
def InitializeAudibilityOfMegaphone(pCellsSize, pCells, pCellsCount, pCellsIndex, pBuffers, pBuffersCount, pBuffersIndex,
                                   pBoundsX, pBoundsY, pBoundsZ, pGround, pAudibility2D, pUIB, pVoxelIndex,
                                   pAudibilityVoxels, pBuildingsSize, pBuildings):
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uib, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings
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
    uib = pUIB
    VoxelIndex = pVoxelIndex
    audibilityVoxels = pAudibilityVoxels
    buildingsSize = pBuildingsSize
    buildings = pBuildings

# ============================================
# Calculate audibility of squares and voxels by the specific megaphone
# ============================================
def CalculateAudibilityOfMegaphone(uim):
    env.logger.info('Start calculation for Megaphone #{}', uim)
    standaloneMegaphoneHeight = round(cfg.heightStansaloneMegaphone / cfg.sizeVoxel) + 1

    # Global variables
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uib, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings
    
    # Global counters
    global countCheckedSquares, countAudibilitySquares, countCheckedVoxels, countAudibilityVoxels
    countCheckedSquares = 0
    countAudibilitySquares = 0
    countCheckedVoxels = 0
    countAudibilityVoxels = 0

    # Loop through megaphones cells
    idxCell = cells_index[uim]
    for i in range(cells_count[uim]):

        xCell = cells[idxCell] # Coordinates of megaphone cell
        yCell = cells[idxCell+1]
        uibMegaphone = uib[xCell*boundsY+yCell] # UIB of megaphone building (if exists)
        if uibMegaphone<0:
            zCell = ground[xCell*boundsY+yCell] + standaloneMegaphoneHeight
        else:
            if cfg.BuildingGroundMode != 'levels':
                zCell = buildings[uibMegaphone*env.sizeBuilding+1] + buildings[uibMegaphone*env.sizeBuilding] + 1
            else:
                zCell = ground[xCell*boundsY+yCell] + buildings[uibMegaphone*env.sizeBuilding] + 1

        # Loop through buffer zone
        idxBuffer = buffers_index[uim]
        for i in range(buffers_count[uim]):
            xBuffer = buffers[idxBuffer] # Coordinates of test cell
            yBuffer = buffers[idxBuffer+1]
            uibTest = uib[xBuffer*boundsY+yBuffer] # UIB building on test cell (if exists)
            zStart = ground[xBuffer*boundsY+yBuffer]

            # Check ground square audibility
            flag = CheckAudibility(xBuffer, yBuffer, zStart, uibTest, 0, xCell, yCell, zCell, uibMegaphone)
            countCheckedSquares = countCheckedSquares + 1
            if flag:
                audibility2D[xBuffer*boundsY+yBuffer] = 1
                countAudibilitySquares = countAudibilitySquares + 1

            # There is any building on tested square
            if uibTest>=0:
                if cfg.BuildingGroundMode != 'levels':
                    zStart = buildings[uibTest*env.sizeBuilding+1]
                else:
                    zStart = ground[xCell*boundsY+yCell]
                floors = buildings[uibTest*env.sizeBuilding]
                for floor in range(floors): # Loop through floors

                    # Check building voxel audibility
                    flag = CheckAudibility(xBuffer, yBuffer, zStart+floor, uibTest, floor, xCell, yCell, zCell, uibMegaphone)
                    countCheckedVoxels = countCheckedVoxels + 1
                    if flag:
                        audibilityVoxels[ VoxelIndex[xBuffer*boundsY+yBuffer] + floor ] = 1
                        countAudibilityVoxels = countAudibilityVoxels + 1

            idxBuffer = idxBuffer + cellsSize # Go to next test cell

        idxCell = idxCell + cellsSize # Go to next megaphone cell

    env.logger.success('Finish calculation for Megaphone #{}. {} ({}) audibility squares found. {} ({}) audibility voxels found',
                       uim, env.printLong(countAudibilitySquares), f'{countAudibilitySquares/countCheckedSquares:.0%}', 
                       env.printLong(countAudibilityVoxels), f'{countAudibilityVoxels/countCheckedVoxels:.0%}')

# ============================================
# Calculate audibility of all squares and voxels
# ============================================
def CalculateAudibility():

    # Collect array of processes parameters
    params = []
    for uim in range(env.countMegaphones):
        params.append((uim,))

    # Shcedule processes
    with mp.Pool(processes=mp.cpu_count(), initializer=InitializeAudibilityOfMegaphone, 
                 initargs=(env.sizeCell, env.MegaphonesCells, env.MegaphonesCells_count, env.MegaphonesCells_index,
                           env.MegaphonesBuffers, env.MegaphonesBuffers_count, env.MegaphonesBuffers_index,
                           env.bounds[0], env.bounds[1], env.bounds[2], env.ground, env.audibility2D, env.uib, env.VoxelIndex,
                           env.audibilityVoxels, env.sizeBuilding, env.buildings)) as pool:
        pool.starmap(CalculateAudibilityOfMegaphone, params)

