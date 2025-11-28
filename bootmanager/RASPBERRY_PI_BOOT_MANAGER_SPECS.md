# 📋 Raspberry Pi Boot Manager — Documentation Technique

## 📑 Table des matières
1. [Spécifications Techniques](#-spécifications-techniques)
2. [Découpage du Projet](#-découpage-du-projet)
3. [Flow Complet](#-flow-complet)
4. [Installation et Configuration](#-installation-et-configuration)
5. [Référence des Commandes](#-référence-des-commandes)

---

## 🔧 Spécifications Techniques

### Matériel Requis

| Composant | Spécification | Notes |
|-----------|---------------|-------|
| **Carte principale** | Raspberry Pi 4 Model B | 2GB+ RAM recommandé |
| **Matrice LED** | MAX7219 8×8 monochrome rouge | Interface SPI |
| **Câblage SPI** | Pins GPIO | CLK, DIN, CS, GND, VCC |
| **Alimentation** | 5V 3A USB-C | Officielle recommandée |
| **Stockage** | MicroSD 16GB+ | Classe 10 minimum |

### Configuration des Pins GPIO (MAX7219)

```
MAX7219 → Raspberry Pi 4
━━━━━━━━━━━━━━━━━━━━━━━
VCC  → Pin 2  (5V)
GND  → Pin 6  (Ground)
DIN  → Pin 19 (GPIO 10, MOSI)
CS   → Pin 24 (GPIO 8, CE0)
CLK  → Pin 23 (GPIO 11, SCLK)
```

### Logiciel et Dépendances

#### Système d'exploitation
- **OS** : Raspberry Pi OS Lite (Debian 12 Bookworm)
- **Kernel** : 6.1+
- **Python** : 3.11+

#### Dépendances Python

```bash
# Core dependencies
discord.py>=2.3.0      # Bot Discord avec Message Content Intent
requests>=2.31.0       # Requêtes HTTP pour ngrok API
luma.led_matrix>=1.7.0 # Pilote MAX7219
luma.core>=2.4.0       # Bibliothèque de base pour luma

# System utilities
psutil>=5.9.0          # Monitoring des processus
netifaces>=0.11.0      # Informations réseau
```

#### Outils Système

```bash
# Network management
wpa_supplicant         # Gestion Wi-Fi
dhcpcd                 # Client DHCP

# Remote access
openssh-server         # Serveur SSH
ngrok                  # Tunnel TCP

# Process management
systemd                # Orchestration des services
```

### Configuration Réseau

#### Wi-Fi (wpa_supplicant)
```conf
# /etc/wpa_supplicant/wpa_supplicant.conf
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1
country=FR

network={
    ssid="VOTRE_HOTSPOT"
    psk="MOT_DE_PASSE"
    key_mgmt=WPA-PSK
    priority=10
}
```

#### Configuration ngrok
```yaml
# ~/.config/ngrok/ngrok.yml
version: "2"
authtoken: VOTRE_TOKEN_NGROK
tunnels:
  ssh:
    proto: tcp
    addr: 22
```

### Secrets et Tokens

Fichier de configuration : `/home/pi/.config/bootmanager/secrets.env`

```bash
DISCORD_BOT_TOKEN=votre_token_bot_discord
DISCORD_CHANNEL_ID=123456789012345678
NGROK_AUTH_TOKEN=votre_token_ngrok
WIFI_SSID=NomHotspot
WIFI_PASSWORD=MotDePasse
```

---

## 🏗️ Découpage du Projet

### Architecture Générale

```
raspberry-pi-boot-manager/
│
├── src/
│   ├── main.py                    # Point d'entrée principal
│   ├── config.py                  # Gestion de la configuration
│   │
│   ├── network/
│   │   ├── __init__.py
│   │   ├── wifi_manager.py        # Connexion Wi-Fi
│   │   └── tunnel_manager.py      # Gestion du tunnel ngrok
│   │
│   ├── display/
│   │   ├── __init__.py
│   │   ├── led_controller.py      # Contrôle de la matrice LED
│   │   └── animations.py          # Animations et symboles
│   │
│   ├── discord/
│   │   ├── __init__.py
│   │   ├── bot.py                 # Bot Discord principal
│   │   ├── commands.py            # Gestionnaire de commandes
│   │   └── job_manager.py         # Gestion des processus
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py              # Système de logs
│       └── process_runner.py      # Exécution de commandes
│
├── systemd/
│   └── bootmanager.service        # Service systemd
│
├── config/
│   └── secrets.env.example        # Template de configuration
│
├── logs/                          # Logs du système
├── .cmdruns/                      # Logs des commandes Discord
│
├── requirements.txt               # Dépendances Python
├── install.sh                     # Script d'installation
└── README.md                      # Documentation utilisateur
```

### Modules Principaux

#### 1. `main.py` — Orchestrateur Principal
**Responsabilités :**
- Initialisation de tous les composants
- Gestion du cycle de vie de l'application
- Coordination entre les modules
- Gestion des erreurs globales

**Points clés :**
```python
async def main():
    # 1. Charger la configuration
    # 2. Initialiser la matrice LED
    # 3. Établir la connexion Wi-Fi
    # 4. Lancer le tunnel ngrok
    # 5. Démarrer le bot Discord
    # 6. Boucle de surveillance
```

#### 2. `network/wifi_manager.py` — Gestion Wi-Fi
**Responsabilités :**
- Connexion au hotspot configuré
- Vérification de l'état de connexion
- Retry automatique en cas d'échec
- Reporting du statut (IP, signal)

**Interface publique :**
```python
class WiFiManager:
    async def connect(ssid: str, password: str) -> bool
    async def is_connected() -> bool
    async def get_ip_address() -> str
    async def wait_for_connection(timeout: int) -> bool
```

#### 3. `network/tunnel_manager.py` — Gestion Ngrok
**Responsabilités :**
- Lancement du tunnel ngrok
- Récupération de l'URL publique
- Monitoring de l'état du tunnel
- Redémarrage automatique si déconnexion

**Interface publique :**
```python
class TunnelManager:
    async def start_tunnel() -> str  # Retourne l'URL SSH
    async def get_tunnel_url() -> str
    async def is_tunnel_active() -> bool
    async def stop_tunnel() -> None
```

#### 4. `display/led_controller.py` — Contrôle LED
**Responsabilités :**
- Initialisation de la matrice MAX7219
- Affichage de symboles et texte
- Gestion des animations
- Nettoyage et extinction

**Interface publique :**
```python
class LEDController:
    def show_symbol(symbol: str) -> None  # 'wifi', 'error', 'W', etc.
    def animate_wifi_search() -> None
    def show_text(text: str, scroll: bool) -> None
    def clear() -> None
```

**Symboles disponibles :**
- `wifi_searching` : Animation de recherche
- `wifi_connected` : Lettre "W"
- `wifi_error` : Wi-Fi barré
- `tunnel_active` : Symbole tunnel
- `error` : Croix d'erreur

#### 5. `discord/bot.py` — Bot Discord
**Responsabilités :**
- Connexion au serveur Discord
- Gestion des événements
- Envoi de messages et notifications
- Coordination avec le gestionnaire de commandes

**Événements clés :**
```python
@bot.event
async def on_ready()           # Bot connecté
async def on_message(message)  # Nouveau message reçu
async def on_command_error()   # Erreur de commande
```

#### 6. `discord/commands.py` — Gestionnaire de Commandes
**Responsabilités :**
- Parsing des commandes Discord
- Validation des arguments
- Exécution des commandes système
- Formatage des réponses

**Commandes implémentées :**
```python
async def cmd_execute(command: str) -> dict       # !<commande>
async def cmd_ps() -> list                        # !ps
async def cmd_tail(job_id: str, lines: int) -> str  # !tail
async def cmd_stop(job_id: str) -> bool           # !stop
```

#### 7. `discord/job_manager.py` — Gestion des Jobs
**Responsabilités :**
- Création et tracking des processus
- Gestion des ID uniques
- Lecture des logs en temps réel
- Termination propre des jobs

**Structure de données :**
```python
class Job:
    id: str              # UUID court (8 char)
    command: str         # Commande exécutée
    process: subprocess.Popen
    log_file: str        # Chemin du fichier log
    start_time: datetime
    status: str          # 'running', 'completed', 'killed'
```

#### 8. `utils/process_runner.py` — Exécuteur de Processus
**Responsabilités :**
- Exécution sécurisée de commandes shell
- Capture de stdout/stderr
- Gestion du timeout
- Logging automatique

**Interface publique :**
```python
class ProcessRunner:
    async def run(command: str, timeout: int) -> dict
    async def run_async(command: str, log_file: str) -> Popen
    @staticmethod
    def sanitize_command(command: str) -> str
```

---

## 🔄 Flow Complet

### 1. Séquence de Démarrage (Boot Flow)

```
┌─────────────────────────────────────────────────────────────────┐
│                    DÉMARRAGE DU RASPBERRY PI                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  systemd lance  │
                    │ bootmanager.service │
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : INITIALISATION                                        │
├─────────────────────────────────────────────────────────────────┤
│ • Chargement de config.py                                       │
│ • Lecture de secrets.env                                        │
│ • Vérification des dépendances                                  │
│ • Initialisation du logger                                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : INITIALISATION MATRICE LED                           │
├─────────────────────────────────────────────────────────────────┤
│ • Connexion SPI (GPIO 8, 10, 11)                               │
│ • Test de la matrice MAX7219                                    │
│ • LED : Animation de démarrage (2s)                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : CONNEXION WI-FI                                       │
├─────────────────────────────────────────────────────────────────┤
│ • LED : Animation "recherche Wi-Fi" (boucle)                   │
│ • wifi_manager.connect(SSID, PASSWORD)                          │
│ • Tentatives : 10 × 5 secondes                                 │
│                                                                  │
│   ┌────────────────┐                                            │
│   │ SUCCÈS ?       │                                            │
│   └────────────────┘                                            │
│     │           │                                                │
│    OUI         NON                                               │
│     │           │                                                │
│     │           ▼                                                │
│     │    ┌──────────────────┐                                   │
│     │    │ LED : Wi-Fi barré│                                   │
│     │    │ Log : ERROR      │                                   │
│     │    │ Exit code 1      │                                   │
│     │    └──────────────────┘                                   │
│     │                                                            │
│     ▼                                                            │
│ • LED : Lettre "W"                                              │
│ • Log : Connecté à SSID (IP: 192.168.x.x)                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4 : LANCEMENT DU TUNNEL NGROK                            │
├─────────────────────────────────────────────────────────────────┤
│ • LED : "T" (tunnel en cours)                                   │
│ • tunnel_manager.start_tunnel()                                 │
│ • Commande : ngrok tcp 22 --authtoken=...                      │
│ • Attente de l'URL publique (API ngrok)                        │
│ • Récupération : tcp://X.tcp.ngrok.io:XXXXX                    │
│ • LED : Checkmark ✓                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5 : DÉMARRAGE DU BOT DISCORD                             │
├─────────────────────────────────────────────────────────────────┤
│ • discord_bot.start(TOKEN)                                      │
│ • Connexion au serveur Discord                                  │
│ • Événement : on_ready()                                        │
│ • LED : "D" (Discord actif)                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 6 : NOTIFICATION DISCORD                                  │
├─────────────────────────────────────────────────────────────────┤
│ • Envoi du message dans le salon configuré :                   │
│                                                                  │
│   🚀 **Raspberry Pi Boot Manager - Ready**                     │
│   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━                          │
│   📡 **Connexion SSH disponible :**                            │
│   ```                                                           │
│   ssh pi@X.tcp.ngrok.io -p XXXXX                               │
│   ```                                                           │
│   🌐 IP locale : 192.168.x.x                                   │
│   ⏰ Boot time : 23s                                           │
│                                                                  │
│ • LED : Idle (rotation des symboles)                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  SYSTÈME PRÊT   │
                    │ En attente de   │
                    │    commandes    │
                    └─────────────────┘
```

### 2. Flow d'Exécution de Commande Discord

```
┌─────────────────────────────────────────────────────────────────┐
│            UTILISATEUR ENVOIE UNE COMMANDE DISCORD               │
│                     Exemple : !uptime                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 1 : RÉCEPTION ET PARSING                                 │
├─────────────────────────────────────────────────────────────────┤
│ • Événement : on_message(message)                               │
│ • Vérification : message.channel.id == DISCORD_CHANNEL_ID       │
│ • Vérification : message.content.startswith('!')                │
│ • Extraction : command = message.content[1:]                    │
│ • Validation : sanitize_command(command)                        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 2 : CRÉATION DU JOB                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Génération job_id = uuid4().hex[:8]  # Ex: "a3f7b21c"        │
│ • Création log_file = ~/.cmdruns/{job_id}.log                  │
│ • Enregistrement dans job_manager.active_jobs[]                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 3 : LANCEMENT DU PROCESSUS                               │
├─────────────────────────────────────────────────────────────────┤
│ • process = subprocess.Popen(                                   │
│     command,                                                     │
│     shell=True,                                                  │
│     stdout=log_file,                                            │
│     stderr=subprocess.STDOUT                                     │
│   )                                                              │
│ • LED : Clignotement rapide (activité)                         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 4 : CAPTURE DES 5 PREMIÈRES SECONDES                     │
├─────────────────────────────────────────────────────────────────┤
│ • Attente : 5 secondes                                          │
│ • Lecture : output = read_log_file(job_id, last_lines=20)      │
│ • Vérification : process.poll()  # Statut du processus         │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│ ÉTAPE 5 : RÉPONSE DISCORD                                       │
├─────────────────────────────────────────────────────────────────┤
│ • Message formaté :                                             │
│                                                                  │
│   🔧 **Commande exécutée** [`a3f7b21c`]                        │
│   ```bash                                                       │
│   $ uptime                                                      │
│   ```                                                           │
│   📤 **Sortie (5s):**                                           │
│   ```                                                           │
│   14:23:45 up 2:15, 1 user, load average: 0.24, 0.18, 0.12    │
│   ```                                                           │
│   📊 Statut : ✅ Terminé                                        │
│   💡 Utilisez `!tail a3f7b21c` pour voir la suite              │
│                                                                  │
│ • LED : Retour à idle                                           │
└─────────────────────────────────────────────────────────────────┘
```

### 3. Flow de Gestion des Jobs Longs

```
┌─────────────────────────────────────────────────────────────────┐
│           COMMANDE LONGUE LANCÉE : !python3 train.py            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  Job ID: b4c8d92f │
                    │  Status: RUNNING │
                    └─────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
    ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
    │ !ps          │  │ !tail b4c8d92f│  │ !stop b4c8d92f│
    │ Liste jobs   │  │ Affiche log   │  │ Tue le job   │
    └──────────────┘  └──────────────┘  └──────────────┘
            │                 │                 │
            ▼                 ▼                 ▼
                              
┌─────────────────┐  ┌──────────────────┐  ┌─────────────────┐
│ ID: b4c8d92f    │  │ [12:34:56] ...   │  │ Process killed  │
│ Cmd: python3... │  │ [12:35:01] ...   │  │ Job terminated  │
│ Status: RUNNING │  │ [12:35:12] ...   │  │                 │
│ Uptime: 2m 34s  │  │ (20 last lines)  │  │ Exit code: -9   │
└─────────────────┘  └──────────────────┘  └─────────────────┘
```

### 4. Gestion des Erreurs et Recovery

```
┌─────────────────────────────────────────────────────────────────┐
│                     SCÉNARIOS D'ERREUR                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐
│ 1. WI-FI DÉCONNECTÉ         │
├─────────────────────────────┤
│ • Détection : ping 8.8.8.8  │
│ • LED : Clignotement erreur │
│ • Action : Retry connexion  │
│ • Discord : Notification    │
│ • Tentatives : 5 × 10s      │
│ • Si échec : LED barré      │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 2. TUNNEL NGROK DOWN        │
├─────────────────────────────┤
│ • Détection : API ngrok     │
│ • LED : "T" clignotant      │
│ • Action : Restart ngrok    │
│ • Discord : Nouveau lien SSH│
│ • Retry : illimité (30s)    │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 3. BOT DISCORD CRASH        │
├─────────────────────────────┤
│ • Détection : Exception     │
│ • Log : Traceback complet   │
│ • Action : Restart bot      │
│ • LED : "D" clignotant      │
│ • systemd : Relance auto    │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 4. COMMANDE MALFORMÉE       │
├─────────────────────────────┤
│ • Validation : Regex        │
│ • Blocage : rm -rf, sudo    │
│ • Réponse : Message d'erreur│
│ • Pas d'exécution           │
└─────────────────────────────┘

┌─────────────────────────────┐
│ 5. MATRICE LED ERREUR       │
├─────────────────────────────┤
│ • Détection : Exception SPI │
│ • Action : Mode dégradé     │
│ • Logs uniquement           │
│ • Système continue          │
└─────────────────────────────┘
```

### 5. Diagramme d'État du Système

```
                    ┌──────────┐
                    │  BOOT    │
                    └────┬─────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ INIT MATRIX │
                  └──────┬──────┘
                         │
                         ▼
              ┌──────────────────┐
              │ CONNECTING WIFI  │◄─────┐
              └────┬─────────────┘      │
                   │                    │
                   ▼                    │ Retry
            ┌─────────────┐             │
       ┌────┤ WIFI OK ?   ├────┐        │
       │    └─────────────┘    │        │
      NON                     OUI       │
       │                       │        │
       ▼                       ▼        │
  ┌─────────┐         ┌───────────────┐│
  │ ERROR   │         │ STARTING      ││
  │ STATE   │         │ TUNNEL        ││
  └─────────┘         └───────┬───────┘│
                              │        │
                              ▼        │
                      ┌──────────────┐ │
                      │ STARTING BOT │ │
                      └───────┬──────┘ │
                              │        │
                              ▼        │
                      ┌──────────────┐ │
                   ┌──┤   READY      ├─┤───┐
                   │  └──────┬───────┘ │   │
                   │         │         │   │
                   │         ▼         │   │
                   │   ┌──────────┐   │   │
                   │   │ IDLE     │   │   │
                   │   └────┬─────┘   │   │
                   │        │         │   │
                   │        ▼         │   │
                   │  ┌──────────┐   │   │
      Commande ────┼─►│EXECUTING │   │   │
                   │  └────┬─────┘   │   │
                   │       │         │   │
                   │       ▼         │   │
                   │  ┌──────────┐   │   │
                   └──┤  READY   │◄──┘   │
                      └────┬─────┘       │
                           │             │
                    Erreur │             │
                           ▼             │
                      ┌─────────┐        │
                      │RECOVERY │────────┘
                      └─────────┘
```

---

## 🚀 Installation et Configuration

### Prérequis

```bash
# Mise à jour du système
sudo apt update && sudo apt upgrade -y

# Installation des dépendances système
sudo apt install -y python3-pip python3-venv git \
    openssh-server wpa_supplicant network-manager

# Installation de ngrok
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-arm.tgz
sudo tar xvzf ngrok-v3-stable-linux-arm.tgz -C /usr/local/bin
rm ngrok-v3-stable-linux-arm.tgz

# Vérification
ngrok --version
```

### Installation du Projet

```bash
# Cloner le repository
git clone https://github.com/votre-repo/raspberry-pi-boot-manager.git
cd raspberry-pi-boot-manager

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Configurer les secrets
cp config/secrets.env.example config/secrets.env
nano config/secrets.env  # Éditer avec vos tokens

# Lancer l'installation
sudo bash install.sh
```

### Configuration du Service systemd

```ini
# /etc/systemd/system/bootmanager.service
[Unit]
Description=Raspberry Pi Boot Manager
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/raspberry-pi-boot-manager
Environment="PATH=/home/pi/raspberry-pi-boot-manager/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/pi/raspberry-pi-boot-manager/venv/bin/python3 src/main.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/bootmanager.log
StandardError=append:/var/log/bootmanager.error.log

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer le service
sudo systemctl daemon-reload
sudo systemctl enable bootmanager.service
sudo systemctl start bootmanager.service

# Vérifier le statut
sudo systemctl status bootmanager.service

# Voir les logs
journalctl -u bootmanager.service -f
```

---

## 📖 Référence des Commandes

### Commandes Discord

| Commande | Description | Exemple |
|----------|-------------|---------|
| `!<cmd>` | Exécute une commande shell | `!ls -la` |
| `!ps` | Liste tous les jobs actifs | `!ps` |
| `!tail <id> [n]` | Affiche les n dernières lignes d'un job | `!tail a3f7b21c 50` |
| `!stop <id>` | Termine un job en cours | `!stop a3f7b21c` |
| `!status` | Affiche l'état du système | `!status` |
| `!reboot` | Redémarre le Raspberry Pi | `!reboot` |

### Exemples d'Utilisation

#### Lancer un script Python
```
!python3 /home/pi/scripts/data_processor.py
```

#### Vérifier l'espace disque
```
!df -h
```

#### Surveiller l'utilisation CPU
```
!top -b -n 1 | head -20
```

#### Mettre à jour le système
```
!sudo apt update && sudo apt upgrade -y
```

#### Lister les processus actifs
```
!ps
```
**Réponse :**
```
📋 Jobs actifs (3):
━━━━━━━━━━━━━━━━━━━━━━
ID: a3f7b21c
Cmd: python3 train.py
Status: RUNNING
Uptime: 5m 23s

ID: b8f2c45d
Cmd: ping -c 1000 8.8.8.8
Status: RUNNING
Uptime: 1m 12s

ID: c9d3a76e
Cmd: tail -f /var/log/syslog
Status: RUNNING
Uptime: 45s
```

#### Suivre les logs d'un job
```
!tail a3f7b21c 30
```
**Réponse :**
```
📜 Logs du job a3f7b21c (30 dernières lignes):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Epoch 1/100 - Loss: 0.4523
Epoch 2/100 - Loss: 0.3891
Epoch 3/100 - Loss: 0.3456
...
```

#### Arrêter un job
```
!stop a3f7b21c
```
**Réponse :**
```
🛑 Job a3f7b21c terminé avec succès
```

### Commandes Système (via SSH)

```bash
# Démarrer le service
sudo systemctl start bootmanager.service

# Arrêter le service
sudo systemctl stop bootmanager.service

# Redémarrer le service
sudo systemctl restart bootmanager.service

# Voir les logs en temps réel
journalctl -u bootmanager.service -f

# Vérifier l'état du Wi-Fi
nmcli device status

# Vérifier le tunnel ngrok
curl http://localhost:4040/api/tunnels

# Lister les logs de commandes
ls -lh ~/.cmdruns/
```

---

## 🔒 Sécurité

### Recommandations

1. **Secrets** : Ne jamais commit `secrets.env` dans Git
2. **SSH** : Utiliser des clés SSH au lieu de mots de passe
3. **Firewall** : Configurer UFW pour bloquer les ports non utilisés
4. **Commandes** : Bloquer les commandes dangereuses (rm -rf, dd, etc.)
5. **Discord** : Limiter l'accès au salon de contrôle

### Commandes Bloquées

Le système refuse automatiquement :
- `rm -rf /`
- `sudo rm`
- `dd if=/dev/zero`
- `mkfs.*`
- `:(){ :|:& };:` (fork bomb)

---

## 📊 Monitoring

### Métriques Collectées

- Uptime du système
- Température CPU
- Utilisation mémoire
- Espace disque
- Qualité signal Wi-Fi
- Statut tunnel ngrok
- Nombre de jobs actifs

### Logs

```
/var/log/bootmanager.log       # Log principal
/var/log/bootmanager.error.log # Erreurs uniquement
~/.cmdruns/<job_id>.log        # Logs par job
```

---

## 🐛 Dépannage

### Le service ne démarre pas

```bash
# Vérifier le statut
sudo systemctl status bootmanager.service

# Voir les erreurs
journalctl -u bootmanager.service -n 50

# Tester manuellement
cd /home/pi/raspberry-pi-boot-manager
source venv/bin/activate
python3 src/main.py
```

### La LED ne s'allume pas

```bash
# Vérifier le câblage SPI
ls -l /dev/spidev0.0

# Activer SPI si nécessaire
sudo raspi-config
# Interface Options > SPI > Enable
```

### Le bot Discord ne répond pas

```bash
# Vérifier le token
cat config/secrets.env | grep DISCORD_BOT_TOKEN

# Vérifier les intents du bot (Message Content Intent activé ?)
# https://discord.com/developers/applications
```

### Ngrok ne se lance pas

```bash
# Vérifier le token
ngrok config check

# Tester manuellement
ngrok tcp 22
```

---

## 📝 Notes de Version

### v1.0.0 — Release Initiale
- ✅ Connexion Wi-Fi automatique
- ✅ Tunnel SSH via ngrok
- ✅ Bot Discord avec exécution de commandes
- ✅ Matrice LED MAX7219
- ✅ Gestion des jobs avec logs
- ✅ Service systemd

### Roadmap v1.1.0
- 🔄 Support multi-hotspots Wi-Fi
- 🔄 Interface web de monitoring
- 🔄 Authentification Discord par rôle
- 🔄 Statistiques d'utilisation
- 🔄 Export des logs en PDF

---

## 📄 Licence

MIT License — Voir le fichier `LICENSE` pour plus de détails.

---

## 🤝 Contribution

Les contributions sont les bienvenues ! Merci de :
1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/AmazingFeature`)
3. Commit les changements (`git commit -m 'Add AmazingFeature'`)
4. Push la branche (`git push origin feature/AmazingFeature`)
5. Ouvrir une Pull Request

---

## 📧 Support

Pour toute question ou problème :
- Ouvrir une issue sur GitHub
- Contact : votre-email@example.com

---

**Construit avec ❤️ pour le Raspberry Pi 4**
