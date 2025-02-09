/** 
 * Library audibility.so
 * Calculate audibility of surface squares and buildings voxels in multiprocessing mode
 * Used from python module audibility.py
*/

#include <math.h>
#include <stdbool.h>

/**
 * @brief Retrieves integer vertical coordinate of the first voxel of building in (x, y) cell with UIB=uib. uib cannot be negative. Do not use this function for a cells without buildings.
 *
 * @param x The x-coordinate of cell.
 * @param y The y-coordinate of cell.
 * @param uib The unique identificator of building.
 * @param bounds_y The y-dimension size of the world.
 * @param ground Pointer to the signed short array with ground levels.
 * @param building_size The size of each building entry in the buildings array.
 * @param buildings Pointer to unsigned short array of building information.
 * @param building_ground_mode Mode to determine ground point of buildings:
 *       0 - each voxel of building positioned at its own ground level
 *       1..n - each voxel of building positioned at the common level for the entire building
 * @return unsigned short vertical coordinate of the first voxel of building
 */
unsigned short get_first_building_voxel(unsigned int x, unsigned int y, 
    unsigned long uib, unsigned int bounds_y, signed short *ground, 
    unsigned int building_size, unsigned short *buildings, 
    unsigned char building_ground_mode) {
        if (building_ground_mode > 0) {
            return buildings[uib * building_size + 1];
        } else {
            return ground[x * bounds_y + y];
        }
}

/**
 * @brief Check audibility on destination voxel with integer coordinates (xDst, yDst, zDst)
 * from megaphone on source voxel with integer coordinates (xSrc, ySrc, zSrc)
 * uibDst - UIB of building on checked destination voxel, -1 if not exists
 * uibSrc - UIB of building, where is source megaphone based
 *
 * @param x_dst The x-coordinate of the destination voxel.
 * @param y_dst The y-coordinate of the destination voxel.
 * @param z_dst The z-coordinate of the destination voxel.
 * @param uib_dst The unique identificator of the destination building (if exists).
 * @param x_src The x-coordinate of the source voxel.
 * @param y_src The y-coordinate of the source voxel.
 * @param z_src The z-coordinate of the source voxel.
 * @param uib_src The unique identificator of the source building (if exists).
 * @param bounds_y The y-dimension size of the world.
 * @param ground Pointer to the signed short array with ground levels.
 * @param uibs Pointer to the signed long array of building identificators.
 * @param building_size The size of each building entry in the buildings array.
 * @param buildings Pointer to unsigned short array of building information.
 * @param building_ground_mode Mode to determine ground point of buildings:
 *       0 - each voxel of building positioned at its own ground level
 *       1..n - each voxel of building positioned at the common level for the entire building
 * @param size_step The step size for checking audibility of voxels.
 * @param flag_calculate_audibility Flag to calculate audibility (1) or not (0).
 * @return unsigned char 1 if the destination voxel is audible, 0 otherwise.
 */
unsigned char check_audibility(unsigned int x_dst, unsigned int y_dst, 
    unsigned int z_dst, signed long uib_dst, unsigned int x_src, 
    unsigned int y_src, unsigned int z_src, signed long uib_src, 
    unsigned int bounds_y, signed short *ground, signed long *uibs, 
    unsigned int building_size, unsigned short *buildings, 
    unsigned char building_ground_mode, float size_step, 
    unsigned char flag_calculate_audibility) {

    // Check if we do not need to calculate audibility
    if (flag_calculate_audibility == 0) {
        return 1;
    }

    // Common building is audibility by default
    if ((uib_src >= 0) && (uib_dst == uib_src)) {
        return 1;
    }
    
    // Calculate distance between source and destination voxels
    int dx = x_dst - x_src;
    int dy = y_dst - y_src;
    int dz = z_dst - z_src;
    float distance = sqrt(dx * dx + dy * dy + dz * dz);
    if (distance == 0) { // Avoid division by zero
        return 1;
    }
    int max_axis_distance = fmax(fmax(abs(dx), abs(dy)), abs(dz));
    float step = size_step / max_axis_distance; // Step size to check audibility of voxels

    // Analyze segment between source and destination voxels
    // We move in small steps along the segment and check for extraneous buildings or the earth's surface.
    float t = 0.0;
    while (t <= 1.0) {
        // Calculate coordinates of the Intermediate voxel (x, y, z) on the segment
        int x = round(x_src + t * dx);
        int y = round(y_src + t * dy);
        int z = round(z_src + t * dz);
        long uib = uibs[x * bounds_y + y];

        // if intermediate voxel does not belong to source or destination buildings
        if ((uib >= 0) && (uib != uib_src) && (uib != uib_dst)) {
            // If there is an extraneous building on the intermediate voxel, check if the intermediate voxel is higher than the building
            if (z < (get_first_building_voxel(x, y, uib, bounds_y, ground, building_size, buildings, building_ground_mode) + buildings[uib * building_size])) {
                return 0;
            }
        }

        // If there is no building there, check if the intermediate voxel is higher than the earth's surface
        if (uib < 0) {
            if (z < (ground[x * bounds_y + y] - 1)) { // smoothing out the steps of the earth's surface
                return 0;
            }
        }

        t += step; // Go to the next step on the segment
    }

    // If no obstacles were found, the destination voxel is audible
    return 1;
}