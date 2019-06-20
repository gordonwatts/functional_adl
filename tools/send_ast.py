# Send an ast to a requested queue name on a rabbit server using the RPC call pattern
import sys
from write_ast import generate_ast
import pika
import os
import pickle
import uuid

done = False
corr_id = None

def on_response (ch, method, props, body):
    'We get the info back - print it out'
    global corr_id
    global done
    if corr_id == props.correlation_id:
        done = True
        print (body)

def send_ast_msg (ast_number:int, rabbit_address:str, queue_name:str, rabbit_user:str, rabbit_pass:str):
    a = generate_ast(ast_number)

    # Open connection to Rabbit, and declare the main queue we will be sending to.
    if rabbit_pass in os.environ:
        rabbit_pass = os.environ[rabbit_pass]
    credentials = pika.PlainCredentials(rabbit_user, rabbit_pass)
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbit_address, credentials=credentials))
    channel = connection.channel()
    channel.queue_declare(queue=queue_name)

    # Declare the call-back queue (an anonymous queue)
    result = channel.queue_declare(queue='', exclusive=True)
    callback_queue = result.method.queue

    channel.basic_consume(queue=callback_queue, on_message_callback=on_response, auto_ack=True)

    # Now, send the message
    global corr_id
    corr_id = str(uuid.uuid4())
    channel.basic_publish(exchange='',
        routing_key=queue_name,
        properties=pika.BasicProperties(
            reply_to=callback_queue,
            correlation_id=corr_id
        ),
        body=pickle.dumps(a)
    )

    # Wait for a response
    global done
    while not done:
        channel.connection.process_data_events()

    channel.close()

if __name__ == "__main__":
    bad_args = len(sys.argv) != 6
    bad_args = bad_args or not str.isdigit(sys.argv[1])

    if bad_args:
        print ('Usage: python send_ast.py <ast-number> <rabbit-ip-address> <queue-name> <rabbit-username> <rabbit-password>')
    else:
        send_ast_msg(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5])
