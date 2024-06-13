def threaded_function(result_holder, func, args):
    """
    Executes a function with given arguments in a thread and stores the result.
    
    Parameters:
        result_holder (dict): A dictionary to hold the result of the function.
        func (callable): The function to be executed.
        args (tuple): The arguments to be passed to the function.
    """
    try:
        result = func(*args)  # Call the function with the provided arguments
        result_holder['result'] = result  # Store the result in the dictionary
    except Exception as e:
        result_holder['error'] = str(e)  # Store error message in case of failure
