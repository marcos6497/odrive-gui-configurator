# ODrive GUI Configurador

Interface gráfica moderna para **configuração e monitoramento de placas ODrive**, desenvolvida em **Python** e distribuída em versão compilada `.exe`.


## 🚀 Funcionalidades

### 🔌 Conexão e Controle
- **Conectar com ODrive** – Inicia a comunicação e carrega os dados de configuração.  
- **Desconectar ODrive** – Interrompe a comunicação manualmente.  
- **Reiniciar ODrive** – Envia o comando de reboot para a placa.  
- **Colocar em IDLE (Eixo 0)** – Coloca o eixo 0 no estado `IDLE`, necessário antes de salvar configurações.
- **Fonte (DC)** – Configurações e leitura da alimentação.  
- **Motor** – Ajustes e status do motor.  
- **Encoder** – Status e parâmetros do encoder.  
- **CAN** – Configuração da comunicação CAN.  
- **Gráfico** – Monitoramento visual em tempo real.  
- **Terminal** – Comandos diretos de interação.    

### ⚙️ Configurações
- **Salvar Configurações** – Executa `odrv.save_configuration()` para gravar os parâmetros atuais na flash.  
- **Apagar Configurações** – Executa `odrv.erase_configuration()` e restaura o ODrive ao padrão de fábrica (ação irreversível).  
- **Visualizar Configurações** – Exibe todas as configs (geral, eixo, motor, encoder, controlador, CAN) em janela própria com opção de salvar em `.txt`.  

### 📊 Monitoramento em Tempo Real
- **Posição do encoder** (em graus).  
- **Velocidade estimada** (voltas/s).  
- **Tensão do barramento (VBus)** em volts.  
- **Limite de corrente** configurado (A).  
- **Estado atual do eixo** (`AXIS_STATE_*`).  
- **Gráfico em tempo real** com atualização contínua.  

### 🧰 Erros e Diagnóstico
- **Mostrar Erros** – Abre uma janela dedicada que lista todos os erros atuais do ODrive com destaque em HTML.  
- **Limpar Erros** – Botão para resetar os erros da placa.  


### ⚙️ Fotos

<img width="850" height="629" alt="{691F36C1-3C34-45FE-B5C4-E4033D0AF3B2}" src="https://github.com/user-attachments/assets/f0db9eed-3f75-4479-9f82-3af7cd1e7a00" />
<img width="852" height="633" alt="{745D86B8-A70D-4892-B862-666CAAA3C399}" src="https://github.com/user-attachments/assets/1abc74e6-7a3a-4da0-b13a-2378cf75b241" />


---

## 📦 Download
👉 A versão compilada em **`.exe`** está disponível na aba **[Releases](../../releases)**.  
Basta baixar e executar, não é necessário instalar nada.

---

## 📄 Licença
Este projeto utiliza bibliotecas de terceiros. Consulte `licenses.txt` para detalhes.

---
