import json
import pika
import base64
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

leiloes_ativos = {}
ultimos_lances = {}

###########################################################################

channel.queue_declare(queue='lance_realizado')

channel.queue_declare(queue='lance_validado')


def callback_lance(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    id_usuario = data.get('id_usuario')
    valor_do_lance = data.get('valor_do_lance')
    assinatura_base64 = data.get('assinatura')

    if not all([id_leilao, id_usuario, valor_do_lance, assinatura_base64]):
        print(" [x] Mensagem de lance incompleta recebida.")
        return
    
    if id_leilao not in leiloes_ativos:
        print(f"Erro: Leilão '{id_leilao}' não existe ou já encerrou!")
        print(f"   Leilões disponíveis: {', '.join(leiloes_ativos.keys())}")
        return

    try:
        with open(f'public_{id_usuario}.bin', 'rb') as f:
            key = RSA.import_key(f.read())

        msg_original = b'SistemasDistribuidos2025.2'
        h = SHA256.new(msg_original)

        assinatura_bytes = base64.b64decode(assinatura_base64)

        pkcs1_15.new(key).verify(h, assinatura_bytes)
        
        print(f"Assinatura do usuário {id_usuario} VÁLIDA.")
        print(f" Lance de R${valor_do_lance} recebido para o leilão {id_leilao}")

    except (ValueError, TypeError):
        print(f"Assinatura do usuário {id_usuario} INVÁLIDA. Lance descartado.")
        return
    except FileNotFoundError:
        print(f"Chave pública 'public_{id_usuario}' não encontrada. Lance descartado.")
        return
    except Exception as e:
        print(f"Ocorreu um erro inesperado ao processar o lance: {e}")
        return

    ultimo_lance_valor = (ultimos_lances.get(id_leilao, {})).get('valor_do_lance', 0)

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
    ch.basic_ack(delivery_tag=method.delivery_tag)

    
channel.basic_consume(queue='lance_realizado', on_message_callback=callback_lance, auto_ack=False)


###########################################################################

channel.exchange_declare(exchange='leiloes', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
fila_inicio_leilao = result.method.queue
channel.queue_bind(exchange='leiloes', queue=fila_inicio_leilao)

def callback_inicio_leilao(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    descricao = data.get('descricao')
    leiloes_ativos[id_leilao] = descricao
    ch.basic_ack(delivery_tag=method.delivery_tag)


channel.basic_consume(queue=fila_inicio_leilao, on_message_callback=callback_inicio_leilao, auto_ack=False)

###########################################################################

channel.queue_declare(queue='leilao_finalizado')
channel.queue_declare(queue='leilao_vencedor')

def callback_leilao_finalizado(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    print(f"Leilão {id_leilao} finalizado.")

    if id_leilao in leiloes_ativos:
                del leiloes_ativos[id_leilao]

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
    
    body_vencedor = json.dumps(mensagem).encode('utf-8')
    channel.basic_publish(exchange='', routing_key='leilao_vencedor', body=body_vencedor)
    ch.basic_ack(delivery_tag=method.delivery_tag)
    

channel.basic_consume(queue='leilao_finalizado',auto_ack=False, on_message_callback=callback_leilao_finalizado)

###########################################################################

channel.start_consuming()