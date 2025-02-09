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
                                    pMegaphonesCount, pChecksCount,
                                    pMegaphonesLeft, pMadeChecks):
    global lib
    global cellsSize, cells, cells_count, cells_index, \
           buffersInt, buffersInt_count, buffersInt_index, \
           buffersExt, buffersExt_count, buffersExt_index, \
           boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, \
           megaphonesCount, checksCount, \
           megaphonesLeft, madeChecks

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
    checksCount = (ctypes.c_ulonglong * len(pChecksCount)).from_buffer(pChecksCount)
    megaphonesLeft = (ctypes.c_ubyte * len(pMegaphonesLeft)).from_buffer(pMegaphonesLeft)
    madeChecks = (ctypes.c_ulonglong * len(pMadeChecks)).from_buffer(pMadeChecks)

    # Import functions from C shared library
    lib = ctypes.CDLL('./audibility.so')

    # calculate_audibility_of_megaphone function
    lib.calculate_audibility_of_megaphone.argtypes = (ctypes.c_ulong, ctypes.c_ushort,
        ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long),
        ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long),
        ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_long),
        ctypes.c_uint, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(ctypes.c_short), 
        ctypes.POINTER(ctypes.c_byte), ctypes.POINTER(ctypes.c_long), ctypes.POINTER(ctypes.c_ulong),
        ctypes.POINTER(ctypes.c_byte), ctypes.c_uint, ctypes.POINTER(ctypes.c_ushort),
        ctypes.POINTER(ctypes.c_ulonglong), ctypes.c_int,
        ctypes.c_ubyte, ctypes.c_float,
        ctypes.c_ubyte, ctypes.c_float,
        ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong),
        ctypes.POINTER(ctypes.c_ulonglong), ctypes.POINTER(ctypes.c_ulonglong))
    lib.calculate_audibility_of_megaphone.restype = None

# ============================================
# Calculate audibility of squares and voxels by the specific megaphone
# ============================================
def CalculateAudibilityOfMegaphone(num,uim):
    # Global variables
    global cellsSize, cells, cells_count, cells_index, \
           buffersInt, buffersInt_count, buffersInt_index, \
           buffersExt, buffersExt_count, buffersExt_index, \
           boundsX, boundsY, boundsZ, ground, \
           audibility2D, uibs, VoxelIndex, \
           audibilityVoxels, buildingsSize, buildings, \
           megaphonesCount, checksCount, \
           megaphonesLeft, madeChecks
    
    # Global counters
    countCheckedSquares = ctypes.c_ulonglong(0)
    countAudibilitySquares = ctypes.c_ulonglong(0)
    countCheckedVoxels = ctypes.c_ulonglong(0)
    countAudibilityVoxels = ctypes.c_ulonglong(0)

    # Prepare calculation
    env.logger.debug('Start {} (megaphone #{}) of {}: {} checks have been started', 
                     num+1, uim, megaphonesCount, env.printLong(checksCount[uim]))

    # Call C shared library function to calculate audibility 
    # of all cells of this megaphone and its buffer zones
    try:
        lib.calculate_audibility_of_megaphone(uim, cellsSize,
            cells, cells_count, cells_index,
            buffersInt, buffersInt_count, buffersInt_index,
            buffersExt, buffersExt_count, buffersExt_index,
            boundsX, boundsY, boundsZ, ground, audibility2D, uibs, VoxelIndex,
            audibilityVoxels, buildingsSize, buildings, 
            madeChecks, round(cfg.heightStansaloneMegaphone / cfg.sizeVoxel),
            0 if cfg.BuildingGroundMode == 'levels' else 1, cfg.sizeStep,            
            1 if cfg.flagCalculateAudibility else 0, cfg.distancePossibleAudibilityInt/cfg.sizeVoxel,
            ctypes.byref(countCheckedSquares), ctypes.byref(countAudibilitySquares), 
            ctypes.byref(countCheckedVoxels), ctypes.byref(countAudibilityVoxels))
    except Exception as e:
        env.logger.error(e)

    # Finish calculation
    megaphonesLeft[uim] = 0
    env.logger.debug("Finish #{}. {} combinations checked. {} ({}) audibility squares, {} ({}) audibility voxels found",
                       uim+1, env.printLong(madeChecks[uim]),
                       env.printLong(countAudibilitySquares.value), f'{countAudibilitySquares.value/countCheckedSquares.value:.0%}', 
                       env.printLong(countAudibilityVoxels.value), f'{countAudibilityVoxels.value/countCheckedVoxels.value:.0%}' )

# ============================================
# Calculate audibility of all squares and voxels
# ============================================
def CalculateAudibility():

    # Nested function to update progress bar
    def UpdateProgress():
        madeChecks = 0
        for check in env.madeChecks:
            madeChecks = madeChecks + check
        pbar.update(madeChecks - pbar.n)
        leftMegaphones = 0
        for left in env.leftMegaphones:
            leftMegaphones = leftMegaphones + left
        pbar.set_description(str(leftMegaphones)+" processes left")

    env.logger.info("Switching to multiprocessing mode...")
    env.logger.info("Please note that due the CPU cores, the actual time may be x2 long as expected at first...")

    # Collect array of processes parameters
    processes = []
    for uim in range(env.countMegaphones):
        processes.append((uim,env.countChecks[uim]))
    # Order by descending number of checks
    processes.sort(key=lambda x: x[1], reverse=True)
    # Prepare parameters for multiprocessing
    params = []
    for index, (uim, _) in enumerate(processes):
        params.append((index,uim,))

    # Schedule processes
    with mp.Pool(processes=mp.cpu_count(), initializer=InitializeAudibilityOfMegaphone, 
                 initargs=(env.sizeCell, env.MegaphonesCells, env.MegaphonesCells_count, env.MegaphonesCells_index,
                           env.MegaphonesBuffersInt, env.MegaphonesBuffersInt_count, env.MegaphonesBuffersInt_index,
                           env.MegaphonesBuffersExt, env.MegaphonesBuffersExt_count, env.MegaphonesBuffersExt_index,
                           env.bounds[0], env.bounds[1], env.bounds[2], env.ground, env.audibility2D, env.uib, env.VoxelIndex,
                           env.audibilityVoxels, env.sizeBuilding, env.buildings, 
                           env.countMegaphones, env.countChecks,
                           env.leftMegaphones, env.madeChecks)) as pool:
        result = pool.starmap_async(CalculateAudibilityOfMegaphone, params)

        # Show progress bar
        with env.tqdm(total=env.totalChecks) as pbar:
            while not result.ready():
                UpdateProgress()
                time.sleep(0.1)
            UpdateProgress()