'use client'

import { AppSidebar } from "@/components/app-sidebar"
import { SiteHeader } from "@/components/site-header"
import { SidebarInset, SidebarProvider, } from "@/components/ui/sidebar"
import { DataTable, FileTableData } from "@/components/file-table"
import { columns } from "@/components/file-table"
import { getFiles } from "@/lib/api"
import { useEffect, useState } from "react"
import FileUploadModal from "@/components/FileUploadModel"
import { RefreshButton } from "@/components/RefreshButton"


export default function Page() {
  const [files, setFiles] = useState<FileTableData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      const result = await getFiles();
      setFiles(result);
    };

    fetchData();
    setLoading(false)
  }, []);

  const refreshFiles = async () => {
    setRefreshing(true)
    setLoading(true)
    setLoading(true)
    const result = await getFiles();
    setFiles(result);
    setRefreshing(false)
    setLoading(false)
  };

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

        <div className="flex flex-1 flex-col">
          <div className="@container/main flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
              <div className="px-4 lg:px-6">

                <div className="flex items-center gap-2">
                  <FileUploadModal onUploadComplete={refreshFiles} />
                  <RefreshButton onClick={refreshFiles} isLoading={refreshing || loading} />
                </div>

                {loading ? <>
                  <div className="container mx-auto py-10">
                    <DataTable columns={columns(refreshFiles)} data={[]} onDataChanged={refreshFiles} />
                  </div>
                </> : <>
                  <div className="container mx-auto py-10">
                    <DataTable columns={columns(refreshFiles)} data={files} onDataChanged={refreshFiles} />
                  </div>
                </>}
              </div>
            </div>
          </div>
        </div>

      </SidebarInset>
    </SidebarProvider>
  )
}
