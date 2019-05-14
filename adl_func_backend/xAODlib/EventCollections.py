# Collected code to get collections from the event object
import cpplib.cpp_ast as cpp_ast
import ast
from cpplib.cpp_vars import unique_name
from cpplib.cpp_representation import cpp_collection, cpp_variable


# all the collections types that are available. This is required because C++
# is strongly typed, and thus we have to transmit this information.
collections = [
    {
        'function_name': "Jets",
        'include_files': ['xAODJet/JetContainer.h'],
        'container_type': 'const xAOD::JetContainer*'
    },
    {
        'function_name': "Tracks",
        'include_files': ['xAODTracking/TrackParticleContainer.h'],
        'container_type': 'const xAOD::TrackParticleContainer*'
    },
    {
        'function_name': "EventInfo",
        'include_files': ['xAODEventInfo/EventInfo.h'],
        'container_type': 'const xAOD::EventInfo*',
        'is_collection': False,
    },
    {
        'function_name': "TruthParticles",
        'include_files': ['xAODTruth/TruthParticleContainer.h'],
        'container_type': 'const xAOD::TruthParticleContainer*',
    },
]

def getCollection(info, call_node):
    r'''
    Return a cpp ast for accessing the jet collection
    '''
    # Get the name jet collection to look at.
    if len(call_node.args) != 1:
        raise BaseException("Calling {0} - only one argument is allowed".format(info['function_name']))
    if type(call_node.args[0]) is not ast.Str:
        raise BaseException("Calling {0} - only acceptable argument is a string".format(info['function_name']))

    # Fill in the CPP block next.
    r = cpp_ast.CPPCodeValue()
    r.args = ['collection_name',]
    r.include_files += info['include_files']

    r.running_code += ['{0} result = 0;'.format(info['container_type']),
                        'ANA_CHECK (evtStore()->retrieve(result, collection_name));']
    r.result = 'result'

    is_collection = info['is_collection'] if 'is_collection' in info else True
    if is_collection:
        r.result_rep = cpp_collection(unique_name(info['function_name'].lower()), scope=None, cpp_type=info['container_type'], is_pointer=True)
    else:
        r.result_rep = cpp_variable(unique_name(info['function_name'].lower()), scope=None, cpp_type=info['container_type'], is_pointer=True)

    # Replace it as the function that is going to get called.
    call_node.func = r

    return call_node

# Config everything.
def create_higher_order_function(info):
    'Creates a higher-order function because python scoping is broken'
    return lambda call_node: getCollection(info, call_node)

for info in collections:
    cpp_ast.method_names[info['function_name']] = create_higher_order_function(info)
