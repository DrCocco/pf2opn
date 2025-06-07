#!/usr/bin/env python3
"""
Script per migrare DHCP static mappings da pfSense a OPNsense
Autore: Assistente AI <3
Versione: 1.0
"""

import xml.etree.ElementTree as ET
import json
import csv
import sys
import argparse
from pathlib import Path

def extract_pfsense_reservations(xml_file):
    """Estrae le DHCP reservations dal file di configurazione pfSense"""
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        reservations = []
        
        # Cerca nelle configurazioni DHCP di tutte le interfacce
        dhcpd = root.find('dhcpd')
        if dhcpd is not None:
            for interface in dhcpd:
                interface_name = interface.tag
                print(f"Processando interfaccia: {interface_name}")
                
                staticmaps = interface.findall('staticmap')
                for staticmap in staticmaps:
                    reservation = {}
                    
                    # Estrai i campi principali
                    mac = staticmap.find('mac')
                    if mac is not None:
                        reservation['mac'] = mac.text
                    
                    ipaddr = staticmap.find('ipaddr')
                    if ipaddr is not None:
                        reservation['ip'] = ipaddr.text
                    
                    hostname = staticmap.find('hostname')
                    if hostname is not None:
                        reservation['hostname'] = hostname.text
                    
                    descr = staticmap.find('descr')
                    if descr is not None:
                        reservation['description'] = descr.text
                    
                    # Campi aggiuntivi
                    cid = staticmap.find('cid')
                    if cid is not None:
                        reservation['cid'] = cid.text
                    
                    # Aggiungi informazioni sull'interfaccia
                    reservation['interface'] = interface_name
                    
                    # Aggiungi solo se ha almeno MAC e IP
                    if 'mac' in reservation and 'ip' in reservation:
                        reservations.append(reservation)
                        print(f"  Trovata reservation: {reservation['mac']} -> {reservation['ip']}")
        
        return reservations
        
    except ET.ParseError as e:
        print(f"Errore nel parsing XML: {e}")
        return []
    except Exception as e:
        print(f"Errore generico: {e}")
        return []

def save_to_csv(reservations, output_file):
    """Salva le reservations in formato CSV"""
    if not reservations:
        print("Nessuna reservation da salvare")
        return
    
    fieldnames = ['interface', 'mac', 'ip', 'hostname', 'description', 'cid']
    
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        for reservation in reservations:
            # Assicurati che tutti i campi esistano
            row = {field: reservation.get(field, '') for field in fieldnames}
            writer.writerow(row)
    
    print(f"Salvate {len(reservations)} reservations in {output_file}")

def save_to_json(reservations, output_file):
    """Salva le reservations in formato JSON"""
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(reservations, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"Salvate {len(reservations)} reservations in {output_file}")

def generate_opnsense_commands(reservations, output_file):
    """Genera comandi curl per l'API di OPNsense"""
    if not reservations:
        print("Nessuna reservation per generare comandi")
        return
    
    commands = []
    commands.append("#!/bin/bash")
    commands.append("# Script per importare DHCP reservations in OPNsense via API")
    commands.append("# Modifica le variabili seguenti con i tuoi valori:")
    commands.append('OPNSENSE_HOST="https://your-opnsense-ip"')
    commands.append('API_KEY="your-api-key"')
    commands.append('API_SECRET="your-api-secret"')
    commands.append("")
    
    for i, reservation in enumerate(reservations):
        mac = reservation.get('mac', '')
        ip = reservation.get('ip', '')
        hostname = reservation.get('hostname', '')
        description = reservation.get('description', '')
        
        # Costruisci il comando curl per l'API OPNsense
        cmd = f'''# Reservation {i+1}: {hostname or mac}
curl -X POST \\
  "$OPNSENSE_HOST/api/dhcpv4/leases/addLease" \\
  -H "Content-Type: application/json" \\
  -u "$API_KEY:$API_SECRET" \\
  -d '{{
    "lease": {{
      "interface": "lan",
      "mac": "{mac}",
      "ip": "{ip}",
      "hostname": "{hostname}",
      "description": "{description}"
    }}
  }}'
'''
        commands.append(cmd)
        commands.append("")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(commands))
    
    print(f"Generati comandi API in {output_file}")
    print("IMPORTANTE: Modifica il file con i tuoi dati API prima di eseguirlo!")

def main():
    parser = argparse.ArgumentParser(description='Migra DHCP reservations da pfSense a OPNsense')
    parser.add_argument('input_xml', help='File XML di configurazione pfSense')
    parser.add_argument('-o', '--output', default='dhcp_reservations', 
                       help='Nome base per i file di output (default: dhcp_reservations)')
    parser.add_argument('--csv', action='store_true', help='Genera file CSV')
    parser.add_argument('--json', action='store_true', help='Genera file JSON')
    parser.add_argument('--api', action='store_true', help='Genera script API per OPNsense')
    parser.add_argument('--all', action='store_true', help='Genera tutti i formati')
    
    args = parser.parse_args()
    
    # Verifica che il file di input esista
    if not Path(args.input_xml).exists():
        print(f"Errore: File {args.input_xml} non trovato")
        sys.exit(1)
    
    # Se non specificato nessun formato, genera tutti
    if not (args.csv or args.json or args.api):
        args.all = True
    
    print(f"Analizzando {args.input_xml}...")
    reservations = extract_pfsense_reservations(args.input_xml)
    
    if not reservations:
        print("Nessuna DHCP reservation trovata nel file XML")
        sys.exit(1)
    
    print(f"Trovate {len(reservations)} DHCP reservations")
    
    # Genera i file di output richiesti
    if args.csv or args.all:
        save_to_csv(reservations, f"{args.output}.csv")
    
    if args.json or args.all:
        save_to_json(reservations, f"{args.output}.json")
    
    if args.api or args.all:
        generate_opnsense_commands(reservations, f"{args.output}_api.sh")
    
    print("\nMigrazione completata!")
    print("\nProsimi passi:")
    print("1. Controlla i file generati per verificare che i dati siano corretti")
    print("2. Per l'importazione via API, modifica il file .sh con le tue credenziali OPNsense")
    print("3. Esegui lo script API o importa manualmente i dati da CSV/JSON")

if __name__ == '__main__':
    main()
