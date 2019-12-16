import os
import re
import sys
import distutils.sysconfig as sysconfig
import subprocess


class UnknownPythonVersionError(Exception):
    pass


class UnknownPath(Exception):
    pass


class Parser:
    def __init__(self, project_path: str):
        self.project_path = project_path
        self.py_files = []
        self.parse_py_files(self.project_path)
        self.py_files_imports = {}
        self.find_all_imports()

    def parse_py_files(self, path: str):
        for file in os.listdir(path):
            temp_path = os.path.join(path, file)
            if os.path.isdir(temp_path):
                self.parse_py_files(temp_path)
            else:
                file_type = file.split('.')[-1]
                if file_type == 'py':
                    self.py_files.append(temp_path)

    def find_all_imports(self):
        for filename in self.py_files:
            if filename not in self.py_files_imports:
                self.py_files_imports[filename] = []
            with open(filename) as file:
                for line in file.read().split('\n'):
                    regex_data = re.search(r'^(?:from (\S*)|import (\S*))', line)
                    if regex_data:
                        self.py_files_imports[filename].append(regex_data.group(1) or regex_data.group(2))


class PythonLibsSearcher:
    def __init__(self):
        self.python_version = sys.version_info.major
        self.standard_libs = []
        self.libs_parse()

    def libs_parse(self):
        std_lib = sysconfig.get_python_lib(standard_lib=True)
        for top, dirs, files in os.walk(std_lib):
            for nm in files:
                if nm != '__init__.py' and nm[-3:] == '.py':
                    self.standard_libs.append(os.path.join(top, nm)[len(std_lib) + 1:-3].replace(os.sep, '.'))


class LibsInstaller:
    def __init__(self, std_libs: list, project_libs: dict, python_version: int):
        self.std_libs, self.project_libs = std_libs, project_libs
        self.python_version = python_version
        self.check_is_lib_in_std()

    def check_is_lib_in_std(self):
        project_modules_names = [x.split('/')[-1].strip('.py') for x in self.project_libs.keys()]
        for key in self.project_libs:
            for lib in self.project_libs[key]:
                if lib not in self.std_libs:
                    if lib not in project_modules_names:
                        print(f'Find uninstall lib: {lib}')
                        self.lib_installer(lib)

    def lib_installer(self, lib: str):
        if self.python_version in [2, 3]:
            print(f'Install {lib}, python version: {self.python_version}')
            if self.python_version == 3:
                subprocess.run(['pip3', 'install', lib])
            elif self.python_version == 2:
                subprocess.run(['pip2', 'install', lib])
        else:
            raise UnknownPythonVersionError(self.python_version)


def main(project_dir: str):
    python_lib_searcher_obj = PythonLibsSearcher()
    parser_obj = Parser(project_dir)
    LibsInstaller(python_lib_searcher_obj.standard_libs, parser_obj.py_files_imports, python_lib_searcher_obj.python_version)


if __name__ == '__main__':
    if len(sys.argv) == 2:
        if sys.argv[1] in os.listdir(os.path.curdir):
            main(sys.argv[1])
        else:
            raise UnknownPath(f'Unknown path: {sys.argv[1]}')
    else:
        print('Usage:\n  python main.py <dir>')
