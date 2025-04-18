import { SidebarInset, SidebarProvider, } from "@/components/ui/sidebar"
import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"



export default function SettingsPage() {
    return (
        <SidebarProvider
            style={
                {
                    "--sidebar-width": "calc(var(--spacing) * 72)",
                    "--header-height": "calc(var(--spacing) * 12)",
                } as React.CSSProperties
            }
        >
            <AppSidebar variant="inset" />

            <SidebarInset>
                <SiteHeader />

                <div className="p-4">
                    <h1 className="text-2xl font-bold mb-4">Settings</h1>
                    <p>Itt lesznek a beállításaid.</p>

                    <p>ALGO</p>
                    <p>Change algo</p>

                    <p>Link to account settings</p>
                </div>
            </SidebarInset>
        </SidebarProvider>

                )
}