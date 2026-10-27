import Link from "next/link";
import { Suspense } from "react";

import { Logo, Wordmark } from "@/components/shared/logo";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

import { CurrentNavMenu, NavMenu } from "./app-nav";

/** The app's sidebar: the logo, then one link per section, the current one highlighted. */
export function AppSidebar() {
  return (
    <Sidebar collapsible="icon">
      <SidebarHeader className="border-b py-3">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton
              size="lg"
              tooltip="GovMine"
              className="gap-3 hover:bg-transparent active:bg-transparent"
              render={<Link href="/" />}
            >
              <Logo className="size-10! shrink-0 group-data-[collapsible=icon]:size-8!" />
              <Wordmark className="text-xl" />
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupContent>
            <Suspense fallback={<NavMenu pathname={null} />}>
              <CurrentNavMenu />
            </Suspense>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
    </Sidebar>
  );
}
