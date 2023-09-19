
import os
import re
import subprocess


def command(cmd, cwd=os.getcwd()):
    """ run command in specific directory
    """
    p = subprocess.Popen(cmd, cwd=cwd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, errors = p.communicate()
    if len(output) == 0 and len(errors) > 0:
        ret = errors
    else:
        ret = output
    try:
        lines = ret.decode('gb2312')
    except:
        try:
            lines = ret.decode('utf8')
        except:
            lines = ''
    return lines


def regexMatch(basename, reg):
    prog = re.compile(reg, re.IGNORECASE | re.X | re.S)
    result = prog.findall(basename)
    return result


def getOriginBranches(repo_folder):
    """ 获取仓库地址内所有 origin 的分支
    """
    out = command('git branch -r ', repo_folder)
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


def detect_forceupdate():
    """
#!/bin/sh
if [ "$1" == "prepared" ]
then
  while read -r line
   do
        #only protect the master / main branch (must be specified which branches to protect)
        ([[ ! "$line" =~ refs\/head\/master$ ]] && [[ ! "$line" =~ refs\/head\/main$ ]]) && continue
        count=$(git rev-list --abbrev-commit $(echo $line|cut -d " " -f 1) ^$(echo $line|cut -d " " -f 2) | wc -l)
        if [ $count -ne 0 ]
        then
                echo $(date) forced update detected in $PWD >> ~/forcedupdates.log
                exit 1
        fi
  done
fi
    """
    print("detect")

    # 获取 origin 分支内的提交记录，从 upstream hex 开始
    # git rev-list --abbrev-commit origin ^upstream
    # 如果有记录，则说明 upstream 低于 origin。则推测为 forced update
    # 存疑，如果撤销后又有新增，是否可以处理？


if __name__ == "__main__":

    root = "E:\\Gitlab\\backup"