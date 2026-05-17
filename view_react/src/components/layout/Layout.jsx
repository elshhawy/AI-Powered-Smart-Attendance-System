import { Outlet } from 'react-router-dom'
import Sidebar from './Sidebar'
import { motion } from 'framer-motion'

export default function Layout() {
  return (
    <div className="flex h-screen overflow-hidden bg-surface-950">
      <Sidebar />
      <main className="flex-1 ml-64 overflow-y-auto">
        <motion.div
          key={location.pathname}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.2 }}
          className="min-h-full p-8"
        >
          <Outlet />
        </motion.div>
      </main>
    </div>
  )
}
