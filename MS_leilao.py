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
        "data_inicio": datetime.datetime(2025, 8, 15, 11, 0),
        "data_fim": datetime.datetime(2025, 8, 15, 11, 30),
        "status": "pendente"
    },
    {
        "id": "leilao_02",
        "descricao": "pc gamer",
        "data_inicio": datetime.datetime(2025, 8, 15, 11, 20),
        "data_fim": datetime.datetime(2025, 8, 15, 12, 0),
        "status": "pendente"
    }
]

###########################################################################

channel.queue_declare(queue='leilao_iniciado')








###########################################################################

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

            channel.basic_publish(exchange='', routing_key='leilao_iniciado', body=body)

        elif leilao['status'] == 'ativo' and agora >= leilao['data_fim']:
            leilao['status'] = 'encerrado'
            print(f"leilao {leilao['id']} finalizado")

            mensagem = {
                "id_leilao": leilao['id'],
                "data_fim": leilao['data_fim'].isoformat()
            }
            body = json.dumps(mensagem).encode('utf-8')
            channel.basic_publish(exchange='', routing_key='leilao_finalizado', body=body)

    time.sleep(1)

