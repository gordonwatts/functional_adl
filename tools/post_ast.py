# Send an ast to a url
import sys
from write_ast import generate_ast
import os
import pickle
import requests
import json
import time

def send_ast_msg (ast_number:int, base_url:str):
    a = generate_ast(ast_number)

    # Build the URL and send it.
    d = pickle.dumps(a)

    done = False
    first = True
    while not done:
        if not first:
            time.sleep(10)
        first = False

        r = requests.post(f'{base_url}/query', headers={"content-type": "application/octet-stream"},  data=d)

        if r.content.decode("utf-8")[0:1] != '{':
            print (f'Error: {r.content}')
        else:
            dr = json.loads(r.content)
            print (dr)
            done = dr['done']
    print (dr['files'])

if __name__ == "__main__":
    bad_args = len(sys.argv) != 3
    bad_args = bad_args or not str.isdigit(sys.argv[1])

    if bad_args:
        print ('Usage: python post_ast.py <ast-number> <url>')
        print ('  url is in the form http://localhost:8000, for example.')
    else:
        send_ast_msg(int(sys.argv[1]), sys.argv[2])
