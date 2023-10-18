
import os
import re
import subprocess
import  random
from datetime import datetime

def command(cmd, cwd=os.getcwd()):
    """ run command in specific directory
    """
    if os.name == 'nt':
        os.environ["COMSPEC"] = "powershell"
    p = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    if len(output) == 0 and len(errors) > 0:
        ret = errors
    else:
        ret = output
    try:
        lines = ret.decode("gb2312")
    except:
        try:
            lines = ret.decode("utf8")
        except:
            lines = ""
    return lines


def getOriginBranches(repo_folder):
    """ get remote repo branches
    """
    out = command("git branch -r ", repo_folder)
    lines = out.splitlines()
    branches = []
    for br in lines:
        br = br.strip().split(" ")[0]
        if br.startswith("origin/"):
            branch = br.replace("origin/", "")
            if branch == "HEAD":
                continue
            branches.append(branch)
    return branches


def start(root):
    remotes = command("git remote -v", root)
    if "not a git repository" in remotes:
        print(f"!!!!!!! not a git repository !!!!!!!")
        return False
    branches = getOriginBranches(root)
    for branch in branches:
        if "_mirror_" in branch:
            print("this is a mirror branch, pass...")
            continue
        command(f"git checkout {branch} ", f)
        # detect force-update
        out = command("git rev-list --abbrev-commit HEAD ^origin", root)
        if len(out) > 0:
            print("detect force update")
            # create mirror branch
            new_branch = branch + "_mirror_" + datetime.now().strftime("%Y%m%d%H%M%S") + "_" + str(random.randint(0, 100))
            command(f"git checkout -b {new_branch} {branch}", root)
            command(f"git checkout {branch} ", f)

        command(f"git reset --hard origin/{branch}", f)
        out2 = command(f"git pull origin", f)
        print(out2)
        print(f"{branch} updated ...")

if __name__ == "__main__":

    root = "/volume1/iCloud/Gitea/mirror"
    dirs = os.listdir(root)
    for entry in dirs:
        f = os.path.join(root, entry)
        if os.path.isdir(f):
            print("====================")
            print(f"check {entry}...")
            start(f)
