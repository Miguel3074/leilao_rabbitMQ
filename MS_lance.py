import json
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

channel.queue_declare(queue='lance_realizado')

def callback_lance(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    id_usuario = data.get('id_usuario')
    valor_do_lance = data.get('valor_do_lance')
    assinatura = data.get('assinatura_digital')

    print(f" [x] Novo lance recebido!")
    print(f"     ID do Leilão: {id_leilao}")
    print(f"     ID do Usuário: {id_usuario}")
    print(f"     Valor do Lance: {valor_do_lance}")
    print(f"     Assinatura: {assinatura}")

channel.basic_consume(queue='lance_realizado', on_message_callback=callback_lance, auto_ack=True)



#----------------------------------#

channel.queue_declare(queue='lance_validado')




#----------------------------------#

###########################################################################

channel.queue_declare(queue='leilao_iniciado')








###########################################################################

channel.queue_declare(queue='leilao_finalizado')





#----------------------------------#

channel.queue_declare(queue='leilao_vencedor')




#----------------------------------#
channel.start_consuming()