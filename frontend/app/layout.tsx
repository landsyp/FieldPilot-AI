import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "FieldPilot AI",
  description: "Technician field operations for lawn care teams.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
