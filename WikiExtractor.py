#!/usr/bin/python
import sys
#sys.path.append("./lib")
sys.path.append("./lib/python{0:d}.{1:d}/site-packages/".format(sys.version_info.major,  sys.version_info.minor))
import base64
import getopt
from io import StringIO
import os.path
import pylzma
import struct

from multiprocessing import Process
from multiprocessing import cpu_count
from multiprocessing import Queue

from lib.writer.sqlite import OutputSqlite
from lib.wikimedia.XMLworker import XMLworker
from lib.wikimedia.converter import WikiConverter
from lib.wikimedia import wikitools


# TODO Use argparse instead

class Main(object):

    FINIESHED_MSG = u'finished'

    def __init__(self, input_file, output_file):

        self.output = OutputSqlite(output_file)
        self.xml_extractor = XMLworker(input_file)
        self.wikiconverter = WikiConverter(wikitype=u'wikipedia', wikilang=u'fr')

        self.extraction_queue = Queue()
        self.writing_queue = Queue()

        nb_workers = cpu_count()

	self.result_manager = Process(target=self.ResultManagerTask, args=(self.writing_queue, self.extraction_queue, nb_workers))
	self.ventilator = Process(target=self.ExtractArticlesTask, args=(self.extraction_queue,))
        self.worker_processes = []
	for wrk_num in range(nb_workers):
	    self.worker_processes.append(Process(target=self.WorkerTask, args=(wrk_num, self.extraction_queue, self.writing_queue)))

    def ExtractArticlesTask(self, out_queue):
        self.xml_extractor.run(out_queue)
        print("ExtractArticlesTask finished")

    def ResultManagerTask(self, in_queue, ctrl_queue, nb_workers):
        counter = 0
        expected_nb_msg = -1

        while(True):
            message_json = in_queue.get()
            title = message_json[u'title']
            body = message_json[u'body']
            if message_json[u'type'] == 1:
                self.output.AddRedirect(title, body)
            elif message_json[u'type'] == 3:
                self.output.AddArticle(title, base64.b64decode(body))
            elif message_json[u'type'] == 0:
                expected_nb_msg = message_json[u'title']
            else:
                raise Exception('wrong type : %d'%message_json[u'type'])
            counter += 1
            if expected_nb_msg == counter:
                break

        print(u'Setting Metadata')
        self.output.SetMetadata(self.xml_extractor.db_metadata)
        print(u'Building Indexes')
        self.output.Close()
        for i in range(nb_workers):
            ctrl_queue.put(u'finished')
        print(u'Result Manager has finished')

    def WorkerTask(self, wrk_num, in_queue, out_queue):
        while True:
            message_json = in_queue.get()
            if message_json == u'finished':
                break
            if message_json[u'type'] == 2:
                title, body = self.wikiconverter.Convert(
                        message_json[u'title'], message_json[u'body'])
                c = pylzma.compressfile(StringIO(body), dictionary=23)
                result = c.read(5)
                result+=struct.pack('<Q', len(body))
                body = result+c.read()
                message_json[u'type'] = 3
                message_json[u'body'] = base64.b64encode(body)

            out_queue.put(message_json)

    def run(self):
        self.running = True

	for worker in self.worker_processes:
            worker.start()

	self.ventilator.start()
	self.result_manager.start()

        self.result_manager.join()
        self.running = False

def show_usage():
    print("""Usage: python WikiExtractor.py  [options] -x wikipedia.xml
Converts a wikipedia XML dump file into sqlite databases to be used in WikipOff

Options:
        -x, --xml       Input xml dump
        -d, --db        Output database file (default : 'wiki.sqlite')
/bin/bash: q : commande introuvable
        -t, --type      Wikimedia type (default: 'wikipedia')
""")


def main():

    script_name = os.path.basename(sys.argv[0])

    try:
        long_opts = ['help', "db=", "xml=",'type=']
        opts, args = getopt.gnu_getopt(sys.argv[1:], 'hx:d:t:', long_opts)
    except getopt.GetoptError:
        show_usage()
        sys.exit(1)

    output_file=""

    for opt, arg in opts:
        if opt in ('-h', '--help'):
            show_usage()
            sys.exit()
        elif opt in ('-d', '--db'):
            output_file = arg
        elif opt in ('-x','--xml'):
            input_file = arg

    if not 'input_file' in locals():
        print("Please give me a wiki xml dump with -x or --xml")
        sys.exit()

    if output_file is None or output_file=="":
        print("I need a filename for the destination sqlite file")
        sys.exit(1)

    if os.path.isfile(output_file):
        print("%s already exists. Won't overwrite it."%output_file)
        sys.exit(1)


    m = Main(input_file, output_file)
    m.run()

    print("Converting xml dump %s to database %s. This may take eons..."%(input_file,output_file))

if __name__ == '__main__':
    main()
