from scipy.spatial.distance import cdist
def find_nearest_2d(array, value, output='index'):
    # 'array' must be a 2D array
    # 'value' must be a 1D array with 2 elements
    # 'output' defines what the output should be. Can be 'index' (default) to return
    #    the index of the array that is closest to the value, 'value' to return the
    #    value that is closest, or 'both' to return index,value
    import numpy as np
    array = np.array(array)
    value = np.array(value)
    array[~np.isfinite(array)] = np.nan
    index = np.where(array == value)[0] # Make sure the value isn't in the array
    if index.size == 0:
        index = np.nanargmin(cdist([value],array,method='euclidean')[0])
    if output == 'index': return index
    elif output == 'value': return array[index]
    elif output == 'both': return index,array[index]
    else: raise ValueError("Keyword 'output' must be one of 'index', 'value', or 'both'")
