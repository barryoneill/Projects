IMAP Summary Script
===================

Connects to the specified IMAP server using the supplied credentials, queries all mailboxes 
(as returned by [IMAP4.list()](http://docs.python.org/3.1/library/imaplib.html#imap4-objects)) 
and pretty prints a summary of the folders.  

The username and password can be specified on the command line, but will be prompted for if
not supplied.  

The summary can be sorted according to name, size or number of messages (ascending or descending)

### Usage ###

Use Python 3!

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
	  --password PASSWORD   The password (will prompt if not provided)
	  --no-tls              Specify to use IMAP instead of IMAP_SSL module
	  --sort {name,num_msgs,size}
	                        Sort output by foldername, num messages, or size
	                        (bytes)
	  --sort-reverse        Specify to reverse sort output
	

### Sample output ###

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
