# Specs Techniques - Sprint 2

## 🎯 Objectif
Implémenter une hiérarchie complète Projet→Sprint→UserStory→Task avec visualisation multi-jauges et layouts.

---

## 📊 Modèles de données

### Projet
```json
{
  "id": "uuid",
  "name": "string",
  "description": "string",
  "created_at": "datetime"
}
```

### Sprint
```json
{
  "id": "uuid",
  "name": "string",
  "project_id": "uuid",
  "start_date": "date",
  "end_date": "date",
  "status": "planned | active | completed"
}
```

### UserStory
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "sprint_id": "uuid",
  "priority": "P0 | P1 | P2",
  "status": "new | in_progress | completed"
}
```

### Task
```json
{
  "id": "uuid",
  "title": "string",
  "description": "string",
  "user_story_id": "uuid",
  "status": "new | completed",
  "created_at": "datetime"
}
```

---

## 📡 API Endpoints

### Projets
- `GET /api/projects` - Liste tous les projets
- `GET /api/projects/:id` - Détails projet + arborescence complète
- `POST /api/projects` - Créer projet
- `PUT /api/projects/:id` - Modifier projet
- `DELETE /api/projects/:id` - Supprimer (cascade)

### Sprints
- `GET /api/projects/:project_id/sprints` - Liste sprints du projet
- `GET /api/sprints/:id` - Détails sprint + user stories
- `POST /api/projects/:project_id/sprints` - Créer sprint
- `PUT /api/sprints/:id` - Modifier sprint
- `DELETE /api/sprints/:id` - Supprimer (cascade)

### User Stories
- `GET /api/sprints/:sprint_id/user-stories` - Liste US du sprint
- `GET /api/user-stories/:id` - Détails US + tasks
- `POST /api/sprints/:sprint_id/user-stories` - Créer US
- `PUT /api/user-stories/:id` - Modifier US
- `DELETE /api/user-stories/:id` - Supprimer (cascade)

### Tasks
- `GET /api/user-stories/:us_id/tasks` - Liste tasks de l'US
- `POST /api/user-stories/:us_id/tasks` - Créer task
- `PUT /api/tasks/:id` - Modifier task
- `DELETE /api/tasks/:id` - Supprimer task

### Progression
- `GET /api/projects/:id/progress` - Progression projet
- `GET /api/sprints/:id/progress` - Progression sprint
- `GET /api/user-stories/:id/progress` - Progression US

**Calcul cascade :**
- Task : 0% (new) ou 100% (completed)
- US : (tasks completed / total tasks) × 100
- Sprint : (US completed / total US) × 100
- Projet : (sprints completed / total sprints) × 100

### Multi-LEDs
- `POST /api/leds/multi-update` - Mise à jour multi-zones
- Body : `[{zone_id, percentage, color}, ...]`

---

## 🎨 Frontend - Composants

### Pages
- `/projects` - Liste des projets avec cartes
- `/projects/:id` - Vue détail projet + arborescence

### Composants clés

**TreeNode.tsx** (récursif)
- Props : `{type, data, level, children, onExpand, onAction}`
- Affichage : icône + label + badge status + % progression
- Actions : expand/collapse, edit, delete, add child

**ProjectTree.tsx**
- Affiche l'arborescence complète
- Gère état expand/collapse
- Menu contextuel sur chaque nœud

**GaugeLayout.tsx**
- Props : `{layoutType, projectData}`
- 4 layouts :
  - **Single** : 1 jauge projet
  - **Sprint View** : 1 jauge par sprint (grid 3 col)
  - **User Story View** : jauges des US (grid responsive)
  - **Hierarchy** : jauge projet + jauges sprints dessous

**MultiGauge.tsx**
- Props : `{gauges: Array<{id, label, percentage, color}>}`
- Affiche N jauges en grid
- Polling 2s pour mise à jour

**Modals CRUD**
- `ProjectFormModal.tsx`
- `SprintFormModal.tsx`
- `UserStoryFormModal.tsx`
- `TaskFormModal.tsx`
- Modes : create / edit

**LayoutSelector.tsx**
- Dropdown pour sélectionner layout
- Sauvegarde dans localStorage
- 4 options avec icônes

---

## 🔌 Hardware - Multi-LEDs

### Configuration `config.json`
```json
{
  "hardware": {
    "led_zones": [
      {"id": "zone-1", "start_led": 0, "end_led": 31},
      {"id": "zone-2", "start_led": 32, "end_led": 63}
    ],
    "total_leds": 64,
    "default_color": [0, 255, 0]
  }
}
```

### Module `multi_led_controller.py`

**Fonction principale :**
```python
def update_multi_leds(gauges: List[Dict]):
    """
    gauges = [
        {"zone_id": "zone-1", "percentage": 75, "color": [0,255,0]},
        {"zone_id": "zone-2", "percentage": 30, "color": [255,255,0]}
    ]
    """
    # Mapper zone_id → start_led, end_led
    # Calculer nb LEDs à allumer par zone
    # Allumer les LEDs avec couleur
```

**Fallback mono-zone :**
- Si 1 seule zone configurée : afficher jauge sélectionnée
- Sélecteur "Jauge principale" dans UI

---

## 🗂️ Structure de fichiers

### Backend
```
/backend
├── models/
│   ├── project.py
│   ├── sprint.py
│   ├── user_story.py
│   └── task.py
├── routes/
│   ├── projects.py
│   ├── sprints.py
│   ├── user_stories.py
│   └── tasks.py
├── controllers/
│   ├── multi_led_controller.py
│   └── progress_calculator.py
├── config.json
└── app.py
```

### Frontend
```
/frontend
├── app/
│   ├── projects/
│   │   ├── page.tsx
│   │   └── [id]/page.tsx
│   └── layout.tsx
├── components/
│   ├── TreeNode.tsx
│   ├── ProjectTree.tsx
│   ├── GaugeLayout.tsx
│   ├── MultiGauge.tsx
│   ├── LayoutSelector.tsx
│   └── modals/
│       ├── ProjectFormModal.tsx
│       ├── SprintFormModal.tsx
│       ├── UserStoryFormModal.tsx
│       └── TaskFormModal.tsx
└── lib/
    └── api.ts
```

---


### `seed_data.py`
```python
# Créer 1 projet "Demo"
# Créer 2 sprints
# Créer 3-4 US par sprint
# Créer 3-5 tasks par US
# Mix de status
```

---

## 📦 Base de données

### Relations
```
Project (1) ──< (N) Sprint
Sprint (1) ──< (N) UserStory
UserStory (1) ──< (N) Task
```

### Cascade delete
- Supprimer Projet → supprime Sprints → supprime US → supprime Tasks
- Géré par : `ondelete='CASCADE'` sur foreign keys

### SQLite Schema
```sql
CREATE TABLE projects (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    created_at DATETIME
);

CREATE TABLE sprints (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT,
    start_date DATE,
    end_date DATE,
    status TEXT,
    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
);

CREATE TABLE user_stories (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    sprint_id TEXT,
    priority TEXT,
    status TEXT,
    FOREIGN KEY (sprint_id) REFERENCES sprints(id) ON DELETE CASCADE
);

CREATE TABLE tasks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    user_story_id TEXT,
    status TEXT,
    created_at DATETIME,
    FOREIGN KEY (user_story_id) REFERENCES user_stories(id) ON DELETE CASCADE
);
```

---

## ✅ Livrables Sprint 2

1. **Backend**
   - [ ] 4 modèles avec relations
   - [ ] ~20 endpoints REST
   - [ ] Cascade delete fonctionnel
   - [ ] Calcul progression multi-niveaux
   - [ ] Module multi-LEDs

2. **Frontend**
   - [ ] Arborescence expandable/collapsible
   - [ ] 4 layouts de visualisation
   - [ ] CRUD complet (4 modals)
   - [ ] Multi-jauges virtuelles
   - [ ] Sélecteur de layout avec persistance

3. **Configuration**
   - [ ] config.json pour hardware
   - [ ] seed_data.py avec démo
   - [ ] README complet
