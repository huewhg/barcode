import time
from dataclasses import dataclass
from pathlib import Path

import code128
import flask


@dataclass
class entry:
    """Structure for storing the products
    id: numerical id, user unimportant
    name: FULL NAME of object. Will get printed human readable
    code: the barcode data, will get printed as a barcode AND below it for parity
    code_svg: svg data of the barcode. empty if none generated yet."""
    id:int
    name:str
    code:str
    code_svg:str
    def get_barcode(self) -> str:
        """returns the barcode for the current entry"""
        #print(self.code)
        self.code_svg = code128.svg(self.code)
        return self.code_svg
    def __str__(self):
        codeclean:str = ""
        for i in self.code_svg:
            if i != "\n" and i !="\t" and i != "|":
                codeclean += i
        return f"{self.id}|{self.name}|{self.code}|{codeclean}"
    def __repr__(self):
        return str(self)

        
def parsedb(inp:str) -> entry:
    #print(inp)
    s:list = inp.split("|")
    if len(s) != 4:
        #print(len(s))
        return
    return entry(int(s[0]), s[1], s[2],s[3])
entries: list[entry] = []
p:Path = Path("db.vlsv")
if not p.exists():
    with p.open('w') as dbfile:
        print(f"file {p} created")
else:
    with p.open('r') as dbfile:
        for l in dbfile.readlines():
            e: entry = parsedb(l)
            if e:
                entries.append(e)
    print(f"DBfile {p} already exists")


times:list[int] = []
app = flask.Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    #print(entries)
    
    context = {
        "entries":entries
    }
    return flask.render_template(
        "index.html",
        **context,
    )
    
@app.route("/add", methods=["POST"])
def add():
    start:int = time.time_ns()
    if len(entries) > 0:
        e: entry = entry(
                entries[-1].id + 1, flask.request.form["name"], flask.request.form["code"], ""
            )
    else:
        e: entry = entry(
                        0, flask.request.form["name"], flask.request.form["code"], ""
                    )
    e.get_barcode()
    with p.open("a") as dbfile:
        dbfile.write(f"\n{e}")
    entries.append(e)
    end:int = time.time_ns()
    times.append(end-start)
    s:int = 0
    for t in times:
        s+=t
    print(f"avg (ns): {s/len(times)}")
    return flask.redirect("/")
@app.route("/remove", methods=["POST"])
def remove():
    #print(flask.request.form)
    id: int = int(flask.request.form["id"])
    #print(id)
    for e in entries:
        if e.id == id:
            entries.remove(e)
            break
    with p.open("r") as fr:
        lines = fr.readlines()
    with p.open("w") as dbfile:
        for line in lines:
            #print(line)
            parsed = parsedb(line)
            if parsed and parsed.id != id:
                dbfile.write(line)
    return flask.redirect("/")
@app.route("/a4", methods=["GET"])
def a4():
    context = {
            "entries":entries
        }
    return flask.render_template("a4.html",  **context)
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
