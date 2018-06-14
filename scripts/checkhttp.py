#!/usr/bin/env python3

import os
import re
import requests
import subprocess
import urllib


url_re = re.compile(r'\bhttp://[^ ,"\')<>\]]+')
example_re = re.compile(r'\bexample\.')


def main():
    # prune_wholepath = [
    #     'data',
    # ]

    prune_name = [
        '.git',
        '.hg',
        '.tox',
        '__pycache__',
        '_vendor',
        'LC_MESSAGES',
        'node_modules',
        'vendor',
    ]

    ignore_ext = [
        '.bmp',
        '.bz2',
        '.db',
        '.eot',
        '.exe',
        '.gif',
        '.gz',
        '.ico',
        '.inv',
        '.jpeg',
        '.jpg',
        '.lzma',
        '.mo',
        '.pdf',
        '.png',
        '.po',
        '.pyc',
        '.pyo',
        '.sql',
        '.svg',
        '.tgz',
        '.ttf',
        '.whl',
        '.woff',
        '.woff2',
        '.xls',
        '.xz',
        '.zip',
    ]

    root = os.getcwd()
    for dirpath, dirnames, filenames in os.walk(root):
        # if dirpath == root:
        #     for name in prune_wholepath:
        #         try:
        #             dirnames.remove(name)
        #         except ValueError:
        #             pass

        for name in prune_name:
            try:
                dirnames.remove(name)
            except ValueError:
                pass

        for fn in filenames:

            _, ext = os.path.splitext(fn)
            if ext not in ignore_ext:
                path = os.path.join(dirpath, fn)
                if os.path.islink(path):
                    continue

                print(path)

                urls = {}
                try:
                    with open(path) as fp:
                        for line in fp:
                            matches = url_re.findall(line)
                            for match in matches:
                                match = match.strip()
                                if match not in urls:
                                    if '.' in match:
                                        if not example_re.search(match):
                                            print('  %s' % match)

                                            pr = list(urllib.parse.urlparse(match))
                                            pr[0] = 'https'
                                            secure_url = urllib.parse.urlunparse(pr)

                                            urls[match] = None
                                            try:
                                                r = requests.get(secure_url, timeout=3)
                                            except (requests.exceptions.SSLError,
                                                    requests.exceptions.ConnectionError,
                                                    requests.exceptions.ReadTimeout,
                                                    requests.exceptions.TooManyRedirects):
                                                pass
                                            else:
                                                pr = urllib.parse.urlparse(r.url)
                                                if pr.scheme == 'https' and r.status_code == 200:
                                                    print('  -> %s' % r.url)
                                                    urls[match] = r.url
                except UnicodeDecodeError as e:
                    print(str(e))

                for old_url, new_url in urls.items():
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

                            '-exec', 'sed', '-i', '-e', 's|%s|%s|g' % (re.escape(old_url), new_url), '{}', ';'
                        ]
                        subprocess.check_call(cmd)




if __name__ == '__main__':
    main()
