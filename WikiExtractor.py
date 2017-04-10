#!/usr/bin/python
import sys
#sys.path.append("./lib")
sys.path.append(u'./lib/python{0:d}.{1:d}/site-packages/'.format(
    sys.version_info.major, sys.version_info.minor))
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


# TODO Use argparse instead

class WikiExtractor(object):

    def __init__(self, input_file, output_file):

        self.output = OutputSqlite(output_file)
        self.xml_extractor = XMLworker(input_file)
        self.wikiconverter = WikiConverter(wikitype=u'wikipedia', wikilang=u'fr')

        self.extraction_queue = Queue()
        self.writing_queue = Queue()

        nb_workers = cpu_count()

        self.result_manager = Process(
            target=self.ResultManagerTask,
            args=(self.writing_queue, self.extraction_queue, nb_workers))
        self.ventilator = Process(target=self.ExtractArticlesTask, args=(self.extraction_queue,))
        self.worker_processes = []
        for _ in range(nb_workers):
            self.worker_processes.append(
                Process(
                    target=self.WorkerTask,
                    args=(self.extraction_queue, self.writing_queue)))

    def ExtractArticlesTask(self, out_queue):
        self.xml_extractor.run(out_queue)
        print("ExtractArticlesTask finished")

    def ResultManagerTask(self, in_queue, ctrl_queue, nb_workers):
        counter = 0
        expected_nb_msg = -1

        while True:
            if (counter%100) == 0:
                msg_str = u'\rCompressing{0:s}\r'.format(u'.'*(counter/100))
                sys.stdout.write(msg_str)
                sys.stdout.flush()
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
        for _ in range(nb_workers):
            ctrl_queue.put(u'finished')
        print(u'Result Manager has finished')

    def WorkerTask(self, in_queue, out_queue):
        while True:
            message_json = in_queue.get()
            if message_json == u'finished':
                break
            if message_json[u'type'] == 2:
                _, body = self.wikiconverter.Convert(
                    message_json[u'title'], message_json[u'body'])
                compressed_article = pylzma.compressfile(StringIO(body), dictionary=23)
                result = compressed_article.read(5)
                result += struct.pack(u'<Q', len(body))
                body = result + compressed_article.read()
                message_json[u'type'] = 3
                message_json[u'body'] = base64.b64encode(body)

            out_queue.put(message_json)

    def run(self):
        for worker in self.worker_processes:
            worker.start()

        self.ventilator.start()
        self.result_manager.start()

        self.result_manager.join()

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
    try:
        long_opts = [u'help', u'db=', u'xml=', u'type=']
        opts, _ = getopt.gnu_getopt(sys.argv[1:], 'hx:d:t:', long_opts)
    except getopt.GetoptError:
        show_usage()
        sys.exit(1)

    output_file = None

    for opt, arg in opts:
        if opt in (u'-h', u'--help'):
            show_usage()
            sys.exit()
        elif opt in (u'-d', u'--db'):
            output_file = arg
        elif opt in (u'-x', u'--xml'):
            input_file = arg

    if not u'input_file' in locals():
        print(u'Please give me a wiki xml dump with -x or --xml')
        sys.exit()

    if not output_file:
        print(u'I need a filename for the destination sqlite file')
        sys.exit(1)

    if os.path.isfile(output_file):
        print(u'%s already exists. Won\'t overwrite it.'%output_file)
        sys.exit(1)

    wikiextractor = WikiExtractor(input_file, output_file)
    print(u'Converting xml dump {0:s} to database {1:s}. This may take eons...'.format(
        input_file, output_file))
    wikiextractor.run()


if __name__ == '__main__':
    main()
