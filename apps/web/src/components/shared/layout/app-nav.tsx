"use client";

import {
  Building2Icon,
  DatabaseIcon,
  FileTextIcon,
  LayoutDashboardIcon,
  RefreshCwIcon,
  type LucideIcon,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";

const nav: { href: string; label: string; icon: LucideIcon }[] = [
  { href: "/", label: "Overview", icon: LayoutDashboardIcon },
  { href: "/institutions", label: "Institutions", icon: Building2Icon },
  { href: "/runs", label: "Runs", icon: RefreshCwIcon },
  { href: "/documents", label: "Documents", icon: FileTextIcon },
  { href: "/records", label: "Records", icon: DatabaseIcon },
];

/** Whether the nav item at `href` covers the current page, its subpages included. */
function isCurrent(pathname: string | null, href: string): boolean {
  if (pathname === null) return false;
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(`${href}/`);
}

/** One link per section, the one at `pathname` highlighted (none while it is unknown). */
export function NavMenu({ pathname }: { pathname: string | null }) {
  return (
    <SidebarMenu className="gap-1">
      {nav.map(({ href, label, icon: Icon }) => (
        <SidebarMenuItem key={href}>
          <SidebarMenuButton
            tooltip={label}
            isActive={isCurrent(pathname, href)}
            className="h-9 font-medium text-muted-foreground data-active:text-sidebar-accent-foreground"
            render={<Link href={href} />}
          >
            <Icon />
            <span>{label}</span>
          </SidebarMenuButton>
        </SidebarMenuItem>
      ))}
    </SidebarMenu>
  );
}

/** The nav for the current URL; it streams in behind a <Suspense>, like <PageTitle>. */
export function CurrentNavMenu() {
  return <NavMenu pathname={usePathname()} />;
}
