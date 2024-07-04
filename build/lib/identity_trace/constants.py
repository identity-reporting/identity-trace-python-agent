import jsonpickle


DEFAULT_FUNCTION_SPECIFIC_CONFIG = dict(
    deep_copy_input = False,
    copy_input = True,
    deep_copy_output = False,
    copy_output = True,
    find_parent = True,
    input_serializer = lambda x: jsonpickle.encode(x, False),
    output_serializer = lambda x: jsonpickle.encode(x, False),
)
