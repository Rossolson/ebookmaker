import os
import shutil
import re
from datetime import datetime
from flask import Flask, request, render_template_string

app = Flask(__name__)

myname = "index.php"
mybaseurl = "https://ebookmaker2.pglaf.org"
prog = "export LC_ALL=C.UTF-8; export LANG=C.UTF-8; cd /opt/ebookmaker; /var/www/.local/bin/pipenv run ebookmaker"
pbase = "ebookmaker"  # do not show users the whole prog line.
tmpdir = "/htdocs/ebookmaker/cache"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'make' in request.form:
            if 'upfile1' not in request.files or request.files['upfile1'].filename == '':
                return "<p>no file</p>\n\n"

            upfile1 = request.files['upfile1']
            upfile1_name = fix_filename(upfile1.filename)
            tmpsubdir = datetime.now().strftime('%Y%m%d%H%M%S')
            dirname = os.path.join(tmpdir, tmpsubdir)
            newname = os.path.join(dirname, upfile1_name)
            os.makedirs(dirname)  # where our output will go
            upfile1.save(newname)  # save the uploaded file
            os.chmod(newname, 0o644)
            outfile = os.path.join(tmpdir, tmpsubdir, "output.txt")
            whichmatch = re.search(r"\.zip$", newname)

            if whichmatch:
                with open(outfile, 'a') as out:
                    out.write(f"unzipping {newname}\n")
                os.system(f"/usr/bin/unzip -l {newname} >> {outfile} 2>&1")
                os.system(f"USER=www-data;LOGNAME=www-data;HOME={newname}; /usr/bin/unzip -o -U {newname} -d {dirname}")

            gopts = ""
            basename = ""
            gotdir = 0

            if os.path.isdir(dirname):
                for file in os.listdir(dirname):
                    if file in ('.', '..'):
                        continue

                    if os.path.isdir(os.path.join(dirname, file)):
                        if gotdir != 0:
                            return "<p><font color=\"red\">More than one directory.</font></p>\n"
                        continue

                    if re.search(r"output.txt", file) or re.search(r"\.zip$", file):
                        continue

                    if re.search(r"\.txt$", file):
                        gotdir = 0
                        basename = os.path.basename(file)
                        gopts += "--make=epub --make=kindle --make=txt --make=html "
                        with open(outfile, 'a') as out:
                            out.write(f"Input file: {basename}\n")
                        break

            if gotdir != 0:
                dirname = os.path.join(dirname, gotdir)
                if not os.path.isdir(dirname):
                    return "<p><font color=\"red\">Sorry</p>\n"

            if basename == "":
                return "<p>Sorry</p>"

            basename = os.path.join(dirname, basename)
            gopts += "--max-depth=3 "
            gopts += f"--output-dir={os.path.join(tmpdir, tmpsubdir)} "

            if 'mytitle' in request.form and request.form['mytitle']:
                gopts += f"--title=\"{request.form['mytitle']}\" "

            command = f"{prog} {gopts} file://{basename}"
            os.system(f"{prog} --version >> {outfile}")
            retval = os.system(command + f" >> {outfile} 2>&1")

            if retval == 0:
                return "will stay available for a day or two:"
            else:
                return "<p>Sorry, ebookmaker ended with an error file.</p>\n"

        return render_template_string('''
            <html lang="en">
            <head><title>ebm</title></head>
            <body>
              <h1>ebm</h1>
              <blockquote>
                <form enctype="multipart/form-data" method="POST" accept-charset="UTF-8" action="index.php">
                  <input type="file" name="upfile1"> Your file (any of: zip/rst/txt/htm/html)
                  <br><input type="submit" value="Make it!" name="make">
                </form>
              </blockquote>
              <h2>Usage Details</h2>
              <p>Add</p>
              <p>Currently, supported operations</p>
            </body>
            </html>
        ''')

def fix_filename(filename):
    # Implement the filename fixing logic here
    return filename

if __name__ == '__main__':
    app.run()

