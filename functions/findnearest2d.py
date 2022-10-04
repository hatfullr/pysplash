def find_nearest_2d(array, value, kind='cdist', output='index'):
    # 'array' must be a 2D array
    # 'value' must be a 1D array with 2 elements
    # 'kind' defines what method to use to calculate the distances. Can choose one
    #    of 'cdist' (default) or 'euclidean'. Choose 'euclidean' for very large
    #    arrays. Otherwise, cdist is much faster.
    # 'output' defines what the output should be. Can be 'index' (default) to return
    #    the index of the array that is closest to the value, 'value' to return the
    #    value that is closest, or 'both' to return index,value
    import numpy as np
    if kind == 'cdist':
        try: from scipy.spatial.distance import cdist
        except ImportError:
            print("Warning (find_nearest_2d): Could not import cdist. Reverting to simpler distance calculation")
            kind = 'euclidean'
    array = np.array(array)
    value = np.array(value)
    array[~np.isfinite(array)] = np.nan
    index = np.where(array == value)[0] # Make sure the value isn't in the array
    if index.size == 0:
        if kind == 'cdist': index = np.nanargmin(cdist([value],array)[0])
        elif kind == 'euclidean': index = np.nanargmin(np.sum((array-value)**2.,axis=1))
        else: raise ValueError("Keyword 'kind' must be one of 'cdist' or 'euclidean'")
    if output == 'index': return index
    elif output == 'value': return array[index]
    elif output == 'both': return index,array[index]
    else: raise ValueError("Keyword 'output' must be one of 'index', 'value', or 'both'")
