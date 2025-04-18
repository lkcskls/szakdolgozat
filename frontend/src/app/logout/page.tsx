"use client"

import { useEffect } from "react"
import { useRouter } from "next/navigation"
import { logoutUser } from "@/lib/api"
import { motion } from "framer-motion"
import { LogOut } from "lucide-react"

export default function LogoutPage() {
    const router = useRouter()

    useEffect(() => {
        const performLogout = async () => {
            try {
                await logoutUser()
            } catch (error) {
                console.error("Logout error:", error)
            } finally {
                router.replace("/login")
            }
        }

        performLogout()
    }, [router])

    return (
        <div className="flex flex-col items-center justify-center h-screen gap-4">
            <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.8 }}
                className="text-2xl font-semibold"
            >
                Logging out...
            </motion.div>

            <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
            >
                <LogOut className="h-12 w-12 text-gray-600" />
            </motion.div>
        </div>
    )
}
