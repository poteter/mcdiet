import pika
import os
from dotenv import load_dotenv
from formatter.src.formatter.bk import bk_formatter
from formatter.src.formatter.mcd import mcd_formatter
load_dotenv('../environment/formatter.env')

def get_codes_from_queue(queue_name, rabbit_host, rabbit_port, rabbit_username, rabbit_password):
    codes = []
    credentials = pika.PlainCredentials(rabbit_username, rabbit_password)
    parameters = pika.ConnectionParameters(
        host=rabbit_host,
        port=rabbit_port,
        credentials=credentials
    )

    connection = pika.BlockingConnection(parameters)
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    while True:
        method_frame, header_frame, body = channel.basic_get(queue=queue_name, auto_ack=True)

        if method_frame:
            codes.append(body.decode('utf-8'))
        else:
            break

    connection.close()
    return codes # get_codes_from_queue

# sort list of codes from the queue into sub-lists of codes by their meta code
# mcd-500232
# bgk-4835-fsd4123-324f
def sort_codes(code_list, sort_code):
    result_list = []
    for code in code_list:
        if sort_code in code:
            result_list.append(code)
    return result_list # sort_codes

def run():
    # rabbitMQ Configuration
    rabbitmq_host = os.getenv('RABBITMQ_HOST', 'localhost')
    rabbitmq_port = int(os.getenv('RABBITMQ_PORT', 5672))
    rabbitmq_username = os.getenv('RABBITMQ_USERNAME', 'guest')
    rabbitmq_password = os.getenv('RABBITMQ_PASSWORD', 'guest')

    carry_code_queue = os.getenv('CODE_QUEUE_NAME')

    # sorts codes by meta code
    queue_codes = get_codes_from_queue(carry_code_queue, rabbitmq_host, rabbitmq_port, rabbitmq_username, rabbitmq_password)

    # calls the formatter modules
    bk_formatter.run(sort_codes(queue_codes, "bgk"))
    mcd_formatter.run(sort_codes(queue_codes, "mcd"))

if __name__ == '__main__':
    run()