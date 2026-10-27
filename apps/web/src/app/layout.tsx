import type { Metadata } from "next";
import { Barlow_Condensed, Geist } from "next/font/google";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

import "./globals.css";

import { Providers } from "./providers";

// Exposes --font-sans and --font-logo on <html>; globals.css maps them to
// Tailwind's font-sans and font-logo. Barlow Condensed is only for the wordmark.
const geist = Geist({ subsets: ["latin"], variable: "--font-sans" });
const barlow = Barlow_Condensed({
  subsets: ["latin"],
  weight: "600",
  variable: "--font-logo",
});

export const metadata: Metadata = {
  title: { default: "GovMine", template: "%s · GovMine" },
  description: "Crawls public institutions' websites and extracts cited records",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // next-themes sets the `dark` class on <html> before hydration.
    <html
      lang="en"
      className={cn("font-sans", geist.variable, barlow.variable)}
      suppressHydrationWarning
    >
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
