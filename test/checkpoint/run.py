
import os
import subprocess

p = subprocess.Popen(["./a.out"], stderr=subprocess.PIPE)

p.wait()
out, errs = p.communicate()
print(errs)


