#!/usr/bin/python
import argparse
import base64
import itertools
import os.path
import sys
from time import sleep

from multiprocessing import Process
from multiprocessing import cpu_count
from multiprocessing import Queue
from multiprocessing import Value

from lib.writer.compress import LzmaCompress
from lib.writer.sqlite import OutputSqlite
from lib.wikimedia.XMLworker import XMLworker
from lib.wikimedia.converter import WikiConverter


class WikiDoStuff(object):

    def __init__(self, input_file, output_file):

        self.output = OutputSqlite(output_file)
        self.xml_extractor = XMLworker(input_file)
        self.wikiconverter = WikiConverter(wikitype=u'wikipedia', wikilang=u'fr')

        self.extraction_status = Value('f', 0.0)

        self.extraction_queue = Queue(maxsize=1000)
        self.writing_queue = Queue()

        nb_workers = cpu_count()

        self.result_manager = Process(
            name='ResultsManager',
            target=self.ResultManagerTask,
            args=(self.writing_queue, self.extraction_queue, nb_workers, self.extraction_status))
        self.ventilator = Process(
            name='ventilator',
            target=self.ExtractArticlesTask, args=(self.extraction_queue, self.extraction_status))
        self.worker_processes = []
        for i in range(nb_workers):
            self.worker_processes.append(
                Process(
                    name='Worker-%d'%i,
                    target=self.WorkerTask,
                    args=(self.extraction_queue, self.writing_queue)))

    def ExtractArticlesTask(self, out_queue, status):
        self.xml_extractor.run(out_queue, status)
        return

    def ResultManagerTask(self, in_queue, ctrl_queue, nb_workers, status):
        counter = 0
        expected_nb_msg = -1

        spinner_chars = itertools.cycle("\|/-")
        while True:
            if (counter%50) == 0:
                extraction_status = u'%.02f%%'%status.value
                if status.value > 99.89:
                    extraction_status = u'Complete'
                msg_str = u'\rExtraction: {0:s} | Compressing {1:s} | Results Queue Size: {2:d}\r'.format(
                        extraction_status, next(spinner_chars), ctrl_queue.qsize())
                sys.stdout.write(msg_str)
                sys.stdout.flush()
            message_json = in_queue.get()
            title = message_json[u'title']
            body = message_json[u'body']
            if message_json[u'type'] == 1:
                self.output.AddRedirect(title, body)
                counter += 1
            elif message_json[u'type'] == 3:
                self.output.AddArticle(title, base64.b64decode(body))
                counter += 1
            elif message_json[u'type'] == 0:
                expected_nb_msg = message_json[u'title']
            else:
                raise Exception('wrong type : %d'%message_json[u'type'])
            if expected_nb_msg == counter:
                break

        print(u'Setting Metadata')
        self.output.SetMetadata(self.xml_extractor.db_metadata)
        print(u'Building Indexes')
        self.output.Close()
        for _ in range(nb_workers):
            ctrl_queue.put(u'finished')
        print(u'Result Manager has finished')
        sleep(1)
        return

    def WorkerTask(self, in_queue, out_queue):
        while True:
            message_json = in_queue.get()
            if message_json == u'finished':
                break
            if message_json[u'type'] == 2:
                _, body = self.wikiconverter.Convert(
                    message_json[u'title'], message_json[u'body'])
                compressed_body = LzmaCompress(body)
                message_json[u'type'] = 3
                message_json[u'body'] = base64.b64encode(compressed_body)
            out_queue.put(message_json)
        return

    def _AbortAbort(self):
        for worker in self.worker_processes:
            worker.terminate()

        self.ventilator.terminate()
        self.result_manager.terminate()
        print("Termination complete")

    def run(self):
        try:
            for worker in self.worker_processes:
                worker.start()

            self.ventilator.start()
            self.result_manager.start()
            self.result_manager.join()
        except KeyboardInterrupt as e:
            self._AbortAbort()
            raise e


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(u'xml_file', help=u'the input xml wikimedia dump')
    parser.add_argument(u'output_file', help=u'the destination file')

    args = parser.parse_args()

    if not os.path.exists(args.xml_file):
        print(u'{0:s} doesn\'t exist.'.format(args.xml_file))
        sys.exit(1)

    if os.path.exists(args.output_file):
        print(u'{0:s} already exists. Won\'t overwrite it.'.format(args.output_file))
        sys.exit(1)

    wikiextractor = WikiDoStuff(args.xml_file, args.output_file)
    print(u'Converting xml dump {0:s} to database {1:s}. This may take eons...'.format(
        args.xml_file, args.output_file))
    wikiextractor.run()

if __name__ == '__main__':
    main()
