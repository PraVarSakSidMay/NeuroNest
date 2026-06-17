/* ──────────────────────────────────────────────────────────────
   NotFound — 404 page
   ────────────────────────────────────────────────────────────── */
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import Button from "../components/common/Button";

export default function NotFound() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4"
    >
      <div className="text-8xl mb-6">🌙</div>
      <h2 className="text-4xl font-bold gradient-text mb-4">Page Not Found</h2>
      <p className="text-surface-500 mb-10 max-w-md text-lg">
        The page you're looking for doesn't exist or has been moved. Let's get you back to safety.
      </p>
      <Link to="/">
        <Button size="lg">Back to Dashboard</Button>
      </Link>
    </motion.div>
  );
}
