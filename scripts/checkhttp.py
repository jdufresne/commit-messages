#!/usr/bin/env python3

import os
import re
import requests
import subprocess
import urllib


# From Django's URLValidator.
ul = '\u00a1-\uffff'  # unicode letters range (must not be a raw string)

# Host patterns
hostname_re = r'[a-z' + ul + r'0-9](?:[a-z' + ul + r'0-9-]{0,61}[a-z' + ul + r'0-9])?'
# Max length for domain name labels is 63 characters per RFC 1034 sec. 3.1
domain_re = r'(?:\.(?!-)[a-z' + ul + r'0-9-]{1,63}(?<!-))*'
tld_re = (
    r'\.'                                # dot
    r'(?!-)'                             # can't start with a dash
    r'(?:[a-z' + ul + '-]{2,63}'         # domain label
    r'|xn--[a-z0-9]{1,59})'              # or punycode label
    r'(?<!-)'                            # can't end with a dash
    r'\.?'                               # may have a trailing dot
)
host_re = hostname_re + domain_re + tld_re

url_re = re.compile(
    r'http://' + host_re + r'(?:[/?][^\s#]*)?',
    re.IGNORECASE
)
example_re = re.compile(r'\bexample\.')


def main():
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
    urls = {}
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
                if os.path.islink(path):
                    continue

                print(path)

                try:
                    with open(path) as fp:
                        for line in fp:
                            matches = url_re.findall(line)
                            for match in matches:
                                # Strip rst & md syntax.
                                match = match.rstrip('"\'(),.<>[]_`')
                                if match not in urls:
                                    pr = list(urllib.parse.urlparse(match))
                                    if not example_re.search(pr[1]):
                                        print('  %s' % match)

                                        pr[0] = 'https'
                                        secure_url = urllib.parse.urlunparse(pr)

                                        urls[match] = None
                                        try:
                                            r = requests.get(secure_url, timeout=3)
                                        except requests.exceptions.InvalidURL as e:
                                            print('    %s' % e)
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

    for old_url, new_url in sorted(urls.items(), key=lambda item: len(item[0]), reverse=True):
        if new_url:
            print(f'{old_url} -> {new_url}')

            prune_args = []
            for name in prune_name:
                prune_args.extend(['-name', name, '-prune', '-o'])

            ignore_args = []
            for ext in ignore_ext:
                ignore_args.extend(['-not', '-name', f'*{ext}'])

            cmd = [
                'find', root,
                *prune_args,
                *ignore_args,
                '-type', 'f',
                '-exec', 'sed', '-i', '-e', 's|%s|%s|g' % (re.escape(old_url), new_url), '{}', ';'
            ]
            subprocess.check_call(cmd)


if __name__ == '__main__':
    main()
