import json
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

###########################################################################

def callback_lance_validado(ch, method, properties, body):

    print("Lance validado recebido")

    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    id_usuario = data.get('id_usuario')
    tipo = data.get('tipo')
    valor_do_lance = data.get('valor_do_lance')
    channel.queue_declare(queue=id_leilao)

    msg = {
        "id_leilao": id_leilao,
        "id_usuario": id_usuario,
        "valor_do_lance": valor_do_lance,
        "tipo": tipo
    }
    body_envio = json.dumps(msg).encode('utf-8')
    channel.basic_publish( exchange='leiloes', routing_key=f"{id_leilao}.lance", body=body_envio)


channel.queue_declare(queue='lance_validado')
channel.basic_consume(queue='lance_validado', on_message_callback=callback_lance_validado, auto_ack=True)



###########################################################################

channel.queue_declare(queue='leilao_vencedor')




###########################################################################

channel.start_consuming()

