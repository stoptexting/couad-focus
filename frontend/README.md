# Focus Tasks - Frontend

A Next.js 14+ frontend application for task management with synchronized physical LED gauge. Built with TypeScript, Tailwind CSS, and shadcn/ui components.

## Features

- ✅ Full CRUD operations for tasks
- ✅ Real-time progress tracking with visual LED gauge
- ✅ Synchronized with physical LED hardware
- ✅ Auto-refresh every 2 seconds
- ✅ Responsive design (mobile, tablet, desktop)
- ✅ Dark mode support
- ✅ Accessibility features (ARIA labels, keyboard navigation)
- ✅ Loading states and error handling
- ✅ Form validation

## Tech Stack

- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript (strict mode)
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui
- **State Management:** TanStack React Query
- **HTTP Client:** Axios
- **Icons:** Lucide React

## Prerequisites

- Node.js 18.x or higher
- npm or yarn
- Backend server running on port 5000 (see ../server)

## Installation

1. Install dependencies:

```bash
npm install
```

2. Create environment file:

```bash
cp .env.example .env.local
```

3. Configure environment variables in `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## Development

Start the development server:

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

## Build

Create a production build:

```bash
npm run build
```

Start the production server:

```bash
npm start
```

## Project Structure

```
frontend/
├── app/
│   ├── layout.tsx          # Root layout with React Query provider
│   ├── page.tsx            # Dashboard page (main UI)
│   ├── providers.tsx       # Client-side providers wrapper
│   ├── globals.css         # Tailwind imports + custom styles
│   └── favicon.ico
├── components/
│   ├── TaskCard.tsx        # Task card with checkbox, edit, delete
│   ├── ProgressGauge.tsx   # 8-row LED visualization
│   ├── TaskFormModal.tsx   # Create/edit modal dialog
│   └── ui/                 # shadcn components (auto-generated)
│       ├── button.tsx
│       ├── card.tsx
│       ├── dialog.tsx
│       ├── badge.tsx
│       ├── checkbox.tsx
│       ├── input.tsx
│       ├── textarea.tsx
│       ├── label.tsx
│       └── progress.tsx
├── lib/
│   ├── types.ts            # TypeScript interfaces
│   ├── queryClient.ts      # React Query configuration
│   ├── utils.ts            # Utility functions (cn, etc.)
│   └── api/
│       ├── client.ts       # Axios instance
│       └── tasks.ts        # API functions
├── .env.local             # Environment variables (gitignored)
├── .env.example           # Template for env vars
├── .gitignore
├── next.config.js
├── package.json
├── tsconfig.json
├── tailwind.config.ts
├── postcss.config.js
├── components.json        # shadcn/ui configuration
├── PLAN.md               # Implementation plan
└── README.md             # This file
```

## API Endpoints

The frontend connects to the Flask backend at `http://localhost:5000`:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/tasks` | List all tasks |
| GET | `/api/tasks/:id` | Get single task |
| POST | `/api/tasks` | Create task |
| PUT | `/api/tasks/:id` | Update task |
| DELETE | `/api/tasks/:id` | Delete task |
| GET | `/api/progress` | Get progress stats |

## Components Overview

### TaskCard

Displays individual task with:
- Title and description (truncated)
- Status badge (new/completed)
- Checkbox to toggle completion
- Edit and delete buttons
- Created date

### ProgressGauge

Visual representation of task completion:
- 8 rows matching physical LED matrix
- Color gradient:
  - 0-33%: Red
  - 34-66%: Yellow
  - 67-100%: Green
- Real-time updates every 2 seconds
- Connection status indicator
- Displays "X / Y tasks completed"

### TaskFormModal

Modal for creating/editing tasks:
- Title field (required, max 100 chars)
- Description field (optional, max 500 chars)
- Client-side validation
- Character counters
- Error messages

## Responsive Design

- **Mobile (<640px):** 1 column grid
- **Tablet (640-1024px):** 2 column grid
- **Desktop (>1024px):** 3 column grid

## Accessibility

- Semantic HTML structure
- ARIA labels on interactive elements
- Keyboard navigation support
- Focus management in modals
- Screen reader friendly

## Testing Scenarios

### CRUD Operations

1. Create 3 tasks → verify list with status "new"
2. Modify task title → verify persistence
3. Check "Completed" checkbox → verify status changes to "completed"
4. Uncheck completed task → verify status changes to "new"
5. Delete task → verify removal from list

### Synchronization

1. Create 4 tasks → progress = 0% (0/4)
2. Mark 2 tasks completed → progress = 50% (2/4)
3. Verify ProgressGauge shows 50% (4/8 rows lit)
4. Mark all completed → progress = 100% (4/4)
5. Delete 1 completed task → progress recalculated (3/3 = 100%)
6. Verify gauge updates automatically (2s polling)

## Scripts

- `npm run dev` - Start development server
- `npm run build` - Create production build
- `npm start` - Start production server
- `npm run lint` - Run ESLint

## Troubleshooting

### Backend Connection Issues

If you see "Failed to load tasks":
1. Ensure backend server is running on port 5000
2. Check `NEXT_PUBLIC_API_URL` in `.env.local`
3. Verify CORS is enabled on backend

### Build Errors

If you encounter TypeScript errors:
1. Delete `.next` folder
2. Run `npm install` again
3. Run `npm run build`

## License

ISC
