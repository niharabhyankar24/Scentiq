import "./globals.css"
import Navbar from "./components/Navbar"
import { Playfair_Display, DM_Sans } from "next/font/google"

const playfair = Playfair_Display({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-playfair"
})

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500"],
  variable: "--font-dm-sans"
})

export const metadata = {
  title: "Scentiq",
  description: "AI-powered fragrance intelligence platform"
}

export default function RootLayout({ children }) {
  return (
    <html lang="en" className={`${playfair.variable} ${dmSans.variable}`}>
      <body className="bg-white dark:bg-[#100f0d] min-h-screen font-sans text-neutral-900 dark:text-white">
        <Navbar />
        <main className="max-w-4xl mx-auto px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}