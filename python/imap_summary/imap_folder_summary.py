"""
Script to display a summary of folders in an IMAP account, based on
a really crude script I used back in the day on Redbrick.

:author: Barry O'Neill (barry@barryoneill.net)

 ----------------------------------------------------------------

usage: imap_folder_summary.py [-h] [--username USERNAME] [--password PASSWORD]
                              [--no-tls] [--sort {name,num_msgs,size}]
                              [--sort-reverse]
                              hostname port

Display a summary of all folders in an IMAP account

positional arguments:
  hostname              The IMAP hostname
  port                  The IMAP port number (eg 993)

optional arguments:
  -h, --help            show this help message and exit
  --username USERNAME   The username (will prompt if not provided)
  --password PASSWORD   The password (will prompt if not provided
  --no-tls              Specify to use IMAP instead of IMAP_SSL module
  --sort {name,num_msgs,size}
                        Sort output by foldername, num messages, or size
                        (bytes)
  --sort-reverse        Specify to reverse sort output


 -----------------------------------------------------------------------

Sample output
~> python imap_folder_summary.py imap.somewhere.com 993 --sort=size
Username: eve
Password:

Name                            No. Msgs             Size(b)   Size(txt)
"VacationStuff"                      133             1015676    991.87KB
"Work.ProjectA"                      240             1734018      1.65MB
"Friends.Alice"                      685             1777753      1.70MB
"Work.ProjectB"                      274             1954619      1.86MB
"Projects"                           788             2832524      2.70MB
"Friends.Bob"                        298             4180646      3.99MB
"INBOX"                              951            15076086     14.38MB
"archive"                           2027            24877812     23.73MB

"""

import sys
import re
import socket
import getpass
from argparse import ArgumentParser
from imaplib import IMAP4, IMAP4_SSL

def main():
    try:

        parser = ArgumentParser(description='Display a summary of all folders in an IMAP account')

        # positional
        parser.add_argument('hostname', metavar='hostname', help='The IMAP hostname')
        parser.add_argument('port', metavar='port', type=int, help='The IMAP port number (eg 993)')

        # optional
        parser.add_argument('--username', dest='username', help='The username (will prompt if not provided)')
        parser.add_argument('--password', dest='password', help='The password (will prompt if not provided)')
        parser.add_argument('--no-tls', dest='no_tls', action='store_true',
                            help='Specify to use IMAP instead of IMAP_SSL module')
        parser.add_argument('--sort', dest='sort', choices=['name','num_msgs','size'], default='name',
                            help='Sort output by foldername, num messages, or size (bytes)')
        parser.add_argument('--sort-reverse', dest='sort_reverse', action='store_true',
                            help='Specify to reverse sort output')

        args = parser.parse_args()

        # prompt for username/password if not provided via args
        if not args.username:
            args.username = input("Username: ")

        if not args.password:
            args.password = getpass.getpass("Password: ")


        folderlist = get_folder_summary(args.hostname,args.port,args.username,args.password,not args.no_tls)

        folderlist.sort(key=lambda f:f[args.sort],reverse=args.sort_reverse)

        line_fmt = "%-30s%10s%20s%10s"

        print(line_fmt % ("Name", "No. Msgs", "Size(b)","Size(txt)"))
        for folder in folderlist:
            print((line_fmt % (folder['name'], folder['num_msgs'], folder['size'], greek(folder['size']))))

        return 0

    except KeyError as e:
        sys.stderr.write('Missing config key: {}, check all entries in serverconfig.cfg are present'.format(e))

    except IMAP4.error as e:
       sys.stderr.write('IMAP error: {}'.format(e))

    except socket.error as e:
        sys.stderr.write('Network error: {} (check that hostname and port are correct)'.format(e))

    return 1


def get_folder_summary(hostname, port, username, password, ssl=True):

    """
    Connect to the specified server with the provided credentials and get a summary of each mailbox
    :type username: str
    :type password: str
    :type hostname: str
    :type port: int
    :type ssl: bool
    """

    # Extract from: http://docs.python.org/3.1/library/imaplib.html#imap4-objects
    # Each command returns a tuple (type, [data, ...]) where type is usually 'OK' or 'NO', and data is either
    # the text from the command response, or mandated results from the command. Each data is either a string,
    # or a tuple. If a tuple, then the first part is the header of the response, and the second part contains
    # the data (ie: ‘literal’ value)."

    ## Regular expression for catching the size param
    re_size = re.compile('.*RFC822\.SIZE\s*([0-9]+)\)\s*')
    folderlist = []

    print(("Connecting to {}:{}, ssl={}...".format(hostname, port, ssl)))
    imap = IMAP4_SSL(hostname, port) if ssl else IMAP4(hostname, port)

    print(("Authenticating user '{}'...".format(username)))
    login_result,server_props = imap.login(username, password)
    check_result_ok(login_result,"Server rejected login credentials")

    print("Connected.  Listing mailboxes:")

    list_resultcode, mbox_list = imap.list()
    check_result_ok(list_resultcode, "server failed to list messages")

    for mailbox_entry in mbox_list:

        folder = {}

        # mailbox_entry is a string eg, '(\\HasNoChildren) "." "Drafts"' - we're only interested in the name
        mbox_name = mailbox_entry.decode("utf-8").split(sep=' "." ')[1]

        print("Querying maibox", mbox_name)

        ## Do a SELECT on the individual mailbox
        ## (returns the number of messages)
        select_resultcode, select_response = imap.select(mbox_name, 1)

        if select_resultcode != 'OK':
            print("   .. skipping mailbox {}, SELECT command said: {}".format(mbox_name, select_resultcode))
            continue

        folder['name'] = mbox_name
        folder['size'] = 0
        folder['num_msgs'] = int(select_response[0])

        search_resultcode, msg_numbers = imap.search(None, 'ALL')
        if search_resultcode != 'OK':
            print("   .. skipping mailbox {}, SEARCH command said: {}".format(mbox_name, search_resultcode))
            continue

        # get an int list of all the message numbers
        msg_numbers = [int(msgnum) for msgnum in msg_numbers[0].split()]

        if msg_numbers:

            # fetch UID and size for each message in this this folder.  Done as a batch, by
            # requesting all messages with message_set parameter:"lowest_num:highest_num"
            msg_numbers.sort()
            message_set = "%d:%d" % (msg_numbers[0], msg_numbers[-1])

            fetch_resultcode, message_infos = imap.fetch(message_set, "(UID RFC822.SIZE)")
            if fetch_resultcode != 'OK':
                print("   .. skipping mailbox {}, FETCH for {} said: {}".format(mbox_name, message_set, search_resultcode))
                continue

            for message_info in message_infos:

                sizematch = re_size.match(message_info.decode("utf-8"))
                folder['size'] += int(sizematch.group(1))


        ## Append this folder info to the folder list
        folderlist.append(folder)

    return folderlist

def check_result_ok(status, err_msg):
    """
    utility method for checking IMAP responses for errors (status will not be 'OK')
    """

    if status != 'OK':
        raise IMAP4.error("{}: server said: {}".format(err_msg,status))

# -----------------------------------------------------------------------

## yoinked a very long time ago from
## http://mail.python.org/pipermail/python-list/1999-December/018519.html

def greek(size):
    """Return a string representing the greek/metric suffix of a size"""

    _abbrevs = [
        (1 << 50, 'PB'),
        (1 << 40, 'TB'),
        (1 << 30, 'GB'),
        (1 << 20, 'MB'),
        (1 << 10, 'KB'),
        (1, '')
    ]

    for factor, suffix in _abbrevs:
        if size > factor:
            break
    return "{:10.2f}{}".format(size / factor, suffix)


if __name__ == '__main__':
    sys.exit(main())
