import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Pulse ERP",
  description: "Modular ERP with Real-time Business Intelligence",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
