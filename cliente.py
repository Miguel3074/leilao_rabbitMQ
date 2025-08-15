import json
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

channel.queue_declare(queue='leilao_iniciado')

def callback(ch, method, properties, body):
    print(f" [x] Recebido: {body}")

channel.basic_consume(queue='leilao_iniciado',
                      on_message_callback=callback,
                      auto_ack=True)

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
channel.start_consuming()