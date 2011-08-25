#!/usr/bin/env python
#coding: utf-8

import subprocess
import shlex
import time
import tempfile
import sys
from optparse import OptionParser


def log(text):
    print '[%s] *** %s' % (time.strftime('%Y-%m-%d %H:%M:%S'), text)


def sh(command, finalize=True):
    process = subprocess.Popen(shlex.split(command), stderr=subprocess.PIPE,
                               stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    if finalize:
        process.wait()
        process.out = process.stdout.read()
        process.err = process.stderr.read()
    return process


def bash(command, finalize=True):
    return sh('bash -c "%s"' % command, finalize=finalize)


def table_line(columns):
    row = []
    for value, size in columns:
        row.append(str(value).center(size))
    return '|%s|' % '|'.join(row)


parser = OptionParser()
parser.add_option('-s', '--since-commit', help='Since this commit ID', metavar="SINCE_COMMIT")
parser.add_option('-p', '--path', help='Path to the repository', metavar="REPOSITORY_PATH")
(options, args) = parser.parse_args()
if not options.path:
    path = '.'
else:
    path = options.path
if not options.since_commit:
    since_commit = ''
else:
    since_commit = options.since_commit + '..'


log('Getting commit history...')
tmp_filename = tempfile.mktemp()
command = 'cd "%s"; git log --shortstat %s > %s' % (path, since_commit,
                                                    tmp_filename)
commits_pipe = bash(command)
if commits_pipe.err:
    print 'ERROR:'
    print commits_pipe.err
    print
    parser.print_help()
    print 'Exiting...'
    exit(1)


log('Ok, collecting only information we need on these commits...')
commits_fp = open(tmp_filename)
commits = []
author = ''
insertions = -1
deletions = -1
files_changed = -1
for i, line in enumerate(commits_fp):
    if line.startswith('commit') and i > 0:
        if author == '' or insertions == -1 or deletions == -1 or files_changed == -1:
            continue
        commits.append({'author': author, 'insertions': insertions,
                        'deletions': deletions,
                        'files_changed': files_changed})
        author = ''
        insertions = -1
        deletions = -1
        files_changed = -1
    elif line.startswith('Author'):
        author = ' '.join(line.split()[1:])
    elif 'insertion' in line:
        parameters = [int(x.strip().split()[0]) for x in line.split(',')]
        files_changed, insertions, deletions = parameters
commits.append({'author': author, 'insertions': insertions,
                'deletions': deletions,
                'files_changed': files_changed})
commits_fp.close()


log('Consolidating commits by author...')
commits_consolidated_by_author = {}
for commit in commits:
    email = commit['author'].split('<')[1].split('>')[0]
    if email not in commits_consolidated_by_author:
        commits_consolidated_by_author[email] = {}
        commits_consolidated_by_author[email]['insertions'] = 0
        commits_consolidated_by_author[email]['deletions'] = 0
        commits_consolidated_by_author[email]['files_changed'] = 0
        commits_consolidated_by_author[email]['commits'] = 0
    commits_consolidated_by_author[email]['insertions'] += commit['insertions']
    commits_consolidated_by_author[email]['deletions'] += commit['deletions']
    commits_consolidated_by_author[email]['files_changed'] += commit['files_changed']
    commits_consolidated_by_author[email]['commits'] += 1


log('Done! Enjoy the results:')
header = table_line([('Author', 50), ('# of commits', 14),
                    ('# of insertions', 17), ('# of deletions', 16),
                    ('# of file changes', 19)])
print '-' * len(header)
print header
print '-' * len(header)
authors_emails = commits_consolidated_by_author.keys()
authors_emails.sort()
for author_email in authors_emails:
    value = commits_consolidated_by_author[author_email]
    print table_line([(author_email, 50), (value['commits'], 14),
                      (value['insertions'], 17), (value['deletions'], 16),
                      (value['files_changed'], 19)])
    
print '-' * len(header)
