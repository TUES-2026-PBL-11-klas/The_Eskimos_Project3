import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

import Header from "@/components/Header";
import Footer from "@/components/Footer";
import DueRemindersPopup from "@/components/DueRemindersPopup";
import { USE_MOCK } from "@/lib/api/config";
import { DemoProvider } from "@/lib/demo/store";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "EventHub — discover events across Bulgaria",
    template: "%s · EventHub",
  },
  description:
    "EventHub aggregates events from across Bulgaria into one place — browse, search and filter concerts, tech meetups, theatre, sports and more.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="page-bg flex min-h-full flex-col">
        <DemoProvider useMock={USE_MOCK}>
          <Header />
          <div className="flex-1">{children}</div>
          <Footer />
          <DueRemindersPopup />
        </DemoProvider>
      </body>
    </html>
  );
}
