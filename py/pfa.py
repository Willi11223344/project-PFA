import tkinter as tk
from tkinter import messagebox
import sqlite3
import cv2
import face_recognition
import numpy as np
import json
from datetime import datetime


# Connexion à la base de données
conn = sqlite3.connect('don.db')
cursor = conn.cursor()

cursor.execute('''CREATE TABLE IF NOT EXISTS employes (
                    id INTEGER PRIMARY KEY,
                    nom TEXT,
                    prenom TEXT,
                    poste TEXT,
                    departement TEXT,
                    photo BLOB,
                    face_encoding TEXT)''')
conn.commit()

cursor.execute('''CREATE TABLE IF NOT EXISTS pointages (
                    id INTEGER PRIMARY KEY,
                    id_emp INTEGER,
                    date TEXT,
                    heure_arrivee TEXT,
                    heure_depart TEXT)''')
conn.commit()

def capturer_image(type_pointage):
    # Ouvrir la caméra pour capturer l'image de l'employé
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    cap.release()

    if ret:
        # Conversion de l'image en format compatible pour stockage dans la base de données
        _, img_encoded = cv2.imencode('.jpg', frame)
        photo_bytes = img_encoded.tobytes()

        # Reconnaissance faciale sur l'image capturée
        face_locations = face_recognition.face_locations(frame)
        face_encodings = face_recognition.face_encodings(frame, face_locations)

        # Vérifier si un visage a été détecté
        if len(face_encodings) > 0:
            # Charger les visages enregistrés dans la base de données
            cursor.execute("SELECT id, nom, prenom, face_encoding FROM employes")
            rows = cursor.fetchall()
            known_face_encodings = []
            known_face_names = []

            for row in rows:
                employe_id, employe_nom, employe_prenom, employe_face_encoding_str = row
                employe_face_encoding = np.array(json.loads(employe_face_encoding_str))
                known_face_encodings.append(employe_face_encoding)
                known_face_names.append((employe_id, f"{employe_nom} {employe_prenom}"))

            # Comparaison des visages détectés avec les visages enregistrés
            for face_encoding in face_encodings:
                # Comparaison avec les visages connus
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                id_emp = None

                # Trouver la correspondance
                if True in matches:
                    first_match_index = matches.index(True)
                    id_emp, name = known_face_names[first_match_index]
                    if type_pointage == "arrivee":
                        pointer_arrivee(id_emp, name)
                    elif type_pointage == "depart":
                        pointer_depart(id_emp, name)
                else:
                    messagebox.showerror("Erreur", "Visage introuvable dans la base de données.")
        else:
            messagebox.showerror("Erreur", "Aucun visage détecté.")

def pointer_arrivee(id_emp, nom):
    now = datetime.now()
    heure = now.strftime("%H:%M:%S")
    date = now.strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO pointages (id_emp, date, heure_arrivee) VALUES (?, ?, ?)", (id_emp, date, heure))
    conn.commit()
    messagebox.showinfo("Succès", f"Pointage d'arrivée enregistré pour {nom} à {heure}.")

def pointer_depart(id_emp, nom):
    now = datetime.now()
    heure = now.strftime("%H:%M:%S")
    cursor.execute("UPDATE pointages SET heure_depart = ? WHERE id_emp = ? AND date = ?", (heure, id_emp, datetime.now().strftime("%Y-%m-%d")))
    conn.commit()
    messagebox.showinfo("Succès", f"Pointage de départ enregistré pour {nom} à {heure}.")

def reconnaissance_facial():
    # Ouvrir la caméra pour la reconnaissance faciale
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        messagebox.showerror("Erreur", "Impossible d'ouvrir la caméra.")
        return

    # Charger les visages enregistrés dans la base de données
    cursor.execute("SELECT id, nom, prenom, face_encoding FROM employes")
    rows = cursor.fetchall()
    employes = []
    known_face_encodings = []
    known_face_names = []

    for row in rows:
        employe_id, employe_nom, employe_prenom, employe_face_encoding_str = row
        employes.append((employe_nom, employe_prenom))
        employe_face_encoding = np.array(json.loads(employe_face_encoding_str))
        known_face_encodings.append(employe_face_encoding)
        known_face_names.append(f"{employe_nom} {employe_prenom}")

    while True:
        # Capturer une image de la caméra
        ret, frame = cap.read()
        if not ret:
            messagebox.showerror("Erreur", "Impossible de lire l'image de la caméra.")
            break

        # Conversion de l'image pour le traitement avec face_recognition
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Détection des visages dans l'image capturée
        face_locations = face_recognition.face_locations(rgb_frame)
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        # Comparaison des visages détectés avec les visages enregistrés
        for face_encoding in face_encodings:
            # Comparaison avec les visages connus
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Inconnu"

            # Trouver la correspondance
            if True in matches:
                first_match_index = matches.index(True)
                name = known_face_names[first_match_index]

            # Affichage du nom de la personne détectée sur l'image
            cv2.putText(frame, name, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # Affichage de l'image avec les noms détectés
        cv2.imshow('Reconnaissance Faciale', frame)

        # Sortie de la boucle si la touche 'q' est enfoncée
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Libération de la caméra et fermeture de la fenêtre
    cap.release()
    cv2.destroyAllWindows()

   

# Interface utilisateur pour l'ajout d'un employé
def ajouter_employe_interface():
    def ajouter_employe():
        nom = nom_entry.get()
        prenom = prenom_entry.get()
        poste = poste_entry.get()
        departement = departement_entry.get()
        capturer_image(nom, prenom, poste, departement)
        
        # Mise à jour des étiquettes avec les informations de l'employé ajouté
        nom_label.config(text="Nom: " + nom)
        prenom_label.config(text="Prénom: " + prenom)
        poste_label.config(text="Poste: " + poste)
        departement_label.config(text="Département: " + departement)

    root = tk.Tk()
    root.geometry("250x300")
    root.title("Ajouter Employé")

    tk.Label(root, text="Nom:").grid(row=0, column=0)
    nom_entry = tk.Entry(root)
    nom_entry.grid(row=0, column=1)

    tk.Label(root, text="Prénom:").grid(row=1, column=0)
    prenom_entry = tk.Entry(root)
    prenom_entry.grid(row=1, column=1)

    tk.Label(root, text="Poste:").grid(row=2, column=0)
    poste_entry = tk.Entry(root)
    poste_entry.grid(row=2, column=1)

    tk.Label(root, text="Département:").grid(row=3, column=0)
    departement_entry = tk.Entry(root)
    departement_entry.grid(row=3, column=1)

    ajouter_button = tk.Button(root, text="Ajouter employé", command=ajouter_employe)
    ajouter_button.grid(row=4, columnspan=2)

    # Ajouter des étiquettes pour afficher les informations de l'employé
    nom_label = tk.Label(root, text="")
    nom_label.grid(row=5, columnspan=2)

    prenom_label = tk.Label(root, text="")
    prenom_label.grid(row=6, columnspan=2)

    poste_label = tk.Label(root, text="")
    poste_label.grid(row=7, columnspan=2)

    departement_label = tk.Label(root, text="")
    departement_label.grid(row=8, columnspan=2)

    root.mainloop()

# Main interface
main_root = tk.Tk()
main_root.geometry("200x100")
main_root.title("Gestion Employés")

ajouter_button = tk.Button(main_root, text="Ajouter Employé", command=ajouter_employe_interface)
ajouter_button.pack()

recon_button = tk.Button(main_root, text="Reconnaissance Faciale", command=reconnaissance_facial)
recon_button.pack()

arrivee_button = tk.Button(main_root, text="Pointer Arrivée", command=lambda: capturer_image("arrivee"))
arrivee_button.pack()

depart_button = tk.Button(main_root, text="Pointer Départ", command=lambda: capturer_image("depart"))
depart_button.pack()

main_root.mainloop()
