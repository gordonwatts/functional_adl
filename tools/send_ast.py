# Send an ast to a requested queue name on a rabbit server.
import sys
from write_ast import generate_ast
import pika
import pickle

def send_ast_msg (ast_number:int, rabbit_address:str, queue_name:str):
    a = generate_ast(ast_number)

    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_address))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    channel.basic_publish(exchange='', routing_key=queue_name, body=pickle.dumps(a))
    channel.close()

if __name__ == "__main__":
    bad_args = len(sys.argv) != 4
    bad_args = bad_args or not str.isdigit(sys.argv[1])

    if bad_args:
        print ('Usage: python send_ast.py <ast-number> <rabbit-ip-address> <queue-name>')
    else:
        send_ast_msg(int(sys.argv[1]), sys.argv[2], sys.argv[3])
