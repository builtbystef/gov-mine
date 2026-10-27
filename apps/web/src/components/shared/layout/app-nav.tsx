"use client";

import {
  Building2Icon,
  DatabaseIcon,
  FileTextIcon,
  LayoutDashboardIcon,
  RefreshCwIcon,
  type LucideIcon,
} from "lucide-react";
import type { Route } from "next";
import Link from "next/link";
import { usePathname } from "next/navigation";

import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarMenuSub,
  SidebarMenuSubButton,
  SidebarMenuSubItem,
} from "@/components/ui/sidebar";
import { recordTypeLabels, recordTypes, recordTypeSlugs } from "@/features/records/schemas";

const nav: { href: Route; label: string; icon: LucideIcon }[] = [
  { href: "/", label: "Overview", icon: LayoutDashboardIcon },
  { href: "/institutions", label: "Institutions", icon: Building2Icon },
  { href: "/runs", label: "Runs", icon: RefreshCwIcon },
  { href: "/documents", label: "Documents", icon: FileTextIcon },
  { href: "/records", label: "Records", icon: DatabaseIcon },
];

/** Each record type's own page, listed under Records. */
const recordPages = recordTypes.map((type) => ({
  href: `/records/${recordTypeSlugs[type]}` as Route,
  label: recordTypeLabels[type],
}));

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
      {nav.map(({ href, label, icon: Icon }) => {
        const subs = href === "/records" ? recordPages : [];
        const onSub = subs.some((sub) => isCurrent(pathname, sub.href));
        return (
          <SidebarMenuItem key={href}>
            <SidebarMenuButton
              tooltip={label}
              isActive={isCurrent(pathname, href) && !onSub}
              className="h-9 font-medium text-muted-foreground data-active:text-sidebar-accent-foreground"
              render={<Link href={href} />}
            >
              <Icon />
              <span>{label}</span>
            </SidebarMenuButton>
            {subs.length > 0 && (
              <SidebarMenuSub>
                {subs.map((sub) => (
                  <SidebarMenuSubItem key={sub.href}>
                    <SidebarMenuSubButton
                      isActive={isCurrent(pathname, sub.href)}
                      className="text-muted-foreground data-active:font-medium"
                      render={<Link href={sub.href} />}
                    >
                      <span>{sub.label}</span>
                    </SidebarMenuSubButton>
                  </SidebarMenuSubItem>
                ))}
              </SidebarMenuSub>
            )}
          </SidebarMenuItem>
        );
      })}
    </SidebarMenu>
  );
}

/** The nav for the current URL; it streams in behind a <Suspense>, like <PageTitle>. */
export function CurrentNavMenu() {
  return <NavMenu pathname={usePathname()} />;
}
