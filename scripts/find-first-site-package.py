# Found on
#  https://gist.github.com/asimihsan/9186003

from distutils.sysconfig import get_python_lib

def getsitepackages():
    """Returns a list containing all global site-packages directories
    (and possibly site-python).

    For each directory present in the global ``PREFIXES``, this function
    will find its `site-packages` subdirectory depending on the system
    environment, and will return a list of full paths.
    """
    sitepackages = []
    seen = set()

    for prefix in PREFIXES:
        if not prefix or prefix in seen:
            continue
        seen.add(prefix)

        if sys.platform in ('os2emx', 'riscos'):
            sitepackages.append(os.path.join(prefix, "Lib", "site-packages"))
        elif os.sep == '/':
            sitepackages.append(
                os.path.join(prefix, "lib64", "python" + sys.version[:3], "site-packages")
            )
            sitepackages.append(
                os.path.join(prefix, "lib", "python" + sys.version[:3], "site-packages")
            )
            sitepackages.append(os.path.join(prefix, "lib", "site-python"))
        else:
            sitepackages.append(prefix)
            sitepackages.append(os.path.join(prefix, "lib64", "site-packages"))
            sitepackages.append(os.path.join(prefix, "lib", "site-packages"))
        if sys.platform == "darwin":
            # for framework builds *only* we add the standard Apple
            # locations.
            from sysconfig import get_config_var
            framework = get_config_var("PYTHONFRAMEWORK")
            if framework:
                sitepackages.append(
                    os.path.join("/Library", framework, sys.version[:3], "site-packages")
                )
    return sitepackages

if __name__ == "__main__":
    # print(getsitepackages()[0])
    print(get_python_lib()[0])
