import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { KeyProvider } from "@/components/KeyProvider";
import { Toaster } from "@/components/ui/sonner"

import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Kolos Lukácsi Thesis",
  description: "PQC File Storage",
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${geistSans.variable} ${geistMono.variable} antialiased`}>
        <KeyProvider>
          {children}
          <Toaster />
        </KeyProvider>
      </body>
    </html>
  );
}
