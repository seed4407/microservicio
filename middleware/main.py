import pika, sys, os
import logging

def main():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host="172.18.0.4"))
    channel = connection.channel()

    channel.queue_declare(queue='hello')

    def callback(ch, method, properties, body):
        logging.info("aaaaaaaaaaaaaaaaaa")

    channel.basic_consume(queue='hello', on_message_callback=callback, auto_ack=True)

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
