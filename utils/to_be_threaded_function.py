# Define the function to be run in a thread
def threaded_function(result_holder, func, args):
    result = func(*args)  # Example task: summing the arguments
    result_holder['result'] = result