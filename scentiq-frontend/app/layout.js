import "./globals.css"
import Navbar from "./components/Navbar"

export const metadata = {
  title: "Scentiq",
  description: "AI-powered fragrance intelligence platform"
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="bg-white dark:bg-gray-950 min-h-screen">
        <Navbar />
        <main className="max-w-4xl mx-auto px-6 py-8">
          {children}
        </main>
      </body>
    </html>
  )
}