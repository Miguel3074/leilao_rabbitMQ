import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

channel.queue_declare(queue='leilao_iniciado')








###########################################################################

channel.queue_declare(queue='leilao_finalizado')