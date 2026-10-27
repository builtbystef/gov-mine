import type { Metadata } from "next";
import Link from "next/link";

import { DocumentTitle } from "@/components/shared/layout/document-title";
import { Logo } from "@/components/shared/logo";
import { Button } from "@/components/ui/button";

export const metadata: Metadata = { title: "Page not found" };

/** Also reached from inside a page whose title has already streamed (a record
 * that does not exist); hence <DocumentTitle>. */
export default function RootNotFound() {
  return (
    <main className="flex min-h-svh flex-col items-center justify-center gap-4 p-6">
      <DocumentTitle title="Page not found · GovMine" />
      <Logo className="size-12" />
      <h1 className="text-2xl font-semibold tracking-tight">Page not found</h1>
      <Button variant="outline" nativeButton={false} render={<Link href="/" />}>
        Back to GovMine
      </Button>
    </main>
  );
}
