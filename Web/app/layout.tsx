import type React from "react"
import type { Metadata } from "next"

import { Analytics } from "@vercel/analytics/react"
import { Geist, Geist_Mono, Playfair_Display } from "next/font/google"
import "./globals.css"

const geist = Geist({
  subsets: ["latin"],
  variable: "--font-sans",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
})

const playfair = Playfair_Display({
  subsets: ["latin"],
  variable: "--font-playfair",
})

export const metadata: Metadata = {
  title: "Scipher",
  description: "AI-powered research paper analysis",
  generator: "v0.app",
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" className={`${geist.variable} ${geistMono.variable} ${playfair.variable}`}>
      <body className="font-sans antialiased bg-black text-white">
        {children}
        <Analytics />
      </body>
    </html>
  )
}
