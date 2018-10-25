import time
import urllib, json
import ctypes
import os
import platform
import sys



def get_noun_list(path):
        f = open(path,'r')
        noun_list = []
        while True:
                x = f.readline()
                x = x.rstrip()
                if not x: break
                if len(x)> 2:
                        noun_list.append(x)
        return noun_list


def get_europeanna_data(search_term, api_key):
        #url='https://www.europeana.eu/api/v2/search.json?wskey=bPuG7ryC8&query=entity&qf=IMAGE_SIZE%3Aextra_large&reusability=open&qf=TYPE%3AIMAGE&start=1&rows=100&profile=rich&cursor=*'
        url = 'http://www.europeana.eu/api/v2/search.json?wskey='+api_key+'&query='+search_term+'&qf=IMAGE_SIZE%3Aextra_large&reusability=open&qf=TYPE%3AIMAGE&start=1&rows=100&profile=rich&cursor=*'
        print url
        response = urllib.urlopen(url)
        data = json.loads(response.read())
        return data

def get_free_space_mb(dirname):
        st = os.statvfs(dirname)
        return st.f_bavail * st.f_frsize / 1024 / 1024

def get_file_size(path):
        return os.path.getsize(path) / 1000.0 / 1000.0

def poll_until_free_space(dirname, free_space_threshold_mb):
        while 1:
                if get_free_space_mb(dirname) < free_space_threshold_mb:
                        print "waiting for free space. current space is: ",get_free_space_mb(dirname)
                        time.sleep(1)
                else:
                        break
def get_api_key(path):
        f = open(path,'r')
        contents = f.read()
        if(len(contents)>0):
                return contents.strip()
        else:
                return False

def transfer_until_full(data, dirname, free_space_threshold_mb):
        for item in data["items"]:
                id = item["id"]
                id = id.replace("/", "_");
                image_path="../images/"+id+".jpg"
                meta_data_path="../meta_data/"+id+".json"
                print "saving to ",image_path
                try:
                        urllib.urlretrieve(item["edmIsShownBy"][0], image_path)
                        with open(meta_data_path, "w") as write_file:
                                json.dump(item, write_file)
                        if get_free_space_mb(dirname) > free_space_threshold_mb:
                                print "space remaining ",get_free_space_mb(dirname)
                        else:
                                poll_until_free_space(dirname, free_space_threshold_mb)
                except IOError:
                        print "download error"

print "getting noun list"
path = "../noun_list/noun_list.txt"
api_path = "../keys/api_key.txt"
noun_list = get_noun_list(path)
api_key = get_api_key(api_path)


print "starting scrape"
index = 0
for noun in noun_list:
        print "___________________________getting data for",noun,"___________________________"
        try:
                data = get_europeanna_data(noun, api_key)
                transfer_until_full(data, "./", 5240)
                f = open(path,'wb')
                for i in range(index, len(noun_list)-1):
                        f.write(noun_list[i]+"\n")
                f.close()
                print "updated noun list"
                index+=1
        except IOError:
                print "ioerro",IOError

        #update list to remove already used words

