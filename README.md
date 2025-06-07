# pf2opn
tool collection to switch from pfsense to opnsense

Come usarlo:
1. Esporta la configurazione da pfSense:

Vai in Diagnostics > Backup & Restore
Scarica il backup completo in formato XML

2. Esegui lo script:

python3 dhcp_migration.py config-pfsense.xml --all

3. Opzioni disponibili:

--csv: Genera file CSV per importazione manuale
--json: Genera file JSON con tutti i dati
--api: Genera script bash con comandi API per OPNsense
--all: Genera tutti i formati (default se non specifichi nulla)

Output dello script:
File CSV: Per importazione manuale o come riferimento
File JSON: Formato strutturato con tutti i dati
Script API: File bash con comandi curl per automatizzare l'importazione
Per usare l'API di OPNsense:

Abilita l'API in OPNsense (System > Access > Users, crea chiavi API)
Modifica il file *_api.sh generato con:

L'IP del tuo OPNsense
Le tue chiavi API


Esegui lo script: bash dhcp_reservations_api.sh

Nota: Potrebbe essere necessario adattare leggermente i comandi API in base alla versione di OPNsense.