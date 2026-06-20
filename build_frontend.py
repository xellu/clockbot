import os
import shutil
from nautica.ext.Util import rmDir

print("building...")
os.system("cd frontend && npm run build")

print("copying to static...")

rmDir("static")
shutil.copytree("frontend/build", "static")