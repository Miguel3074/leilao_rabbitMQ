import json
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


ultimos_lances = {}
chaves_publicas = {
    'cliente_1': '123456',
    'cliente_1': '654321'
}

###########################################################################

channel.queue_declare(queue='lance_realizado')

def buscar_leilao(id_leilao):
    raise NotImplementedError

def callback_lance(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    id_usuario = data.get('id_usuario')
    valor_do_lance = data.get('valor_do_lance')
    assinatura = data.get('assinatura_digital')

###   SAO OS IF MALUCO LA Q A PROFESSORA QUER, NAO ESTAO FUNCIONANDO AINDA TODOS, N ENTENDI ESSA PSSWORD AI  ###

    if not all([id_leilao, id_usuario, valor_do_lance, assinatura]):
        return

    chave_publica = chaves_publicas.get(id_usuario)
    if not chave_publica or chave_publica != assinatura:
        return
    
    leilao_encontrado = buscar_leilao(id_leilao)
    if not leilao_encontrado or leilao_encontrado['status'] != 'ativo':
        return

    ultimo_lance_valor = ultimos_lances.get(id_leilao, 0)
    if valor_do_lance <= ultimo_lance_valor:
        return

    ultimos_lances[id_leilao] = valor_do_lance
    print(f"lance valido de R${valor_do_lance} para o leilao {id_leilao} aceito")

        
    
channel.basic_consume(queue='lance_realizado', on_message_callback=callback_lance, auto_ack=True)



#----------------------------------#

channel.queue_declare(queue='lance_validado')




#----------------------------------#

###########################################################################
channel.exchange_declare(exchange='inicio_leilao',
                         exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='inicio_leilao', queue=queue_name)


def callback(ch, method, properties, body):
    print(f"Mensagem recebida: {body.decode()}")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=queue_name,
                      on_message_callback=callback)





###########################################################################
channel.queue_declare(queue='leilao_finalizado')





#----------------------------------#

channel.queue_declare(queue='leilao_vencedor')




#----------------------------------#
channel.start_consuming()