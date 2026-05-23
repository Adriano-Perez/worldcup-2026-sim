import type { ReactNode } from 'react';
import { Navbar } from '../components/Navbar';

// Minimal root layout: keep Navbar and main wrapper; remove extra font helper imports.
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Navbar />
        <main>{children}</main>
      </body>
    </html>
  );
}
