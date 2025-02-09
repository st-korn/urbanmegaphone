# ============================================
# Module: Calculate audibility of surface squares and buildings voxels in multiprocessing mode
# ============================================

# Modules import
# ============================================

# Standart modules
import multiprocessing as mp # Use multiprocessing
from multiprocessing.shared_memory import SharedMemory # Use shared memory
import ctypes # Use primitive datatypes for multiprocessing data exchange
import time # For updating multiprocessing progress bar

# Own core modules
import modules.settings as cfg # Settings defenition
import modules.environment as env # Environment defenition

'''
# ============================================
# Get integer vertical coordinate of the first voxel of building in (x, y) cell with UIB=uib
# x, y - integer coordinates of cell
# uib - integer UIB of building
# uib cannot be negative. Do not use this function for a cells without buildings
# ============================================
def GetFirstBuildingVoxel(x, y, uib):
    # Global variables
    global boundsY, ground, buildingsSize, buildings
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
    global boundsY, ground, uibs, buildingsSize, buildings

    # Check if we do not need to calculate audibility
    if not(cfg.flagCalculateAudibility):
        return True

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
        # starting from the source voxel (xSrc, ySrc, zSrc) with the step t
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
            if z < (ground[x* boundsY+y] - 1): # smoothing out the steps of the earth's surface
                return False

        t = t + step # Go to the next step on the segment

    # If no obstacles were found, the destination voxel is audible
    return True
'''

# ============================================
# Initialize calculation audibility of squares and voxels by the specific megaphone
# Retrieve scalar variables from parameters of function 
# and store them in global variables of this module of current proccess
# ============================================
def InitializeAudibilityOfMegaphone(pCellsSize, pCells, pCellsCount, pCellsIndex, 
                                    pBuffersInt, pBuffersIntCount, pBuffersIntIndex,
                                    pBuffersExt, pBuffersExtCount, pBuffersExtIndex,
                                    pBoundsX, pBoundsY, pBoundsZ, pGround, pAudibility2D, pUIB, pVoxelIndex,
                                    pAudibilityVoxels, pBuildingsSize, pBuildings, 
                                    pMegaphonesCount, pMegaphonesLeft, pMadeChecks):
    global lib
    global cellsSize, cells, cells_count, cells_index, \
           buffersInt, buffersInt_count, buffersInt_index, \
           buffersExt, buffersExt_count, buffersExt_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, \
           megaphonesCount, megaphonesLeft, madeChecks

    # Store parameters in global variables
    cellsSize = pCellsSize # integer
    cells = (ctypes.c_long * len(pCells)).from_buffer(pCells)
    cells_count = (ctypes.c_long * len(pCellsCount)).from_buffer(pCellsCount)
    cells_index = (ctypes.c_long * len(pCellsIndex)).from_buffer(pCellsIndex)
    buffersInt = (ctypes.c_long * len(pBuffersInt)).from_buffer(pBuffersInt)
    buffersInt_count = (ctypes.c_long * len(pBuffersIntCount)).from_buffer(pBuffersIntCount)
    buffersInt_index = (ctypes.c_long * len(pBuffersIntIndex)).from_buffer(pBuffersIntIndex)
    buffersExt = (ctypes.c_long * len(pBuffersExt)).from_buffer(pBuffersExt)
    buffersExt_count = (ctypes.c_long * len(pBuffersExtCount)).from_buffer(pBuffersExtCount)
    buffersExt_index = (ctypes.c_long * len(pBuffersExtIndex)).from_buffer(pBuffersExtIndex)
    boundsX = pBoundsX # integer
    boundsY = pBoundsY # integer
    boundsZ = pBoundsZ # integer
    ground = (ctypes.c_short * len(pGround)).from_buffer(pGround)
    audibility2D = (ctypes.c_byte * len(pAudibility2D)).from_buffer(pAudibility2D)
    uibs = (ctypes.c_long * len(pUIB)).from_buffer(pUIB)
    VoxelIndex = (ctypes.c_ulong * len(pVoxelIndex)).from_buffer(pVoxelIndex)
    audibilityVoxels = (ctypes.c_byte * len(pAudibilityVoxels)).from_buffer(pAudibilityVoxels)
    buildingsSize = pBuildingsSize # integer
    buildings = (ctypes.c_ushort * len(pBuildings)).from_buffer(pBuildings)
    megaphonesCount = pMegaphonesCount # integer
    megaphonesLeft = (ctypes.c_ubyte * len(pMegaphonesLeft)).from_buffer(pMegaphonesLeft)
    madeChecks = (ctypes.c_ulonglong * len(pMadeChecks)).from_buffer(pMadeChecks)

    # Import functions from C shared library
    lib = ctypes.CDLL('./audibility.so')
    # get_first_building_voxel function
    lib.get_first_building_voxel.argtypes = (ctypes.c_uint, ctypes.c_uint, 
                                             ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_short), 
                                             ctypes.c_uint, ctypes.POINTER(ctypes.c_ushort), ctypes.c_ubyte)
    lib.get_first_building_voxel.restype = ctypes.c_ushort
    lib.check_audibility.argtypes = (ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_long,
                                     ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.c_long,
                                     ctypes.c_uint, ctypes.POINTER(ctypes.c_short), ctypes.POINTER(ctypes.c_long),
                                     ctypes.c_uint, ctypes.POINTER(ctypes.c_ushort),
                                     ctypes.c_ubyte, ctypes.c_float, 
                                     ctypes.c_ubyte, ctypes.c_float)
    lib.check_audibility.restype = ctypes.c_ubyte

# ============================================
# Calculate audibility of squares and voxels by the specific megaphone
# ============================================
def CalculateAudibilityOfMegaphone(uim):
    # Global variables
    global cellsSize, cells, cells_count, cells_index, \
           buffersInt, buffersInt_count, buffersInt_index, \
           buffersExt, buffersExt_count, buffersExt_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, \
           megaphonesCount, megaphonesLeft, madeChecks
    
    # Global counters
    global countCheckedSquares, countAudibilitySquares, countCheckedVoxels, countAudibilityVoxels
    countCheckedSquares = 0
    countAudibilitySquares = 0
    countCheckedVoxels = 0
    countAudibilityVoxels = 0
    countChecked = 0

    env.logger.debug('Start megaphone #{} of {}', uim+1, megaphonesCount)
    standaloneMegaphoneHeight = round(cfg.heightStansaloneMegaphone / cfg.sizeVoxel)
    flagBuildingGroungMode = 0 if cfg.BuildingGroundMode == 'levels' else 1
    flagCalculateAudibility = 1 if cfg.flagCalculateAudibility else 0

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
            #zCell = GetFirstBuildingVoxel(xCell, yCell, uibMegaphone) + buildings[uibMegaphone*env.sizeBuilding]
            zCell = lib.get_first_building_voxel(xCell, yCell, uibMegaphone, boundsY, ground, 
                                                 buildingsSize, buildings, flagBuildingGroungMode)

        # Loop through buffer zone in the buildings
        idxBufferInt = buffersInt_index[uim]
        for j in range(buffersInt_count[uim]):
            xBuffer = buffersInt[idxBufferInt] # Coordinates of test cell
            yBuffer = buffersInt[idxBufferInt+1]
            uibTest = uibs[xBuffer*boundsY+yBuffer] # UIB building on test cell (if exists)
            zStart = ground[xBuffer*boundsY+yBuffer]

            # There is any building on tested square
            if uibTest>=0:
                flats = buildings[uibTest*buildingsSize+2]
                if flats>0: # If this is a living building
                    #zStart = GetFirstBuildingVoxel(xBuffer, yBuffer, uibTest)
                    zStart = lib.get_first_building_voxel(xBuffer, yBuffer, uibTest, boundsY, ground, 
                                                          buildingsSize, buildings, flagBuildingGroungMode)
                    floors = buildings[uibTest*buildingsSize]
                    # Loop through floors of building
                    for floor in range(floors):
                        # Check building voxel audibility
                        countCheckedVoxels = countCheckedVoxels + 1
                        flag = (audibilityVoxels[ VoxelIndex[xBuffer*boundsY+yBuffer] + floor ] > 1)
                        if not(flag): # If voxel is not audibility yet
                            #flag = CheckAudibility(xBuffer, yBuffer, zStart+floor, uibTest, xCell, yCell, zCell, uibMegaphone)
                            flag = lib.check_audibility(xBuffer, yBuffer, zStart+floor, uibTest, xCell, yCell, zCell, uibMegaphone,
                                                        boundsY, ground, uibs, buildingsSize, buildings, 
                                                        flagBuildingGroungMode, cfg.sizeStep, 
                                                        flagCalculateAudibility, cfg.distancePossibleAudibilityInt/cfg.sizeVoxel)   
                            audibilityVoxels[ VoxelIndex[xBuffer*boundsY+yBuffer] + floor ] = (flag if flag>0 else -1)
                        countAudibilityVoxels = countAudibilityVoxels + (1 if flag else 0)

            idxBufferInt = idxBufferInt + cellsSize # Go to next test cell

        # Loop through buffer zone on the streets
        idxBufferExt = buffersExt_index[uim]
        for j in range(buffersExt_count[uim]):
            xBuffer = buffersExt[idxBufferExt] # Coordinates of test cell
            yBuffer = buffersExt[idxBufferExt+1]
            uibTest = uibs[xBuffer*boundsY+yBuffer] # UIB building on test cell (if exists)
            zStart = ground[xBuffer*boundsY+yBuffer]

            # Check ground square audibility
            countCheckedSquares = countCheckedSquares + 1
            flag = (audibility2D[xBuffer*boundsY+yBuffer] > 1)
            if not(flag): # If voxel is not audibility yet
                #flag = CheckAudibility(xBuffer, yBuffer, zStart, uibTest, xCell, yCell, zCell, uibMegaphone)
                flag = lib.check_audibility(xBuffer, yBuffer, zStart, uibTest, xCell, yCell, zCell, uibMegaphone,
                            boundsY, ground, uibs, buildingsSize, buildings, 
                            flagBuildingGroungMode, cfg.sizeStep, 
                            flagCalculateAudibility, cfg.distancePossibleAudibilityInt/cfg.sizeVoxel)
                audibility2D[xBuffer*boundsY+yBuffer] = (flag if flag>0 else -1)
            countAudibilitySquares = countAudibilitySquares + (1 if flag else 0)

            idxBufferExt = idxBufferExt + cellsSize # Go to next test cell

        idxCell = idxCell + cellsSize # Go to next megaphone cell
        countChecked = countChecked + buffersInt_count[uim] + buffersExt_count[uim]
        madeChecks[uim] = countChecked

    megaphonesLeft[uim] = 0
    env.logger.debug("Finish #{}. {} combinations checked. {} ({}) audibility squares, {} ({}) audibility voxels found",
                       uim+1, env.printLong(countChecked),
                       env.printLong(countAudibilitySquares), f'{countAudibilitySquares/countCheckedSquares:.0%}', 
                       env.printLong(countAudibilityVoxels), f'{countAudibilityVoxels/countCheckedVoxels:.0%}' )
    env.logger.debug("{} tasks left: {} done",
                    megaphonesLeft.value, f'{(1-megaphonesLeft.value/megaphonesCount):.0%}' )

# ============================================
# Calculate audibility of all squares and voxels
# ============================================
def CalculateAudibility():
    env.logger.info("Switching to multiprocessing mode...")
    env.logger.info("Please note that due the CPU cores, the actual time may be x2 long as expected at first...")

    # Collect array of processes parameters
    params = []
    for uim in range(env.countMegaphones):
        params.append((uim,))

    # Schedule processes
    with mp.Pool(processes=mp.cpu_count(), initializer=InitializeAudibilityOfMegaphone, 
                 initargs=(env.sizeCell, env.MegaphonesCells, env.MegaphonesCells_count, env.MegaphonesCells_index,
                           env.MegaphonesBuffersInt, env.MegaphonesBuffersInt_count, env.MegaphonesBuffersInt_index,
                           env.MegaphonesBuffersExt, env.MegaphonesBuffersExt_count, env.MegaphonesBuffersExt_index,
                           env.bounds[0], env.bounds[1], env.bounds[2], env.ground, env.audibility2D, env.uib, env.VoxelIndex,
                           env.audibilityVoxels, env.sizeBuilding, env.buildings, 
                           env.countMegaphones, env.leftMegaphones, env.madeChecks)) as pool:
        result = pool.starmap_async(CalculateAudibilityOfMegaphone, params)

        # Show progress bar
        with env.tqdm(total=env.totalChecks) as pbar:
            while not result.ready():
                madeChecks = 0
                for check in env.madeChecks:
                    madeChecks = madeChecks + check
                pbar.update(madeChecks - pbar.n)
                leftMegaphones = 0
                for left in env.leftMegaphones:
                    leftMegaphones = leftMegaphones + left
                pbar.set_description(str(leftMegaphones)+" processes left")
                time.sleep(0.1)
