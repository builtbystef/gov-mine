import { Suspense, type ReactNode } from "react";

import { AppSidebar } from "@/components/shared/layout/app-sidebar";
import { PageTitle } from "@/components/shared/layout/page-title";
import { TimeZoneSync } from "@/components/shared/time-zone-sync";
import { SidebarInset, SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { getTimeZone } from "@/lib/time-zone/server";

/** The shell is static and prerendered; the title and the time zone stream in. */
export default function AppLayout({ children }: { children: ReactNode }) {
  return (
    <SidebarProvider>
      <AppSidebar />
      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 shrink-0 items-center gap-2 border-b bg-background/85 px-4 backdrop-blur">
          <SidebarTrigger className="-ml-1" />
          <Suspense>
            <PageTitle />
          </Suspense>
        </header>
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-6 sm:px-6 md:py-8">
          {children}
        </main>
      </SidebarInset>
      <Suspense>
        <CurrentTimeZone />
      </Suspense>
    </SidebarProvider>
  );
}

async function CurrentTimeZone() {
  return <TimeZoneSync serverTimeZone={await getTimeZone()} />;
}
