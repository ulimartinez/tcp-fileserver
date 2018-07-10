# TCP file transfer
This is a python implementation of a file server using sockets and following the TCP protocol. The file server is:
* single-threaded 
* accepts multiple concurrent client connections

Since TCP is stream oriented, the outputs of multiple writes may be concatenated and reads may only return a portion of the data already sent.

