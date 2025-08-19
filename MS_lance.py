import json
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


ultimos_lances = {}
chaves_publicas = {
    'cliente_1': '123456',
    'cliente_2': '654321'
}

###########################################################################

channel.queue_declare(queue='lance_realizado')

channel.queue_declare(queue='lance_validado')


def buscar_leilao(id_leilao):
    for leilao in leiloes_ativos: # nao implementado
        if leilao['id'] == id_leilao:
            return leilao
    return None

def callback_lance(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    id_usuario = data.get('id_usuario')
    valor_do_lance = data.get('valor_do_lance')
    assinatura = data.get('assinatura_digital')

    if not all([id_leilao, id_usuario, valor_do_lance, assinatura]):
        return

    #chave_publica = chaves_publicas.get(id_usuario)
    #if not chave_publica or chave_publica != assinatura:
    #    return
    
    #leilao_encontrado = buscar_leilao(id_leilao)
    #if not leilao_encontrado or leilao_encontrado['status'] != 'ativo':
    #    return

    ultimo_lance_valor = (ultimos_lances.get(id_leilao, {})).get('valor', 0)

    if valor_do_lance <= ultimo_lance_valor:
        print(f"Lance de R${valor_do_lance} para o leilão {id_leilao} recusado (menor ou igual ao melhor lance).")
        return

    ultimos_lances[id_leilao] = {
        'valor_do_lance': valor_do_lance,
        'id_usuario': id_usuario
    }

    print(f"lance valido de R${valor_do_lance} para o leilao {id_leilao} aceito")
    mensagem = {
        "id_leilao": id_leilao,
        "id_usuario": id_usuario,
        "valor_do_lance": valor_do_lance
    }

    body_e = json.dumps(mensagem).encode('utf-8')

    channel.basic_publish(exchange='', routing_key='lance_validado', body=body_e)

    
channel.basic_consume(queue='lance_realizado', on_message_callback=callback_lance, auto_ack=True)


###########################################################################

channel.exchange_declare(exchange='leiloes', exchange_type='topic')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='leiloes', queue=queue_name, routing_key='*.inicio')

def callback_inicio_leilao(ch, method, properties, body):
    print(f"Mensagem recebida: {body.decode()}")


channel.basic_consume(queue=queue_name, on_message_callback=callback_inicio_leilao, auto_ack=True)

###########################################################################

channel.queue_declare(queue='leilao_vencedor')

def callback_leilao_finalizado(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')

    if not id_leilao:
        return
    
    if id_leilao not in ultimos_lances:
        print(f"Leilão {id_leilao} não possui lances válidos.")
        mensagem = {
            "id_leilao": id_leilao,
            "id_usuario":  "ninguem",
            "valor_do_lance": 0.00,
        }
    else:
        mensagem = {
            "id_leilao": id_leilao,
            "id_usuario": ultimos_lances[id_leilao]['id_usuario'],
            "valor_do_lance": ultimos_lances[id_leilao]['valor_do_lance']
        }
    
    print(f"Leilão {id_leilao} finalizado.")
    body_vencedor = json.dumps(mensagem).encode('utf-8')
    channel.basic_publish(exchange='', routing_key='leilao_vencedor', body=body_vencedor)  
    
channel.basic_consume(queue='leilao_finalizado', on_message_callback=callback_leilao_finalizado, auto_ack=True)

###########################################################################

channel.start_consuming()