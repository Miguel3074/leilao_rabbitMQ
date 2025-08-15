import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

channel.queue_declare(queue='lance_validado')





###########################################################################

channel.queue_declare(queue='leilao_vencedor')




###########################################################################