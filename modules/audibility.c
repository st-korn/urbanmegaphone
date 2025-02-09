/** 
 * Library audibility.so
 * Calculate audibility of surface squares and buildings voxels in multiprocessing mode
 * Used from python module audibility.py
*/

#include <math.h>
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
 * @param possible_distance_int The distance of possible audibility in the buildings.
 * @param audibility_prev The previous value of audibility of the destination voxel.
 * @return signed char:
 * 2 if the destination voxel is audible and distance between them and sound source is less than possible_distance_int,
 * 1 if the destination voxel is audible but distance between them and sound source is more than possible_distance_int,
 * -1 otherwise.
 */
signed char check_audibility(signed long x_dst, signed long y_dst, signed long z_dst, signed long uib_dst, 
    signed long x_src, signed long y_src, signed long z_src, signed long uib_src, 
    unsigned int bounds_y, signed short *ground, signed long *uibs, 
    unsigned int building_size, unsigned short *buildings, 
    unsigned char building_ground_mode, double size_step, 
    unsigned char flag_calculate_audibility, double possible_distance_int,
    signed char audibility_prev) {

    // Voxel is just audible. Nothing to check
    if (audibility_prev > 1) {
        return audibility_prev;
    }

    // Calculate distance between source and destination voxels
    double dx = x_dst - x_src;
    double dy = y_dst - y_src;
    double dz = z_dst - z_src;
    double distance = sqrt(dx * dx + dy * dy + dz * dz);

    
    // Check, if we can not improve audibility of the destination voxel
    if ((distance > possible_distance_int) && (audibility_prev > 0)) {
        return audibility_prev;
    }

    // Avoid division by zero
    if (distance == 0) { 
        return 2;
    }
    
    // Check if the distance is greater than the distance of possible audibility in the buildings
    unsigned char target = 1;
    if (distance <= possible_distance_int) { 
        target = 2;
    }

    // Check if we do not need to calculate audibility
    if (flag_calculate_audibility == 0) {
        return target;
    }

    // Common building is audibility by default
    if ((uib_src >= 0) && (uib_dst == uib_src)) {
        return target;
    }

    // Find the maximum distance along the axes
    double max_axis_distance = fmax(fmax(abs(dx), abs(dy)), abs(dz)); 
    // Calculate step size on the longest axis to check audibility of voxels
    double step = size_step / max_axis_distance; 

    // Analyze segment between source and destination voxels
    // We move in small steps along the segment and check for extraneous buildings or the earth's surface.
    double t = 0.0;
    while (t <= 1.0) {

        // Calculate coordinates of the Intermediate voxel (x, y, z) on the segment
        signed long x = round(x_src + t * dx);
        signed long y = round(y_src + t * dy);
        signed long z = round(z_src + t * dz);
        signed long uib = uibs[x * bounds_y + y];
        
        // if intermediate voxel does not belong to source or destination buildings
        if ((uib >= 0) && (uib != uib_src) && (uib != uib_dst)) {
            // If there is an extraneous building on the intermediate voxel, check if the intermediate voxel is higher than the building
            if (z < (get_first_building_voxel(x, y, uib, bounds_y, ground, building_size, buildings, building_ground_mode) + buildings[uib * building_size])) {
                // If previous audibility was better, return it
                return (audibility_prev > 0 ? audibility_prev : -1);
            }
        }

        // If there is no building there, check if the intermediate voxel is higher than the earth's surface
        if (uib < 0) {
            if (z < (ground[x * bounds_y + y] - 1)) { // smoothing out the steps of the earth's surface
                // If previous audibility was better, return it
                return (audibility_prev > 0 ? audibility_prev : -1);
            }
        }

        t += step; // Go to the next step on the segment
    }

    // If no obstacles were found, the destination voxel is audible
    return target;
}


void calculate_audibility_of_megaphone(unsigned long uim, unsigned short cells_size, 
    signed long *cells, signed long *cells_count, signed long *cells_index,
    signed long *buffers_int, signed long *buffers_int_count, signed long *buffers_int_index,
    signed long *buffers_ext, signed long *buffers_ext_count, signed long *buffers_ext_index,
    unsigned int bounds_x, unsigned int bounds_y, unsigned int bounds_z, signed short *ground,
    signed char *audibility_2d, signed long *uibs, unsigned long *voxel_index, 
    signed char *audibility_voxels, unsigned int building_size, unsigned short *buildings, 
    unsigned long long *made_checks, signed int height_standalone_megaphone,
    unsigned char building_ground_mode, float size_step,
    unsigned char flag_calculate_audibility, float possible_distance_int,
    unsigned long long *count_checked_squares, unsigned long long *count_audibility_squares,
    unsigned long long *count_checked_voxels, unsigned long long *count_audibility_voxels) {
    
    // Loop through megaphones cells
    signed long idx_cell = cells_index[uim];
    for (signed long i = 0; i < cells_count[uim]; i++) {

        // Get coordinates of the megaphone cell
        signed long x_cell = cells[idx_cell];
        signed long y_cell = cells[idx_cell + 1];

        // # UIB of megaphone building (if exists)
        signed long uib_megaphone = uibs[x_cell * bounds_y + y_cell];

        // Calculate height of megaphone
        signed long z_cell;
        if (uib_megaphone < 0) {
            z_cell = ground[x_cell * bounds_y + y_cell] + height_standalone_megaphone;
        } else {
            z_cell = get_first_building_voxel(x_cell, y_cell, uib_megaphone, bounds_y, ground, building_size, buildings, building_ground_mode);
        }

        // Loop through internal and external buffers
        signed long idx_buffer_int = buffers_int_index[uim];
        for (signed long  j = 0; j < buffers_int_count[uim]; j++) {

            // Coordinates of test cell
            signed long  x_buffer = buffers_int[idx_buffer_int];
            signed long  y_buffer = buffers_int[idx_buffer_int + 1];

            // UIB building on test cell (if exists)
            signed long  uib_test = uibs[x_buffer * bounds_y + y_buffer];
            signed long  z_start = ground[x_buffer * bounds_y + y_buffer];

            // There is any building on tested square
            if (uib_test >= 0) {

                unsigned short flats = buildings[uib_test * building_size + 2];
                
                // If this is a living building
                if (flats > 0) {

                    z_start = get_first_building_voxel(x_buffer, y_buffer, uib_test, bounds_y, ground, building_size, buildings, building_ground_mode);
                    unsigned short floors = buildings[uib_test * building_size];

                    // Loop through floors of the building
                    for (unsigned short floor = 0; floor < floors; floor++) {

                        // Check audibility of each voxel of the building
                        (*count_checked_voxels)++;
                        signed char flag = audibility_voxels[voxel_index[x_buffer * bounds_y + y_buffer] + floor];
                        flag = check_audibility(x_buffer, y_buffer, z_start + floor, uib_test, 
                            x_cell, y_cell, z_cell, uib_megaphone,
                            bounds_y, ground, uibs, 
                            building_size, buildings, 
                            building_ground_mode, size_step, 
                            flag_calculate_audibility, possible_distance_int, flag);
                        audibility_voxels[voxel_index[x_buffer * bounds_y + y_buffer] + floor] = flag;
                        (*count_audibility_voxels) += (flag>0 ? 1 : 0);
                    }
                }
            }
            idx_buffer_int += cells_size; // Go to next test cell
        }

        // Loop through buffer zone on the streets
        signed long idx_buffer_ext = buffers_ext_index[uim];
        for (signed long j = 0; j < buffers_ext_count[uim]; j++) {
            
            // Coordinates of test cell
            signed long x_buffer = buffers_ext[idx_buffer_ext];
            signed long y_buffer = buffers_ext[idx_buffer_ext + 1];

            // UIB building on test cell (if exists)
            signed long uib_test = uibs[x_buffer * bounds_y + y_buffer];
            signed long z_start = ground[x_buffer * bounds_y + y_buffer];

            // Check ground square audibility
            (*count_checked_squares)++;
            signed char flag = audibility_2d[x_buffer * bounds_y + y_buffer];
            flag = check_audibility(x_buffer, y_buffer, z_start, uib_test, 
                x_cell, y_cell, z_cell, uib_megaphone,
                bounds_y, ground, uibs, 
                building_size, buildings, 
                building_ground_mode, size_step, 
                flag_calculate_audibility, possible_distance_int, flag);
            audibility_2d[x_buffer * bounds_y + y_buffer] = flag;
            (*count_audibility_squares) += (flag>0 ? 1 : 0);

            idx_buffer_ext += cells_size;
        }

        idx_cell += cells_size;
        made_checks[uim] += buffers_int_count[uim] + buffers_ext_count[uim];
    }

}