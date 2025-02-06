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
import modules.environment as env # Environment defenition

# ============================================
# Initialize calculation audibility of squares and voxels by the specific megaphone
# Retrieve scalar variables from parameters of function 
# and store them in global variables of this module of current proccess
# ============================================
def InitializeAudibilityOfMegaphone(pCellsSize, pCells, pCellsCount, pCellsIndex, pBuffers, pBuffersCount, pBuffersIndex,
                                   pBoundsX, pBoundsY, pBoundsZ, pGround, pShmemAudibility2D, pUIB, pVoxelIndex,
                                   pAudibilityVoxels, pBuildingsSize, pBuildings):
    global cellsSize, cells, cells_count, cells_index, buffers, buffers_count, buffers_index
    global boundsX, boundsY, boundsZ, ground, audibility2D, uib, VoxelIndex
    global audibilityVoxels, buildingsSize, buildings
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
    shm2D = SharedMemory(name=pShmemAudibility2D)
    audibility2D = (ctypes.c_byte * (boundsX*boundsY)).from_buffer(shm2D.buf)
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
    
    # Loop through buffer zone
    idx = buffers_index[uim]
    count = 0
    for i in range(buffers_count[uim]):
        x = buffers[idx]
        y = buffers[idx+1]
        #audibility2D[x*boundsX+y] = 1
        idx = idx + cellsSize
        count = count + 1

    env.logger.success('Finish calculation for Megaphone #{}. {} audibility squares found', uim, count)

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
                           env.bounds[0], env.bounds[1], env.bounds[2], env.ground, env.shmemAudibility2D.name, env.uib, env.VoxelIndex,
                           env.audibilityVoxels, env.sizeBuilding, env.buildings)) as pool:
        pool.starmap(CalculateAudibilityOfMegaphone, params)

