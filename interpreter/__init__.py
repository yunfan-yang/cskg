def get_module_prefix(folder_path):
    return ".".join(folder_path.split("/")[0:-1])


def remove_module_prefix(qualified_name, folder_path):
    module_prefix = get_module_prefix(folder_path)
    if qualified_name.startswith(module_prefix):
        return qualified_name.replace(module_prefix + ".", "")
    return qualified_name
