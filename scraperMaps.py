from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException, StaleElementReferenceException
import time
import csv
import re
import os
import random

class GoogleMapsSeleniumScraper:
    def __init__(self, headless=False):
        """
        Inicializa o scraper com o Selenium.
        
        Args:
            headless (bool): Se True, o navegador rodará em modo "headless" (sem interface gráfica).
        """
        # Configurar opções do Chrome
        chrome_options = Options()
        if headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--disable-notifications")
        chrome_options.add_argument("--disable-infobars")
        chrome_options.add_argument("--start-maximized")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--no-sandbox")
        
        # Adicionar user-agent para parecer mais humano
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36")
        
        # Desativar detecção de automação
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        print("Inicializando o navegador Chrome...")
        
        try:
            # Tentar encontrar o driver do Chrome (chromedriver)
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                print("Chrome inicializado com sucesso!")
            except Exception as e:
                print(f"Erro ao iniciar o Chrome: {str(e)}")
                print("Tentando encontrar o chromedriver no PATH...")
                
                # Tente especificar o caminho para o chromedriver
                service = Service('./chromedriver')  # Ajuste o caminho conforme necessário
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                print("Chrome inicializado com serviço personalizado!")
                
        except Exception as e:
            print(f"Erro ao inicializar o Chrome: {str(e)}")
            print("\nVocê precisa ter o Chrome e o chromedriver instalados.")
            print("Baixe o chromedriver em: https://chromedriver.chromium.org/downloads")
            print("Certifique-se de baixar a versão compatível com seu Chrome.")
            print("Coloque o chromedriver no mesmo diretório deste script ou adicione-o ao PATH.")
            raise e
        
        # Definir tempos de espera
        self.driver.implicitly_wait(10)
        self.wait = WebDriverWait(self.driver, 30)
    
    def search_businesses(self, query, region, max_results=0):
        """
        Pesquisa empresas no Google Maps com base na consulta e região.
        
        Args:
            query (str): O tipo de negócio a ser pesquisado (ex: 'autoescola')
            region (str): A região para buscar (ex: 'São Paulo, SP')
            max_results (int): Número máximo de resultados a coletar (0 ou negativo = sem limite)
            
        Returns:
            list: Uma lista de dicionários com os dados das empresas
        """
        results = []
        search_term = f"{query} {region}"
        
        print(f"Buscando por: {search_term}")
        
        try:
            # Acessar o Google Maps
            self.driver.get("https://www.google.com/maps")
            
            # Aceitar cookies se aparecer (múltiplas tentativas com diferentes seletores)
            self._accept_cookies()
            
            # Localizar a caixa de pesquisa e inserir o termo de busca
            search_box = self.wait.until(EC.presence_of_element_located(
                (By.ID, "searchboxinput")
            ))
            search_box.clear()
            search_box.send_keys(search_term)
            search_box.send_keys(Keys.ENTER)
            
            print("Pesquisa realizada, aguardando resultados...")
            
            # Aguardar o carregamento dos resultados
            time.sleep(5)
            
            # Verificar se existem resultados
            try:
                # Esperar pelo contêiner de resultados (tentando vários seletores possíveis)
                result_selector = self._wait_for_first_element_present([
                    (By.CSS_SELECTOR, "div.Nv2PK"),
                    (By.CSS_SELECTOR, "div.bfdHYd"),
                    (By.CSS_SELECTOR, "div[role='feed'] > div")
                ], timeout=10)
                
                if not result_selector:
                    print("Não foi possível identificar o seletor dos resultados.")
                    return results
                
                print(f"Resultados encontrados com seletor: {result_selector}")
            except TimeoutException:
                print("Não foram encontrados resultados para esta busca.")
                return results
            
            # Definir a quantidade de rolagens
            # Se max_results <= 0 (ou seja, sem limite), podemos rolar várias vezes por padrão (ex.: 10).
            # Se max_results > 0, estimamos ~5 resultados por rolagem.
            if max_results > 0:
                scroll_count = max(1, max_results // 5)
            else:
                scroll_count = 10  # Rolagem fixa para tentar coletar vários resultados
            
            # Rolar para baixo para carregar mais resultados
            self._scroll_results(scroll_count)
            
            # Coletar todos os resultados de negócios usando o seletor identificado
            business_elements = self.driver.find_elements(By.CSS_SELECTOR, result_selector)
            print(f"Encontrados {len(business_elements)} resultados.")
            
            # Se max_results > 0, limitar o número de resultados para processamento
            if max_results > 0:
                business_elements = business_elements[:max_results]
            
            # Para cada resultado, extrair informações básicas e detalhes
            for index, element in enumerate(business_elements):
                try:
                    # Criar um dicionário para armazenar informações do negócio
                    business = {}
                    
                    # Tentar obter o nome do negócio usando diferentes seletores
                    name_element = self._find_element_with_multiple_selectors(element, [
                        (By.CSS_SELECTOR, "div.qBF1Pd"),       # Seletor antigo
                        (By.CSS_SELECTOR, "span.fontHeadlineSmall"),
                        (By.CSS_SELECTOR, "div.fontHeadlineSmall"),
                        (By.CSS_SELECTOR, "span.vcAjh"),
                        (By.CSS_SELECTOR, "h3")
                    ])
                    
                    if name_element:
                        business['name'] = name_element.text.strip()
                        print(f"Processando negócio {index+1}/{len(business_elements)}: {business['name']}")
                        
                        # Tentar obter URL para a página de detalhes (isso pode mudar no futuro)
                        try:
                            # Tentar encontrar o elemento clicável que vai para os detalhes
                            clickable_element = self._find_element_with_multiple_selectors(element, [
                                (By.CSS_SELECTOR, "a"),                # Qualquer link dentro do elemento
                                (By.CSS_SELECTOR, "div[role='button']"),
                                (By.CSS_SELECTOR, "div[jsaction*='placeCard']"),
                                (By.CSS_SELECTOR, "div[jsaction*='click']")
                            ])
                            
                            if clickable_element:
                                # Tentar clicar com diferentes abordagens
                                clicked = self._try_click_element(clickable_element)
                                
                                if clicked:
                                    # Aguardar carregamento dos detalhes
                                    time.sleep(random.uniform(3, 5))
                                    
                                    # Extrair detalhes da página de detalhes
                                    business_details = self._extract_business_details()
                                    business.update(business_details)
                                    
                                    # Verificar se conseguimos informações além do nome
                                    if len(business) > 1:
                                        print(f"✓ Detalhes obtidos para: {business['name']}")
                                    else:
                                        print(f"⚠ Apenas o nome foi obtido para: {business['name']}")
                                    
                                    # Voltar para a lista de resultados usando diferentes seletores
                                    self._go_back_to_results()
                                    
                                    # Aguardar carregamento da lista novamente
                                    time.sleep(random.uniform(2, 3))
                                    
                                    # Atualizar a lista de elementos se necessário (para evitar StaleElementReferenceException)
                                    if index < len(business_elements) - 1:
                                        try:
                                            # Reobter os elementos se eles estiverem obsoletos
                                            business_elements = self.driver.find_elements(By.CSS_SELECTOR, result_selector)
                                        except Exception as e:
                                            print(f"Erro ao reatualizar lista de resultados: {str(e)}")
                                else:
                                    print(f"⚠ Não foi possível clicar no elemento para: {business['name']}")
                            else:
                                print(f"⚠ Não foi encontrado elemento clicável para: {business['name']}")
                                
                        except Exception as e:
                            print(f"Erro ao obter detalhes para {business['name']}: {str(e)}")
                    else:
                        print(f"⚠ Não foi possível obter o nome para o resultado {index+1}")
                        continue
                    
                    # Adicionar negócio à lista de resultados
                    results.append(business)
                    
                except StaleElementReferenceException:
                    print("Elemento ficou obsoleto, tentando recarregar os resultados...")
                    # Recarregar os elementos
                    business_elements = self.driver.find_elements(By.CSS_SELECTOR, result_selector)
                    # Pular este elemento
                    continue
                except Exception as e:
                    print(f"Erro ao processar resultado {index+1}: {str(e)}")
                    
                # Pausa entre negócios para evitar detecção
                time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            print(f"Erro durante a pesquisa: {str(e)}")
        
        return results
    
    def _accept_cookies(self):
        """
        Tenta aceitar cookies usando vários seletores possíveis
        """
        try:
            cookie_selectors = [
                "//button[contains(., 'Aceitar')]",
                "//button[contains(., 'Concordo')]",
                "//button[contains(., 'Accept')]",
                "//button[contains(., 'I agree')]",
                "//button[@jsname='higCR']"
            ]
            
            for selector in cookie_selectors:
                try:
                    cookie_button = self.driver.find_element(By.XPATH, selector)
                    cookie_button.click()
                    print("Cookies aceitos.")
                    time.sleep(1)
                    return True
                except NoSuchElementException:
                    continue
                    
        except Exception as e:
            print(f"Não foi necessário aceitar cookies ou ocorreu erro: {str(e)}")
            
        return False
        
    def _wait_for_first_element_present(self, selector_list, timeout=10):
        """
        Aguarda pelo primeiro seletor que encontrar um elemento presente
        
        Args:
            selector_list: Lista de tuplas (BY, seletor)
            timeout: Tempo máximo de espera em segundos
            
        Returns:
            str: O seletor CSS que funcionou ou None
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            for by, selector in selector_list:
                try:
                    if self.driver.find_elements(by, selector):
                        return selector
                except:
                    pass
            time.sleep(0.5)
        return None
        
    def _find_element_with_multiple_selectors(self, parent_element, selector_list):
        """
        Tenta encontrar um elemento usando múltiplos seletores
        
        Args:
            parent_element: Elemento pai para buscar dentro
            selector_list: Lista de tuplas (BY, seletor)
            
        Returns:
            WebElement ou None
        """
        for by, selector in selector_list:
            try:
                element = parent_element.find_element(by, selector)
                return element
            except NoSuchElementException:
                continue
            except Exception:
                continue
        return None
        
    def _try_click_element(self, element):
        """
        Tenta clicar em um elemento usando diferentes métodos
        
        Args:
            element: Elemento para clicar
            
        Returns:
            bool: True se conseguiu clicar, False caso contrário
        """
        methods = [
            # Método 1: Clique normal
            lambda: element.click(),
            # Método 2: Clique via JavaScript
            lambda: self.driver.execute_script("arguments[0].click();", element),
            # Método 3: Ações
            lambda: webdriver.ActionChains(self.driver).move_to_element(element).click().perform(),
            # Método 4: Clique com JS após scroll
            lambda: self.driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", element)
        ]
        
        for method in methods:
            try:
                method()
                return True
            except (ElementClickInterceptedException, StaleElementReferenceException):
                # Se o elemento estiver interceptado ou obsoleto, tente o próximo método
                continue
            except Exception as e:
                print(f"Erro ao tentar clicar: {str(e)}")
                continue
                
        return False
        
    def _scroll_results(self, scroll_count):
        """
        Rola a lista de resultados para carregar mais itens
        
        Args:
            scroll_count: Número de vezes para rolar
        """
        print(f"Rolando para carregar mais resultados ({scroll_count} rolagens)...")
        
        # Tentar diferentes seletores para o elemento rolável
        scrollable_selectors = [
            "div[role='feed']",
            "div.m6QErb[role='region']",
            "div.m6QErb",
            "div.section-layout",
            "div.section-scrollbox"
        ]
        
        for i in range(scroll_count):
            try:
                # Tentar encontrar o elemento rolável
                scrollable_div = None
                for selector in scrollable_selectors:
                    try:
                        scrollable_div = self.driver.find_element(By.CSS_SELECTOR, selector)
                        break
                    except NoSuchElementException:
                        continue
                
                if scrollable_div:
                    print(f"Fazendo rolagem {i+1}/{scroll_count}...")
                    # Tentar diferentes métodos de rolagem
                    try:
                        # Método 1: scrollTop
                        self.driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", scrollable_div)
                    except:
                        try:
                            # Método 2: scrollBy
                            self.driver.execute_script("arguments[0].scrollBy(0, 300)", scrollable_div)
                        except:
                            # Método 3: página inteira
                            self.driver.execute_script("window.scrollBy(0, 300)")
                else:
                    # Se não encontrou elemento rolável, role a página
                    self.driver.execute_script("window.scrollBy(0, 300)")
                    
                # Pausa para carregar novos resultados
                time.sleep(random.uniform(2, 3))
            except Exception as e:
                print(f"Erro durante rolagem: {str(e)}")
                
    def _go_back_to_results(self):
        """
        Volta para a lista de resultados a partir da página de detalhes
        """
        # Tentar diferentes métodos para voltar
        methods = [
            # Método 1: Botão de voltar específico
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button[jsaction='pane.topappbar.back']").click(),
            # Método 2: Botão com ícone de voltar
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Voltar']").click(),
            # Método 3: Botão com ícone de voltar (outra variação)
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button[aria-label='Back']").click(),
            # Método 4: Qualquer botão com ícone de seta
            lambda: self.driver.find_element(By.CSS_SELECTOR, "button.gsqi").click(),
            # Método 5: Voltar do navegador
            lambda: self.driver.execute_script("window.history.go(-1)")
        ]
        
        for method in methods:
            try:
                method()
                # Esperar a lista de resultados reaparecer
                time.sleep(1)
                return True
            except Exception:
                continue
                
        print("⚠ Não foi possível voltar para a lista de resultados. Tentando nova pesquisa...")
        # Se falhar todas as tentativas, tente recarregar a página
        try:
            self.driver.refresh()
            time.sleep(3)
        except:
            pass
            
        return False
    
    def _extract_business_details(self):
        """
        Extrai detalhes do negócio da página de detalhes aberta (sem horários/avaliações/ratings).
        
        Returns:
            dict: Um dicionário com os detalhes do negócio
        """
        details = {}
        
        try:
            # Esperar pelo carregamento completo
            time.sleep(2)
            
            # Coletar todos os textos dos botões e links para análise
            all_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button, a")
            all_button_texts = {button.text.strip(): button for button in all_buttons if button.text.strip()}
            
            # Imprimir alguns botões encontrados para depuração
            print(f"Botões encontrados: {min(5, len(all_button_texts))} de {len(all_button_texts)}")
            
            # Seletores para endereço
            address_selectors = [
                # Método 1: Botão específico com atributos
                (By.CSS_SELECTOR, "button[data-item-id^='address'], [data-tooltip='Copiar endereço']"),
                # Método 2: Botão com texto de endereço
                (By.XPATH, "//button[contains(@aria-label, 'ndereço')]"),
                # Método 3: Qualquer elemento com aria-label de endereço
                (By.CSS_SELECTOR, "[aria-label*='endereço']"),
                # Método 4: Links com \"maps\" na URL que podem conter o endereço
                (By.CSS_SELECTOR, "a[href*='maps']"),
                # Método 5: Botão com texto que parece um endereço (rua, avenida, etc)
                (By.XPATH, "//button[contains(text(), 'Rua') or contains(text(), 'Av') or contains(text(), 'Avenida')]")
            ]
            
            # Tentar extrair endereço
            address_element = self._find_first_matching_element(address_selectors)
            if address_element:
                details['address'] = address_element.text.strip()
                print(f"Endereço encontrado: {details['address'][:30]}...")
            
            # Seletores para telefone
            phone_selectors = [
                # Método 1: Botão específico
                (By.CSS_SELECTOR, "button[data-item-id^='phone'], [data-tooltip='Copiar número de telefone']"),
                # Método 2: Botão com label de telefone
                (By.XPATH, "//button[contains(@aria-label, 'elefone')]"),
                # Método 3: Qualquer elemento com texto que parece telefone
                (By.XPATH, "//button[contains(text(), '(') and contains(text(), ')')]"),
                # Método 4: Links com \"tel:\" na URL
                (By.CSS_SELECTOR, "a[href^='tel:']")
            ]
            
            # Tentar extrair telefone
            phone_element = self._find_first_matching_element(phone_selectors)
            if phone_element:
                # Se for um link de telefone, extrair da URL
                if phone_element.tag_name == 'a' and phone_element.get_attribute('href'):
                    href = phone_element.get_attribute('href')
                    if 'tel:' in href:
                        details['phone'] = href.split('tel:')[1]
                else:
                    details['phone'] = phone_element.text.strip()
                print(f"Telefone encontrado: {details.get('phone')}")
            
            # Seletores para website
            website_selectors = [
                # Método 1: Link específico
                (By.CSS_SELECTOR, "a[data-item-id^='authority'], [data-tooltip='Abrir website']"),
                # Método 2: Link com label de site
                (By.XPATH, "//a[contains(@aria-label, 'site')]"),
                # Método 3: Link com texto 'website' ou 'site'
                (By.XPATH, "//a[contains(text(), 'site') or contains(text(), 'Site') or contains(text(), 'Website')]"),
                # Método 4: Qualquer link externo (não do Google)
                (By.CSS_SELECTOR, "a:not([href*='google'])")
            ]
            
            # Tentar extrair website
            website_element = self._find_first_matching_element(website_selectors)
            if website_element and website_element.get_attribute('href'):
                href = website_element.get_attribute('href')
                # Verificar se é um link externo válido
                if ('http' in href and 'google' not in href):
                    details['website'] = href
                    print(f"Website encontrado: {details['website']}")
            
            # Extrair categoria
            try:
                category_selectors = [
                    (By.CSS_SELECTOR, "button[jsaction*='category']"),
                    (By.XPATH, "//button[contains(@jsaction, 'category')]"),
                    (By.CSS_SELECTOR, "span.DkEaL, span.mgr77e")
                ]
                
                category_element = self._find_first_matching_element(category_selectors)
                if category_element:
                    details['category'] = category_element.text.strip()
                    print(f"Categoria encontrada: {details['category']}")
            except Exception as e:
                print(f"Erro ao extrair categoria: {str(e)}")
            
            # Tentar encontrar email no texto da página
            try:
                # Procurar links de email
                email_selectors = [
                    (By.CSS_SELECTOR, "a[href^='mailto:']"),
                    (By.XPATH, "//a[contains(@href, 'mailto:')]")
                ]
                
                email_element = self._find_first_matching_element(email_selectors)
                if email_element and email_element.get_attribute('href'):
                    email = email_element.get_attribute('href').replace('mailto:', '')
                    details['email'] = email
                    print(f"Email encontrado (link): {email}")
                else:
                    # Se não encontrou link direto, buscar padrão de email no conteúdo da página
                    page_source = self.driver.page_source
                    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                    email_matches = re.findall(email_pattern, page_source)
                    
                    if email_matches:
                        # Filtrar emails que parecem ser do Google
                        valid_emails = [e for e in email_matches
                                        if not ('google' in e.lower() or 'gstatic' in e.lower())]
                        if valid_emails:
                            details['email'] = valid_emails[0]
                            print(f"Email encontrado (texto): {details['email']}")
            except Exception as e:
                print(f"Erro ao extrair email: {str(e)}")
            
        except Exception as e:
            print(f"Erro geral ao extrair detalhes: {str(e)}")
        
        return details
    
    def _find_first_matching_element(self, selector_list):
        """
        Encontra o primeiro elemento que corresponde a um dos seletores na lista
        
        Args:
            selector_list: Lista de tuplas (By, seletor)
            
        Returns:
            WebElement ou None
        """
        for by, selector in selector_list:
            try:
                elements = self.driver.find_elements(by, selector)
                if elements:
                    return elements[0]
            except Exception:
                continue
        return None
    
    def export_to_csv(self, businesses, filename='empresas.csv'):
        """
        Exporta os resultados para um arquivo CSV
        
        Args:
            businesses (list): Lista de dicionários com os dados das empresas
            filename (str): Nome do arquivo CSV a ser criado
            
        Returns:
            bool: True se a exportação foi bem-sucedida, False caso contrário
        """
        if not businesses:
            print("Nenhum dado para exportar.")
            return False
        
        try:
            # Coletar todas as chaves que aparecem nos dicionários
            all_keys = set()
            for biz in businesses:
                all_keys.update(biz.keys())
            
            fieldnames = list(all_keys)
            
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                
                for biz in businesses:
                    writer.writerow(biz)
            
            print(f"Dados exportados para '{filename}' com sucesso!")
            return True
        except Exception as e:
            print(f"Erro ao exportar para CSV: {str(e)}")
            return False

    def close(self):
        """
        Encerra o WebDriver e fecha o navegador.
        """
        if self.driver:
            self.driver.quit()
            print("Navegador fechado.")


if __name__ == "__main__":
    niche = input("Informe o nicho (categoria) de negócios a pesquisar: ")
    region = input("Informe a região: ")

    # Pergunta ao usuário quantas empresas deseja coletar.
    # Se o usuário digitar 0, consideramos ilimitado.
    try:
        qtd_str = input("Quantas empresas deseja coletar? (0 = sem limite): ")
        max_results = int(qtd_str)
    except ValueError:
        max_results = 0  # Se o usuário não digitar um número, consideramos sem limite.

    scraper = GoogleMapsSeleniumScraper(headless=False)
    try:
        resultados = scraper.search_businesses(niche, region, max_results=max_results)
        scraper.export_to_csv(resultados, filename="resultados.csv")
    finally:
        scraper.close()
