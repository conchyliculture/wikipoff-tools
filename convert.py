#!/usr/bin/python

import sys
import os
import readline
import lxml
import getopt

def download_file(url,dest=None):
    import urllib2
    # stolen from https://stackoverflow.com/questions/22676/how-do-i-download-a-file-over-http-using-python
    if dest:
        file_name=dest
    else:
        file_name = url.split('/')[-1]
    do_dl = True
    if os.path.isfile(file_name):
        resri = raw_input("%s already exists, overwrite? [y/N]"%file_name)
        if resri=="" or resri=="n" or resri=="N":
            do_dl = False

    if do_dl: 
        u = urllib2.urlopen(url)
        f = open(file_name, 'wb')
        meta = u.info()
        file_size = int(meta.getheaders("Content-Length")[0])
        print "Downloading: %s Bytes: %s" % (file_name, file_size)

        file_size_dl = 0
        block_sz = 8192
        while True:
            buffer = u.read(block_sz)
            if not buffer:
                break

            file_size_dl += len(buffer)
            f.write(buffer)
            status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
            status = status + chr(8)*(len(status)+1)
            print status,

        f.close()
    return file_name 

def prepare_env():
    eggdir=os.path.join(os.getcwd(),"lib","python2.7/site-packages/pylzma-0.4.4-py2.7-linux-x86_64.egg")
    print eggdir
    if not os.path.exists(eggdir):
        os.makedirs(eggdir)
    if not os.path.exists(os.path.join(eggdir,"pylzma.so")):
        if os.environ.has_key("PYTHONPATH"):
            os.environ['PYTHONPATH']=os.environ['PYTHONPATH']  +":"+os.path.join(eggdir,"..")
        else:
            os.environ['PYTHONPATH']=os.path.join(eggdir,"..")

        print("Downloading required libs")
        download_file("https://pypi.python.org/packages/source/p/pylzma/pylzma-0.4.4.tar.gz#md5=a2be89cb2288174ebb18bec68fa559fb","pylzma-0.4.4.tar.gz")
        os.system("tar xzf pylzma-0.4.4.tar.gz")
        curdir=os.getcwd()
        os.chdir("pylzma-0.4.4")
        download_file("http://pypi.python.org/packages/2.7/s/setuptools/setuptools-0.6c11-py2.7.egg")
        os.system("python setup.py install --prefix=\"%s/../\""%os.getcwd())
        os.chdir(curdir)
        os.system("rm -rf ./bin")
        print("done")
        print("you can rm -rf pylzma-0.4.4*") 
        



def ask_method():
    while True:
        print("")
        print("Please select where to get Wiki dump from: ")
        print("")
        print("[1] Provide URL to dump")
        print("[2] Provide a path to dump")
        print("")
        try: 
            method = int(raw_input('Please select: '))
            return method
        except ValueError:
            return 0

def ask_output(i):
    default,x,lost = i.rpartition(".xml")
    default=default+".sqlite"
    res = raw_input("Please select output sqlite db output name:\n[%s] "%default) or default
    return res

def ask_type(i):
    default="wikipedia.org"
    res = raw_input("Please choose wiki type (ex: 'elderscrolls.wikia'):\n[%s] "%default) or default
    return res



def download_url(url=None):
    if url is None:
        url = raw_input("Please enter the URL: ")

    file_name = download_file(url)

    return file_name

def pathCompleter(text,state):
    import glob
    """
    This is the tab completer for systems paths.
    Only tested on *nix systems
    """
    line = readline.get_line_buffer().split()
    
    return [x for x in glob.glob(text+'*')][state]

def select_path():

    readline.set_completer_delims('\t')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(pathCompleter)
    ans = raw_input("What file do you want? ")
    return ans

def show_usage():
    print "lol"

def main():
    try:
        long_opts = ['path=', "url=","output="]
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'p:u:o:', long_opts)
    except getopt.GetoptError:
        show_usage()
        sys.exit(1)

    method=0
    url=None
    o=None
    xml_path = None
    dump_file=None

    for opt, arg in opts:
        if opt in ('-p', '--path'):
            xml_path=arg
            method=2
        if opt in ('-u', '--url'):
            url=arg
            method=1
        if opt in ('-o', '--output'):
            o = arg

    prepare_env()

    if method==0:
        method = ask_method()

    while True:
        if method == 1:
            dump_file = os.path.join(os.getcwd(), download_url(url))
            method = 3
        elif method == 2:
            dump_file = xml_path or select_path()
            method = 3
        elif method == 3:
            break
        else:
            ask_method()

    output_sqlite = o or ask_output(dump_file) 
    if os.path.isfile(output_sqlite):
        resri = raw_input("%s already exists, overwrite ? [y/N]"%output_sqlite)
        if resri=="" or resri=="n" or resri=="N":
            print("Exiting.")
            sys.exit(0)
        else:
            os.remove(output_sqlite)


    if os.path.isfile(dump_file):
        ext = dump_file.split('.')[-1]
        ext = '.'.join(dump_file.split('.')[-2:])
        if ext=="xml.bz2":
            os.system("bunzip2 \"%s\""%dump_file)
            dump_file='.'.join(dump_file.split('.')[:-1])
        elif ext=="xml.gz":
            os.system("gunzip \"%s\""%dump_file)
            dump_file='.'.join(dump_file.split('.')[:-1])
        elif ext.endswith(".xml"):
            pass
        else:
            print("I only know about .xml, .xml.bz2 or .xml.gz files")
            sys.exit(1)
    else:
        print("Unable to find %s, exiting."%dump_file)
        sys.exit(1)

    if not os.path.isfile(dump_file):
        print("Can't find expected %s after decompressing, exiting"%dump_file)
        sys.exit(1)

    cmd="python WikiExtractor.py  -x \"%s\" -d \"%s\""%(dump_file,output_sqlite)
    print cmd
    os.system(cmd)

main()
