import json
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

channel.exchange_declare(exchange='inicio_leilao',
                         exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='inicio_leilao', queue=queue_name)





###########################################################################

dados_do_lance = {
    "id_leilao": "leilao_123",
    "id_usuario": "usuario_456",
    "valor_do_lance": 150.75,
    "assinatura_digital": "aBcD_1234_eFgH"
}
mensagem_json = json.dumps(dados_do_lance)
body_bytes = mensagem_json.encode('utf-8')

channel.queue_declare(queue='lance_realizado')

channel.basic_publish(exchange='', routing_key='lance_realizado',body=body_bytes)

###########################################################################

def callback(ch, method, properties, body):
    print(f"Mensagem recebida: {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=queue_name,
                      on_message_callback=callback)

channel.start_consuming()