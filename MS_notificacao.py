import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

channel.queue_declare(queue='lance_validado')

# se for validado tem que criar a queue do leilao?



###########################################################################

channel.queue_declare(queue='leilao_vencedor')




###########################################################################


