import os
import json
import glob
import shutil
import re

path = './'
notebooks = [f for f in glob.glob(path + "**/*.ipynb", recursive=True)]
nonNotebookFiles = [f for f in glob.glob(path + "**/*", recursive=True) if ".ipynb" not in f and "./src/" not in f and not os.path.isdir(f)]

shutil.rmtree("./src/", ignore_errors=True)
shutil.copytree('.', './src/', ignore=shutil.ignore_patterns('*.pyc', '*.ipynb', './src/*', '.git'))

for notebook in notebooks:
    lines = []
    outputFileName = notebook.replace('./', './src/').replace('ipynb', 'py')
    for cell in json.load(open(notebook))["cells"]:
        if cell["cell_type"] == "code":
            if len(cell["source"]) > 0:
                if "#export" in cell["source"][0]:
                    cell = cell["source"][1:]
                    for i, line in enumerate(cell):
                        if "import ." in line or "from ." in line:
                            cell[i] = line.replace("src.", ".")
                    lines = lines + cell + ["\n\n"]

    if len(lines) > 0:
        print(outputFileName)
        with open(outputFileName, 'w') as output:
            output.writelines(lines)

