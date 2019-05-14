# Utility routines to help with variables

# A global counter to help with unique variable numbering.

unique_var_index = 0

def unique_name(name, is_class_var = False):
    r'''Will return a new C++ legal variable name that has been made unique with an index.

    name - Base name of the variable. For example, if it is "dude", then "dude7" might be the result.
    is_class_var - If true, this is intended to be defined at the class level. A "_" is added as prefix.

    returns:

    String of a new variable number.
    '''

    global unique_var_index
    v_name = ("_" if is_class_var else "") + name + str(unique_var_index)
    unique_var_index += 1
    return v_name
