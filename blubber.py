#!/usr/bin/python3

import os
import platform
import subprocess
import sys

LINEFEED = "\n"
SHELL = "/bin/bash"

DEFAULT_BUILD_PATH = "build"

# some general helper functions
def get_layerfile_path(subconfig = None):
	LAYERFILE_TAIL = "/conf/bblayers.conf"
	head = DEFAULT_BUILD_PATH
	if subconfig:
		head = head + "-" + subconfig
	return head + LAYERFILE_TAIL

def get_conffile_path(subconfig = None):
	CONFFILE_TAIL = "/conf/local.conf"
	head = DEFAULT_BUILD_PATH
	if subconfig:
		head = head + "-" + subconfig
	return head + CONFFILE_TAIL

def get_source_magic(subconfig = None):
	path = DEFAULT_BUILD_PATH
	if subconfig:
		path = path + "-" + subconfig
	return ". ./poky/oe-init-build-env " + path + " &> /dev/null"

# The Blubber_Platform object is meant to deal with tasks that are
# related to the build host in use rather than the actual project.
# So far, it only supports checking for git, as weel as the needed
# packages on debianoid Linux distributions.
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

# some helper stuff for dealing with the Blubberfile syntax
SECTIONSTART_BEGIN = "["
SECTIONSTART_END = "]"

SECTION_LAYERS = "layers"
SECTION_LOCAL = "local"
SECTION_BLUBBER = "blubber"

SECTIONSTART_LAYERS = SECTIONSTART_BEGIN + SECTION_LAYERS + SECTIONSTART_END
SECTIONSTART_LOCAL = SECTIONSTART_BEGIN + SECTION_LOCAL + SECTIONSTART_END
SECTIONSTART_BLUBBER = SECTIONSTART_BEGIN + SECTION_BLUBBER + SECTIONSTART_END

MESSAGE_TRIGGER = "_MESSAGE"

def is_sectionstart(line):
	if line.startswith(SECTIONSTART_BEGIN) and line.endswith(SECTIONSTART_END):
		return True
	return False

def get_sectionstart_main(line):
	result = None
	if is_sectionstart(line):
		content = line.strip().strip("[]").split(":")
		if len(content) <= 2:
			result = content[0]
	return result

def get_sectionstart_subconfig(line):
	result = None
	if is_sectionstart(line):
		content = line.strip().strip("[]").split(":")
		if len(content) == 2:
			result = content[1]
	return result

LAYER_SEPARATOR = ";"

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

# A 'simple' git fetcher implementation
def get_git_layer(layer):
	b = layer.split(LAYER_SEPARATOR)
	if os.path.isdir(b[1]):
		print(b[1] + " seems to already exist, checking...")
		result = subprocess.call("cd " + b[1] + "; git status", shell=True)
		if result == 0:
			print("...looks good!")
			print("We didn't clone " + b[1] + " now but it seems to be intact.");
		else:
			print("...this didn't work!")
			print("We didn't clone " + b[1] + " now but it seems to be broken.");
		print("In any case, please manually check the state of the layer!")
	else:
		cmd = "git clone " + b[2] + " " + b[1]
		subprocess.call(cmd, shell=True)
		if len(b) > 3:
			cmd = None
			g = b[3].split("=")
			if len(g) == 1:
				cmd = "cd " + b[1] + "; git checkout -b blubber_" + b[3] + " " + b[3]
			elif g[0] == "tag" or g[0] == "commit":
				cmd = "cd " + b[1] + "; git checkout -b blubber_" + g[1] + " " +g[1]
			elif g[0] == "branch":
				cmd = "cd " + b[1] + "; git checkout -b blubber_" + g[1] + " origin/" + g[1]
			else:
				print("no idea what \"" + b[3] + "\" means, keeping a normal clone")
			if cmd:
				subprocess.call(cmd, shell=True)

# The Config object deals with most of the project related tasks.
class Config:
	def __init__(self):
		self.layers = []
		self.local = []
		self.blubber = {}
		self.subconfigs = {}
		self.BUILD_DEFAULT = "BUILD_DEFAULT"
		self.NO_BASE_CONFIG = "NO_BASE_CONFIG"
	def has_base_config(self):
		if self.NO_BASE_CONFIG in self.blubber:
			value = self.blubber[self.NO_BASE_CONFIG]
			if not value == None and not value == 0 and not value == "" and not value == "0" and not value == False and not value == "False":
				return False
		return True
	def assert_subconfig(self, ident):
		if not ident in self.subconfigs:
			self.subconfigs[ident] = Config()
	def add_layer(self, layer, subconfig = None):
		if subconfig:
			self.assert_subconfig(subconfig)
			self.subconfigs[subconfig].add_layer(layer)
		else:
			self.layers.append(layer)
	def get_layers(self):
		for l in self.layers:
			b = l.split(LAYER_SEPARATOR)
			if len(b) < 3:
				break
			elif b[0] == "git" or b[0] == "git-master":
				get_git_layer(l)
		for s in self.subconfigs.values():
			s.get_layers()
	def add_local(self, local, subconfig = None):
		if subconfig:
			self.assert_subconfig(subconfig)
			self.subconfigs[subconfig].add_local(local)
		else:
			self.local.append(local)
	def add_blubber(self, key, value, subconfig = None):
		if subconfig:
			self.assert_subconfig(subconfig)
			self.subconfigs[subconfig].add_blubber(key, value)
		else:
			self.blubber[key] = value
	def execute_poky_command(self, cmd, subconfig = None):
		result = 0
		if LOCAL_PLATFORM.is_Linux():
			if subconfig or self.has_base_config():
				cmd_intern = get_source_magic(subconfig) + "; " + cmd
				result = subprocess.call(cmd_intern, shell=True, executable=SHELL)
		return result
	def init_build_directories(self, subconfig = None):
		if self.has_base_config():
			self.execute_poky_command("", subconfig)
		for s in self.subconfigs.keys():
			self.subconfigs[s].init_build_directories(s)
	def setup_bblayers(self, subconfig = None, additional = []):
		real_layers = additional + self.layers
		if self.has_base_config():
			bbfile = get_layerfile_path(subconfig)
			if not os.path.isfile(bbfile):
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
			for i in real_layers:
				a = i.split(";")
				if a[0] == "subrepo":
					bb.insert(found + 1, "  " + p + "/" + a[2] + "/" + a[1] + " \\" + LINEFEED);
				elif not a[1] == "poky" and not a[0].endswith("-master"):
					bb.insert(found + 1, "  " + p + "/" + a[1] + " \\" + LINEFEED);
			f = open(bbfile, "w")
			for i in bb:
				f.write(i)
			f.close()
		for s in self.subconfigs.keys():
			self.subconfigs[s].setup_bblayers(s, real_layers)
	def setup_local(self, subconfig = None, additional = []):
		real_local = additional + self.local
		if self.has_base_config():
			localfile = get_conffile_path(subconfig)
			if not os.path.isfile(localfile):
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
			for i in real_local:
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
		for s in self.subconfigs.keys():
			self.subconfigs[s].setup_local(s, real_local)
	def show_message_single(self, ident):
		key = ident + MESSAGE_TRIGGER
		if key in self.blubber:
			print(self.blubber[key]);
	def show_message_all(self, ident):
		all_configs = [self] + list(self.subconfigs.values())
		for s in all_configs:
			s.show_message_single(ident)
	def setup(self):
		self.get_layers()
		self.init_build_directories()
		self.setup_bblayers()
		self.setup_local()
		self.show_message_all("SETUP")
	def build_default(self, subconfig = None):
		result = 0
		target = None
		if subconfig and self.subconfigs[subconfig].has_base_config() and self.BUILD_DEFAULT in self.subconfigs[subconfig].blubber:
			target = self.subconfigs[subconfig].blubber[self.BUILD_DEFAULT]
			print("will build default target " + target)
		elif self.BUILD_DEFAULT in self.blubber and self.has_base_config():
			target = self.blubber[self.BUILD_DEFAULT]
			print("will build default target " + target)
		else:
			print("no " + self.BUILD_DEFAULT + " set, aborting.")
		if target:
			result = self.execute_poky_command("bitbake " + target, subconfig)
			self.show_message_single("BUILD")
		return result

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

def get_config_layers(config, content):
	trig = False
	subconfig = None
	for l in content:
		i = l.strip()
		if is_sectionstart(i):
			if get_sectionstart_main(i) == SECTION_LAYERS:
				trig = True
				subconfig = get_sectionstart_subconfig(i)
			else:
				trig = False
				subconfig = None
		elif trig:
			config.add_layer(i, subconfig)

def get_config_local(config, content):
	b = ""
	first = -1
	trig = False
	subconfig = None
	for l in content:
		i = l.strip()
		if is_sectionstart(i):
			b = ""
			first = -1
			if get_sectionstart_main(i) == SECTION_LOCAL:
				trig = True
				subconfig = get_sectionstart_subconfig(i)
			else:
				trig = False
				subconfig = None
		elif trig:
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
				config.add_local(ass, subconfig)
				b = ""
				first = -1

def get_config_blubber(config, content):
	b = ""
	first = -1
	trig = False
	subconfig = None
	for l in content:
		i = l.strip()
		if is_sectionstart(i):
			b = ""
			first = -1
			if get_sectionstart_main(i) == SECTION_BLUBBER:
				trig = True
				subconfig = get_sectionstart_subconfig(i)
			else:
				trig = False
				subconfig = None
		elif trig:
			if first == -1:
				first = content.index(l)
			b += i
			if b.endswith("\\"):
				b = b[:-1] + "\r\n"
			else:
				b_in = b.split("=");
				if len(b_in) == 2:
					key = b_in[0].strip(" \"\r\n")
					if not key.endswith(MESSAGE_TRIGGER):
						value = b_in[1].strip(" \"").replace("\r","").replace("\n","")
					else:
						value = b_in[1].strip(" \"\r\n")
					config.add_blubber(key, value, subconfig)
				b = ""
				first = -1

def get_config(fname):
	if not os.path.isfile(fname):
		exit_fail("could not open Blubberfile")
	with open(fname) as f:
		raw_content = f.readlines()
	content = [i for i in raw_content if not i.strip() == "" and not i.strip().startswith("#")]
	config = Config()
	get_config_layers(config, content)
	get_config_local(config, content)
	get_config_blubber(config, content)
	return config

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
	print("    -s subconfig   Use 'subconfig' as configuration instead of default")
	print("  Supported commands:")
	print("    build          bitbakes the default target if BUILD_DEFAULT is set in the")
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

# Here is the actual main part!
FILENAME = "Blubberfile"
SUBCONFIG = None

CMD_HELP = ["help"]
CMD_VALIDATE = ["validate"]
CMD_CREATE = ["create"]
CMD_SETUP = ["setup"]
CMD_SHELL = ["shell"]
CMD_RUN = ["run"]
CMD_BUILD = ["build"]

CMDS_NEEDING_CONFIG = CMD_SETUP + CMD_SHELL + CMD_RUN + CMD_BUILD

if len(sys.argv) <= 1:
	print_help()
	exit(0)
cmd_index = 1
result = 0
while (len(sys.argv) > cmd_index) and (sys.argv[cmd_index].startswith("-")):
	if sys.argv[cmd_index] == "-f":
		if len(sys.argv) > cmd_index + 1:
			FILENAME = sys.argv[cmd_index + 1]
			print("using Blubberfile '" + FILENAME + "'")
			cmd_index = cmd_index + 2
		else:
			print("option -f needs additional Blubberfile path to be passed")
			cmd_index = cmd_index + 1
	elif sys.argv[cmd_index] == "-s":
		if len(sys.argv) > cmd_index + 1:
			SUBCONFIG = sys.argv[cmd_index + 1]
			print("using subconfiguration '" + SUBCONFIG + "'")
			cmd_index = cmd_index + 2
		else:
			print("option -s needs additional subconfiguration name to be passed")
			cmd_index = cmd_index + 1
	else:
		print("option " + sys.argv[cmd_index] + " could not be recognized, skipping")
		cmd_index = cmd_index + 1

if (len(sys.argv) <= cmd_index) or (sys.argv[cmd_index] == "help"):
	print_help()
	quit(0)

cmd = sys.argv[cmd_index]
c = None
if cmd in CMDS_NEEDING_CONFIG:
	c = get_config(FILENAME)

if cmd in CMD_VALIDATE:
	LOCAL_PLATFORM.validate()
elif cmd in CMD_CREATE:
	to_blubberfile(None)
elif cmd in CMD_SETUP:
	c.setup()
elif cmd in CMD_SHELL:
	c.execute_poky_command(SHELL, SUBCONFIG)
elif cmd in CMD_RUN:
	a = sys.argv[cmd_index + 1:]
	cmd = ""
	for i in a:
		cmd += i.strip() + " "
	result = c.execute_poky_command(cmd, SUBCONFIG)
elif cmd in CMD_BUILD:
	result = c.build_default(SUBCONFIG)
else:
	print("could not recognize commmand '" + sys.argv[cmd_index] + "'")
	print_help()

quit(result)
