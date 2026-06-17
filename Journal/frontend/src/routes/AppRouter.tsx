/* ──────────────────────────────────────────────────────────────
   App Router — React Router v7 route configuration
   ────────────────────────────────────────────────────────────── */
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Layout } from "../components/layout/Layout";
import ProtectedRoute from "../components/layout/ProtectedRoute";
import Dashboard from "../pages/Dashboard/Dashboard";
import JournalList from "../pages/Journal/JournalList";
import CreateEntry from "../pages/Journal/CreateEntry";
import EditEntry from "../pages/Journal/EditEntry";
import ViewEntry from "../pages/Journal/ViewEntry";
import ReflectionPage from "../pages/Reflection/ReflectionPage";
import TimelinePage from "../pages/Timeline/TimelinePage";
import NotFound from "../pages/NotFound";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<ProtectedRoute />}>
          <Route element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="journal" element={<JournalList />} />
            <Route path="journal/new" element={<CreateEntry />} />
            <Route path="journal/:id" element={<ViewEntry />} />
            <Route path="journal/:id/edit" element={<EditEntry />} />
            <Route path="reflections" element={<ReflectionPage />} />
            <Route path="timeline" element={<TimelinePage />} />
            <Route path="*" element={<NotFound />} />
          </Route>
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
