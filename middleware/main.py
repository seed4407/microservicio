import pika, sys, os
import logging

logging.basicConfig(level=logging.INFO, encoding='utf-8')

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="172.18.0.6"))
    channel = connection.channel()

    channel.queue_declare(queue='publicidad')

    def callback(ch, method, properties, body):
        logging.info(body)
        ch.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue='publicidad', on_message_callback=callback, auto_ack=False)

    logging.info(' [*] Waiting for messages. To exit press CTRL+C')
    channel.start_consuming()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
