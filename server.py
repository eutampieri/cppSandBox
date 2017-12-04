"""Main module to run Sandbox server"""
from os import geteuid, path, chdir
import subprocess
from shutil import copy2
from json import dumps
from uuid import uuid4
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
isolateSandBox = subprocess.Popen("./isolate/isolate --init", shell=True, stdout=subprocess.PIPE).stdout.read().replace("\n",'')
app = Flask(__name__)
@app.route('/')
def hello_world():
    """Home page"""
    return '<h1>Sandbox backend</h1>'
@app.route('/run', methods = ['GET', 'POST'])
def esegui():
    global isolateSandBox
    """Run code with input and return output"""
    if request.method=="GET":
        return """
    <form method="POST" action="run">
    <textarea name="code"></textarea><br>
    <textarea name="input"></textarea><br>
    <input type="submit">
    """
        return "<h1>Invalid request</h1>"
    f=open(isolateSandBox+"/box/run.cpp",'w')
    f.write(request.form["code"])
    f.close()
    f=open(isolateSandBox+"/box/input.txt",'w')
    f.write(request.form["input"])
    f.close()
    subprocess.call("cd "+isolateSandBox+"/box&&g++ -std=c++0x run.cpp", shell=True)
    res=subprocess.Popen("./isolate/isolate --run a.out -t 1 -w 3 -m 50000 < "+isolateSandBox+"/box/input.txt > "+isolateSandBox+"/box/output.txt", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    res.wait()
    execRes=open(isolateSandBox+"/box/output.txt",'r').read()
    subprocess.call("isolate/isolate --cleanup", shell=True)
    isolateSandBox = subprocess.Popen("./isolate/isolate --init", shell=True, stdout=subprocess.PIPE).stdout.read().replace("\n",'')
    return execRes+" - - - "+res.stderr.read()
app.run(host='0.0.0.0', port=19563)
