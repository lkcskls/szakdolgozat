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
import KeyInpupt from "@/components/KeyInput"
import { Spinner } from "@/components/Spinner"


export default function Page() {
  const [files, setFiles] = useState<FileTableData[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  //fájlok lekérése betöltéskor
  useEffect(() => {
    const fetchData = async () => {
      try {
        const result = await getFiles();
        setFiles(result);
      }
      catch (err) { console.log(err) }
    };

    fetchData();
    setLoading(false)
  }, []);

  //táblázat frissítése
  const refreshFiles = async () => {
    setRefreshing(true)
    setLoading(true)
    setLoading(true)
    try {
      const result = await getFiles();
      setFiles(result);
    }
    catch (err) { console.log(err) }
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

        <div className="flex flex-1 flex-col overflow-x-hidden max-w-full">
          <div className="@container/main container-type:inline-size flex flex-1 flex-col gap-2">
            <div className="flex flex-col gap-4 py-4 md:gap-6 md:py-6">
              <div className="container px-4 sm:px-6 lg:px-8">

                <div className="flex flex-wrap gap-2">
                  <FileUploadModal onUploadComplete={refreshFiles} />
                  <RefreshButton onClick={refreshFiles} isLoading={refreshing || loading} />
                  <KeyInpupt />
                </div>

                {loading ? <>
                  <div className="container mx-auto py-10">
                    <Spinner />
                  </div>
                </> : <>
                  <div className="container mx-auto py-10 overflow-x-auto">
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
