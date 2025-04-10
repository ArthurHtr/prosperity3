"""
Ce script lit le fichier logs_1.log, qui peut contenir une en-tête (ex. « Sandbox logs: »)
suivie de plusieurs objets JSON concaténés.
Il regroupe tous les logs lisibles dans un seul fichier de sortie, avec une mise en forme claire.
"""

import json
import re

def main():
    input_filename = "utils/logs_2.log"
    output_filename = "trader_execution_output.txt"

    try:
        with open(input_filename, "r", encoding="utf-8") as f:
            content = f.read()
    except IOError as e:
        print("Erreur lors de l'ouverture du fichier :", e)
        return

    # Ignorer l'entête éventuelle (tout ce qui précède le premier '{')
    first_brace = content.find('{')
    if first_brace == -1:
        print("Aucun caractère '{' trouvé dans le fichier.")
        return
    content = content[first_brace:]

    # Séparer les blocs JSON concaténés
    blocks = re.split(r'(?={)', content)
    blocks = [b.strip() for b in blocks if b.strip().startswith('{')]

    if not blocks:
        print("Aucun bloc JSON valide trouvé dans le fichier.")
        return

    try:
        with open(output_filename, "w", encoding="utf-8") as out_f:
            out_f.write("##############################################\n")
            out_f.write("#      LOGS D’EXÉCUTION DU TRADER (FORMATÉ)   #\n")
            out_f.write("##############################################\n\n")

            for i, block in enumerate(blocks, start=1):
                try:
                    data = json.loads(block)
                except Exception as e:
                    print(f"Erreur lors du parsing du bloc {i} : {e}")
                    continue

                timestamp = data.get("timestamp", "N/A")
                lambda_log = data.get("lambdaLog", "").strip()

                out_f.write(f"---------- Bloc {i} ----------\n")
                out_f.write(f"Timestamp : {timestamp}\n")
                out_f.write("=== Début de l'exécution ===\n\n")
                out_f.write(lambda_log + "\n\n")
                out_f.write("=== Fin de l'exécution ===\n\n")
                out_f.write("\n" + "="*50 + "\n\n")

        print(f"Fichier de sortie généré : {output_filename}")

    except IOError as e:
        print(f"Erreur lors de l'écriture dans le fichier {output_filename} : {e}")

if __name__ == "__main__":
    main()
