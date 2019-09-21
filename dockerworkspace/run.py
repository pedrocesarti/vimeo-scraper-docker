import urllib.request
from threading import Thread
import pymongo
from queue import Queue

import logging
import sys
logging.basicConfig(level=logging.INFO,format="")

# file_handler = logging.FileHandler('vimeo.log')
# file_handler.setFormatter(logging.Formatter(""))
# logging.getLogger().addHandler(file_handler)

myclient = pymongo.MongoClient("mongodb://db_0:27017/")
mydb = myclient["vimeo"]
mycol = mydb["videos"]

jobs = Queue()

base_url = "https://player.vimeo.com/video/"

def th(q):
    while not q.empty():
        try: 
            vid = q.get()
            htmltext = urllib.request.urlopen("{}{}".format(base_url, vid)).read().decode('utf-8')
            title = str(htmltext).split('<title>')[1].split('</title>')[0]
            
            if title == "Private Video on Vimeo":
                q.task_done()
                continue

            data = { 
                "_id": vid, 
                "title": title, 
                "url": "{}{}".format(base_url, vid)}

            key = {"_id": vid}
            print(key)
            print(q.qsize())
            mycol.update(key, data, upsert=True)
            q.task_done()
        except urllib.error.HTTPError as err:
            if err.code == 404:
                logging.info("404 - Não Encontrado!")
                continue
            if err.code == 403:
                logging.info("403 - Não Autorizado!")
                continue
            else:
                raise

def get_max_id():
    maxrecord = mycol.find_one(sort=[("_id", -1)])
    if maxrecord is None:
        logging.info("Initiate DB")
        data = {
            "_id": 0,
            "title": "First"}

        mycol.update({"_id": 0}, data, upsert=True)
        maxrecord = mycol.find_one(sort=[("uid", -1)])
       
    logging.info("MAX ID: {} - ARGV: {}".format(int(maxrecord["_id"]), int(sys.argv[1])))
    if int(maxrecord["_id"]) > int(sys.argv[1]):
        return int(maxrecord["_id"])
    else:
        return int(sys.argv[1])


for i in range(get_max_id(), int(sys.argv[2])):
    jobs.put(f'{i:09}')

for i in range(100):
    t = Thread(target=th,args=(jobs,))
    t.setDaemon(True)
    t.start()

jobs.join()