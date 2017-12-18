"""Main module to run Sandbox server"""
from os import geteuid, path, chdir
import subprocess
from shutil import copy2
from json import dumps, loads
#from uuid import uuid4
try:
    from flask import Flask, request
except ImportError:
    print "You have to install flask: pip install flask"
    exit()
if not geteuid() == 0:
    print "You must be root in order to run this application"
    exit()
if not path.isdir("isolate"):
    subprocess.call("git submodule update --init", shell=True)
if not path.isfile("isolate/isolate"):
    chdir("isolate")
    subprocess.call("make isolate", shell=True)
    chdir("..")
if not path.isfile("/usr/local/etc/isolate"):
    copy2("isolate/default.cf", "/usr/local/etc/isolate")
subprocess.call("isolate/isolate --cleanup", shell=True)
isolate_sandbox = subprocess.Popen("./isolate/isolate --init", shell=True, stdout=subprocess.PIPE).stdout.read().replace("\n", '')
app = Flask(__name__)
@app.route('/')
def hello_world():
    """Home page"""
    return '<h1>Sandbox backend</h1>'
@app.route('/run', methods=['GET', 'POST'])
def esegui():
    """Run code with input and return output"""
    global isolate_sandbox
    if not request.method == "POST":
        return """
    <h1>Invalid request</h1>
    <form method="POST" action="run">
    <textarea name="code"></textarea><br>
    <textarea name="input"></textarea><br>
    Time: <input type="text" name="time"><br>
    Mem: <input type="text" name="memory"><br>
    <input type="submit">
    """
    file_write = open(isolate_sandbox+"/box/run.cpp", 'w')
    file_write.write(request.form["code"])
    file_write.close()
    file_write = open(isolate_sandbox+"/box/input.txt", 'w')
    file_write.write(request.form["input"])
    file_write.close()
    subprocess.call("cd "+isolate_sandbox+"/box&&g++ -std=c++0x run.cpp", shell=True)
    time = float(request.form["time"])
    memory = int(float(request.form["memory"])*1000)
    res = subprocess.Popen("./isolate/isolate --run a.out -t "
                           "" + str(time) + " -w " + str(3*time) + " -m " + str(memory) + " <"
                           " "+isolate_sandbox+"/box/input.txt > "+isolate_sandbox+"/box/output"
                           ".txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res.wait()
    exec_res = open(isolate_sandbox+"/box/output.txt", 'r').read()
    subprocess.call("isolate/isolate --cleanup", shell=True)
    isolate_sandbox = subprocess.Popen("./isolate/isolate --init", shell=True, stdout=subprocess.PIPE).stdout.read().replace("\n", '')
    return dumps({"output":exec_res, "exit_status":res.stderr.read()})
app.run(host='0.0.0.0', port=loads(open("config.json").read())["port"])
