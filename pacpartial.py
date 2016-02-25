#!/usr/bin/env python
# Copyright 2016 Tom Mewett
# License: Apache 2.0

# A new subprocess API was released in v3.5,
# but the old one will be used until depreciated.
# Eventually this may use ctypes & libalpm,
# or become a C program.
from subprocess import DEVNULL, check_output
from os import environ, execvp
from collections import defaultdict


from argparse import ArgumentParser
parser = ArgumentParser(description="Intelligently upgrade or install specific packages on a partially-updated system")

parser.add_argument('package', nargs='+')
parser.add_argument('-v', '--verbose', action='store_true', help="output in more detail")
parser.add_argument('-c', '--checkupdates', action='store_true', help="use checkupdates' default temporary database (implies -n)")
parser.add_argument('-n', '--dry-run', action='store_true', help="simulate; don't install anything")
parser.add_argument('-k', '--keep',
    action='append', default=[], metavar="package", help="keep this package from being updated or installed (can be specified multiple times)")

parser.add_argument('--version', action='version', version="%(prog)s 0.1")

args = parser.parse_args()
if args.checkupdates: args.dry_run = True


def command(*cmd):
    return check_output(cmd, stderr=DEVNULL, universal_newlines=True)

def cmd2set(*cmd):
    return set(command(*cmd).splitlines())

# Calls pactree and collects & processes the results into a database.
# Database is a dict of {pkg: [dbit, rbit, related]} where the bits/bools determine
# which "tree" (deps or reverse deps) has been done yet. rbit is implied as !dbit
# because, well, who would call a function to do nothing?
# This is an over-the-top way of reducing the calls to pactree, which take a long time.
_reldict = defaultdict(lambda: [False, False, set()])
def _relupdate(tree, dbit):

    for line in tree.splitlines():
        text = line.lstrip(r"| `-")
        name = text.split()[0] # handle X provides Y
        level = (len(line) - len(text)) // 2
        if level == 0:
            lastlev = 0
            lastname = name
            keystack = []
            continue
        if level > lastlev: keystack.append(lastname)
        elif level < lastlev: del keystack[level-lastlev:] # fall multiple levels
        val = _reldict[keystack[-1]]
        if dbit: val[0] = True
        if not dbit: val[1] = True
        val[2].add(name)
        lastname = name
        lastlev = level

def related(pkg):
    if args.verbose: print("Finding related for %s..." % pkg)

    val = _reldict[pkg]
    if not val[0]: _relupdate(command('pactree', '-sa', pkg), True)
    if not val[1]:
        try:
            _relupdate(command('pactree', '-ra', pkg), False)
        except:
            if args.verbose: print("%s not installed, reverse deps skipped." % pkg)

    return val[2]

# This is the main tree-traversal algorithm, implemented recursively.
# NOTE "missing" refers to uninstalled AND out-of-date packages.
# NOTE found is a proper subset of visited.
def findmissing(pkgs, found=set(), visited=set()):
    pkgs -= visited
    if not pkgs: return found
    if args.verbose: print("Current set size: %d" % len(pkgs))
    rel = pkgs.copy() # related doesn't give its called packages back
    for pkg in pkgs:
        rel |= related(pkg)
    # keep just uninstalled or out-of-date
    missing = rel - (installed - stale) | always
    return findmissing(missing, found | missing, pkgs | visited)

def install(pkgs, others=set()):
    conflicts = keep & (pkgs | others)
    if conflicts:
        print("The following kept packages must be updated to complete this operation:")
        print("\n".join(conflicts))
        # TODO put this back in, honoring -c
#        check_call(("pacman", "-Qu", *conflicts))
        print("NOTE: keeping could mean these packages or those that depend on them break.")
        choice = input("Continue? [yes/no/keep] ")
        if choice == "keep":
            pkgs -= conflicts
            others -= conflicts
        elif choice not in ("y", "Y", "yes", "YES"): return
    if args.dry_run:
        print("\n".join(pkgs | others))
        return
    # We can discard all uninstalled others because they will be pulled in.
    # pacman -S updates packages maintaining their explicit/dep status.
    pkgs |= others & stale
    execvp("pacman", ("pacman", "-S", "--needed", *pkgs))


targets = set(args.package)
keep = set(args.keep)
installed = cmd2set("pacman", "-Qq")
explicit = cmd2set("pacman", "-Qeq")

if args.checkupdates:
    stale = cmd2set("pacman", "-Quq", "--dbpath", "/tmp/checkup-db-" + environ['LOGNAME'])
else:
    stale = cmd2set("pacman", "-Quq")

# Some things just have to be done...
#always = cmd2set() # maybe packages in base should be updated always?
always = {"archlinux-keyring"} & stale

try:
    with open("/etc/pacman.d/partial_keep", 'r') as f:
        keep |= set(f.read().splitlines())
except IOError:
    if args.verbose: print("Keep-file cannot be read, continuing.")

try:
    with open("/etc/pacman.d/partial_always", 'r') as f:
        always |= set(f.read().splitlines())
except IOError:
    if args.verbose: print("Always-file cannot be read, continuing.")


if not stale:
    print("Up to date (according to DB). Starting install.")
    install(targets)

print("Finding missing & related packages...")
missing = findmissing(targets)
#print(_reldict)
if missing:
    print("Found. Starting update.")
    install(targets, missing)
else:
    print("None found. Starting install.")
    install(targets)
