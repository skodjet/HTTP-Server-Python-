"""
THIS CODE IS MY OWN WORK, IT WAS WRITTEN WITHOUT CONSULTING

A TUTOR OR CODE WRITTEN BY OTHER STUDENTS - Thomas Skodje
"""
import signal
import sys
import socket

def receive_data(tertiary_url, request, is_get):
    # Create a second socket that will send requests to the web server and wait for a response.
    sending_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Set the sending socket timeout to 20 seconds
    sending_socket.settimeout(20)

    # Connect to web server on port 80 (HTTP port)
    sending_socket.connect((tertiary_url, 80))
    sending_socket.sendall(request)

    # Receive data from the server
    web_data_counter = 1

    receiving = True
    while receiving:
        web_data = sending_socket.recv(4096)
        web_data_counter += 1

        if len(web_data) > 0:
            conn.send(web_data)
        else:
            receiving = False
            break


# Have the user input the port number as a command line argument
try:
    port_num = int(sys.argv[1])
except IndexError:
    print("Please input a valid port number as an argument")
    exit(1)
except ValueError:
    print("Please input a valid integer as an argument (strings are not accepted)")
    exit(1)

# Get this computer's IP address
host = socket.gethostname()
ip_addr = socket.gethostbyname(host)

# Create a TCP socket that will listen on startup for incoming requests.
listening_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
listening_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

listening_socket.bind(('localhost', port_num))

# Only 1 connection is accepted at a time
listening_socket.listen(1)
listening = True

url = None
host_port_num = None
subsequent_request = False
webserver_name = ""
not_implemented = ""


try:
    while listening:
        (conn, addr) = listening_socket.accept()

        # Buffer size of 4096 (4 Kilobytes)
        request = conn.recv(4096)

        # Put each line of the request into an array.
        decoded_request = request.decode()
        request_array = decoded_request.split("\r\n")

        if request_array[0] == "":
            continue

        request_type = request_array[0]

        # Don't handle requests that need outside information to continue
        host_line = request_array[1]
        contains_localhost = host_line.find("localhost")
        contains_url = -1

        if len(webserver_name) > 5:
            contains_url = host_line.find(webserver_name[5:])

        if (contains_localhost == -1) and (contains_url == -1):
            continue

        is_get = (request_type[:3] == 'GET')

        # Handle requests that are not GET requests
        if not is_get:
            not_implemented = "HTTP/1.0 501 Not Implemented\r\n\r\n"

        # Find the url of the website
        first_line_array = request_type.split(" ")
        url = first_line_array[1]


        # Get the url without the "http://" or "https://"
        secondary_url_index = url.find("//")
        secondary_url = url[secondary_url_index + 2:]

        tertiary_url_index = secondary_url.find("/")

        if tertiary_url_index != -1:
            tertiary_url = secondary_url[:tertiary_url_index]
        else:
            tertiary_url = secondary_url

        # Create the correct GET request.
        get_line = first_line_array[1]
        correct_get = "/"
        num_slashes = 0
        for char in get_line:
            if num_slashes >= 2:
                correct_get += char
            if char == "/":
                num_slashes += 1

        if num_slashes < 2:
            correct_get = "/"

        # Create the correct hostname
        split_hostname_array = request_array[1].split(" ")
        correct_hostname = split_hostname_array[0] + tertiary_url

        # Find if there is a "Referer" line
        if not subsequent_request:

            has_referer = False
            for line in request_array:
                referer = line.find("Referer")

                # Referer line found! Reformat request.
                if referer != -1:
                    has_referer = True

                    # The correct hostname is everything between the third slash and fourth slash in this line.
                    line_slashes = 0
                    correct_hostname = "Host:"
                    tertiary_url = ""
                    correct_get = ""
                    for character in line:
                        if line_slashes == 3:
                            if character != '/':
                                correct_hostname += character
                                tertiary_url += character

                        if line_slashes >= 4:
                            correct_get += character

                        if character == '/':
                            line_slashes += 1

                    if len(correct_get) == 0:
                        correct_get = first_line_array[1]

        elif subsequent_request:
            correct_hostname = webserver_name
            tertiary_url = webserver_name[5:]
            correct_get = first_line_array[1]

        # Reassemble the request
        http_type = first_line_array[2]
        unencoded_request = "GET " + correct_get + " " + http_type + "\r\n" + correct_hostname + "\r\n"

        for j in range(2, len(request_array)):
            unencoded_request += request_array[j]
            unencoded_request += "\r\n"

        unencoded_request = unencoded_request[:-2]

        # unencoded_request += "\r\n"

        encoded_request = unencoded_request.encode('utf-8')

        if is_get:
            receive_data(tertiary_url, encoded_request, is_get)
        if not is_get:
            not_implemented_encoded = not_implemented.encode("utf-8")
            receive_data(tertiary_url, not_implemented_encoded, False)

        if not subsequent_request:
            subsequent_request = True
            webserver_name = correct_hostname

# Handle Control + C
except KeyboardInterrupt:
    listening_socket.close()
    sys.exit()
