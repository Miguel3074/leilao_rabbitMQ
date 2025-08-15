import datetime
import json
import time
import pika

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost'))
channel = connection.channel()


leiloes = [
    {
        "id": "leilao_01",
        "descricao": "iphone",
        "data_inicio": datetime.datetime(2025, 8, 15, 14, 49),
        "data_fim": datetime.datetime(2025, 8, 15, 14, 50),
        "status": "pendente"
    },
    {
        "id": "leilao_02",
        "descricao": "pc gamer",
        "data_inicio": datetime.datetime(2025, 8, 15, 14, 50),
        "data_fim": datetime.datetime(2025, 8, 15, 14, 55),
        "status": "pendente"
    }
]

###########################################################################

channel.exchange_declare(exchange='inicio_leilao',
                         exchange_type='fanout')

channel.queue_declare(queue='leilao_finalizado')




while True:
    for leilao in leiloes:

        agora = datetime.datetime.now()

        if leilao['status'] == 'pendente' and agora >= leilao['data_inicio']:
            leilao['status'] = 'ativo'
            print(f"leilao {leilao['id']} iniciado")
            mensagem = {
                "id_leilao": leilao['id'],
                "descricao": leilao['descricao'],
                "data_inicio": leilao['data_inicio'].isoformat(),
                "data_fim": leilao['data_fim'].isoformat()
            }
            body = json.dumps(mensagem).encode('utf-8')

            channel.basic_publish(exchange='inicio_leilao', routing_key='', body=body)

        elif leilao['status'] == 'ativo' and agora >= leilao['data_fim']:
            leilao['status'] = 'encerrado'
            print(f"leilao {leilao['id']} finalizado")

            mensagem = {
                "id_leilao": leilao['id'],
                "data_fim": leilao['data_fim'].isoformat()
            }
            body = json.dumps(mensagem).encode('utf-8')
            channel.basic_publish(exchange='fim_leilao', routing_key='', body=body)

    time.sleep(1)

