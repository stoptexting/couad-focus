# Specs Sprint 1 - Jauge Physique LED

## 🎯 Objectif
Créer un système de gestion de tâches avec jauge physique (LEDs) et virtuelle (web) synchronisées en temps réel.

## 🏗️ Architecture
- **Backend:** Flask (Raspberry Pi 4) → API REST + Contrôle LEDs
- **Frontend:** Next.js 14+ → Interface web de gestion
- **Infrastructure:** ✅ Ngrok et auto-boot déjà en place
- **Hardware:** Panneau LED RGB adressable

---

## 📡 API Flask - Endpoints

### Gestion des tâches

**GET /api/tasks**
- Liste toutes les tâches
- Response: `[{id, title, description, status, created_at, updated_at}]`

**GET /api/tasks/:id**
- Détails d'une tâche
- Response: `{id, title, description, status, created_at, updated_at}`

**POST /api/tasks**
- Créer une nouvelle tâche
- Body: `{title: string, description: string}`
- Response: `{id, title, description, status: "new", created_at, updated_at}`

**PUT /api/tasks/:id**
- Modifier une tâche existante
- Body: `{title?: string, description?: string, status?: "new" | "completed"}`
- Response: `{id, title, description, status, created_at, updated_at}`

**DELETE /api/tasks/:id**
- Supprimer une tâche
- Response: `{success: true, message: "Task deleted"}`

### Progression globale

**GET /api/progress**
- Calcule la progression globale du projet
- Formule: `(nombre_taches_completed / nombre_total_taches) * 100`
- Response: `{percentage: number, total_tasks: number, completed_tasks: number}`

**POST /api/leds/update**
- Déclenche manuellement la mise à jour des LEDs
- Body: `{percentage: number (0-100)}`
- Response: `{success: true, leds_lit: number}`

---

## 🎨 Interface Next.js - Pages & Composants

### Page principale: `/` (Dashboard)
- Liste de toutes les tâches (carte par tâche)
- Jauge virtuelle de progression globale (composant `ProgressGauge`)
- Bouton "Nouvelle tâche"

### Composant: `TaskCard`
**Affichage:**
- Titre de la tâche
- Description (tronquée)
- Status (badge coloré: new=orange, completed=vert)
- Checkbox pour marquer comme terminée

**Actions:**
- Checkbox "Terminée" → PUT /api/tasks/:id avec status: "completed"
- Bouton "Modifier" → ouvre modal d'édition
- Bouton "Supprimer" → confirmation puis suppression

### Composant: `ProgressGauge`
- Représentation visuelle 1:1 du panneau LED physique
- Affichage du % exact (tâches complétées / total)
- Dégradé de couleurs: rouge (0-33%) → jaune (34-66%) → vert (67-100%)
- Mise à jour automatique toutes les 2 secondes (polling `/api/progress`)
- Indicateur de connexion (connecté/déconnecté)
- Affichage: "X / Y tâches complétées"

### Modal: `TaskFormModal`
**Création:**
- Champs: Titre (requis), Description (optionnel)
- Validation: titre non vide
- Submit → POST /api/tasks (status: "new" par défaut)

**Édition:**
- Champs pré-remplis avec données existantes
- Titre et Description modifiables
- Submit → PUT /api/tasks/:id

---

## 🔧 Modèle de données - Tâche

```python
{
    "id": "uuid",
    "title": "string (max 100 chars)",
    "description": "string (max 500 chars)",
    "status": "new" | "completed",
    "created_at": "ISO datetime",
    "updated_at": "ISO datetime"
}
```

**Règles métier:**
- Status par défaut = "new" à la création
- `updated_at` mis à jour à chaque modification
- Sprint 1: Tâches stockées en JSON ou SQLite (4-5 tâches initiales en dur)

---

## 🔌 Contrôle Panneau LED

### Module: `led_controller.py`

**Fonction: `update_leds(percentage: int)`**
- Convertit le % en nombre de LEDs à allumer
- Pourcentage = (tâches completed / total tâches) * 100
- Exemple: 32 LEDs, 4 tâches dont 2 completed → 50% → 16 LEDs allumées
- Dégradé de couleurs selon progression
- Gestion d'erreur si hardware non disponible

**Bibliothèque:** `rpi-rgb-led-matrix` ou équivalent

**Déclenchement automatique:**
- Après chaque modification de tâche (POST/PUT/DELETE)
- Calcul de la progression → appel `update_leds()`

---

## ✅ Tests manuels requis

**CRUD Tâches:**
1. Créer 3 tâches différentes → vérifier liste avec status "new"
2. Modifier le titre d'une tâche → vérifier persistence
3. Cocher la checkbox "Terminée" → vérifier status passe à "completed"
4. Décocher une tâche completed → vérifier status repasse à "new"
5. Supprimer une tâche → vérifier disparition

**Synchronisation:**
1. Créer 4 tâches → progression = 0% (0/4)
2. Marquer 2 tâches comme completed → progression = 50% (2/4)
3. LEDs physiques et virtuelles affichent 50%
4. Marquer toutes comme completed → progression = 100% (4/4)
5. Supprimer 1 tâche completed → progression recalculée (3/3 = 100%)
6. Vérifier que jauge virtuelle = jauge physique (même %)

---

## 📦 Livrables Sprint 1

- ✅ API Flask complète (5 endpoints: GET, POST, PUT, DELETE, GET progress)
- ✅ Interface Next.js responsive (desktop + mobile)
- ✅ CRUD opérationnel pour les tâches (new/completed)
- ✅ Calcul de progression automatique (tâches completed / total)
- ✅ Contrôle panneau LED fonctionnel
- ✅ Synchronisation temps réel (polling 2s)
- ✅ 4-5 tâches initiales en dur dans le code