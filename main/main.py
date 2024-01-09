from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Event

continuar_verificacao = True
evento_parar = Event()
entrou_modo_tela_cheia = False

# Função para clicar em "Agora não" e sinalizar para parar a verificação
def verificar_agora_nao(driver):
    global continuar_verificacao
    try:
        botao_agora_nao = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.XPATH, '//*[contains(text(),"agora não")]'))
        )
        botao_agora_nao.click()
        print("Clicou em 'Agora não'.")
        evento_parar.set()  # Sinaliza para parar a verificação após clicar
    except:
        print("Nenhum botão 'Agora não' encontrado ou não foi possível clicar.")

# Função para tentar pular o anúncio de forma assíncrona
def tentar_pular_anuncio_async(driver):
    global continuar_verificacao
    try:
        botao_pular = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ytp-ad-skip-button-container'))
        )
        if 'pular' in botao_pular.text.lower():
            botao_pular.click()
            print("Anúncio pulado com sucesso.")
            evento_parar.set()  # Sinaliza para parar a verificação após clicar
            return True
    except:
        print("Nenhum botão 'Pular' encontrado ou o anúncio já foi pulado.")
        return False

def entrar_modo_cheio_apenas_quando_pular(driver):
    global continuar_verificacao, entrou_modo_tela_cheia
    try:
        botao_pular = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ytp-ad-skip-button-container'))
        )
        if 'pular' in botao_pular.text.lower():
            botao_pular.click()
            print("Botão 'Pular' pressionado.")
            if not entrou_modo_tela_cheia:
                entrou_modo_tela_cheia = True
                botao_modo_cheio = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '.ytp-fullscreen-button'))
                )
                botao_modo_cheio.click()
                print("Entrando em modo de tela cheia.")
                time.sleep(99999)  # Adiciona um atraso após entrar em modo de tela cheia
            evento_parar.set()  # Sinaliza para parar a verificação após entrar pela primeira vez
    except:
        print("Nenhum botão 'Pular' encontrado ou erro ao entrar em modo de tela cheia.")

# Função para despausar o vídeo
def despausar_video(driver):
    try:
        botao_play = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ytp-play-button'))
        )
        botao_play.click()
        print("Vídeo despausado com sucesso.")
    except:
        print("Nenhum botão 'Play' encontrado ou o vídeo já está sendo reproduzido.")

# Função para avançar para o próximo vídeo
def avancar_proximo_video(driver):
    try:
        botao_proximo = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '.ytp-next-button'))
        )
        botao_proximo.click()
        print("Avançando para o próximo vídeo.")
    except:
        print("Nenhum botão 'Próximo' encontrado ou não foi possível avançar para o próximo vídeo.")

# Função para verificar se o vídeo está em modo de tela cheia
def verificar_tela_cheia(driver):
    try:
        return driver.execute_script("return document.fullscreenElement !== null;")
    except:
        return False

# Função para obter o tempo atual de reprodução do vídeo
def obter_tempo_atual_reproducao(driver, video_element):
    try:
        tempo_atual = driver.execute_script("return arguments[0].currentTime;", video_element)
        return tempo_atual
    except Exception as e:
        print(f"Erro ao obter tempo de reprodução: {str(e)}")
        return None

# ...

# Função principal de automação
def realizar_automacao(frase):
    driver = webdriver.Chrome()

    try:
        driver.get('https://www.google.com')
        search_box = driver.find_element(By.NAME, 'q')
        search_box.send_keys(frase)
        search_box.send_keys(Keys.RETURN)

        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#search')))

        youtube_link = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.PARTIAL_LINK_TEXT, 'YouTube'))
        )
        youtube_link.click()

        WebDriverWait(driver, 3).until(EC.presence_of_element_located((By.CSS_SELECTOR, '#video-title')))

        first_result = WebDriverWait(driver, 7).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '#video-title'))
        )
        first_result.click()

        video_element = None  # Inicializa a variável fora do bloco while

        # Adiciona contadores
        contador_pular = 0
        contador_agora_nao = 0
        contador_modo_tela_cheia = 0

        with ThreadPoolExecutor(max_workers=3) as executor:
            # Primeiro loop - antes do modo de tela cheia
            while not evento_parar.is_set():
                executor.submit(verificar_agora_nao, driver)
                executor.submit(tentar_pular_anuncio_async, driver)

                time.sleep(5)

                time.sleep(3)

                video_element = driver.find_element(By.CSS_SELECTOR, 'video')
                video_element.click()

                tempo_maximo_espera = 30
                tempo_inicio = time.time()

                while time.time() - tempo_inicio < tempo_maximo_espera:
                    despausar_video(driver)
                    entrar_modo_cheio_apenas_quando_pular(driver)
                    tempo_atual = obter_tempo_atual_reproducao(driver, video_element)

                    if tempo_atual is not None and tempo_atual >= tempo_maximo_espera or evento_parar.is_set():
                        break

                    if tentar_pular_anuncio_async(driver) and evento_parar.is_set():
                        print("Anúncio pulado com sucesso. Interrompendo a verificação.")
                        break
                    time.sleep(1)  # Aguarda um segundo entre as iterações para evitar loop muito rápido

                    # Adiciona contagem para o botão "Pular"
                    if tentar_pular_anuncio_async(driver):
                        contador_pular += 1
                        if contador_pular >= 3:  # Limite de verificação do botão "Pular"
                            print("Limite de verificação do botão 'Pular' atingido. Interrompendo a verificação.")
                            evento_parar.set()
                            break

                    # Adiciona contagem para o botão "Agora não"
                    if verificar_agora_nao(driver):
                        contador_agora_nao += 1
                        if contador_agora_nao >= 3:  # Limite de verificação do botão "Agora não"
                            print("Limite de verificação do botão 'Agora não' atingido. Interrompendo a verificação.")
                            evento_parar.set()
                            break

            # Segundo loop - aguardando o término do vídeo em modo de tela cheia
            while verificar_tela_cheia(driver) and not evento_parar.is_set():
                tempo_atual = obter_tempo_atual_reproducao(driver, video_element)

                if tempo_atual is not None and tempo_atual >= tempo_maximo_espera or evento_parar.is_set():
                    break

                time.sleep(1)

                # Adiciona contagem para o modo de tela cheia
                contador_modo_tela_cheia += 1
                if contador_modo_tela_cheia >= 10:  # Limite de verificação do modo tela cheia
                    print("Limite de verificação do modo de tela cheia atingido. Interrompendo a verificação.")
                    evento_parar.set()
                    break

    except Exception as e:
        print(f"Ocorreu um erro: {str(e)}")
    finally:
        try:
            if not evento_parar.is_set():
                evento_parar.set()  # Certifica-se de que o evento de parar seja definido antes de fechar o driver
            driver.quit()
        except Exception as e:
            print(f"Erro ao fechar o navegador: {str(e)}")

# Exemplo de uso
frase_a_pesquisar = input("Digite a frase a ser pesquisada: ")
realizar_automacao(frase_a_pesquisar)
