#!/usr/bin/python3

import os
import subprocess
import sys

FILENAME = "Blubberfile"
LINEFEED = "\n"
SOURCE_MAGIC = ". ./poky/oe-init-build-env &> /dev/null"
SHELL = "/bin/bash"
LAYERFILE = "build/conf/bblayers.conf"
CONFFILE = "build/conf/local.conf"

SECTIONSTART_LAYERS = "[layers]"
SECTIONSTART_LOCAL = "[local]"
SECTIONSTART_BLUBBER = "[blubber]"

class Config:
	def __init__(self):
		self.layers = []
		self.local = []
		self.blubber = {}

class Fragment:
	def __init__(self, s):
		self.first = -1
		self.last = -1
		self.keyword = ""
		self.assignment = ""
		self.content = ""
		self.longcontent =  False
		x = s.find("\"")
		if not x == -1:
			self.longcontent = True
			y = s.rfind("\"")
			self.content = s[x + 1:y]
			s = s[:x]
		bi = s.split(" ")
		self.keyword = bi[0]
		self.assignment = bi[1]
		if not self.longcontent:
			self.content = bi[2]
	def __repr__(self):
		return "fragment: keyword = '" + self.keyword + "', assignment '" + self.assignment + "', content '" + self.content + "', in lines " + str(self.first) + "-" + str(self.last)
	def __unicode__(self):
		return unicode(self.__repr__())
	def tofile(self):
		icontent = ""
		try:
			icontent = "\"" + os.environ[self.keyword] + "\""
		except KeyError:
			if self.longcontent:
				icontent = "\"" + self.content + "\""
			else:
				icontent = self.content
		return self.keyword + " " + self.assignment + " " + icontent

def exit_fail(message):
	print("aborting: " + message)
	quit(1)

def get_config(fname):
	if not os.path.isfile(fname):
		exit_fail("could not open Blubberfile")
	with open(fname) as f:
		content = f.readlines()
	conf = Config()
	trig = 0
	for l in content:
		i = l.strip()
		if i == SECTIONSTART_LAYERS:
			trig = 1
		elif i.startswith("[") and i.endswith("]"):
			trig = 0
		elif trig:
			conf.layers.append(i)
	trig = 0
	b = ""
	first = -1
	for l in content:
		i = l.strip()
		if i == SECTIONSTART_LOCAL:
			trig = 1
		elif i.startswith("[") and i.endswith("]"):
			trig = 0
		elif trig:
			if not i == "" and not i.startswith("#"):
				if first == -1:
					first = content.index(l)
				b += i
				if b.endswith("\\"):
					b = b[:-1]
				else:
					b.strip()
					ass = Fragment(b)
					ass.first = first
					ass.last = content.index(l)
					conf.local.append(ass)
					b = ""
					first = -1
	trig = 0
	for l in content:
		i = l.strip()
		if i == SECTIONSTART_BLUBBER:
			trig = 1
		elif i.startswith("[") and i.endswith("]"):
			trig = 0
		elif trig:
			b_in = l.split("=");
			if len(b_in) == 2:
				conf.blubber[b_in[0].strip(" \"\r\n")] = b_in[1].strip(" \"\r\n")
	return conf

def to_blubberfile(obj):
	if os.path.isfile(FILENAME):
		os.remove(FILENAME)
	f = open(FILENAME, "w")
	f.write(SECTIONSTART_LAYERS + LINEFEED)
	if not obj is None and hasattr(obj, "layers"):
		pass
	f.write(SECTIONSTART_LOCAL + LINEFEED)
	if not obj is None and hasattr(obj, "local"):
		pass
	f.close()

def print_help():
	print("Usage:")
	print("  help      Shows this help message")
	print("  create    Creates a minimal Blubberfile")
	print("  setup     Sets up the layers and build directory according to the Blubberfile")
	print("  shell     Gives you a shell initialized for the project")
	print("  run       Forwards everything after the command to a shell initialized for the project")
	quit(0)

def get_layers(obj):
	if obj is None or not hasattr(obj, "layers"):
		return;
	for l in obj.layers:
		b = l.split(";")
		if len(b) < 3:
			break
		elif b[0] == "git":
			cmd = "git clone " + b[2] + " " + b[1]
			subprocess.call(cmd, shell=True)
			if len(b) > 3:
				cmd = "cd " + b[1] + "; git checkout -b blubber_" + b[3] + " " + b[3]
				print("want to do: " + cmd)
				subprocess.call(cmd, shell=True)

def setup_bblayers(obj):
	bbfile = LAYERFILE
	if not os.path.isfile(bbfile) or obj == None or not hasattr(obj, "layers"):
		return
	with open(bbfile) as f:
		bb = f.readlines()
	found = -1
	for l in bb:
		i = l.strip()
		if i.startswith("BBLAYERS "):
			found = bb.index(l)
			break
	if found < 0:
		return
	p = os.getcwd()
	for i in obj.layers:
		a = i.split(";")
		if not a[1] == "poky":
			bb.insert(found + 1, "  " + p + "/" + a[1] + " \\" + LINEFEED);
	f = open(bbfile, "w")
	for i in bb:
		f.write(i)
	f.close()

def setup_local(obj):
	localfile = CONFFILE
	if not os.path.isfile(localfile) or obj == None or not hasattr(obj, "local"):
		return
	with open(localfile) as f:
		lc = f.readlines()
	lcf = []
	for i in lc:
		lcf.append(i.strip())
	b = ""
	first = -1
	fragments = []
	for l in lcf:
		if not l == "" and not l.startswith("#"):
			if first == -1:
				first = lcf.index(l)
			b += l
			if b.endswith("\\"):
				b = b[:-1]
			else:
				b.strip()
				ass = Fragment(b)
				ass.first = first
				ass.last = lcf.index(l)
				fragments.append(ass)
				b = ""
				first = -1
	for i in obj.local:
		trig = False
		for j in fragments:
			if i.keyword == j.keyword:
				trig = True
				del lcf[j.first:j.last + 1]
				lcf.insert(j.first, i.tofile())
				if not j.first == j.last:
					for i in range(j.first, j.last):
						lcf.insert(j.first + 1, "")
				break
		if not trig:
			lcf.append(i.tofile())
	f = open(localfile, "w")
	for i in lcf:
		f.write(i + LINEFEED)
	f.close()

if len(sys.argv) <= 1:
	print_help()
if sys.argv[1] == "help":
	print_help()
elif sys.argv[1] == "create":
	to_blubberfile(None)
elif sys.argv[1] == "setup":
	c = get_config(FILENAME)
	get_layers(c)
	subprocess.call(SOURCE_MAGIC, shell=True, executable=SHELL)
	setup_bblayers(c)
	setup_local(c)
elif sys.argv[1] == "shell":
	cmd = SOURCE_MAGIC + "; " + SHELL
	subprocess.call(cmd, shell=True, executable=SHELL)
elif sys.argv[1] == "run":
	a = sys.argv[2:]
	cmd = SOURCE_MAGIC + "; "
	for i in a:
		cmd += i.strip() + " "
	subprocess.call(cmd, shell=True, executable=SHELL)
