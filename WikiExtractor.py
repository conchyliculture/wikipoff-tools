#!/usr/bin/python
import sys
#sys.path.append("./lib")
#sys.path.append("./lib/python{0:d}.{1:d}/site-packages/".format(sys.version_info.major,  sys.version_info.minor))
import base64
import getopt
from io import StringIO
import os.path
import pylzma
#import sqlite3
import struct
from time import sleep
#from threading import Thread
#from wikimedia import XMLworker

import zmq
from multiprocessing import Process

from lib.writer.sqlite import OutputSqlite 
from lib.wikimedia.XMLworker import XMLworker
from lib.wikimedia import wikitools


# TODO argparse

class Main(object):

    def __init__(self, input_file, output_file):

        self.halt = False

        self.articles_parsed = 0

        self.output = OutputSqlite(output_file)
        self.xml_extractor = XMLworker(input_file)

        self.context = zmq.Context()


	self.result_manager = Process(target=self.ResultManagerTask, args=())
        sleep(1)

        self.worker_processes = []
	for wrk_num in range(8):
	    self.worker_processes.append(Process(target=self.WorkerTask, args=(wrk_num,)))
        sleep(1)

	self.ventilator = Process(target=self.ExtractArticlesTask, args=())
        sleep(1)

    def ExtractArticlesTask(self):
        # Set up a channel to send work
        ventilator_send = self.context.socket(zmq.PUSH)
        ventilator_send.bind("tcp://127.0.0.1:5557")

        # Give everything a second to spin up and connect
        sleep(1)

        self.xml_extractor.run(ventilator_send)
        print("ExtractArticlesTask finished")

    def ResultManagerTask(self):
        # Set up a channel to receive results
        results_receiver = self.context.socket(zmq.PULL)
        results_receiver.bind("tcp://127.0.0.1:5558")
    
        # Set up a channel to send control commands
        control_sender = self.context.socket(zmq.PUB)
        control_sender.bind("tcp://127.0.0.1:5559")

        while(True):
            message_json = results_receiver.recv_json()
            title = message_json[u'title']
            body = message_json[u'body']
            if message_json[u'type'] == 1:
                self.output.AddRedirect(title, body)
            elif message_json[u'type'] == 3:
                self.output.AddArticle(title, base64.b64decode(body))
            elif message_json[u'type'] == 0:
                break
            else:
                raise Exception('wrong type : %d'%message_json[u'type'])

        print(u'Setting Metadata')
        self.output.set_metadata(self.xml_extractor.get_infos())
        print(u'Building Indexes')
        self.output.Close()
        control_sender.send_string(u'finished')
        self.halt = True
        print(u'Result Manager has finished')

    def WorkerTask(self, wrk_num):
        work_receiver = self.context.socket(zmq.PULL)
        work_receiver.connect("tcp://127.0.0.1:5557")

        control_receiver = self.context.socket(zmq.SUB)
        control_receiver.connect("tcp://127.0.0.1:5559")
        control_receiver.setsockopt_string(zmq.SUBSCRIBE, u'')
    
        # Set up a channel to send result of work to the results reporter
        results_sender = self.context.socket(zmq.PUSH)
        results_sender.connect("tcp://127.0.0.1:5558")
    
        # Set up a poller to multiplex the work receiver and control receiver channels
        poller = zmq.Poller()
        poller.register(work_receiver, zmq.POLLIN)
        poller.register(control_receiver, zmq.POLLIN)

        # Loop and accept messages from both channels, acting accordingly
        while not self.halt:
            socks = dict(poller.poll())
            if socks.get(work_receiver) == zmq.POLLIN:
                message_json = work_receiver.recv_json()
                if message_json[u'type'] == 2:
                    title, body = wikitools.WikiConvertToHTML(
                            message_json[u'title'], message_json[u'body'], self.xml_extractor.GetTranslator())
                    c = pylzma.compressfile(StringIO(body),dictionary=23)
                    result = c.read(5)
                    result+=struct.pack('<Q', len(body))
                    body = result+c.read()
                    message_json[u'type'] = 3
                    message_json[u'body'] = base64.b64encode(body)
                        
                results_sender.send_json(message_json)
            elif socks.get(control_receiver) == zmq.POLLIN:
                ctrl_message = control_receiver.recv()
                if ctrl_message == u'finished':
                    break
        print(u'Worker-%d has finishaide'%wrk_num)

    def run(self):
	for worker in self.worker_processes:
            worker.start()

	self.result_manager.start()

	self.ventilator.start()

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
