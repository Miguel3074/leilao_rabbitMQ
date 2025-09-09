import json
import pika
import threading
import base64 
import sys
from Crypto.PublicKey import RSA
from Crypto.Signature import pkcs1_15
from Crypto.Hash import SHA256
from Crypto.PublicKey import RSA

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host='localhost')
)
channel = connection.channel()


if len(sys.argv) > 1:
    CLIENTE_ID = sys.argv[1] # Pega o primeiro argumento (ex: "cliente_01")
else:
    print("ERRO: ID do cliente não fornecido na linha de comando.")
    print("Uso: python cliente.py <id_do_cliente>")
    sys.exit(1)
leiloes_interessados = set()
leiloes_conhecidos = {}

secret_code = "alemDosBits"
key = RSA.generate(2048)
private_key = key.export_key()
with open(f"private_{CLIENTE_ID}.bin", "wb") as f:
    f.write(private_key)

public_key = key.publickey().export_key()
with open(f"public_{CLIENTE_ID}.bin", "wb") as f:
    f.write(public_key)

###########################################################################
channel.exchange_declare(exchange='leiloes', exchange_type='fanout')
result = channel.queue_declare(queue='', exclusive=True)
queue_name = result.method.queue
channel.queue_bind(exchange='leiloes', queue=queue_name)

def callback_inicio_leilao(ch, method, properties, body):
    msg = body.decode('utf-8')
    data = json.loads(msg)
    id_leilao = data.get('id_leilao')
    descricao = data.get('descricao')
    leiloes_conhecidos[id_leilao] = descricao
    
    print(f"\n NOVO LEILÃO INICIADO!")
    print(f"   ID: {id_leilao}")
    print(f"   Descrição: {descricao}")
    print(f"   Data início: {data.get('data_inicio')}")
    print(f"   Data fim: {data.get('data_fim')}")
    print("-" * 50)

channel.basic_consume(queue=queue_name, on_message_callback=callback_inicio_leilao, auto_ack=True)

###########################################################################

msg = b'SistemasDistribuidos2025.2'
chave = RSA.import_key(open(f'private_{CLIENTE_ID}.bin').read())
aga = SHA256.new(msg)
assinatura = pkcs1_15.new(chave).sign(aga)

###########################################################################

def dar_lance(id_leilao, valor):
    if id_leilao not in leiloes_conhecidos:
        print(f"Erro: Leilão '{id_leilao}' não existe!")
        print(f"   Leilões disponíveis: {', '.join(leiloes_conhecidos.keys())}")
        return
    
    if id_leilao not in leiloes_interessados:
        leiloes_interessados.add(id_leilao)
        escutar_leilao(id_leilao)
        
    if valor <= 0:
        print(f"Erro: Valor do lance deve ser maior que zero!")
        return
    
    assinatura_base64 = base64.b64encode(assinatura).decode('utf-8')

    dados_do_lance = {
        "id_usuario": CLIENTE_ID,
        "id_leilao": id_leilao,
        "valor_do_lance": valor,
        "assinatura": assinatura_base64 
    }
    
    try:
        connection_envio = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost')
        )
        canal_envio = connection_envio.channel()

        canal_envio.queue_declare(queue='lance_realizado')
        mensagem_json = json.dumps(dados_do_lance)
        canal_envio.basic_publish(exchange='',routing_key='lance_realizado',body=mensagem_json.encode('utf-8')        )
        connection_envio.close()

        print(f" Lance de R${valor} enviado para o leilão {id_leilao} ({leiloes_conhecidos[id_leilao]})")
        print(f"   Aguardando validação do servidor...")

    except Exception as e:
        print(f" Erro ao enviar lance: {e}")

###########################################################################
channel.exchange_declare(exchange='leilao', exchange_type='topic')

def escutar_leilao(id_leilao):
    def callback_notificacao(ch, method, properties, body):
        msg = body.decode('utf-8')
        data = json.loads(msg)

        routing_key = method.routing_key
        
        if routing_key.endswith('.lance'):
            print(f"\nNOVO LANCE NO LEILÃO {id_leilao}!")
            print(f"   Usuário: {data.get('id_usuario')}")
            print(f"   Valor: R${data.get('valor_do_lance')}")
            print("-" * 30)
            
        if routing_key.endswith('.fim'):
            print(f"\n LEILÃO {id_leilao} FINALIZADO!")
            print(f"   Vencedor: {data.get('id_vencedor')}")
            print(f"   Valor final: R${data.get('valor_negociado')}")
            if data.get('id_vencedor') == CLIENTE_ID:
                print("    PARABÉNS! VOCÊ VENCEU!")
            print("=" * 50)

    def thread_listener():
        try:
            conn_local = pika.BlockingConnection(
                pika.ConnectionParameters('localhost')
            )
            ch_local = conn_local.channel()

            result = ch_local.queue_declare(queue='', exclusive=True)
            qname = result.method.queue
            
            ch_local.queue_bind(exchange='leilao', queue=qname, routing_key=f"{id_leilao}.lance")
            ch_local.queue_bind(exchange='leilao', queue=qname, routing_key=f"{id_leilao}.fim")
            
            ch_local.basic_consume(queue=qname, on_message_callback=callback_notificacao, auto_ack=True)
            print(f"Escutando eventos do leilão {id_leilao} via topic")
            
            ch_local.start_consuming()
        except Exception as e:
            print(f"Erro ao escutar leilão {id_leilao}: {e}")

    t = threading.Thread(target=thread_listener, daemon=True)
    t.start()

###########################################################################
def interface_usuario():
    print("\n" + "="*60)
    print(" SISTEMA DE LEILÕES - CLIENTE")
    print("="*60)
    print("Opções disponíveis:")
    print("  1 - Dar um lance")
    print("  2 - Ver leilões que está escutando")
    print("  3 - Ver todos os leilões ativos")
    print("  4 - Sair do sistema")
    print("="*60)
    
    while True:
        try:
            opcao = input("\nDigite uma opção (1-4): ").strip()
            
            if opcao == '1':
                id_leilao = input("Digite o ID do leilão: ").strip()
                valor_str = input("Digite o valor do lance: ").strip()
                try:
                    valor = float(valor_str)
                    dar_lance(id_leilao, valor)
                except ValueError:
                    print(" Valor deve ser um número!")
                    
            elif opcao == '2':
                if leiloes_interessados:
                    print(f"Leilões que você está escutando: {', '.join(leiloes_interessados)}")
                else:
                    print("Você não está escutando nenhum leilão ainda")
                    
            elif opcao == '3':
                print("LEILÕES ATIVOS:")
                print("-" * 40)
                for leilao_id, descricao in leiloes_conhecidos.items():
                    print(f"  {leilao_id}: {descricao} - ATIVO")
                print("-" * 40)
                    
            elif opcao == '4':
                print("Saindo do sistema...")
                break
                
            else:
                print("Opção inválida! Digite 1, 2, 3 ou 4.")
                
        except KeyboardInterrupt:
            print("\nSaindo do sistema...")
            break
        except Exception as e:
            print(f"Erro: {e}")

###########################################################################
thread_interface = threading.Thread(target=interface_usuario, daemon=True)
thread_interface.start()

print("Cliente iniciado - aguardando leilões...")
print("Use a interface numérica para interagir!")

try:
    channel.start_consuming()
except pika.exceptions.StreamLostError:
    print("Conexão com RabbitMQ perdida. Tentando reconectar...")
except KeyboardInterrupt:
    print("Cliente interrompido pelo usuário")
except Exception as e:
    print(f"Erro inesperado: {e}")
finally:
    try:
        connection.close()
    except:
        pass
