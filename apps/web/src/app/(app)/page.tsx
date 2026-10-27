import {
  ArrowRightIcon,
  Building2Icon,
  DatabaseIcon,
  FileTextIcon,
  RefreshCwIcon,
} from "lucide-react";
import type { Metadata } from "next";
import Link from "next/link";

import { Logo } from "@/components/shared/logo";

export const metadata: Metadata = { title: "Overview" };

const sections = [
  {
    href: "/institutions",
    title: "Institutions",
    icon: Building2Icon,
    text: "The public bodies GovMine watches, and the websites and crawl settings for each.",
  },
  {
    href: "/runs",
    title: "Runs",
    icon: RefreshCwIcon,
    text: "Every crawl: what was fetched or skipped, the snapshots and documents it kept, and what the AI calls cost.",
  },
  {
    href: "/documents",
    title: "Documents",
    icon: FileTextIcon,
    text: "Every document found, with each version kept and the records extracted from it.",
  },
  {
    href: "/records",
    title: "Records",
    icon: DatabaseIcon,
    text: "Structured records extracted from documents, each field cited to the text it came from.",
  },
] as const;

export default function HomePage() {
  return (
    <div className="flex flex-col gap-8">
      <section className="flex items-center gap-5 rounded-2xl border bg-card p-6 shadow-xs sm:p-8">
        <Logo className="hidden size-16 shrink-0 sm:block" />
        <div className="flex flex-col gap-2">
          <h2 className="text-2xl font-semibold tracking-tight sm:text-3xl">
            Gov<span className="text-primary">Mine</span>
          </h2>
          <p className="max-w-2xl text-muted-foreground">
            Crawls government websites, keeps every page and file it reads, and extracts structured
            records with a citation for each field.
          </p>
        </div>
      </section>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {sections.map(({ href, title, icon: Icon, text }) => (
          <Link
            key={href}
            href={href}
            className="group flex flex-col gap-3 rounded-xl border bg-card p-5 shadow-xs transition-colors hover:border-primary/40 hover:bg-accent/40"
          >
            <span className="flex size-10 items-center justify-center rounded-lg bg-secondary text-primary">
              <Icon className="size-5" />
            </span>
            <span className="flex items-center gap-1.5 font-semibold">
              {title}
              <ArrowRightIcon className="size-4 text-muted-foreground transition-transform group-hover:translate-x-0.5" />
            </span>
            <span className="text-sm text-muted-foreground">{text}</span>
          </Link>
        ))}
      </div>
    </div>
  );
}
