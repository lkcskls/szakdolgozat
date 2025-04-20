"use client"

import * as React from "react"
import {
  IconChartBar,
  IconDashboard,
  IconDatabase,
  IconFileWord,
  IconInnerShadowTop,
  IconListDetails,
  IconLogout,
  IconReport,
  IconSettings,
  IconUsers,
} from "@tabler/icons-react"

import { NavDocuments } from "@/components/nav-documents"
import { NavSecondary } from "@/components/nav-secondary"
import { NavUser } from "@/components/nav-user"
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar"
import { User, getUser } from "@/lib/api"
import { useEffect, useState } from "react"


const data = {
  navMain: [
    {
      title: "Every file",
      url: "#",
      icon: IconDashboard,
    },
    {
      title: "Public files",
      url: "#",
      icon: IconListDetails,
    },
    {
      title: "Encrypted files",
      url: "#",
      icon: IconChartBar,
    },
  ],
  navSecondary: [
    {
      title: "Settings",
      url: "/settings",
      icon: IconSettings,
    },
    {
      title: "Account",
      url: "/account",
      icon: IconUsers,
    },
    {
      title: "Log out",
      url: "/logout",
      icon: IconLogout,
    },
  ],
  documents: [
    {
      name: "Library",
      url: "/dashboard",
      icon: IconDatabase,
    },
    {
      name: "Public files",
      url: "#public-files",
      icon: IconReport,
    },
    {
      name: "Encrypted files",
      url: "#encrypted-files",
      icon: IconFileWord,
    },
  ],
}

export function AppSidebar({ ...props }: React.ComponentProps<typeof Sidebar>) {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    getUser().then(setUser);
  }, []);

  return (
    <Sidebar collapsible="offcanvas" {...props}>
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              asChild
              className="data-[slot=sidebar-menu-button]:!p-1.5"
            >
              <a href="#">
                <IconInnerShadowTop className="!size-5" />
                <span className="text-base font-semibold">LK szakdolgozat</span>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <NavDocuments items={data.documents} />
        <NavSecondary items={data.navSecondary} className="mt-auto" />
      </SidebarContent>
      <SidebarFooter>
        {user ? <>
          <NavUser user={user} />
        </> : <></>}
      </SidebarFooter>
    </Sidebar>
  )
}
