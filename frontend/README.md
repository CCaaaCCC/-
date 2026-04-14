# Smart Greenhouse Frontend

This is the Vue 3 frontend for the Smart Greenhouse project.

## Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```

2.  Install dependencies:
    ```bash
    npm install
    ```

3.  Run development server:
    ```bash
    npm run dev
    ```

4.  (Optional) Configure backend API base URL:
    ```bash
    # frontend/.env.local
    VITE_API_BASE_URL=http://localhost:8000/api
    ```
    If not set, the app will fallback to `<current-host>:8000/api` in browser.

The application will be available at http://localhost:5173 (or the port shown in the terminal).

## Features
- Real-time monitoring of temperature, humidity, soil moisture, and light.
- Historical data charts using ECharts.
- Device selection to view specific greenhouse data.
- Multi-theme UI system with `light`, `dark`, `modern`, and `system` modes.
- Theme preference persistence in `localStorage` (`ui.theme.mode`).
- Chart theme adaptation via CSS variables for both dashboard and display pages.

## Theme Switching

- Use the top-right theme menu in the main layout.
- `system` mode follows `prefers-color-scheme` automatically.
- Reduced-motion users are respected via `prefers-reduced-motion` in transitions.
