#!/usr/bin/env python3

import os
import re
import requests
import subprocess


url_re = re.compile(r'\bhttps?://docs\.python\.org/2/[^ <>]*')


def main():
    prune_name = [
        '.git',
        '.hg',
        '.tox',
        '__pycache__',
        'LC_MESSAGES',
        'node_modules',
    ]

    ignore_ext = [
        '.bmp',
        '.db',
        '.eot',
        '.exe',
        '.gif',
        '.ico',
        '.inv',
        '.jpeg',
        '.jpg',
        '.mo',
        '.png',
        '.po',
        '.pyc',
        '.pyo',
        '.sql',
        '.svg',
        '.ttf',
        '.whl',
        '.woff',
        '.woff2',
        '.xls',
        '.zip',
    ]

    urls = {}

    root = os.getcwd()
    for dirpath, dirnames, filenames in os.walk(root):
        for name in prune_name:
            try:
                dirnames.remove(name)
            except ValueError:
                pass

        for fn in filenames:
            _, ext = os.path.splitext(fn)
            if ext not in ignore_ext:
                path = os.path.join(dirpath, fn)
                print(path)

                try:
                    with open(path) as fp:
                        for line in fp:
                            matches = url_re.findall(line)
                            for match in matches:
                                match = match.strip()
                                if match not in urls:
                                    print(f'  {match}')

                                    try:
                                        r = requests.get(match, timeout=3)
                                    except (requests.exceptions.SSLError, requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout):
                                        urls[match] = None
                                    else:
                                        if r.status_code == 200:
                                            print(f'  -> {r.url}')
                                            urls[match] = r.url
                except Exception as e:
                    print(f'  {e}')
                    pass

    for old_url, new_url in sorted(urls.items(), key=lambda item: len(item[0]), reverse=True):
        print(f'{old_url} -> {new_url}')
        if new_url:
            cmd = [
                'find', root,

                '-name', '.git', '-prune', '-o',
                '-name', '.hg', '-prune', '-o',
                '-name', '.tox', '-prune', '-o',
                '-name', '__pycache__', '-prune', '-o',
                '-name', 'LC_MESSAGES', '-prune', '-o',
                '-name', 'node_modules', '-prune', '-o',
                '-type', 'f',

                '-exec', 'sed', '-i', '-e', 's|%s|%s|g' % (old_url.replace('.', '\\.'), new_url), '{}', ';'
            ]
            subprocess.check_call(cmd)



if __name__ == '__main__':
    main()
