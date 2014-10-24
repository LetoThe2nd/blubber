blubber
=======

Abstract/Motivation
-------------------

A friendly tool for managing your yocto/poky projects :)
What does this mean? When setting up your local environment for building a yocto/poky based project, you usually follow these steps:
(More or less of course, there are lots of variations based on your worklow and personal likings.)

1. Get poky (download and unpack, or git clone)
2. Get the layers (download and unpack, git clone, svn co, whatever) that are necessary for your build
3. Init the build directory by source-ing poky/oe-init-build-env
4. Modify build/conf/bblayers.conf to include the additional non-poky layers.
5. Modify build/conf/local.conf to include the needed configuration options, like MACHINE, xxx
6. Run your desired build in the shell that source-ed poky/oe-init-build-env

You see, there are quite some steps involved. And most of them (especially 4 and 5) allow for a lot of errors that are easy to avoid/spot for experienced users, but hinder easy reproduction by third persons or users.

Blubber can help you with that!
-------------------------------

But be warned first. Blubber is still in pre-pre-pre-alpha stage (more like a proof of concept), and has the following defects/bugs/non-features
- Horribly bad python code (Yes, its really that bad. Blame me, its my first attempt to use that language)
- No error checking whatsoever
- Largely incomplete feature set
- Did I already mention the utterly bad code?
- Only supports git sources so far.

Despite that, it can already do some magic:
- Getting poky and layers from git, and checking out branches/tags/commits if needed
- Accordingly setting up build/conf/bblayers.conf
- Setting up build/conf/local.conf with a set of predefined options
- Running arbitrary commands with proper shell setup (source-ed poky/oe-init-build-env) for the configured project.
- Environment variables are honoured during the setup step and can be used to override the Blubberfile settings
- Opening a shell properly initialized for the build

How dows it work?
-----------------

Blubber borrows a lot of ideas from make. That means, the only thing your have to do is to drop a _Blubberfile_ in the directory that you want to work in. (So far it has to be named Blubberfile explicitly. See ToDo list below.) Then you can fire up blubber and be done. Blubber itself is a one-file script that can be dropped into the project directory, but should also work fine when called from $PATH or such. So this is how you set up your build with Blubber:

0. Put blubber.py into a directory in your $PATH or just the project directory that you want to work in.
1. Get the Blubberfile for your project
2. Fire up blubber.py setup
... Done. Now you can run your builds - either using the traditional way, or by issuing "blubber.py run bitbake core-image-minimal" for example. Blubber will take everything after the "run" command and just execute it in the build directory as if you had prepared the shell and then typed it manually. It has the advantage though, that its not necessary to keep track of the shells state anymore. And the shell will be unchanged afterwards, as blubber intently uses a sub shell.

Design decisions / ToDo List
----------------------------

Blubber intently is constructed as a one-file script so far. This means you can easily drop it everywhere and just execute it.
What shall go into blubber in the (near) future?
- Error checking!
- Differently named Blubberfiles (think: make -f Foobar.txt)
- Getting layers from svn, ftp, tarballs, or just plain file copy
- Refreshing the Blubberfile after you changed something in conf/{local,bblayers}.conf
- Code base improvements...

If sounds interesting, please have try - and scream loudly if you have comments, questions...

Leto
