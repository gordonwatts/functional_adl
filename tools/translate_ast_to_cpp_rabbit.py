# Run the translation in rabbit
import pika
import sys
import pickle
import ast
import json
from adl_func_backend.xAODlib.exe_atlas_xaod_hash_cache import use_executor_xaod_hash_cache

# WARNING:
# Meant to be run from within a container. Some things are assumed:
#  1) /cache maps to a source code location

def process_message(ch, method, properties, body):
    'Message comes in off the queue. We deal with it.'
    a = pickle.loads(body)
    if a is None or not isinstance(a, ast.AST):
        print (f"Body of message wasn't an ast: {a}")

    # Now do the translation.
    r = use_executor_xaod_hash_cache (a, '/cache')

    # Create the JSON message that can be sent on to the next stage.
    msg = {
        'hash': r.hash,
        'main_script': r.main_script,
        'files:': r.filelist
    }
    ch.basic_publish(exchange='', routing_key='run_cpp', body=json.dumps(msg))

    # Done! Take this off the queue now.
    ch.basic_ack(delivery_tag=method.delivery_tag)


def listen_to_queue(rabbit_server):
    'Look for jobs to come off a queue and send them on'

    # Connect and setup the queues we will listen to and push once we've done.
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_server))
    channel = connection.channel()
    channel.queue_declare(queue='parse_cpp')
    channel.queue_declare(queue='run_cpp')

    channel.basic_consume(queue='parse_cpp', on_message_callback=process_message, auto_ack=False)

    # We are setup. Off we go. We'll never come back.
    channel.start_consuming()


if __name__ == '__main__':
    bad_args = len(sys.argv) != 2
    if bad_args:
        print ("Usage: python translate_ast_to_cpp_rabbit.py <rabbit-mq-node-address>")
    else:
        listen_to_queue(sys.argv[1])
