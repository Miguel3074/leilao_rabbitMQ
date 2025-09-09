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
        "data_inicio": datetime.datetime.now() + datetime.timedelta(seconds=4),
        "data_fim": datetime.datetime.now() + datetime.timedelta(seconds=60),
        "status": "pendente"
    },
    {
        "id": "leilao_02",
        "descricao": "pc gamer",
        "data_inicio": datetime.datetime.now() + datetime.timedelta(seconds=10),
        "data_fim": datetime.datetime.now() + datetime.timedelta(seconds=70),
        "status": "pendente"
    }
]

###########################################################################


channel.queue_declare(queue='leilao_iniciado')
channel.exchange_declare(exchange='leiloes', exchange_type='fanout')
channel.queue_declare(queue='leilao_finalizado')

print("MS Leilão iniciado - monitorando leilões...")
print(f"Leilões configurados:")
for leilao in leiloes:
    print(f"  {leilao['id']}: {leilao['descricao']} - Início: {leilao['data_inicio']} - Fim: {leilao['data_fim']}")

while True:
    for leilao in leiloes:
        agora = datetime.datetime.now()

        if leilao['status'] == 'pendente' and agora >= leilao['data_inicio'] and not agora >= leilao['data_fim']:
            leilao['status'] = 'ativo'
            print(f"Leilão {leilao['id']} iniciado")
            
            mensagem = {
                "id_leilao": leilao['id'],
                "descricao": leilao['descricao'],
                "data_inicio": leilao['data_inicio'].isoformat(),
                "data_fim": leilao['data_fim'].isoformat()
            }
            body = json.dumps(mensagem).encode('utf-8')
            channel.basic_publish(exchange='leiloes', routing_key='', body=body)

        elif leilao['status'] == 'ativo' and agora >= leilao['data_fim']: 
            leilao['status'] = 'encerrado'
            print(f"Leilão {leilao['id']} finalizado")

            mensagem = {
                "id_leilao": leilao['id'],
            }
            body = json.dumps(mensagem).encode('utf-8')
            
            channel.basic_publish(exchange='', routing_key='leilao_finalizado', body=body)
            time.sleep(1)

    time.sleep(1)