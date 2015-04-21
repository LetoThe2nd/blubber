#!/usr/bin/python3

import os
import platform
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

# taken from http://stackoverflow.com/a/3041990
# modification: raw_input() was renamed to input() in python3
#begin
def query_yes_no(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is one of "yes" or "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")
#end

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

class Blubber_Platform:
	def __init__(self):
		self.System = platform.system()
		self.Linux = None
		if not self.System == "Linux":
			print("We're not running on a linux platform.")
			print("  All commands that would be executed in the poky environment will be disabled.")
			print("  Other things might also be broken or malfunctioning in funny ways.")
		else:
			self.Linux = platform.linux_distribution()
	def is_Linux(self):
		return (self.System == "Linux")
	def validate(self):
		print("Trying to run git...")
		result = subprocess.call("git --version", shell=True)
		if result == 0:
			print("...looks good!")
		else:
			print("...this didn't work, please make sure 'git' is installed!")
		if not self.is_Linux():
			return
		print("This seems to be a Linux platform, maybe we can do a little bit more.")
		if (self.Linux[0] == 'Ubuntu') or (self.Linux[0] == "debian"):
			print("Found " + self.Linux[0] + "!")
			print("Checking for needed packages...")
			UBUNTU_PACKAGES = ["gawk", "wget", "git-core", "diffstat", "unzip", "texinfo", "gcc-multilib", "build-essential", "chrpath", "libsdl1.2-dev", "xterm"]
			missing = ""
			for package in UBUNTU_PACKAGES:
				miss = subprocess.call("2>/dev/null 1>/dev/null dpkg -s " + package, shell=True)
				if not miss == 0:
					missing += package + " "
			if not missing == "":
				print("Seems you are missing some packages: " + missing)
				if query_yes_no("Shall we try to install whats missing?"):
					subprocess.call("sudo apt-get install " + missing, shell=True)
			else:
				print("Everything we need is installed, great!")
		elif self.Linux[0] == "Fedora":
			print("Found " + self.Linux[0] + " but not fully supported yet, sorry!")
		elif self.Linux[0] == "openSUSE":
			print("Found " + self.Linux[0] + " but not fully supported yet, sorry!")
		elif self.Linux[0] == "CentOS":
			print("Found " + self.Linux[0] + " but not fully supported yet, sorry!")
		elif self.Linux[0] == "arch":
			print("Found " + self.Linux[0] + " but not fully supported yet, sorry!")
		elif self.Linux[0] == "Gentoo Base System":
			print("Found " + self.Linux[0] + " but not fully supported yet, sorry!")
		else:
			#other distributions to follow....
			pass

LOCAL_PLATFORM = Blubber_Platform()

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
	else:
		f.write("git;poky;git://git.yoctoproject.org/poky.git")
		f.write(LINEFEED)
	f.write(SECTIONSTART_LOCAL + LINEFEED)
	if not obj is None and hasattr(obj, "local"):
		pass
	f.write(SECTIONSTART_BLUBBER + LINEFEED)
	if not obj is None and hasattr(obj, "blubber"):
		pass
	f.close()

def print_help():
	print("Usage:")
	print("  blubber.py [options] command [parameters]")
	print("  Supported options:")
	print("    -f filename    Use 'filename' as configuration instead of")
	print("                     default 'Blubberfile'")
	print("  Supported commands:")
	print("    build          bitbakes the default target if DEFAULT_BUILD is set in the")
	print("                     [blubber] section of the Blubberfile")
	print("    help           Shows this help message")
	print("    create         Creates a minimal Blubberfile")
	print("    setup          Sets up the layers and build directory according to the Blubberfile")
	print("    shell          Gives you a shell initialized for the project")
	print("    run            Forwards all parameters after the command to a")
	print("                     shell initialized for the project")
	print("    validate       Tries to test and fix the build platform for required tools and packages")
	print("                     as far as possible.")
	quit(0)

def get_layers(obj):
	if obj is None or not hasattr(obj, "layers"):
		return;
	for l in obj.layers:
		b = l.split(";")
		if len(b) < 3:
			break
		elif b[0] == "git" or b[0] == "git-master":
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
		if a[0] == "subrepo":
			bb.insert(found + 1, "  " + p + "/" + a[2] + "/" + a[1] + " \\" + LINEFEED);
		elif not a[1] == "poky" and not a[0].endswith("-master"):
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

def execute_poky_command(cmd):
	if LOCAL_PLATFORM.is_Linux():
		cmd_intern = SOURCE_MAGIC + "; " + cmd
		subprocess.call(cmd_intern, shell=True, executable=SHELL)

# Here is the actual main part!

if len(sys.argv) <= 1:
	print_help()
	exit(0)
cmd_index = 1
while (len(sys.argv) > cmd_index) and (sys.argv[cmd_index].startswith("-")):
	if sys.argv[cmd_index] == "-f":
		if len(sys.argv) > cmd_index + 1:
			FILENAME = sys.argv[cmd_index + 1]
			print("using Blubberfile '" + FILENAME + "'")
			cmd_index = cmd_index + 2
		else:
			print("option -f needs additional Blubberfile path to be passed")
			cmd_index = cmd_index + 1
	else:
		print("option " + sys.argv[cmd_index] + " could not be recognized, skipping")
		cmd_index = cmd_index + 1

if (len(sys.argv) <= cmd_index) or (sys.argv[cmd_index] == "help"):
	print_help()
elif sys.argv[cmd_index] == "validate":
	LOCAL_PLATFORM.validate()
elif sys.argv[cmd_index] == "create":
	to_blubberfile(None)
elif sys.argv[cmd_index] == "setup":
	c = get_config(FILENAME)
	get_layers(c)
	execute_poky_command("")
	setup_bblayers(c)
	setup_local(c)
elif sys.argv[cmd_index] == "shell":
	execute_poky_command(SHELL)
elif sys.argv[cmd_index] == "run":
	a = sys.argv[cmd_index + 1:]
	cmd = ""
	for i in a:
		cmd += i.strip() + " "
	execute_poky_command(cmd)
elif sys.argv[cmd_index] == "build":
	c = get_config(FILENAME)
	if "BUILD_DEFAULT" in c.blubber:
		print("will build default target " + c.blubber["BUILD_DEFAULT"])
		execute_poky_command("bitbake " + c.blubber["BUILD_DEFAULT"])
	else:
		print("no DEFAULT_BUILD set, aborting.")
else:
	print("could not recognize commmand '" + sys.argv[cmd_index] + "'")
	print_help()
